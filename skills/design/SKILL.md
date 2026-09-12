---
name: design
description: Runs the design pipeline end to end - detect the stack, ground the direction in real shipped UI, lock it as portable tokens, source real components, assemble, add imagery and motion, then audit before presenting. Use whenever the user asks to design, redesign, restyle, build a page, build a UI surface, or polish an interface, even if they do not say the word "design".
argument-hint: "[what to design] [where]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Skill
  - Agent
  - TodoWrite
  - WebFetch
  - AskUserQuestion
hooks:
  Stop:
    - hooks:
        - type: command
          command: "bash $HOME/.claude/skills/design/scripts/gate.sh"
          statusMessage: "Checking the design gate..."
---

# Design

Run the pipeline on `$ARGUMENTS`. If it is empty, ask what to design and where, in one
question, then proceed.

Whatever the user supplies - a reference image, a URL, brand colors, fonts, a Figma link,
existing CSS - overrides the corresponding step and is locked as given. Whatever they
leave out, you decide and state.

## Step 0 - open the ledger. Do this first, before any conversation about style.

```bash
bash ~/.claude/skills/design/scripts/ledger.sh init <target-dir>
```

Then create one todo per ledger row, worded identically. The ledger is the spine: a Stop
hook reads it and will refuse to let you finish while a row is open. Close each row as
you go:

```bash
bash ~/.claude/skills/design/scripts/ledger.sh set <step> RAN "<evidence path or token>"
bash ~/.claude/skills/design/scripts/ledger.sh set <step> SKIPPED "<reason>"
```

Skip reasons come from a closed set and the script rejects anything else. There is no
prose excuse. `detect`, `direction`, `tokens`, `assemble` and `gate` have an empty set -
they cannot be skipped for any reason.

| step | may be skipped only as |
|---|---|
| `detect` | never |
| `reference` | `user-supplied-reference`, `no-source-available` |
| `direction` | never |
| `tokens` | never |
| `source` | `no-component-need`, `hand-roll-justified`, `magic-mcp-unavailable` |
| `assemble` | never |
| `assets` | `no-imagery-needed`, `assets-supplied` |
| `motion` | `no-motion-warranted`, `reduced-motion-only` |
| `gate` | never |
| `conversion` | `not-marketing-surface` |

## 1. detect - what stack is this actually

Run the cascade in `references/stacks.md` section 1. Print exactly this block and do not
proceed until every line is filled:

```
framework:   <SvelteKit | Django | Astro(no islands) | none | ...>
styling:     <Tailwind v4 | Tailwind v3 | CSS Modules | Panda | plain CSS | ...>
tokens live: <path to the CSS entry, theme.json, or "none yet">
components:  <existing lib or "none"> at <path>
behaviour:   <Alpine | htmx | Stimulus | Livewire | framework runtime | none>
```

If two signals disagree - a `tailwind.config.js` exists but the CSS entry says
`@import "tailwindcss"` - the CSS entry wins and you say so in one line.

Evidence for the ledger: the filled block.

## 2. reference - never design a screen type from memory

Look at real shipped UI before choosing anything. Full step and the fallback ladder are in
`references/reference-lock.md`. Short form: try Mobbin MCP, then Refero MCP, then a
user-supplied reference, then the Chrome MCP against Curated / Lapa Ninja / ScreensDesign,
then design-system docs. Announce in one line and act - do not ask permission.

Collect 6-10 real references, look at every image, then write
`.design/reference-lock.md`: sources with URLs, ONE primary whose signature traits you
keep sharp, at most 2 borrowed details each attributed, a decision ledger, and one line on
the direction you rejected. Do not average several references into mush.

If you cannot cite 3 real references with URLs, say so plainly and ask the user for one.
Do not proceed on vibes and do not pretend the research happened.

Never point the Chrome MCP at mobbin.com or refero.design - both prohibit it. Do not cache
their screenshots to disk; write the lock, not a copy of the library.

Evidence: `.design/reference-lock.md`.

## 3. direction - lock style, palette, type, and the register lens

Precedence, highest first:

1. A locked `brand-system.html` in the project - binding. Read its `:root` custom
   properties and `#brand-tokens` JSON. Do not re-propose.
2. A reference the user pointed at - run `design-dna` to extract it into a quantified
   profile. That is the direction.
3. A saved project/client direction - reuse it.
4. Nothing - `ui-ux-pro-max` for style + palette + font pairing, propose 2 and wait. If
   this is a client build, stop and run `/brand-system` instead.

Then layer the register lens over every visual decision from here on:
premium/calm -> `high-end-visual-design`; editorial/minimal -> `minimalist-ui`;
raw/bold -> `industrial-brutalist-ui`.

**A register skill supplies composition, attitude and restraint. It does NOT supply the
typeface or the palette.** Those come from the search below, every time. Verified 2026-09-09. These skills carry specific recommendations that are
wrong here and you must ignore them - named by item, not by line number, because both files
carry a prepended override block and any line citation goes stale the next time it grows:

