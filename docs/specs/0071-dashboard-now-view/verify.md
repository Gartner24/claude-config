# 0071 verify

## Probe before the build (build plan step 1)

Run 2026-10-22, Claude Code 2.1.308, with a throwaway mod outside the repo (`probe-0071`): its `session.start` ran the
AC-3 call through `$.process.run` and wrote the result to a file. Started headless, so no TTY:

```
claude -p "reply with the word ok" --plugin-dir <probe mod> --setting-sources user --strict-mcp-config --model haiku
```

The call, as the mod runs it (argument list, no shell):

```
$.process.run(['gh', 'api', 'graphql', '-f', 'query=query { search(query: "is:pr is:open author:@me sort:updated-desc", type: ISSUE, first: 20) { issueCount nodes { ... on PullRequest { number title isDraft url repository { name } commits(last: 1) { nodes { commit { statusCheckRollup { state } } } } } } } }'], { timeoutMs: 10000 })
```

- [x] P1 auth with no TTY: exit 0, empty stderr; `gh` used the owner's stored login. PASS.
- [x] P1 timeout: answered in 2123 ms, inside the 10 s timeout. PASS.
- [x] P1 fields: `data.search.issueCount` 10, 10 nodes, each with `number`, `title`, `isDraft`, `url`, `repository.name`
  and `commits.nodes[0].commit.statusCheckRollup` (7 `{state: "FAILURE"}`, 2 `{state: "SUCCESS"}`, 1 `null`, so the
  "no rollup" case is real). `author:@me` works in the GraphQL search. PASS.
- Repo names and titles from the answer are not recorded here: they name work repos (public repo rule).

Result: PASS, the build goes on.

## Verify against the ACs (2026-10-22, the build)

Each step runs the mod's own code through `claude plugin test claude-home/mods/chip-dash` (the test kit drives
`register.tsx` with a stand-in host); every test named here was mutation checked (list below).

- [x] AC-1: `SECTIONS` is `p: Plan`, `n: Now`, `a: Agents` (`panes.tsx:16-20`); the dashboard opens on Plan; `n` opens
  Now; `/chip` and `/wf-dash` both register and open (`hooks/register.tsx:241`, `:245`, `dashboard.test.ts` "both open").
  Plan's next group moved `n` to `t` (`panes.tsx:334`): two buttons on one hotkey, the later wins, so `n` on Plan's
  footer would have beaten the top line. Test `now.test.ts:86`. can fail: Plan keeps `n` for next group, then `n`
  pressed on Plan never opens Now (mutant M1 reddens this test and 17 others).
  OPEN: `dashboard.test.ts:60` still expects `['p', 'a']`; the Assertion Guardian refuses the change until the owner
  types `/allow-test-change` (1 failing test).
