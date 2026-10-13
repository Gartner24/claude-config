# Verify: Morning report · spec 0018 · updated 2026-10-13
_Steps derived from spec 0018 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [x] `python3 -B -m unittest discover -s runner/tests` → all green, `test_report` included → AC-1 to AC-8
- [x] `env -C runner/tests python3 -B -m unittest test_report.TestEndOfRun.test_single` → a run with one built, one parked, two live boxes and one other waiting box writes report.txt with the head, `built:`, `parked: ...: blocked: test park`, `live: 3. C: 2 step(s)`, `yours: 3. C: Check the phone`, `next: wf finish, then review and merge: two`; run.json says `"report": "sent"`; exactly one note titled `wf report` reaches the fake ntfy, its parked line without the detail → AC-1, AC-2, AC-3, AC-4
- [x] `env -C runner/tests python3 -B -m unittest test_report.TestEndOfRun.test_crash_and_failed_send` → an `internal_error` run still sends with `stopped internal_error (crash)`; three failing POSTs print `warning: report: ...`, record `failed: ...` and keep exit 6 → AC-1, AC-3
- [x] `env -C runner/tests python3 -B -m unittest test_report.TestEndOfRun.test_interrupted_sends` → a Ctrl C run exits 130 and still records `"report": "sent"` → AC-1, AC-4
- [x] `env -C runner/tests python3 -B -m unittest test_report.TestParent` → both children record `"parent"`, the parent sends one note whose lines end with each repo label and whose next line is `review and merge: <label a>, <label b>` → AC-1, AC-2
- [x] `env -C runner/tests python3 -B -m unittest test_report.Unit.test_cap_and_scrub` → 30 items give 12 lines, built lines dropped first, `+21 more, run wf report` before `next:`; nine long yours lines stay under 1000 characters; a block list hit turns only that feature into `feature` → AC-4
- [x] `env -C runner/tests python3 -B -m unittest test_report.Unit.test_hook_and_seen test_report.Unit.test_killed_line` → the hook prints the header plus report only when unseen, nothing under `WF_RUN` or a held lock, nothing after `--seen`, again after a newer report; the killed run line shows for a dead pid folder newer than report.txt with no `ended`, and not for an ended record, a live pid, an older folder, or one report.seen names → AC-5, AC-6
- [x] With an empty state folder: `XDG_STATE_HOME=$(mktemp -d) python3 runner/wf.py report` → prints `no report yet`, exit 0; the same with `--hook` prints nothing, exit 0 → AC-5, AC-6
- [x] `grep -n "wf report --hook" settings.json` and `grep -n "wf morning report" rules/runner-handoff.md` → the SessionStart entry runs `/home/santiago/.local/bin/wf report --hook`; the rule says to lead with the report and its next command → AC-7
- [x] `env -C runner/tests python3 -B -m unittest test_resilience.TestFixture` → the e2e script fails with `FAIL: run.json report 'failed: x'` and `FAIL: no report.txt` when either is missing, PASS otherwise → AC-8

## Value sourcing
- [x] Head status and reasons come from each run's `stop_reason`: `test_report.Unit.test_status_and_rows` mixes `internal_error` and `queue_done` and expects `stopped internal_error (crash), queue_done` → AC-2
- [x] Head time is the latest `ended` in local time: `test_report.Unit.test_lines` compares against the record's `ended` converted with `astimezone()`; rerun it with `TZ=Asia/Tokyo` and it still passes → AC-2
- [x] Head counts come from `features[].outcome`: a `waiting` outcome adds no line and no count (`test_lines`) → AC-2
- [x] Head spent is `spent_line()` over all calls: `test_lines` expects `0.50 USD, 15 tokens` from one call of 0.5 USD and 10 + 5 tokens → AC-2
- [x] built, parked, stopped, question lines come from `features[]`: `test_status_and_rows` expects `question k3x9` from the decision id in `detail` → AC-2
- [x] live and yours come from the scope file reread at build time: `test_lines` counts two live boxes, skips the `## Deferred` waiting box, and strips ` · later boxes go on` → AC-2
- [x] no record and not started come from the parent's summary rows: `test_report.Unit.test_parent_rows` expects `no record: ra: exit 5 (ra)` and `not started: rc (rc)`, and skips a row with no work → AC-2
- [x] Repo on the phone is `ntfy.repo_label()`: `TestParent.test_one_note` expects `repo-<sha1>` labels, never the folder names → AC-4
- [x] Send goes to the run's loaded ntfy config: `test_report.Unit.test_deliver` checks title `wf report`, priority 3, tags `[]`, no actions, report.txt mode 0600 and report.seen removed → AC-3, AC-4

## Live (you run these, spec 0019 live steps)
- [ ] `python3 runner/e2e/run.py` → `PASS`, and a `wf report` note on your phone → AC-8
- [ ] `python3 runner/e2e/run.py --parallel` → `PASS`, and one note naming both repos → AC-8

## Acceptance-criteria coverage
- AC-1: unit suite, test_single, test_crash_and_failed_send, test_interrupted_sends, TestParent, test_parent_rows
- AC-2: test_single, test_status_and_rows, test_lines, test_parent_rows, TestParent, value sourcing steps
- AC-3: test_single, test_crash_and_failed_send, test_deliver
- AC-4: test_single, test_cap_and_scrub, test_deliver, TestParent
- AC-5: test_hook_and_seen, test_killed_line, empty state command
- AC-6: test_hook_and_seen, test_killed_line, empty state command
- AC-7: settings.json and rules grep
- AC-8: TestFixture, live e2e steps

## Live runs (wf finish)

- 2026-10-13, Claude Code 2.1.296: `python3 runner/e2e/run.py` PASS
- 2026-10-13, Claude Code 2.1.296: `python3 runner/e2e/run.py --parallel` PASS
