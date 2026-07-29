---
description: Run the design pipeline - lock direction (ui-ux-pro-max + register lens), source real components (21st.dev/magic MCP), assemble (frontend-design + impeccable), generate assets (nano-banana), add motion, then audit before presenting.
---

# Design

Run the full design pipeline on the request in `$ARGUMENTS`. Setup reference: `~/claude-config/DESIGN-PIPELINE.md`.

You can supply as much or as little as you want: target style or direction, brand colors and fonts, reference images (paste/drag them in), a Figma URL, or existing components/CSS to match. Whatever you provide overrides the proposal step and is locked as the direction; whatever you leave out gets proposed (2 options) and confirmed before anything is built.

If `$ARGUMENTS` is empty, ask: what to design + where, and whether to reuse an existing project/client direction.

## Pipeline

1. **Direction - `ui-ux-pro-max`.** Lock style + palette + font pairing + stack.
   - **A locked `brand-system.html` outranks this step.** If one exists, it is the binding source: read its `:root` custom properties + `#brand-tokens` JSON block and use those exact values. Do not re-propose a direction.
   - No brand system, but a saved project/client direction exists: reuse it.
   - Neither: propose 2 directions and wait for a pick. If this is a client build, stop and run `/brand-system` instead.
2. **Register lens.** Layer the aesthetic skill matching the locked direction's register onto every visual decision from here on:
   - premium / calm -> `high-end-visual-design`
   - editorial / minimal -> `minimalist-ui`
   - raw / bold -> `industrial-brutalist-ui`
3. **Source - `magic` MCP (21st.dev) via `/ui`.** Generate/source real shadcn/Tailwind components matching the locked direction before hand-rolling anything. Skip this step if the stack is not React/Next + Tailwind.
4. **Assemble - `frontend-design` + `impeccable`.** Implement the components into the page.
5. **Assets - `nano-banana`.** Generate brand imagery, hero frames, product shots, and the mascot with it (Gemini; `vtracer` post-process to vectorize a logo). Stock (Unsplash/Pexels/Pixabay) is the fallback when generated imagery is wrong for the surface, not the default. Any chart, graph, dashboard, or stat tile: read `dataviz` **before** writing the first line of chart code.
6. **Motion - `design-motion-principles` (build mode).** It is the motion specialist (Emil Kowalski lens); use it for all motion, and `impeccable` for everything else. Add motion only where it earns its place. Kowalski restraint, no motion slop.
7. **Gate - audit before presenting.** Run BOTH impeccable passes - `impeccable critique` (UX review, heuristic scoring) and `impeccable audit` (a11y, perf, responsive) - plus `design-motion-principles` audit mode (catches AI-slop motion). Report what failed, fix it, then present. Never skip this step.
