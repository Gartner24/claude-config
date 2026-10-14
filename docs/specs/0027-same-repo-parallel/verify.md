# 0027 verify

## Probes (2026-10-13)

- **P1** (local, no network): in a temp dir, `git init r`, an empty base commit, `git -C r worktree add ../a -b a` and `../b -b b`, then 50 commits of one file in `a` and in `b` at the same time. Both `git -C a rev-list --count a` and `git -C b rev-list --count b` print 51, no commit failed (no `index.lock` or ref lock error), and `git -C r fsck` exits 0. Result: PASS.

## Live

- **AC-10**: `python3 runner/e2e/run.py --same-repo` (real claude) waits on you.
