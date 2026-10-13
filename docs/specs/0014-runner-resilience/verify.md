# 0014 verify

## Probes before accept (AC-9), Claude Code 2.1.296, 2026-10-12

- **P1 session id**: `env -C <scratch> claude -p "Reply with the single word ok." --output-format json --session-id 11eecd84-fe72-45bb-9661-86ff635083f5`. Result: JSON `session_id` equals the given uuid, `subtype` `success`. Pass.
- **P2 live transcript**: `claude -p "Use the Bash tool to run: sleep 25. Then reply done." --output-format json --permission-mode auto --session-id 6a0d6c1e-2f4b-4c8e-9a51-3b7d2e9f1c40` in the background; while the call slept, `~/.claude/projects/*/6a0d6c1e-2f4b-4c8e-9a51-3b7d2e9f1c40.jsonl` already held 33 lines, 9 naming the `sleep` call. Pass.
- **P3 usage fields**: the P1 JSON holds `usage` with `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens` (ints), `total_cost_usd`, and `api_error_status: null`. Pass.

## Follow-up probe (waits on you)

- **Outage shape**: at the next real API outage, copy the failed call's `call-NN.json` and the last lines of `call-NN.stderr` from the run folder here. Pass when `api_error_status` is 500 or more, or the text matches `OUTAGE`.

## End to end (build step 9)

- `python3 runner/e2e/run.py`: record the date, Claude Code version, and `PASS` or the `FAIL` line.

# Verify: Runner resilience · spec 0014 · updated 2026-10-13
_Steps derived from spec 0014 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [x] `python3 -B -m unittest discover -s runner/tests` → all pass (355 at build time) → AC-1 to AC-8
- [x] `env -C runner/tests python3 -B -m unittest test_resilience` → all pass → AC-1 to AC-8
- [x] `test_resilience.TestOutage.test_backoff`: two `api_error_status: 529` calls wait 1 then 2 minutes (12 naps of 15 s), are not counted toward `--max-calls 4`, and a plain failure after them still gets its one retry → AC-1
- [x] `TestOutage.test_cap`: waits 1, 2, 4, 8, 16, 30, 30, then `stopped: api_outage` with 8 calls → AC-1
- [x] `TestOutage.test_connection_error` and `test_not_outage`: stderr `API Error: Connection error` with no JSON is an outage; a successful result naming `overloaded_error` is not; a usage limit text wins over a 529 → AC-1 (value source: `api_error_status`, else `OUTAGE` over result, subtype, stderr tail)
- [x] `TestOutage.test_wait_stops`, `test_max_hours`, `TestOutageApp.test_restart`: Autopilot off during a wait stops the repo, Ctrl C stops `interrupted`, a 60 minute wait under `--max-hours 0.01` still finishes, the app is stopped before the wait and a new one serves the rerun → AC-1
- [x] `TestCrashLoop`: two features in a row parking `denied` with the same first 60 characters stop `crash_loop` after the second park (both parks recorded); a `feature_done` between breaks the chain; three `call_timeout` parks never stop; the previous feature may be in another repo; a detail differing inside its first 60 characters does not count → AC-2 (value source: `run.json` `features` in `n` order, detail key)
- [x] `TestTokens`: per call `tokens` from `usage`, feature and run sums, `usage_partial`, `spent: 1.23+ USD, 4567+ tokens`; nothing known prints `spent: - USD, - tokens`; everything known prints no `+`; an `internal_error` stop prints the line too → AC-3 (value source: `usage.*_tokens`, `total_cost_usd`)
- [x] `TestTimeout`: a call that ticks its box and is killed parks naming the box, Park `cap` null; a larger `--call-timeout` and an untick then retick keep the park; unticking clears it; a timeout that ticked nothing keeps `cap` → AC-4 (value source: box states before vs after the call)
- [x] `TestLiveLog` and `test_run.TestHappyPath.test_argv`: fresh calls and retries get distinct uuid4 `--session-id` right after `--output-format json`, a resume none; `log.txt` 0600 holds start, call (transcript under `CLAUDE_CONFIG_DIR`), end, park, wait and done or stop lines → AC-6 (value source: `uuid.uuid4()`, `CLAUDE_CONFIG_DIR` else `~/.claude`)
- [x] `TestSyncBox`: a `/sync` box runs last with its box text and the prompt line, parks `no_progress` when left open, a ticked one turns off the automatic `/sync`, a finished feature is not in the plan, a question from it keeps its box text through the resume → AC-7 (value source: the box command's first word)
- [x] `TestSkipAhead`: a ` · waits on you · later boxes go on` box is passed, then the feature ends `waiting` (no Park record) and plans `skip: ... waiting` until ticked; an untagged one stops; `next` launches the box after a tagged one, refuses an untagged one, warns on a near miss → AC-7, AC-8 (value source: `OWED` and `SKIP_AHEAD` on the box's own text)
- [x] `TestFixture`: `runner/e2e/run.py` with a fake `wf` prints `PASS` and deletes its temp folder, then `FAIL: wf exit 6` and keeps repo, state and config (ntfy copy 0600, branch `wf-e2e`); the fixture scope plans as `queued: 1. Add function` → AC-5

## Manual (waits on you)
- [ ] `cp ~/claude-config/rules/scope-contract.md ~/.claude/rules/scope-contract.md`, then `diff` shows no output → AC-8
- [ ] `python3 runner/e2e/run.py` with `!` on the real claude prints `PASS` → AC-5, AC-9

## Acceptance-criteria coverage
- AC-1 TestOutage, TestOutageApp · AC-2 TestCrashLoop · AC-3 TestTokens, TestHappyPath · AC-4 TestTimeout · AC-5 TestFixture plus the manual end to end · AC-6 TestLiveLog, test_argv, test_no_session · AC-7 TestSyncBox, TestSkipAhead · AC-8 TestSkipAhead plus the manual rule copy · AC-9 probes above (P1 to P3 run before accept) and the outage probe that waits on you