- [x] AC-2: `readOwed` (`hooks/register.tsx:121-131`) tries this chat's id, then `prev`; `parseOwed` (`now.ts:36-41`);
  `owedLines` (`panes.tsx:398-410`). Tests `now.test.ts:99` (no folder: `catch not installed (row 92)`), `:104` (no file
  for this chat, then an empty list: `nothing owed`), `:113` (broken JSON: `owed ?` and the error), `:120` (each line),
  `:127` (after `/clear`, the replaced id's file). can fail: a parse error read as an empty list prints `nothing owed`
  (M4), or the `prev` id left out of the loop (M6).
- [x] AC-3: one call, `prArgv()` (`now.ts:5-6`) with the probe's query, run with `timeoutMs: 10000`
  (`hooks/register.tsx:219`); rows in `prBlock` and `NowSection` (`panes.tsx:416-437`, `:462-481`). Tests `now.test.ts:139`
  (argv, rows `here#4   ready  checks failing  Fix it`), `:151` (mapping, plus `?` for an undocumented state),
  `:164` (`+7 more on GitHub` from issueCount 27), `:171` (`no open PRs`), `:177` (a failed call keeps the list,
  `stale since HH:MM: <stderr line>`), `:186` (`reading GitHub`, count `?`), `:196` (a first failure: `?` and the error,
  never `no open PRs`). can fail: a failed call stores `data: null` and the list empties (M11); the count before the
  first answer shows 0 (M12).
- [x] AC-4: `loadPrs` (`hooks/register.tsx:208-228`) returns unless the engine lists the pane open and the view is
  `now`; forced on Now opening (`:319`), on `r` (`:323`) and on reopening the dashboard (`:79`); otherwise only when
  `time.prTick` passed, on the 10 s panes tick. Tests `now.test.ts:205` (0 calls in 5 minutes closed and 5 minutes on
  Plan; 1 on `n`; 2 at the first tick past 2 minutes; 3 on `r`; none on Plan with `r`; 4 back on Now; none after close),
  `:233` (close stops it), the reopen test (1 then 2). can fail: the view check dropped, Plan calls GitHub (M14); the
  open check falls back to the module flag after a close (M15).
- [x] AC-5: `handoffLines` (`panes.tsx:439-443`) uses the band's words and the band's source (`HANDOFF.auto`, the
  chain file that holds the per folder off since row 95); the link through `handoverLink` (`handoff.ts:34-37`), which the
  band's own link line now calls. Tests `now.test.ts` AC-5 pair: `handoff on 250k`, `last handover: <link>`,
  `handoff off`, `handoff ?`; no link without `previous`. can fail: the link rule loses its `previous` check (M17).
- [x] AC-6: `count` (`hooks/register.tsx:314`) from `$.agent.list()` and `shells($)`, the Agents view's lists; `shells`
  now returns null on an unreadable transcript (`:43-46`) and the Agents view keeps its old `[]` there. Test AC-6:
  `agents 2 running, 1 shells` from 2 running of 3 agents and 2 shells with one stopped; `agents ?` when either list
  fails. can fail: counting every listed agent as running (M18).
- [x] AC-7: `segments` adds `owed N` warn bold only when N > 0 (`band.tsx:86-87`), drawn before `handoff`
  (`:162`), counted in `fit()`, never dropped by it (`:108`), kept in the compact band (`:144-147`); read each 5 s band
  tick, also while `facts.py` fails (`hooks/register.tsx:169`, the stale branch). Tests: count shown, nothing at 0, on
  a broken file, without the folder, before the first read; kept past the model and in the 31-cell column; the tick
  reads the file and drops the segment when it empties. can fail: `owed 0` printed (M19); owed dropped in the compact
  band (M20); the tick never writes owed into the facts (M21).
  Note: the 31-cell column is 2 cells short for `owed N` beside `on 200k`, so the handoff state truncates at its end
  there (the band's existing rule), rather than `owed` dropping.
- [x] AC-8: footer `j: down  k: up  r: refresh  esc closes` on one row (`panes.tsx:491-499`); `j` and `k` dim at the
  ends; no action key. Test AC-8/AC-9: `k` dim at the top, lit after `j`. can fail: the list never scrolls (M23).
- [x] AC-9: fixed heights from `pane.now` (owed 3, PRs 6, handoff 2, agents 1; `tokens.ts:103`, `panes.tsx:461-486`),
  docked extra rows to PRs; `and k more` for owed, `N above, +M more, +K more on GitHub` for PRs; titles truncate.
  Tests AC-9 owed overflow and AC-8/AC-9 PR overflow. design-gate pass 1 and 2 rendered every data state with Ink 5.2.1
  at 40-200 columns: 0 over the 14 rows, 0 height changes. can fail: owed past 3 rows shown whole (M22).
- [ ] AC-10: mod tests 80 pass, 1 fail (the owner-blocked `dashboard.test.ts:60` above); `claude plugin validate`
  passes; design-gate pass 2: FAIL on that one must-fix only, every design lens clean, 2 should-fix left
  (`.design/audit-report.md`). Not met until `/allow-test-change`.

### Mutation checks (each: cp backup, mutate, run the mod's tests, test red, restore, green)
The kit has no single file mode; each mutant ran the mod's 81 tests (about 4 s). After every restore: 80 pass, 1 fail
(the owner-blocked test).
M1 Plan next group back on `n` -> AC-1 red. M2 no folder read as nothing owed -> AC-2 no folder red. M3 no file read as
`?` -> AC-2 no file red. M4 parse error as empty -> AC-2 broken red. M5 first owed line dropped -> AC-2 lines red. M6
`prev` left out -> AC-2 clear red. M7 draft and ready swapped -> AC-3 rows red. M8 ERROR not failing -> AC-3 mapping
red. M9 no GitHub overflow -> AC-3 more than 20 red. M10 empty list says nothing -> AC-3 zero red. M11 failure empties
the list -> AC-3 stale red. M12 unknown count as 0 -> AC-3 reading red. M13 first failure says reading -> AC-3 first
failure red. M14 no view check -> AC-4 calls red. M15 open check falls back past a close -> AC-4 close red. M16 off
says on -> AC-5 red. M17 link without previous -> AC-5 no previous red. M18 every agent counted running -> AC-6 red.
M19 `owed 0` printed -> AC-7 shown red. M20 owed droppable -> AC-7 compact red. M21 tick skips owed -> AC-7 tick red.
M22 owed overflow shown whole -> AC-9 owed red. M23 no scroll -> AC-8/AC-9 PRs red. M24 no search on reopen -> AC-4
reopen red. M25 search started before the pane opens: survived (the kit's stand-in host lists the pane at once; the
engine's timing is not reproducible here, so the order is kept by the comment at `hooks/register.tsx:77-78`).

### Suite
`python3 runner/tests/fast.py`: 1136 tests, 0 failed.
