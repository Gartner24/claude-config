# Design audit - wf-dash band and alerts (hooks/register.tsx feeding band.tsx) - 2026-10-18

verdict: PASS WITH FINDINGS (pass 3 stands; budget reached, no fourth pass opened; 7 should-fixes go to the owner as a list)
pass: 3 of 3 (re-stamp: the audited code is unchanged since pass 3)
ai-tell fails: 1/36        (unchanged since pass 1: item 10, counts not fixed width; no markup changed)
token leaks: 3 (token-leak.sh NOT APPLICABLE, no tokens.css; substitute check = literals in hooks/ that bypass tokens.ts, unchanged)
a11y: static only (terminal surface, no page to serve)
wcag22: not run (terminal surface, no page to serve)
contrast failures: not measured (colors are Claude Code theme keys from the user's theme)
responsive: stale band clean at the documented ~31 cell column and up (bodyColumns 23-120, pass 2); band.tsx unchanged since pass 2
motion: none in scope
reference: not re-run (pass 1: 2 sections against k9s, 0 worse; owner accepted the look at 29/40 on 2026-10-17; nothing since changed it)
perf: NOT MEASURED (no browser surface)

## Why this is not a pass 4

The caller describes this round as logic only: the stale mark is no longer cut, and a failing helper shows `?`.
Both changes are commit ee72849 (05:08). Pass 3's report was written at 05:17 and cites those exact lines
(`hooks/register.tsx:46`, `:71`, `:72`, `:97`; band.tsx stale budget `:105-112`, `:119`). Since then:

- `git diff HEAD -- claude-home/mods/wf-dash` is empty, and the only commit after 05:17 is 1b35b21, which touches
  `register.test.ts` and `docs/scope/scope.md`, not `band.tsx` or `hooks/register.tsx`.
- The 05:24 mtimes on `band.tsx` and `hooks/register.tsx` come from a later write with the same content, most
  likely the `/test` mutation check restoring from a backup. They are not a code change.

The code pass 3 graded is byte for byte the code here, so pass 3's findings stand as written. The budget allows 3
passes, and a fourth pass over unchanged code could only produce new opinions. The open items need an owner
decision, not another audit.

Finding count: pass 3 had 0 must-fixes and 7 should-fixes. This re-stamp has the same 7, with every cited line
checked against the current file.

## Must fix
None.

## Should fix (carried, for the owner to decide; this re-stamp raised none)
- [ ] (pass 2) design.md does not describe the compact stale band - `claude-home/mods/wf-dash/design.md:42-44` - line 42 still says the question count is the last to go; with a stale band ` stale` is last and the band can read `stale` alone; line 44 names only `stale since HH:MM`.
- [ ] (pass 1) A stale tick throws away the fresh runner counts it just read - `claude-home/mods/wf-dash/hooks/register.tsx:97` - `{ ...lastGood, staleSince }` keeps `lastGood.wf`, so the band can show `wf 2 building ... stale since 10:42` while `wf status` said 3.
- [ ] (pass 1) `finished` toasted for a run that parked or lost its lock - `claude-home/mods/wf-dash/alerts.ts:29` - spec 0059 AC-3 wording, a decision for `/architect`.
- [ ] (pass 1) Alerts view empty state is the same whether wf was watched or unreadable - `claude-home/mods/wf-dash/panes.tsx:436` with `hooks/register.tsx:66-67`.
- [ ] (pass 1) Theme key and width literals bypass tokens.ts - `claude-home/mods/wf-dash/hooks/register.tsx:171` (`color="inactive"`, is `color.dim`), `:177` and `:193` (`?? 80`).
- [ ] (pass 1) Runner counts not fixed width - `claude-home/mods/wf-dash/band.tsx:57` and `:115-117`; `width.count` in `tokens.ts` unused. AI-tell item 10.
- [ ] (pass 1) Docs name removed commands - `claude-home/mods/wf-dash/design.md:108` (`/wf-dash-alerts`), `design.md:13` and `tokens.ts:42` (`/wf-alerts`).

## Checked and clean
- Unchanged code: working tree equals HEAD for the whole mod; the band.tsx and hooks/register.tsx diff since ab1a9d4 is exactly ee72849, which pass 3 audited.
- Suite: `claude plugin test claude-home/mods/wf-dash` - 28 pass, 0 fail across 4 files (pass 3 had 27; the new one is `register.test.ts`).
- Pass 3 coverage gap closed in part: `register.test.ts` (1b35b21) now drives `register.tsx` through `session.start` and the band tick. It asserts that live runner counts and `folder: null` hold while facts.py fails from the start, and that `staleSince` is set only after a later failure. This is the behavior pass 3 checked in its scratch harness.

## Coverage notes
- This audit did not mutation-check the new repo test. A revert of `hooks/register.tsx:72` to the pass 2 form (`lastGood ? null : {}`) was refused by the session's permission classifier, and the file was left as it was. Pass 3's scratch harness saw that same mutant go red. Whether `register.test.ts` goes red on it is for `/test` to confirm under its own mutation-check gate.
- Below P1, carried from pass 3 and not re-raised: `hooks/register.tsx:68` `JSON.parse` throws when facts.py exits 0 with non-JSON output; compact `idle stale` and `? status stale` are not budgeted (`band.tsx:104`, `:98`).
- 0 findings cut for lack of `file:line`.