| Skill | Ignore | Why |
|---|---|---|
| `industrial-brutalist-ui` | Inter, Roboto Flex as "optimal" | popularity 5 and 2 - the two most-used faces on the web |
| `industrial-brutalist-ui` | Neue Haas Grotesk, Monument Extended | commercial, not self-hostable |
| `industrial-brutalist-ui` | Playfair Display, Times New Roman | Playfair is popularity 25 and a named tell |
| `industrial-brutalist-ui` | `#E61919` / `#FF2A2A` Aviation Red | one hardcoded palette for every brutalist project |
| `minimalist-ui` | SF Pro Display, Helvetica Neue | Apple-licensed, illegal to self-host |
| `minimalist-ui` | the pale-pastel hex list | one hardcoded palette |
| `minimalist-ui` | `picsum.photos` placeholders | random stock imagery headed for production |

Take their layout logic, spacing discipline and motion character. Take nothing with a hex
code or a font name in it.

**Never pick a typeface from a list, and never pick a hue from a catalogue.** Both are
searches with a project-specific input, and both have a tool:

```bash
bash ~/.claude/skills/design/scripts/fontdata.sh          # once, then monthly
python3 ~/.claude/skills/design/scripts/fontsearch.py \
  --adjectives <brief adjectives> --anti <anti-adjective> \
  --category Display --seed <client-slug> --top 8
python3 ~/.claude/skills/design/scripts/pair.py <chosen display face>
```

`--seed <client-slug>` is not optional. It samples the qualifying band instead of always
taking the top of the ranking, which is what made every project come out the same. The
default `--min-pop 300` floor excludes Inter, Roboto, Poppins, Montserrat, Open Sans, Lato
and Playfair by construction - they all sit in the top 30 by popularity - while still
leaving 189 quality-72+ Display families. If the search returns nothing, loosen one
constraint and say which. Never fall back to a default face.

For the hue: map 8-12 competitors into OKLCH, bin hue into 24 buckets, then commit to
OCCUPY or VACATE and say which. Subtract the semantic anchors (12-42 danger, 60-90 warning,
135-165 success) before choosing. Full procedure in `BRAND-SYSTEM-GUIDE.md` sec. 5.3.

Before locking, read `references/craft.md` -> "The craft moves worth encoding" and commit
to the first six. They are near-free and they are what separates this from a generated
page. Evidence: the register skill name, the chosen faces with the seed used, and the hue
angle with its one-sentence reason.

## 4. tokens - the direction becomes portable here

The output of step 3 is **not** Tailwind classes. Write `tokens.css` with a full `:root`
block covering the nine groups in `references/stacks.md` section 3: color (OKLCH with hex
fallback), font, type, space, radius, shadow, duration, ease, plus the
`prefers-reduced-motion` duration override. Wire it into the stack's global stylesheet.

**Generate the colour ramp, do not hand-pick it:**

```bash
node ~/.claude/skills/design/scripts/build-ramp.mjs --hue <deg> --sat 0.9 >> tokens.css
node ~/.claude/skills/design/scripts/build-ramp.mjs --check    # 384/384 contrast targets
```

It expresses chroma as a fraction of maximum in-gamut chroma at each lightness, so the arc
comes off the gamut boundary automatically, is correct at any hue with no retuning, and
cannot clip. Contrast pairs are solved for rather than checked afterwards - text steps are
computed against step 2, and step 9 is the max-chroma survivor that passes in both
directions. If you hand-write a ramp instead, you are guessing at what this proves.

**If a signed `brand-system.html` exists, this step is transcription, not derivation.**
Copy its `:root` and `#brand-tokens` values exactly. Then verify the board itself conforms:
`uv run --no-project --with jsonschema python3 ~/projects/freelance/website-build-templates/scripts/check-brand-system.py <path>`

Emit a bridge only if step 1 says one is needed - Tailwind v4 `@theme inline`, Tailwind v3
`theme.extend` pointing at `var()`, Angular Material `--mat-sys-*`, WordPress `theme.json`
presets, Panda/vanilla-extract/StyleX token config.

Write `tokens.json` (DTCG 2025.10) only when there are two or more emit targets or a
native platform is in scope. One stack, one target: hand-written CSS is the right rung.

Evidence: path to `tokens.css`.

## 5. source - components, per component, down the ladder

Native element -> existing repo component -> installed library -> registry copy ->
generate -> hand-roll. Take the highest rung that works. Log which rung each component
came from; if more than about a third were hand-rolled, stop and say why.

**The shadcn MCP is installed user-scoped and is available in every project** - no per-project
`mcp init`, no API key, no account. It resolves `components.json` from the working directory,
so it targets whatever repo you are in, and it reaches any shadcn-compatible registry
including third-party ones. It is not React-only.

Use it as the primary component source. If its tools are missing, the session predates the
install - say so and use `npx shadcn add` directly rather than hand-rolling:

```bash
npx shadcn@latest add <name|url>
```

(A project that wants the server pinned in-repo can still run
`pnpm dlx shadcn@latest mcp init --client claude`, which writes `.mcp.json`. That is optional
and only useful for sharing the setup with teammates.)

Per-stack sources and the registry commands are the matrix in `references/stacks.md`.

