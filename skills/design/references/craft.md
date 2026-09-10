# Craft - the AI tells, the practitioners, and modern responsive CSS

> Research reference for the design pipeline. Compiled 2026-09-09 from primary
> sources; every tool, endpoint and browser-support figure was verified at that
> date and carries its URL inline. Items that could not be confirmed are marked
> UNVERIFIED - treat those as leads, not facts. Re-verify prices and model IDs
> before quoting them to a client.

# Research B: Anti-AI Craft

What separates shipped web UI from instantly-recognizable AI-generated UI.
Research date: 2026-09-09. Every browser-support claim below was checked against
caniuse.com or MDN on that date, with the URL given.

Source-quality note: section 1 (the tells) has thin primary-source coverage - most
of what exists in 2025-2026 is agency blogs and Medium posts, not engineers' own
writing. Those are cited but marked. Sections 2-5 are almost entirely primary
sources (the practitioners' own sites, MDN, caniuse).

---

## 1. The tells

Grouped by category. Each is phrased so an auditor could check it against a diff or
a rendered page. Sources for each cluster are given at the end of the cluster.

### 1.1 Color

**T1. Violet/indigo is the only accent.**
Check: the accent token resolves to something in the `violet-*` / `indigo-*` /
`purple-*` band (Tailwind `indigo-500`, `violet-600`, `purple-500`) and there is no
second accent, no neutral-warm, no semantic split.
Source: prg.sh names `bg-indigo-500` explicitly; isthatvibecoded.com lists
"purple-to-blue gradient color schemes" as a primary detection signal.

**T2. A gradient exists and it goes violet -> blue/cyan.**
Check: grep for `linear-gradient` / `bg-gradient-to-` and inspect stops. Two-stop
purple-to-blue is the canonical tell. Also check for `bg-clip-text` +
`text-transparent` on the H1 (gradient hero text).
Source: isthatvibecoded.com signals list; 925studios "purple-to-blue gradients
appearing in hero sections, CTA buttons, and background accents".

**T3. Gradients are decorative, not semantic.**
Check: count gradient usages. More than one distinct gradient, or a gradient on a
surface that carries no meaning (a section background, a card border), fails.
The developersdigest fix: "limit gradients to a single accent element".

**T4. Every shadow is a single blur, black, low alpha.**
Check: every `box-shadow` in the file has exactly one layer, color is
`rgba(0,0,0,0.1)` or `#000` at ~0.1, and offsets are `0 Npx`. prg.sh names it
exactly: "subtle shadows (exactly 0.1 opacity)".

**T5. Colored glow shadows.**
Check: `box-shadow` whose color is the accent hue at high blur/spread (e.g.
`0 0 40px rgba(139,92,246,.5)`). developersdigest pattern 8.

**T6. Dark mode is permanent and its body text is mid-grey.**
Check: no light theme exists; body text is `#a1a1aa`-ish on `#09090b`-ish, which
lands near or below 4.5:1. developersdigest patterns 5 and 6: "body text that fails
WCAG AA" in generated dark themes.

**T7. Glassmorphism cards with `backdrop-filter: blur()` over a gradient.**
Check: `backdrop-blur` + semi-transparent white/black border + a gradient behind.
isthatvibecoded.com detection signal.

**T8. Colored left/top border on cards.**
Check: `border-left: 4px solid <accent>` or `border-top` on a repeated card
component. developersdigest pattern 11.

### 1.2 Type

**T9. Inter (or the system stack) for everything, one family.**
Check: exactly one `font-family` declared, and it is Inter / Geist / Roboto /
`ui-sans-serif, system-ui`. No display face, no serif, no mono for data.
Source: 925studios; developersdigest pattern 1; prg.sh ("Inter, Roboto, Arial").

**T10. The 2026 replacement cliche: Space Grotesk + Instrument Serif + Geist.**
Check: those three names in the font stack. developersdigest pattern 2 - the
"escape" fonts have themselves become a tell.

**T11. One italic serif word inside an otherwise-sans hero headline.**
Check: an `<em>`/`<span>` inside the H1 with a different `font-family` and
`font-style: italic`. developersdigest pattern 3.

**T12. The type scale is a pure ratio with no display cut.**
Check: computed font sizes form a clean geometric sequence (1.25 or 1.333) with no
oversized display step and no compressed body steps. A real scale usually breaks
the ratio at the top (a display size) and at the bottom (caption/label).
Source: this is the inverse of the Utopia method (utopia.fyi) - see 3.1.

**T13. Letter-spacing is untouched, or applied uniformly.**
Check: no `letter-spacing` anywhere, OR a single `-0.02em` applied to all text
including body. Real practice: negative tracking on display sizes only, positive
tracking on small caps/labels.

**T14. All-caps section eyebrows everywhere.**
Check: `text-transform: uppercase` on more than one section label, usually with
`tracking-widest` and the accent color. developersdigest pattern 16.

**T15. No tabular numerals on numbers.**
Check: any stat row, table, price, or timer without
`font-variant-numeric: tabular-nums`. Digits jitter on update.

**T16. Measure is unbounded or set in px.**
Check: no `max-width` in `ch` on prose containers. A body column wider than
~75ch, or capped with `max-w-4xl` regardless of font size, both fail.

### 1.3 Layout

**T17. Centered hero, badge above H1, two buttons below.**
Check: the first section is `text-center`, contains a pill/badge element as the
first child, an H1, a subhead, and exactly two CTAs (one solid, one ghost).
Source: developersdigest patterns 9 and 10; prg.sh; 925studios.

**T18. Three feature cards in a row, icon on top.**
Check: `grid-cols-3` (or `md:grid-cols-3`) whose children are structurally
identical: icon, H3, paragraph. Source: prg.sh ("three features in boxes below,
each with an icon"); developersdigest pattern 12.

**T19. The canonical section order.**
Check the document outline for: hero -> logo strip -> 3 features -> how it works
(1-2-3) -> stats banner -> testimonials -> pricing -> FAQ -> CTA -> footer.
Any five in that order is a strong signal. Source: shuffle.dev, 925studios.

**T20. Numbered 1-2-3 step strip.**
Check: a row of three elements each containing a literal digit. developersdigest
pattern 13.

**T21. Stat banner row.**
Check: a horizontal row of 3-4 big-number + label pairs, evenly distributed.
developersdigest pattern 14.

**T22. The grid is never broken.**
Check: every section uses the same container width and the same column count.
No full-bleed element, no offset element, no element that spans into the gutter.

**T23. Perfect symmetry everywhere.**
Check: every multi-column layout is 1fr 1fr or 1fr 1fr 1fr. No `2fr 1fr`, no
sidebar, no asymmetric split.

### 1.4 Spacing and shape

**T24. Every border-radius resolves to the same token.**
Check: collect all `border-radius` values. If the set has size 1 (usually 8px,
12px, or 16px), fail. 925studios: "uniform 16px border radius everywhere".

**T25. Nested radii are equal, not concentric.**
Check: a rounded child inside a rounded parent where
`child.radius != parent.radius - padding`. See 4.3.

**T26. Every section has identical vertical padding.**
Check: collect all section `padding-block`. One value (usually `py-20` / 80px or
`py-24` / 96px) across every section, fail. Real pages vary rhythm by content
weight.

**T27. Identical card padding and identical card heights.**
Check: `p-6` on every card; all cards in a grid forced to the same height with no
content-driven variation. 925studios: "identical 24px padding", "identical card
heights throughout".

**T28. Spacing values come only from the framework's default scale.**
Check: no `calc()`, no custom property arithmetic, no optical adjustment anywhere.
Every gap is a raw `gap-4` / `gap-6` / `gap-8`.

### 1.5 Motion

**T29. One fade-in-on-scroll applied to every section.**
Check: a single reveal component or `data-aos`-style attribute wrapping every
section with identical duration and delay. 925studios: "the same generic fade-in
on every element". prg.sh notes the same for a scroll-following line "for no
discernible reason".

**T30. Buttons snap - no transition on `:active`, no hover transform.**
Check: interactive elements with `hover:bg-*` only, no `transition-*`, no
`:active` state. 925studios: "buttons that snap instead of easing", "hover states
that do nothing".

**T31. Durations are round and long.**
Check: every duration is 300ms or 500ms; no 120ms button feedback, no 200ms
tooltip. Emil Kowalski's standards put button feedback at 100-160ms and cap UI at
under 300ms (see 2.1).

**T32. Easing is the framework default or `ease-in-out` on everything.**
Check: no custom `cubic-bezier`. `ease-in` used on an entrance is an outright
error by Kowalski's rule ("never use ease-in on UI").

**T33. No `prefers-reduced-motion` block at all, or one that sets everything to
`animation: none`.**
Check: grep. Absent = fail. Present but nuking all motion = also a craft failure
(see 5.1).

**T34. Popovers/dropdowns scale from center, not from their trigger.**
Check: no `transform-origin` bound to the anchor. Kowalski's standards call for
origin-aware scaling off the trigger.

### 1.6 Imagery and icons

**T35. Lucide (or Heroicons) used unmodified, one size, one stroke width.**
Check: single icon package, every icon at 24px/1.5 stroke, no size or weight
variation for hierarchy. isthatvibecoded.com lists "Lucide icons throughout" as a
detection signal.

**T36. Emoji as icons.**
Check: emoji characters inside headings, sidebar nav items, or feature cards.
isthatvibecoded.com: "sparkle or rocket emojis in headings". developersdigest
pattern 15 (sidebar with emoji icons).

**T37. Abstract 3D blob / gradient mesh hero art.**
Check: an SVG/PNG that is a smooth abstract shape with no content meaning.
925studios: "abstract 3D blobs floating in space ... slightly too smooth, slightly
too symmetrical".

**T38. Stock photo of diverse team at a laptop.**
925studios names this literally.

**T39. No real product surface anywhere.**
Check: no screenshot, no data, no actual UI of the thing being sold. A generic
browser-chrome mockup wrapping a gradient counts as a fail.

### 1.7 Copy

**T40. Headline is a category, not a claim.**
Check for the literal families 925studios names: "Build the future of work",
"Your all-in-one platform", "Scale without limits". Generalize: headline contains
no proper noun, no number, and no verb the reader could disagree with.

**T41. Every feature card body is the same length and shape.**
Check: the three descriptions are within ~10 characters of each other and all
follow "Verb your noun with adjective noun."

**T42. No empty state, no error copy, no loading copy.**
Check: grep for empty/error/loading strings. Absent means only the happy path was
designed. This is the hey.com/kostac "missing edge states" tell.

### 1.8 Component choice and code shape

**T43. shadcn/ui primitives used at their defaults.**
Check: components imported and rendered with no variant additions, no token
overrides, `components.json` untouched. isthatvibecoded.com: shadcn/ui is "used by
almost every AI scaffold".

**T44. Tailwind arbitrary values are absent AND custom theme tokens are absent.**
Check: `tailwind.config` theme is empty/default and there are no `[...]` arbitrary
values. Everything came from the default palette and scale.

**T45. Leftover agent artifacts.**
Check: `CLAUDE.md`, `.cursorrules`, generator `<meta>` tags shipped to production.
isthatvibecoded.com uses these as fingerprints.

**T46. No optical alignment anywhere.**
Check: icon+label pairs aligned by bounding box; a play triangle centered in a
circle by geometric center; a quote mark not hung into the margin; no
`text-box-trim` or manual compensation. See 4.1.

**Sources for section 1** (all secondary/opinion unless noted):
- https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website
- https://isthatvibecoded.com/ (a working detector; its signal list is the most
  operational thing found)
- https://www.developersdigest.tech/blog/ai-design-slop-and-how-to-spot-it
  (16 named patterns, the most checkable list)
- https://www.925studios.co/blog/ai-slop-web-design-guide
- https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c
- https://shuffle.dev/blog/2026/01/why-do-most-ai-generated-websites-look-the-same/

The common causal claim across all of them: a generator returns the statistical
mean of its training data, and the mean of "modern SaaS landing page" is exactly
the list above. The tells are not bugs; they are the centroid.

---

## 2. The engineers, and the one technique each

### 2.1 Emil Kowalski - motion standards as literal numbers
Technique: a decision tree from interaction type to easing curve, plus duration
bands, plus a forbidden-property list. Concretely, from his own published
standards file:
```css
--ease-out:   cubic-bezier(0.23, 1, 0.32, 1);    /* entries and exits   */
--ease-in-out:cubic-bezier(0.77, 0, 0.175, 1);   /* on-screen movement  */
--ease-drawer:cubic-bezier(0.32, 0.72, 0, 1);    /* iOS-style drawer    */
```
Durations: button feedback 100-160ms, tooltip/popover 125-200ms, dropdown 150-250ms,
modal/drawer 200-500ms, with UI generally under 300ms. Never `ease-in` on UI.
Animate only `transform` and `opacity`. Never `scale(0)` - enter from `scale(0.9-0.97)`
plus `opacity: 0`. Button press is `scale(0.97)` at 160ms `ease-out`. Stagger 30-80ms.
Spring: Apple-style `{ type: "spring", duration: 0.5, bounce: 0.2 }`, bounce kept
0.1-0.3. Use CSS transitions (interruptible) over keyframes (restart from zero) for
anything dynamic. Never animate keyboard-initiated actions.
URLs:
- https://emilkowal.ski/ui/great-animations
- https://github.com/emilkowalski/skills/blob/main/skills/review-animations/STANDARDS.md
- https://animations.dev/ (his course)

### 2.2 Rauno Freiberg - the invisible details
Technique: motion must encode spatial origin and must be interruptible at any
frame; high-frequency interactions get no animation at all. Specifics he names:
app/menu opens from the element that spawned it (spatial provenance); destructive
gestures commit on gesture *end*, not on distance threshold; lightweight overlays
commit *during* the swipe past a distance; thrown objects keep momentum and angle;
command menus and context menus appear with zero motion because the animation
becomes a cognitive tax after the hundredth use; a selected item gets a brief
accent blink instead of a transition; Fitts's-law affordances (screen-edge "magic
corners" are infinitely large targets, radial menus equalize distance to every
option).
URLs:
- https://rauno.me/craft/interaction-design
- https://uiplaybook.dev/ (his documented component collection - verified live,
  covers Tooltip, Button, Select, Notification, TextField, Avatar, Checkbox,
  Motion, Popover)
