# Prompting an image model - per-model method, set consistency, paste-ready templates

> Compiled 2026-09-09 from the labs' own prompting documentation. Quotes carry URLs.
> Items marked UNVERIFIED are blog-level only - do not repeat them as fact.

# Research H: prompting image models for website / brand imagery (2026)

Scope: what the labs themselves document, as of 2026-09. Every claim below is either
quoted from a primary doc with its URL, or labelled `UNVERIFIED`.

Two consumers of this research:
- **API path** - programmatic call to `gemini-3.1-flash-image` / `gemini-3-pro-image` /
  FLUX.2 / Recraft, conditioned on a reference image for set consistency.
- **Manual path** - user has no API key, pastes one self-contained block into the
  Gemini consumer app or AI Studio and downloads the PNG.

---

## 0. Primary sources used

| Lab | Doc | URL |
|---|---|---|
| Google | Gemini API image generation | https://ai.google.dev/gemini-api/docs/image-generation |
| Google | How to prompt Gemini image generation | https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/ |
| Google | Ultimate prompting guide for Nano Banana | https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana |
| Google DeepMind | Gemini 3 Pro Image model page | https://deepmind.google/models/gemini-image/pro/ |
| Google | Nano Banana Pro announcement (consumer app) | https://blog.google/innovation-and-ai/products/nano-banana-pro/ |
| BFL | Prompting Basics | https://docs.bfl.ai/guides/prompting_unified_basics |
| BFL | Prompting Guide FLUX.2 [pro] and [max] | https://docs.bfl.ai/guides/prompting_guide_flux2 |
| BFL | FLUX.2 Text to Image | https://docs.bfl.ai/flux_2/flux2_text_to_image |
| OpenAI | Image generation guide | https://developers.openai.com/api/docs/guides/image-generation |
| OpenAI | Image prompting guide | https://developers.openai.com/api/docs/guides/image-prompting |
| OpenAI | Cookbook: gpt-image-1.5 prompting guide | https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide |
| Ideogram | Generate with Ideogram 3.0 (API ref) | https://developer.ideogram.ai/api-reference/api-reference/generate-v3 |
| Ideogram | Prompting fundamentals | https://docs.ideogram.ai/using-ideogram/getting-started/prompting-guide/2-prompting-fundamentals |
| Ideogram | Quick summary | https://docs.ideogram.ai/using-ideogram/getting-started/prompting-guide/in-a-nutshell |
| Recraft | Styles | https://www.recraft.ai/docs/api-reference/styles |
| Recraft | Endpoints | https://www.recraft.ai/docs/api-reference/endpoints |
| Recraft | Prompting with Recraft V4 | https://www.recraft.ai/docs/prompt-engineering-guide/prompting-with-recraft-v4 |
| Recraft | How to craft prompts | https://www.recraft.ai/blog/how-to-craft-prompts-for-accurate-ai-generated-images |
| Midjourney | Seeds | https://docs.midjourney.com/hc/en-us/articles/32604356340877-Seeds (direct fetch returned 403; quoted below via search extract of that page) |

---

## 1. Per-model documented method, and where they disagree

### 1.1 Google Gemini image models - narrative prose, explicitly

This is the single most load-bearing quote in the whole research, and it is Google's own:

> "Describe the scene, don't just list keywords. The model's core strength is its deep
> language understanding. A narrative, descriptive paragraph will almost always produce
> a better, more coherent image than a simple list of disconnected words."
> - https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/

Repeated by Google Cloud for Nano Banana:

> "A simple list of keywords won't cut it; you need to describe the scene narratively."
> - https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana

Google's own documented best-practice list (verbatim headings, from the developers blog):

1. **Be hyper-specific** - "The more detail you provide, the more control you have.
   Instead of 'fantasy armor,' describe it: 'ornate elven plate armor, etched with
   silver leaf patterns, with a high collar and pauldrons shaped like falcon wings.'"
2. **Provide context and intent** - explain what the image is *for*.
3. **Iterate and refine** - "Don't expect a perfect image on the first try. Use the
   conversational nature of the model to make small changes."
4. **Use "semantic negative prompts"** - "Instead of saying 'no cars,' describe the
   desired scene positively: 'an empty, deserted street with no signs of traffic.'"
5. **Control the camera** - "Use photographic and cinematic language to control the
   composition. Terms like `wide-angle shot`, `macro shot`, `low-angle perspective`,
   `85mm portrait lens`, and `Dutch angle` give you precise control."
6. **Character consistency** - "If you notice a character's features begin to drift
   after many iterative edits, you can restart a new conversation with a detailed
   description to retain consistency."
7. **Aspect ratios on edit** - the model preserves the input's aspect ratio; with
   multiple inputs of differing ratios it adopts the last image's dimensions.

Google Cloud's formula for text-to-image:

> "[Subject] + [Action] + [Location/context] + [Composition] + [Style]"

and for reference-conditioned generation:

> "[Reference images] + [Relationship instruction] + [New scenario]"

Google Cloud also documents, verbatim:
- "Be specific: Provide concrete details on subject, lighting, and composition."
- "Use positive framing: Describe what you want, not what you don't want (e.g. 'empty
  street' instead of 'no cars')."
- Lighting: "Tell the model exactly how the scene is illuminated" (examples given:
  "three-point softbox setup", "Chiaroscuro lighting with harsh, high contrast").
