---
name: intent-router
description: >
  Config-driven intent router. Fires automatically when intent is ambiguous — reads
  USAGE.md from ~/projects/personal/claude-config to score the prompt against every installed skill's
  TRIGGERS/BLOCKS/PRIORITY and invokes the best match. Use when the request could
  involve multiple skills or when the right tool isn't immediately obvious. Skip for
  simple file edits, direct questions, and single-tool operations where the answer
  is unambiguous.
---

# Intent Router

Config-driven skill dispatcher. Reads live routing rules from `~/projects/personal/claude-config/USAGE.md`,
scores the current prompt against every skill's TRIGGERS/BLOCKS/PRIORITY, announces
the winner in one line, and invokes it.

## When to fire

Fire this skill when:
- The request mentions a workflow (debugging, reviewing, shipping, building, designing)
- The intent is ambiguous between two or more skills
- The user says something like "help me with X" without a specific skill in mind

Skip this skill when:
- The user explicitly names a skill (`/council`, `/investigate`, etc.)
- The task is a simple file edit, read, or single-tool operation
- Answering a direct factual question

## Step 1 — Load routing table

```bash
cat ~/projects/personal/claude-config/USAGE.md 2>/dev/null || echo "ROUTING_TABLE_MISSING"
```

If output is `ROUTING_TABLE_MISSING`: fall back to the built-in table at the
bottom of this skill. Tell the user: "Routing table not found at ~/projects/personal/claude-config/USAGE.md
— using built-in defaults. Clone https://github.com/Gartner24/claude-config to get
personalized routing."

## Step 2 — Parse routing blocks

From the USAGE.md output, extract every block in this format:

```
### <skill-name>
TRIGGERS: <comma-separated phrases>
BLOCKS: <comma-separated phrases>
PRIORITY: <number> - <reason>
```

Build an internal scoring table: `{ skill, triggers[], blocks[], priority }`.

## Step 3 — Score the prompt

Take the user's current message (the prompt that triggered this skill).

For each skill in the table:
1. **Block check first** — if any BLOCKS phrase appears in the prompt, score = 0. Skip.
2. **Trigger score** — count how many TRIGGERS phrases match the prompt (substring,
   case-insensitive). Score = match_count × priority.
3. **Threshold** — discard any skill with score < 3. If nothing clears the threshold,
   exit silently without invoking anything (prompt is not skill-territory).

## Step 4 — Resolve winner

- **Clear winner** (top score ≥ 2× second place): proceed to Step 5.
- **Tie or close race** (top two scores within 20% of each other): check if they
  are a known sequence (e.g. `council` → `investigate`, `brainstorming` → `gsd-plan-phase`).
  If yes, note both in the announcement and invoke the first. If no natural sequence,
  pick the higher-priority skill.
- **Nothing above threshold**: exit silently. Do not announce, do not intercept.

## Step 5 — Announce and invoke

One line only, then invoke immediately. Format:

```
Using /<skill-name> — <one-phrase reason from TRIGGERS match>.
```

Examples:
```
Using /council — tradeoff decision with multiple valid approaches.
Using /investigate — error with unclear cause.
Using /design-motion-principles — motion-first request; prefer over impeccable animate.
Using /brainstorming — new feature request; explore intent before planning.
Using /mem-search — checking if this was solved in a previous session first.
```

After the announcement, invoke the skill exactly as if the user had typed `/<skill-name>`.
Pass the original user prompt as context.

## Step 6 — After invocation

Nothing. Do not add a summary, do not explain what happened. The invoked skill
takes over completely.

---

## Skill interaction rules (personal overrides)

These rules encode personal preferences that override pure trigger scoring:

1. **mem-search first** — if the prompt contains memory-check signals
   (`did we`, `last time`, `previously`, `remember`), invoke `/mem-search` before
   anything else, even if another skill scores higher.

2. **council before implement** — if the prompt contains `should I`, `which is better`,
   `tradeoff`, or `can't decide` AND would otherwise route to a build/plan skill,
   route to `/council` first.

3. **design-motion-principles over impeccable animate** — if the prompt is
   primarily about motion/animation (contains `animation`, `motion`, `transition`,
   `animate`, `easing`, `spring`, `janky`), route to `/design-motion-principles`,
   not `/impeccable animate`. Both handle motion but design-motion-principles is
   dedicated and has the Emil Kowalski lens.

4. **investigate over ad-hoc debugging** — any bug/error prompt goes to
   `/investigate`, never to a general coding response. No exceptions.

5. **brainstorming before gsd-plan-phase** — if the idea is still vague or
   exploratory (`I want to`, `I'm thinking`, `maybe we could`), route to
   `/brainstorming` before `/gsd-plan-phase`.

---

## Built-in fallback table

Used only when `~/projects/personal/claude-config/USAGE.md` is not found.

| Skill | Triggers | Priority |
|-------|----------|----------|
| mem-search | did we solve, previously, last time, remember | 10 |
| council | should I, tradeoff, architecture choice, which is better, second opinion | 9 |
| investigate | bug, error, crash, broken, not working, failing | 9 |
| gsd-new-project | new project, start a project, initialize project | 9 |
| context-restore | resume, continue where, pick up where | 9 |
| brainstorming | new feature, let's build, I want to add, design this | 8 |
| qa | does this work, test this, verify it works | 8 |
| review | review this, before I merge, check this PR | 8 |
| ship | ship it, push this, create a PR, deploy | 8 |
| impeccable audit | audit the UI, check the design, a11y, anti-patterns | 8 |
| design-motion-principles | animation, motion, transition, animate, easing, spring | 8 |
| gsd-plan-phase | plan this, break this down, create tasks | 7 |
| ralph-loop | keep going, run autonomously, don't stop | 7 |
| two-stage-review | large diff, big PR, complex review | 7 |
