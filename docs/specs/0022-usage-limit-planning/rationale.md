# 0022 rationale

## Context

- Scope feature 12, brought back by docs/briefs/finish-runner-today.md item 11: estimate each step, fit the run to the 5 hour window and the week, start after a reset. The request of 2026-10-13 adds: never refuse; a run that does not fit asks or waits, and the screen says "fits / does not fit, starts at <time>". The scope row's old "Done when" ("refused before it starts") is replaced by that.
- What the runner records today: every call record has `kind`, `command`, `started`, `duration_s`, `cost_usd`, `tokens`, `limited`, `outage` (run.py:1992-1994, filled at run.py:2027-2033; `limited` at run.py:2064). Run folders are pruned to the newest 50 (`RUNS_KEPT`, run.py:308).
- What the runner does at a limit today: `limit_wait` sleeps to the reset parsed from the limit text, else 30 minutes, and never ends the run (run.py:2609-2633, `LIMIT_UNKNOWN` run.py:299, spec 0021 U3). The parse reads only a time of day (`RESET`, run.py:297), so a weekly limit days away loops on 30 minute sleeps.
- Where usage numbers can come from (checked 2026-10-13):
  - `claude -p` JSON: no rate limit field (probe P2 on a real call file: keys are `usage`, `modelUsage`, `total_cost_usd`, `duration_ms` and others, no `rate_limits`).
  - The status line input JSON carries `rate_limits.five_hour` and `seven_day` with `used_percentage` and `resets_at`, but the status line runs only in an interactive session, never inside `wf`.
  - The OAuth usage endpoint the jjstack status line calls (`statusline.sh:139-165`: `GET https://api.anthropic.com/api/oauth/usage`, bearer token from `~/.claude/.credentials.json`, `anthropic-beta: oauth-2025-04-20`) answers `five_hour` and `seven_day` objects with `utilization` (percent) and `resets_at` (probe P1, read from the status line's cache file, no token touched). `used_dollars` and `limit_dollars` exist but are null on this account, so percent is the only unit.
  - `--output-format stream-json` may emit a rate limit event (P3); unconfirmed, and not needed.

## Options considered

1. Where to read usage: (a) the OAuth endpoint from `wf` itself (chosen): fresh, works at night with no session open; costs one small request a minute at most and handles your token. (b) The status line's cache file in `/tmp`: no token handling, but stale all night when no session is open, and a world writable folder. (c) Only learn from limit errors: no planning at all before the first limit.
2. Unit of the estimate: (a) dollars per call (`total_cost_usd`, chosen) converted to percent by a ratio learned from samples: every call already records it. (b) Tokens: cache reads dominate and do not map to the limit the same way. (c) Percent per call measured before and after each call: breaks with repos running side by side.
3. What "does not fit" does: (a) wait for the reset, with Enter, numbers or `now` at the prompt (chosen, the request says never refuse). (b) Refuse, as the old scope row said (overruled by the request). (c) Start now and let the limit sleep handle it: burns the week you need by day.
4. Weekly reserve: (a) keep 10 points of the week for your own use (chosen); (b) none; (c) a flag. The 0008 user story asks for a run that does not eat "the weekly usage I need by day".

## Decided without asking (2026-10-13)

Per docs/briefs/finish-runner-today.md ("the conductor answers every design question itself with the recommended option and records it").

| Question | Options | Pick |
|---|---|---|
| Where does `wf` read your 5 hour and weekly usage? | OAuth usage endpoint with your token; status line cache file; only from limit errors | Endpoint, token never printed, logged or saved (a token grep test proves it) |
| What unit does a step's estimate use? | dollars from `total_cost_usd`; tokens; percent per call | Dollars, turned into percent by a ratio learned from usage samples |
| Estimate per what? | per command kind (`/develop`, `/check verify`, `/test`, `/debug`, `/sync`...); per feature; per repo | Per command kind, median, fall back to all calls under 3 samples |
| A run that does not fit the week | wait for the reset (ask at the prompt); refuse; start anyway | Wait, Enter keeps it, numbers pick fewer, `now` starts anyway; `-y` waits |
| When does the 5 hour window delay the start? | when even the first call would not fit; when the whole run does not fit one window; never | Only when the first call would not fit; a longer run sleeps through resets (U3) |
| Weekly reserve kept for your day use | 10 points; none; a flag | 10 points, fixed |
| What runs during the wait? | only the builds wait; everything waits | Only the builds: report, swap, retakes and checks run at once |
| Unknown usage (no login, no samples, endpoint down) | start now with "unknown"; wait; ask | Start now, the screen says unknown and why |
| Weekly limit hit mid run | sleep to the account's `resets_at`; today's 30 minute retries | Account's `resets_at` when the text has no date (AC-10) |
| Cache and sample retention | 60 s cache, 2000 sample lines, 14 day ratio window; other values | Those values, fixed |

## Rationale

The runner already sleeps through resets (spec 0021 U3), so the only missing piece is knowing, before the run, whether the night fits and when to start. Dollars per call are already recorded for every call, so the estimate needs no new recording; the one new input is where you stand in each window, which only the endpoint answers when no session is open. The ratio learned from samples is rough by design: it errs toward "does not fit", and the outcome is never a refusal, only a later start you can override with `now`.

## Consequences

- One small request to Anthropic per minute at most while `wf` runs; an undocumented endpoint can change shape: then usage reads unknown and runs start now, as before this spec.
- `wf` reads your login token file (it never did before); the token stays in the `wf` process memory for one request.
- A `-y` start that does not fit waits, maybe for days until the weekly reset; Ctrl C cancels.
- Estimates are medians per command kind, so a feature with an unusual step is guessed wrong; the guess improves as runs pile up.