- Camera: "Use specific hardware and photographic terminology" (examples: "GoPro for an
  immersive, distorted action feel", "shallow depth of field (f/1.8)").
- Colour grading: film-stock language, e.g. "as if on 1980s color film, slightly grainy".
- Materiality: "Define their physical makeup" - "navy blue tweed" not just "suit jacket".

**Model IDs** (https://ai.google.dev/gemini-api/docs/image-generation):
`gemini-3.1-flash-lite-image` (1K only), `gemini-3.1-flash-image` (up to 4K),
`gemini-3-pro-image` (premium / "professional asset production"),
`gemini-2.5-flash-image` (legacy).

**Reference-image budget**, per the docs page: "You can now mix up to 14 reference
images to produce the final image", split per model -
- `gemini-3.1-flash-lite-image`: up to 14 object images
- `gemini-3.1-flash-image`: up to 10 object + 4 character + 3 style reference images
- `gemini-3-pro-image`: up to 6 object + 5 character images

**Thinking**: "Gemini 3 image models are thinking models that use a reasoning process
for complex prompts" and the model "generates up to two interim images to test
composition" before the final output. Practical consequence: long, ordered, reasoned
prose is not wasted on this model the way it would be on a pure diffusion model.

**Negative prompt**: no negative-prompt field is documented anywhere in the Gemini image
API. Confirmed by absence plus the explicit "semantic negative prompts" workaround.

**Aspect ratio / size**: the docs page shows a request-side config carrying
`aspect_ratio` and `image_size`, e.g.

```
response_format={
    "type": "image",
    "mime_type": "image/jpeg",
    "aspect_ratio": "16:9",
    "image_size": "1K"
}
```

Ratios documented: `1:1, 3:2, 2:3, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9`
(Google Cloud's Nano Banana guide adds `1:4, 4:1, 1:8, 8:1` for Nano Banana 2).
Sizes: `512px`, `1K`, `2K`, `4K`.

CAUTION - two config shapes are in circulation. The `google-genai` Python SDK form is
`types.GenerateContentConfig(response_modalities=["IMAGE"],
image_config=types.ImageConfig(aspect_ratio="16:9", image_size="2K"))`. The skill must
read the current SDK signature at build time rather than hardcode either shape. Do not
invent a third.

**Multi-turn editing**: `previous_interaction_id` continues an edit chain server-side.

### 1.2 BFL FLUX.2 - natural language, order-sensitive, optional JSON

Structure (https://docs.bfl.ai/guides/prompting_guide_flux2):

> "Use this framework for consistent results: **Subject + Action + Style + Context**"

Priority: "Main subject -> Key action -> Critical style -> Essential context ->
Secondary details", and:

> "Word order matters - FLUX.2 pays more attention to what comes first."

Length, verbatim:
> "**Short (10-30 words)**: Quick concepts and style exploration; **Medium (30-80
> words)**: Usually ideal for most projects; **Long (80+ words)**: Complex scenes
> requiring detailed specifications"

Negative prompts, verbatim:
> "**No negative prompts**: FLUX.2 does not support negative prompts. Focus on
> describing what you want, not what you don't want."

BFL's basics template (https://docs.bfl.ai/guides/prompting_unified_basics):
> "[SUBJECT], [LOCATION], [STYLE], [CAMERA SETTINGS], [LIGHTING], [COLORS], [EFFECT],
> [ADDITIONAL ELEMENTS]" - described as "a useful starting structure, not a strict
> formula."

FLUX.2 also accepts a **JSON prompt**. Exact schema fields from the BFL guide:

```json
{
  "scene": "overall scene description",
  "subjects": [
    { "description": "detailed subject description",
      "position": "where in frame",
      "action": "what they're doing" }
  ],
  "style": "artistic style",
  "color_palette": ["#hex1", "#hex2", "#hex3"],
  "lighting": "lighting description",
  "mood": "emotional tone",
  "background": "background details",
  "composition": "framing and layout",
  "camera": { "angle": "camera angle", "lens": "lens type",
              "depth_of_field": "focus behavior" }
}
```

This is the single best structured-prompt vehicle for an agent-built brand set: the
`color_palette` hex array and the `camera` object are exactly the two things a style
contract needs to pin. **Note the disagreement**: Ideogram explicitly rejects hex codes
in prompts, FLUX.2 accepts them as a JSON field.

Multi-reference: "[pro] API has a 9MP total limit for input+output. At 1MP output you
can use up to 8 reference images, at 2MP output up to 7, and so on." And: "When using
multiple input images, clearly describe the role of each: subject from image 1, style
from image 2, background from image 3."

Consistency across a series, verbatim from the guide's comic-panel worked example:
> "Repeat these details in every panel prompt."

Text: "**Use quotation marks**", "**Specify placement**", "**Describe style**"
('elegant serif typography', 'bold industrial lettering').

Endpoint seen on the FLUX.2 text-to-image page: `https://api.bfl.ai/v1/flux-2-pro-preview`,
with `prompt`, `width`, `height`. `seed` and `prompt_upsampling` exist per BFL's
GitHub repo docs (https://github.com/black-forest-labs/flux2) but their exact API
descriptions are `UNVERIFIED` from the docs.bfl.ai reference (the parameter-reference
page 404'd on fetch). Do not hardcode them without checking.

### 1.3 OpenAI gpt-image - labelled sections, invariant restatement

Models on the guide page: `gpt-image-2.5-sunburst` and `gpt-image-2.5-flare` -
"Choose Sunburst for workflows where editing precision matters most, and Flare for
fast, high-quality everyday image generation."
(The cookbook at `image-gen-1.5-prompting_guide` covers `gpt-image-1.5`; treat both as
the same prompting family.)

Order, verbatim from the cookbook:
> "background/scene -> subject -> key details -> constraints"

and "use short labeled segments or line breaks" for complex requests instead of one
long paragraph. **This is a real disagreement with Google**: Gemini wants a flowing
narrative paragraph; OpenAI wants labelled segments. The manual path targets Gemini, so
the paste-ready blocks below are prose. The API path can branch.

Intended use, verbatim: "Name the subject and intended use, such as a product
photograph, advertisement, or diagram."

Photorealism, verbatim from the cookbook:
- treat the prompt "as if a real photo is being captured in the moment"
- request "pores, wrinkles, fabric wear, imperfections"
- avoid "words that imply studio polish or staging"
- "camera/composition terms" "steer realism more reliably than generic" quality
  descriptors
- do not use generic quality descriptors like "8K/ultra-detailed" alone

And from the guide page:
> "Treat camera specifications as cues for appearance, not a guarantee of exact
> physical simulation."
> "specify scale, atmosphere, and color instead of relying on mood words alone."

Edits / invariants, verbatim:
> "For edits, say 'change only X' and list the details to preserve, such as identity,
> geometry, layout, lighting, or labels."
> "pass the previous output as the next edit input, request one change, and repeat the
> details to preserve."
> "Repeated edits can still change details you intended to preserve. Restate those
> constraints and inspect each result."

Sizes: `1024x1024`, `1536x1024`, `1024x1536` recommended; custom `WIDTHxHEIGHT` where
"Width and height must be multiples of 16, the aspect ratio must be between 1:3 and
3:1, and neither edge may exceed 3840 pixels." Quality: `low, medium, high, xhigh,
max, auto`. **No negative-prompt parameter documented.**

Text: "Although significantly improved, the model can still struggle with precise text
placement and clarity."

### 1.4 Ideogram - short-ish, front-loaded, has a real negative_prompt

API params, quoted from https://developer.ideogram.ai/api-reference/api-reference/generate-v3:
- `prompt`: "The prompt to use to generate the image."
- `seed`: "Random seed. Set for reproducible generation."
- `negative_prompt`: "Description of what to exclude from an image. Descriptions in the
  prompt take precedence to descriptions in the negative prompt."
- `style_codes`: "A list of 8 character hexadecimal codes representing the style of the
  image. Cannot be used in conjunction with style_reference_images or style_type."
- `style_reference_images`: "A set of images to use as style references (max size 25MB
  per image; the whole request must stay under 50MB)."
- `character_reference_images`: "...currently only supports 1 character reference image."
- plus `resolution`, `aspect_ratio`, `rendering_speed`, `magic_prompt`, `num_images`,
  `style_type` (AUTO / GENERAL / REALISTIC / DESIGN / FICTION).
- v4 endpoint exists: `POST /v1/ideogram-v4/generate`.

Prompting rules (docs.ideogram.ai):
- Length ceiling: "approximately 150-160 words (around 200 tokens)"; "prompts longer
  than this may be ignored or generate less accurate results."
- "things written earlier in the prompt tend to be given more importance."
- Text: "If you want text in your image, describe it near the beginning of the prompt -
  this leads to better results with fewer errors."
- Explicitly **do not** use: `--ar`, `--v`, `--style` flags; weights like `::1` or
  `(important)`; hex codes / RGB values such as `#E4BC73` (use natural colour words).
- "Use positive descriptions rather than negatives (say 'empty street' instead of 'no
  people')" - even though the API has a `negative_prompt` field.
- Non-Latin scripts are unreliable for text-heavy results; use English.

### 1.5 Recraft - style is a first-class object, not prompt text

Generate params (https://www.recraft.ai/docs/api-reference/endpoints):
- `prompt`: "A text description of the desired image(s)."
- `style_id`: "Use a style as visual reference."
- `model`: "The model to use for image generation. When style references are attached,
  defaults to `recraftv4_styles`."
- `size`: "The size of the generated images in `WxH` or `w:h` format."
- `n`: "The number of images to generate, must be between 1 and 6."
- `negative_prompt`: "A text description of undesired elements on an image."
- `controls`: "A set of custom parameters to tweak generation process."
- `text_layout`, `style`, `response_format`.

Styles (https://www.recraft.ai/docs/api-reference/styles):
- Build a custom style from "from one to ten images"; "no training or fine-tuning is
  required"; the response returns a `style_id` reusable on every later call.
- `style_match`: "precise" or "flexible" for V4/V4.1; "regular" for V2/V3.
- `style_id` and inline style-reference images are **mutually exclusive** - a request
  containing both is rejected.
- The V4 Styles line ("recraftv4_styles", "recraftv4_styles_pro", ...) "always requires
  a style"; other V4/V4.1 models treat styles as optional.

Prompt template (Recraft blog):
> "A <image style> of <main content>. <detailed description of the main content>.
> <description of the background>. <detailed style description>."

And, despite owning a `negative_prompt` field:
> "Including negative phrases like 'no cake' or 'without penguins' can sometimes confuse
> the AI."

Recraft V4 guide adds a global-to-local ordering: core concept -> background/environment
-> subject framing and pose -> physical attributes -> secondary subjects and spatial
relationships -> lighting -> camera/depth/contrast -> mood, and notes short prompts
(3-6 words) "activate interpretive behavior" whereas structured prompts make outcomes
"intentional, controllable, and repeatable."

### 1.6 The disagreement table (this is what the skill must branch on)

| Question | Gemini | FLUX.2 | OpenAI | Ideogram | Recraft |
|---|---|---|---|---|---|
| Prose or keywords | Narrative paragraph, explicitly | Natural language, order-weighted; JSON also supported | Labelled segments / line breaks | Natural language, front-loaded | Either; structure when it must be repeatable |
| Length sweet spot | Long is fine (thinking model) | 30-80 words typical | Medium, segmented | <= ~150 words hard-ish ceiling | Short = interpretive, long = controlled |
| Negative prompt field | None | None (documented) | None | Yes (`negative_prompt`) | Yes (`negative_prompt`) |
| Lab's stance on negatives | Rephrase positively | Rephrase positively | State exclusions in prompt text | Prefer positive phrasing anyway | Negative phrases "can confuse the AI" |
| Hex colours in prompt | Not documented | Yes, `color_palette` JSON array | Not documented | Explicitly discouraged | Via `controls`, not prose |
| Reference images | Up to 14, typed (object/character/style) | Up to 8 at 1MP output | One or more | `style_reference_images` + 1 character ref | 1-10 refs -> reusable `style_id` |
| Style handle that persists | Reference image only | Reference image only | Reference image only | `style_codes` (8-char hex) | `style_id` (workspace-persistent) |
| Seed exposed | Not documented | Yes | Not documented | Yes | Not documented |

A keyword-soup prompt tuned for the Midjourney/SD era is actively wrong on four of
these five models. That mismatch is the most common failure this research exists to
prevent.

---

## 2. Anatomy of a strong prompt, and who respects which slot

Slots, in the order the labs converge on, with a per-model note on whether the slot is
actually honoured:

1. **Image type / medium declaration** - "a photorealistic editorial photograph",
   "a flat vector spot illustration". Google's own templates open this way
   ("A photorealistic [type of shot] of..."). OpenAI: "request 'photorealistic' or
   'real photograph' explicitly when that is the goal." Respected everywhere. Put it
   first: Ideogram and FLUX.2 both weight the front of the prompt.
2. **Subject, hyper-specific** - Google: "Instead of 'fantasy armor,' describe it:
   'ornate elven plate armor, etched with silver leaf patterns...'". Respected
   everywhere. This is the highest-yield slot; generic subjects are what pull the
   output toward the dataset average.
3. **Action / state** - explicit in FLUX.2's "Subject + Action + Style + Context" and
   Google's "[Subject] + [Action] + ...". Respected everywhere. A subject with no verb
   renders as a posed stock photo.
4. **Scene / environment** - Recraft lists "Environment" as its own axis. Respected
   everywhere.
5. **Composition and framing** - "medium-full shot, center-framed", "subject on the
   right third". Respected everywhere; Gemini has a dedicated minimalist/negative-space
   template ("A minimalist composition featuring a single [subject] positioned in the
   [bottom-right/top-left/etc.]").
6. **Camera and optics** - Google: `wide-angle shot`, `macro shot`, `low-angle
   perspective`, `85mm portrait lens`, `Dutch angle`; Google Cloud: "shallow depth of
   field (f/1.8)"; FLUX.2 JSON has a `camera` object with `angle`, `lens`,
   `depth_of_field`. OpenAI honours the *look* but warns: "Treat camera specifications
   as cues for appearance, not a guarantee of exact physical simulation." So: focal
   length and aperture are style vocabulary, not a simulator. ISO in particular is
   `UNVERIFIED` as a documented lever on any of these models - it reads as grain
   language and nothing more; prefer saying "fine 35mm film grain" directly.
7. **Lighting: direction, quality, temperature, time of day** - Google Cloud: "Tell the
   model exactly how the scene is illuminated" with worked examples ("three-point
   softbox setup", "Chiaroscuro lighting"). Respected everywhere; this is the second
   highest-yield slot after subject specificity and the one that carries a set's
   coherence.
8. **Materials and surface behaviour** - Google Cloud: "navy blue tweed" over "suit
   jacket"; Recraft V4 tells you to describe "physical systems" for 3D. Respected
   everywhere, under-used by non-experts.
9. **Colour palette** - FLUX.2: `color_palette` hex array in JSON. Ideogram: hex codes
   explicitly discouraged, use words. Recraft: `controls`. Gemini: `UNVERIFIED` whether
   hex is honoured in prose; use named colours plus a comparative ("a desaturated
   sage green, close to the colour of old copper patina").
10. **Mood** - OpenAI cautions: "specify scale, atmosphere, and color instead of relying
    on mood words alone." So mood is a tie-breaker slot, never a substitute for 6-9.
11. **Art-direction reference** - name a genre or process ("1980s colour film, slightly
    grainy", "Kodak Portra", "editorial fashion magazine"). Naming a *living artist* is
    a policy risk on every platform and adds nothing a process description does not.
12. **Aspect ratio** - a parameter on every API. In chat it is prompt text ("with a 16:9
    aspect ratio"), which is documented as working for the Gemini app.
13. **Negative space for text overlay** - the slot most site imagery needs and most
    prompts omit. Say where the empty region is, roughly how much of the frame it
    occupies, and what should be in it (a flat, low-contrast surface), because every
    lab tells you to phrase absence positively.

---

## 3. Consistency across a set of 8

Ranked by what the docs actually support, best first.

**1. Reference-image conditioning (generate one hero, condition the rest on it).**
The only mechanism all five labs document. Gemini takes typed references - "up to 14
reference images", split into object / character / style-reference buckets per model.
FLUX.2 takes up to 8 at 1MP output and tells you to "clearly describe the role of each:
subject from image 1, style from image 2, background from image 3." OpenAI takes "one
or more images as a reference". Ideogram has `style_reference_images`. This is the
workflow to build the skill on: approve one hero, pass it as the style reference on
every subsequent call, and describe its role explicitly in the prompt text.

**2. A persistent style handle, where the platform has one.**
Recraft is the strongest here: build a style from "from one to ten images", get a
`style_id` that "belongs to your workspace and persists indefinitely", "no training or
fine-tuning is required", then pass `style_id` on every generation. Ideogram's
`style_codes` (8-char hex) is the equivalent, with the caveat that it "Cannot be used in
conjunction with style_reference_images or style_type". Gemini, FLUX.2 and OpenAI have
no persistent style ID - for those, the reference image *is* the handle, so the skill
must store the hero PNG alongside the style contract.

**3. A verbatim repeated style block in the prompt text.**
BFL's own comic-panel example: "Repeat these details in every panel prompt." OpenAI's
version: "repeat the preserve list on each iteration to reduce drift" and "re-specify
critical details if they start to drift." Cheap, model-agnostic, and it works. The
practical form is a fixed 40-60 word paragraph - same camera, same lighting, same
palette, same grain, same processing - appended identically to all 8 prompts, with only
the subject sentence varying.

**4. Multi-turn continuation.** Gemini's `previous_interaction_id` keeps an edit chain
server-side; the consumer app does the same conversationally. Good for variants of one
image, weak for 8 different subjects - Google itself warns features "begin to drift
after many iterative edits" and recommends restarting with a detailed description.

**5. Seed locking - the overrated one.** Midjourney's docs state it plainly:

> "Seeds can't capture or bookmark a specific style, character, or appearance across
> different prompts. They only influence the initial layout of noise that begins the
> rendering process."
> - docs.midjourney.com Seeds article (fetched via search extract; direct fetch 403)

Ideogram's own description is equally narrow: "Random seed. Set for reproducible
generation." Gemini and OpenAI do not expose a seed at all in the documented image
paths. **Verdict: a seed reproduces one image; it does not carry a style across
different prompts.** Any skill that promises set consistency via seed locking is
promising something no lab documents. Use a seed for regenerating the identical asset
after a code change, nothing else.

**6. Character/subject consistency features.** Gemini: "up to 4 images of characters"
(3.1 Flash) or 5 (3 Pro, "the consistency and resemblance of up to five characters").
Ideogram: `character_reference_images`, "currently only supports 1 character reference
image". Relevant for a mascot across a site; not the mechanism for photographic set
coherence.

**What people believe works but does not:** identical seed across different prompts;
appending the same trailing keyword stack ("cinematic, 8k, professional") - it
homogenises toward the dataset average rather than toward *your* look; asking one model
for 8 images in a single prompt (composition collapses and per-image aspect ratio is
lost).

---

## 4. Killing the AI look, at the prompt level

**4a. The negative stack is inert on Gemini, FLUX.2 and OpenAI.** Verified: no
negative-prompt field is documented on any of the three. Only Ideogram
(`negative_prompt`: "Description of what to exclude from an image. Descriptions in the
prompt take precedence to descriptions in the negative prompt.") and Recraft
(`negative_prompt`: "A text description of undesired elements on an image.") have one -
and Recraft's own blog says negative *phrasing* "can sometimes confuse the AI". So a
`--no plastic skin, extra fingers, watermark` stack shipped to Gemini is dead weight
that also eats attention budget.

**What replaces it - positive phrasing of absence.** Google's documented term is
"semantic negative prompts":

> "Instead of saying 'no cars,' describe the desired scene positively: 'an empty,
> deserted street with no signs of traffic.'"

Google Cloud: "Use positive framing: Describe what you want, not what you don't want
(e.g. 'empty street' instead of 'no cars')." BFL: "Focus on describing what you want,
not what you don't want." Ideogram: "say 'empty street' instead of 'no people'."
Four labs, same instruction. Convert every negative into a described positive:

| Instead of | Write |
|---|---|
| no text, no watermark | a clean, unmarked surface with no signage in frame |
| not plastic skin | visible pores, fine lines at the eye corners, a slight shine on the nose |
| no extra fingers | hands resting flat on the table, fingers relaxed and countable |
| not oversaturated | muted, slightly desaturated colour, close to unedited raw |
| no bokeh blobs | a background that falls off gently, foliage still readable |

OpenAI is the exception that proves the shape: it *does* tell you to "state exclusions
such as unwanted text, logos, or watermarks" - as prompt sentences, not a parameter.

**4b. Imperfection nouns beat quality adjectives.** OpenAI's cookbook, verbatim: request
"pores, wrinkles, fabric wear, imperfections"; treat the prompt "as if a real photo is
being captured in the moment"; avoid "words that imply studio polish or staging". The
working set: dust on a matte surface, a fingerprint on glass, a scuffed table edge, one
strand of hair out of place, a slightly crooked label, uneven wear on a floorboard,
mixed colour temperature where a window meets a lamp, a shadow falling across part of
the subject, a crop that clips something at the frame edge.

**4c. Specific subjects beat generic ones.** Google: "Be hyper-specific... The more
detail you provide, the more control you have." A generic noun is a request for the
average of every image captioned with that noun - which is precisely the AI look.
"A ceramicist" -> Google's own example: "A photorealistic close-up portrait of an
elderly Japanese ceramicist..."

**4d. Counterproductive tokens.** Verified from primary sources:
- OpenAI cookbook: do not use generic quality descriptors like "8K/ultra-detailed"
  alone; "camera/composition terms steer realism more reliably than generic" quality
  descriptors. Also: avoid "studio polish", "staging", "cinematic grading",
  "overly enhanced" language when the goal is grounded photorealism.
- Google (twice): a list of disconnected keywords underperforms a narrative paragraph.
- Ideogram: no `--ar`/`--v`/`--style` flags, no `::1` weights, no `(important)`, no hex
  codes, and non-Latin script for text is unreliable.

The specific token list - `masterpiece`, `8k`, `hyperrealistic`, `award-winning`,
`trending on artstation`, `ultra detailed`, `professional`, `high quality` - is
**partly verified**: "8K/ultra-detailed" and generic quality descriptors are named by
OpenAI, and "cinematic"-style grading language is named as an anti-pattern for realism.
The stronger claim that `masterpiece` and `award-winning` actively *degrade* modern
model output is `UNVERIFIED` against any lab doc; it appears only in secondary blog
sources. The defensible rule, which needs no unverified claim: these tokens carry no
documented benefit on any 2026 model, they consume front-of-prompt attention on the two
models that weight word order, and they pull toward a training-caption average. Drop
them. Spend those words on lighting direction and one material instead.

Two more that are AI-look tells and cost nothing to avoid: perfectly centred symmetry
with a subject staring down the lens, and a shallow depth of field applied to a scene
that would not have been shot that way.

---

## 5. Text inside images

Documented capability, best first:
- **Gemini 3 Pro Image** - DeepMind claims "the lowest error rates" in single-line text
  rendering across languages, "Generate clear text for posters and intricate diagrams",
  and the API docs say "Use Gemini 3 Pro Image for professional asset production" for
  advanced text rendering. It also does localisation: "Generate localized text, or
  translate text inside images."
- **Ideogram** - purpose-built for typography; `style_codes`, `style_type: DESIGN`, and
  a documented instruction to put the text early in the prompt.
- **Recraft** - has `text_layout`, which places individual words inside explicit
  bounding boxes. That is the only *coordinate-level* text control in this set.
- **OpenAI** - self-declared limit: "Although significantly improved, the model can
  still struggle with precise text placement and clarity."

Syntax that the labs actually document:
- **Quote the literal string.** Google Cloud: "Use quotes: Enclose your desired words in
  quotes (e.g., 'Happy Birthday' or 'URBAN EXPLORER')." BFL: "Use quotation marks: 'The
  text 'OPEN' appears in red neon letters above the door'." OpenAI: "Put required
  wording in quotes and describe its position and typography", plus ALL CAPS as an
  alternative marker.
- **Name the typography.** Google Cloud: "Choose a font: Describe the typography style
  or name of the font. Prompt for a 'bold, white, sans-serif font' or 'Century Gothic
  12px font'."
- **Spell hard words out.** OpenAI: "spell unusual words or brand names letter by letter
  when needed."
- **Say where.** Both Google and OpenAI ask for placement relative to other elements.
- **Ask for nothing else.** OpenAI: "ask for no extra text, then check spelling and
  legibility in the output."
- **Text-first trick (Gemini).** Google Cloud: "When generating text for an image,
  Gemini Image models work best if you first converse with it to generate the text
  concepts, and then ask for an image with that text." This is free on the manual path
  and unavailable in a single API call - a genuine chat-UI advantage.
- **English.** Ideogram: non-Latin scripts are unreliable for text-heavy output.

**When to give up and composite in code.** Rule for the skill: generate text in the
image only for a single short line - a wordmark, a poster headline, a sign inside the
scene, roughly a headline's worth. Anything that is body copy, a paragraph, a legal
line, a price, a URL, a phone number, or anything that must be selectable, translatable,
searchable, A/B-testable or exactly on-brand-font: generate the plate with negative
space and set the type in HTML/CSS. Comparative "headlines yes, paragraphs no" rankings
circulating for 2026 are `UNVERIFIED` blog benchmarks, but the composite rule stands on
OpenAI's own admission plus the fact that no lab claims reliable multi-line body copy.

---

## 6. The manual / chat-UI path

What the consumer Gemini app documents (blog.google Nano Banana Pro announcement,
gemini.google/overview/image-generation, Google Cloud guide):

- **Entry point**: tools menu -> "Create images". Model choice exposed as Fast /
  Thinking / Pro; the announcement says to "select 'Create images' with the 'Thinking'
  model" for the Pro-grade path.
- **Aspect ratio without a parameter**: state it in the prompt sentence. Google Cloud's
  own example prompt ends "...with 2:3 aspect ratio". Same ratio list as the API.
- **Resolution**: "a range of available aspect ratios and available 2K and 4K
  resolution" in the app.
- **Editing is conversational**: "Adjust camera angles, change the focus and apply
  sophisticated color grading, or even transform scene lighting (e.g. changing day to
  night or creating a bokeh effect)." Google's blog also documents restarting a fresh
  conversation when features drift.
- **Consistency of people**: "up to 5 people" in the app.
- **Watermark**: every output carries "an imperceptible SynthID digital watermark".
  Users can upload an image and ask whether Google AI generated it.

**What chat can do that the API cannot**: the text-first trick (converse to settle the
wording, then ask for the image); iterative "keep everything the same but..." edits with
no ID plumbing; asking the model to critique its own output and regenerate; uploading a
reference by drag-and-drop.

**What the API can do that chat cannot**: a fixed `aspect_ratio`/`image_size` guaranteed
per call rather than requested in prose; deterministic reuse of the same reference set
across 8 calls; `previous_interaction_id` chains; batch; typed reference buckets
(object vs character vs style); any seed or negative-prompt field on the models that
have them.

**Rules for writing the paste-ready block** (this is what the skill emits):
1. One block, prose, no headings, no markdown, no bracketed placeholders left unfilled.
2. Open with the medium and shot type; close with the aspect ratio sentence.
3. No parameter syntax of any kind - no `--ar`, no `seed=`, no JSON. The chat UI has no
   such fields and Ideogram documents that flags are simply not parsed.
4. Every constraint phrased positively (see 4a).
5. Include the "leave the left third clean and unoccupied for a headline" sentence when
   the asset takes an overlay.
6. Add one line the user can send as a follow-up turn if attempt 1 misses, e.g. "Keep
   everything identical but make the light come from the left and lower the contrast."
7. For a set: tell the user to generate the hero first, then attach that image to each
   subsequent chat turn and say "match the lighting, colour and grain of the attached
   image exactly; only the subject changes."

**What to tell the user to do with the result**:
- Download at the largest offered size (4K if available; 2K minimum for a hero, 1K is
  fine for a spot illustration or an OG plate).
- Check, in this order: (a) the intended empty region is genuinely empty and flat enough
  to carry type at contrast; (b) any rendered text is spelled correctly, character by
  character; (c) hands, ears, teeth, eyeglass frames, and where two objects meet;
  (d) repeated texture patterns and cloned foliage/crowd; (e) light direction and
  shadow direction agree, and agree with the rest of the set; (f) the subject is not
  clipped by the crop the site will apply; (g) product/brand assets are accurate and
  not invented.
- Re-encode for the web (AVIF/WebP with a JPEG fallback), set explicit width/height, and
  never ship the raw PNG.
- Note that outputs carry SynthID; if the brand has a disclosure policy, it applies.

---

## The prompt builder

The procedure an agent follows to turn a design brief plus a style contract into a
prompt. Deterministic; run it identically for all 8 assets in a set.

**Inputs.**
- `brief`: asset class, subject, what the image is for, where it sits on the page.
- `style_contract`: a frozen record of medium, camera, lighting, palette, processing,
  mood - written once for the whole site, never re-derived per asset.
- `overlay`: none | text-left | text-right | text-centre | text-bottom, plus the
  fraction of frame the type needs.
- `target`: model id, aspect ratio, output size.
- `hero_ref`: path to the approved hero image, or null if this *is* the hero.

**Step 1 - freeze the style contract, once.** Fill exactly these fields, in words a
photographer would use, and never change them for the rest of the set:
`medium` (e.g. 35mm colour film photograph), `lens` (e.g. 50mm, shallow depth of field),
`light` (direction + quality + temperature + hour, e.g. low afternoon sun raking in from
the left, warm, hard-edged shadows), `palette` (3-4 named colours plus one accent),
`processing` (e.g. slightly lifted blacks, fine grain, no vignette),
`materials` (the two or three surfaces that recur across the site),
`mood` (one clause only).

**Step 2 - pick the branch.**
- Gemini or the chat UI -> narrative prose, one paragraph, 80-150 words.
- FLUX.2 -> either the ordered prose (Subject + Action + Style + Context, 30-80 words,
  most important first) or the JSON schema with `color_palette` hex.
- OpenAI -> labelled segments in the order scene, subject, details, constraints.
- Ideogram -> under 150 words, text-bearing content named first, `negative_prompt`
  populated, no hex, no flags.
- Recraft -> create the `style_id` from 1-10 hero images once, then keep prompts to
  subject + scene and let `style_id` carry the look.

**Step 3 - assemble the slots in order** (section 2): medium -> subject (hyper-specific,
with one proper noun or one concrete material) -> action/state -> environment ->
composition and where the subject sits in frame -> camera and optics -> lighting ->
materials and surfaces -> palette -> one mood clause -> art-direction reference.

**Step 4 - insert the overlay sentence** when `overlay != none`: name the region, its
share of the frame, and what occupies it, positively. "The left third of the frame is an
uninterrupted expanse of pale plaster wall, evenly lit and free of objects."

**Step 5 - convert every negative into a positive.** Scan the draft for "no", "without",
"not", "avoid", "free of <bad thing>". Rewrite each per the table in 4a. If the target
model has a real `negative_prompt` field (Ideogram, Recraft), the field takes only the
residue that cannot be phrased positively - typically watermark, signature, border.

**Step 6 - strip counterproductive tokens.** Delete: masterpiece, 8k, 4k as a quality
word, ultra detailed, hyperrealistic, award-winning, professional, high quality,
trending on artstation, best quality, cinematic (as a bare adjective), stunning,
breathtaking, and any `--flag` or `::weight`. Replace the space with one more lighting
or material detail.

**Step 7 - add two imperfections** drawn from the physical logic of the scene, never
generic ones. Dust where dust would settle; wear where a hand would rest.

**Step 8 - bind the set.** If `hero_ref` is not null: attach it, and add the fixed
sentence "Match the lighting direction, colour palette, grain and processing of the
attached reference image exactly; only the subject and setting change." If the model
takes typed references, declare the role of each image. If the platform has a persistent
handle (Recraft `style_id`, Ideogram `style_codes`), pass it and shorten the prose.

**Step 9 - append the ratio.** API: set the parameter. Chat: one closing sentence,
"Render this at a 16:9 aspect ratio."

**Step 10 - emit both forms.** The API payload, and the paste-ready chat block that
carries no parameters, no placeholders and no markdown, plus one suggested follow-up
turn and the acceptance checklist from section 6.

**Step 11 - do not iterate blind.** BFL: change one detail at a time. OpenAI: "start
with a clean base prompt, then refine with small, single-change follow-ups" and restate
the preserve list every time.

---

## Paste-ready templates

Ten asset classes. Each gives the **API form** (slots in `{}`; prose targeted at Gemini
unless noted) and the **Chat form** (self-contained, no parameters, ratio stated in
words). `{STYLE}` = the frozen style-contract sentence from builder step 1;
`{BIND}` = "Match the lighting direction, colour palette, grain and processing of the
attached reference image exactly; only the subject and setting change." Include `{BIND}`
on every asset after the hero.

### 1. Photoreal hero (with overlay space)

**API.** `A photorealistic {shot type} of {hyper-specific subject}, {action or state},
in {specific place}. The subject sits in the {right/left} third of the frame; the
{left/right} third is an uninterrupted expanse of {flat surface}, evenly lit and free of
objects. Shot on {lens, e.g. a 35mm lens at f/2.8}, {camera height/angle}. {Lighting:
direction, quality, colour temperature, hour}. {Two materials, described physically}.
{Palette: 3 colours plus accent}. {One imperfection}, {one imperfection}. {Processing}.
{BIND}` + `aspect_ratio: 16:9`, `image_size: 4K`.

**Chat.** "A photorealistic wide editorial photograph of {subject, hyper-specific},
{doing what}, in {place}. Place the subject in the right third of the frame and leave
the left third as an uninterrupted expanse of {pale plaster wall}, evenly lit and clear
of any object, so a headline can sit there. Shot on a 35mm lens at f/2.8 from just below
eye level. {Late afternoon sun rakes in from the left, warm and hard-edged, throwing one
long shadow across the floor.} {Materials.} The palette stays {colour, colour, colour}
with a single {accent} accent. A little dust catches the light near the window and one
corner of the {object} is scuffed from use. Slightly lifted blacks, fine 35mm grain, no
vignette. Render this at a 16:9 aspect ratio."
*Follow-up if it misses:* "Keep everything identical but clear the left third
completely and lower the overall contrast a little."

### 2. Atmospheric background plate

**API.** `A photorealistic {texture/landscape/interior} filling the frame with no
distinct subject: {material or place}, seen {distance/angle}. The whole frame is calm
and low-contrast so text can sit anywhere over it. {Lighting}. {Palette, narrow}.
{Grain/processing}. Depth falls off gently toward the {top/edges}. {BIND}` +
`aspect_ratio: 21:9`.

**Chat.** "A photorealistic background plate with no distinct subject: {a wall of
weathered concrete / a field of low fog over grass / a dark walnut tabletop}, filling
the entire frame, seen straight on. Keep the whole image calm and low in contrast so
that white text stays readable anywhere over it. {Soft, even, diffused daylight with no
harsh shadow.} The palette stays within {two close colours}. Fine grain, no vignette,
gentle falloff toward the edges. Render this at a 21:9 aspect ratio."

### 3. Product / packshot

**API.** `A high-resolution, studio-lit product photograph of {product, named material
and finish} on {surface}. {Three-point softbox setup / single large softbox at 45
degrees from the left with a white bounce on the right}, {specular behaviour on the
product's surface}. {Camera: 100mm macro, f/8, straight-on at label height}. The
background is {seamless colour} with a soft gradient falloff. The label reads "{TEXT}"
in {font style}. {One honest imperfection: a faint fingerprint on the glass}. {BIND}` +
`aspect_ratio: 4:5`.
*(Google's own template: "A high-resolution, studio-lit product photograph of a
[product description] on a [background surface].")*

**Chat.** "A high-resolution, studio-lit product photograph of {a matte black ceramic
coffee cylinder with a brushed steel lid} standing on {a pale grey concrete slab}. Light
it with a single large softbox at 45 degrees from the left and a white bounce card on
the right, so the highlight runs down the left edge of the cylinder and the shadow falls
short and soft to the right. Shot on a 100mm macro lens at f/8, camera straight on at
label height. The background is a seamless warm grey with a gentle gradient falloff.
The label reads \"{ORIGIN 04}\" in a bold, condensed sans-serif. Leave one faint
fingerprint on the steel lid. Render this at a 4:5 aspect ratio."

### 4. Environmental portrait

**API.** `A photorealistic {medium/close-up} portrait of {specific person: age, role,
one distinguishing detail, what they are wearing described by material} in {their actual
workplace, named objects}. They are {doing something with their hands}, {gaze
direction}. Shot on {85mm portrait lens, f/2}. {Lighting: window light from camera-left,
soft, cool, mid-morning}. Visible pores and fine lines at the eye corners; {fabric}
shows real wear. Hands rest {position}, fingers relaxed. {Palette}. {Processing}.
{BIND}` + `aspect_ratio: 4:5`.

**Chat.** "A photorealistic medium portrait of {an elderly Japanese ceramicist with
clay-dusted forearms, wearing a faded indigo cotton apron} in {his own workshop, wheel
and drying racks behind him}. He is {steadying a half-thrown bowl}, looking down at his
hands rather than at the camera. Shot on an 85mm lens at f/2, so the racks behind him
fall gently out of focus while the shelves stay readable. Soft cool window light comes
from camera-left in the mid-morning. Show visible pores and fine lines at the corners of
his eyes; the apron is worn through at one pocket. His hands rest on the rim, fingers
relaxed. The palette stays earth brown, indigo and bone white. Slightly lifted blacks,
fine grain. Render this at a 4:5 aspect ratio."

### 5. Abstract texture / surface

**API.** `An extreme macro photograph of {material}, filling the frame, {angle}. The
surface shows {physical behaviour: how light scatters, grain direction, wear}. {Raking
light from {direction} at a shallow angle to bring out relief}. {Palette, 2 colours}.
Shot on {a 100mm macro at f/11 for even sharpness across the frame}. No object is
recognisable; the image reads as pure surface. {BIND}` + `aspect_ratio: 1:1`.

**Chat.** "An extreme macro photograph of {hand-torn cotton rag paper}, filling the
entire frame, seen straight on. Show how the fibres catch light at the torn edge and how
the surface dips where the sheet was pressed. Rake a hard light in from the lower left
at a shallow angle so the relief throws small, precise shadows. The palette stays bone
white and warm grey only. Shot on a 100mm macro lens at f/11, sharp corner to corner.
Nothing recognisable should appear; the image reads as pure surface. Render this at a
1:1 aspect ratio."

### 6. Editorial section image

**API.** `A photorealistic {shot} of {a specific moment that illustrates {concept}} -
{concrete scene, not a metaphor}. {Composition: subject off-centre on the {third},
foreground element cropped by the frame edge}. Shot on {35mm, f/4}. {Lighting}.
{Materials}. {Palette}. {One imperfection}. Candid rather than posed - captured as the
moment happens. {BIND}` + `aspect_ratio: 3:2`.

**Chat.** "A photorealistic candid photograph of {two engineers leaning over a laptop on
a cluttered workbench, one pointing at the screen mid-sentence}. Put them off-centre on
the right third and let a coil of cable in the foreground be cropped by the bottom edge.
Shot on a 35mm lens at f/4 from standing height. Overhead fluorescent light mixes with
warm light from a desk lamp on the right, so the colour temperature is uneven across the
frame. The bench is scratched MDF; one mug has left a ring. The palette stays cool grey,
warm oak and a single yellow accent. Nothing is posed - this is the moment as it
happens. Render this at a 3:2 aspect ratio."

### 7. Blog cover

**API.** `A photorealistic {shot} of {single concrete object or scene standing for
{topic}}, centred low in the frame with generous clear space above it for a title.
{Lighting: soft and even so type stays readable across the top}. {Palette limited to
{2 colours} plus {accent}}. Shot on {50mm, f/5.6}. Background is {flat surface}, unbroken
across the upper half. {One imperfection}. {BIND}` + `aspect_ratio: 16:9`.

**Chat.** "A photorealistic photograph of {a single brass key lying flat on a sheet of
grey linen}, placed low and slightly left of centre. Leave the entire upper half of the
frame as unbroken linen, evenly lit, so a title can sit across it. Soft, diffused
overhead light with no hard shadow. The palette is grey linen, warm brass and a single
deep green accent. Shot on a 50mm lens at f/5.6, straight down. One thread of the linen
is pulled loose near the bottom edge. Render this at a 16:9 aspect ratio."

### 8. Spot illustration in a set style

**API (Recraft preferred).** Create the style once from 1-10 approved illustrations ->
`style_id`. Then per asset: `A flat vector spot illustration of {single object or tiny
scene}, centred, on a plain {colour} background, no shadow. {One or two details that
make it specific}.` with `style_id={id}`, `size=1024x1024`, `negative_prompt` left for
watermark/border only.
**API (Gemini/FLUX).** Attach 1-3 approved illustrations as style references and add:
`Draw this in exactly the same illustration style as the attached images: same line
weight, same limited palette, same flat fills, same level of detail. {BIND}`

**Chat.** "A flat vector spot illustration of {a watering can tipped slightly forward,
one drop leaving the spout}, centred on a plain {cream} background with no shadow. Use
{three flat colours only: terracotta, sage and cream}, an even {2px} line weight with
rounded ends, and no gradients or texture. Keep the detail sparse - the shape reads at
32 pixels. Render this at a 1:1 aspect ratio."
*(For the rest of the set, attach the approved first illustration and add: "Match the
attached illustration exactly - same line weight, same three colours, same flat fills,
same level of detail. Only the object changes.")*

### 9. OG card plate (text set in code afterwards)

**API.** `A {photorealistic / abstract} plate for a social preview card: {simple subject
or texture} occupying the {right 40%} of the frame; the remaining {left 60%} is a flat,
evenly lit {colour} surface with no objects, no signage and no lettering. Low contrast
throughout so white type stays readable. {Lighting}. {Palette}. {BIND}` +
`aspect_ratio: 1.91:1` if supported, otherwise generate 16:9 and crop.
*Note: 1.91:1 is not in Gemini's documented ratio list - generate 16:9 at 2K and crop
to 1200x630 in code.*

**Chat.** "A photorealistic plate for a social preview card. Put {a single slate-grey
ceramic bowl} in the right 40 percent of the frame and leave the left 60 percent as a
flat, evenly lit {warm off-white} surface with nothing on it and no lettering anywhere
in the image. Keep contrast low throughout so white text stays readable over the left
side. Soft, diffused light from above and slightly right. The palette is warm off-white,
slate grey and one muted ochre accent. Render this at a 16:9 aspect ratio."
*Then: crop to 1200x630 and set the headline in HTML.*

### 10. Mascot (character consistency)

**API.** Turnaround first: `A {style} character design of {mascot: species/form, one
silhouette-defining feature, colour, material}, standing in a neutral pose, front view,
on a plain {colour} background. {Line/render style}. Full body, feet visible.` Then every
later pose passes that image as a **character reference**
(Gemini: up to 4-5 character images; Ideogram: exactly 1) with:
`The character in the attached image, now {new pose/action} in {new setting}. Keep the
character's proportions, colours, markings and expression style exactly as in the
reference; only the pose and background change.`

**Chat.** Turn 1: "A friendly flat-vector character design of {a round, moss-green
tortoise with an oversized hexagon-patterned shell and small round glasses}, standing in
a neutral pose facing front, full body with feet visible, on a plain cream background.
Use flat fills, a single even line weight and no gradients. Render this at a 1:1 aspect
ratio."
Turn 2 onward (attach the approved image): "Using the attached character, draw it {now
waving with one arm raised, standing beside a stack of books}. Keep its proportions,
colours, shell pattern, glasses and expression exactly as in the attached image - only
the pose and the background change. Same flat fills, same line weight, plain cream
background. Render this at a 1:1 aspect ratio."

---

### Set procedure (applies to all ten)

1. Freeze the style contract. Write it once.
2. Generate the hero. Iterate to approval with single-change follow-ups only.
3. Attach the approved hero to every remaining asset and append `{BIND}`.
4. On Recraft: build the `style_id` from the approved images and drop `{BIND}` prose.
5. Never change the style contract mid-set. If it has to change, regenerate all 8.
6. Accept nothing without running the section-6 checklist.
