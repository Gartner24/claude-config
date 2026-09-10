---
name: assets
description: Sources, generates, codes and edits imagery for a design - photos, icons, illustrations, blobs, patterns, grain, logos, background removal and the optimization ladder. Triages each asset to the right source instead of generating everything. Use when asked for images, icons, illustrations, a mascot, a hero visual, product shots, a logo, an SVG, a background, or to cut out or clean up an image.
argument-hint: "[what imagery] [for which surface]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - AskUserQuestion
---

# Assets

Runs standalone, or as step 7 of `/design`. When `.design/direction.json` or
`.design/tokens.css` exists, every asset is bound to those tokens. Write
`.design/assets-manifest.json` when running inside a design run.

## Triage first. Most assets should never touch an image model.

Classify every asset before doing anything. This table is the anti-slop policy - five of
these ten classes are made worse by a generator.

| Asset | Source | Why |
|---|---|---|
| Icon | **Iconify API**, one prefix for the whole project | Free, unauthenticated, `currentColor` preserved. Mixing sets is a visible tell. |
| Abstract background, mesh, gradient | **Code it** | No native CSS mesh exists in 2026; stacked `radial-gradient(at X% Y%)` in OKLCH plus grain beats any generated blob. |
| Grain, noise, texture | **Code it** - `feTurbulence` at 6-20% | ~300 bytes, highest visual return per byte on the whole list. Never fetch a grain PNG. |
| Blob, wave, divider, angled section | **Code it** - Catmull-Rom, `clip-path`, `mask-image` | Seedable, themeable, tiny, untraceable to a library. |
| Dot grid, hatch, stripes | **Code it** - repeating gradients + `color-mix` | Zero bytes, auto dark-mode, scales with the layout. |
| OG / social card | **satori / @vercel/og** | Text rendered as text. A generated card garbles its own copy. |
| UI mockup / product screenshot | **Screenshot the real thing** | A generated UI is uncanny and shows a product you do not ship. |
| Chart, graph, stat tile | **Code it** in the charting layer | Never an image. |
| Photograph of a real place, object or person | **Openverse first**, then Wikimedia Commons, then Unsplash | Free, licensed, and both first corpora were shot to document rather than to sell - which is exactly what stops them reading as stock. |
| Photograph of a generic business concept | **Do not fetch one. Replace it.** | Every free source's "business" corpus is the overused set. This is where the stock tell lives. Use a product screenshot, typography, or a coded background. |
| Spot illustration | Code it, or omit it. If truly needed: one artist, one pack, recoloured to tokens | **Never unDraw or Humaaans.** Corporate Memphis is the strongest template tell there is. |
| Hero photograph, conceptual or atmospheric | **Generate** - see below | The one class where a model genuinely wins. |
| Product packshot | **Edit mode over a real photo.** Never text-to-image | |
| Portrait, avatar, testimonial face | **Do not generate. Ask for a real photograph.** | Faces are where the tells live, and a fabricated person on a real company's site is a trust problem, not a craft one. |
| Logo / brand mark | Generate for exploration only; the final mark is drawn | |

If an asset depicts a real person, a real product the user sells, or a real place, stop
and ask for a real photograph. Do not generate it.

## Fetching photographs

Openverse needs no key and works right now:

```bash
curl -s -A "your-app/1.0 (contact@example.com)" \
  "https://api.openverse.org/v1/images/?q=<query>&license_type=commercial,modification&page_size=20" \
  | jq '.results[] | {title,url,license,attribution}'
```

`license_type=commercial,modification`, both terms - **not `commercial` alone**. Alone it
returns `by-nd` results, and a pipeline that crops, duotones or composites an image is
making a derivative work. Verified 2026-09-09: the pair filters ND out, `commercial` alone
does not.

Then apply the selection rules - they are executable, not taste:

