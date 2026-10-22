#!/usr/bin/env python3
"""The chip-dash band's facts about this session's folder, as JSON on stdout: folder, git and the provider
(spec 0059 AC-2). Stdlib only and self-contained: it used to import the wf runner's wf.py and statusbar.py, and
the runner is retired."""
import json
import os
import re
import subprocess
import sys

# C0 and C1 controls and undecodable bytes: a folder or branch name with an ESC in it used to reach the terminal
CONTROL = re.compile(r"[\x00-\x1f\x80-\x9f\udc80-\udcff]")
COMMIT_HASH = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# a planted core.fsmonitor or hook in the repo used to run on `git status`
GIT_SAFE = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")


def clean(text):
    return CONTROL.sub("", text)


def head_branch(path):
    # HEAD read from the files, so a repo with its own filter driver never runs git
    dot = os.path.join(path, ".git")
    try:
        if os.path.isfile(dot):
            with open(dot, encoding="utf-8", errors="replace") as f:
                dot = os.path.join(path, f.read().strip().removeprefix("gitdir:").strip())
        with open(os.path.join(dot, "HEAD"), encoding="utf-8", errors="replace") as f:
            head = f.read().strip()
    except OSError:
        return "no git"
    if head.startswith("ref: refs/heads/"):
        name = head[len("ref: refs/heads/"):]
        # reftable repos keep the real HEAD elsewhere and write this placeholder
        return "-" if name in ("", ".invalid") else clean(name)
    return "detached " + head[:7] if COMMIT_HASH.fullmatch(head) else "-"


def repo_filters(cwd):
    # `git status` runs filter drivers; one set in the repo's own config is code from whoever made the repo
    try:
        out = subprocess.run(["git", *GIT_SAFE, "config", "--includes", "--show-scope", "--get-regexp", r"^filter\."], cwd=cwd,
                             capture_output=True, text=True, timeout=1).stdout
    except (OSError, subprocess.SubprocessError):
        return True
    return any(not line.startswith(("system\t", "global\t")) for line in out.splitlines())


def git(cwd):
    if repo_filters(cwd):
        branch = head_branch(cwd)
        return None if branch == "no git" else {"branch": branch, "changes": None, "staged": None, "modified": None, "untracked": None}
    try:
        out = subprocess.run(["git", *GIT_SAFE, "status", "--porcelain=v1", "-b", "--ignore-submodules=all"], cwd=cwd, capture_output=True,
                             text=True, timeout=1).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    lines = out.splitlines()
    if not lines or not lines[0].startswith("## "):
        return None
    branch = clean(lines[0][3:].split("...")[0])
    rows = lines[1:]
    untracked = sum(r.startswith("??") for r in rows)
    staged = sum(r[0] not in " ?" for r in rows)
    modified = sum(len(r) > 1 and r[1] not in " ?" for r in rows)
    return {"branch": branch, "changes": len(rows), "staged": staged, "modified": modified, "untracked": untracked}


def via():
    # spec 0058's rule: `via <host>` when Claude Code talks to a provider that is not Anthropic, else the usage meters
    base = os.environ.get("ANTHROPIC_BASE_URL", "")
    if base and "anthropic.com" not in base:
        host = base.split("://", 1)[-1].split("/", 1)[0].rsplit("@", 1)[-1].split(":", 1)[0]
        return clean(os.environ.get("CLAUDE_PROVIDER_LABEL") or host)
    return None


if __name__ == "__main__":
    cwd = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(json.dumps({"folder": clean(os.path.basename(cwd.rstrip("/")) or "/"), "git": git(cwd), "via": via()}))
