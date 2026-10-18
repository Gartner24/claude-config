#!/usr/bin/env python3
"""Spec 0052 AC-8: 8 worktrees of one repo committing at once through wf.git().

Runs before raising `parallel` past 4: git keeps one common dir per repo, so 8 features
building side by side share its refs and object store. Exit 0 only on a clean
`git fsck --full` and every new commit present; prints PASS or FAIL: <check>.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import wf  # noqa: E402

WORKERS = 8
COMMITS = 50
IDENTITY = {"GIT_AUTHOR_NAME": "stress", "GIT_AUTHOR_EMAIL": "stress@example.invalid",
            "GIT_COMMITTER_NAME": "stress", "GIT_COMMITTER_EMAIL": "stress@example.invalid"}


def must(r, what):
    if r is None or r.returncode != 0:
        sys.exit(f"FAIL: {what}: {r.stderr.strip() if r else 'no git'}")
    return r


def worker(clone, n):
    tree = os.path.join(os.path.dirname(clone), f"tree-{n}")
    must(wf.git(clone, "worktree", "add", "-q", "-b", f"stress-{n}", tree), f"worker {n} worktree add")
    for i in range(COMMITS):
        with open(os.path.join(tree, f"w{n}.txt"), "a", encoding="utf-8") as f:
            f.write(f"{i}\n")
        must(wf.git(tree, "add", f"w{n}.txt"), f"worker {n} add {i}")
        must(wf.git(tree, "commit", "-q", "-m", f"w{n} c{i}"), f"worker {n} commit {i}")


def main():
    os.environ.update(IDENTITY)
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        worker(sys.argv[2], int(sys.argv[3]))
        return 0
    tmp = tempfile.mkdtemp(prefix="wf-stress-")
    origin, clone = os.path.join(tmp, "origin"), os.path.join(tmp, "clone")
    must(wf.git(tmp, "init", "-q", "-b", "main", origin), "init")
    with open(os.path.join(origin, "README"), "w", encoding="utf-8") as f:
        f.write("scratch\n")
    must(wf.git(origin, "add", "README"), "add")
    must(wf.git(origin, "commit", "-q", "-m", "seed"), "seed commit")
    must(wf.git(tmp, "clone", "-q", origin, clone), "clone")
    before = int(must(wf.git(clone, "rev-list", "--all", "--count"), "count").stdout)
    procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), "--worker", clone, str(n)])
             for n in range(WORKERS)]
    failed = [n for n, p in enumerate(procs) if p.wait() != 0]
    if failed:
        print(f"FAIL: workers {failed} exited non zero (temp left in {tmp})")
        return 1
    fsck = wf.git(clone, "fsck", "--full")
    if fsck.returncode != 0:
        print(f"FAIL: git fsck --full: {fsck.stderr.strip()} (temp left in {tmp})")
        return 1
    after = int(must(wf.git(clone, "rev-list", "--all", "--count"), "count").stdout)
    if after - before != WORKERS * COMMITS:
        print(f"FAIL: {after - before} new commits, expected {WORKERS * COMMITS} (temp left in {tmp})")
        return 1
    print(f"PASS: {WORKERS} worktrees, {after - before} commits, fsck clean")
    shutil.rmtree(tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
