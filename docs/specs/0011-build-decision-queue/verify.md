# Verify: Build queue and decision queue · spec 0011 · updated 2026-10-12
_Steps derived from spec 0011 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [x] `python3 -B -m unittest discover -s runner/tests` -> all pass                                   -> AC-2, AC-3, AC-7, AC-8, AC-10, AC-16 to AC-19
- [x] `python3 -B -m unittest test_queue.TestDoneWhen` (in `runner/tests`) -> first feature parks `blocked`, second ends `feature_done`, one Park record in `queue.json`, mode 0600, exit 6 -> AC-8, AC-9, AC-10, AC-19
- [x] `python3 -B -m unittest test_queue.TestQueueRules test_queue.TestSections test_queue.TestEpicSplit` -> only the tagged feature with every `(spec)` box ticked is queued, twins skip `ambiguous_feature`, a comment edit changes the section hash -> AC-2, AC-3
- [x] `python3 -B -m unittest test_queue.TestTreeRule test_queue.TestParkMemory` -> `skip: 2. B: dirty with parks`, a section edit and a higher `--budget` clear a park, `call_error` writes no record -> AC-3, AC-7, AC-10
- [x] `python3 -B -m unittest test_queue.TestCapsPerFeature test_queue.TestStateFile test_queue.TestExit` -> per feature `--max-calls` and debug count, `queue_unreadable` leaves the file as is, a failed write stops `internal_error` -> AC-16, AC-17, AC-19

- [x] `python3 -B -m unittest test_queue.TestDecisionMoveOn test_queue.TestAcrossRuns` -> a question ends its feature `open:`, the next feature runs, the phone reply resumes the first with `--resume s-1`; the record is still in `queue.json` during the resume and gone after; an open record from an earlier run is answered and resumed by the next run; a stale or twice failing resume is dropped `stale:` -> AC-7, AC-11, AC-12, AC-13, AC-15
- [x] `python3 -B -m unittest test_run.TestParking` -> no counted call left parks `max_calls` with no id and no ping; the end wait runs out `queue done: 0 done, 0 parked, 1 open` with the record kept; Ctrl C in the end wait exits 130 -> AC-11, AC-15, AC-16