- https://devouringdetails.com/

### 2.3 Paco Coursey - composable primitives over configured components
Technique: ship the behavior, not the skin. `cmdk` exposes `Command`,
`Command.Input`, `Command.List`, `Command.Item` and owns only filtering, keyboard
navigation and ARIA; every visual decision is yours. Same shape in `next-themes`
(no flash of wrong theme; the class is applied before paint). The reusable move is
the split: a headless layer that owns focus, keys and ARIA, and a styling layer
that owns nothing else.
URLs: https://paco.me/ , https://github.com/pacocoursey/cmdk ,
https://github.com/pacocoursey/next-themes
(Currently webmaster at Linear; previously Vercel design system.)

### 2.4 Jhey Tompkins - CSS-only interaction, no JS budget
Technique: build the effect with scroll-driven animations and anchor positioning
instead of a scroll listener and a positioning library. Formerly Chrome CSS/UI
DevRel, then design engineer at Vercel; his demos are the reference corpus for
`animation-timeline: view()` and the anchor API.
URL: https://www.jhey.dev/

### 2.5 Adam Argyle - tokens as custom properties, not a framework
Technique: Open Props - a flat set of CSS custom properties (sizes, colors,
easings, shadows, gradients, animations) you import and use directly, so the design
system is CSS variables rather than a build step. Components are authored with
private `--_`-prefixed locals so a consumer overrides one public prop rather than
fighting specificity:
```css
:where(.button) {
  --_bg-color: transparent;
  --_border-radius: var(--button-border-radius);
  --_min-height: 2.375rem;
  --_text-color: var(--primary);
}
```
`:where()` keeps specificity at zero so any consumer selector wins.
URLs: https://nerdy.dev/ , https://nerdy.dev/open-props-ui ,
https://open-props.style , GUI Challenges: https://web.dev/shows/gui-challenges

