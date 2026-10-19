# Verify: runner bugs found 2026-10-18 (scope row 78)

No spec; the checklist is the brief's Runner bugs section and the retry line under the PR #77 leftovers
([leftovers-2026-10-18.md](leftovers-2026-10-18.md)). Verified 2026-10-18 on `bef34ea`, every step against the real
runner modules or the real `wf run` command in scratch git repos, with scenarios that differ from the test file.
Each step was then run against a scratch copy of `runner/` with that fix broken, and went red.

## Commands
- [x] Bug 1: accept as is on a design gate park, then a fresh run: `queue.json` holds `design_ok` with a sha256 per file, the next run is not asked, and changing one of the two accepted files asks again for it. can fail: the accept is kept only in the run (`accept_design` call removed), no `queue.json` record, red.
- [x] Bug 2: PR #60 replayed: a branch made from an old main, main then gets a spec and a brief. `fork_point` returns where the branch left main (a new branch gets main's tip); `reverts` lists the two files main has that a branch tree laid over main's tip deletes, and nothing for a clean branch; `squash` onto main's tip asks `squash_failed` and leaves HEAD alone. can fail: three mutants, each red alone: `fork_point` always returns the tip, `reverts` returns nothing, the squash ancestor guard turned off.
- [x] Bug 3: a worktree child whose own scope copy has the design box open, main's copy has it ticked: the real `Run.plan` prints `queued: 4. Thing`. can fail: the `plan_in` call at plan time removed, the plan says `nothing to run`, red.
- [x] Bug 4 (fixed in #79, `80b48f2`): `test_plan_copy_kept` passes on this branch. can fail: the set aside `git checkout` of the plan copy removed, the update returns False, red.
- [x] Bug 5: a call that lists its own "Learn this first" option gets it once, last (`TestLearnOnce`, a real `wf run` with a fake claude). can fail: the filter line removed, the options carry it twice, red.
- [x] Bug 6: real `wf run <repo>` on a scratch repo (no `-y`, no tty, so no call starts): prints `warning: 1. Fix things: tagged auto, not queued: needs a ticked (spec) box`, no warning for the queued feature or the feature not tagged auto. can fail: the warning line's filter set to nothing, no warning, red.
- [x] Bug 7: page and passing report committed, the page copied out, changed, and copied back with `cp` (newer date, same bytes): no problem. A real edit with the same newer date: `older than the file`. can fail: `content_time` not used, the restored page parks, red.
- [x] Bug 8: a link chain `a/b/c/l -> ../../../q`, `m -> a/b/c/l/../../..` is refused with `a symlink leaves the clean copy: m`; a normal tree with an inside link, a nested folder and an executable still copies whole. can fail: the realpath pass removed, the chain is accepted, red; the parent folder check removed, `test_parent_link` red.
- [x] Retry line: a `VERIFY FAIL: develop` then "try again" runs `/develop a -- the last /check verify found ...` with the verify text, then `/check verify a` (`TestVerifyRetryRun`, real `wf run` with a fake claude). can fail: `rebuild` never set, the retry runs verify again, red.
- [x] Whole suite: `python3 runner/tests/fast.py` ran 1061 tests, 0 failed.

## Coverage
- Bugs 1 to 8 and the retry line: all met. None dropped.
