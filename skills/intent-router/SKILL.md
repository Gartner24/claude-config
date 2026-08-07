---
name: intent-router
description: >
  Use when a request could involve multiple skills, mentions a workflow (debug, review,
  ship, build, design) without naming one, or the right tool isn't immediately obvious.
  Skip for simple file edits, direct factual questions, single-tool operations, and any
  request that already names a skill.
---

# Intent Router

Config-driven skill dispatcher. Reads live routing rules from `~/claude-config/USAGE.md`,
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

## Step 1 - Load routing table

```bash
cat ~/claude-config/USAGE.md 2>/dev/null || echo "ROUTING_TABLE_MISSING"
```

If output is `ROUTING_TABLE_MISSING`: fall back to the built-in table at the
bottom of this skill. Tell the user: "Routing table not found at ~/claude-config/USAGE.md
- using built-in defaults. Clone https://github.com/Gartner24/claude-config to get
personalized routing."

## Step 2 - Parse routing blocks

From the USAGE.md output, extract every block in this format:

```
### <skill-name>
TRIGGERS: <comma-separated phrases>
BLOCKS: <comma-separated phrases>
PRIORITY: <number> - <reason>
```

Build an internal scoring table: `{ skill, triggers[], blocks[], priority }`.

## Step 3 - Score the prompt

Take the user's current message (the prompt that triggered this skill).

For each skill in the table:
1. **Block check first** - if any BLOCKS phrase appears in the prompt, score = 0. Skip.
2. **Trigger score** - count how many TRIGGERS phrases match the prompt (substring,
   case-insensitive). Score = match_count x priority.
3. **Threshold** - discard any skill with score < 3. If nothing clears the threshold,
   exit silently without invoking anything (prompt is not skill-territory).

## Step 4 - Resolve winner

- **Clear winner** (top score >= 2x second place): proceed to Step 5.
- **Tie or close race** (top two scores within 20% of each other): check if they
  are a known sequence (e.g. `council` -> `investigate`).
  If yes, note both in the announcement and invoke the first. If no natural sequence,
  pick the higher-priority skill.
- **Nothing above threshold**: exit silently. Do not announce, do not intercept.

## Step 5 - Announce and invoke

One line only, then invoke immediately. Format:

```
Using /<skill-name> - <one-phrase reason from TRIGGERS match>.
```

Examples:
```
Using /council - tradeoff decision with multiple valid approaches.
Using /investigate - error with unclear cause.
Using /animate - motion-first request; building new motion.
Using /brainstorming - new feature request; explore intent before planning.
Using /mem-search - checking if this was solved in a previous session first.
```

After the announcement, invoke the skill exactly as if the user had typed `/<skill-name>`.
Pass the original user prompt as context.

## Step 6 - After invocation

Nothing. Do not add a summary, do not explain what happened. The invoked skill
takes over completely.

---

## Skill interaction rules (personal overrides)

These rules encode personal preferences that override pure trigger scoring:

1. **mem-search first** - if the prompt contains memory-check signals
   (`did we`, `last time`, `previously`, `remember`), invoke `/mem-search` before
   anything else, even if another skill scores higher.

2. **council before implement** - if the prompt contains `should I`, `which is better`,
   `tradeoff`, or `can't decide` AND would otherwise route to a build/plan skill,
   route to `/council` first.

3. **motion dispatches by kind, never to a single skill** - a motion prompt is
   never handled by a general coding response, but it is also never all routed to
   one skill. Pick by what is being asked (updated 2026-08-06):
   - build new motion -> `animate` (Emil Kowalski's own skill, the primary source)
   - plain CSS transition on a standard component (modal, dropdown, accordion,
     tabs, skeleton, icon swap) -> `transitions-dev`
   - scroll-driven, pinned, parallax, or timeline choreography -> `gsap-scrolltrigger`
     / `gsap-timeline` (`gsap-react` in React)
   - gesture, spring, drag, swipe, sheet, momentum -> `apple-design`
   - review or audit existing motion -> `review-animations` (a diff) /
     `improve-animations` (a whole app) / `transitions-polish` (timing and tokens)
   - 3D or WebGL -> the `threejs-*` set
   - `design-motion-principles` ONLY when an HTML report with looping demos is
     wanted. It was the motion skill before the emilkowalski set was installed;
     it is now demoted to priority 5 and kept for that one output.

4. **investigate over ad-hoc debugging, but not over the specialists** - a runtime
   or logic bug goes to `/investigate`, never to a general coding response. It does
   NOT take prompts that name a more specific failure:
   - build, compile, or type errors -> `/build-fix` (or `/go-build`, `/rust-build`,
     `/gradle-build` when the toolchain is named)
   - a page not converting -> `cro`
   - language-specific review concerns (goroutines, borrow checker, error handling
     patterns) -> the matching `*-review` skill
   `investigate` triggers on generic words (`bug`, `error`, `broken`, `failing`)
   that appear in all of the above, so it will often score highly. Prefer the
   specialist whenever the prompt names a toolchain, a build step, or a domain.

5. **brainstorming before any plan/build skill** - if the idea is still vague or
   exploratory (`I want to`, `I'm thinking`, `maybe we could`), route to
   `/brainstorming` before any planning or implementation skill.

---

## Built-in fallback table

Used only when `~/claude-config/USAGE.md` is not found.

| Skill | Triggers | Priority |
|-------|----------|----------|
| mem-search | did we solve, previously, last time, remember | 10 |
| council | should I, tradeoff, architecture choice, which is better, second opinion | 9 |
| investigate | bug, error, crash, broken, not working, failing | 9 |
| context-restore | resume, continue where, pick up where | 9 |
| brainstorming | new feature, let's build, I want to add, design this | 8 |
| qa | does this work, test this, verify it works | 8 |
| review | review this, before I merge, check this PR | 8 |
| ship | ship it, push this, create a PR, deploy | 8 |
| impeccable audit | audit the UI, check the design, a11y, anti-patterns | 8 |
| animate | animate this, add motion, svg animation, micro-interaction | 9 |
| transitions-dev | transition, dropdown animation, modal animation, accordion | 9 |
| gsap | gsap, scrolltrigger, scroll animation, parallax, pin the section | 9 |
| apple-design | spring, gesture, drag, swipe, sheet, momentum | 9 |
| review-animations | audit the motion, feels janky, animation feels off | 9 |
| ralph-loop | keep going, run autonomously, don't stop | 7 |
| two-stage-review | large diff, big PR, complex review | 7 |
