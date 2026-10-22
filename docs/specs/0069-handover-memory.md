# 0069. Handover memory: four kinds, quoted, one index per feature

**Date**: 2026-10-22
**Status**: Proposed
**Paths:** `claude-home/mods/wf-handoff/templates/*.md`, `claude-home/mods/wf-handoff/hooks/register.ts`, `claude-home/mods/wf-handoff/tests/**`, `claude-home/rules/handover-carry.md`, `claude-home/rules/check-gates.md`, `claude-home/CLAUDE.md`, `scripts/handover-memory.py`

## What you're agreeing to
- A handover keeps only four things: open questions, things shown to you that are still needed, agreed decisions, and helpers still running. Your raw messages, the reasoning and the mistakes are never saved.
- A small helper writes them at each handoff, and every item carries a word for word quote of the message it came from; an item whose quote is not found in the chat is dropped by a script.
- In a repo each feature gets one short index file plus detail files next to it; outside a repo one folder under `~/.claude/state/`. Never `/tmp`. The new chat reads only the index and opens a detail file when it needs it.
- Every item has a status and a date. Open items are never deleted on their own and show their age; finished items move to an archive and are deleted after 14 days or when the feature closes.
- One brief per feature: when the feature closes, `/sync` checks every agreed item landed in a spec, `AGENTS.md` or the scope, then deletes the brief; it warns about briefs no row cites and links to briefs that do not exist.

## Summary
Today the auto handoff writes a long handover into the jjstack slot: every owner message word for word, tried and failed notes, files, open ends (`templates/sections.md`). The 2026-10-22 audit found lists and reports shrink to a summary, open decisions hide behind the last request, files sit in `/tmp` and vanish, and false lessons ("every tool call is refused") travel down the chain. The owner rejected "save everything shown" and agreed this design instead: the cost-of-remembering idea (a public MIT repo of github.com/RinDig: file each conversation into a small folder tree, a later agent reads the top and walks down only when needed), cut to four kinds of item, each tied to a quote. The feature's brief becomes that index, so the brief lifecycle and the handover memory are one file.

## Sources (agreed by the owner, quoted)
- [retire-runner.md](../briefs/retire-runner.md) "Promised work, do not drop (2026-10-22)": "Handoff keeps only four kinds (open questions, deliverables still needed, agreed decisions, live state); a writer helper quotes the source of each item or drops it."; "Index file per feature in a repo, ~/.claude/state/ outside a repo, never /tmp; new chat reads the index only."; "Tracking: every item has status and date; open items never auto-deleted and show their age; done items archived, removed after 14 days or when the feature closes."; "Brief lifecycle: one brief per feature, /sync checks agreed items landed then deletes it, warns on uncited or broken brief links".
- Same brief, "Owner answers 2026-10-22": fix 1 "(save everything shown): NO. Too much context, and it would carry bad prompts and mistakes."; "Decisions 2026-10-22 (second chat)": "Temp files: router + leaves design from handoff-brain-research.md; open items never auto-deleted, resolved items archived then removed after 14 days or when the feature closes."
- [handoff-brain-research.md](../briefs/handoff-brain-research.md) "Proposed handoff design" 1 to 5 (kinds, writer, where, deletion, reading).
- [handoff-loss-audit.md](../briefs/handoff-loss-audit.md) fixes 2 and 6 (fix 1 is replaced by this design).
- [jsm-course-check.md](../briefs/jsm-course-check.md) section 3 (brief lifecycle steps 1 to 5).
- The chat request of 2026-10-22 that ordered this spec: "raw prompts, reasoning and mistakes are never saved"; "the new chat reads only the index (about 500 tokens)".

