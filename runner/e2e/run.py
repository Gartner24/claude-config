#!/usr/bin/env python3
# Spec 0014 AC-5: `wf run` end to end in a throwaway copy of fixture/. It makes real claude calls, so you run it
# yourself with `!` after a Claude Code upgrade or a runner change; install.sh and the unittest suite never do.
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


def setup(top):
    """The temp repo, state and config folders, with your ntfy config copied in. Returns (repo, env)."""
    repo, state, config = (os.path.join(top, n) for n in ("repo", "state", "config"))
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
    subprocess.run(["wf", "allow", repo], env=env, check=True, capture_output=True)
    return repo, env


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


def main():
    if not os.path.isfile(ntfy.path()):
        print(f"FAIL: no ntfy config at {ntfy.path()}, run wf ntfy init")
        return 1
    top = tempfile.mkdtemp(prefix="wf-e2e-")
    try:
        repo, env = setup(top)
        problem = failure(top, repo, env)
    except (OSError, subprocess.CalledProcessError) as e:
        problem = f"setup: {e}"
    if problem is None:
        shutil.rmtree(top)
        print("PASS")
        return 0
    print(f"FAIL: {problem}")
    # The copy of your ntfy config stays in config/ until you delete the folder.
    for name in ("repo", "state", "config"):
        print(f"kept: {os.path.join(top, name)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
