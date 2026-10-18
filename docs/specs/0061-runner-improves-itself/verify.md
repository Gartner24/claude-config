# Verify: runner that improves itself · spec 0061 · updated 2026-10-17
_Steps derived from spec 0061 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
Run each with a scratch state folder: `export XDG_STATE_HOME=$TMPDIR/v61 CLAUDE_CONFIG_DIR=$TMPDIR/v61-claude`.
- [x] Put 12 fixture runs in `$XDG_STATE_HOME/wf/runs/` (an Edit denial of one path in 3 of the last 10, a park reason in 3, a `call_timeout` on `/develop` in 3, something else in 2), run `python3 runner/wf.py insights` -> the 3 of 3 lines say HOT, the 2 of 10 line does not; `insights/inbox.md` gets 3 proposals naming the tool and path, never a command text -> AC-2, AC-3, AC-4
- [x] Run `python3 runner/wf.py insights` again -> 1 new proposal (the 4th HOT finding), then 0 on a third run, and 0 after emptying `inbox.md` by hand -> AC-4
- [x] Add a run folder whose `run.json` has `"ended": null` -> not in `insights/history.jsonl`; set `ended` and rerun -> appended once; delete the folder and rerun -> still in history -> AC-2
- [x] Write `{not json` as a run's `run.json` -> the print says `1 unreadable run.json skipped` -> AC-2
- [x] `python3 runner/wf.py report --hook` with unseen proposals -> `wf proposals: N new (<inbox path>)` and no proposal text; after `python3 runner/wf.py insights --seen` -> no line; after a new proposal -> the line again; with a held repo lock or `WF_RUN=1` -> no line -> AC-6
- [x] Put `<h1>Top</h1><script>x()</script>` plus 5,000 characters in `$CLAUDE_CONFIG_DIR/usage-data/report.html` -> `wf insights` prints a `from /insights (data):` section of at most 4,000 characters with no tags and no `x()`; the inbox does not change; without the file no section -> AC-7
- [x] List every file under a temp HOME before and after `wf insights` and `wf insights --seen` -> every new or changed file is under `$XDG_STATE_HOME/wf/insights/` -> AC-1, AC-8
- [x] Make `insights.update` raise inside a real `wf run` end (or `python3 -c` calling `insights.end_of_run` with it patched) -> one `warning: insights: ...` line, exit code unchanged; `run.py` calls it before `prune_runs` -> AC-5
- [x] With a fake `~/.claude` (HOME in a temp folder): `names.txt` holding a name, a session in an allowed project typing that name, an `sk-` key, an email and a 40 character hex run, and a second project not on `history-allow.txt` -> `python3 claude-home/skills/improve-my-system/extract.py` writes one `project-01.jsonl` holding none of them, no subagent words, no tool results -> AC-9
- [x] Remove `history-allow.txt`, or `names.txt`, or add `.git` to the temp HOME -> extract exits 1 with its reason and writes nothing -> AC-9
- [x] `extract.py --propose a b c d` -> 3 lines added to the runner inbox, a repeat adds 0, the hook counts them -> AC-9
- [x] `python3 -B runner/tests/fast.py test_insights` -> OK -> AC-10

## UI / manual
- [ ] Run `/improve-my-system` by hand in a session after writing `~/.claude/private/history-allow.txt` -> `~/claude-improve/report.md` has every listed section, each finding with 3 or more sessions, dates and a quote, a 15 line summary, and it asks before changing any file -> AC-9 · left to the box: Write `~/.claude/private/history-allow.txt` with your own project folders (AC-9)

## Acceptance-criteria coverage
- AC-1: step 7 · AC-2: steps 1, 3, 4 · AC-3: step 1 · AC-4: steps 1, 2 · AC-5: step 8 · AC-6: step 5 · AC-7: step 6 · AC-8: step 7 · AC-9: steps 9 to 11 and the manual step · AC-10: step 12

## Results 2026-10-17 (`/check verify`)
Run by one scratch driver against the real `runner/wf.py` and `extract.py` as subprocesses, with HOME, `XDG_STATE_HOME` and `CLAUDE_CONFIG_DIR` in a temp folder. Every step was also run against a copy of the code with one line broken; each "can fail" below names that break, and each went red.