- Search the physical scene, not the concept. "welder in a workshop", never "innovation".
- Reject the pose vocabulary: arms crossed, handshake, thumbs up, "isolated on white".
- Score the copy region before committing to a text overlay - under 12 is safe:
  `magick in.jpg -crop 800x400+100+100 +repage -format "%[fx:standard_deviation*100]" info:`
- Prove it survives every ratio the layout needs: `magick in.jpg -resize 1600x1600^ -extent 21:9 test.jpg`
- Enforce set consistency: measure mean H/S/L per candidate, duotone the outliers to tokens.
- Overuse: no free API exists. Unsplash's `downloads` field is the free proxy - over 100k
  means it is already on a thousand sites. Deep-page and use 4+ word queries.

Attribution and hotlink rules per source are in `references/source-and-shapes.md` section 1.
Unsplash in particular requires hotlinking `photo.urls` and firing `links.download_location`.

## Generating imagery

**Requires a Gemini key on a billing-enabled project.** Image generation is not on the
Gemini API free tier and a consumer Gemini subscription does not grant API quota.

Read the key from the keyring, never from a hardcoded string or a committed file:

```bash
GEMINI_API_KEY="$(bash ~/.claude/skills/assets/scripts/gemini-key.sh get)" || exit 1
```

It falls back to `$GEMINI_API_KEY` if the keyring is unavailable, and exits non-zero with
an instruction if there is no key at all - so a missing key fails loudly instead of
producing nothing. `gemini-key.sh test` proves both that the key is accepted and that an
image model is actually visible to it (an empty image-model list means the project has no
billing, which is the failure that looks like a working key).

**No key? Do not skip the step - hand over the prompt.** The user has a Gemini
subscription and can run it by hand. Print, for each asset:

1. A fenced, **self-contained paste block** - no parameters the chat UI does not have, no
   placeholders left unfilled, the style contract already inlined. One block per image.
2. Where it goes (`assets/photos/hero.png`) and at what size.
3. What to check before accepting it - the audit list at the bottom of this file.
4. The order to run them: the hero FIRST, then attach that PNG to every following prompt so
   the set matches. Say this explicitly; it is the whole trick and it is not obvious.

Then record them in `.design/assets-manifest.json` as `pending-manual` so the design ledger
can still close the `assets` row with real evidence. Never mark imagery done because a
prompt was written.

Templates for all ten asset classes, in both API and paste form, are in
`references/prompting.md` -> "Paste-ready templates".

Default `gemini-3.1-flash-image` ($0.067/1K); `gemini-3-pro-image` for a hero; FLUX.2 [pro]
via `api.bfl.ai` ($0.03) as the non-Google lane. A full site set runs about $3.

Method, in full in `references/generate.md`:

0. **There is no universal prompt format - match the model.** Google is explicit: "Describe
   the scene, don't just list keywords... A narrative, descriptive paragraph will almost
   always produce a better, more coherent image than a simple list of disconnected words."
   Gemini 3 image models are *thinking* models, so long ordered prose pays. OpenAI's cookbook
   wants short labelled segments (background/scene -> subject -> key details -> constraints).
   FLUX.2 wants "Subject + Action + Style + Context" and warns word order matters. Ideogram
   caps at ~150-160 words and bans hex codes. Keyword soup is a Midjourney habit and it is
   actively wrong on the model we default to.
1. Write a **style contract** - one paragraph covering medium, lighting, palette in the
   project's real tokens, lens character, mood. Generate ONE reference image against it and
   get it approved before the other ten. Then condition every later generation on that
   image, not on repeating the prompt.
2. Each image must illustrate a specific claim on the page. If you cannot name the sentence
   it illustrates, the image should not exist.
3. One or two imperfection nouns. Never three or more. OpenAI's cookbook is the source:
   "pores, wrinkles, fabric wear, imperfections", and avoid "words that imply studio polish
   or staging".
