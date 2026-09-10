# Generating imagery - models, per-asset routing, cost, and the anti-slop method

> Research reference for the design pipeline. Compiled 2026-09-09 from primary
> sources; every tool, endpoint and browser-support figure was verified at that
> date and carries its URL inline. Items that could not be confirmed are marked
> UNVERIFIED - treat those as leads, not facts. Re-verify prices and model IDs
> before quoting them to a client.

# Research D: Image generation for a Claude Code agent that cannot draw

Target machine: Arch Linux, AMD Radeon 890M iGPU (no CUDA), Python 3.14.7 + uv, node 24.
Zero image API keys currently set. User has a Gemini (consumer) subscription.
Research date: 2026-09-09. Prices change; every number below carries its source URL.

Verification legend: a claim with an official-docs URL is verified. Anything marked
`UNVERIFIED` came only from secondary sources (vendor blogs, aggregators, press) and
should be re-checked before it is relied on for money.

---


> **VERIFIED CORRECTION 2026-09-09 - read this before copying any request below.**
> Queried live against a real key: `gemini-3.1-flash-image` and `gemini-3-pro-image` both
> report `supportedGenerationMethods: ['generateContent','countTokens','batchGenerateContent']`.
> A working REST call is:
> `POST https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`
> with `{"contents":[{"parts":[{"text":"..."}]}]}` and an `x-goog-api-key` header. The image
> comes back as base64 in `candidates[0].content.parts[].inlineData.data`.
> Where this file says `/v1beta/interactions`, treat that as the newer SDK surface and
> UNVERIFIED against the REST API - `generateContent` is what was actually confirmed working.


## 0. The one thing to internalise first

For a website asset set, image *generation* is the right tool for roughly half the
asset classes and the wrong tool for the other half. Icons, OG cards, UI mockups,
abstract backgrounds, charts and final logos are all better produced by **code** or by
an **existing free library**, at zero marginal cost, with perfect text and perfect
theme-awareness. Generating them is the single largest source of the "AI slop website"
look. Section 2 marks each case explicitly.

---

## 1. Model landscape, 2026

### 1.1 Google Gemini image models (the "Nano Banana" line)

Official pricing: https://ai.google.dev/gemini-api/docs/pricing
Official guide:   https://ai.google.dev/gemini-api/docs/image-generation

| Model ID | Marketing name | Price per image (standard) | Batch | Notes |
|---|---|---|---|---|
| `gemini-3-pro-image` | Nano Banana Pro | $0.134 (1K and 2K), $0.24 (4K) | $0.067 / $0.12 | Best text rendering, Search grounding, multi-subject identity |
| `gemini-3.1-flash-image` | Nano Banana 2 | $0.045 (0.5K), $0.067 (1K), $0.101 (2K), $0.151 (4K) | ~50% | The workhorse. Up to 4K, Search grounding |
| `gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | $0.0336 (1K) | $0.0168 | 1K only, high volume |
| `gemini-2.5-flash-image` | Nano Banana (original) | $0.039 | $0.0195 | Legacy, migration recommended |

**Free tier: no.** The official pricing page shows image generation models as not
available on the free tier. The consumer Gemini app and the AI Studio browser
playground give you interactive image generation on a subscription/daily-cap basis
(Free ~20/day, AI Pro ~100/day, Ultra ~1000/day - `UNVERIFIED`, secondary sources only),
but **none of that is reachable headlessly from a CLI agent**. A billed Gemini API key
is required. This is exactly why the user's existing `nano-banana` skill has never run.

- The `gemini-cli-extensions/nanobanana` extension also wants `NANOBANANA_API_KEY` set
  to a Gemini API key, and secondary reports say quota defaults to 0 without a billing
  account attached (`UNVERIFIED`). Treat the Gemini subscription as giving you a nice
  *manual* fallback in the browser, not an API path.
- Imagen 4 was reportedly removed from the Gemini API on 2026-08-17 (`UNVERIFIED`), and
  it is indeed absent from the current official pricing page. Do not target Imagen IDs.

API shape (verified, https://ai.google.dev/gemini-api/docs/image-generation):

- `POST https://generativelanguage.googleapis.com/v1beta/interactions`
- Header `x-goog-api-key: $GEMINI_API_KEY`
- Body: `{"model": "...", "input": [{"type":"text","text":"..."}], "response_format":
  {"type":"image","mime_type":"image/jpeg","aspect_ratio":"16:9","image_size":"2K"}}`
