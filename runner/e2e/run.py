#!/usr/bin/env python3
# Spec 0014 AC-5: `wf run` end to end in a throwaway copy of fixture/. It makes real claude calls, so you run it
# yourself with `!` after a Claude Code upgrade or a runner change; install.sh and the unittest suite never do.
# Spec 0017 AC-8: `--parallel` runs a bare `wf run` over two copies and checks their calls overlapped.
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

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
        outcomes = [e.get("outcome") for e in json.load(f).get("features", [])]
    if outcomes != ["feature_done"]:
        return f"run.json outcomes {outcomes}"
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
    return None


def main():
    if not os.path.isfile(ntfy.path()):
        print(f"FAIL: no ntfy config at {ntfy.path()}, run wf ntfy init")
        return 1
    parallel = sys.argv[1:] == ["--parallel"]
    top = tempfile.mkdtemp(prefix="wf-e2e-")
    try:
        if parallel:
            _, env = setup(top, ("one", "two"))
            problem = parallel_failure(top, env)
        else:
            repos, env = setup(top)
            problem = failure(top, repos[0], env)
    except (OSError, subprocess.CalledProcessError) as e:
        problem = f"setup: {e}"
    if problem is None:
        shutil.rmtree(top)
        print("PASS")
        return 0
    print(f"FAIL: {problem}")
    # The copy of your ntfy config stays in config/ until you delete the folder.
    for name in (("one", "two") if parallel else ("repo",)) + ("state", "config"):
        print(f"kept: {os.path.join(top, name)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
