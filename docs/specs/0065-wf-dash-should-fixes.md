# 0065. wf-dash design should-fixes

**Date**: 2026-10-18
**Status**: Proposed
**Paths:** `claude-home/mods/wf-dash/**`
**Amends:** [0059](0059-wf-dash-band.md) AC-3 (a run that leaves `running` toasts `finished` only when its record says it finished)

## What you're agreeing to
- All seven small fixes the design check left on the bottom bar get built (your pick of 2026-10-18).
- The bar shows the runner counts it just read, even when it is stale.
- A run that stopped for any other reason than finishing pops up `stopped` with the reason, never `finished`.
- An empty alerts list says when the runner could not be read.
- The design notes, colors and number widths are tidied; nothing else on screen changes.

## Summary
The design gate's pass 3 report (`claude-home/mods/wf-dash/.design/audit-report.md`, "Should fix") listed seven should-fixes. You picked all seven. Six are local fixes; one changes alert wording, so it amends spec 0059 AC-3.

## Requirements
- **AC-1** (fresh counts): when a band tick marks the band stale (`hooks/register.tsx:97`), it keeps the runner counts read on that tick when that read succeeded; only the fields that failed keep their last good value. The tick also stores `statusOk` on `FACTS`: true when that tick's `wf status` parsed and at least one field was not `null`, else false.
- **AC-2** (truthful finished alert): when a run id leaves `running` (`alerts.ts:29`), `alertTick` reads that run's record, before it calls `diff`, which stays pure and takes the results as a map from id to record (or `null`). The record is `<state>/wf/runs/<id>/run.json` (`<state>` is `XDG_STATE_HOME`, else `~/.local/state`) (`runner/run.py:735`; the id is that folder name, `runner/auto.py` `run_id`), read with `$.fs.read`. Kind `finished` when the record has `ended` set and `stop_reason` is `queue_done` or `feature_done` (both written as the run's stop reason, `runner/run.py:3479` and `:3950`). A record that is missing or has no `ended` yet is read again on each of the next 3 ticks before the alert settles; the id is marked toasted only when it settles. Otherwise kind `stopped`, with detail `in <repo>, <stop_reason with _ as spaces>`; a record that is missing, unreadable or has no `ended` gives detail `in <repo>, ended with no record (lost its lock or crashed)`. Each id still toasts once. Spec 0059 AC-3's kinds become `finished`, `stopped`, `stuck`, `question`: `stopped` is added to `WfDashAlert.kind` (`types/index.d.ts:20`) and to the `alert` map in `tokens.ts` as `color.warn`, and the Alerts view (`panes.tsx:441`) shows it like the others.
- **AC-3** (empty alerts list): the Alerts view (`panes.tsx:436`) shows `could not read wf` instead of the empty text when `FACTS.statusOk` (AC-1) is false; the empty text stays when it is true, and before the first tick (no `FACTS` yet) the view shows `reading wf`.
- **AC-4** (design notes): `design.md:42-44` describes the short stale band (` stale` is the last part to go, and the band can read `stale` alone); `design.md:108`, `design.md:13` and `tokens.ts:42` no longer name the removed `/wf-dash-alerts` and `/wf-alerts` commands.
- **AC-5** (shared values): `hooks/register.tsx:171` uses `color.dim` from `tokens.ts` instead of `"inactive"`; `:177` and `:193` use a new token `width.viewport: 80` in `tokens.ts` instead of `?? 80`.
- **AC-6** (steady widths): in the full band only (`band.tsx:115-117`), each runner count's number (or its `?`) is left padded to `width.count` from `tokens.ts` with the existing `pad()`. `countRun` (`band.tsx:57`) and the compact band stay unpadded, so its zero hiding (`:102`) and length budget (`:108`) keep working.
- **AC-7** (gate): `design-gate` runs again over the mod after the build and its report sits in `claude-home/mods/wf-dash/.design/`.

## Decision
Build all seven in the mod; the finished alert reads the run record the runner already writes, so `wf status --json` keeps its shape.

## Rationale
The run record already carries `ended` and `stop_reason` (`runner/run.py`, read by the morning report), and the running id is that record's folder name (`runner/auto.py` `run_id`). Reading it in the mod avoids a contract change to `wf status --json`. Runner up: add an `ended` list to `wf status --json`, rejected as a wider change for one alert.

## Feature design
**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| finished or stopped | why the run ended | `run.json` `ended` and `stop_reason` |
| stopped detail | repo | the departed `running` entry's `repo` |
| widths, color | tokens | `tokens.ts` `width.count`, `width.viewport`, `color.dim`, `alert.stopped` |
| could not read wf | `statusOk` | set by the band tick (AC-1) |

**Critical test scenarios** (`claude plugin test claude-home/mods/wf-dash`):
- a stale tick with a fresh `running` count shows the fresh count, verifies **AC-1**
- a departed id with `queue_done` toasts `finished`; with `decision_open` toasts `stopped: ... decision open`; with no record toasts the no record text, verifies **AC-2**
- a failed tick shows `could not read wf`, a good empty tick shows the empty text, verifies **AC-3**

## Build plan
1. Alerts: record read and kinds, satisfies **AC-2**
2. Band: fresh counts, padded widths, tokens, satisfies **AC-1**, **AC-5**, **AC-6**
3. Alerts view text, satisfies **AC-3**
4. design.md and tokens.ts text, satisfies **AC-4**
5. Tests, then design gate, satisfies **AC-7**

## Consequences
**Positive**: the bar and its alerts never claim a fact the runner did not report.
**Negative / tradeoffs**: one file read per ended run; alert wording you are used to changes for runs that did not finish.
