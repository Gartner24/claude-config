# Design audit - chip-dash Now view and band owed segment, spec 0071, pass 3 - 2026-10-22

verdict: PASS WITH FINDINGS (the pass 2 must-fix is closed, the readOwed change created no defect; the one should-fix left is an owner call on accepted spec text. Pass budget spent: no fourth pass on this surface)
pass: 3 of 3 (scope = pass 2's findings only, plus any defect the fixes created; diff since pass 2 = dashboard.test.ts:59-60 assertion and test name, committed in ba3c441; uncommitted hooks/register.tsx readOwed, `:119-134`, and now.test.ts `existsFails` host switch plus the test at `:122`)
findings: 2 -> 1 (pass 2: 1 must-fix owner-blocked, 1 should-fix; now: 0 must-fix, 1 should-fix unchanged; 1 fixed, 0 created by the fixes. The count fell, so not STOP)
ai-tell fails: 0/36        (not re-graded; no drawing code changed: panes.tsx, band.tsx, tokens.ts have no diff since pass 2)
token leaks: 0. token-leak.sh exit 2, NOT APPLICABLE (no tokens.css; tokens are the TS object in tokens.ts). Substitute check on the changed lines: readOwed adds no color, width or timing literal
a11y: static only (terminal surface). The new unknown state draws `owed ?` in warn bold plus the error in dim (`panes.tsx:401`): word and color, never color alone
wcag22: not run (terminal surface); 2.5.7 no drag, 3.2.6 no help affordance, 3.3.8 no login
contrast failures: not measured (theme keys; the user's theme decides the hues)
responsive: unchanged from pass 2 (no drawing code changed). The new state reuses the parse-error rows of `owedLines` (`panes.tsx:401`, 2 rows inside the 3-row owed block) and each row truncates (`panes.tsx:452` `wrap="truncate-end"`), so a long EACCES message with a path cannot add a row
motion: none in scope (the fixes add no animation, timer or spinner)
reference: not re-run (pass 1 compared 4 sections against k9s, 0 worse)
perf: NOT MEASURED (no browser surface)

## Must fix
None open.

- [x] FIXED (pass 1 and 2 Must fix) - the suite is green: `claude plugin test claude-home/mods/chip-dash` - 82 pass, 0 fail across 8 files. `dashboard.test.ts:59` now expects `['p', 'n', 'a']` and the test name reads "the views switch on p n a" (`dashboard.test.ts:55`), after the owner allowed the change. Spec 0071 AC-10 is met.

## Should fix (for the owner; not an agent fix)
1. [ ] CARRIED (pass 2 item 1, unchanged) - at 40 columns `failing` and `pending` lose their last letters (`checks faili...`, `checks pendi...`; the color stays) because the `checks ` label is kept - `panes.tsx:474`. AC-3 spells the row with that label, so dropping it under 80 columns changes accepted spec text: an owner call through `/architect`.

0 lower-severity findings dropped. 0 findings cut for lack of `file:line`.

## Fix-created defects checked (readOwed, hooks/register.tsx:119-134)
- None found. A rejected `$.fs.exists` on the folder or on a chat's file, a rejected `$.fs.read`, and a parse failure all reach `{ installed: true, lines: null, error }` (`:131-132`, `now.ts:36-40`), which the Now view draws as `owed ?` plus the error (`panes.tsx:401`). Before, a rejected exists read as false: `catch not installed` for the folder, a skipped file (so `nothing owed`, or the other id's file) for the file.
- The band: `lines: null` adds no segment (`band.tsx:85-87`), the same as before for the folder case (then `installed: false`, also no segment). It never prints `owed ?` or `owed 0`, as AC-7 says.
- One behavior narrows on purpose: a rejected exists on this chat's file no longer falls through to the replaced id's file. The answer for this chat is unknown, so `owed ?` is the right fact; not counted.
- The read error text used to be caught per call; it is now one catch for the block, with the same `String(err?.message ?? err)` (`:132`), so the message the view shows is unchanged.

## Checked and clean
- Suite: 82 pass, 0 fail. now.test.ts: 25 pass, the new exists test among them.
- New test can fail, mutation checked: re-adding `.catch(() => false)` to the folder exists (`register.tsx:124`) turns `AC-2 an exists check that fails...` (`now.test.ts:122`) red at its first `owed ?` expect; re-adding it to the file exists (`:127`) turns the same test red at its second half. Each restored from a `cp` backup; suite green again after (82 of 82).
- ASCII: no non-ASCII in hooks/register.tsx or now.test.ts.
- The comment at `register.tsx:119-121` names the past failure ("it used to read a rejected exists as false"), the repo's comment style.

## Coverage notes
- Per the re-audit rules, only pass 2's findings and fix-created defects were graded. Nothing new below P1 was raised.
- No render probe was rerun: no file the probe copies (panes.tsx, band.tsx, tokens.ts, handoff.ts) changed since pass 2. The new state's height comes from reading `owedLines` and the truncating row, not a fresh render.
- The 3-pass budget is spent. The should-fix above goes to the owner as a decision, not to a fourth audit.

---

# Design audit - chip-dash Now view and band owed segment, spec 0071, pass 2 - 2026-10-22

verdict: FAIL (owner-blocked: the one must-fix is still open and the agent cannot close it; every design lens is clean. Once the owner allows the test change and the assertion is updated, this surface is PASS WITH FINDINGS with the one should-fix below)
pass: 2 of 3 (scope = pass 1's findings only, plus any defect the fixes created; diff since pass 1 = panes.tsx NowSection id cap and agents row, tokens.ts `pane.col.prId`, hooks/register.tsx open order, design.md lines 29-30 and 109-110)
findings: 6 -> 2 (pass 1: 1 must-fix, 5 should-fix; now: 1 must-fix owner-blocked, 1 should-fix narrowed; 4 fixed, 0 created by the fixes. The count fell, so not STOP)
ai-tell fails: 0/36        (item 10 fixed; other items as in pass 1: CSS/web items N/A, 30 passes)
token leaks: 0. token-leak.sh exit 2, NOT APPLICABLE (no tokens.css; tokens are the TS object in tokens.ts). Substitute check on the changed lines: the id cap reads `pane.col.prId` / `pane.col.repo` / `pane.specMin`, no literal widths or colors added
a11y: static only (terminal surface). Unchanged since pass 1: color is never the only signal
wcag22: not run (terminal surface); 2.5.7 no drag, 3.2.6 no help affordance, 3.3.8 no login
contrast failures: not measured (theme keys; the user's theme decides the hues)
responsive: Now clean 40-200 columns at 14 rows inline and 30 rows docked (0 of 18,144 renders over budget, 0 wider than the pane, 0 height changes across data states); 30 columns unchanged from pass 1 (2,016 over, Coverage notes). Band unchanged (same 1-line result 24-160 columns). PR rows keep the checks word whole from 41 columns and part of the title from about 45 (pass 1: about 50 and 70)
motion: none in scope (the fixes add no animation, timer or spinner)
reference: not re-run (pass 1 compared 4 sections against k9s, 0 worse)
perf: NOT MEASURED (no browser surface)

## Must fix
- [ ] OWNER-BLOCKED (pass 1 Must fix, still open) - the suite is red: `claude plugin test claude-home/mods/chip-dash` - 80 pass, 1 fail across 8 files. `dashboard.test.ts:60` still expects `SECTIONS.map(s => s.key)` to equal `['p', 'a']` and gets `['p', 'n', 'a']` (`panes.tsx:16-20`, correct per spec 0071 AC-1). The agent cannot make this edit: the Assertion Guardian hook refuses a changed assertion until the owner types `/allow-test-change`. Owner step: type `/allow-test-change`, then the assertion becomes `['p', 'n', 'a']` and the test name ("switch on p a") becomes "switch on p n a". AC-10 (suite passes) stays unmet until then.

## Should fix
1. [ ] NARROWED (pass 1 item 1) - the narrow id cap works: under `pane.specMin` the id column is capped at `pane.col.repo` (14), `panes.tsx:458`. Measured at 56 columns: `claude-conf...  ready  checks ok       A pull reque...` (pass 1: `claude-config#105         ready  checks ok       A ...`). Left: at 40 columns `failing` and `pending` lose their last letters (`checks faili...`, `checks pendi...`; the color stays), because the `checks ` label (`panes.tsx:474`) is kept. AC-3 spells the row with that label, so dropping it under 80 columns changes accepted spec text: an owner call through `/architect`, not an agent fix. 40 columns is also the width where Plan already breaks (pass 5 of the wf-dash audit, Coverage notes).

0 lower-severity findings dropped. 0 findings cut for lack of `file:line`.

## Fixed since pass 1
- [x] Item 2 - design.md's Plan footer now reads `t: next group` (`design.md:109`), narrow `t: group` (`:110`), and notes `n` went to Now. The assumed letter `t` is still recorded as the owner's to confirm (`design.md:9-11`): the owner has to be told.
- [x] Item 3 - `loadPrs(true)` now runs after `await $.ui.open(...)` (`hooks/register.tsx:76-79`), so `$.ui.panes()` lists the pane when `loadPrs` checks it (`:212`). Pinned by `now.test.ts` "AC-4 reopening the dashboard left on Now runs the search at once" (passes). Not a regression: `openDashboard` already awaited `$.ui.open` before returning its text, so `open` resolves on open, not on close.
- [x] Item 4 - the id cap has its own token, `pane.col.prId: 24` (`tokens.ts:97-98`), used at `panes.tsx:458`; a change to Plan's `col.next` no longer resizes Now's ids.
- [x] Item 5 (AI-tell item 10) - the count box grows (`panes.tsx:489`, `flexGrow={1}`), so `a: details` sits at the row's right edge whatever the counts' digits. Rendered at 84 columns: `agents 2 running, 1 shells` then `a: details` ending at column 84. can fail: pass 1's copy, rendered by the same probe, put `a: details` right after the count.

## Checked and clean
- Suite: 80 pass, 1 fail (only the owner-blocked assertion above). now.test.ts: 24 pass, the reopen test among them.
- Fixed height after the fixes: the pass 1 probe rerun on copies of the current panes.tsx, band.tsx, tokens.ts, handoff.ts (`/tmp/gate0071/probe2`): 20,160 renders, 2,016 over budget, all of them at 30 columns (the same count as pass 1), 0 wider than the pane, 0 widths with a height change. can fail: the probe still flags every 30-column render.
- design.md describes the new cap (`design.md:29-30`: "24 at most, 14 under 80 body columns").
- ASCII: no new non-ASCII in the changed files; the only hit is the allowed `·` at `panes.tsx:108`.
- Band: band.tsx has no diff since pass 1; the owed segment renders the same at 24-160 columns, one line, with and without stale.

## Coverage notes
- Per the re-audit rules, only pass 1's findings and fix-created defects were graded. Nothing new below P1 was raised.
- At 30 columns, with a count, `agents 2 running,...  a:` cuts and the `s` of `details` lands on the footer row. This is the pass 1 30-column note (the row wrapped into the footer then too), below the 40-column floor, uncounted.
- Probe limits as in pass 1: ink 5.2.1 through ink-testing-library with a stand-in Button; Claude Code's own renderer not observed live.

---

# Design audit - chip-dash Now view (panes.tsx NowSection) and band owed segment (band.tsx), spec 0071 - 2026-10-22

verdict: FAIL (one must-fix: the mod's own suite is red because an older test still asserts the two-view key list; every design lens is clean or carries only should-fixes)
pass: 1 of 3 for this surface (scope = the uncommitted diff on feat/0071-dashboard-restructure-for-the-setup-without-wf: panes.tsx, band.tsx, tokens.ts, handoff.ts, hooks/register.tsx, now.ts, types/index.d.ts)
ai-tell fails: 1/36        (item 10; items 1-9, 11-29, 31-34 and 36 are CSS/web items with nothing to grade in a terminal mod: N/A; 30 passes, 35 N/A)
token leaks: 0 color literals in the diff. token-leak.sh exit 2, NOT APPLICABLE (no tokens.css; tokens are the TS object in tokens.ts). Substitute check: every color in the new code is `color.*` or `checksTone` (which maps to `color.*`), every height is `pane.now.*`, every timing `time.prTick` / `time.prTimeout`. One token reused under another column's name (Should fix 4)
a11y: static only (terminal surface, no page to serve). Color is never the only signal: checks print their word, draft/ready print a word, unknowns print `?`, the cursor is `>` plus bold
wcag22: not run (terminal surface); 2.5.7 no drag, 3.2.6 no help affordance, 3.3.8 no login
contrast failures: not measured (every color is a Claude Code theme key; the user's theme decides the hues)
responsive: Now clean 40-200 columns at 14 rows inline and 30 rows docked (0 of 18,144 renders over budget, 0 wider than the pane, 0 height changes across data states); at 30 columns it is 16 rows (Coverage notes). Band one line 30-220 columns with and without `owed`, 0 segment collisions. PR rows lose the title below ~70 columns and the checks word below ~45 (Should fix 1)
motion: none in scope for this diff (no animation, timer-driven visual or spinner added; the handoff spinner in hooks/register.tsx was audited against review-animations in the spec 0064 passes and is unchanged)
reference: 4 sections (owed, PRs, handoff, agents) compared against k9s by reading only, 0 worse; not screenshotted (terminal)
perf: NOT MEASURED (no browser surface). Cost noted: one `gh api graphql` call per 2 minutes while Now is shown, 10 s timeout

## Must fix
- [ ] The suite is red: `claude plugin test claude-home/mods/chip-dash` - 79 pass, 1 fail. `dashboard.test.ts:60` still expects `SECTIONS.map(s => s.key)` to equal `['p', 'a']` and now gets `['p', 'n', 'a']` (`panes.tsx:16-20`). This change created it. Spec 0071 AC-10 needs the suite to pass, and AC-1 makes the new value correct. Fix: change the assertion to `['p', 'n', 'a']` and update the test name ("switch on p a") to match.

## Should fix
1. [ ] Below about 70 body columns a PR row has no room for its title, and below about 45 it loses the checks word too - `panes.tsx:457`, `:470-475`. The id column is capped at 24 cells (`pane.col.next`). With the two-cell gaps, `ready`/`draft`, the `checks ` label and the 7-cell checks word, about 50 cells are fixed before the title. Rendered at 56 columns: `claude-config#105         ready  checks ok       A ...`. At 40 columns: `claude-config#105         ready  ch...`, so the check state is gone in word and color both. Other views switch to a narrow layout under `pane.specMin` (80); Now has none. Fix: under `pane.specMin`, cap the id at `pane.col.repo` (14) and drop the `checks ` label (the colored word stays).
2. [ ] design.md still lists Plan's footer key as `n: next group` - `design.md:109`, while the code moved it to `t` (`panes.tsx:334`). design.md:10-11 records `t` as an assumed letter the owner still has to confirm: tell the owner about it, then fix line 109.
3. [ ] (PLAUSIBLE) Reopening the dashboard while it was left on Now can skip the forced search on open - `hooks/register.tsx:76-78`. `void loadPrs(true)` starts before `await $.ui.open(...)`, and `loadPrs` returns early when `$.ui.panes()` does not list the pane yet (`:211-212`). If that happens, `reading GitHub` (or the old list) shows until the next 10 s tick, which runs the search because `prStarted` is old. The AC-4 test opens Plan and presses `n` (the `go` path at `:318`), so it does not cover this order. Fix: call `loadPrs(true)` after `await $.ui.open(...)`.
4. [ ] The PR id column cap reuses the Plan's next-step width token - `panes.tsx:457` (`Math.min(pane.col.next, ...)`). The 24 comes from design.md:29, but its token is named for another column, so a later change to Plan's next column would silently resize Now's ids. Fix: add `pane.now.id: 24` beside `pane.now` (`tokens.ts:103`) and use it here.
5. [ ] AI-tell item 10 (counts not in fixed cells): `agents N running, M shells` has no fixed width, so `a: details` moves one cell to the right when a count goes from 9 to 10 - `panes.tsx:445`, `:487-488`. The band pads its counts for the same reason (design.md:87). Fix: pad both counts, or put `a: details` before the counts.

0 lower-severity findings dropped. 0 findings cut for lack of `file:line`.

## Checked and clean
- Contract, AC-1 to AC-9 against the code: top line `p: Plan  n: Now  a: Agents` (`panes.tsx:16-20`, rendered `chip   p: Plan  n: [Now]  a: Agents`); owed cases (`:398-410`); PR row format, checks mapping, `+k more on GitHub`, `no open PRs`, `reading GitHub`, stale with time (`:416-437`, `now.ts:9-33`); search only while open on Now (`hooks/register.tsx:207-228`); handoff words the same as the band's (`panes.tsx:439-443` vs `band.tsx:93-95`), link rule shared through `handoverLink` (`handoff.ts:34-37`); agents count (`hooks/register.tsx:313-315`); footer and dimmed keys (`panes.tsx:491-498`); block heights from `pane.now` (`tokens.ts:103`).
- Fixed height: the probe renders Dashboard on Now with real Ink 5.2.1 (6 owed states, 7 PR states, 4 handoff states, 2 agent counts, 3 cursor positions) at 40, 56, 64, 80, 84, 100, 120, 160 and 200 columns. Every data state gives the same frame height at each width, so a refresh never moves a row. can fail: the same probe flags all 2,016 renders at 30 columns as over budget.
- Band `owed N`: warn bold, just before `handoff`. It never prints `owed 0` or `owed ?` (`band.tsx:86-87`: lines null or empty adds no segment). It stays one line at 30-220 columns and in the compact band at 31 cells (`w:  chip     owed 12  on 200k`). The folder and git segments make room for it in drop order. can fail: the collision regex fired on a wrong-width first run (stdout fixed at 100 columns), before the probe width was corrected.
- Owed outlives facts.py: a failed facts tick still writes the fresh `owed` (`hooks/register.tsx:171-175`). Facts failing from the start still writes it, through the `{}` path (`:151-170`).
- ASCII: no new non-ASCII in now.ts, panes.tsx, band.tsx, tokens.ts or design.md. The only hit is the allowed `·` at `panes.tsx:108`. The id cut uses `glyph.cut`.
- Empty, error and loading copy exists for every block (AI-tell item 30).
- PRODUCT.md and design.md describe the Now view and the band segment (design.md:13-43, PRODUCT.md "Today").

## Coverage notes
- Probe: copies of panes.tsx, band.tsx, tokens.ts and handoff.ts in `/tmp/gate0071/probe`, rendered with ink 5.2.1 and react 18.3.1 through ink-testing-library, with the stdout width patched to match each test width and a stand-in Button that draws `<key>: <label>`. Claude Code's own renderer was not observed live, and its truncation mark may differ from Ink's.
- At 30 body columns Now takes 16 rows, because the top line and the footer wrap, and the agents row's `a: details` wraps into the footer row. The Plan view already breaks at 40 (pass 5 note below), so this is not counted.
- Below about 29 cells the compact band cuts the handoff value (`on 2...` at 26 cells beside `owed 3`). band.tsx:104-107 states this as the chosen order: owed stays, the handoff state truncates.
- `agents 1 shells` keeps the plural. That is the spec's literal wording (AC-6), so it is not counted.
- With 3 or more owed lines, the 3-row block shows one line and then `and k more`. This is the spec's row budget (AC-9), not a defect.

---

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
