---
description: Produce a client's brand system as a self-contained HTML brand board (the canonical, binding source the build follows) - palette, typography, spacing, logo lockups, mascot, voice, components - with a machine-readable tokens block. Gets client sign-off. Run before /new-site.
---

# Brand System

Create (or formalize) a client's brand system as **`brand-system.html`** - the **canonical, binding
source of truth** the whole build follows, and the visual artifact the client signs off on. One file
does both jobs. `$ARGUMENTS` = client name + any existing material.

Spec to fill: `~/projects/freelance/website-build-templates/templates/brand-system.template.md`
(the required sections + the mandatory tokens block).

## Inputs
Whatever the client has: logo(s), existing colors/fonts, photos, sites they like, brand guidelines. If
there's nothing, make the decisions yourself from their positioning/audience. Ask only for what's
needed to decide.

## Step 1 - Make the brand decisions
Run the design-direction work: `ui-ux-pro-max` (style + palette + font pairing), plus the aesthetic
skills (`high-end-visual-design` / `minimalist-ui` / etc. as fits) and `impeccable` for discipline.
Lock: positioning/essence, voice, color, typography, spacing/layout, logo + lockups, mascot (if any),
imagery direction, motion principles, do/don't. Follow the template spec section by section.

## Step 2 - Emit `brand-system.html` (canonical + visual in one file)
A single self-contained HTML file that is BOTH the human sign-off board AND the machine source:
- **Visual board** (for the client): palette swatches, type specimens + scale, spacing, logo lockups
  (horizontal + stacked, each mode), mascot, example components (button/card/etc.), voice + do/don't.
- **Machine-readable tokens (mandatory - this is what the build imports):**
  - a `:root { --color-...; --font-...; --space-...; ... }` CSS custom-properties block - the literal
    tokens the site imports/copies, so the build uses exact values, never eyeballed ones.
  - a `<script type="application/json" id="brand-tokens">{ ...all tokens... }</script>` block so the
    tokens parse unambiguously (color, type, scale, spacing, radii, motion).
- Self-host fonts referenced; contrast pairings pass WCAG AA; mark any pairings to avoid.

## Step 3 - Sign-off (the gate)
Show the client the board. Get **explicit sign-off**. Record it in the file (a visible status line:
`signed off YYYY-MM-DD`). Until signed off, the build is blocked (static template §1 / `/new-site` Step 4).

## Output
`brand-system.html` in the client repo. `/new-site` and the templates read **this file's tokens** as
the binding source - Claude follows the `:root`/JSON tokens, not the prose. An accompanying
`brand-system.md` is optional notes only; the HTML is canonical.
