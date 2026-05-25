# Usage Guide

When to reach for which skill. This is the decision guide - not a feature list.

The personal-router skill reads the TRIGGERS/BLOCKS/PRIORITY fields from this file
to route prompts automatically. Keep those fields accurate when you add skills.

ROUTING-FORMAT-VERSION: 1

---

## Starting a new project

### gsd-new-project
TRIGGERS: new project, start a project, initialize project, fresh project, from scratch, create a roadmap, new repo setup
BLOCKS: existing project, adding a feature, small change
PRIORITY: 9 - highest for project init; nothing else should fire first on a blank slate

1. `/gsd-new-project` - creates roadmap, phases, milestones
2. `/impeccable teach` - give Claude design context for the project (run once)
3. `/learn-codebase` (claude-mem) - prime Claude's memory with the codebase

---

## Memory and context (check these first)

### mem-search
TRIGGERS: did we solve this, did we do this before, how did we, remember when, previously, last time, past session, have we already
BLOCKS: nothing - memory check should always fire when these phrases appear
PRIORITY: 10 - highest priority overall; always check memory before starting any non-trivial task

### context-restore
TRIGGERS: resume, continue where, pick up where, last session, where were we, restore context, I was working on
BLOCKS: nothing
PRIORITY: 9

### learn-codebase
TRIGGERS: learn this codebase, prime the codebase, get up to speed, read all the files, new codebase, unfamiliar repo
BLOCKS: already primed this session
PRIORITY: 8

- `/mem-search` - did we solve this before? search past sessions
- `/learn-codebase` - read every file in a repo into memory (one-time per project)
- `/context-save` - snapshot current session to continue later
- `/context-restore` - resume from a saved snapshot
- `/smart-explore` (claude-mem) - explore a codebase semantically

---

## Hard decisions

### council
TRIGGERS: should I, which is better, tradeoff, tradeoffs, architecture choice, monolith, microservice, which database, which library, build vs buy, second opinion, not sure which approach, multiple options, launch decision, risk, 3 possible causes, can't decide, help me decide, debate
BLOCKS: simple questions with one clear answer, implementation tasks, bug fixes with obvious cause
PRIORITY: 9 - invoke before any implementation skill when decision signals are present

Use `/council` when one answer isn't enough:
- Architecture choices (monolith vs microservices, which DB, which library)
- Debugging with 3+ possible causes
- Strategy tradeoffs
- Whether to build vs buy
- Launch decisions with real risk

Council runs 3 rounds: independent analysis, cross-examination, final verdict with confidence.

---

## Planning a feature

### brainstorming
TRIGGERS: new feature, let's build, I want to add, design this, let's make, create a, I'm thinking of building, plan this feature, explore this idea, before we start
BLOCKS: already have a plan, executing existing plan, bug fix
PRIORITY: 8 - fires before gsd-plan-phase; explore intent before writing plans

### gsd-plan-phase
TRIGGERS: plan this, break this down, create tasks, make a plan, roadmap, phase plan, detailed plan, implementation plan
BLOCKS: new project (use gsd-new-project), ambiguous idea (use brainstorming first)
PRIORITY: 7

### gsd-execute-phase
TRIGGERS: execute the plan, run the plan, start phase, implement phase, do the plan
BLOCKS: no plan exists yet
PRIORITY: 7

1. `/brainstorming` (superpowers) - explore intent before writing code
2. `/gsd-plan-phase` - break feature into executable tasks with a written plan
3. `/gsd-execute-phase` - execute the plan with checkpoints

---

## Debugging

### investigate
TRIGGERS: bug, error, crash, broken, not working, failing, unexpected behavior, wrong output, exception, traceback, it broke, why is this, what's wrong, debug, fix this error
BLOCKS: nothing - always use investigate for bugs over ad-hoc debugging
PRIORITY: 9

### council (for complex bugs)
TRIGGERS: 3 possible causes, multiple causes, not sure why, could be X or Y or Z, weird bug, intermittent, hard to reproduce
BLOCKS: simple bugs with obvious cause
PRIORITY: 9 - tie with investigate; use council THEN investigate when causes are unclear

- `/investigate` for bugs - systematic debugging, scientific method
- `/council` then `/investigate` when there are 3+ possible causes

---

## Everyday coding

### qa
TRIGGERS: does this work, test this, verify it works, check if it works, run the app, does it work, make sure it works, test the feature, test it manually
BLOCKS: writing tests (use gsd-add-tests), code review (use review)
PRIORITY: 8

### review
TRIGGERS: review this, pre-landing, before I merge, check this PR, code review, review my changes, check my diff, is this ready to merge
BLOCKS: nothing - review fires on any merge/PR intent
PRIORITY: 8

### ship
TRIGGERS: ship it, push this, create a PR, commit and push, submit PR, deploy, send it
BLOCKS: not committed yet (commit first), failing tests
PRIORITY: 8

- `/skill-router` is always active - describe what you want and it routes to the right skill
- `/investigate` for bugs - systematic debugging, scientific method
- `/qa` to test something works - actually runs the app and checks behavior
- `/review` before merging - pre-landing diff review (SQL safety, logic bugs, security)
- `/ship` to create a PR and push - handles commit, PR description, branch