### 2.6 Josh W. Comeau - shadows as a light model, not a blur
Technique: pick one light source for the whole page and hold the ratio (vertical
offset = 2x horizontal). Elevation raises offset and blur and *lowers* opacity.
Never a single shadow - stack 5:
```css
box-shadow:
  0 1px  1px  hsl(0deg 0% 0% / 0.075),
  0 2px  2px  hsl(0deg 0% 0% / 0.075),
  0 4px  4px  hsl(0deg 0% 0% / 0.075),
  0 8px  8px  hsl(0deg 0% 0% / 0.075),
  0 16px 16px hsl(0deg 0% 0% / 0.075);
```
And never pure black: match the background hue and drop saturation/lightness -
on a `220deg` background, use `hsl(220deg 60% 50%)`, not `hsl(0deg 0% 0%)`.
Grey shadows look washed out because they desaturate the surface underneath.
URLs: https://www.joshwcomeau.com/css/designing-shadows/ ,
https://www.joshwcomeau.com/shadow-palette/

Note on the brief: the shadow palette generator is Josh W. **Comeau**'s. No source
was found for a "Josh Brumm" in this area - treat that attribution as UNVERIFIED.

### 2.7 Tobias Ahlin - opacity falloff shapes the shadow's character
Technique: layered `box-shadow` where the *opacity curve across layers* is the
design decision, not the blur. Uniform alpha across layers = neutral; decreasing
alpha (25% -> 5%) = sharp shadow concentrated at the object; increasing alpha
(8% -> 20%) = diffuse. More layers requires lower per-layer alpha to hold total
strength.
URL: https://tobiasahlin.com/blog/layered-smooth-box-shadows/

### 2.8 Andy Bell + Set Studio - CUBE CSS and "mentor, not micromanager"
Technique: CUBE = Composition, Utility, Block, Exception. Composition layer owns
layout and flow and works *with* the cascade rather than isolating every component;
utilities are single-purpose; blocks are components; exceptions are targeted
overrides. Paired with the buildexcellentwebsit.es principles: fluid type and
space, flexible layouts, progressive enhancement, and "be the browser's mentor, not
its micromanager" - give the browser rules and let it decide, rather than pinning
every value at every breakpoint.
URLs: https://cube.fyi/ , https://buildexcellentwebsit.es/

### 2.9 Heydon Pickering - algorithmic layout, zero media queries
Technique: the Flexbox Holy Albatross. Force `flex-basis` via `calc()` to swing
between an arbitrarily large positive and a large negative value, so N items flip
from a row to a column at a *container* threshold with no media query and no
wrapper. Companion technique: quantity queries -
`li:nth-last-child(4n):first-child ~ li` styles a list only when it has a multiple
of four items.
URLs: https://heydonworks.com/article/the-flexbox-holy-albatross-reincarnated/ ,
https://every-layout.dev/ (with Andy Bell)

### 2.10 Every Layout (Pickering + Bell) - the 13 primitives
Technique: compose pages from named, content-driven primitives instead of a grid
system. Verified list on every-layout.dev/layouts/: Stack, Box, Center, Cluster,
Sidebar, Switcher, Cover, Grid, Frame, Reel, Imposter, Icon, Container. Each solves
one layout intent and each is breakpoint-free.
URL: https://every-layout.dev/layouts/

### 2.11 Ahmad Shadeed - container query units
Technique: size type, spacing and avatars off the *container*, not the viewport, so
a component is correct wherever it is dropped:
```css
.card__title    { font-size: clamp(1rem, 3cqi, 2rem); }
.section-title  { margin-bottom: clamp(0.5rem, 1.5cqi, 1rem); }
.c-avatar       { --size: calc(60px + 10cqi); width: var(--size, 100px); }
.card           { gap: calc(0.5rem + 1cqmin); }
```
(His article predates the final unit names and writes `qw`/`qi`; the shipped units
are `cqw cqh cqi cqb cqmin cqmax` - see 3.2.)
URLs: https://ishadeed.com/article/container-query-units/ ,
https://ishadeed.com/article/css-container-query-guide/ ,
https://ishadeed.com/article/css-container-style-queries/

