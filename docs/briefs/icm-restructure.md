# ICM restructure of claude-config (row 97)

## Agreed so far, do not ask again
- The owner leans to a whole restructure, keeping today's quality, but the choice (whole, partial, map only) is decided by research, not by thinking: icm-architect repo in full, its paper (arXiv 2603.16021, linked from the repo), the two videos below, via `/deep-research`.
- The owner sees the proposed structure (a tree) before anything is built.
- Every claim below is checked as fact: correct, incorrect, or missing pieces.
- The tree in icm-research.md section 4 is Claude's draft from reading the skill, NOT the skill's output. Before any /architect question, run icm-architect's own restructure mode read only (scan and install first) and show its proposed tree next to the draft; its output tells us what to set up (owner, 2026-10-22).
- The trace fix for the repeat problem is merged (#152) and live after the restart; the first handoff after it is its real test.
- icm-architect ran read only (2026-10-22); its tree and migration map are icm-research.md section 6.
- How far (owner, 2026-10-22): a whole restructure in two phases. Phase 1 is the skill's safe moves (map, `tests/` split, runner archived, short entry file, scope split). Then check everything works. Phase 2 is the whole restructure, then a review whose job is to prove nothing broke. Phase 2 gets its own migration map; a held path (step 4 of section 6) moves only with every referrer, inside and outside the repo, updated in the same change.
- Review for "nothing broke" must not burn usage: if `/review-stack` is used, launch only the agents this case needs, not the full set (owner, 2026-10-22).
- "Nothing broke" check per restructure PR (owner, 2026-10-22): a reference check script (every path the repo and `~/.claude`, `~/.local/bin`, `settings.json` point at before the move still resolves after), `bin/install.sh --dry-run`, the suite, `spec-paths`, then ONE regression-hunter agent on Sonnet. Not `/review-stack`, not `/review`. Switch phase 2 to `/review` only if it rewrites code rather than moving files.
- Entry file (owner, 2026-10-22): `CLAUDE.md` is the source, as ICM (under about 60 lines, routes only); `AGENTS.md` becomes a generated twin. The risk that `/sync`, `/audit` or any skill edits the generated `AGENTS.md` must go to zero: the plan has its own step that makes such an edit impossible or undone, with a test that proves it, before the switch lands.
- Workflows (owner, 2026-10-22): build `build-features` first. The others are later steps in the plan, not dropped: `review-fix` and `restructure-check` (remind the owner). Before them, a `/deep-research` on workflow templates that searches two things: (1) recommended existing workflows and templates, (2) workflows we can make from our own skills and repos (site design, SEO, reviews and the rest). Also a workflow builder skill based on the ICM research and icm-architect, so later workflows (marketing, publicity: later) are made with it.
- Running workflows show in both places (owner, 2026-10-22): the agent panel (`subagentStatusLine`, one row per agent with its scope row and step) and a short count on the chip band. Probe before the spec is accepted that the mod API sees workflow agents; if it cannot, fall back to the agent panel only and say so.
- Where today's `AGENTS.md` lines go (owner, 2026-10-22): never break rules (public repo, no private names, no attribution, ASCII, commit format), standing answers, agent skills and context files stay in `CLAUDE.md`; the 4 most used commands stay there too. The rest moves to `map/` cards: command list to `map/processes/` (`install.md`, `sync.md`, `checks.md`), copied vs linked install rules to `map/objects/install.md`, vendored trees and SKILLS.md and `**Paths:**` rules to `map/objects/skills.md` and `specs.md`, each gotcha to the card of its part. The build checks every old line has a new home. Trade off accepted: a reference rule on a card loads only when the card is opened.
- `AGENTS.md` becomes a symlink to `CLAUDE.md` (one real file, so skill edits land in `CLAUDE.md`), with a test that it is still a link and a probe before accept that the Edit and Write tools write through the link. Owner did not object when told (2026-10-22); if the probe fails, fall back to a generated copy plus a commit check.
- Runner tests (owner, 2026-10-22): the 41 runner only test files move with the runner to `_archive/runner/tests/`, out of the suite, runnable by hand from one command on the runner card. Also: leftovers from old runs are cleaned out, each thing kept once where it belongs in the docs structure, no duplicated decision, no deprecated files left. Scope of that cleanup (owner, 2026-10-22): repo runner docs only (runner specs, `docs/specs/*/probes/`, runner briefs and reviews) move to `_archive/runner/docs/` in git; before a spec moves, every decision of it still in force is confirmed to have one live home. The consumed handover files outside git are NOT deleted.
- Behavior stays (owner, 2026-10-22): reorganizing files the ICM way is the purpose, in both phases. How things work from the inside must not change or break: the workflow chain, rules, skills, hooks, mods, handoffs, reviews, branches and PRs behave the same after every move. Any change to how something works is not part of the restructure; it comes to the owner as its own question.
- Rows (owner, 2026-10-22): row 97 is the restructure only (phase 1 now, phase 2 after its review). New rows: 100 `build-features` workflow plus where runs show; 101 workflow template research plus the workflow builder skill; 102 `review-fix` and `restructure-check` workflows (the reminder).

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
