# ICM restructure of claude-config (row 97)

## Agreed so far, do not ask again
- The owner leans to a whole restructure, keeping today's quality, but the choice (whole, partial, map only) is decided by research, not by thinking: icm-architect repo in full, its paper (arXiv 2603.16021, linked from the repo), the two videos below, via `/deep-research`.
- The owner sees the proposed structure (a tree) before anything is built.
- Every claim below is checked as fact: correct, incorrect, or missing pieces.
- The tree in icm-research.md section 4 is Claude's draft from reading the skill, NOT the skill's output. Before any /architect question, run icm-architect's own restructure mode read only (scan and install first) and show its proposed tree next to the draft; its output tells us what to set up (owner, 2026-10-22).
- The trace fix for the repeat problem is merged (#152) and live after the restart; the first handoff after it is its real test.

## Owner's ideas to check (2026-10-22, owner's words condensed)
1. In ICM there is no file per agent: folders are workflows, and those workflows are the agents. Is that right?
2. Several workflows the owner selects to run; running ones show on the status bar (chip band) or under the agents bar that lists running agents.
3. Our current agents would be replaced using icm-architect's skill and videos. Find the correct name for these ("ICM agents"?).
4. Use them for the batch work: after the scope and /architect queue has every question answered, trigger them to build. They can trigger other agents as needed, with our model and effort picks per task.
5. The main chat is the orchestrator that controls all of them.
6. The rollover handover needs a new section for them once built, so the next chat knows what is running.
7. How many workflows should we have? Help decide.

## Sources to read
- https://github.com/RinDig/icm-architect (README, SKILL.md, references/core.md, forms.md, system-map.md, reference-integrity.md, assets/templates/)
- The paper: Van Clief and McDermott, arXiv 2603.16021
- https://www.youtube.com/watch?v=dZ8P7zevuGw
- https://www.youtube.com/watch?v=UDJmO7xyCSo

## Known so far (first read, 2026-10-22)
- icm-architect is a skill that designs a layout per workspace, not one fixed layout. Six forms: Pipeline, Umbrella, Record library, Knowledge bundle, Context map, System map. Restructure mode audits, proposes a migration map for approval, then migrates and checks references.
- Constraint here: `claude-home/` mirrors `~/.claude` (install, sync, live links, about 70 spec `**Paths:**` lines depend on it).

## Research result
Full report: [icm-research.md](icm-research.md) (2026-10-22). Open questions for /architect are in its section 5.