### 2.12 Trys Mudford + James Gilyead (Utopia, Clearleft) - fluid scales
Technique: define two type scales - one at the min viewport, one at the max - and
let the browser interpolate. The clamp is derived, not hand-picked:
```
slope     = (maxSize - minSize) / (maxVw - minVw)
intercept = minSize - slope * minVw
font-size: clamp(minSize_rem, intercept_rem + (slope*100)vw, maxSize_rem)
```
e.g. `clamp(1.62rem, 1.5041rem + 0.5793vi, 1.9531rem)`. Crucially Utopia also
*warns* when a step fails WCAG 1.4.4 - see 5.2.
URLs: https://utopia.fyi/ , https://utopia.fyi/blog/clamp/ ,
https://www.trysmudford.com/blog/utopia-wcag-warnings/

### 2.13 Adam Wathan + Steve Schoger (Refactoring UI) - hierarchy without size
Technique: most interface problems are hierarchy problems, and the fix is usually
to *de-emphasize the secondary* rather than enlarge the primary. Use weight and
color to carry hierarchy before reaching for size. Their free primer is "7
Practical Tips for Cheating at Design".
URLs: https://refactoringui.com/ ,
https://medium.com/refactoring-ui/7-practical-tips-for-cheating-at-design-40c736799886
(Medium returns 403 to automated fetch; title and authorship verified via search.
The specific tip contents there are UNVERIFIED at this URL.)

### 2.14 Erik Kennedy - HSB-derived palettes
Technique: think in HSB, not RGB or hex, because changes to H/S/B are predictable
by eye. Generate the whole UI palette by moving saturation and brightness within
one or two hues, which gives you darks, lights, backgrounds, accents and
eye-catchers without the page looking noisy.
URL: https://www.learnui.design/blog/7-rules-for-creating-gorgeous-ui-part-1.html

### 2.15 Matthew Strom-Awn - least-wrong colors, perceptual difference
Technique: choose palette members by perceptual distance (CIE Delta-E) rather than
by even hue rotation, so categorical colors are actually distinguishable and
accessible, not just evenly spaced in HSL.
URLs: https://mattstromawn.com/writing/how-to-pick-the-least-wrong-colors/ ,
https://mattstromawn.com/writing/generating-color-palettes/

### 2.16 Nate Baldwin - Leonardo, contrast-first color
Technique: generate swatches from *target contrast ratios* against a specified
background rather than from lightness steps, and let the tool place key colors on
the scale by their perceptual lightness. The palette is a function of the
background brightness, so a theme can be re-derived instead of re-picked.
URLs: https://leonardocolor.io/ , npm `@adobe/leonardo-contrast-colors`

