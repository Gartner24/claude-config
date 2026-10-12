# Verify: failure and park policy · spec 0008 · updated 2026-10-12

## Probes before accept (spec gate)

- [x] Check 1, denial shape: `rg -o '"permission_denials":\[\{.{0,400}' ~/.local/state/wf/runs`. Result: entries hold `tool_name`, `tool_use_id`, `tool_input`; no reason field. Confirmed on claude 2.1.296 run records. -> AC-5
- [x] Check 2, denial reason: `rg -l <tool_use_id> ~/.claude/projects` found the session transcript; its line for that id holds `toolUseResult: "Error: PreToolUse:Bash hook error: SHAPE: ..."`. Confirmed. -> AC-5
- [ ] Check 3, usage limit in `claude -p` JSON: UNCONFIRMED. Run this the next time a session or weekly limit is hit, then paste the output here:
  `env -C "$(mktemp -d)" claude -p "say ok" --output-format json`
  Pass: the output is a failed result (`is_error` true or a non success subtype, or a nonzero exit) and its `result`, subtype or stderr matches the AC-8 limit pattern, and the reset part matches the reset pattern. Anything else: back to `/architect`. -> AC-8, AC-11

## Manual checks after the build (real claude)

- [ ] Check 4: a scratch repo whose `/develop` box asks for `sudo pacman -S <pkg>` parks `blocked` with the package in the detail. -> AC-4
- [ ] Check 5: a scratch feature with a deliberately failing behavior: the real `/check verify` call ends with a `VERIFY FAIL:` line and `wf` runs `/debug`. -> AC-2
- [ ] Check 6: inside a call, `env | grep -c -E '_API_KEY|SECRET'` prints 0 and reading `~/.aws` fails. -> AC-7

## Commands (added by /develop 2026-10-12)

_Steps derived from spec 0008 acceptance criteria and its Value sourcing table. `/check verify` runs these; `/test` locks the durable ones._

- [ ] `python3 -B -m unittest discover -s runner/tests` -> all pass (187 at build time) -> AC-1 to AC-10
- [ ] `python3 -B -m unittest test_park.TestParkSets test_park.TestParkPrint` (from `runner/tests`) -> every reason in exactly one set; `parked:` / `stopped:` prefix; `parked` true, false or null; exit 6 for both, 130 for interrupted -> AC-1
- [ ] `test_park.TestVerifyLoop` -> verify, debug, verify, debug, verify, then `verify_failed: 2 debug attempts made`; the debug command is `/debug a -- the last /check verify failed:` plus the last 1500 characters, cleaned, newlines kept; `develop` (or any other value) parks at once with the marker and 5 lines before it -> AC-2 (value rows: debug command, failure text)
- [ ] `test_park.TestDebugGuard test_park.TestTouched` -> spec edit, spec add, test delete, skip added, test definition removed, new skipped test file, committed spec edit each park `debug_touched` naming the path; a rename plus a new test, and earlier calls' `verify.md` and tests, pass -> AC-3 (value rows: guarded file list, before and after, specs folder, added lines)
- [ ] `test_park.TestBlocked` -> `BLOCKED:` parks with its text and wins over `DECISION NEEDED:`; no decision recorded -> AC-4
- [ ] `test_park.TestDenials` -> two denials with reasons from a `CLAUDE_CONFIG_DIR` transcript; park `denied` on the first non AskUserQuestion; null reason without a transcript; a call that progressed keeps going -> AC-5 (value rows: denial tool, input, park detail, reason)
- [ ] `test_park.TestRetry` and `test_run.TestClassify` -> one retry with `retry_of`, two failures park `call_error`, a resume retries with the same id and prompt, `error_max_turns` never retried, a branch change stops before the retry, spawn failure stops `spawn_failed` -> AC-6
- [ ] `test_park.TestPaidEnv` and `test_run.TestHappyPath.test_argv` -> paid names absent from call and resume env, `CLAUDE_CODE_OAUTH_TOKEN` and `PATH` kept; `~/.aws`, `~/.config/gcloud`, `~/.azure` in `denyRead` and as `Read` denies -> AC-7
- [ ] `test_park.TestLimit test_park.TestParseReset` -> sleeps to 2 minutes after the reset (1320 s at 6:00 for 6:20 Bogota), reruns the same command, limited call not counted, 1 minute past sleeps 120 s, second limit / far reset / no reset / unknown zone stop `usage_limit`, Autopilot off and Ctrl C during the sleep stop, sleep not counted toward `--max-hours`; a reset in another zone gives the right offset -> AC-8 (value rows: reset time, wait cap, max calls, max hours)
- [ ] `test_park.TestTrust` -> `wf allow` twice leaves one real path, 0600 file in a 0700 folder under `XDG_CONFIG_HOME`; unlisted, missing, broken and non string files refuse `untrusted` exit 5 with no lock and no run folder -> AC-9 (value row: trust)
- [ ] `test_park.TestRecord` -> run and call fields after a retry, a verify fail and a debug call -> AC-10

## Acceptance criteria coverage

- AC-1 to AC-10: the Commands steps above. AC-11: checks 3 to 6 above, on the real claude (they wait on you).
- Note: the spec's "reset 30 hours away" scenario cannot happen with a time of day reset (at most about 24 hours ahead); the test uses a reset 7h20m away.
