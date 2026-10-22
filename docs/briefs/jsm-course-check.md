# JSM course vs our setup (research, 2026-10-22)

Research agent report, copied verbatim in substance. [read] = read the source, [inferred] = reasoning.

Reach: course page (13 modules, about 80 lessons), 7 free lesson transcripts (What This Course Will (and Won't) Make You, Prerequisites, Why AI Coding Falls Apart, What Context Engineering Means, Demo: Running /scope, Data Model, Setup Design System and UI Foundation), the skills repo at pinned commit 43b69e4 (= upstream HEAD, no drift), workflow-research notes 04 and 05, memory notes. Gated lessons not watched; most likely to change findings: "Clearing vs. Compacting", "CLAUDE.md & AGENTS.md: How They Load", "/sync: Understand It, Then Automate It".

## 1. Skill count

- Nine skills [read]: scope, audit, architect, develop, check, test, document, sync, debug. All nine installed.
- Likely "10th" [inferred]: `/check review`, the second mode of `/check`, dropped on purpose (note 05 section 2; our `/review` replaces it).
- Other candidates: the page's workflow picker shows a `/review` step ("second model checks"); the repo also ships helper agents `scout` and `researcher` (installed).
- Nothing dropped by accident.

## 2. Gaps and contradictions, most important first

1. Always-loaded context is large. Module 5: keep the always-on layer "ruthlessly small". In a claude-config chat it is about 78 KB, ~20k tokens (`~/.claude/CLAUDE.md` 13 KB, 14 rules files ~31 KB, `AGENTS.md` 16 KB, `MEMORY.md` 16 KB). Review-tool choice is written twice (CLAUDE.md and `rules/skill-map.md`). Change: one copy of each rule; move skill-specific rules (`scope-contract`, `branch-pr`, `cheap-worker`, `runner-handoff`) to on-demand files; trim MEMORY.md index lines.
2. Owner approves specs less than the course does. Course: "You decide -> it implements"; the author reads spec, criteria and reasoning, then approves. Ours: `rules/standing-answers.md` auto-answers "data model matches" and self-accepts specs. Change: at least stop auto-answering "Does this data model match?".
3. Second review is not on a different model. Course Module 10 and `/check review` require a different model; our `/review` runs on Claude. Change: write the reason down; optionally a different-model pass for top-risk paths.
4. When to clear differs. Course clears between skills (after /scope, after /architect) and keeps chats under 150k. Ours: feature boundaries plus 200k auto handoff. Change: prefer a clear after /architect accepts a spec.
5. Check chain optional in the course, mandatory and automatic here. Deliberate, no change.

## 3. Briefs

- Not in the course. "Brief" there means a client's input brief or a helper-agent prompt.
- Ours: memory `brief-before-handoff.md` (2026-10-11, after a /scope dropped two features), then `~/.claude/CLAUDE.md` `### Context`, `rules/check-gates.md` section 4, runner spec 0034 (`BRIEF_CAP` 6000 chars). First briefs in git 2026-10-12.
- 20 briefs: no auto-load into chats, so little context cost. Real cost is drift: only `tool-review-2026-10.md` (25 KB) is cited by open rows (59, 87); three briefs cited by no row (`finish-runner-today.md`, `night-2026-10-15.md`, `leftovers-2026-10-18-verify.md`); one broken link (`briefs/runner-ideas-2026-10-12.md`, rows 24 and 25, never committed).
- Deletion rule today: none.
- Recommended lifecycle:
  1. One brief per feature; split `tool-review-2026-10` by row.
  2. `/sync` closes it when the feature gets `· done`: every agreed item must already be in a spec, `AGENTS.md` or scope, else `/sync` stops and names it.
  3. Then delete it (git keeps it; `Source:` can point at the commit), or move to `docs/briefs/done/`.
  4. `/sync` warns on broken brief links and uncited briefs.
  5. Write the rule into `CLAUDE.md` `### Context` next to the creation rule.
