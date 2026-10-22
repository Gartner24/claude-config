# Dashboard restructure for the setup without wf (scope row 93)

## Agreed so far, do not ask again
- 2026-10-22, views: Plan and Agents stay, and a new Now view (key `n`) shows this chat: the step it owes (spec 0070 catch state), the handoff state, open PRs waiting for you, and running agents. Owner panel: "Add a Now view (Recommended)".
- 2026-10-22, PRs in the Now view: every open PR the owner authored, from one `gh search prs --author @me --state open` call; PRs others opened are not listed. Owner panel: "All mine, one search (Recommended)".
- 2026-10-22, band: a short `owed N` segment in warn color before the handoff segment, gone when nothing is owed; the full owed lines are in the Now view. Owner panel: "Short owed count (Recommended)".
- 2026-10-22, name: the owner's tools are the "chip" family. This mod becomes `chip-dash` everywhere now (folder, plugin id, state keys, tests, chip text), command `/chip`, `/wf-dash` kept as an alias; the owner relinks it after the security scan. Done by a parallel agent (scope row 96). Owner: "rename it chip, my tools will be called chip", then "chip-dash everywhere now by a parallel agent".
- 2026-10-22, Now view order top to bottom: owed steps; open PRs (repo, number, draft or ready, checks); handoff state (on or off for this folder, token line, last handover file); running agents as one count line (details stay in the Agents view). Owner panel: "Owed, PRs, handoff, agents (Recommended)".
- 2026-10-22, PR refresh: when the Now view opens, on `r`, and every 2 minutes while it is open; never while closed. A failed call keeps the last list marked `stale since HH:MM`. Owner panel: "Open, r, and 2 min (Recommended)".
- 2026-10-22, spec 0071 cross check: owner picked "Apply all twelve": checks on every PR row through one `gh api graphql` search; owed read from this chat's id or the one it replaced after `/clear`; owed emptied when a turn ends unblocked (spec 0070 data model line); row budget owed 3, PRs 6, handoff 2, agents 1; `owed N` is a right side segment before `handoff`, last to drop.

## Context
- The runner parts are already gone (design.md, 2026-10-22 note): the band's right end shows the auto handoff, Plan has 6 filters from `plan.py`, Agents lists this chat's agents and shells.
- New live sources from today: the catch state file `~/.claude/state/chain-catch/<session>.json` (`owed`), `gh pr list` per repo, the wf-handoff chain file and handover slot.
