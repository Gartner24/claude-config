# 0071. Dashboard restructure: a Now view and an owed count for the setup without wf

**Date**: 2026-10-22
**Status**: Accepted
**Paths:** `claude-home/mods/chip-dash/**`

## What you're agreeing to
- The dashboard gets a third view, Now (key `n`): the steps this chat owes, your open PRs, the handoff state and a count of running agents, in that order.
- Your open PRs, with their check state, come from one GitHub search for PRs you opened, fetched only while the Now view is open: on open, on `r`, and every 2 minutes.
- The band shows `owed N` in warn color when this chat owes a step, and nothing when it owes none.
- Plan and Agents stay as they are.
- The build starts after the auto handoff fix (row 95) and the rename to chip-dash (row 96) merge, since it reads both.

## Summary
The runner parts are already gone from the dashboard; what is missing is today's setup. Spec 0070's catch saves what a chat owes, spec 0069 and the wf-handoff mod keep the handoff state and the handover, and the parallel builds open PRs in several repos. This spec adds one view that answers "what is next for this chat right now", and one short band segment for the owed step.

## Context
- The mod is `claude-home/mods/chip-dash/` after row 96 (today `wf-dash/`). Views today: Plan (`p`, `plan.py`) and Agents (`a`). The band's right end shows the auto handoff from wf-handoff's files; `handoff.ts` reads wf-handoff's `panel.json` (spec 0064) for the handover link.
- Spec 0070 (accepted, not built) writes `~/.claude/state/chain-catch/<session id>.json` with `owed` (list of text) and `blocks`.
- Row 95 changes where the auto handoff on/off lives (per folder instead of per chat). This spec reads whatever wf-handoff's files say after that fix; it adds no state of its own for it.
- Design rules stay (`design.md`, `PRODUCT.md`): theme keys only, ASCII only, unknown is `?` never 0, a failed fetch keeps the last good value marked stale, never pushes, merges or deletes.

## Requirements

**User stories**:
- As the owner, I want one screen that shows what this chat still owes, which of my PRs wait, and whether this chat will hand off by itself, so that I never ask where things stand.

**Acceptance criteria**:
- **AC-1** (views and command): the top line reads `p: Plan  n: Now  a: Agents`; `n` opens Now. The dashboard opens on Plan, as today. `/chip` opens it and `/wf-dash` stays as an alias (built by row 96; this spec keeps both working).
- **AC-2** (owed): Now's first block, `owed N`, lists each line of `owed` from the catch state file, one per row, in warn. The file read is this chat's id, else the id this chat replaced after a `/clear` (`prev`, as `register.tsx` keeps it). Cases: no `~/.claude/state/chain-catch/` folder: `catch not installed (row 92)`, dim; the folder but no file for either id, or an empty `owed`: `nothing owed`, dim; a file that does not parse: `owed ?` and the parse error in dim.
- **AC-3** (PRs): the second block, `your PRs N`, comes from one call: `gh api graphql` with a `search(query: "is:pr is:open author:@me sort:updated-desc", type: ISSUE, first: 20)` query returning, per PR, repository `name`, `number`, `title`, `isDraft`, `url`, and the last commit's `statusCheckRollup.state`. One row each, newest update first: `<repo name>#<number>  draft|ready  checks ok|failing|pending|none  <title>`. Checks mapping: `SUCCESS` ok; `FAILURE` or `ERROR` failing; `PENDING` or `EXPECTED` pending; no rollup none. More than 20 open: a dim `+k more on GitHub` line (k from `issueCount`). Zero results: `no open PRs`. A failed call keeps the last list with `stale since HH:MM: <error>`; before the first call ends, `reading GitHub`.
- **AC-4** (PR refresh): the call runs when Now opens, on `r`, and every 2 minutes while the dashboard is open and its view (`$.state` `VIEW` `section`) is `now`; never while closed or on another view. The list lives in its own `$.state` key; the 2 minute check rides the panes' existing tick.
- **AC-5** (handoff): the third block reads `handoff on <line>`, `handoff off` (for this folder, after row 95) with the same words and source as the band, plus `last handover: <link>` under the same condition the band uses for its link line (`handoff.ts`: the panel names this chat, has `previous` and a `link`). Unknown: `handoff ?`. Built after row 95 merges, reading its final file shape.
- **AC-6** (agents): the last line is `agents N running, M shells` from the Agents view's source (`$.agent.list()` and `shells($)`), also fetched while Now is shown: N counts agents with status `running`, M counts shells not stopped or finished. With `a: details`. Unknown: `agents ?`.
- **AC-7** (band owed): the band shows `owed N` in warn bold as a right side segment just before `handoff`, when this chat's `owed` (same file rule as AC-2) has N > 0 lines; nothing when 0, missing or unreadable (the band never prints `owed 0` or `owed ?`). It is read on the band's 5 second refresh into `Facts`, counted in `fit()`, is the last segment to drop, and stays in the compact band.
- **AC-8** (keys): Now's footer `j: down  k: up  r: refresh  esc closes`; `j`/`k` move a `>` cursor over PR rows and scroll the list. Keys dim when they would do nothing, as the other views. Now has no action.
- **AC-9** (height and width): Now keeps the dashboard's fixed height (padded blank, no layout shift on refresh). Row budget in the 14 row pane: owed up to 3 rows (`and k more` past that), PRs up to 6 rows (`+k more` past that, scrolled by `j`/`k`), handoff 2 rows, agents 1 row; a taller docked pane gives the extra rows to PRs. PR titles truncate, never wrap.
- **AC-10** (tests): mod tests cover AC-2 (each case, and a `/clear` reading `prev`), AC-3 (list, checks mapping, more than 20, empty, failed keeps stale, reading), AC-4 (no call while closed or on Plan), AC-5 (on, off, unknown), AC-6 (counting rule), AC-7 (count shown, nothing at 0 and on unreadable, kept when narrow), AC-9 (overflow lines), each mutation checked; `claude plugin test claude-home/mods/chip-dash` passes and the `design-gate` audit passes.