4. Skip `masterpiece`, `8k`, `hyperrealistic`, `perfect lighting`, `award-winning`,
   `ultra-detailed`, `professional photograph`. The honest reason: **no documented benefit**,
   and on order-weighted models they burn front-of-prompt attention. The stronger claim that
   they actively degrade output is blog-level only - do not repeat it as fact. Camera and
   composition terms steer realism more reliably than any of them.
5. Gemini, FLUX.2 and OpenAI have **no negative-prompt field** - a negative stack is inert
   there. Use Google's documented replacement, semantic negative prompts: "Instead of saying
   'no cars,' describe the desired scene positively." Ideogram does expose one; use it there.
6. **Seed locking is a myth for style.** Midjourney's own docs: seeds "can't capture or
   bookmark a specific style, character, or appearance across different prompts", and Gemini
   and OpenAI expose no seed at all. What actually carries a look across a set, in order:
   reference-image conditioning (Gemini takes up to 14 refs, typed into object/character/style
   buckets), a persistent style handle (Recraft `style_id`), then a verbatim repeated style
   block.
7. Three attempts per final. If attempt 3 is wrong the prompt is wrong, not the seed -
   rewrite the scene, do not reroll.
8. Post-process photographic rasters only, never illustrations or anything with text:
   `magick in.png -attenuate 0.4 +noise Gaussian -modulate 100,92,100 -quality 88 out.jpg`
9. Save the receipts next to the assets: style contract, every final prompt, model ID,
   reference-image path, post-processing command. Regenerating one image in six months
   without these means redoing the whole set.

## Editing - background removal

The good version, not the sloppy one. `-vm` (ViTMatte) re-estimates alpha and
decontaminates internally, recovering hair and fur that a plain cut chops flat. It costs
about 3 seconds more. Full runbook in `references/edit.md`.

```bash
bash ~/.claude/skills/assets/scripts/bgremove.sh in.jpg cut.png [general|portrait|anime|cod|hard]
```

**Never omit `-m`.** rembg's default model is `bria-rmbg`, CC BY-NC 4.0 - one forgotten
flag turns a client deliverable into a licence problem. The script always passes it.

Then look at it on magenta at 300%, which is the step people skip and the whole game:

```bash
magick cut.png -background magenta -flatten -crop 400x300+X+Y +repage -filter point -resize 300% check.png
```

Coloured rim -> re-cut with `-vm`. Hair cut off flat -> add `-ae 20`. Grey wash across the
transparent area -> `magick cut.png -channel A -level 5%,95% +channel cut.png`.

First run downloads ~1 GB of model weights and takes about 30s; warm runs are 17-20s for a
2000px image on this machine.

## Shipping any asset

- SVG: `npx -y svgo --multipass`, check the `viewBox` (vtracer emits none), convert fills to
  `currentColor` so it survives a theme flip.
- Raster: resize to 2x rendered width, emit AVIF + WebP + JPEG, real `sizes`, a ThumbHash or
  24px LQIP placeholder, explicit `width`/`height` to prevent CLS.
- Budget: hero under 200KB, section images under 120KB. Never ship an image wider than 2x
  its largest rendered CSS width.

## Before handing back

1. Does each image illustrate a named sentence on its page?
2. Does the set look like one photographer or one illustrator, or like ten prompts?
3. Any baked-in text - is every character correct?
4. Hands, screens, signage, reflections - zoom in.
5. Is it the diverse-team-in-a-glass-office, the glowing-abstract-network, or the
   floating-glass-dashboard? Then it is slop regardless of render quality. Kill it.
6. Contrast on any text over an image, in both themes.
7. Total page image weight inside budget?

## References

- `references/generate.md` - model landscape with verified IDs and prices, per-asset routing, the anti-slop prompt method, CLI plumbing
- `references/source-and-shapes.md` - stock APIs with licence terms, Iconify, illustration packs to avoid, and runnable code for blobs, grain, mesh, patterns, vectorizing, and the optimization ladder
- `references/edit.md` - matting model comparison with measured CPU timings, the fringe-removal craft, crops, grading, generative edit
