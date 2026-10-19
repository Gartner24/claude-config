# 0065 verify: the build (`/check verify`, 2026-10-18)

Driven through `claude plugin test claude-home/mods/wf-dash` with a scratch test (`zz-verify.test.ts`, never committed) that ran
the real `hooks/register.tsx`, `alerts.ts`, `band.tsx` and `panes.tsx`. Its inputs were the real `wf status --json`
output of this machine (3 running runs) and three real run records from `~/.local/state/wf/runs`: one ended
`interrupted`, one ended `queue_done`, and one still running (no `ended`).

## Commands
- [x] A tick where the band facts fail but `wf status` reads 3 running, 0 parked, 0 questions stores `wf` as
  `{running: 3, parked: 0, questions: 0}`, `staleSince` set and `statusOk` true; a next tick with `wf status` failing
  keeps those counts with `statusOk` false → AC-1. can fail: the stale branch keeps `lastGood.wf`, which was 0 running.
- [x] Four runs leave `running` in one tick: the `interrupted` record toasts `stopped: 1. Int - in claude-config,
  interrupted`, the `queue_done` record toasts `finished: 2. Done - in claude-config` on that tick; the record with no
  `ended` and the id with no folder toast nothing until 3 more ticks, then `stopped: ... - in claude-config, ended with
  no record (lost its lock or crashed)`; 4 alerts in all, each once → AC-2. can fail: every departed run toasts
  `finished` (the old code), or the retry count is off.
- [x] The Alerts view draws a `stopped` row with its kind word, feature and detail; `alert.stopped` is `color.warn`
  (`panes.tsx:442` reads `alert[a.kind]`) → AC-2. can fail: a kind missing from the `alert` map draws uncolored.
- [x] The empty Alerts view reads `could not read wf` for `statusOk` false, `reading wf` for no facts yet, and the
  `No alerts yet ...` text for true → AC-3. can fail: the view ignores `statusOk` and always shows the empty text.
- [x] Full band runner counts: `wf   1 building    0 stuck    ? questions` and `wf  12 building  100 stuck    3
  questions` are the same length (`width.count` 3); compact band still `2 ask 3 run` with the zero dropped → AC-6.
  can fail: no padding, or padding applied to the compact band too (breaks its zero test).
- [x] No `"inactive"` literal or `?? 80` left in `hooks/register.tsx`; `width.viewport` is 80 and `color.dim` is the
  value used → AC-5. can fail: the literals stay in `register.tsx`.
- [x] `design.md` and `tokens.ts` name neither `/wf-dash-alerts` nor `/wf-alerts`; `design.md:44-47` describes the
  compact ` stale` mark as the last part to go and `stale` alone → AC-4. can fail: the old text stays.
- [x] `design-gate` over `claude-home/mods/wf-dash` wrote `.design/audit-report.md`: PASS, 0 must fix, 0 should fix
  → AC-7. can fail: any of the seven items left open in the report.

## Acceptance criteria coverage
- AC-1 met · AC-2 met · AC-3 met · AC-4 met · AC-5 met · AC-6 met · AC-7 met