The 21st.dev `magic` MCP is optional, React+Tailwind only, and its key is currently
rejected. It is an inspiration source, not a component source - shadcn's MCP does that job
better, free. If magic is not connected, print one line and continue; never block on it.
Close the row as `SKIPPED magic-mcp-unavailable` only if it was the sole source you needed.

## 6. assemble - build it

`frontend-design` + `impeccable`. Every color, duration and easing in component source
comes from a token. No literal hex, no literal `300ms`, no `ease-in-out` outside
`tokens.css`. The gate greps for exactly this.

**Charts, graphs, dashboards, stat tiles:** read
`~/.claude/skills/ui-ux-pro-max/data/charts.csv` before the first line of chart code. 25 data
shapes mapped to the right chart type, with library, colour and accessibility guidance per
row. If the bundled `dataviz` skill is available in your
session, load it too - it covers chart honesty (picking the form the data's shape calls for,
encodings that do not exaggerate, titling the finding rather than the axes) while
`charts.csv` covers the type-to-library mapping. A chart is
never an image: code it, and give it the same token treatment as everything else.

## 7. assets - imagery, icons, shapes

Invoke `/assets`. It reads `.design/direction.json` and writes
`.design/assets-manifest.json`. Its triage decides what gets generated, fetched, or
coded - most of it should be coded or fetched. Skip only when the surface genuinely needs
no imagery, or the user supplied it.

## 8. motion - only where it earns its place, and built by the motion skills

**Invoke the skill, do not freehand the animation.** The first real run shipped a
scroll-driven isotipo reveal while invoking zero motion skills - the routing below existed
only as prose and nothing checked it. The ledger now refuses `set motion RAN` unless the
evidence names the skill that built it as `skill=<name>`:

```bash
bash ~/.claude/skills/design/scripts/ledger.sh set motion RAN "skill=animate; one scroll-driven isotipo reveal, reduced-motion fallback"
```

Pick by kind. Durations and easings come from `--duration-*` and `--ease-*`, never literals:

- General, or unsure -> `animate` (Emil Kowalski's own skill: whether to animate at all, purpose, tool, properties, curve, interruption, exit).
- Plain CSS transitions - dropdown, modal, accordion, tabs, skeleton, icon swap -> `transitions-dev`; tune existing motion against its token scale with `transitions-polish`.
- Scroll-driven, pinned, timeline-choreographed -> `gsap-scrolltrigger` / `gsap-timeline` (`gsap-react` in React). Native `animation-timeline: view()` is fine too - still route the decision through `animate`.
- Gesture, spring, drag/swipe/sheet, anything that must feel physical and interruptible -> `apple-design`.
- Don't know what the effect is called -> `animation-vocabulary`, then one of the above.
- Motion craft reference while building -> `design-motion-principles` (Create mode) or `emil-design-eng`.
- 3D / WebGL -> the `threejs-*` set.

Legal skips stay `no-motion-warranted` and `reduced-motion-only`. The audit half lives in
`design-gate` lens 5, which reads `review-animations`' standards directly - that skill is
user-only (`disable-model-invocation: true`) and cannot be called from here.

## 9. gate - audit before presenting. This one has no escape.

Invoke `design-gate`. It runs forked and blind - it reads the built files, not the
reasoning that produced them, which is the point: an auditor that remembers arguing for a
choice cannot grade it honestly. It writes `.design/audit-report.md`.

Then fix what it found and re-run it. The Stop hook checks that the report exists, is
non-empty, and that **no file under the target is newer than the report** - so editing
after the audit re-opens the gate. That is deliberate.

| the thought | the answer |
|---|---|
| "it already looks good" | Looking good is not an audit result. |
| "I'll note the issues instead" | A note is not a report. |
| "the user is waiting" | The audit is faster than a rebuild. |
| "I'll audit after presenting" | Presenting is the claim. The claim needs evidence first. |

## 10. conversion - marketing surfaces only

Landing, pricing, signup, or paywall: run `cro`, plus `pricing` / `signup` / `paywalls` /
`popups` for the surface and `marketing-psychology` for the framing. Internal tools and
app UI: `SKIPPED not-marketing-surface`.

## 11. close - print the table, do not write it

```bash
bash ~/.claude/skills/design/scripts/ledger.sh show
```

That table is generated from the ledger, so it cannot disagree with what actually ran.
Print it as the last thing you say. If a row reads SKIPPED, say the reason out loud rather
than letting the user find it in the table.

## References

- `references/stacks.md` - stack detection, the component matrix for every stack, the nine token groups with real syntax
- `references/reference-lock.md` - Mobbin/Refero MCPs, the gallery fallback ladder, ToS boundaries
- `references/craft.md` - the 36-item AI-tell checklist, 25 ranked craft moves, modern responsive CSS with verified support figures
- `references/_audit-2026-09-09.md` - why the previous version of this pipeline failed
- `references/_architecture-2026-09-09.md` - why the ledger and the hook are built this way

Verify the ledger and hook still work after editing either script:
`bash ~/.claude/skills/design/scripts/test-ledger.sh`
