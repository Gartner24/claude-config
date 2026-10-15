---
name: brand-system
description: Produces a client's brand system as a self-contained, contract-validated HTML brand board - the canonical binding source the build follows. Positioning, register, typography, colour, logo lockups, imagery, motion, voice, plus a machine-readable tokens block. Gets client sign-off. Use whenever asked to create, formalize, redo or extend a brand, a brand system, brand guidelines, a visual identity, or a style guide. Run before /new-site and before /design on a client build.
argument-hint: "[client name] [any existing material]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Skill
  - TodoWrite
  - WebFetch
  - AskUserQuestion
hooks:
  Stop:
    - hooks:
        - type: command
          command: "bash $HOME/.claude/skills/design/scripts/gate.sh"
          statusMessage: "Checking the brand system gate..."
---

# Brand system

Build `brand-system.html` for the client in `$ARGUMENTS`. It is **both** the sign-off board a
human reads **and** the machine source the build imports. One file, both jobs.

The craft lives in `~/projects/freelance/website-build-templates/guides/BRAND-SYSTEM-GUIDE.md`.
Read it. `ui-ux-pro-max` is a raw-options database you may pull candidates from, never the
decision process.

## Step 0 - open the ledger, before any conversation about style

```bash
bash ~/.claude/skills/design/scripts/ledger.sh init <client-repo> --pipeline brand
```

Then one todo per row, worded identically. A Stop hook reads this ledger and **will not let
you finish while a row is open**. Close rows as you go:

```bash
bash ~/.claude/skills/design/scripts/ledger.sh set <step> RAN "<evidence>"
bash ~/.claude/skills/design/scripts/ledger.sh set <step> SKIPPED "<reason>"
```

| step | may be skipped only as |
|---|---|
| `brief` | never |
| `reference` | `no-client-material` |
| `direction` | never |
| `type` | never |
| `color` | never |
| `logo` | `logo-supplied` |
| `imagery` | `no-imagery-scope` |
| `surfaces` | never |
| `audit` | never |
| `emit` | never |
| `signoff` | `internal-project` |

## 1. brief - four things, written down

Positioning in one sentence (what it is and who it beats), audience, 3-5 personality
adjectives, one primary emotion. Guide sec. 3.2. **Force the adjectives to DISCRIMINATE** -
"premium, modern, clean, trustworthy" describes half the market and translates to nothing;
"defiant, working-class, nocturnal" translates directly. Ask only what would change the
result. Evidence: the four lines.

## 2. reference - measure what the client already points at

If they gave you logos, sites they like, photos or existing guidelines, run **`design-dna`**
on them. It is the only measure-and-verify path in this toolchain and it returns a quantified
profile rather than an impression. Evidence: the profile path. Nothing supplied at all is the
one legal skip.

**Then widen once, to the register - and NOT through `/design`'s reference ladder.** Mobbin
and Refero index app screens and web UI. A brand system is a wordmark, a palette, a voice and
a type system, and those are not visible in a screenshot of somebody's settings page. Reaching
for that ladder here is a category error.

Use **guide sec. 9** instead: a named-brand cheat-sheet per register - Nike and Supreme for
bold/street, Aime Leon Dore and Fear of God for premium/editorial, Stripe and Linear for
technical - with the signature move distilled for each. Study two or three of the named
brands directly, at their own sites, and take the MOVE rather than the look. That is
reference at the identity layer, which is the layer this skill works at.

`/design` uses the Mobbin/Refero ladder later, for the surfaces, where it is the right tool.

## 3. direction - commit, do not hedge

Pick ONE register (guide sec. 3.1). Keep exactly one adjective as the **tension axis**
("premium but raw"), and name one **anti-adjective** it must never look like. State it as
"we are X, specifically NOT Y". Hedging averages to generic, and the average is where generic
lives. Evidence: the register plus the tension axis plus the anti-adjective.

## 4. type - a search, unless the client already decided

**A client-mandated typeface outranks the search, and is not a failure of it.** If the brief,
the existing identity, a licence they already hold, or a parent-brand guideline fixes the
face, that IS the answer - record it and move on. Do not "improve" it, do not run the search
to second-guess it, and never quietly substitute a lookalike because the mandated face is
popular or not on Google Fonts. A brand the client cannot reproduce is worthless to them.

Record which of these applies, because the next session must not re-decide it:

| Provenance | What to record |
|---|---|
| `client-mandated` | the face, who mandated it, and the licence they hold (foundry, seats, web/desktop) |
| `inherited` | the existing asset it was measured off, via `design-dna` |
| `searched` | the seed, the adjectives, and every constraint loosened |

If the mandated face is commercial, say so in the board and name the licence - a
self-hosting instruction the client has no right to follow is worse than no instruction.
If it cannot be self-hosted at all, say that too rather than silently swapping it.

**Only when nothing is fixed do you search.** Then: search the corpus, never pick from a list.

```bash
bash ~/.claude/skills/design/scripts/fontdata.sh
python3 ~/.claude/skills/design/scripts/fontsearch.py \
  --adjectives <brief adjectives> --anti <anti-adjective> \
  --category Display --seed <client-slug> --top 8
python3 ~/.claude/skills/design/scripts/pair.py "<chosen display face>"
```

`--seed <client-slug>` is mandatory - it is what stops two clients getting the same face.
The default `--min-pop 300` floor excludes Inter, Roboto, Poppins, Montserrat, Open Sans,
Lato and Playfair by construction; they are all top-30 by popularity. Guide sec. 4.3.

