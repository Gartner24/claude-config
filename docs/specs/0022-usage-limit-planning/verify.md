# 0022 verify

## Probes (2026-10-13, at the build)

- **P1** (endpoint shape, no token touched): `jq -c '{five_hour: (.five_hour|{utilization, resets_at}), seven_day: (.seven_day|{utilization, resets_at})}' /tmp/claude-usage-cache.json` prints both windows with a float `utilization` and an ISO `resets_at` with offset (`2026-10-14T05:00:00.819794+00:00`). The keys have not moved. Result: PASS.
- **P2** (`claude -p` carries no limit data): `jq -c keys <state>/runs/<a run of today>/call-05.json` lists `api_error_status, duration_api_ms, duration_ms, ..., total_cost_usd, usage, uuid` and no `rate_limits`. Result: PASS (the runner needs the AC-1 read).
- **P3**: not run (calls the real claude; not needed for this build).
- **P4**: waits on you, at the first real `wf` after the build.
