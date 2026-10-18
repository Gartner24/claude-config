#!/usr/bin/env python3
"""Design preview facts for the wf-dash band, as JSON on stdout.

shortcut: stands in for `wf status --json` (spec 0059 AC-1) and statusbar.render (spec 0058) until row 72 builds them;
the build replaces this file, the band's drawing stays.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[3] / "runner"
sys.path.insert(0, str(RUNNER))


def wf_clean(s):
    import wf
    return wf.clean(s)


def repo_filters(cwd):
    # `git status` runs filter drivers; one set in the repo's own config is code from whoever made the repo
    import wf
    try:
        out = subprocess.run(["git", *wf.GIT_SAFE, "config", "--includes", "--show-scope", "--get-regexp", r"^filter\."], cwd=cwd,
                             capture_output=True, text=True, timeout=1).stdout
    except (OSError, subprocess.SubprocessError):
        return True
    return any(not line.startswith(("system\t", "global\t")) for line in out.splitlines())


def git(cwd):
    import wf
    if repo_filters(cwd):
        branch = wf.head_branch(cwd)
        return None if branch == "no git" else {"branch": branch, "changes": None, "staged": None, "modified": None, "untracked": None}
    try:
        out = subprocess.run(["git", *wf.GIT_SAFE, "status", "--porcelain=v1", "-b", "--ignore-submodules=all"], cwd=cwd, capture_output=True,
                             text=True, timeout=1).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    lines = out.splitlines()
    if not lines or not lines[0].startswith("## "):
        return None
    branch = wf.clean(lines[0][3:].split("...")[0])
    rows = lines[1:]
    untracked = sum(r.startswith("??") for r in rows)
    staged = sum(r[0] not in " ?" for r in rows)
    modified = sum(len(r) > 1 and r[1] not in " ?" for r in rows)
    return {"branch": branch, "changes": len(rows), "staged": staged, "modified": modified, "untracked": untracked}


def wf():
    try:
        import auto
        import run
    except Exception:
        return {"running": None, "parked": None, "questions": None}
    try:
        running = len([a for a in run.read_active() if auto.entry_running(a)])
    except Exception:
        running = None
    try:
        ds = run.queue_transact()["decisions"]
        open_ = [d for d in ds if d["answer"] is None]
        parked = len([d for d in open_ if d.get("parked")])
        questions = len(open_)
    except Exception:
        parked = questions = None
    return {"running": running, "parked": parked, "questions": questions}


def autonomous(cwd):
    # the bar's AUTO segment (spec 0046 AC-7): this chat drives the runner, or how many chats do
    try:
        import auto
        s = auto.load()
        _, c = auto.chat(s, cwd)
    except Exception:
        return None
    return {"here": c is not None, "chats": len((s or {}).get("chats") or {})}


if __name__ == "__main__":
    cwd = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(json.dumps({"folder": wf_clean(os.path.basename(cwd.rstrip("/")) or "/"), "git": git(cwd),
                      "wf": wf(), "auto": autonomous(cwd)}))