A character display face plus a neutral body, each **with a stated reason**. If a strange
face fits the brief and clears quality 72, use it - that is the point. Stay boring in the
body. If the search returns nothing, loosen one constraint and say which; never fall back to
a default face. Evidence: both faces, the seed, and the reason.

## 5. color - a hue with a reason, then a generated ramp

Map 8-12 competitors into OKLCH, bin hue into 24 buckets, commit to **OCCUPY or VACATE** and
say which. Subtract the semantic anchors (12-42 danger, 60-90 warning, 135-165 success)
before choosing. Guide sec. 5.3.

**Where the competitor set comes from** - this step needs real colours from real rivals, and
you must not invent them:

1. A research file already in the project (`RESEARCH.md`, a brief, an audit). Grep it for hex
   values first - the work may already be done.
2. Otherwise ask the client for 8-12 named competitors, or name them yourself from the
   positioning and say you did.
3. Get each one's actual brand colour by visiting their site with the **Chrome MCP** and
   sampling the rendered page - their nav, their primary button, their headline. Not a gallery
   and not Mobbin: those show you good design, and here you need *these specific rivals*.
4. Record every source with its URL in `.design/color.md`, so the arc argument can be checked.

If you cannot assemble at least 8, say so plainly and state that the OCCUPY/VACATE call is
made on a thin sample. Do not present a hue-arc argument built on colours you assumed.

```bash
node ~/.claude/skills/design/scripts/build-ramp.mjs --hue <deg> --sat <0-1>
```

Brand-tinted neutrals as the workhorse plus ONE owned signal colour, 60-30-10. Every token
group defined. The action colour must pass AA **as a fill and as text on the page**.
Evidence: the hue angle, the strategy, and the one-sentence reason.

## 6. logo - designed, not typed

A wordmark is drawn, not a font set at defaults. Guide sec. 6. Horizontal and stacked
lockups, both modes, clear-space rule, and a reduction test down to favicon scale. Generate
source imagery with `/assets`; vectorize with `vtracer`. Skip only when the client supplied a
finished mark.

**[P0] Every shipped lockup carries outlines, not live text.** An SVG with `<text
font-family="X">` renders in a fallback on any machine without X - a printer, a sign-maker, a
client's Word document - and the letterforms you argued for are gone. Keep the live-text file
alongside as `<name>-editable.svg` and ship the outlined one.

Convert with the real font at the size it is set at, not at the font's default. A variable
face must be instantiated at the rendered optical size first: Bodoni Moda defaults to
`opsz 11`, so outlining a 58px wordmark without pinning `opsz 58` freezes small-text
hairlines at display size, which for a Didone destroys the contrast that chose it.

```bash
inkscape --actions="select-all;object-to-path;export-filename:out.svg;export-plain-svg;export-do" in.svg
npx -y svgo --multipass out.svg
```

Then prove it: render the outlined file with the font uninstalled and diff it against the
font-rendered original. Zero differing pixels, or it is not outlined.

## 7. imagery and motion - one treatment, one signature moment

Guide sec. 6-7. One imagery treatment stated and demonstrated, one signature motion moment.
Use `/assets` - it will refuse to generate a portrait and will code a texture rather than
fetch one. Never `picsum.photos`.

## 8. surfaces - prove it on real applied surfaces

**2-3 real applied surfaces, never a swatch sheet.** A palette looks fine everywhere; a
pricing table and a nav bar are where a direction actually fails. This is the step that
catches a system that only works as squares.

## 9. audit - the anti-generic catalog

Walk the applied surfaces against the **32-item anti-generic catalog at guide sec. 8**, then
the checklist at **guide sec. 11**. (Those section numbers were wrong in the previous version
of this command - it pointed at sec. 7 and sec. 10, which are Imagery and Output contract, so
the gate was reading the wrong pages.) Fix every P0 and every type, layout and logo tell.
Zero unaddressed tells is the gate to emit.

Also cross-check `references/craft.md` in the `design` skill - the 36-item AI-tell checklist
overlaps and is phrased as pass/fail.

## 10. emit - and the contract is machine-checked

Write `brand-system.html`: the visual board (palette, specimens, scale, spacing, lockups,
components, voice, do/don't) **and** the mandatory `:root` custom-property block plus the
`<script type="application/json" id="brand-tokens">` block. Self-host the fonts - no
`fonts.googleapis.com` link.

```bash
uv run --no-project --with jsonschema python3 \
  ~/projects/freelance/website-build-templates/scripts/check-brand-system.py brand-system.html
```

**This must exit 0 before the row closes, and the Stop hook re-runs it.** It pins the section
set and order, both token layers, the seven required groups, the clamp-spacing rule, the
register enum, both contrast directions, and it rejects Inter/Poppins/Montserrat/Playfair as
a primary face. Measured reality: all three existing client boards fail it (27, 35 and 73
violations), and they are 258, 1431 and 482 lines from the same command. That divergence is
what this gate exists to end.

## 11. signoff - the build is blocked until it exists

Show the client the board. Get explicit sign-off and record it as a visible status line
(`signed off YYYY-MM-DD`). `/new-site` and `/design` read this file's tokens as binding.
Skip only for an internal project with no client.

Close with `ledger.sh show` - generated from the ledger, so it cannot disagree with what ran.

## Handoff to `/design`

`/brand-system` owns **identity**. `/design` owns **surfaces**. A signed `brand-system.html`
outranks every direction source in `/design`, which transcribes its `:root` rather than
re-deriving it. Never let `/design` re-decide a colour or a face this file already fixed.
