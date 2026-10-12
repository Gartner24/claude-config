# Verify: Build queue and decision queue · spec 0011 · updated 2026-10-12
_Steps derived from spec 0011 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [ ] `python3 -B -m unittest discover -s runner/tests` -> all pass                                   -> AC-2, AC-3, AC-7, AC-8, AC-10, AC-16 to AC-19
- [ ] `python3 -B -m unittest test_queue.TestDoneWhen` (in `runner/tests`) -> first feature parks `blocked`, second ends `feature_done`, one Park record in `queue.json`, mode 0600, exit 6 -> AC-8, AC-9, AC-10, AC-19
- [ ] `python3 -B -m unittest test_queue.TestQueueRules test_queue.TestSections test_queue.TestEpicSplit` -> only the tagged feature with every `(spec)` box ticked is queued, twins skip `ambiguous_feature`, a comment edit changes the section hash -> AC-2, AC-3
- [ ] `python3 -B -m unittest test_queue.TestTreeRule test_queue.TestParkMemory` -> `skip: 2. B: dirty with parks`, a section edit and a higher `--budget` clear a park, `call_error` writes no record -> AC-3, AC-7, AC-10
- [ ] `python3 -B -m unittest test_queue.TestCapsPerFeature test_queue.TestStateFile test_queue.TestExit` -> per feature `--max-calls` and debug count, `queue_unreadable` leaves the file as is, a failed write stops `internal_error` -> AC-16, AC-17, AC-19

## Value sourcing
- [ ] Queue: tag a feature `· auto-merge`, or tick its `(spec)` box `· skipped`; `wf run <repo>` (no `-y`, no tty) prints no `queued:` line for it -> AC-2
- [ ] Section hash: edit only a comment inside a parked feature's section; the next plan shows `queued:` instead of `parked:` -> AC-3
- [ ] Cap park: a `budget` park with `cap` 1 shows `parked:` under `--budget 1` and `queued:` under `--budget 1.5`, and the plan alone leaves the record -> AC-3
- [ ] Tree rule: `git status` failing (a folder that is not a repo) reads dirty, `run.dirty` returns True -> AC-7
- [ ] Exit code: a run that leaves a Park record exits 6 even when the other feature is `feature_done` -> AC-19

## Manual (AC-22, after all build steps)
- [ ] The four checks of AC-22 on the real claude and your phone · waits on you -> AC-22

## Acceptance-criteria coverage
- AC-2, AC-3, AC-7 (one repo, no decisions yet), AC-8, AC-10, AC-16, AC-17, AC-18 (repos, features, Call feature), AC-19: Commands and Value sourcing above.
- AC-1, AC-4 to AC-6 across repos, AC-9 `guard_changed` split, AC-11 to AC-15, AC-20, AC-21, AC-22: not built yet (milestones 2 to 5).
