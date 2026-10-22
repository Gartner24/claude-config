# Verify: guard baseline between repos · spec 0025

Run 2026-10-14 on `feat/release-4` (f4eba15). Each step runs the real bare `wf run` (`runner/wf.py`, parent plus one child per repo) on scratch repos in a temp HOME, with the scripted claude and fake ntfy from `runner/tests/test_run.py`. Repo `ra`'s call rewrites a hook script that both repos' guards hash; `rb` starts after it (`--jobs 1`). A real claude call is not part of this check.
To rerun: `python3 -B -m unittest discover -s runner/tests -p test_parallel.py -k TestPlanBaseline -k TestBaselineFile`, and `python3 -B docs/specs/0025-guard-baseline-between-repos/probes/ac4_overnight.py Ac4.test_unanswered_then_next_wf`.

Mutation check: `runner/` is write denied inside a `wf` session, so each mutant was applied to a scratch copy of `runner/`, the named steps run there, then restored and green again.

## Commands
- [x] `test_change_asks_then_accept` -> `[rb] stopped repo rb: guard_changed: <hook> changed after the plan, before this repo started`, then `answered: <id> rb: accept the new setup and go on`, `[rb] done: 1. A`, queue empty, no baseline files left -> AC-1, AC-2, AC-3, AC-4
  can fail: with the `plan_check()` call removed from `run()`, rb builds with no question (mutant `no_call`: red).
- [x] `test_stop_this_repo` -> reply `2`: `answered: <id> rb: stop this repo`, no call made in rb, ra `feature_done`, summary lists both -> AC-3, AC-4
  can fail: same mutant `no_call`, rb makes its call and builds (red).
- [x] `test_swap_asks_nothing` -> the same hook change written to `swaps.jsonl` gives no `guard_changed`, `[rb] done: 1. A`, no queue -> AC-2, AC-5
  can fail: dropping the `accepted_by` filter asks about a wf swap (mutant `no_ledger`: red).
- [x] `test_answers_changed` -> ra's call rewrites rb's `## Standing answers`: `stopped repo rb: guard_changed: standing answers changed after the plan`, no call in rb -> AC-2
  can fail: skipping the `read_answers` comparison lets rb build (mutant `no_answers`: red).
- [x] `test_no_flag_and_missing` -> `wf run rb -y` with no flag and a changed hook asks nothing; `--plan-guard <missing file>` gives `guard_changed: plan baseline unreadable: <path>` -> AC-1, AC-2
  can fail: an unreadable baseline treated as no change (mutant `fail_open`: red).
- [x] `test_files_and_sigint` -> while ra runs, one baseline `<parent pid>-<sha1 of ra>.json`, mode 0600 in a 0700 folder, keys `absent_denied, answers, guarded_files` with the hook in it; after SIGINT the parent exits 130 and the folder is empty -> AC-1
  can fail: the parent's `finally` not removing its files leaves them behind (mutant `no_cleanup`: red, also red in `test_change_asks_then_accept`).
- [x] `TestBaselineFile.test_cases`, `test_unseen_file_is_a_change` -> a 0644 file, another parent's pid, a file outside the state folder, a symlink, empty or malformed JSON all read as None (fail closed); a guarded file the plan never hashed is a change -> AC-2
  can fail: a baseline accepted at any file mode (mutant `trust_any_file`: red).
- [x] `ac4_overnight.py Ac4.test_unanswered_then_next_wf` -> run 1 unanswered: rb exits 6, queue.json holds one decision `reason guard_changed, level repo`, report.txt has `question <id>: (repo): ...`, no call in rb. Run 2 (next bare `wf`, reply `1`): plan shows `open: <id> (repo)`, no second question, `answered: <id> rb: accept the new setup and go on`, `[rb] done: 1. A`, queue empty -> AC-4
  can fail: mutant `no_call` leaves no question in queue.json (red).

## Acceptance-criteria coverage
- AC-1 met (files, mode, name, flag, cleanup after normal end and SIGINT, no flag unchanged) · AC-2 met · AC-3 met · AC-4 met (accept, stop, unanswered kept and resumed next `wf`; "a newer change replaces it" not exercised) · AC-5 met · AC-6 met (tests exist and pass; the spec's own mutation, dropping the AC-2 check, turns the first test red)
