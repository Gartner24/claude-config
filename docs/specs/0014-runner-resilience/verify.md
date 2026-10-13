# 0014 verify

## Probes before accept (AC-9), Claude Code 2.1.296, 2026-10-12

- **P1 session id**: `env -C <scratch> claude -p "Reply with the single word ok." --output-format json --session-id 11eecd84-fe72-45bb-9661-86ff635083f5`. Result: JSON `session_id` equals the given uuid, `subtype` `success`. Pass.
- **P2 live transcript**: `claude -p "Use the Bash tool to run: sleep 25. Then reply done." --output-format json --permission-mode auto --session-id 6a0d6c1e-2f4b-4c8e-9a51-3b7d2e9f1c40` in the background; while the call slept, `~/.claude/projects/*/6a0d6c1e-2f4b-4c8e-9a51-3b7d2e9f1c40.jsonl` already held 33 lines, 9 naming the `sleep` call. Pass.
- **P3 usage fields**: the P1 JSON holds `usage` with `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens` (ints), `total_cost_usd`, and `api_error_status: null`. Pass.

## Follow-up probe (waits on you)

- **Outage shape**: at the next real API outage, copy the failed call's `call-NN.json` and the last lines of `call-NN.stderr` from the run folder here. Pass when `api_error_status` is 500 or more, or the text matches `OUTAGE`.

## End to end (build step 9)

- `python3 runner/e2e/run.py`: record the date, Claude Code version, and `PASS` or the `FAIL` line.
