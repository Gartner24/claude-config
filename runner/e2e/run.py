#!/usr/bin/env python3
# Spec 0014 AC-5: `wf run` end to end in a throwaway copy of fixture/. It makes real claude calls, so you run it
# yourself with `!` after a Claude Code upgrade or a runner change; install.sh and the unittest suite never do.
# Spec 0017 AC-8: `--parallel` runs a bare `wf run` over two copies and checks their calls overlapped.
# Spec 0018 AC-8: both forms also check the morning report, so a PASS sends a real note to your phone.
# Spec 0020 AC-11: `--beside` runs `wf -y` beside a running `wf run`, in a temp CLAUDE_CONFIG_DIR holding a copy of
# your login (removed at the end however it ends), and checks the run takes the swap and still stops on a hand edit.
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import ntfy  # noqa: E402

FIXTURE = os.path.join(HERE, "fixture")
BRANCH = "wf-e2e"
CAPS = ["--max-calls", "10", "--max-hours", "1"]
OPEN_BOX = re.compile(r"^\s*[-*+]\s+\[ \].*$", re.M)


def git(repo, *args):
    # A fixed author: the temp repo must commit even where no git identity is set.
    subprocess.run(["git", "-C", repo, "-c", "user.name=wf-e2e", "-c", "user.email=wf-e2e@localhost", *args],
                   check=True, capture_output=True)


def setup(top, names=("repo",)):
    """The temp repos, state and config folders, with your ntfy config copied in and only those repos trusted.
    Returns (repos, env)."""
    state, config = (os.path.join(top, n) for n in ("state", "config"))
    repos = [os.path.join(top, n) for n in names]
    for repo in repos:
        shutil.copytree(FIXTURE, repo)
        subprocess.run(["git", "init", "-q", "-b", BRANCH, repo], check=True, capture_output=True)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "chore: wf e2e fixture")
    os.makedirs(os.path.join(config, "wf"), mode=0o700)
    os.makedirs(state, mode=0o700)
    # Read before the env below points XDG_CONFIG_HOME at the temp folder.
    dest = os.path.join(config, "wf", "ntfy.json")
    shutil.copyfile(ntfy.path(), dest)
    os.chmod(dest, 0o600)
    env = {**os.environ, "XDG_STATE_HOME": state, "XDG_CONFIG_HOME": config}
    for repo in repos:
        subprocess.run(["wf", "allow", repo], env=env, check=True, capture_output=True)
    return repos, env


def failure(top, repo, env):
    """None when every AC-5 check passes, else the check that failed."""
    rc = subprocess.run(["wf", "run", repo, "-y", *CAPS], env=env, stdin=subprocess.DEVNULL).returncode
    if rc != 0:
        return f"wf exit {rc}"
    runs = glob.glob(os.path.join(top, "state", "wf", "runs", "*", "run.json"))
    if len(runs) != 1:
        return f"{len(runs)} run.json files"
    with open(runs[0], encoding="utf-8") as f:
        rec = json.load(f)
    outcomes = [e.get("outcome") for e in rec.get("features", [])]
    if outcomes != ["feature_done"]:
        return f"run.json outcomes {outcomes}"
    # Spec 0018 AC-8: the run wrote its morning report and the note reached ntfy.
    if not os.path.isfile(os.path.join(top, "state", "wf", "report.txt")):
        return "no report.txt"
    if rec.get("report") != "sent":
        return f"run.json report {rec.get('report')!r}"
    with open(os.path.join(repo, "docs", "scope", "scope.md"), encoding="utf-8") as f:
        left = OPEN_BOX.findall(f.read())
    if left:
        return f"open box: {left[0].strip()}"
    if subprocess.run([sys.executable, "-m", "unittest"], cwd=repo, capture_output=True).returncode != 0:
        return "unittest"
    return None


def spans(rec):
    at = datetime.datetime.fromisoformat
    return [(at(c["started"]), at(c["started"]) + datetime.timedelta(seconds=c["duration_s"] or 0)) for c in rec["calls"]]


