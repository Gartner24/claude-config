# Leftovers found on 2026-10-18

Bugs and open items found while conducting the runner on 2026-10-18 (rows 72, 51, 76, 77 and the security review of that day). Each is a bug or a decision, not a new feature.

## Agreed so far, do not ask again
- The owner lets the conductor session run, merge and install everything in claude-config itself; only work repos are off limits (owner, 2026-10-18).
- Row 72's look was accepted as is at critique 29/40 (owner, 2026-10-17); its 7 design gate should-fixes are the owner's to pick, never blockers.

## Runner bugs (row 78)
1. "accept as is" on a design_gate park does not persist to the next run: row 72 was asked three times (questions 5rl1, m2mh, 3hqr). The real cause that time was a report one folder too low (`hooks/.design/` covers only `hooks/`), but an accepted park still came back.
2. A branch squashed on an old plan copy opens a PR whose diff reverts main: PR #60 (row 51) would have deleted specs 0063, 0064 and `docs/briefs/auto-handoff.md`; closed by hand. Check a PR's diff against origin/main, not only its base, before opening it.
3. A worktree child plans from the worktree's own scope copy (`runner/run.py:2598`) before `pr.plan_in` copies main's scope (`runner/run.py:3450`), so a reused old branch picks no feature.
4. The runner's uncommitted scope copy in a feature worktree blocks bringing the branch up to date with main: question amh3 on row 72 ("Your local changes to the following files would be overwritten by merge: docs/scope/scope.md"). Stashed by hand in the feat-0059 worktree.
5. A runner question shows "learn this first" twice.
6. Row 71 (self merge rules and review notes) never enters the queue; its heading has `· auto` but no status tag.

## Security review leftovers 2026-10-18 (row 79)
1. `runner/statusbar.py` runs git without `GIT_SAFE` (fsmonitor and hooks path), caches under `/tmp`, and prints the folder name unsanitized.
2. `scripts/skill-scan.py`: the NOISE regex is unanchored, and two findings can collide on one key.

## Spec 0054 AC-13 trusted list (row 80)
The skill scan skips gstack, jjstack and ui-ux-pro-max and names them in its report (owner's words in the tool review brief, B2 skill scan line). Needs the spec 0054 amendment first.

## Row 72 design gate should-fixes (row 81)
Seven should-fixes in `claude-home/mods/wf-dash/.design/audit-report.md` (pass 3, verdict PASS WITH FINDINGS). The owner picks which to build.