- Image returns base64 at `interaction.output_image.data`.
- The legacy `:generateContent` endpoint "remains fully supported"
  (https://ai.google.dev/gemini-api/docs/migrate-to-interactions).

### 1.2 OpenAI image models

Official pricing: https://developers.openai.com/api/docs/pricing
Official guide:   https://developers.openai.com/api/docs/guides/image-generation
Official ref:     https://developers.openai.com/api/docs/api-reference/images/create

Current recommended IDs (verified): `gpt-image-2.5-sunburst` (editing precision) and
`gpt-image-2.5-flare` (fast everyday generation). Also live: `gpt-image-2`,
`gpt-image-1.5`, `gpt-image-1-mini`, `gpt-image-1` (being retired),
`chatgpt-image-latest`.

Token pricing per 1M (verified, official pricing page):

| Model | Text in | Image in | Image out |
|---|---|---|---|
| `gpt-image-2.5-sunburst` | $5.00 | $8.00 | $30.00 |
| `gpt-image-2.5-flare` | $5.00 | $8.00 | $30.00 |
| `gpt-image-2` | $5.00 | $8.00 | $30.00 |
| `gpt-image-1.5` | $5.00 | $8.00 | $32.00 |
| `gpt-image-1-mini` | $2.00 | $2.50 | $8.00 |
| `gpt-image-1` | $5.00 | $10.00 | $40.00 |

Batch API is 50% off. OpenAI does not publish a per-image table on that page; it points
at a calculator in the image guide. Third-party normalisation (Artificial Analysis,
https://artificialanalysis.ai/image/leaderboard/text-to-image) puts **GPT Image 2 (high)
at $0.211/image** and **GPT Image 1.5 (high) at $0.133/image**. Per-image cost for
`flare`/`sunburst` is `UNVERIFIED`; assume the same order as GPT Image 2 until measured.

No free tier. Endpoint `POST https://api.openai.com/v1/images/generations`,
`Authorization: Bearer $OPENAI_API_KEY`. GPT image models **always** return base64
(`data[0].b64_json`), ignoring `response_format`. `quality` accepts
`low|medium|high|xhigh|max|auto`.

### 1.3 Black Forest Labs FLUX

Official pricing: https://docs.bfl.ai/quick_start/pricing
Official quickstart: https://docs.bfl.ai/quick_start/generating_images

| Model | Price per image |
|---|---|
| FLUX.2 [klein] 4B | from $0.014 |
| FLUX.2 [klein] 9B | from $0.015 |
| FLUX.2 [pro] | from $0.03 |
| FLUX.2 [flex] | from $0.05 |
| FLUX.2 [max] | from $0.07 |
| FLUX.1 Kontext [pro] / [max] | $0.04 / $0.08 |
| FLUX1.1 [pro] / Ultra / Raw | $0.04 / $0.06 / $0.06 |
| FLUX.1 Fill [pro] | $0.05 |

FLUX.2 is priced by output megapixels, so "from" is the floor. API: base
`https://api.bfl.ai/v1`, header `x-key`, async submit-then-poll, result is a
**signed URL valid 10 minutes** at `result.sample` - you must download immediately.
The quickstart's worked example uses the endpoint path `/v1/flux-2-pro-preview`.

**FLUX 3** was announced 2026-07-23 as a joint image/video/audio model but is in gated
early access with **no public API and no published image pricing** (`UNVERIFIED`,
secondary). Do not target it.

Fine-tuning: BFL ships a FLUX Pro Finetuning API (https://bfl.ai/blog/25-01-16-finetuning)
and FLUX.2 [klein] training docs exist. fal hosts a `fal-ai/flux-2-trainer` and
`fal-ai/flux-2/lora` for LoRA. Practical guidance from those pages: 15-20 sharp,
well-captioned images is the working minimum for a brand-style LoRA.

Aggregators: Replicate `black-forest-labs/flux-1.1-pro` $0.04/image, `flux-dev`
$0.025, `flux-schnell` $0.003 (https://replicate.com/pricing). fal lists Flux Kontext
Pro at $0.04/image (https://fal.ai/pricing).

### 1.4 Ideogram (text-in-image specialist)

Official API ref: https://developer.ideogram.ai/api-reference/api-reference/generate-v4
(and `.../generate-v3`)

- v4: `POST https://api.ideogram.ai/v1/ideogram-v4/generate`, header `Api-Key`,
  `multipart/form-data`, fields `text_prompt` (enables magic prompt) **or**
  `json_prompt` (structured, disables magic prompt), `resolution`, `rendering_speed`,
  `enable_copyright_detection`. `rendering_speed=FLASH` currently 400s ("coming soon").
- v3: `POST https://api.ideogram.ai/v1/ideogram-v3/generate`, same auth, adds
  `style_type`, `style_preset`, **`style_codes`**, `seed`, `negative_prompt`,
  `num_images`, **`style_reference_images`**, **`character_reference_images`**.
- Response returns time-limited **URLs**, not base64. Download immediately.

Pricing is `UNVERIFIED` (Ideogram's own docs page defers to an app-internal page).
Consistent third-party figures: v4 Turbo $0.03 / Default $0.06 / Quality $0.10;
v3 Turbo $0.03 / Default $0.06 / Quality $0.09. Also reported: adding a card triggers
an initial $40 top-up with auto-top-up at $10 (`UNVERIFIED`) - that is a real
onboarding friction point for a one-off website build.

### 1.5 Recraft (the vector/SVG and brand-consistency play)

Official docs: https://www.recraft.ai/docs/api-reference/getting-started.md,
`.../endpoints.md`, `.../pricing.md`

- Base URL `https://external.api.recraft.ai/v1`, `Authorization: Bearer $RECRAFT_API_TOKEN`.
  OpenAI-SDK-compatible base URL.
- `POST /images/generations`, plus explicit `/images/generations/raster` and
  `/images/generations/vector`.
- Body: `prompt`, `model` (default `recraftv4_1`), `n` (1-6), `size` (`WxH` or `w:h`),
  `style` (e.g. `vector_illustration`), `style_id` (UUID of a style you created from
  reference images), `response_format` (`url` | `b64_json`).
- 18 operations total including vectorize, upscale, inpaint, background removal/replace,
  and **style creation** - the style_id mechanism is the reason Recraft wins
  "consistent illustration set".

Verified price table (USD per image):

| Raster | $ | Vector (SVG) | $ |
|---|---|---|---|
| V4.1 | 0.035 | V4.1 Vector | 0.08 |
| V4.1 Pro | 0.21 | V4.1 Pro Vector | 0.30 |
| V4 | 0.04 | V4 Vector | 0.08 |
| V4 Pro | 0.25 | V4 Pro Vector | 0.30 |
| V4 Styles | 0.035 | V4 Styles Vector | 0.05 |
| V4 Styles Pro | 0.10 | V4 Styles Pro Vector | 0.12 |
| V3 | 0.04 | V3 Vector | 0.08 |
| V2 | 0.022 | V2 Vector | 0.044 |

Recraft Studio (web) has a permanent free tier of ~50 credits/day; **API Units are a
separate prepaid balance** and the API key is only issuable once that balance is above
zero (verified in getting-started.md). So Recraft API is not free.

### 1.6 Everything else

| Service | Status | Price | Source |
|---|---|---|---|
| Midjourney | **No official API.** ToS forbids automated access. Every "Midjourney API" is an unofficial wrapper that risks the account. | n/a | secondary, consistent across sources |
| Stability AI | Credit API, 1 credit = $0.01, 25 free credits on signup. Ultra $0.08, SD3.5 Medium $0.035, Core $0.03 | as listed | `UNVERIFIED` (secondary) |
| Luma Photon | Photon $0.015 per 1080p, Photon Flash $0.002 | as listed | `UNVERIFIED` (secondary) |
| ByteDance Seedream | `fal-ai/bytedance/seedream/v4/text-to-image` $0.03/image on fal; v4.5 exists; Seedream 5.0 Pro listed at $0.09/image on Artificial Analysis | as listed | fal pricing page (verified for v4), rest secondary |
| Microsoft MAI-Image-2.6 | Azure AI Foundry public preview + OpenRouter. $5/$8/$38 per 1M text-in/image-in/image-out. ~$0.0389/image normalised | as listed | Artificial Analysis + MS blog, `UNVERIFIED` per-image |
| Qwen Image 3.0 | fal: $0.02 per megapixel | as listed | https://fal.ai/pricing |

**Quality ranking (blind ELO, Artificial Analysis text-to-image leaderboard, Sept 2026)**
with their normalised $/1000 images:

1. GPT Image 2 (high) 1172 - $211
2. MAI-Image-2.6 1145 - $38.9
3. Reve 2.1 1127 - $200
4. Nano Banana 2 (gemini-3.1-flash-image) 1122 - $67
5. Muse Image 1112 - $10
6. MAI-Image-2.5 1105 - $48.1
7. GPT Image 1.5 (high) 1103 - $133
8. MAI-Image-2.6-Flash 1099 - $19.5
9. Nano Banana Pro (gemini-3-pro-image) 1097 - $134
10. MAI-Image-2.5-Pro 1097 - $108.5
11. Nano Banana 2 Lite 1085 - $33.6
12. Qwen-Image-3.0-Pro 1085 - $40
13. Seedream 5.0 Pro 1080 - $90
14. Qwen-Image-3.0 1076 - $30
15. grok-imagine-image-quality 1040 - $50

Read that as: the top of the board is a ~9% ELO spread over a 20x price spread. Paying
GPT Image 2 prices for a section image is not defensible; paying them for the one hero
sometimes is.

### 1.7 Local generation on this machine - honest answer

Radeon 890M is RDNA 3.5 with full ROCm support on Linux, and ComfyUI/A1111 run natively.
A secondary benchmark puts **SDXL at roughly 20-30 s per image** on the 890M
(`UNVERIFIED`, single blog source: https://minipclab.com/blog/best-mini-pc-for-stable-diffusion).

Verdict: technically viable, practically not worth it here.

- SDXL is a 2023-class model. Its output is *the* AI look this research is trying to
  kill. You would spend the setup effort to buy yourself worse images.
- FLUX.1-dev (12B) or FLUX.2-dev (32B) on shared iGPU memory means minutes per image at
  best, with VRAM pressure against system RAM.
- The whole asset set costs $1-5 on an API. Local wins only on privacy or on volume
  measured in thousands.

Use local only if the user later wants an offline, no-key, unlimited-iteration
sandbox and accepts SDXL-tier quality. Otherwise skip.

---

## 2. Which model for which website asset

| Asset class | Winner | Why | Price/image | When generation is wrong |
|---|---|---|---|---|
| Photorealistic hero | **FLUX.2 [pro]** primary, `gemini-3-pro-image` when the hero needs legible text baked in | FLUX responds hardest to camera-physics prompting (diffusion, not LLM-mediated), and has `negative_prompt` + seed + raw modes. FLUX1.1 [pro] Raw exists specifically for a less-processed look | $0.03 / $0.134 | If the page is about a real place, product or team, a real photo always wins. A hero is the most-scrutinised image on the site |
| Product shot / packshot | **`gpt-image-2.5-sunburst`** or **FLUX.1 Kontext [pro]**, both in *edit* mode over a real photo | Both are tuned for editing precision; Kontext is BFL's edit model. Recraft also has background removal/replace endpoints | $0.04 (Kontext) | **Almost always wrong.** Never generate a product you actually sell. Photograph it on white, then use edit/background-replace. A generated packshot of a real SKU is a returns problem and arguably a misrepresentation |
| Human portrait / testimonial avatar | **Do not generate** | Fake faces attached to fake names are the highest-trust-cost thing on a marketing site, and faces are where AI tells concentrate (waxy skin, identical catchlights, wrong ear/hand geometry) | - | Use a real photo with consent, an illustrated/abstract avatar (Recraft vector, consistent style_id), or initials in a circle. If a placeholder is genuinely needed, label it as an illustration |
| Abstract background / texture / gradient mesh | **Code, not a model** | CSS `radial-gradient` stacks, SVG `feTurbulence`+`feDisplacementMap`, canvas/WebGL noise. Resolution-independent, theme-aware, ~0 bytes, animatable, no license question | $0 | Generation is the wrong answer here roughly always. A 2MB JPEG of a blurry gradient is a Core Web Vitals bug wearing a design hat |
| Spot illustration, consistent style set | **Recraft V4.1 Vector** with a saved `style_id` | Only major line emitting native editable SVG *and* exposing a reusable style handle. SVG means you can recolor to brand tokens in CSS and it stays crisp in dark mode | $0.08 | If you already have an illustration library (unDraw, Humaaans, Blush, Storyset), use it |
| Icon | **Do not generate. Use a library** | Lucide, Phosphor, Heroicons, Tabler. Free, optically corrected on a shared grid, tree-shakeable, already accessible | $0 | A bespoke set is the only exception: Recraft V4.1 Vector with one locked `style_id` and a fixed `size` |
| Logo / mark | **Recraft V4.1 Pro Vector for exploration only** | Real editable paths you can hand to a designer. But an AI logo is unownable-ish, un-trademarkable in practice, and reads generic | $0.30 | Final mark: hand-drawn, or hand-written SVG (see section 3 - a frontier LLM writes clean geometric marks well). Never ship a generated logo as the brand |
| UI screenshot / product mockup | **Never generate. Screenshot the real thing** | Playwright/Chromium headless against the actual app or a static HTML mock. Generated UI has garbled labels, impossible controls and inconsistent iconography - it is the single most obvious "this product does not exist" tell | $0 | No exception |
| Blog cover | `gemini-3.1-flash-image` at 2K, 16:9 | Cheap, fast, Search-grounded when the post is about something real | $0.101 | If the post has a strong pull-quote, a typographic cover rendered from code beats any generated image |
| OG / social card | **Code: satori / `@vercel/og` / Playwright screenshot** | Must be pixel-exact 1200x630, must carry per-page dynamic text, must match brand type. https://vercel.com/docs/og-image-generation | $0 | Generation is the wrong answer always. Even the best text-rendering model cannot guarantee a per-post title renders correctly, and you would pay per post forever |
| Charts / diagrams | **Code** (Recharts, D3, Mermaid, inline SVG) | Same reasoning as OG cards, plus the data has to be right | $0 | No exception |

Compressed default: **generate hero/section/blog imagery; use Recraft vector for
bespoke illustration; write everything else in code or take it from a library.**

---

## 3. Vector and SVG

### 3.1 Recraft: is it real SVG?

Yes, per multiple independent write-ups and per Recraft's own architecture: the vector
models emit SVG directly from the prompt rather than raster-then-trace. Output contains
`<path>`, `<rect>`, `<circle>` and `<g>` elements with explicit `fill`/`stroke` and
standard cubic-Bezier `d` data, editable in Figma/Illustrator/Inkscape.
(https://www.mindstudio.ai/blog/how-to-generate-editable-svg-files-recraft-v4-1-vector,
https://www.datastudios.org/post/recraft-true-svg-vector-generation-model-pricing-and-api-explained
- both secondary, so `UNVERIFIED` as a formal claim, but consistent and checkable in
one $0.08 call.)

Caveat that matters: **path count scales with scene complexity.** Flat icons and limited-
palette illustrations come out clean and hand-editable. Anything approaching photoreal
comes out as hundreds of overlapping stacked paths - technically vector, practically a
blob you cannot recolor by hand. Keep vector prompts to flat, limited-palette, geometric
subjects.

Recraft also exposes a separate **vectorize** endpoint (raster -> SVG trace). That is the
tracing path; the `/generations/vector` route is not it. Do not confuse the two.

### 3.2 Other real-SVG services

- **Recraft is the only major model line with native vector output.** Everything else in
  the "AI SVG generator" space is either a wrapper over Recraft or a raster generator
  plus an autotrace (potrace/vtracer) step.
- Wrappers/competitors seen: SVG.io, SVGMaker, SVG AI, Iconify AI (icons only), SVG Genie.
  Treat any of them as trace-based unless they document otherwise.
- Open source: VectorFusion, DiffVG, SVGDreamer. All need a real GPU, all produce output
  that needs substantial cleanup. Not viable on a 890M.
- **Autotrace is a legitimate fallback**: generate a flat 2-color raster with any model,
  then `vtracer` or `potrace` locally. Free, offline, and for genuinely flat art the
  result is close to native. Worth having in the runbook as the no-Recraft-key path.

### 3.3 Frontier LLM writing SVG by hand

Viable in 2026, within a narrow band.

Evidence: Simon Willison's writeup of Tom Gally's benchmark
(https://simonwillison.net/2025/Nov/25/llm-svg-generation-benchmark/) ran 30 "SVG of X
doing Y" prompts across 9 frontier models. Results were highly variable: Gemini 3 Pro
and Claude Sonnet 4.5 produced genuinely good detailed drawings; weaker models produced
"a floating brown pill with a hint of a chimney" instead of a steam engine, and abstract
shapes instead of compositions. Academic benchmarks exist (SVGenius arXiv 2506.03139,
VGBench arXiv 2407.10972). Design Arena currently ranks Claude Opus 5 top for
code-written SVG (`UNVERIFIED`, secondary).

Known failure modes, in the order you will hit them:

1. **Coordinate drift on organic shapes.** Anything with a curve the model cannot derive
   from a formula ends up lumpy or self-intersecting.
2. **Proportion collapse.** Individually correct parts assembled at wrong relative scale.
3. **Silent occlusion.** Correct paths in wrong z-order, so the subject is behind the
   background.
4. **Unverifiable output.** The model cannot see what it drew. Without a render-and-look
   loop it is writing blind.

So: use hand-written SVG for **geometric, constructible** things - logos built from
circles/arcs/polygons, patterns, dividers, spot illustrations that are basically
diagrams, and anything where you can express the shape as math. Do not use it for
organic subjects. And always close the loop: render to PNG (`rsvg-convert` or
`chromium --headless --screenshot`) and Read the PNG back before shipping.

---

## 4. Killing the AI look

### 4.1 Does camera-math prompting still hold?

Partly, and the split matters.

- **On diffusion models (FLUX, SDXL, Ideogram, Seedream): yes, still the primary lever.**
  Focal length, aperture, ISO, film stock and lighting nouns are in the training
  captions and move the output measurably. Negative prompts also work: FLUX and Ideogram
  v3 both expose `negative_prompt`.
- **On LLM-mediated models (Gemini 3 image line, GPT Image 2.5): weaker leverage,
  different technique.** These read the prompt as instructions rather than as a caption
  distribution. They respond better to a plainly described *scene with specified
  imperfections* than to a spec sheet. Critically, **neither Gemini nor OpenAI exposes a
  negative prompt field** - you have to state what you want in positive terms
  ("shot on an overcast afternoon, flat light, visible skin texture and pores"), because
  "no plastic skin" gets read as a mention of plastic skin.
- The universally-agreed prompt-side rules, which did survive into 2026:
  - Never write `masterpiece`, `perfect lighting`, `8k`, `award-winning`, `hyperrealistic`.
    Those words are a direct request for the idealised, over-rendered mean.
  - Name a photographer or a documentary tradition instead of an adjective.
    "In the style of William Eggleston" carries more real-world signal than "cinematic".
  - Words that imply a human operator: `candid`, `shot from the hip`, `handheld`,
    `available light`, `slightly underexposed`, `mid-conversation`.
  - Add **one or two** imperfection nouns, three maximum. More and the model
    over-corrects into a deliberately-degraded look, which is its own tell.
    (https://upsampler.com/blog/make-ai-images-look-real,
    https://delv.tools/blog/ai-images-that-dont-look-ai-generated)

### 4.2 The higher-leverage 2026 techniques

Ordered by how much they actually buy you:

1. **Reference-image conditioning. This is the big one.** The 2026 default workflow is:
   lock the look in one reference image, then condition every subsequent generation on
   it. Gemini's Interactions API takes `{"type":"image","mime_type":...,"data":...}`
   blocks in `input`. Ideogram v3 takes `style_reference_images` and
   `character_reference_images` as file uploads. Recraft takes a `style_id` created from
   references. FLUX Kontext is edit-from-reference by design. Every "consistent set"
   problem is solved here, not in the prompt.
2. **Style handles, not prompt copy-paste.** Recraft `style_id`, Ideogram `style_codes`.
   These are opaque tokens that reproduce a look across different prompts. This is what
   a prompt string cannot do.
3. **Seed locking - understand what it does not do.** A seed fixes the starting noise. It
   reproduces one image from one prompt. It is **not** a style handle and does not carry
   a look across different prompts - this is the single most common misconception
   (https://prompt-architects.com/blog/355-seeds-and-reproducibility-in-image-generation).
   Correct use: A/B a prompt edit with the composition held constant.
4. **LoRA / finetune for a real brand style.** BFL Finetuning API
   (https://bfl.ai/blog/25-01-16-finetuning), fal `flux-2-trainer` + `flux-2/lora`
   endpoints. 15-20 sharp, well-captioned images is the working minimum. Worth it for a
   client with an existing photo library and an ongoing content need; overkill for one
   site build.
5. **Generate-then-composite.** Generate elements separately (background plate, subject,
   product) and assemble in code. You get real occlusion, real shadows you control, and
   you dodge the models' worst failure - a single monolithic image where every element is
   equally, uncannily in focus.
6. **Post-processing.** Cheap, deterministic, and it removes the statistical fingerprints
   detectors and trained eyes pick up: absent sensor noise, absent compression artifacts,
   absent lens character (https://imagera.ai/blog/why-ai-images-get-flagged-2026).
   All available locally on Arch:

```bash
# 1. Luminance-dependent grain (the single highest-value step)
magick in.png -attenuate 0.4 +noise Gaussian out.png

# 2. Slight desaturation + cool the white balance (AI output skews warm/saturated)
magick in.png -modulate 100,92,100 -channel B -evaluate multiply 1.02 +channel out.png

# 3. Chromatic aberration: shift the R and B channels a hair apart
magick in.png -channel R -roll +1+0 -channel B -roll -1+0 +channel out.png

# 4. Break the too-perfect framing: rotate a fraction of a degree, then crop back
magick in.png -distort SRT 0.4 -shave 12x12 out.png

# 5. Re-encode as JPEG at a realistic quality so it carries real compression artifacts
magick in.png -quality 88 out.jpg
```

Apply 1, 2 and 5 always. Apply 3 and 4 to photographic assets only, never to
illustrations or anything with text.

### 4.3 What makes an image obviously AI *in a website context specifically*

This is a different list from the general "check the hands" one. On a website the tells
are compositional and semantic, not anatomical:

- **The stock-photo-of-nothing.** A generic scene that illustrates no specific claim on
  the page. Real brand photography shows *this* office, *this* product, *this* customer.
  A hero image that would fit any SaaS company is the loudest possible signal.
- **The diverse-team-in-a-glass-office.** Four people of carefully varied ethnicity
  laughing at a laptop. This was already stock-photo cliche before AI; AI just made it
  free, so it is everywhere.
- **Glossy-plastic surface treatment.** Everything lit like a car ad. Uniform specular
  highlights, no matte surfaces, no dust, no wear.
- **Uniform depth of field.** Real lenses fall off. AI images are frequently sharp
  everywhere or blurred by a fake bokeh that does not respect distance.
- **Impossible or garbled UI/text inside the image.** Screens showing nonsense charts,
  keyboards with wrong key counts, signage in a language that is not a language.
- **Every image in the set lit identically at a different subject.** A real shoot has one
  photographer with drifting light. A generated set has one model with a fixed prior.
  Paradoxically the fix is *deliberate variation* across the set, not more consistency.
- **The image carries no information.** If deleting it costs the page nothing, it is
  decoration, and decoration that costs 400KB and reads as AI is a net negative. The
  correct fix for most of these is not a better prompt - it is no image.
- **Hands, ears, teeth, jewelry, reflections.** Still worth a look, but 2026 frontier
  models get hands right most of the time; this is no longer where the money is.

---

## 5. CLI plumbing (headless, one command each)

All of these save a PNG and use only `curl`, `jq`, and `uv run --with X` - nothing
installed globally. Latency figures are order-of-magnitude and `UNVERIFIED`.

### 5.1 Gemini (recommended default)

Key: `GEMINI_API_KEY` (from https://aistudio.google.com/apikey, **billing must be
attached**). Returns base64. Latency ~5-15 s flash, ~15-40 s pro.

The raw-curl JSON path for the Interactions response is not documented verbatim, so use
the documented SDK call:

```bash
GEMINI_API_KEY=... uv run --with google-genai python - <<'PY'
import base64, os
from google import genai
client = genai.Client()   # reads GEMINI_API_KEY
r = client.interactions.create(
    model="gemini-3.1-flash-image",
    input="<prompt>",
)
open("out.png","wb").write(base64.b64decode(r.output_image.data))
PY
```

Verified against https://ai.google.dev/gemini-api/docs/image-generation. To control
aspect ratio and size, add `response_format={"type":"image","mime_type":"image/png",
"aspect_ratio":"16:9","image_size":"2K"}` (keys verified from the same page; exact SDK
kwarg spelling is `UNVERIFIED` - if it rejects, fall back to raw curl below).

Raw curl equivalent (endpoint, headers and request keys verified; the `jq` extraction
path is `UNVERIFIED` - inspect the response once and fix the path):

```bash
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-3.1-flash-image",
       "input":[{"type":"text","text":"<prompt>"}],
       "response_format":{"type":"image","mime_type":"image/png",
                          "aspect_ratio":"16:9","image_size":"2K"}}' \
  | jq -r '.output_image.data' | base64 -d > out.png
```

### 5.2 Black Forest Labs FLUX (photoreal fallback)

Key: `BFL_API_KEY`. Submit then poll; the result is a signed URL valid 10 minutes.
Latency ~5-20 s. Verified against https://docs.bfl.ai/quick_start/generating_images.

```bash
POLL=$(curl -s -X POST "https://api.bfl.ai/v1/flux-2-pro-preview" \
  -H "accept: application/json" -H "x-key: $BFL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"<prompt>","width":1440,"height":2048}' | jq -r '.polling_url')

until URL=$(curl -s "$POLL" -H "accept: application/json" -H "x-key: $BFL_API_KEY" \
            | jq -r '.result.sample // empty'); [ -n "$URL" ]; do sleep 2; done
curl -sL "$URL" -o out.png
```

### 5.3 OpenAI

Key: `OPENAI_API_KEY`. GPT image models always return base64. Latency ~10-60 s at high
quality. Verified against https://developers.openai.com/api/docs/api-reference/images/create.

```bash
curl -s https://api.openai.com/v1/images/generations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2.5-flare","prompt":"<prompt>",
       "size":"1536x1024","quality":"high","output_format":"png","n":1}' \
  | jq -r '.data[0].b64_json' | base64 -d > out.png
```

### 5.4 Recraft (vector / SVG and consistent illustration sets)

Key: `RECRAFT_API_TOKEN`. Note the base host is `external.api.recraft.ai`. Latency
~10-20 s for vector. Verified against
https://www.recraft.ai/docs/api-reference/endpoints.md.

```bash
# SVG out
curl -s -X POST "https://external.api.recraft.ai/v1/images/generations/vector" \
  -H "Authorization: Bearer $RECRAFT_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"<prompt>","model":"recraftv4_1_vector",
       "style":"vector_illustration","size":"1024x1024","response_format":"url"}' \
  | jq -r '.data[0].url' | xargs curl -sL -o out.svg

# Same call with response_format":"b64_json" returns .data[0].b64_json instead.
# Add "style_id":"<uuid>" to reuse a saved style across a whole illustration set.
```

### 5.5 Ideogram (text baked into the image)

Key: `IDEOGRAM_API_KEY`. **multipart/form-data**, not JSON. Returns a time-limited URL.
Verified against https://developer.ideogram.ai/api-reference/api-reference/generate-v4.

```bash
curl -s -X POST "https://api.ideogram.ai/v1/ideogram-v4/generate" \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -F 'text_prompt=<prompt>' \
  -F 'resolution=1280x720' \
  | jq -r '.data[0].url' | xargs curl -sL -o out.png
```

(v3, if you need `style_reference_images` / `negative_prompt` / `seed`, is the same
shape at `/v1/ideogram-v3/generate`.)

### 5.6 fal.ai (one key, many models - Seedream, FLUX, Qwen)

Key: `FAL_KEY`, header `Authorization: Key $FAL_KEY`, host `https://queue.fal.run`.
Verified against https://fal.ai/docs/model-apis/quickstart. The queue response field
names for polling are `UNVERIFIED`; fal's own docs steer you to the client, so use it:

```bash
FAL_KEY=... uv run --with fal-client python - <<'PY'
import fal_client, urllib.request
r = fal_client.subscribe("fal-ai/bytedance/seedream/v4/text-to-image",
                         arguments={"prompt": "<prompt>"})
urllib.request.urlretrieve(r["images"][0]["url"], "out.png")
PY
```

### 5.7 Replicate

Key: `REPLICATE_API_TOKEN`. Billed per output image. Useful mainly as a single key that
reaches FLUX, Recraft and Ideogram at once, at a small markup and with extra cold-start
latency. Prefer the direct APIs above for anything you will run repeatedly.

### 5.8 Zero-cost local steps in the pipeline

```bash
sudo pacman -S imagemagick librsvg oxipng     # grain/grade, SVG->PNG, PNG squeeze
paru -S vtracer                                # raster -> SVG fallback if no Recraft key
npx --yes svgo out.svg -o out.min.svg          # SVG cleanup, always run on model output
chromium --headless --screenshot=og.png --window-size=1200,630 file://$PWD/og.html
```

---

## 6. Cost model

Asset set: 1 hero + 4 section images + 6 spot illustrations + 1 OG card = 12 finals.
Realistic iteration factor for a build where nobody is babysitting each prompt: **3x**,
so ~36 generations. OG card is generated at $0 (code), so 11 generated finals / 33 gens.

| Strategy | Composition | Cost for the set (33 gens) |
|---|---|---|
| **Recommended default** | hero+sections: `gemini-3.1-flash-image` @2K ($0.101 x 15); illustrations: Recraft V4.1 Vector ($0.08 x 18); OG: code | **$2.96** |
| **All-Gemini** | everything `gemini-3.1-flash-image` @2K; illustrations as raster | $3.33 |
| **Premium hero** | above, but hero on `gemini-3-pro-image` @4K ($0.24 x 3) | $3.38 |
| **Cheap fallback** | `gemini-3.1-flash-lite-image` @1K ($0.0336) for everything raster, vtracer for SVG | **$1.11** |
| **No-Google fallback** | FLUX.2 [pro] ($0.03) raster + Recraft vector | $1.89 |
| **Text-heavy site** | Ideogram v4 Default ($0.06) for anything with baked text | ~$2 |
| **Worst reasonable** | everything on GPT Image 2 high ($0.211) | $6.96 |
| **Local SDXL** | $0 in API, ~15-20 min of wall clock for 33 gens, 2023-tier output | $0 |

The whole debate is worth under $6. Optimise for output quality and for how many keys
the user has to create, not for cents.

Recommended default: **Gemini**, one key, covers raster + editing + reference
conditioning + best-in-class baked text. Cheap fallback: same key, `-flash-lite-image`.
Second key only if the site needs real SVG: **Recraft**.

---

## Recommended setup for this machine

One-time, in this order. Stop after step 2 if the site has no bespoke illustrations.

1. **Get a Gemini API key with billing attached.**
   - https://aistudio.google.com/apikey -> Create API key.
   - Attach it to a Google Cloud project that **has billing enabled**. This is the step
     that has been missing: the consumer Gemini subscription does not grant API quota,
     and image models are not on the Gemini API free tier
     (https://ai.google.dev/gemini-api/docs/pricing). Expect the whole site build to bill
     $2-4.
   - Store it. Do **not** put it in shell rc as plaintext if avoidable:
     ```bash
     # option A, simplest
     echo 'export GEMINI_API_KEY="..."' >> ~/.config/environment.d/gemini.conf   # or ~/.zshrc
     # option B, better: keep it out of the shell environment
     secret-tool store --label='Gemini API' service gemini key api
     # then in the skill:  GEMINI_API_KEY=$(secret-tool lookup service gemini key api)
     ```
   - Verify in one call:
     ```bash
     uv run --with google-genai python -c "
     import base64
     from google import genai
     r = genai.Client().interactions.create(
         model='gemini-3.1-flash-image', input='a single ripe banana on a white table')
     open('/tmp/t.png','wb').write(base64.b64decode(r.output_image.data)); print('ok')"
     ```
   - Then fix the `nano-banana` skill to read `GEMINI_API_KEY` and use
     `gemini-3.1-flash-image` (its documented model ID is almost certainly stale).

2. **Install the local toolchain** (free, needed by every path):
   ```bash
   sudo pacman -S imagemagick librsvg oxipng jq
   ```

3. **Only if the project needs real SVG illustrations or icons:** create a Recraft
   account, buy the minimum API Unit top-up (the API key is not issuable at a zero
   balance), and export `RECRAFT_API_TOKEN`. https://www.recraft.ai/docs/api-reference/getting-started.md

4. **Only if the project needs heavy baked-in text** that Gemini 3 Pro Image cannot
   nail: Ideogram key. Be aware of the reported $40 initial top-up (`UNVERIFIED`) -
   for a single site this is usually not worth it; render text in code over a generated
   plate instead.

5. Skip: OpenAI (3-7x the price for a marginal ELO gain), Midjourney (no API, ToS
   forbids it), Replicate/fal (markup + latency, only worth it to reach many models on
   one key), local diffusion (SDXL-tier output on this GPU is not the quality bar we are
   aiming at).

---

## Agent runbook

Per asset class. The agent runs this without asking, and asks only where marked.

**Step 0 - triage before generating anything.**
Classify the asset. If it is an icon, OG card, chart, UI mockup, abstract background,
or a final logo: **do not call an image API.** Go to the code/library path in the
section-2 table and stop. If it depicts a real person, a real product you sell, or a
real place: stop and ask the user for a real photograph. Generation resumes only for
conceptual, illustrative, or atmospheric imagery.

**Step 1 - lock the direction once, before the first generation.**
Write a *style contract*: one paragraph, reused verbatim in every prompt in the set,
covering medium, lighting quality, palette (in the project's actual brand tokens),
lens character and mood. Generate one reference image against it. Show it to the user.
Do not generate the other ten until that one is approved. Then condition every
subsequent generation on that reference image (Gemini `input` image block, Recraft
`style_id`, Ideogram `style_reference_images`) rather than hoping the prompt repeats.

**Step 2 - prompt construction.**
- Describe a specific scene that supports a specific claim on the page. If you cannot
  say which sentence on the page the image illustrates, the image should not exist.
- Append the style contract verbatim.
- Add one or two imperfection nouns (visible skin texture, dust in the light, a slightly
  crooked horizon, an unlit corner). Never three or more.
- Banned tokens: `masterpiece`, `8k`, `hyperrealistic`, `perfect lighting`,
  `award-winning`, `ultra-detailed`, `professional photograph`.
- On Gemini/OpenAI: state everything positively. There is no negative prompt field.
- On FLUX/Ideogram: use `negative_prompt` for the plastic-skin / glossy / oversaturated
  stack.

**Step 3 - generate.**
| Asset | Call |
|---|---|
| Hero (photoreal) | `gemini-3-pro-image` @2K, or FLUX.2 [pro] if the look needs camera-physics control |
| Section image | `gemini-3.1-flash-image` @2K |
| Blog cover | `gemini-3.1-flash-image` @2K, 16:9 |
| Spot illustration | Recraft `/generations/vector`, `recraftv4_1_vector`, fixed `style_id`. No key -> generate flat raster on Gemini, then `vtracer` |
| Product / packshot | edit mode over a real photo (FLUX Kontext or `gpt-image-2.5-sunburst`). Never text-to-image |
| Icon / OG / chart / mockup / background | no API call - library or code |

Budget 3 attempts per final. If attempt 3 is still wrong, the prompt is wrong, not the
seed - rewrite the scene description rather than rerolling.

**Step 4 - post-process every raster (mandatory, local, free).**
```bash
magick in.png -attenuate 0.4 +noise Gaussian \
              -modulate 100,92,100 \
              -quality 88 out.jpg
```
Add the channel-roll chromatic aberration and the fractional rotate/shave for
photographic assets only. Never post-process illustrations, SVG, or anything containing
text.

**Step 5 - optimise and place.**
- SVG: `npx svgo`, then strip hardcoded fills and drive color from CSS custom properties
  so it survives dark mode.
- Raster: emit AVIF/WebP with a JPEG fallback, always set explicit `width`/`height`,
  `loading="eager"` + `fetchpriority="high"` on the hero only, `loading="lazy"`
  everywhere else. Budget: hero under 200KB, section images under 120KB.
- Never ship an image wider than 2x its largest rendered CSS width.

**Step 6 - audit before showing the user.** Walk this list and report failures, do not
silently pass:
1. Does each image illustrate a specific claim on its page? Name the sentence.
2. Does the set look like one photographer or one illustrator, or like ten prompts?
3. Any baked-in text? Is every character correct? If it is decorative garble, regenerate
   or crop it out.
4. Any hands, screens, signage, reflections? Zoom in.
5. Is any of it the diverse-team-in-a-glass-office, the glowing-abstract-network, or the
   floating-glass-dashboard? If yes, it is slop regardless of render quality - kill it.
6. Contrast check any text placed over an image, at both themes.
7. Total image weight of the page under budget?

**Step 7 - record the receipts.** Save, next to the assets: the style contract, every
final prompt, the model ID, the seed or reference-image path, and the post-processing
command. Regenerating one image in six months without this means redoing the whole set.
