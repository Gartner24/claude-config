# Design audit - wf-dash band, alerts view and hooks/register.tsx after spec 0065 - 2026-10-18

verdict: PASS
pass: 4 of 3 - a fix verification, not a fresh pass. Pass 3 hit the budget and handed 7 should-fixes to the owner; the owner picked all 7 (spec 0065), and AC-7 of that spec asks for this re-run. Run under the re-audit rules only: each carried item checked, regressions from the fixes in scope at full severity, no new opinions below P1.
ai-tell fails: 0/36        (item 10 fixed: full band counts are now right aligned in width.count cells)
token leaks: 0 (token-leak.sh exit 2, NOT APPLICABLE, no tokens.css; substitute check = theme-key and width literals in hooks/ that bypass tokens.ts: 0, was 3)
a11y: static only (terminal surface, no page to serve)
wcag22: not run (terminal surface, no page to serve)
contrast failures: not measured (colors are Claude Code theme keys from the user's theme)
responsive: clean at the documented ~31 cell column and 94/120/160 (band.test.ts); the padded full band only leaves left segments sooner, via fit()
motion: none in scope
reference: not re-run (pass 1: 2 sections against k9s, 0 worse; the only visible changes are the count padding and the new `stopped` kind, both ones the owner picked in spec 0065)
perf: NOT MEASURED (no browser surface)

Finding count: pass 3 had 0 must-fixes and 7 should-fixes. This run has 0 and 0. The count fell, so there is no STOP.

## Carried should-fixes, each checked

- [x] Fresh runner counts on a stale tick - fixed. `hooks/register.tsx:104-107` merges this tick's `wf` into `lastGood.wf` field by field, so a field that failed keeps its last good count. It also stores `statusOk` (`:70`) and saves the mark into `lastGood`, so `stale since` keeps its first time. Pinned by `register.test.ts` "a stale tick shows the runner counts it just read".
- [x] `finished` toasted for any end - fixed. `alerts.ts:40-46` gives `finished` only when `ended` is set and `stop_reason` is `queue_done` or `feature_done`, otherwise `stopped` with the reason. A record that is missing or has no `ended` is read again for 3 ticks (`:15`, `:48`). `alertTick` reads the records before the pure `diff` (`:96-101`), and an id that does not match `RUN_ID` (`:83`) is never turned into a path. `runner/run.py:3950` always writes `ended` and `stop_reason` together, so the `String(r.stop_reason)` at `alerts.ts:42` never prints `null` for a real record.
- [x] Empty Alerts view the same whether wf was read or not - fixed. `panes.tsx:437` shows `reading wf` (no FACTS yet), the empty text (statusOk true) or `could not read wf` (false). It is fed by `hooks/register.tsx:203`.
- [x] Literals that bypass tokens.ts - fixed. `hooks/register.tsx:181` uses `color.dim`, `:187` and `:203` use `width.viewport` (`tokens.ts:168`). A grep for `color="` and `?? <digit>` under hooks/ returns 0.
- [x] Counts not fixed width - fixed in the full band. `band.tsx:117-119` pass `width.count` to `countRun` (`:56-60`), which left pads with the existing `pad()`. The compact band passes none, so its zero filter (`:104`) and budget (`:108-112`) still read bare text, as AC-6 says.
- [x] design.md did not describe the compact stale band - fixed. `design.md:44-47` says the fresh counts show, the 3 cell alignment, ` stale` is the last part to go, and the band can read `stale` alone.
- [x] Docs named removed commands - fixed. `design.md:13`, `design.md:113` and `tokens.ts:42` now name the dashboard's Alerts view (`l`). A grep for `wf-alerts` / `wf-dash-alerts` finds them only in this report's own history.

## Regressions the fixes could have created, checked

- Band width: the padded full band is up to 6 cells wider. `fit()` (`band.tsx:128-136`) drops left segments by the DROP order and the band falls back to compact when only the chip is left, so nothing overflows. The 94/120/160 and 31 cell band tests pass.
- The `stopped` kind is 7 characters, inside `pane.col.kind` (10) (`tokens.ts:116`). `alert.stopped` = `color.warn` (`tokens.ts:46`), drawn at `panes.tsx:442`.
- A seen record saved by the old code (no `pending`) loads through `isSeen` (`alerts.ts:82`). `seen.pending ?? []` covers it, and the first tick writes it back once.
- `JSON.parse` of a bad run.json sits inside `.catch(() => null)` (`alerts.ts:98`), so a corrupt record counts as missing and never throws out of the tick.

## Must fix
None.

## Should fix
None.

## Checked and clean
- Suite: `claude plugin test claude-home/mods/wf-dash` - 37 pass, 0 fail across 5 files. 33 of them are in the 4 tracked files (pass 3 had 28). The other 4 are the untracked `zz-verify.test.ts` scratch from `/check verify`, ignored as asked.
- `claude plugin validate claude-home/mods/wf-dash` passes. It reports the new `$.env.get` reads (HOME, XDG_STATE_HOME) and no env writes.
- Spec 0065 AC-1 to AC-6, each mapped to the code above. AC-7 is this report.

## Coverage notes
- Not raised (the mod already did this before the fix, so it is not a regression; below P1): if a run's `wf status` entry loses its id for one tick, then it counts as gone. Before, it toasted `finished` at once. Now, since its run.json has no `ended`, it toasts `stopped ... ended with no record` after 3 ticks. A fix would drop a pending id that comes back into `running` (`alerts.ts:48`).
- Spec wording, not a defect: a `queue_done` run whose features all parked still toasts `finished`. Its parked features toast `stuck` on their own.
- The compact band's counts are still unpadded on purpose (spec 0065 AC-6). That is why AI-tell item 10 counts only the full band.
- This audit did not mutation-check the new tests. `/test` does that under its own gate.
- 0 findings cut for lack of `file:line`.