## Context
- `hooks/register.ts` `beginHandoff()` (line 287) fills `templates/sections.md` and runs `/rollover` with it through `$.command.run`; `finishRollover()` (line 310) finds the slot, adds the facts block and clears; `seed()` (line 363) runs `/resume-from-clear` with `templates/instructions.md`. Templates are read from `~/.claude/auto-handoff/<name>.md` first, the mod copy second (`template()`, line 258).
- A typed `/rollover` (no mod) gets no sections template; the vendored jjstack rollover asks for a short handover and is overwritten on every pull, so a change for it must live in a rule (`rules/handover-carry.md`), never in the skill.
- `startHandoff()` (line 271) already waits for running background agents (fix 5, PR #133).
- `rules/check-gates.md` gate 4 reads a brief's `## Agreed so far, do not ask again` section; gate 3 shows the pattern for a check `/sync` runs from a rule (`spec-paths`), since `/sync` itself is vendored.
- `~/.claude/CLAUDE.md` `### Context` writes the brief rule; `claude-home/CLAUDE.md` and `claude-home/rules/` are copied files (live wins): the build edits the live file, then `bin/sync.sh`.
- No daemon and no vector store: the MemPalace trial showed search stores get polluted and claude-mem was removed (handoff-brain-research.md, Verdict).

## Data model (the owner approves this)

### Where the files live
| Case | Index | Detail files | Archive |
|---|---|---|---|
| Repo, feature known | `docs/briefs/<feature-slug>.md` | `docs/briefs/<feature-slug>/<id>.md` | `docs/briefs/<feature-slug>/archive.md` |
| Bot-reviewed repo | same under `.workflow/briefs/` | same | same |
| Repo, no feature in this chat | `docs/briefs/general.md` | `docs/briefs/general/` | `docs/briefs/general/archive.md` |
| No repo | `~/.claude/state/handover/<project>/index.md` | same folder, `<id>.md` | same folder, `archive.md` |

`<feature-slug>` is the scope row heading in lower case with runs of other characters as `-` (the rule `branch-pr.md` uses for branch names); when the row's `Source:` already names a brief, that file is the index. `<project>` is the start folder's real path with `/` as `-` (the name Claude Code gives its project folder). The index is the feature's brief: one file, not two (Open decision 4).

### Index file format
```
# <feature heading>: brief and handover memory
**Feature:** <scope file path> row <n> | none
**Updated:** <YYYY-MM-DD HH:MM> by <session id, 8 chars>

## Open questions
<item lines, or "- none">

## Shown to the owner, still needed
<item lines, or "- none">

## Agreed so far, do not ask again
<item lines, or "- none">

## Live state
<item lines, or "- none">
```

Item line, one line each, fields split by ` | `:
```
- <id> | <status> | <date> | <text> | <who> <session8> "<quote>" | <detail>
```
| Field | Values | Rule |
|---|---|---|
| id | `Q<n>` question, `S<n>` shown and still needed, `D<n>` agreed decision, `L<n>` live state | never reused inside one index, archive included |
| status | `open`, `done` | `Q` done = answered (the answer becomes a `D` item); `S` done = no longer needed; `D` done = landed in a spec, `AGENTS.md` or scope, written as `landed: <path>` in the detail field; `L` done = the helper finished |
| date | `YYYY-MM-DD` | the day the item was first written; age = today minus this date, shown as `open <n>d` by the reader and the script |
| text | at most 120 characters | one plain sentence |
| who | `owner` or `claude` | whose message the quote is from (`claude` only for text shown to the owner) |
| session8 | first 8 characters of the chat's session id | finds the transcript the quote is checked against |
| quote | at most 160 characters, straight quotes inside replaced by `'` | an exact substring of that message's text after collapsing runs of whitespace |
| detail | `-`, a path relative to the index, or `landed: <path>` | a shown deliverable is saved word for word in its detail file |

Only `open` items stay in the index. A `done` item moves to `archive.md` with ` | done <YYYY-MM-DD>` appended. The index stays under about 500 tokens (owner figure), checked as 2000 characters by the script (4 characters a token); over that it prints a warning naming the longest lines, and never deletes an open item to fit.

### Example (`docs/briefs/handover-memory.md`)
```
# Handover memory: brief and handover memory
**Feature:** docs/scope/scope.md row 90
**Updated:** 2026-10-22 18:40 by 3f2a1b9c

## Open questions
- Q1 | open | 2026-10-22 | Save then remove the six unused local MCP servers? | claude 9c41d07e "Open question to the owner: save then remove the six unused local MCP servers" | -

## Shown to the owner, still needed
- S1 | open | 2026-10-22 | Runner feature list, 62 rows with a recommendation each | claude 9c41d07e "Full table with a recommendation per feature" | S1.md

## Agreed so far, do not ask again
- D1 | open | 2026-10-22 | Finished items are deleted 14 days after they are done | owner 3f2a1b9c "resolved items archived then removed after 14 days or when the feature closes" | -
- D2 | open | 2026-10-22 | Handoff line stays 250k in coding chats | owner 3f2a1b9c "Handoff line stays 250k" | -

## Live state
- L1 | open | 2026-10-22 | Research agent on gated course lessons, id a81f3c2e | claude 3f2a1b9c "Gated course lessons: deep research on public discussion running" | -
```
`archive.md` line after D2 lands:
```
- D2 | done | 2026-10-22 | Handoff line stays 250k in coding chats | owner 3f2a1b9c "Handoff line stays 250k" | landed: docs/specs/0063-auto-handoff.md | done 2026-10-23
```

## Requirements
- **AC-1** (four kinds only): the writer helper writes only `Q`, `S`, `D` and `L` items. The handover never holds a copy of the owner's messages, reasoning, tool output, or "tried and failed" notes; `templates/sections.md` loses its "What the owner said" and "Tried and failed, and gotchas" sections (Open decision 5 for what the slot keeps). A lasting trap found in the chat goes to `AGENTS.md` or memory through the normal paths, not the handover.
- **AC-2** (quote or drop): `scripts/handover-memory.py check <index> --transcript <jsonl>` reads every item whose session8 matches the transcript's session and looks for its quote in that session's owner messages (`who owner`) or assistant text (`who claude`), after collapsing whitespace. An item with no match is removed from the index and printed as `dropped: <id> <text>`; items from older sessions are left as they are (checked when written). Exit 0 with the dropped list; exit 1 only on a file it cannot parse, naming the line.
- **AC-3** (writer at handoff): at every auto handoff and every typed `/rollover`, the writer helper (where it runs: Open decision 1) gets the transcript path, the current index if any, and the item format; it adds new items, marks finished ones `done`, never edits a quote of an existing item, and then AC-2 runs on its output. A newer owner message wins over an older item: the writer marks the older `D` item `done` with `detail: replaced by D<n>`.
- **AC-4** (no /tmp): before the index is written, every file the chat made under `/tmp` or the session scratchpad that an `S` item needs is moved into the detail folder and the item points at it. `rules/handover-carry.md` says a deliverable is saved as an `S` detail file the moment it is shown (fix 6), not at the handoff.
- **AC-5** (new chat reads only the index): `templates/instructions.md` tells the fresh chat to read the index named in the slot and nothing else at start; its first turn lists every open `Q` item with its age, the title of every open `S` item, every `L` item to check, and says plainly which items AC-2 dropped (fix 2: show what is pending, say what could not be recovered). A detail file is opened only when the next step needs it.
- **AC-6** (status, age, archive): `handover-memory.py prune <index>` moves `done` items to `archive.md` and deletes archive lines whose done date is more than 14 days before today; it never touches an `open` item. It runs at each handoff after AC-2 and from `/sync` (AC-8). With no daemon, "after 14 days" means at the first handoff or `/sync` after that day.
- **AC-7** (ages shown): `handover-memory.py ages <index>` prints each open item as `<id> open <n>d <text>`; AC-5's first turn uses it.
- **AC-8** (brief lifecycle in /sync): a new gate 5 in `rules/check-gates.md` (it beats the vendored `/sync`): when `/sync` closes a feature (`· done`), it runs `handover-memory.py close <index>`. That exits 1 and names each item when any `Q`, `S` or `L` item is still `open`, or any `D` item is not `done` with a `landed:` path that exists in the repo (how landing is found: Open decision 3). On exit 0 `/sync` deletes the index, its detail folder and archive with `git rm`, and points the row's `Source:` at the last commit that had it.
- **AC-9** (brief links): on every `/sync`, `handover-memory.py lint <repo>` prints `warning: uncited brief <path>` for each brief no scope row's `Source:` names and `warning: broken brief link <row> <path>` for each `Source:` naming a missing brief; `/sync` copies them under a heading `Briefs to tidy` and never stops on them.
- **AC-10** (one brief per feature): `~/.claude/CLAUDE.md` `### Context` says a feature has one brief, which is its handover index; the rule for writing it stays next to the creation rule (course check step 5).
- **AC-11** (tests): `handover-memory.py --test` covers AC-2 (a made up quote dropped, a real one kept, an older session left alone), AC-6 (a 15 day old done line deleted, a 13 day old one kept, an open item of any age kept), AC-8 (an open item and an unlanded decision each exit 1) and AC-9 (both warnings); each test mutation checked. Mod changes keep `claude plugin test claude-home/mods/wf-handoff` green, with a test that the sections template no longer asks for owner messages.
- **AC-12** (replay before live): replay the 11 audited handoffs of handoff-loss-audit.md: run the writer and AC-2 on each old transcript and count open questions, shown lists and decisions that reach the index against the audit's numbers. Results in `docs/specs/0069-handover-memory/verify.md`. A replay that keeps fewer open decisions than today's slots stops the build and goes back to `/architect`.

## Open decisions (the owner picks; each has a recommendation)

### 1. Where the writer helper runs
- **A. In the handoff mod's rollover turn (recommended).** `sections.md` tells the rollover turn to start one writer agent (Agent tool, sonnet, effort low) with the transcript path, wait for it, then run AC-2 and AC-6. A rule line in `handover-carry.md` makes a typed `/rollover` do the same. Gains: no new mod API, works today, the mod already waits for agents. Risk: it depends on the model following the template; AC-2 catches made up items but not missing ones. Needs a probe: a foreground agent inside the mod-started rollover turn finishes before the slot check.
- **B. The mod runs it itself as code.** After the slot is written, `register.ts` runs `claude -p` with the writer prompt through `$.process.run`, then the script. Gains: runs every time, not up to the model. Risk: a second Claude process inside the handoff makes it slower (the owner asked for faster), and a typed `/rollover` still needs option A's rule.
- **C. Rule text only.** The model writes the items itself during any handoff, no helper. Gains: least to build. Risk: it is not the "small writer helper" agreed, and the chat that made the mistakes judges its own items.
Why A: the agreed helper with the least new code, and the quote check is code either way.

### 2. File format
- **A. Markdown, one line per item, fields split by ` | ` (recommended, used in the data model above).** Gains: readable in git and on GitHub, the brief stays a brief, gate 4 keeps reading its "Agreed so far" section. Risk: a `|` inside text needs care (the script refuses the line and names it).
- **B. JSON index plus markdown detail files.** Gains: exact parsing. Risk: nobody reads JSON in a PR, and the brief would become two files.
- **C. Markdown with a YAML header per item.** Gains: room for more fields later. Risk: longer index, harder to keep under 500 tokens.
Why A: smallest, readable, and it is already how briefs and scope rows look.

### 3. How /sync knows an agreed item landed
- **A. A `landed:` path written when the item is written down (recommended).** Whoever puts a `D` item into a spec, `AGENTS.md` or the scope (`/architect` usually) sets it `done` with `landed: <path>`; at close the script only checks the path exists. Gains: exact, cheap, no guessing. Risk: an item written down without the mark shows as not landed, and `/sync` stops to ask (safe direction).
- **B. The script searches specs, `AGENTS.md` and scope for the item's quote or key words.** Gains: nothing to mark by hand. Risk: specs reword decisions, so it misses real landings and finds false ones.
- **C. `/sync` reads the items and the spec and judges.** Gains: handles rewording. Risk: a model judging its own work, the failure the check gates exist to stop.
Why A: it fails safe and needs no judgement.

### 4. Index and brief: one file or two
- **A. One file: the feature's brief is the index (recommended, used above).** Gains: one place, the "one brief per feature" rule and the handover memory share one lifecycle. Risk: an existing long brief (`tool-review-2026-10.md`, 25 KB) must be split by row first (already promised).
- **B. Two files: the brief stays, the index sits beside it in `docs/briefs/<slug>/index.md`.** Gains: old briefs untouched. Risk: agreed decisions live in two places and drift.
Why A: two copies of agreed decisions is the drift the course check found.

### 5. What the jjstack slot keeps
- **A. Next actions, the last request with its status, the facts block, and the index path (recommended).** The owner message copy, tried and failed notes, and the fresh chat's `jq` read of every owner message go. Gains: matches "never saved" and "reads only the index". Risk: the safety net that "the messages win" is gone; AC-12's replay is what shows whether that loses anything.
- **B. Same as A, but keep the `jq` read of owner messages at start.** Gains: keeps today's safety net. Risk: thousands of tokens at every start, against the 500 token agreement.
Why A: it is what was agreed; B stays possible if the replay shows losses.

## Build plan
1. Owner picks the open decisions; `/architect` amends this spec and the owner accepts it.
2. Probe for decision 1 (if A: a foreground agent inside a mod-started rollover; if B: `claude -p` from `$.process.run` inside the handoff), recorded in `verify.md`; a FAIL goes back to `/architect`.
3. `scripts/handover-memory.py` with `check`, `prune`, `ages`, `close`, `lint` and `--test`, satisfies **AC-2**, **AC-6** to **AC-9**, part of **AC-11**.
4. Replay, satisfies **AC-12**; stop on a loss.
5. `templates/sections.md`, `templates/instructions.md`, and `register.ts` only if decision 1 is B, with mod tests, satisfies **AC-1**, **AC-3**, **AC-5**, rest of **AC-11**.
6. Live edits (copied files, live wins): `~/.claude/rules/handover-carry.md`, `~/.claude/rules/check-gates.md` gate 5, `~/.claude/CLAUDE.md` `### Context`, the live templates under `~/.claude/auto-handoff/`, then `bin/sync.sh`, satisfies **AC-4**, **AC-8**, **AC-10** · waits on you if the sandbox refuses the write.

## Consequences
**Positive**: a fresh chat starts with about 500 tokens of what is still open instead of a long slot; open questions and shown lists survive by name; no file lives in `/tmp`; briefs stop piling up.
**Negative / tradeoffs**: the owner message copy goes, so the handover relies on the writer finding every open item; `/sync` stops a feature close until every agreed item is marked landed.
**Neutral**: `docs/briefs/general.md` is never closed by `/sync`; its items leave only by the 14 day archive rule.
