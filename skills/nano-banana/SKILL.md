---
name: nano-banana
description: >
  Generate hyper-realistic, tightly-controlled images (product shots, hero frames, brand imagery, blog
  images) using Google's Nano Banana (Gemini image model) via structured JSON prompting that neutralizes
  the plastic "AI look." Use in /brand-system (mascot/logo/imagery - replaces the manual step) and for
  /new-site + content-ops assets. Runs on the Gemini API (AI Studio key) or manually in the Gemini app.
---

# Nano Banana - controlled realistic image generation

Nano Banana = Google's Gemini image model. The value here is the **structured prompt method** that forces
optical realism and strips AI-averaging - adapted from the local reference to run on **Google's own Gemini
API** (the user has a Gemini subscription + can use an AI Studio key), not a reseller.

## Three ways to run
1. **Manual (free, uses the Gemini subscription):** paste the dense prompt into the Gemini app / AI Studio,
   download the PNG. Good for low volume. No key needed.
2. **Gemini API (automated):** `scripts/generate_gemini.py` (below) with a **Google AI Studio API key** in
   `GEMINI_API_KEY`. Free tier, then pay-per-image. This is the default for batch/asset work.
3. **kie.ai (optional cheaper backend):** the local `generate_kie.py`/`get_kie_image.py` in `~/Downloads/temp`
   still work if you ever want kie's per-image pricing or its video models.

## The method - structured prompting for realism
Build a **dense narrative prompt** with explicit optics + flaws (this is what kills the plastic look):
- **Camera math:** exact focal length / aperture / ISO (e.g. `85mm, f/1.8, ISO 200`). Keep ISO < 800.
- **Explicit imperfections:** `visible pores, mild redness, subtle freckles` (people); `micro-scratches on
  anodized aluminum, subsurface scattering through dew` (products/nature).
- **Lighting behavior:** name what the light *does* ("direct on-camera flash, sharp highlights, shadowed bg").
- **Direct negative commands inside the positive prompt:** "Do not beautify or alter features. No makeup."
- **A negative-prompt stack:** `plastic skin, skin smoothing, anatomy normalization, dataset-average anatomy,
  beautification filters, airbrushed texture, stylized realism`.
- For products/brand imagery, replace skin logic with **material physics** + clean typography for flat-lays.

Full schema + multi-panel grids: the local `~/Downloads/temp/master_prompt_reference.md` (JSON schema) and
`Nano Banana 2.md` (the two prompt paradigms). Keep those as the deep reference.

## Wired into
- `/brand-system` - mascot / logo source imagery / brand photography (replaces today's manual Nano Banana step;
  post-process a logo through `vtracer` as before).
- `/new-site` + `content-ops` - hero images, section imagery, blog cover/inline images.

## Notes
- Confirm the current model id in AI Studio (Nano Banana = `gemini-2.5-flash-image`; Pro tier is a newer id) -
  it's a single variable in the script.
- Prefer physical subject imperfections over heavy camera noise (noise triggers the "illustration" bias).