### 2.17 Stripe - perceptually uniform color systems
Technique: translate the palette into CIELAB, where L is perceptually uniform
(unlike HSL's lightness), then adjust and compare colors by perceptual contrast.
Stripe built a visualizer because the tooling did not exist, and used it to steer
around "impossible colors" (out-of-gamut Lab values).
URL: https://stripe.com/blog/accessible-color-systems

### 2.18 Linear - density and noise reduction as the design goal
Technique: the redesign brief was explicitly to reduce visual noise while
*increasing* hierarchy and density of navigation - sidebar, tabs, headers and
panels re-aligned to a shared optical grid. Their published craft notes are the
clearest example of "the design is the removal".
URLs: https://linear.app/now/craft , https://linear.app/now/a-design-reset ,
https://linear.app/now/how-we-redesigned-the-linear-ui ,
https://linear.app/now/behind-the-latest-design-refresh

### 2.19 Cassie Evans - SVG animation with a real timeline
Technique: animate SVG with GSAP rather than CSS once you need morphing, stroke
drawing, or cross-browser consistency, because browsers implement the SVG spec
differently and the library normalizes it. Her worked example (drawing and rigging
an SVG self-portrait) is the teaching artifact.
URLs: https://www.cassie.codes/posts/making-a-lil-me-part-1/ ,
https://www.cassie.codes/speaking/getting-started-with-svg-animation/

### 2.20 Lynn Fisher - responsive as a set of distinct compositions
Technique: her portfolio is redesigned yearly and each breakpoint is a *different
drawing*, not a reflow of the same one - which is the strongest counterexample to
"responsive means the same layout, narrower". Companion: A Single Div, ten years of
CSS drawings using one HTML element, which is a discipline for learning what
pseudo-elements, gradients and shadows can actually do.
URLs: https://lynnandtonic.com/thoughts/entries/case-study-2020-refresh/ ,
https://lynnandtonic.com/work/
(The "A Single Div" project is confirmed; its standalone domain is UNVERIFIED.)

### 2.21 Bramus Van Damme - scroll-driven animations reference
Technique: the canonical demo corpus and polyfill guidance for `scroll()` /
`view()` timelines. Site loads the flackr/scroll-timeline polyfill when the browser
lacks support, which is the practical fallback pattern.
URL: https://scroll-driven-animations.style/

---

## 3. Responsive craft, the real version

Browser support verified 2026-09-09. Percentages are caniuse global usage.

### 3.1 Fluid type and space via clamp() (Utopia)
```css
/* one step of a Utopia scale */
--step-0: clamp(1rem, 0.96rem + 0.22vi, 1.125rem);
--step-5: clamp(2.49rem, 1.83rem + 3.29vi, 4.24rem);
--space-m: clamp(1.13rem, 1.07rem + 0.29vi, 1.31rem);
```
Support: `clamp()` is universally available (Baseline; caniuse `css-math-functions`
is in the mid-90s globally and has been shipped in all evergreen engines since
2020). No fallback needed for evergreen targets.
Caveat that matters more than support: see 5.2 - a clamped max font-size can fail
WCAG 1.4.4.
Use `vi` (logical inline viewport unit) over `vw` so the scale is writing-mode
correct.

### 3.2 Container queries and `cq*` units
```css
.card-wrap { container-type: inline-size; container-name: card; }
@container card (min-width: 30rem) {
  .card { grid-template-columns: 12rem 1fr; }
}
.card__title { font-size: clamp(1rem, 3cqi, 2rem); }
```
Support: 94.87% global. Chrome/Edge 106, Safari 16.0, Firefox 110.
https://caniuse.com/css-container-queries
Units: `cqw cqh cqi cqb cqmin cqmax` ship with the same feature. Fallback: a
media-query variant, or the container-query-polyfill for legacy. In 2026 a fallback
is optional for evergreen-only targets.
Style queries (`@container style(--state: active)`) are a separate, later feature -
treat as progressive enhancement.

### 3.3 Intrinsic / algorithmic layouts (Every Layout primitives)
```css
/* Switcher: row until the container is too small, then column - no media query */
.switcher { display: flex; flex-wrap: wrap; gap: var(--space-s); }
.switcher > * { flex-grow: 1; flex-basis: calc((30rem - 100%) * 999); }

/* Sidebar */
.with-sidebar { display: flex; flex-wrap: wrap; gap: var(--space-m); }
.with-sidebar > :first-child { flex-basis: 20rem; flex-grow: 1; }
.with-sidebar > :last-child  { flex-basis: 0; flex-grow: 999; min-inline-size: 50%; }

/* Stack: spacing as a rule about adjacency, not a margin on every element */
.stack > * + * { margin-block-start: var(--space-s); }
```
Support: flexbox + `calc()` - universal, no fallback.
Primitives: Stack, Box, Center, Cluster, Sidebar, Switcher, Cover, Grid, Frame,
Reel, Imposter, Icon, Container. https://every-layout.dev/layouts/

### 3.4 Auto-fitting grid
```css
.grid { display: grid; gap: var(--space-m);
        grid-template-columns: repeat(auto-fit, minmax(min(18rem, 100%), 1fr)); }
```
The `min(18rem, 100%)` guard is the part generators omit; without it the track
overflows below 18rem. Support: universal.

### 3.5 `:has()`
```css
.card:has(img) { grid-template-rows: auto 1fr; }
form:has(:invalid) .submit { opacity: .5; }
label:has(+ input:focus-visible) { color: var(--accent); }
```
Support: 94.82% global. Chrome/Edge 105, Safari 15.4, Firefox 121.
https://caniuse.com/css-has
Fallback: unsupported browsers simply do not match, so it degrades to the base
state. Safe as enhancement; do not put required layout inside it.

### 3.6 Subgrid
```css
.card { display: grid; grid-row: span 3; grid-template-rows: subgrid; }
```
Aligns card internals (title / body / footer) across a grid of cards without fixed
heights - the honest fix for T27.
Support: 93.48% global. Firefox 71, Safari 16.0, Chrome/Edge 117.
https://caniuse.com/css-subgrid
Fallback: `@supports (grid-template-rows: subgrid)` around it; default to flex
column with `margin-block-start: auto` on the footer.

### 3.7 `text-wrap: balance` and `pretty`
```css
h1, h2, h3, .lede { text-wrap: balance; }   /* headings, <= ~6 lines */
p                { text-wrap: pretty; }     /* body: kills orphans    */
```
`balance`: 92.73% global; Chrome/Edge 130 full (partial 114-129), Firefox 121,
Safari 17.5. https://caniuse.com/css-text-wrap-balance
`pretty`: 83.79% global; Chrome/Edge 130, Safari 26.0, **not supported in Firefox**
as of Firefox 158. https://caniuse.com/mdn-css_properties_text-wrap-style_pretty
Both degrade to normal wrapping. No fallback needed; never rely on either for
layout, only for polish.

### 3.8 Logical properties
`margin-block-start`, `padding-inline`, `inset-inline-start`, `border-inline-end`,
`min-inline-size`. Support: universal in evergreen engines (Baseline widely
available). Use them by default - they cost nothing and make the CSS correct under
RTL and vertical writing modes.

### 3.9 `aspect-ratio`
```css
.media { aspect-ratio: 16 / 9; object-fit: cover; }
```
Support: Baseline widely available (Chrome 88, Firefox 89, Safari 15). No fallback
needed. Combine with explicit `width`/`height` attributes on `<img>` to prevent CLS.

### 3.10 `interpolate-size` / `calc-size()` - animating to `auto`
```css
:root { interpolate-size: allow-keywords; }
details::details-content { height: 0; transition: height .3s ease, content-visibility .3s allow-discrete; }
details[open]::details-content { height: auto; }
```
Support: **72.21% global. Chromium only** - Chrome/Edge 129, Opera 115, Samsung 28.
No Firefox (through 158), no Safari (through 27).
https://caniuse.com/mdn-css_properties_interpolate-size
https://developer.mozilla.org/en-US/docs/Web/CSS/interpolate-size
MDN labels it "Limited availability", not Baseline. **Fallback required**: the
transition simply does not run elsewhere, so ensure the open/closed states are both
correct without animation. Note `calc-size()` implies `interpolate-size:
allow-keywords` where it appears; `interpolate-size` is preferred because it
inherits.

### 3.11 Scroll-driven animations
```css
@keyframes reveal { from { opacity: 0; translate: 0 1rem; } }
.section { animation: reveal linear both;
           animation-timeline: view();
           animation-range: entry 10% cover 30%; }
```
Support: `animation-timeline` 87.22% global. Chrome/Edge 115, Firefox 158,
Safari 26.0. https://caniuse.com/mdn-css_properties_animation-timeline
**Fallback required for older Safari/Firefox**: wrap in
`@supports (animation-timeline: view())`, default to the visible end state (never
to `opacity: 0`), or load the flackr/scroll-timeline polyfill as
scroll-driven-animations.style does.

### 3.12 `@starting-style` and `transition-behavior: allow-discrete`
```css
dialog[open] { opacity: 1; translate: 0 0; }
dialog       { opacity: 0; translate: 0 1rem;
               transition: opacity .2s, translate .2s, overlay .2s allow-discrete,
                           display .2s allow-discrete; }
@starting-style { dialog[open] { opacity: 0; translate: 0 1rem; } }
```
Support: `@starting-style` 91.92% global. Chrome/Edge 117, Firefox 129, Safari 17.5.
https://caniuse.com/mdn-css_at-rules_starting-style
Degrades to an instant appearance. No fallback needed.

### 3.13 Popover
```html
<button popovertarget="menu">Open</button>
<div id="menu" popover>...</div>
```
Support: 92.51% global. Chrome/Edge 114, Safari 17.0, Firefox 125.
https://caniuse.com/mdn-html_global_attributes_popover
Gets top-layer, light-dismiss and focus handling for free. Fallback: the element
renders inline in unsupported browsers - gate with
`@supports selector(:popover-open)` or feature-detect `HTMLElement.prototype.popover`.

### 3.14 Anchor positioning
```css
.trigger { anchor-name: --trg; }
.menu    { position: absolute; position-anchor: --trg;
           position-area: block-end span-inline-end;
           position-try-fallbacks: flip-block, flip-inline; }
```
Support: **85.93% global, and mostly partial.** Chrome/Edge 125-150 partial, 151+
full; Safari 26.0+ partial, 27 full; Firefox 145-146 behind a flag, 147+ partial.
https://caniuse.com/css-anchor-positioning
**Fallback required.** Keep a `position: absolute` + JS or flex fallback behind
`@supports (anchor-name: --a)`. This is the single most over-claimed feature in
2026 - it is not safe to ship unguarded.

### 3.15 `field-sizing`
```css
textarea, input { field-sizing: content; min-inline-size: 12ch; max-block-size: 20lh; }
```
Support: 85.81% global. Chrome/Edge 123, Firefox 152, Safari 26.2, Samsung 27.
https://caniuse.com/mdn-css_properties_field-sizing
Degrades to a fixed-size field. No fallback needed for a non-critical nicety; if
auto-grow is required, keep the JS shim behind
`@supports not (field-sizing: content)`.

### 3.16 `light-dark()`
```css
:root { color-scheme: light dark; }
body  { background: light-dark(var(--sand-1), var(--ink-1));
        color:      light-dark(var(--ink-1),  var(--sand-1)); }
```
Support: 89.86% global. Chrome/Edge 123, Firefox 120, Safari 17.5.
https://caniuse.com/mdn-css_types_color_light-dark
Requires `color-scheme` to be set on the element or an ancestor. Fallback: declare
the light value first, then override inside
`@media (prefers-color-scheme: dark)` - cheap and worth doing.

### 3.17 `color-mix()`
```css
--border: color-mix(in oklab, var(--surface) 88%, var(--ink));
--accent-hover: color-mix(in oklab, var(--accent) 85%, black);
--ring: color-mix(in srgb, var(--accent) 40%, transparent);
```
Support: 93.91% global. Chrome/Edge 111, Firefox 113, Safari 16.2.
https://caniuse.com/mdn-css_types_color_color-mix
Fallback: declare a static hex first, then the `color-mix()` line - the older
browser drops the invalid declaration.

### 3.18 OKLCH
```css
--accent-500: oklch(62% 0.19 264);
--accent-600: oklch(54% 0.19 264);   /* same hue+chroma, lightness steps only */
```
Support: 94.25% global. Chrome/Edge 111, Firefox 113, Safari 15.4.
https://caniuse.com/mdn-css_types_color_oklch
Why it matters: OKLCH lightness is perceptually uniform, so a ramp built by
stepping L alone actually looks evenly spaced - which HSL does not (this is the
same argument Stripe makes with CIELAB and Baldwin makes with HSLuv). Fallback: an
sRGB hex declared first.

### 3.19 `text-box-trim` / `text-box-edge`
```css
h1 { text-box: trim-both cap alphabetic; }
```
Removes the font's leading half-boxes so a heading's optical top and bottom sit
where the design says they do - the fix for "the gap above this title is 3px bigger
than the gap below it".
Support: 86.46% global. Chrome/Edge 133, Safari 18.2, Firefox 154.
https://caniuse.com/mdn-css_properties_text-box-trim
Degrades to normal leading. No fallback required, but do not tune padding to
compensate on top of it or the unsupported browsers get double-corrected.

---

## 4. What "designed" looks like in code

### 4.1 Optical alignment
- Geometric centering is wrong for asymmetric glyphs and shapes. A play triangle
  centered in a circle needs roughly 1-2px of horizontal nudge toward the point.
  Check: any `place-items: center` on a container whose child is a triangle, a
  chevron, or a search magnifier.
- Text next to an icon aligns on the cap height and the icon's optical center, not
  on both bounding boxes. `align-items: center` on a `line-height: 1.5` label plus
  a 24px icon is off by roughly (lineHeight - capHeight)/2.
  `text-box: trim-both cap alphabetic` (3.19) removes the cause rather than
  compensating for it.
- Quote marks, bullets and list markers hang into the margin. Check: any blockquote
  whose opening quote sits inside the text column.
- Buttons with a trailing chevron need more inline-end padding than inline-start,
  because the chevron carries less optical weight than a letter.

### 4.2 Optical sizing
```css
body { font-optical-sizing: auto; }        /* default; requires an opsz axis */
h1   { font-variation-settings: "opsz" 72; }
```
`font-optical-sizing: auto` is the initial value and is Baseline widely available
since March 2020 - but it does nothing unless the font is a variable font with an
`opsz` axis.
https://developer.mozilla.org/en-US/docs/Web/CSS/font-optical-sizing
Check: shipping a variable font with `opsz` and then setting
`font-optical-sizing: none`, or shipping a static font and claiming optical sizing.

### 4.3 Concentric radii
```css
.card       { --pad: 0.75rem; --r: 1rem; padding: var(--pad); border-radius: var(--r); }
.card > img { border-radius: calc(var(--r) - var(--pad)); }
```
Rule: `innerRadius = outerRadius - distance`. Equal radii on nested rounded boxes
make the gap look thick at the corners and thin at the edges.
Sources: https://cloudfour.com/thinks/the-math-behind-nesting-rounded-corners/ ,
https://frontendmasters.com/blog/the-classic-border-radius-advice-plus-an-unusual-trick/
Corollary: a design with only one radius token cannot express this - a real system
has at least 3-4 radius steps plus `9999px` for pills.

### 4.4 Hierarchy from four axes, not one
Size, weight, color and measure. Refactoring UI's operative move is to
*de-emphasize the secondary* (drop it to a muted token, drop weight to 400) rather
than enlarge the primary. Check: a page where every level of hierarchy differs only
in `font-size` fails.

### 4.5 Measure in `ch`
```css
.prose { max-inline-size: 68ch; }
.lede  { max-inline-size: 46ch; }
```
`ch` scales with the font, so the measure stays right when the type scale changes.
`max-w-prose`-style px caps do not.

### 4.6 Tabular numerals
```css
.stat, td.num, time, .price { font-variant-numeric: tabular-nums; }
```
Also `slashed-zero` for anything that could be an ID. Without this, any number that
updates (a timer, a counter, a live price) visibly shifts width.

### 4.7 Borders derived from the surface, not flat grey
```css
--border: color-mix(in oklab, var(--surface) 88%, var(--ink));
```
A flat `#e5e7eb` border reads as a foreign object on a tinted or dark surface. A
mixed border stays in the same family and survives a theme flip.

### 4.8 Focus rings that belong to the brand
```css
:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: inherit;
}
```
Support for `:focus-visible`: 95.49% global. Chrome/Edge 86, Firefox 4, Safari 15.4.
https://caniuse.com/css-focus-visible
`outline-offset` beats a `box-shadow` ring because it does not compose with the
element's own shadow and it follows `border-radius`.
Anti-check: `outline: none` anywhere without a `:focus-visible` replacement.

### 4.9 Hover states with a real transform-origin
```css
.card { transition: transform .16s var(--ease-out), box-shadow .16s var(--ease-out); }
.card:hover { transform: translateY(-2px); }
.menu { transform-origin: var(--transform-origin); }  /* set from the trigger */
.btn:active { transform: scale(.97); transition-duration: .1s; }
```
The tell is not "no hover" - it is hover that changes only background color.

### 4.10 Grain and atmosphere
An SVG `feTurbulence` overlay at 2-4% opacity, `mix-blend-mode: overlay`,
`pointer-events: none`, on a fixed pseudo-element. Costs one element and breaks the
flat-gradient look immediately. Turn it off under
`@media (prefers-reduced-transparency: reduce)` if you animate it.

### 4.11 Asymmetric grids and grid-breaking
- `grid-template-columns: minmax(0, 7fr) minmax(0, 5fr)` instead of `1fr 1fr`.
- One element per page that spans into the gutter or goes full-bleed:
  ```css
  .full-bleed { grid-column: 1 / -1; width: 100vw; margin-inline: calc(50% - 50vw); }
  ```
- A grid of cards where one card spans two columns because its content earns it.

### 4.12 Content-driven section rhythm
Vertical rhythm should vary with section weight - a dense comparison table needs
less air than a single-sentence statement. Check: the set of section
`padding-block` values has more than one member, and the largest is at least ~1.6x
the smallest.

---

## 5. Accessibility and motion as craft

### 5.1 `prefers-reduced-motion` done properly
The query value is `reduce`, and it means *reduce*, not *remove*. Kowalski's
standards: keep opacity and color transitions, drop transforms and parallax.
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
    scroll-behavior: auto !important;
  }
}
```
That global nuke is the common recipe and it is a blunt instrument - it also kills
the transitions that communicate state. Better: author motion inside
`@media (prefers-reduced-motion: no-preference)` so the reduced state is the
default, and hand-write a `reduce` variant (cross-fade instead of slide) for the
components where motion carried meaning.
Also handle it in JS: `matchMedia('(prefers-reduced-motion: reduce)')` for anything
driven by Framer Motion / GSAP, since CSS overrides will not reach it.
Sources: https://css-tricks.com/revisiting-prefers-reduced-motion/ (Eric Bailey) ,
https://www.smashingmagazine.com/2021/10/respecting-users-motion-preferences/ ,
https://github.com/emilkowalski/skills/blob/main/skills/review-animations/STANDARDS.md
Why it reads as generated when absent: a page with one scroll-reveal on every
section and no `reduce` branch is the exact signature of a component copied in
without a decision behind it.

### 5.2 Contrast that survives a background change
Two failure modes:
- **The dark-mode default.** Generated dark themes routinely ship mid-grey body
  text that fails 4.5:1 (developersdigest pattern 6). Check every text/background
  pair in *both* themes, not just the one you looked at.
- **The background changed and nobody re-checked.** Contrast is a property of the
  pair. Changing a surface token invalidates every foreground on it.
Structural fix: derive foregrounds from contrast targets rather than picking them -
Leonardo (leonardocolor.io) generates swatches *by target ratio against a stated
background*, so a background change re-derives the palette instead of silently
breaking it. Stripe's CIELAB approach and Strom's Delta-E approach are the same
idea from the perceptual-uniformity side.

### 5.3 Fluid type versus WCAG 1.4.4
The real trap in `clamp()`-based scales: `rem` grows with browser zoom, `vw`/`vi`
does not, because the viewport width is unchanged by zoom. So a step like
`clamp(1.62rem, 1.5041rem + 0.5793vi, 1.9531rem)` can fail to reach 200% of its
original size at 200% zoom, failing WCAG 1.4.4 Resize Text (AA). It bites hardest
on large headings at wide viewports, where the min-to-max spread is biggest.
Utopia now flags failing steps and names the viewport range where they fail.
Remedies: raise the type scale at the min viewport, or lower it at the max
viewport, so the spread narrows. Adrian Roselli's stricter position: do not set a
maximum font size at all, or never set the max below 2x the base.
Sources: https://www.trysmudford.com/blog/utopia-wcag-warnings/ ,
https://adrianroselli.com/2019/12/responsive-type-and-zoom.html ,
https://www.smashingmagazine.com/2023/11/addressing-accessibility-concerns-fluid-type/

### 5.4 Focus management
- Never `outline: none` without a `:focus-visible` replacement (4.8).
- After a route change or a dialog close, focus must land somewhere deliberate -
  the heading of the new view, or the control that opened the dialog. Native
  `<dialog>` and the `popover` attribute handle the trap and the restore for you,
  which is one of the strongest reasons to use them (3.12, 3.13).
- Focus order follows DOM order; CSS `order` and `grid-auto-flow` reordering break
  it. Check any layout that visually reorders items.

### 5.5 Why the pretty-but-inaccessible version reads as generated
The correlation is causal, not coincidental. Every accessibility detail above -
contrast checked in both themes, a designed focus ring, a reduced-motion branch,
focus returned after a dialog, `ch`-based measure, an empty state - is a decision
that only exists because a person went looking for a case that was not the happy
path. A generator produces the happy path. So the absence of edge-case handling is
the same signal as the absence of design: nobody was there.

---

## The AI-tell audit checklist

Each item passes or fails against a diff or a rendered page. Fail count is the
score; anything over ~8 fails reads as generated on sight.

1. Collect every `border-radius` value in the diff. FAIL if the distinct set has
   size 1.
2. Collect every section `padding-block`. FAIL if the distinct set has size 1, or
   if max/min < 1.3.
3. Collect every `box-shadow`. FAIL if any is a single layer, or if every shadow
   color is pure black/grey.
4. Grep the accent token. FAIL if it is the only accent and lands in
   violet/indigo/purple.
5. Grep `linear-gradient` and `bg-gradient-to-`. FAIL if any stop pair is
   purple -> blue/cyan, or if there is more than one distinct gradient, or if the
   H1 uses `bg-clip-text` + `text-transparent`.
6. Count declared `font-family` values. FAIL if there is exactly one and it is
   Inter / Geist / Roboto / bare system stack.
7. Look for an italic serif `<span>` inside the H1. FAIL if present.
8. Compute the ratios between adjacent font-size steps. FAIL if all ratios are
   equal (a pure 1.25 or 1.333 with no display cut and no compressed small end).
9. Grep `letter-spacing`. FAIL if absent entirely, or if one value is applied to
   body text as well as display text.
10. Grep `font-variant-numeric`. FAIL if any stat, price, table cell, or timer
    lacks `tabular-nums`.
11. Grep `ch` in max-width/max-inline-size. FAIL if no prose container is measured
    in `ch`.
12. Inspect the first section. FAIL if it is centered AND has a badge above the H1
    AND has exactly two CTAs.
13. Inspect the second/third section. FAIL if it is a 3-column grid of
    structurally identical icon-title-text cards.
14. Read the document outline. FAIL if five or more sections appear in the order
    hero / logos / features / steps / stats / testimonials / pricing / FAQ / CTA.
15. Grep for a literal 1-2-3 numbered step strip and for a 3-4 item big-number
    stat banner. FAIL if either is present unmodified.
16. Check every multi-column layout's track list. FAIL if all are `1fr 1fr` or
    `1fr 1fr 1fr` with no asymmetric split anywhere.
17. Check for one full-bleed or gutter-breaking element. FAIL if the page never
    leaves the container.
18. For each rounded child inside a rounded parent, check
    `child.radius == parent.radius - padding`. FAIL on any mismatch.
19. Grep `transition` on interactive elements. FAIL if any button/link/card has a
    hover style but no transition, or has no `:active` state.
20. Collect every duration. FAIL if all are 300ms/500ms, or if any UI transition
    exceeds 300ms without a reason (drawer/modal excepted up to 500ms).
21. Grep `cubic-bezier`. FAIL if there is none. FAIL harder if `ease-in` is used on
    an entrance.
22. Check reveal animations. FAIL if a single reveal wrapper with identical
    duration/delay is applied to every section.
23. Check popover/dropdown/tooltip. FAIL if `transform-origin` is not derived from
    the trigger (modals excepted).
24. Grep `prefers-reduced-motion`. FAIL if absent. FAIL if present only as a
    blanket `animation: none` on `*` with no per-component `reduce` variant.
25. Grep `:focus-visible`. FAIL if absent, or if `outline: none` appears without a
    replacement, or if the ring color is browser-default rather than a brand token.
26. Compute contrast for every text/surface pair in BOTH themes. FAIL on anything
    under 4.5:1 for body, 3:1 for large text.
27. Count icon sizes and stroke widths. FAIL if there is exactly one of each across
    the whole page.
28. Grep for emoji in headings, nav items and card titles. FAIL if present.
29. Look for real product surface: a screenshot, real data, an actual UI. FAIL if
    the only imagery is an abstract gradient blob or a stock team photo.
30. Grep for empty-state, error-state and loading copy. FAIL if none exists.
31. Read the H1. FAIL if it contains no proper noun, no number, and makes no claim
    a competitor could contradict.
32. Compare the three feature descriptions. FAIL if they are within 10 characters
    of the same length and share the same grammatical shape.
33. Check the Tailwind/theme config. FAIL if the theme object is default/empty AND
    there are no arbitrary values - nothing was decided.
34. Check shadcn/ui components. FAIL if imported and rendered at defaults with no
    variant additions and no token overrides.
35. Check the repo root and the built output. FAIL if `CLAUDE.md`, `.cursorrules`,
    or a generator `<meta>` tag ships.
36. Look for one deliberate optical adjustment anywhere - a nudged glyph, a hung
    quote, asymmetric button padding, `text-box-trim`. FAIL if there is none.

## The craft moves worth encoding

Ranked by impact per unit of effort. The first six are near-free and change the
read of the page immediately.

1. **Two accents and a real neutral ramp, built in OKLCH by stepping lightness.**
   One line of tokens. Kills tells T1-T3 outright. `oklch()` is 94.25% supported
   with an sRGB hex fallback. (Stripe, Baldwin, Strom, Argyle.)
2. **Layered shadows on a single stated light source, tinted to the surface hue.**
   Five comma-separated layers and an `hsl()` hue match. Kills T4-T5 and makes
   every card look considered. (Comeau, Ahlin.)
3. **A radius *scale* plus the concentric rule `inner = outer - padding`.**
   Three tokens and one `calc()`. Kills T24-T25.
4. **Custom easing tokens plus duration bands per interaction type.**
   Three `cubic-bezier` custom properties and a table. Kills T30-T32. Never
   `ease-in` on UI; button feedback 100-160ms; UI under 300ms. (Kowalski.)
5. **Hierarchy on four axes and de-emphasis of the secondary.**
   Costs nothing but a decision. Weight + color + measure before size. (Wathan and
   Schoger.)
6. **`ch` measure, `tabular-nums` on data, negative tracking on display only.**
   Three declarations. Kills T13, T15, T16.
7. **A `:focus-visible` ring in the brand accent with `outline-offset` and
   `border-radius: inherit`.** 95.49% support, four lines, and it is the single
   most visible accessibility signal a reviewer sees.
8. **Fluid type and space via a derived `clamp()` scale (Utopia), with the WCAG
   1.4.4 check applied.** Replaces the whole breakpoint table. Verify each step can
   still reach 200% at zoom.
9. **Container queries plus `cqi` units for anything reusable.** 94.87% support.
   Makes components correct wherever dropped and is the honest version of
   "responsive". (Shadeed.)
10. **Every Layout primitives (Stack, Sidebar, Switcher, Cluster, Cover, Reel) as
    the layout vocabulary.** Universal support, zero media queries, and it forces
    content-driven layout rather than a 3-column default. (Pickering, Bell.)
11. **A designed `prefers-reduced-motion` branch per component, not a global nuke,
    plus a JS `matchMedia` check for library-driven motion.**
12. **Asymmetric grid tracks plus one deliberate grid-break per page.**
    `minmax(0, 7fr) minmax(0, 5fr)` and one full-bleed element. Kills T22-T23.
13. **Content-driven section rhythm** - vary `padding-block` by section weight.
    Kills T26.
14. **Origin-aware popover/menu scaling** from the trigger via `transform-origin`,
    plus `@starting-style` (91.92%) for entry without JS. (Kowalski, Rauno.)
15. **Native `popover` (92.51%) and `<dialog>`** instead of a positioning library -
    top layer, light dismiss, focus restore, all free.
16. **`color-mix()` borders derived from the surface** (93.91%) so borders survive a
    theme flip.
17. **`text-wrap: balance` on headings, `pretty` on body** (92.73% / 83.79%, both
    graceful) - two lines, removes every heading orphan.
18. **`subgrid` for card internals** (93.48%) instead of forcing equal card heights.
    Kills T27 honestly.
19. **`text-box: trim-both cap alphabetic`** (86.46%) to fix optical vertical
    alignment at the source instead of nudging padding.
20. **A grain/noise overlay at 2-4% opacity.** One pseudo-element; instantly
    non-generic; free.
21. **Scroll-driven animations via `animation-timeline: view()`** (87.22%) behind
    `@supports`, used on one or two elements that earn it - not on every section.
22. **`light-dark()`** (89.86%) with a `prefers-color-scheme` fallback, so both
    themes are authored rather than one being an afterthought.
23. **Headless-primitive split** (cmdk-style): behavior/ARIA/keys in one layer,
    zero visual opinions, all styling yours. Prevents T43. (Coursey.)
24. **`field-sizing: content`** (85.81%) and **`interpolate-size: allow-keywords`**
    (72.21%, Chromium-only - guard it) for content-sized inputs and
    animate-to-`auto` disclosures.
25. **Anchor positioning** - the highest-ceiling, lowest-safety item on this list.
    85.93% and mostly *partial*. Only behind `@supports (anchor-name: --a)` with a
    real fallback.
