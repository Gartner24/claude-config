# Design Pipeline - setup & reuse

A tutorial for wiring `ui-ux-pro-max` + `21st.dev` (and the rest of the stack) so you stop rewriting the prompt.

**Do Steps 1-4 once per machine/project. Then use the kickoff prompt for every task.**

---

## Step 1 - Install 21st Magic MCP in Claude Code

**1a. Get an API key.** Go to `https://21st.dev/magic/console` and generate one. Free tier has usage limits; heavier use needs a plan.

**1b. Install it user-scoped** (recommended - works across all client projects):

```
claude mcp add magic --scope user --env API_KEY="YOUR_KEY" -- npx -y @21st-dev/magic@latest
```

**Or** project-scoped via the CLI installer:

```
npx @21st-dev/cli@latest install claude --api-key YOUR_KEY
```

**Or** add it manually to `.mcp.json`:

```json
{
  "mcpServers": {
    "magic": {
      "command": "npx",
      "args": ["-y", "@21st-dev/magic@latest"],
      "env": { "API_KEY": "YOUR_KEY" }
    }
  }
}
```

Claude Code auto-loads the server. After that, `/ui ...` generates components straight into the repo, e.g. `/ui a pricing table with three tiers and a monthly/annual toggle`.

> Magic writes files into the project - review its writes like any agent edit. It's React + Tailwind (shadcn-style) only.

---

## Step 2 - Add router entries (for the trigger router)

```
ui-ux-pro-max
TRIGGERS: new design, redesign, design this, design a page, design a component, from scratch, what style, pick a style, choose a palette, font pairing, pick fonts, choose a stack, design direction, make this look like, style exploration, new page, new section
BLOCKS: nothing
PRIORITY: 9      # runs first - direction before anything is built

21st.dev
TRIGGERS: build the UI, build this, scaffold, implement the design, need a navbar, need a hero, need a pricing section, need a table, need a modal, need a card, need a component, find a component, real component, production component, shadcn, block, registry
BLOCKS: nothing
CONDITION: stack is React / Next + Tailwind + shadcn/Radix   # skip otherwise
PRIORITY: 8      # runs after direction is locked
CHAIN-AFTER: ui-ux-pro-max
```

Two rules make them work together: pro-max at priority 9 decides direction first; 21st chains after it to source real components matching that direction instead of building from zero.

---

## Step 3 - Add the pipeline rule to CLAUDE.md (for Claude Code)

This is the Claude Code equivalent of the router - it makes the chaining fire on its own. Paste into the project's `CLAUDE.md` (or `~/.claude/CLAUDE.md` for all projects):

```
## UI / design work - pipeline rule

For any UI build or redesign in a React + Tailwind project:

1. Lock direction first. If I point at a reference (screenshot/image/URL), run design-dna
   to extract it. Otherwise ui-ux-pro-max: style + palette + font pairing + stack.
   Reuse the saved project/client direction if one exists; otherwise propose 2 and wait.
2. Source components from the `magic` MCP (21st.dev) before hand-rolling - use /ui.
3. Assemble with frontend-design + impeccable.
4. Add motion only where it earns its place - Kowalski restraint, no motion slop.
   Pick by kind: animate (general), transitions-dev (plain CSS transitions),
   gsap-scrolltrigger / gsap-timeline (scroll + choreography), apple-design
   (gesture, spring, drag/swipe/sheet), threejs-* (3D).
5. Before showing me anything: run /impeccable critique (UX) AND /impeccable audit
   (a11y/perf/responsive) AND a motion audit (review-animations on the diff,
   improve-animations on a whole app, transitions-polish for timing).
   Report what failed, fix it, then present.

Never skip step 5. If the stack is not React/Tailwind, skip step 2 (Magic is React-only).
```

---

## Step 4 - Per-project / per-client one-time setup

Running these once is what lets the kickoff prompt stay short:

- `/impeccable init` - captures durable product context in `PRODUCT.md`.
- `/impeccable document` - generates `DESIGN.md` from the existing project code.
  (These two replaced `/impeccable teach`, removed in impeccable v4.)
- Lock a `ui-ux-pro-max` direction (style + palette + fonts + stack) and **save it per client**, so a returning client's look comes back automatically instead of being re-decided.

---

## Use it - the kickoff prompt

Paste this and fill the brackets:

```
/design [what + where]

Context: [new page | edit existing page] - [client name / personal]
Existing project context: [yes, reuse it | no, set it now]

Run the pipeline:
1. Lock direction. If I gave you a reference image/URL, use design-dna to extract it.
   Otherwise ui-ux-pro-max: style + palette + font pairing + stack.
   If project context exists, reuse it. If not, propose 2 directions and wait.
2. 21st.dev (magic MCP) - source/generate real shadcn/Tailwind components that
   match the locked direction via /ui. Skip if stack isn't React/Tailwind.
3. frontend-design + impeccable - assemble and implement.
4. Motion only where it earns its place: animate (general), transitions-dev (plain
   CSS transitions), gsap-scrolltrigger/gsap-timeline (scroll), apple-design (gesture).
5. Before showing me: run /impeccable critique AND /impeccable audit AND a motion
   audit (review-animations / transitions-polish). Report what failed, then fix.
```

### Short version (after a project context is set)

```
/design [change] - reuse project context, source from magic MCP, audit before showing me.
```

---

## Pipeline at a glance

```
direction          ->  source            ->  build                    ->  motion                       ->  gate                          ->  ship
(design-dna from a     (21st.dev /           (frontend-design +           (animate / transitions-dev /     (impeccable critique +
 reference, else        magic MCP)            impeccable)                  gsap-* / apple-design)           audit + review-animations)
 ui-ux-pro-max,
 +1 aesthetic skill)
```