---

## UI / frontend work

### impeccable (audit)
TRIGGERS: audit the UI, check the design, accessibility issues, anti-patterns, a11y, performance issues in UI, responsive check, design quality
BLOCKS: motion specifically (use design-motion-principles instead)
PRIORITY: 8

### impeccable (polish)
TRIGGERS: polish this, final pass, ready to ship, clean up the UI, tighten the design, before shipping UI
BLOCKS: nothing
PRIORITY: 7

### impeccable (critique)
TRIGGERS: UX review, is the hierarchy clear, does this feel right, UX feedback, information architecture, cognitive load
BLOCKS: nothing
PRIORITY: 7

### design-motion-principles
TRIGGERS: animation, motion, transition, animate this, feels wrong motion, too fast, too slow, spring, easing, framer motion, CSS animation, motion design, this animation, audit animations, motion audit, movement, feels janky, bounce, hover effect feels
BLOCKS: static UI with no animation (use impeccable instead)
PRIORITY: 8 - prefer over impeccable animate when motion is the primary concern

### taste skills (pick one per project)
TRIGGERS for high-end-visual-design: premium, polished, high-end, Stripe feel, Linear feel, Vercel feel, calm UI, expensive looking, soft contrast, whitespace heavy
TRIGGERS for minimalist-ui: minimal, clean, Notion feel, editorial, restrained, Linear feel, simple layout
TRIGGERS for industrial-brutalist-ui: brutalist, experimental, raw, Swiss type, sharp contrast, bold layout
PRIORITY: 6 - taste selection; run once per project before any UI work

Pick a taste skill first (sets visual direction), then use impeccable for quality:

- `high-end-visual-design` - calm, premium, polished (Stripe/Linear/Vercel feel)
- `minimalist-ui` - editorial, restrained (Notion feel)
- `industrial-brutalist-ui` - experimental, sharp, mechanical (use intentionally)
- `ui-ux-pro-max` - when you need to explore styles or pick from a broad palette

Then impeccable commands:
- `/impeccable critique` - is the UX hierarchy clear? does it feel right?
- `/impeccable audit` - technical check: a11y, performance, responsive, anti-patterns
- `/impeccable polish` - final pass before shipping
- `/impeccable bolder` / `/impeccable quieter` - tune the energy level
- `/impeccable animate` - add motion (use design-motion-principles for motion-first work)

For motion specifically:
- `/design-motion-principles` - create mode (build with motion) or audit mode (review + HTML report)
- Emil Kowalski lens = restraint. Cuts unnecessary animation.

For component generation:
- magic MCP is active - ask for a component and it searches the 21st.dev library

---

## Code review

### two-stage-review
TRIGGERS: large diff, big PR, many files changed, complex review, thorough review, deep review
BLOCKS: small change (use review instead)
PRIORITY: 7

### code-review (high effort)
TRIGGERS: security review, important PR, sensitive change, production code, careful review, security-sensitive
BLOCKS: nothing
PRIORITY: 8

| Situation | Command |
|-----------|---------|
| Quick sanity check | `/code-review` (low effort) |
| Normal PR before merge | `/review` (gstack pre-landing) |
| Important PR, security-sensitive | `/code-review` (high/max effort) |
| Full pipeline: plan + review | `/autoplan` |

`/two-stage-review` - splits review into fast structural check then deep logic check. Use for large diffs.

---

## Autonomous / long-running work

### ralph-loop
TRIGGERS: keep going, run autonomously, don't stop, continue without me, run this in the background, autonomous, loop on this, keep running
BLOCKS: nothing
PRIORITY: 7

- `/ralph-loop` - runs Claude autonomously, keeps going without re-prompting
- `/gsd-autonomous` - gstack's autonomous mode for multi-step plans
- `/babysit` (claude-mem) - monitors a background job and reports back

---

## Quality floors (always-on from jjstack)

These aren't commands - they're behaviors jjstack enforces automatically.
No routing needed - they fire on their own:
- `verify-before-done` - verifies work actually works before saying done
- `smart-review` - elevated review standard for any code change
- `smart-simplify` - simplifies code after a feature lands

---

## Specific scenarios (routing cheat sheet)

| Scenario | Route |
|----------|-------|
| Bug with 3+ possible causes | `/council` then `/investigate` |
| New page/screen | taste skill -> `/impeccable shape` -> build -> `/impeccable audit` -> `/impeccable polish` |
| Animation feels wrong | `/design-motion-principles` audit mode |
| Code works but messy | `/smart-simplify` |
| Second opinion on architecture | `/council` |
| Starting a long session | `/context-restore` or `/learn-codebase` |
| Shipping a PR | `/review` -> fix -> `/ship` |
| Full deploy pipeline | `/land-and-deploy` |

---

## Superpowers + claude-mem synergy

### systematic-debugging
TRIGGERS: complex bug, hard to debug, need a systematic approach, methodical debugging
BLOCKS: simple bugs with obvious cause
PRIORITY: 8

These two work as a pair:
- Superpowers provides **how to do things** (structured skill workflows)
- Claude-mem provides **what was learned** (persistent memory of outcomes)

Run `/mem-search "X"` before starting any non-trivial task to check if it was solved before.
