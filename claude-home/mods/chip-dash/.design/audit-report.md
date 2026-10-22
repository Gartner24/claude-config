# Design audit - wf-dash Plan warnings and Agents paging (panes.tsx) - 2026-10-19

verdict: PASS WITH FINDINGS (both must-fixes of pass 4 are fixed; the pass budget is spent, so the rest goes to a person as a list below, no further pass)
pass: 5 (outside the 3-pass budget; scope = the uncommitted panes.tsx and dashboard.test.ts diff on top of 9ef8b43, checking only pass 4's must-fixes and any defect the fixes created)
findings: 16 -> 15 (2 must-fixes closed, 1 created by the Plan fix, 12 carried; the count fell)
ai-tell fails: 1/36        (item 10 carried from pass 1, not re-verified)
token leaks: 0 new; token-leak.sh exit 2, NOT APPLICABLE (no tokens.css; tokens are the TS object in tokens.ts, the new lines use only `color.dim`, `color.warn` and `pane.*`); 7 carried from pass 1
a11y: static only (terminal surface, no page to serve)
wcag22: not run (terminal surface, no page to serve); 3.3.8 no login, 3.2.6 no help affordance, 2.5.7 no drag
contrast failures: not measured (every color is a Claude Code theme key; the user's theme decides the hues)
responsive: Agents clean 30-200 columns at 14 and 30 rows; Plan warnings add 0 rows at any width 40-200 (14 and 30 rows, 6 and 40 features); one regression in a docked empty plan (Should fix 1)
motion: none in scope (the change adds no animation, timer or spinner)
reference: not re-run (pass 1 compared 3 sections against k9s, 0 worse)
perf: NOT MEASURED (no browser surface)

## Must fix
None open.

- [x] FIXED (pass 4 Must fix 1) - the Agents view now has a row budget. `panes.tsx:502` sets `fit = pane.buildRows + extra - parts.rows - <note rows> - 1`, `:503-504` follow the cursor, `:511` draws only `fit` rows, `:520-522` add the dim `N above, +M more` line, and `:593` passes `extra`. Measured: probe `$TMPDIR/gate5/probe.ts agents` renders every width from 30 to 200 columns, with 0 to 40 shells, the cursor at the top, middle and bottom, and with the stop confirm or a failed stop notice open. 0 of 18,468 renders go past 14 rows (inline) or 30 rows (docked), and the cursor row is on screen in all of them. The same probe on pass 4's copy (`$TMPDIR/gate5old`) finds 12,411 overruns, up to 50 rows, so the probe can fail.
- [x] FIXED (carried since pass 1) - plan warnings under All open now come out of the list's page. `panes.tsx:226-231` cap them at `page + extra - 2`, folding the rest into a `+N more plan warnings` line, and `paginate` gets `room` (`:231`). `:316` sizes the box from `room`, and `:355` draws only `warns`. Measured: with 1 to 12 warnings, the Plan view is never taller than the same plan with no warnings, at 40-200 columns, at 14 and 30 rows, and with 6 or 40 features. The pre-fix copy breaks that 663 times (up to 29 rows in a 14-row pane). Test `dashboard.test.ts:117-133` pins the page count (`1/3`) and the `+4 more plan warnings` line.

## Should fix (created by this change)
1. [ ] In a docked pane, an empty All open tab with 5 or more plan warnings puts "Nothing open." in a box of height 0 - `panes.tsx:316-317`. With `extra > 0`, the floor `pane.page - warns.length` drops to 0 or below, and `Math.min(room, 0)` is 0. Pass 4's code floored this box at `pane.page` (5). Measured (`$TMPDIR/gate5/probe-empty.ts`, 100 columns, rows 30): 0 warnings gives height 5, 4 gives 1, and 5 or 6 give 0. The pre-fix copy gives 5 in every case. In Ink, a 0-height box lets its line spill over the next row, so the empty message would collide with the first warning. This case is likely: an empty plan with many warnings is what unreadable scopes produce. Fix: floor it at the two rows `room` always leaves, `height={extra ? Math.max(2, pane.page - warns.length, Math.min(room, pageList[page].length)) : room}`. That stays inside `room`, because `warnMax` keeps `room >= 2`.

## Should fix (carried, not re-verified; pass 4 line numbers, code unchanged by this diff)
2. [ ] `started` has no `agentStatus` entry, so it draws at full strength through the `?? color.text` default - `tokens.ts:84-92`, `panes.tsx:514` (still missing).
3. [ ] A failed read of the chat's messages looks like a chat with no shells - `hooks/register.tsx:46-48`, `:219-220`.
4. [ ] A shell that ended unseen never leaves the list, and its `x` fails every time - `hooks/register.tsx:69-71`.
5. [ ] When shells are listed, the empty-agent-list caveat disappears - `panes.tsx:510` still tests `agents.length`.
6. [ ] A safe step too long for a two-line confirm is never shown whole - `panes.tsx:267-274`, `:94`.
7. [ ] The type-it-yourself note puts the path first and cuts off the command - `panes.tsx:46`.
8. [ ] Builds says the phone is the only way to answer - `panes.tsx:382`, `design.md:99`.
9. [ ] "starting ..." shows in the ok color before the start can fail - `hooks/register.tsx:65`.

6 lower-severity findings dropped (pass 3 carried items 4-9, as listed in pass 4).

## Checked and clean
- Suite: `claude plugin test claude-home/mods/wf-dash` - 43 pass, 0 fail across 5 files (41 at pass 4, plus the 2 new tests at `dashboard.test.ts:117` and `:204`). The failure recorded in 9ef8b43 ("the plan warnings fix fails its own test") no longer reproduces.
- Agents shell note rows: `:502` estimates them as `ceil(length / cells)`, not by word wrap. The probe word-wraps the note the way Ink does, and finds no width from 30 to 200 where that estimate comes up short of the budget. Below 80 columns, the intro line the view drops leaves one spare row.
- `warnMax` is at least 3 (`pane.page` 5 - 2), so `slice(0, warnMax - 1)` never takes a negative end. The `+N` count is `warnAll.length - warnMax + 1`, which is exactly the number of warnings hidden.
- No new non-ASCII; the only hit is the allowed `·` at `panes.tsx:115`.
- The change touches only PlanSection, AgentsSection and the Agents prop at `:593`. The Builds and Alerts code is unchanged.

## Coverage notes
- Row counts come from a scratch probe: a copy of the current panes.tsx and tokens.ts with the classic JSX pragma, rendered with a recording `el`. It counts a truncating Text as 1 row and word-wraps every other Text. The host's real drawing was not observed in a live session.
- Without warnings, the Plan view already measures 17 rows in a 14-row pane at 40 columns, and 33 in a 30-row pane, because the filter keys wrap. It fits at 56 columns and above. This is the same with and without the fix, so it is not counted here.
- The Agents window keeps the cursor on its bottom row when moving up from the end (`start = sel - fit + 1`), so `k` scrolls the list rather than moving the cursor within it. This is a new opinion below P1 and is uncounted.
- 0 findings cut for lack of `file:line`.

---

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

## Band and alerts (spec 0065 fix verification, from main)
Merged from main on 2026-10-19: the band and alerts got their own fix verification after spec 0065 (pass 4 of 3, verdict PASS, 0 must-fix, 0 should-fix, ai-tell 0/36, token leaks 0). The 7 band should-fixes listed in earlier passes are fixed there and no longer open. The handoff line above was graded on the code before that merge; the merge touched only `hooks/register.tsx` (state folder and theme tokens), not the handoff line code.
