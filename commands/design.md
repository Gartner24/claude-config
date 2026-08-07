---
description: Run the design pipeline - lock direction (design-dna from a reference, else ui-ux-pro-max + register lens), source real components (21st.dev/magic MCP), assemble (frontend-design + impeccable), generate assets (nano-banana), add motion (animate/transitions-dev/gsap), then audit before presenting.
---

# Design

Run the full design pipeline on the request in `$ARGUMENTS`. Setup reference: `~/claude-config/DESIGN-PIPELINE.md`.

You can supply as much or as little as you want: target style or direction, brand colors and fonts, reference images (paste/drag them in), a Figma URL, or existing components/CSS to match. Whatever you provide overrides the proposal step and is locked as the direction; whatever you leave out gets proposed (2 options) and confirmed before anything is built.

If `$ARGUMENTS` is empty, ask: what to design + where, and whether to reuse an existing project/client direction.

## Pipeline

1. **Direction - `ui-ux-pro-max`.** Lock style + palette + font pairing + stack.
   - **A locked `brand-system.html` outranks this step.** If one exists, it is the binding source: read its `:root` custom properties + `#brand-tokens` JSON block and use those exact values. Do not re-propose a direction.
   - **A reference the user points at outranks the catalog.** Screenshot, image, or URL of a design they want to match -> run `design-dna` to extract it into a quantified JSON profile (tokens + qualitative style + visual effects), and use that as the locked direction. Only fall through to ui-ux-pro-max's catalog when there is no reference.
   - No brand system, but a saved project/client direction exists: reuse it.
   - Neither: propose 2 directions and wait for a pick. If this is a client build, stop and run `/brand-system` instead.
2. **Register lens.** Layer the aesthetic skill matching the locked direction's register onto every visual decision from here on:
   - premium / calm -> `high-end-visual-design`
   - editorial / minimal -> `minimalist-ui`
   - raw / bold -> `industrial-brutalist-ui`
3. **Source - `magic` MCP (21st.dev) via `/ui`.** Generate/source real shadcn/Tailwind components matching the locked direction before hand-rolling anything. Skip this step if the stack is not React/Next + Tailwind.
4. **Assemble - `frontend-design` + `impeccable`.** Implement the components into the page.
5. **Assets - `nano-banana`.** Generate brand imagery, hero frames, product shots, and the mascot with it (Gemini; `vtracer` post-process to vectorize a logo). Stock (Unsplash/Pexels/Pixabay) is the fallback when generated imagery is wrong for the surface, not the default. Any chart, graph, dashboard, or stat tile: read `dataviz` **before** writing the first line of chart code.
6. **Motion - `animate`.** Emil Kowalski's own skill is the motion specialist now; use it for all motion and `impeccable` for everything else. Add motion only where it earns its place. Kowalski restraint, no motion slop.
   - Simple CSS transitions (dropdown, modal, accordion, tabs, skeleton, icon swap) -> `transitions-dev`. Do not reach for a library for these.
   - Scroll-driven, pinned, or timeline-choreographed motion -> `gsap-scrolltrigger` / `gsap-timeline` (`gsap-react` in React).
   - Gesture-driven, spring, drag/swipe/sheet, or anything that must feel physical and interruptible -> `apple-design`.
   - Don't know what the effect is called -> `animation-vocabulary`.
   - 3D / WebGL surfaces -> the `threejs-*` set, with `gsap-scrolltrigger` if it is scroll-linked.
7. **Gate - audit before presenting.** Run BOTH impeccable passes - `impeccable critique` (UX review, heuristic scoring) and `impeccable audit` (a11y, perf, responsive) - plus a motion audit. Report what failed, fix it, then present. Never skip this step.
   - Motion audit: `review-animations` on the diff you just wrote, `improve-animations` for a whole existing app, `transitions-polish` to align durations/easing to the motion-token scale. Use `design-motion-principles` audit mode when you specifically want its HTML report with looping demos.
8. **Conversion (marketing surfaces only).** Landing, pricing, signup, or paywall? Run `cro` before presenting, and `pricing` / `signup` / `paywalls` / `popups` for the matching surface. `marketing-psychology` for the persuasion framing. Skip entirely for internal tools and app UI.
