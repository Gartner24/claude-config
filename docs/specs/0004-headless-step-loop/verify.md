# Verify: Headless step loop · spec 0004 · updated 2026-10-11
_Steps derived from spec 0004 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## AC-15 manual checks against the real `claude` (run 2026-10-11, Claude Code on the subscription login)

Scratch repos built by a throwaway script: Python `app.py`, `**Autopilot:** allowed`, Prototype tier, branch `work`, one bare local remote.

- [x] Check 1, budget: `wf run budget -y --budget 0.01` stopped `budget`, exit 6. Real stdout is ONE JSON object (not an array), `"type": "result"`, `"subtype": "error_max_budget_usd"`, `"is_error": true`, `"terminal_reason": "budget_exhausted"`, `"errors": ["Reached maximum budget ($0.01)"]`. AC-6 rules 3 and 4 hold as written; no spec correction needed. Note: the call still cost 0.49 USD, because the cap is checked only after a turn, so `--budget` bounds a call to roughly one turn past the cap, not to the cap itself. -> AC-6, AC-15
- [x] Check 2, decision: `wf run decision -y` (storage engine left open on purpose) stopped `decision_needed: Should greetings be stored in sqlite or postgres?`, exit 6. The call transcript has no AskUserQuestion tool use; the only permission denial was a chained Bash call (your shape hook). -> AC-5, AC-6, AC-15
- [x] Check 3, done when: `wf run feature -y` ran `/develop shout` then `/sync`, ended `done: 1. Shout`, exit 0, with no typing. The box is ticked and `app.shout("a") == "A"` passes. This also proves `--permission-mode auto` works on this plan and model. A second `wf run feature -y` during it was refused `locked: another wf run holds this repo: pid 4102759 since 2026-10-11T07:30:32-05:00`, exit 5. `wf run caps -y --max-calls 1` on a two box feature stopped `max_calls` after one call, exit 6. -> AC-7, AC-8, AC-9, AC-15
- [x] Check 4, push: inside `wf run push -y` the step refused to push on the unattended prompt alone and asked a `DECISION NEEDED:`, so the deny list was not reached. Then two direct `claude -p` calls with the same `--disallowedTools` and no prompt, each asked to push: `git push -u origin work` and `git -C . push origin work` both came back in `permission_denials`, denied. `git for-each-ref` on the bare remote is empty. -> AC-4, AC-15

## Commands
- [x] `python3 -m unittest discover -s runner/tests` -> all green (86 tests, about 17 s) -> AC-1 to AC-14
- [x] `wf run claude-config` in this repo -> `refused: waiting: ...` (feature 2's waiting milestone is first), exit 5, no call -> AC-2
- [x] `wf run --help` through the installed `~/.local/bin/wf` symlink -> shows `--budget`, `--call-timeout`, `--max-calls`, `--max-hours` (the lazy `import run` resolves through the symlink) -> AC-1, AC-8
- [x] `wf run <repo> --max-calls 1.5` and `--budget nan` -> usage error, exit 2 -> AC-8
- [x] In a scratch repo with `**Autopilot:** allowed` on branch `main` -> `refused: branch: main`, exit 5; on a detached checkout -> `refused: branch: detached <sha>` -> AC-2
- [x] Start a run, then Ctrl C during the call -> `stopped: interrupted`, exit 130, no `claude` and no `systemd-inhibit` process left (`pgrep -af systemd-inhibit`) -> AC-12, AC-13
- [x] During a run, `systemd-inhibit --list` shows `wf` holding `idle:sleep:handle-lid-switch` -> AC-13
- [x] After any run, `~/.local/state/wf/runs/<name>-<stamp>-<pid>/run.json` has `ended` and `stop_reason` set, plus `call-NN.json` and `call-NN.stderr` per call; `locks/` and `runs/` are mode 700, the lock file 600 -> AC-9, AC-10

## Value sourcing
- [x] Run feature: the run stops at the feature boundary, never runs the next feature's box (fixture with two features; `/sync` runs instead) -> AC-1, AC-7
- [x] Autopilot mid run: flip the header to `off` during a call -> `stopped: autopilot_off` -> AC-6
- [x] Branch drift: switch branch during a call -> `stopped: branch_changed: work -> other` -> AC-6
- [x] Progress: a call that ticks nothing -> `stopped: no_progress` -> AC-6
- [x] Decision: last `DECISION NEEDED:` line wins, `\r` stripped, control characters removed -> AC-6
- [x] call_error detail: non JSON stdout shows the subtype, the first 200 characters of `result` and the last 5 stderr lines, cleaned -> AC-6
- [x] Elapsed time: `--max-hours` tiny stops `run_limit` before the second call, never during one -> AC-8
- [x] State folder: `XDG_STATE_HOME` moves it; an unwritable one refuses `state_unwritable` -> AC-9

## Acceptance criteria coverage
- AC-1, AC-2: `test_run.TestStart` (incl. `test_allow_list`), `TestHappyPath` · AC-3: `TestStart.test_confirm_cancels`, `TestConfirmLine` · AC-4, AC-5: `TestHappyPath.test_argv`, `TestClassify.test_spawn_error`, check 4 · AC-6: `TestClassify`, checks 1 and 2 · AC-7: `TestHappyPath`, `TestClassify.test_sync_stops`, check 3 · AC-8: `TestCaps`, `TestStart.test_bad_caps`, check 3 · AC-9: `TestStart.test_lock`, `test_second_run_refused`, `test_state_fallback`, check 3 · AC-10: `TestHappyPath`, `TestRecordAndSignals.test_internal_error` · AC-11: `TestHappyPath`, `test_minutes` · AC-12: `TestRecordAndSignals`, `TestSpawnRace` · AC-13: `TestRecordAndSignals.test_inhibitor*` · AC-14: exit codes asserted across all classes · AC-15: the four checks above

## Push rule probe (amendment 2026-10-12, review stack finding M9): OWED

- [ ] `bash docs/specs/0004-headless-step-loop/probes/push-rule.sh` on the real claude: steps 1 and 2 run (one stash, one commit whose message holds "push"), steps 3 to 6 appear under denied commands, the bare remote has 0 branches. Not run yet: this session has no claude login, so you run it with `!`. The unit side is pinned by `test_run.TestHappyPath.test_argv` (the exact `--disallowedTools` string).