def parallel_failure(top, env):
    """None when every spec 0017 AC-8 check passes, else the check that failed."""
    rc = subprocess.run(["wf", "run", "-y", *CAPS], env=env, stdin=subprocess.DEVNULL).returncode
    if rc != 0:
        return f"wf exit {rc}"
    runs = sorted(glob.glob(os.path.join(top, "state", "wf", "runs", "*", "run.json")))
    if len(runs) != 2:
        return f"{len(runs)} run.json files"
    recs = []
    for p in runs:
        with open(p, encoding="utf-8") as f:
            recs.append(json.load(f))
    outcomes = [[e.get("outcome") for e in rec.get("features", [])] for rec in recs]
    if outcomes != [["feature_done"]] * 2:
        return f"run.json outcomes {outcomes}"
    if not any(s1 < e2 and s2 < e1 for s1, e1 in spans(recs[0]) for s2, e2 in spans(recs[1])):
        return "no call of one repo ran while a call of the other was running"
    # Spec 0018 AC-8: the children left the report to the parent, which wrote one naming both repos.
    reports = [rec.get("report") for rec in recs]
    if reports != ["parent"] * 2:
        return f"run.json report {reports}"
    try:
        with open(os.path.join(top, "state", "wf", "report.txt"), encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return "no report.txt"
    if "(one)" not in text or "(two)" not in text:
        return "report.txt does not name both repos"
    return None


def wait(test, seconds, what):
    """Poll test() every second; raises RuntimeError naming what never happened."""
    end = time.monotonic() + seconds
    while not test():
        if time.monotonic() > end:
            raise RuntimeError(f"timed out waiting for {what}")
        time.sleep(1)


def first_call(top, name, after=0):
    """True once a run of repo name, past the first `after` run folders, logged its first call."""
    for log in sorted(glob.glob(os.path.join(top, "state", "wf", "runs", f"{name}-*", "log.txt")))[after:]:
        with open(log, encoding="utf-8", errors="replace") as f:
            if " call 1 " in f.read():
                return True
    return False


def run_record(top, name):
    """The newest run.json of repo name, else None."""
    runs = sorted(glob.glob(os.path.join(top, "state", "wf", "runs", f"{name}-*", "run.json")))
    if not runs:
        return None
    with open(runs[-1], encoding="utf-8") as f:
        return json.load(f)


def config_dir(top):
    """AC-11: a temp CLAUDE_CONFIG_DIR with your login copied in and a settings.json whose hook names a script."""
    conf = os.path.join(top, "claude")
    os.makedirs(os.path.join(conf, "hooks"), mode=0o700)
    live = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    for src, name in ((os.path.join(live, ".credentials.json"), ".credentials.json"),
                      (os.path.expanduser("~/.claude.json"), ".claude.json")):
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(conf, name))
            os.chmod(os.path.join(conf, name), 0o600)
    hook = os.path.join(conf, "hooks", "h.sh")
    with open(hook, "w") as f:
        f.write("#!/bin/sh\nexit 0\n")
    with open(os.path.join(conf, "settings.json"), "w") as f:
        json.dump({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": f"sh {hook}"}]}]}}, f)
    return conf


def beside_failure(top):
    """None when every spec 0020 AC-11 check passes, else the check that failed."""
    (a, b), env = setup(top, ("a", "b"))
    conf = config_dir(top)
    env = {**env, "CLAUDE_CONFIG_DIR": conf}
    # B builds nothing: its feature is not queued; it only carries the live copy box.
    scope = os.path.join(b, "docs", "scope", "scope.md")
    with open(scope, encoding="utf-8") as f:
        text = f.read().replace("· in-progress · auto", "· in-progress")
    os.makedirs(os.path.join(b, "hooks"))
    with open(os.path.join(b, "hooks", "h.sh"), "w") as f:
        f.write("#!/bin/sh\necho swapped >/dev/null\nexit 0\n")
    with open(scope, "w", encoding="utf-8") as f:
        f.write(text + "\n### 2. Hook\n- [ ] Copy hook: `cp hooks/h.sh ~/.claude/hooks/h.sh` · waits on you · live\n")
    git(b, "add", "-A")
    git(b, "commit", "-q", "-m", "chore: live copy box")
    with open(os.path.join(top, "a.log"), "w") as log:
        run_a = subprocess.Popen(["wf", "run", a, "-y", *CAPS], env=env, stdin=subprocess.DEVNULL, stdout=log,
                                 stderr=subprocess.STDOUT)
    try:
        wait(lambda: first_call(top, "a"), 600, "A's first call")
        rc = subprocess.run(["wf", "-y"], env=env, stdin=subprocess.DEVNULL).returncode
        if rc != 0:
            return f"wf exit {rc}"
        run_a.wait(timeout=3600)
    finally:
        if run_a.poll() is None:
            run_a.kill()
    hook = os.path.realpath(os.path.join(conf, "hooks", "h.sh"))
    try:
        with open(os.path.join(top, "state", "wf", "swaps.jsonl"), encoding="utf-8") as f:
            ledger = [json.loads(line) for line in f]
    except (OSError, ValueError):
        return "no readable swaps.jsonl"
    if not any(hook in line.get("files", {}) for line in ledger):
        return "the swap ledger does not name the hook script"
    rec = run_record(top, "a")
    outcomes = [e.get("outcome") for e in rec.get("features", [])] if rec else None
    if outcomes != ["feature_done"]:
        return f"A run.json outcomes {outcomes}"
    setups = rec.get("setups") or []
    if len(setups) != 1:
        return f"A run.json setups {setups}"
    at = datetime.datetime.fromisoformat
    if not any(at(c["started"]) > at(setups[0]["at"]) for c in rec["calls"]):
        return "no call of A started after it took the setup"
    with open(scope, encoding="utf-8") as f:
        if "- [x] Copy hook:" not in f.read():
            return "B's live box is not ticked"
    # A hand made change during a fresh run of A still stops it.
    shutil.copyfile(os.path.join(FIXTURE, "docs", "scope", "scope.md"), os.path.join(a, "docs", "scope", "scope.md"))
    git(a, "add", "-A")
    git(a, "commit", "-q", "-m", "chore: fresh run")
    before = len(glob.glob(os.path.join(top, "state", "wf", "runs", "a-*")))
    with open(os.path.join(top, "a2.log"), "w") as log:
        run_a = subprocess.Popen(["wf", "run", a, "-y", *CAPS], env=env, stdin=subprocess.DEVNULL, stdout=log,
                                 stderr=subprocess.STDOUT)
    try:
        wait(lambda: first_call(top, "a", before), 600, "A's fresh run")
        with open(os.path.join(conf, "settings.json"), "w") as f:
            json.dump({"hooks": {}}, f)
        run_a.wait(timeout=3600)
    finally:
        if run_a.poll() is None:
            run_a.kill()
    rec = run_record(top, "a")
    if not rec or rec.get("stop_reason") != "guard_changed":
        return f"a hand made change did not stop A: {rec and rec.get('stop_reason')}"
    return None


def main():
    if not os.path.isfile(ntfy.path()):
        print(f"FAIL: no ntfy config at {ntfy.path()}, run wf ntfy init")
        return 1
    parallel = sys.argv[1:] == ["--parallel"]
    beside = sys.argv[1:] == ["--beside"]
    top = tempfile.mkdtemp(prefix="wf-e2e-")
    try:
        if beside:
            problem = beside_failure(top)
        elif parallel:
            _, env = setup(top, ("one", "two"))
            problem = parallel_failure(top, env)
        else:
            repos, env = setup(top)
            problem = failure(top, repos[0], env)
    except (OSError, subprocess.CalledProcessError, RuntimeError, subprocess.TimeoutExpired) as e:
        problem = f"setup: {e}"
    finally:
        # AC-11: the login copy never outlives the check, however it ends.
        shutil.rmtree(os.path.join(top, "claude"), ignore_errors=True)
    if problem is None:
        shutil.rmtree(top)
        print("PASS")
        return 0
    print(f"FAIL: {problem}")
    # The copy of your ntfy config stays in config/ until you delete the folder.
    for name in (("one", "two") if parallel else ("a", "b") if beside else ("repo",)) + ("state", "config"):
        print(f"kept: {os.path.join(top, name)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