## Decision
**Chosen** (owner, 2026-10-22, all panel answers in `docs/briefs/dashboard-restructure.md`):
1. A new Now view; Plan and Agents stay.
2. PRs: every open PR you opened, one `gh search prs --author @me` call.
3. Band: a short `owed N` count, gone at zero.
4. Now order: owed, PRs, handoff, agents.
5. PR refresh: on open, `r`, and every 2 minutes while open.
6. Name: chip-dash (row 96, built separately).

## Rationale
Today's new state is about this chat (owed step, handoff, the PRs a parallel build opened), while Plan is the whole backlog; one view for each keeps both readable. One search call covers every repo the parallel agents touch. Fetching only while the view is open keeps chats that never look from calling GitHub.

## Options considered
1. Views: **add Now** (picked); fold into Plan and the band; Plan and band only.
2. PRs: **all mine, one search** (picked); every scope repo; this chat's repo.
3. Band: **short owed count** (picked); full owed line; Now view only.
4. Order: **owed, PRs, handoff, agents** (picked); handoff first; two columns when wide.
5. Refresh: **open, r, 2 minutes while open** (picked); open and r only; background with a band count.

## Feature design

**Data model**: none new. Reads only: the catch state file (spec 0070 data model), wf-handoff's files the band already reads, `gh` output.

**Value sourcing**:
| Value | Source |
|---|---|
| owed lines | `~/.claude/state/chain-catch/<session id>.json` `owed` (spec 0070) |
| session id | the mod's session (as `handoff.ts` uses `h.me`) |
| PR list and checks | one `gh api graphql` search call (AC-3), run through `$.process.run` with a 10 s timeout |
| handoff on/off and line | the same wf-handoff file the band reads (after row 95) |
| last handover link | wf-handoff `panel.json` `link`, `ours` rule |
| agents and shells | the Agents view's source |
| stale time | the time of the last good fetch |

**Key invariants**: unknown is never 0; a failed fetch never empties a list; no GitHub call while Now is not shown; the view changes nothing.

**Critical test scenarios**: owed file missing, empty, broken, with lines; `gh` fails after a good list (stale shown, list kept); Plan shown for 5 minutes makes no `gh` call; band at `owed 0` shows nothing.

## Build plan
Starts after rows 95 and 96 merge (it reads the per folder handoff state and lives in `chip-dash/`); one branch `feat/0071-dashboard-restructure-for-the-setup-without-wf` off main.
1. Probe first, result in `docs/specs/0071-dashboard-now-view/verify.md`; a FAIL stops the build and goes back to `/architect`: the AC-3 `gh api graphql` call run through `$.process.run` from the mod (auth, no TTY, timeout, the fields returned). Then the readers: owed file, the PR call, with tests for each state, satisfies **AC-2**, **AC-3**, **AC-4**.
2. The Now view in `panes.tsx` with its keys and fixed height, the `n` view key, satisfies **AC-1**, **AC-5**, **AC-6**, **AC-8**, **AC-9**.
3. The band `owed N` segment and its narrow order in `band.tsx`, satisfies **AC-7**.
4. Update `design.md` (Now view section, band segment) and `PRODUCT.md` surfaces; run the `design` pipeline's gate (`design-gate`) on the Now view, satisfies **AC-10**.

## Consequences
**Positive**: one place shows what this chat owes and which PRs wait; the band flags a skipped step.
**Negative / tradeoffs**: Now depends on spec 0070's state file and shows `catch not installed` until row 92 is built; one GitHub call every 2 minutes while Now is open.
**Neutral**: PRs others opened for you are not listed; Plan and Agents are unchanged.
