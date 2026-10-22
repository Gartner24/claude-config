# Skills start themselves: brief

**Feature:** docs/scope/scope.md row 92 · spec [0070](../specs/0070-skills-start-themselves.md)

## Agreed so far, do not ask again
- 2026-10-22: start mode: catch plus start. A mod starts skills at chat start; a Stop hook blocks a turn end while a step is owed (owner panel answer).
- 2026-10-22: owed source: the scope's next box plus this chat's edits, mapped through spec `**Paths:**` (owner panel answer).
- 2026-10-22: release: the owed command runs, or the box is ticked ` · skipped`; at most 3 blocks per turn, then the turn ends and the owner sees what is owed (owner panel answer).
- 2026-10-22: chat start: both run by themselves, `/audit` when the repo has no `AGENTS.md`, then `/scope` (owner panel answer, picked over the recommended "/audit as a line").
- 2026-10-22: `/debug`: caught on a failing test, and "it should fix the findings automatically" (owner's note on the panel).
- 2026-10-22: data model approved: `~/.claude/state/chain-catch/<session id>.json` with `session`, `turn`, `blocks`, `owed` (owner panel answer).
- 2026-10-22: cross check: another model (standing answer); it found 12 gaps and the owner answered "Apply all twelve". Written into spec 0070 (AC-1 to AC-9, AC-13 to AC-15); team repos never get the automatic `/audit`. Spec accepted 2026-10-22.
- 2026-10-22: amendment, owner picked "Amend with scope chain" after giving three examples: (1) one new feature: explain it, `/scope`, `/architect`, then the rest automatic; (2) several features in a day: `/scope` and `/architect` for each, then parallel agents per feature; (3) a non code repo (topoproof): keep `/scope` and `/architect`; `/develop` writes the documents, `/test` is skipped. Written as AC-16 to AC-21.
- 2026-10-22: owner picked "Apply all eight" for the amendment's cross check gaps, including the new state field `nagged` (AC-19 blocks once per file per chat; root docs, dotfiles and files outside the repo exempt; AC-19 drops out when another owed line exists). Written into AC-9, AC-12, AC-16 to AC-21, the data model and build steps 1 and 5.
