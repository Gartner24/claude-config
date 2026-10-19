# Design audit - wf-dash handoff line under the band (spec 0064: band.tsx HandoffRow, handoff.ts, hooks/register.tsx) - 2026-10-19

verdict: PASS WITH FINDINGS (handoff line: 0 must-fix open; the one pass 2 must-fix was accepted by the owner on 2026-10-19. Budget of 3 passes reached: no further audit pass on this surface, the 4 should-fixes go to the owner as a list)
pass: 3 of 3 for the handoff line (pass 2 had 5 findings: 1 must-fix, 4 should-fix; now 4 open: 0 must-fix, 4 should-fix, plus 1 accepted by the owner. The count fell, so not STOP)
ai-tell fails: 1/36        (item 10 carried from the band; unchanged since pass 2)
token leaks: 4 (token-leak.sh exit 2, NOT APPLICABLE: no tokens.css. Substitute check = literals in the mod that bypass tokens.ts: 3 in hooks/register.tsx, 1 at handoff.ts:26, unchanged since pass 1)
a11y: static only (terminal surface, no page to serve)
wcag22: not run (terminal surface, no page to serve)
contrast failures: not measured (colors are Claude Code theme keys from the user's theme)
responsive: result line with a loopback link cut below ~83 columns, with a Tailscale link below ~85-89 (ACCEPTED by the owner); handover line fits from ~62 columns; every link line and the sticky text cut at the 31-cell docked column
motion: 0 findings against review-animations standards (handoff.ts, hooks/register.tsx)
reference: 1 section (handoff line) compared against k9s by reading only, 0 worse; not screenshotted (terminal)
perf: NOT MEASURED (no browser surface)

## Refresh after pass 3 (2026-10-19, no new pass)

The 3-pass budget is spent, so this is not a fourth audit; it confirms the graded code did not change. `git diff --stat 5548b2b HEAD -- claude-home/mods/wf-dash claude-home/mods/wf-handoff` (5548b2b = the pass 3 report commit) shows one file: `handoff.test.ts`, +28 lines, from 6049190 (two AC-2 dismiss tests). `band.tsx`, `handoff.ts` and `hooks/register.tsx` have no diff since pass 3 and no uncommitted change; `band.tsx` and `handoff.ts` only carry a newer mtime (02:08) with identical content. `hooks/register.tsx` last changed in 6751d0f, the reduced motion spinner fix that passes 2 and 3 already graded. Suite rerun: `claude plugin test claude-home/mods/wf-dash` - 38 pass, 0 fail across 5 files (10 in handoff.test.ts, the 2 new AC-2 tests among them). Verdict, findings and accepted items below stand unchanged.

## Pass 2 must-fixes, rechecked

No code changed since pass 2: `git status` is clean for `claude-home/mods/wf-dash` and `claude-home/mods/wf-handoff/hooks`, no file under the mod is newer than the pass 2 report, and the last commit touching the mod is 6751d0f, the pass 2 reduced motion fix. Suite rerun this pass: `claude plugin test claude-home/mods/wf-dash` - 36 pass, 0 fail across 5 files.

- ACCEPTED BY THE OWNER (2026-10-19), not open - the result line link is cut at narrow widths (`claude-home/mods/wf-dash/band.tsx:186` `wrap="truncate-end"`, link last; `claude-home/mods/wf-dash/handoff.ts:26`, `:29`). Owner's words: "Keep it, full link shows next". Accepted as is: the result line `handed off · 210k -> 95k · <link>` (`claude-home/mods/wf-handoff/hooks/register.ts:405`) loses its last key characters below about 83 columns with a loopback link and below about 85-89 with a Tailscale link. Why it is acceptable: the result line lasts 10 s, and the `handover: <link>` line that follows carries the same full link from about 62 columns. No spec change. The docked 31-cell column still cuts every link line; that case is part of the same accepted finding, and a person reaching the link there widens the window or reads it from the handover page.

## Must fix
None open.

## Should fix (carried from pass 1, not re-graded; for the owner)
- [ ] Sticky failure or pause loses its reason at the docked width - `claude-home/mods/wf-dash/band.tsx:185-189`.
- [ ] design.md does not describe the handoff line - `claude-home/mods/wf-dash/design.md:27`.
- [ ] Non-ASCII separator outside tokens - `claude-home/mods/wf-dash/handoff.ts:26`.
- [ ] (PLAUSIBLE) Lost update between the handoff state writers - `claude-home/mods/wf-dash/hooks/register.tsx:65-67`, `:165`, plus the dismiss paths; the settings read at `:164` widens the window between the get at `:162` and the set at `:165`.

## Accepted by the owner
- [x] Result line link cut below ~83-89 columns, and every link line in the docked column - `claude-home/mods/wf-dash/band.tsx:186`, `claude-home/mods/wf-dash/handoff.ts:26`, `:29` - owner 2026-10-19: "Keep it, full link shows next"; no spec change.

## Checked and clean
- Reduced motion: first frame plus label, host-matching default on a failed settings read (`hooks/register.tsx:164`, `handoff.ts:21-22`); pinned by `under reduced motion the spinner keeps its first frame` (`handoff.test.ts:85-98`), which passed this pass.
- Spinner turns only while a step runs and the line is not sticky (`hooks/register.tsx:163`).
- Suite: 36 pass, 0 fail across 5 files (8 in handoff.test.ts).
- Pass 1's clean rows (color never the only signal, theme-key colors, dismiss key binding, absent answers draw no line) were not re-graded; no line has changed since.

## Coverage notes
- Pass 3 verified only pass 2's must-fix, per the re-audit rules. No regressions: nothing changed since pass 2.
- Widths are still arithmetic on the real link shapes (`wf-handoff/hooks/register.ts:115`, `:239`), not a render at a width.
- The shape of `$.settings.read()` is still taken from the mod test harness, not checked against the live 2.1.303 host.
- 0 findings cut for lack of `file:line`. No new findings below P1 raised in this pass.

## Band and alerts (pass 3 of 3, carried unchanged)
`band.tsx` lines 1-179 and the band and alert paths of `hooks/register.tsx` are as their pass 3 graded them. Its 7 should-fixes stand, for the owner: design.md stale-band wording (`design.md:42-44`), stale tick keeps old runner counts (`hooks/register.tsx:116`), `finished` toast for a parked run (`alerts.ts:29`), Alerts empty state (`panes.tsx:436`), theme key and width literals (`hooks/register.tsx:210`, `:207`, `:239`), counts not fixed width (`band.tsx:58`, `:116-118`), docs naming removed commands (`design.md:108`, `design.md:13`, `tokens.ts:42`).
