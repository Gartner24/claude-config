# 0022 verify

## Probes (2026-10-13, at the build)

- **P1** (endpoint shape, no token touched): `jq -c '{five_hour: (.five_hour|{utilization, resets_at}), seven_day: (.seven_day|{utilization, resets_at})}' /tmp/claude-usage-cache.json` prints both windows with a float `utilization` and an ISO `resets_at` with offset (`2026-10-14T05:00:00.819794+00:00`). The keys have not moved. Result: PASS.
- **P2** (`claude -p` carries no limit data): `jq -c keys <state>/runs/<a run of today>/call-05.json` lists `api_error_status, duration_api_ms, duration_ms, ..., total_cost_usd, usage, uuid` and no `rate_limits`. Result: PASS (the runner needs the AC-1 read).
- **P3**: not run (calls the real claude; not needed for this build).
- **P4**: waits on you, at the first real `wf` after the build.

## Verify steps (2026-10-14, /check verify)

Scratch drivers in `$TMPDIR/v0022/` (not committed). They run the real `usage.py` and real `wf` processes over the repo's fake claude fixtures, with a local HTTP server standing in for the usage endpoint (a `sitecustomize` sends the real URL to it).

- [x] `drive_read.py`: one GET to `/api/oauth/usage` with the five status line headers, 200, 401 (body holds the token), a 7 s hang (gave up at 5.2 s, `TimeoutError`) and bad JSON give the result and the three fixed reasons; the planted token shows 0 times in stdout, stderr and the state folder -> AC-1. can fail: the token is put in the reason text, or the 401 body is printed.
- [x] Same driver: `ANTHROPIC_API_KEY`, a non anthropic `ANTHROPIC_BASE_URL` (also `evilanthropic.com`) and no credentials give `not a subscription login` with 0 requests; a null `utilization` reads `0.0` with `resets_at` None -> AC-1. can fail: the host check uses `endswith("anthropic.com")`.
- [x] Same driver: two reads within 60 s make 1 request, a 61 s old cache makes a new one, `usage.json` and `usage.jsonl` are 0600, 2100 extra lines trim to 2000 with the real read newest -> AC-2. can fail: the cache age check is dropped, or the trim keeps the oldest lines.
- [x] `ChildSampling`: a real `wf run demo -y` with 3 calls makes 4 usage requests when the service answers 503 (start plus after each call) and prints the `warning: usage not read` line once, exit 0; with a 200 answer it makes 1 request (cache) and writes 1 sample -> AC-2. can fail: `sample_usage` loses its call after each call, or the warning flag is not kept.
- [x] `drive_math.py`: medians per kind key (`/develop` 4.0 USD, 250 s, 10 tokens over 4 calls), limited, outage and null cost left out, `/check verify` and `/check` keys apart, under 3 samples falls back to all calls, no calls gives None -> AC-3. can fail: limited calls are counted, or the key takes one word for `/check verify`.
- [x] Same: ratios 2.0 (five hour) and 0.6 (week) by hand; a pair with no call and a changed reset are skipped; under 1 USD and samples older than 14 days give None -> AC-4. can fail: pairs across a reset are summed.
- [x] Same: a feature with a done box, a skipped box, a `/check verify` box and its own sync box costs (7.0, 1000, 4.0); two features in one repo and one in another need ~42% 5h, ~21% week, 0.6h -> AC-5. can fail: the duration adds all repos instead of the largest.
- [ ] Two repos, the first picked feature's first call 1% and the second repo's first call 10% with 5% of the 5h window left: `usage.plan` says `fits, starts now`; AC-6 says "the first call of the first picked feature in any repo", so it should say `5h window nearly used` -> AC-6. FAIL: `runner/usage.py:329` checks only `costs[0][2]`, the first numbered feature. Rerun 2026-10-14 with `drive_ac6.py` (no runner change since `db34b68`): repo `rb`'s first call needs 10% with 5% left, still `fits, starts now`; the control with the big feature first says `5h window nearly used`. Still FAIL.
- [x] `Screen.test_five_hour_nearly_used`: bare `wf -y` with 5h at 99% prints `now: 5h 99% (resets ...)`, `need:`, `5h window nearly used: starts at ...`, waits, then builds both repos -> AC-6, AC-7, AC-9. can fail: the 5h branch is removed.
- [x] `Screen.test_pick_still_does_not_fit`: at the prompt, `1` prints the usage lines again for the pick, still `does not fit the week`, one prompt only, waits, builds only `ra`, exit 0 -> AC-8, AC-9. can fail: the pick's start time is dropped and it starts now.
- [x] `Screen.test_cancel`: `x` at the prompt exits 130 with no build -> AC-8. can fail: any answer is taken as Enter.
- [x] `Screen.test_report_seen_before_wait`: with an unseen report, `report.seen` exists while the builds wait; Ctrl C in the wait exits 130 -> AC-9. can fail: `seen()` moves after the wait.
- [x] `LimitAccount.test_more`: a full 5h window with a later reset sleeps 10920 s, both full sleeps to the later (week) reset 259320 s, a full window earlier than the text and a window at 98 keep the text's 1320 s -> AC-10. can fail: the earliest full reset is taken, or the 99 threshold moves.
- P4 (the real `wf` screen against the status line bars): waits on you; the account read is not reachable from this sandbox (credentials are read denied).
