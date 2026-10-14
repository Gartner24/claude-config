# 0027 verify

## Probes (2026-10-13)

- **P1** (local, no network): in a temp dir, `git init r`, an empty base commit, `git -C r worktree add ../a -b a` and `../b -b b`, then 50 commits of one file in `a` and in `b` at the same time. Both `git -C a rev-list --count a` and `git -C b rev-list --count b` print 51, no commit failed (no `index.lock` or ref lock error), and `git -C r fsck` exits 0. Result: PASS.

## Live

- **AC-10**: `python3 runner/e2e/run.py --same-repo` (real claude) waits on you.

## Check verify (2026-10-14, real `wf` with the fake claude and fake gh, scratch repos)

Drivers: `$TMPDIR/verify0027/drive.py` (RepoCase fixture: repo `par`, `parallel: 2`, A `a.txt`, B `b.txt`, C `a.txt`) and `$TMPDIR/verify0027/rounds.py` (PrCase fixture plus `parallel: 2`, `push: draft PR`).

- [x] `wf run par -y` with `- parallel: 2` and no `branches` line -> exit 5 `refused: bad_answers: AGENTS.md: parallel needs branches: per spec`; `parallel: 5` and `parallel: two` -> exit 5 `... is not allowed for parallel` -> AC-1. can fail: the key is read without the branches check.
- [x] `wf run -y --jobs 3` -> exit 0; three worktrees under `.local/share/wf-trees/par-<6 hex>/feat-000N-x`; main checkout HEAD `refs/heads/work` before and after -> AC-2. can fail: the parent switches the main checkout.
- [x] Same run: run.json `features[].repo` is the main checkout, `tree` the worktree; summary rows `par: 1. A`, `par: 2. B`, `par: 3. C` -> AC-3, AC-9. can fail: records keep the worktree as `repo`.
- [x] Same run: A's call 14:26:48 for 4.1 s, B's call 14:26:48; C's run started 14:26:52, after A's ended 14:26:52; plan line `waits: 3. C: shares a.txt with 1. A` -> AC-4, AC-5. can fail: C starts beside A.
- [x] Same run: `git diff work...feat/000N-x` holds only `x.txt` (plus the scope tick) for each -> AC-7. can fail: one branch carries a sibling's file.
- [x] Same run: A's `--disallowedTools` holds `Edit(//.../feat-0002-b/**)`, `feat-0003-c/**`, their admin folders and refs, never its own tree -> AC-7. can fail: sibling denies left out.
- [x] Drift run (A writes `b.txt` while B builds): A parks `paths_overlap`, options `wait for the other, then go on`, `undo those files and try again`, `skip`, `other: 2. B`, `tree` set; B and C finish -> AC-6. can fail: the drift goes unnoticed.
- [x] Nothing built run (A's call changes nothing): A parks, its worktree is gone from `git worktree list`, B and C keep theirs; `pr.remove_tree` on real git keeps a dirty tree with `kept <tree>: uncommitted changes` and removes a clean merged one -> AC-8 (cleanup). can fail: an empty or dirty tree handled wrong.
- [x] Bare `wf` in a pty: `build:` list `1. par: 1. A`, `2. par: 2. B`, `3. par: 3. C` -> AC-9. can fail: one row per repo.
- [ ] Review round in a `parallel` repo: the round call ran in the worktree (`cwd` `.../wf-trees/prr-<hex>/feat-0001-a`), fix pushed, main HEAD unchanged; then the child prints the `review_ask` question and hangs: no second `pr view`, killed after 110 s although `--max-wait 0.0001`. The same fixture without `parallel` polls again, sees the merge and exits 6 in 1.7 s -> AC-8 (review rounds) FAIL, `/debug`.
  - `/debug` (2026-10-14): not a wf bug, the driver was wrong. The test wrapper's `pr` mode sets `pr.POLL_GAP = 0.05` in the parent process only; the worktree child is a fresh `wf.py run` (`run.py` builds its argv from `sys.executable`), so it keeps the real 600 s gap. A ready PR is watched with no `--max-wait` cutoff (spec 0031 AC-5), so the child correctly waits for its next poll, 10 minutes later, the same as a plain run in real use. Rerun with the child given the same gaps (`$TMPDIR/verify0027/site/sitecustomize.py` on `PYTHONPATH`): second `pr view`, PR `merged`, child `queue done`, exit 6 in 2.3 s, the worktree gone from `git worktree list`, review `cwd` the worktree, main HEAD `refs/heads/work`. Rerun this step with that driver.
- AC-10: not rerun here (real claude); the live run below passed.

## Live runs (wf finish)
- 2026-10-14, Claude Code 2.1.299: `python3 runner/e2e/run.py --same-repo` PASS (second try; the first failed on committed __pycache__ files, fixed with the fixture's .gitignore)
