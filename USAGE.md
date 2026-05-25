# Usage Guide

When to reach for which skill. This is the decision guide - not a feature list.

---

## Starting a new project

1. `/gsd-new-project` - creates roadmap, phases, milestones
2. `/impeccable teach` - give Claude design context for the project (run once)
3. `/learn-codebase` (claude-mem) - prime Claude's memory with the codebase

---

## Planning a feature

1. `/brainstorming` (superpowers) - explore intent before writing code
2. `/gsd-plan-phase` - break feature into executable tasks with a written plan
3. `/gsd-execute-phase` - execute the plan with checkpoints

---

## Everyday coding

- `/skill-router` is always active - just describe what you want and it routes to the right skill
- `/investigate` for bugs (gstack) - systematic debugging, scientific method
- `/qa` to test something works - actually runs the app and checks behavior
- `/review` before merging - pre-landing diff review (SQL safety, logic bugs, security)
- `/ship` to create a PR and push - handles commit, PR description, branch

---

## Hard decisions

Use `/council` when one answer isn't enough:
- Architecture choices (monolith vs microservices, which DB, which library)
- Debugging with 3+ possible causes
- Strategy tradeoffs
- Whether to build vs buy
- Launch decisions with real risk

Council runs 3 rounds: independent analysis from multiple perspectives, cross-examination, final verdict with confidence.

---

## UI / frontend work

### Pick a taste skill first (sets the visual direction)
- `high-end-visual-design` - calm, premium, polished (Stripe/Linear/Vercel feel)
- `minimalist-ui` - editorial, restrained (Notion feel)
- `industrial-brutalist-ui` - experimental, sharp, mechanical (use intentionally)
- `ui-ux-pro-max` - when you need to explore styles or pick from a broad palette

### Then use impeccable for quality
- `/impeccable critique` - is the UX hierarchy clear? does it feel right?
- `/impeccable audit` - technical check: a11y, performance, responsive, anti-patterns
- `/impeccable polish` - final pass before shipping
- `/impeccable bolder` / `/impeccable quieter` - tune the energy level
- `/impeccable animate` - add motion correctly (runs the Emil Kowalski lens)

### For motion specifically
- `/design-motion-principles` - two modes: create (build components with motion) or audit (review existing animations)
- The audit generates an HTML report with live CSS demos next to each finding
- Emil Kowalski lens = restraint. If something shouldn't animate, it says so.

### For component generation
- magic MCP is active - ask for a component and it searches the 21st.dev library
- Pairs well with `impeccable` for post-generation quality checks

---

## Code review

Three levels depending on how much you care:

| Situation | Command |
|-----------|---------|
| Quick sanity check | `/code-review` (low effort) |
| Normal PR before merge | `/review` (gstack pre-landing) |
| Important PR, security-sensitive | `/code-review` (high/max effort) |
| Full pipeline: plan + review | `/autoplan` |

`/two-stage-review` (jjstack) - splits review into fast structural check then deep logic check. Use for large diffs.

---

## Memory and context

- `/mem-search` - did we solve this before? search past sessions
- `/learn-codebase` - read every file in a repo into memory (one-time per project)
- `/context-save` - snapshot current session to continue later
- `/context-restore` - resume from a saved snapshot
- `/smart-explore` (claude-mem) - explore a codebase semantically

---

## Autonomous / long-running work

- `/ralph-loop` - runs Claude autonomously on a task, keeps going without re-prompting
- `/gsd-autonomous` - gstack's autonomous mode for multi-step plans
- `/babysit` (claude-mem) - monitors a background job and reports back

---

## Quality floors (always-on rules from jjstack)

These aren't commands - they're behaviors jjstack enforces automatically:
- `/verify-before-done` - Claude verifies work actually works before saying done
- `/smart-review` - elevated review standard for any code change
- `/smart-simplify` - simplify code after a feature lands

---

## Specific scenarios

**"This bug has 3 possible causes and I'm not sure which"**
- `/council` then `/investigate`

**"I need to build a new page/screen"**
- Pick taste skill -> `/impeccable shape` (plan the UX) -> build -> `/impeccable audit` -> `/impeccable polish`

**"This animation feels wrong"**
- `/design-motion-principles` in audit mode - generates HTML report with demo

**"The code works but it's messy"**
- code-simplifier plugin (runs as subagent automatically after changes)
- `/smart-simplify` (jjstack)

**"I need a second opinion on my architecture"**
- `/council` - set it up as an architecture decision

**"Starting a long coding session"**
- `/context-restore` to resume, or `/learn-codebase` on a new project
- `/gsd-resume-work` to pick up where gstack left off

**"Shipping a PR"**
- `/review` -> fix findings -> `/ship`
- Or `/land-and-deploy` for the full pipeline

---

## Superpowers + claude-mem synergy

These two work as a pair:

- Superpowers provides **how to do things** (structured skill workflows)
- Claude-mem provides **what was learned** (persistent memory of outcomes)

Example: you use `/systematic-debugging` (superpowers) to fix a bug. Claude-mem stores what the root cause was. Next session, when a similar bug appears, `/mem-search` surfaces the prior fix pattern.

Run `/mem-search "X"` before starting any non-trivial task to check if it was solved before.
