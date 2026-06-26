---
description: Run the design pipeline - lock direction (ui-ux-pro-max), source real components (21st.dev/magic MCP), assemble (frontend-design + impeccable), add motion, then audit before presenting.
---

# Design

Run the full design pipeline on the request in `$ARGUMENTS`. Setup reference: `~/claude-config/DESIGN-PIPELINE.md`.

You can supply as much or as little as you want: target style or direction, brand colors and fonts, reference images (paste/drag them in), a Figma URL, or existing components/CSS to match. Whatever you provide overrides the proposal step and is locked as the direction; whatever you leave out gets proposed (2 options) and confirmed before anything is built.

If `$ARGUMENTS` is empty, ask: what to design + where, and whether to reuse an existing project/client direction.

## Pipeline

1. **Direction - `ui-ux-pro-max`.** Lock style + palette + font pairing + stack. If a saved project/client direction exists, reuse it. If not, propose 2 directions and wait for a pick.
2. **Source - `magic` MCP (21st.dev) via `/ui`.** Generate/source real shadcn/Tailwind components matching the locked direction before hand-rolling anything. Skip this step if the stack is not React/Next + Tailwind.
3. **Assemble - `frontend-design` + `impeccable`.** Implement the components into the page.
4. **Motion - `design-motion-principles` (build mode).** Add motion only where it earns its place. Kowalski restraint, no motion slop.
5. **Gate - audit before presenting.** Run `/impeccable audit` AND a motion audit. Report what failed, fix it, then present. Never skip this step.
