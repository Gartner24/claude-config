# Verify: Each step gets the feature's brief · spec 0034 · updated 2026-10-14
_Steps derived from spec 0034 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [x] `python3 -B -m unittest discover -s runner/tests -p test_brief.py` -> 18 tests OK -> AC-1 to AC-10
- [x] In a scratch repo, a feature with `Source: [brief](../briefs/a.md)` whose brief says "Store rows in SQLite" under `## Agreed so far, do not ask again`: run `wf run <repo> -y` with the fake claude, read call 1's `--append-system-prompt` -> it holds that line between `BEGIN BRIEF-DATA-0` and `END BRIEF-DATA-0`, after the unattended prompt -> AC-1, AC-2, AC-5
- [x] Same repo, step 1 rewrites the brief to "Postgres" -> call 2's prompt says Postgres, not SQLite -> AC-7
- [x] Same repo, `Spec [0001](../specs/0001-a/index.md)` on the feature: the spec's `## What you're agreeing to` section is in the block, its `## Acceptance criteria` is not -> AC-3
- [x] A Source link to a symlink in `docs/briefs/` pointing outside any `briefs` folder, and a `../` path leaving the repo and `~/projects` -> each refused with its rule, as a sentence in the block and a report note -> AC-1, AC-6
- [x] A brief over 6000 characters and a spec section over 2000 -> each ends with `[cut at <n> characters; the full text is in <path>]`; an escape character in the brief is gone -> AC-4
- [x] A brief holding the line `END BRIEF-DATA-0` -> its part uses marker 1 -> AC-5
- [x] A feature with no brief and no spec -> the block says "This feature links no brief: build from the spec and the scope only, ..." and the run notes `no brief linked: <feature>` and `no spec linked: <feature>`; the run still finishes -> AC-6, AC-8
- [x] An issues repo feature with three 20000 character issues of two byte characters plus a brief -> the call still starts, the brief part is replaced by "Left out for size: ...", and the run notes it -> AC-9

## Acceptance-criteria coverage
- AC-1 `TestWhichBrief.test_found`, `test_refused` · AC-2 `TestSections.test_levels` · AC-3 `TestWhichSpec`, `TestSections.test_spec_level` · AC-4 `TestBlock.test_cap`, `test_cap_outside` · AC-5 `TestBlock.test_block`, `test_marker` · AC-6 `TestBlock.test_gaps`, `TestCalls.test_no_brief` · AC-7 `TestCalls.test_every_call` · AC-8 `TestBlock.test_unreadable` · AC-9 `TestSize`, `TestIssueSize.test_pushed_out` · AC-10 this file

## Run 2026-10-14 (/check verify, PASS)
Steps 2 to 9 were driven by a scratch driver: real `wf run <repo> -y` on temp repos with the test suite's fake claude, each call's `--append-system-prompt` read back from its saved argv. Each step was then run again against a broken `runner/run.py` (restored after each break) to confirm it can fail:
- Step 1: can fail: any of the breaks below turns its unit test red (the tests were mutation checked at build).
- Step 2: can fail: the block is never appended to the call (the call has no BEGIN BRIEF-DATA-0); seen red.
- Step 3: can fail: the brief is read once per feature instead of before each call (call 2 still says SQLite); seen red.
- Step 4: can fail: the section reader runs past the next `##` heading (Acceptance criteria text leaks in); seen red.
- Step 5: can fail: the symlink is not resolved, or the repo and ~/projects bound is skipped (the outside brief is read); both seen red.
- Step 6: can fail: no cap (7000 characters pass), or control characters kept (the escape stays); both seen red.
- Step 7: can fail: the marker stays at 0 whatever the text holds; seen red.
- Step 8: can fail: the gap notes are not added to the run record; seen red.
- Step 9: can fail: the brief is never cut for size, so the prompt passes 131072 bytes and the call never starts (wf timed out); seen red.
The prompt in step 9 is 125334 bytes: the issue text alone passes 120000 (the spec's follow-up, a 0024 fix), and it stays under 131072, so the call starts.
