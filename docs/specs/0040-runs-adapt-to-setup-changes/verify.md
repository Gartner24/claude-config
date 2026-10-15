# Verify: runs adapt to setup changes · spec 0040

Run on 2026-10-14 against `wf run` itself (the runner process, a fake `claude` and a local fake Telegram bot, as the
suite drives it), plus a real shallow `git clone`. Each step was turned red by the break named in its `can fail` note
(the break was put into `runner/run.py`, only the step's own check was run, then the file was restored from a copy).
A real `claude -p` run was not used: in the sandboxed session it reports Not logged in.

## Commands (from `runner/tests`, `P=../../docs/specs/0040-runs-adapt-to-setup-changes/probes`)
- [x] V1 `python3 -B -m unittest test_telegram.TestRunChannel.test_switch_while_waiting` -> telegram.json written while the run waits on ntfy: the log says `phone channel now Telegram, open questions sent again there` once, the question goes out again on the bot, and a tap there answers it -> AC-1. can fail: the run never rechecks the channel (`recheck_channel` returns early every time).
- [x] V2 `python3 -B $P/ac1_extra.py .` -> an invalid telegram.json in the middle of the run logs `phone channel kept: no_telegram: chat_id must be an integer, ...`, sends nothing to the bot, and a valid file written later switches once -> AC-1. can fail: the refused file is swallowed with no `kept` line.
- [x] V3 `python3 -B -m unittest test_swap_take.SwapTake.test_write_deny_park_retaken` -> an edit the run's own guard denied parks `denied` with `denied_path`, a taken setup drops that deny, the log says `retaken 1. Loop: <path> no longer denied`, the question goes stale and the feature finishes in the same run -> AC-2. can fail: `freed()` never frees a `denied_path` park.
- [x] V4 `python3 -B $P/ac2_extra.py .` (test_no_path_outside_guard) -> an Edit denial on a path the guard does not deny parks with no `denied_path` -> AC-2. can fail: `denied_path` recorded for any denial.
- [x] V5 `python3 -B -m unittest test_swap_take.SwapTake.test_text_block_retaken_once` -> a block stated only in text is retaken once after a setup is taken in the same run, `retaken 1. Loop: the setup changed` -> AC-2 amendment. can fail: the same run setup count never frees it.
- [x] V6 `python3 -B -m unittest test_swap_take.SwapTake.test_text_block_no_loop` -> blocked again after its retry: 2 calls, one `retaken` line -> AC-2 amendment. can fail: `setups_seen` recorded as 0, so it loops.
- [x] V7 `python3 -B $P/ac2_extra.py .` (test_earlier_run_text_block) -> a text block from an earlier run stays parked with no newer setup (still 1 call), and is retaken (`the setup changed`) once a swaps.jsonl line exists -> AC-2 amendment. can fail: the earlier run check never frees it.
- [x] V8 `python3 -B $P/ac2_extra.py .` (test_queue_keeps_park) -> with the deny gone, `wf queue demo` (no guard built) still shows `parked: 1. Loop: denied` -> AC-2. can fail: no guard counts as freed.
- [x] V9 `python3 -B $P/ac3.py ..` -> a real `git clone --depth 4 --no-single-branch -b work`, local main from origin/main with no common commit: the base is beta's tip, only `Work1.tsx` and `Work2.tsx` count, `test_base` gives the same base, upstream `origin/work` is skipped -> AC-3. can fail: no fallback to `nearest_base` (every frontend file counts).
- [x] V10 `python3 -B -m unittest test_design.TestChanged.test_nearest_base` -> the pushed namesake, a branch holding HEAD and a farther branch are not picked -> AC-3. can fail: the namesake skip removed (red), and separately the branch holding HEAD skip removed (red).

## Acceptance criteria coverage
- AC-1: V1, V2 · AC-2: V3 to V8 · AC-3: V9, V10

Suite: `python3 runner/tests/fast.py`, 751 tests, 0 failed.
