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