1. PASS. `wf insights` printed `denied Edit `/x/locked.md`: 3 runs HOT`, `park verify_failed: 3 runs HOT`, `timeout /develop: 3 runs HOT`, `park call_timeout: 3 runs HOT`, `park blocked: 2 runs` (no HOT), and `park debug_touched: 1 runs` (3 runs total, only 1 inside the last 10). The inbox got 3 proposals; the Edit one names the tool and path, and the denied command text (`SECRETCMD`) appears in neither the print nor the inbox. Medians skip nulls: `/check` cost printed `?`, `/develop` duration median 90 with the null run left out. can fail: HOT threshold 2 instead of 3 (`blocked` turns HOT, 4 proposals).
2. PASS. Second run 1 new, third 0, after emptying `inbox.md` 0 (`proposed.json` remembers). can fail: same HOT mutant, second run gave 2.
3. PASS. History lines for the run: 0 while `ended` was null, 1 after it ended (two reruns), 1 after its folder was deleted. can fail: the `ended is None` skip removed, so the live run was appended at once.
4. PASS. `wf insights: 13 runs in history, 0 new, 1 unreadable run.json skipped`. can fail: the corrupt counter not incremented (printed 0).
5. PASS. Hook printed `wf proposals: 4 new (<tmp>/.local/state/wf/insights/inbox.md)` with no proposal text; nothing after `--seen`; `wf proposals: 1 new (...)` after 3 new runs with a new Write denial; nothing with a repo lock held or with `WF_RUN=1`; the line back after the lock went. can fail: `unseen()` ignoring `seen.json` (line stayed after `--seen`), and the lock and WF_RUN check removed (line printed under the lock).
6. PASS. Section of exactly 4,000 characters starting `Top a b`, no `<`, no `x()`; inbox byte identical; no section once the file was removed. can fail: the script strip regex broken (`x()` leaked).
7. PASS. Across `wf insights` and `wf insights --seen` the only changed files under the temp HOME were `.local/state/wf/insights/history.jsonl` and `seen.json`; the fake `.claude/settings.json` untouched. can fail: an append to a file in the live `.claude` (caught as `.claude/x` outside the fence).
8. PASS. Patched `update` raising `disk gone`: stdout `warning: insights: disk gone` then `after`, exit 0. In `run.py`, `report.end_of_run(self)` comes before `insights.end_of_run()`, which comes before `prune_runs`. can fail: the except re raising (exit 1, no warning).
9. PASS. One file `project-01.jsonl`: `{"project": "[REDACTED]", "session": "s1", "date": "2026-10-15", "messages": ["fix [REDACTED] deploy with [REDACTED] and mail me at [REDACTED] hash [REDACTED] ok"], "tools": ["Bash"]}`. None of the name (any case), key, email, hex run, tool input, tool result, sidechain line, subagent file or the project off the allow list. can fail: the email redaction removed (the address leaked).
10. PASS. Each of the three exits 1 with its reason on stderr (`history-allow.txt is missing`, `names.txt is missing`, `claude-improve is inside a git repo`) and no `claude-improve` folder is created. can fail: `in_git` always false (the `.git` case ran).
11. PASS. `propose: 3 added`, repeat `propose: 0 added`, hook count 0 -> 3, the 4th item kept out, a private name in an item redacted in the inbox. can fail: the `[:3]` cap removed (4 added).
12. PASS. `Ran 10 tests in 0.8s, 0 failed`. can fail: not mutated here; the test file's own mutation checks belong to `/test`.

Whole suite (`python3 runner/tests/fast.py`): FAIL, 982 tests, 2 failed, so the Verify box stays open. `test_run.TestParking.test_wait_not_counted` exited 6 because its 0.0005 hour (1.8 second) run limit passed before the run finished; `test_run.TestRecordAndSignals.test_internal_error` found no `fakes/inhibit.json`. Both pass when run alone, both are timing based, and neither reaches `insights` before the point where it failed, so they look like load flakes, not this feature. They go to `/debug`.

## Results 2026-10-17, second run (`/check verify`, after commit ea39f06)
A fresh copy of the same driver ran all 11 command steps against the real `runner/wf.py` and `extract.py`: 12 of 12 checks PASS (step 1 also checks that medians skip nulls). The same outputs as above: 3 HOT plus `park call_timeout` HOT, `park blocked: 2 runs`, 3 proposals, no `SECRETCMD`; 1, 0, 0 new on reruns; history 0, 1, 1; `1 unreadable run.json skipped`; hook line `wf proposals: 4 new (...)`, gone after `--seen`, back at 1 new, silent under the lock and `WF_RUN=1`; a 4,000 character section with no tags; only `insights/history.jsonl` and `seen.json` changed; one warning line and exit 0; the extract leaks nothing; three refusals with exit 1 and no folder; `propose: 3 added`, then 0.
Each step was rerun against a copy with one line broken, and each went red: HOT 2 (steps 1, 2), the `ended` skip removed (3), the corrupt counter (4), `unseen()` ignoring `seen.json` and the lock check removed (5), the script strip regex (6), a write into `.claude` (7), the except re raising (8), the email redaction (9), `in_git` false (10), the `[:3]` cap (11). Step 12: `test_insights` gives 10 OK, and 2 of its tests fail on the HOT 2 copy.
Whole suite (`python3 runner/tests/fast.py`): `Ran 982 tests in 101.1s, 0 failed`.
The manual step is left to the box: Write `~/.claude/private/history-allow.txt` with your own project folders (AC-9).

Noted for review, not a spec failure: the token pattern `[A-Za-z0-9+/=_-]{40,}` in `extract.py` also matches long paths, because `/` is in the class. Any allowed project path with a 40 character run of those characters (no dot in it) prints as `[REDACTED]` in the `project` field and in messages, so the report may not be able to name projects. The fixture's project path showed this.