## Value sourcing
- [x] Queue: tag a feature `· auto-merge`, or tick its `(spec)` box `· skipped`; `wf run <repo>` (no `-y`, no tty) prints no `queued:` line for it -> AC-2
- [x] Section hash: edit only a comment inside a parked feature's section; the next plan shows `queued:` instead of `parked:` -> AC-3
- [x] Cap park: a `budget` park with `cap` 1 shows `parked:` under `--budget 1` and `queued:` under `--budget 1.5`, and the plan alone leaves the record -> AC-3
- [x] Tree rule: `git status` failing (a folder that is not a repo) reads dirty, `run.dirty` returns True -> AC-7
- [x] Exit code: a run that leaves a Park record exits 6 even when the other feature is `feature_done` -> AC-19
- [x] Decision id: drawn inside the `queue.json` transaction; a second question in the same run never reuses an id in the file or in `run.json` `decisions` -> AC-11
- [x] Poll cursor: a run that starts with an open record polls `since=<asked as unix seconds>`; a run with none polls from its first ping id; a message id listed in a record's `pings` or `acks` never counts as a reply (`ignored` stays 0) -> AC-12
- [x] Resume source: the resume call carries the record's `session_id`, `command` and the answer sentence, and the asking call's `last_box` and `test_base` (read from the record's `run` folder when the question came from an earlier run) -> AC-13
- [x] Stale: change the record's `branch`, or delete the feature heading, after the reply; the plan shows `stale: <id> <feature>` and the feature starts fresh with no `--resume` -> AC-13
- [x] End wait budget: `--max-wait 0.0001` ends the run `queue_done` within a few polls, `waited_s` grows, `--max-hours` is not charged -> AC-15

## Manual (AC-22, after all build steps)
- [x] The four checks of AC-22 on the real claude and your phone · waits on you -> AC-22

Run 2026-10-12 from a normal session against the real `claude` (2.1.296) and the real ntfy topic, the user answering on the phone. Scratch repos with `**Autopilot:** allowed`, `· auto` features with a ticked `(spec)` box, a work branch, isolated `XDG_CONFIG_HOME` / `XDG_STATE_HOME` with the ntfy config copied in, `wf allow` per repo. Caps `--budget 3 --call-timeout 20 --max-calls 6 --max-wait 0.5`. About 4 USD total on the subscription.

1. PASS. Bare `wf run -y` over trusted `a1` (work) and `d4` (main). `parked: 1. Park test: blocked: test park` with a clean tree, then `2. Hello file` built, `/sync`, `done: 2. Hello file`, `queue done: 1 done, 1 parked, 0 open`, exit 6. `run.json` features: `blocked`, `feature_done`; `queue.json` holds one Park (`blocked`, `test park`, `cap` null). A first attempt parked feature 2 `denied` because its step text did not say to tick the box (the call committed `hello.txt` and claimed there was no scope); the step text was the probe's fault, rerun with "tick this Build it box".
2. PASS. `wf run b2 -y`: call 1 ended `DECISION NEEDED:` with two `OPTION:` lines, `waiting: h8dv`, ping on the phone, `open: h8dv 1. Color file`, then `2. Hello file` ran (call 2, 12:38:33). The phone tap was polled after call 2 ended: `answered: h8dv blue (phone)` at 12:39:26, then `(resume h8dv)` as call 3. Calls 1 and 3 share `session_id` 21a4b31d-32c5-4b7a-8747-8fe7ba996a82; `decisions[0].resumed_in` 3, `queue.json` empty after. Both features then parked `denied` on the same step text slip as check 1's first attempt (no box tick), which AC-22 (2) does not cover.
3. PASS. `wf run c3 -y`: `open: jqfo`, SIGINT in the end wait: `stopped: interrupted`, exit 130, `wf queue` still shows `open: jqfo`. The next `wf run c3 -y` printed `open: jqfo` in its plan, re-pinged with no `warning: re-ping` line, and the user tapped the new `jqfo` ping: `answered: jqfo blue (phone)`, `(resume jqfo)` with the first run's `session_id` f5e6aff7-15cb-4d66-a056-3e14695bde83, `/sync`, `done: 1. Color file`, exit 0, `queue.json` empty, `color.txt` committed as `blue`.
4. PASS. In check 1's bare run, `d4 on main, 0 changes` / `skip: branch: main, switch to a work branch first` while `a1` ran.

## Acceptance-criteria coverage
- AC-2, AC-3, AC-7 (one repo), AC-8, AC-10, AC-11, AC-12, AC-13, AC-15, AC-16, AC-17, AC-18 (repos, features, Call feature, decisions with `resumed_in`), AC-19: Commands and Value sourcing above.
- AC-1, AC-4 to AC-6, AC-9, AC-14, AC-20, AC-21: `test_queue.TestAcrossRepos`, `TestNestedRepo`, `TestReping`, `TestQueueCommand`, `TestUnpark`, plus live in AC-22 (bare run over two trusted repos, `skip: branch`, the plan, the re-ping) and a live `wf unpark` (ambiguous exit 1, substring, all, `nothing parked`).
- AC-22: Manual above, all four checks passed 2026-10-12.

`/check verify` 2026-10-12: PASS. Full suite 271 tests OK; the named classes above 43 tests OK; value sourcing run live through `wf queue` and `wf run` without `-y` on a scratch repo with hand written `queue.json` records (auto-merge and `· skipped` not queued, `parked:` vs `queued:` under `--budget 1` and `1.5` with both records kept, a comment edit turns `parked:` into `queued:`, `stale: ab12` for a branch mismatch, `run.dirty` True outside a repo).
