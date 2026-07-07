---
name: video-to-website
description: >
  Turn a video into a premium scroll-driven animated hero/section for a client Astro site - ffmpeg frame
  extraction bound to scroll on a canvas, with GSAP + Lenis choreography (multiple animation types, not one
  repeated effect). Adapted to the Astro + Cloudflare stack (island/script, frames in public/ or R2, no
  Vercel). Use in /new-site (premium hero) and /design. Pairs with Cling/Kling for the source video.
---

# Video to premium scroll-driven website (Astro/Cloudflare)

Turn a video into a scroll-experience hero: extract frames, bind them to scroll on a `<canvas>`, and layer
GSAP + Lenis animation choreography. Adapted from the original vanilla build to **our Astro + Cloudflare
stack** - use `astro-patterns` (islands, `astro:assets`) and `frontend-design` for the styling. Source video
comes from Cling/Kling (GPT-Image start/end frames -> AI video), or a real product clip.

## Premium checklist (non-negotiable)
1. **Lenis smooth scroll** (feels like an experience, not a page).
2. **4+ animation types**, never the same entrance twice in a row (fade-up / slide-left / slide-right /
   scale-up / rotate-in / stagger-up / clip-reveal).
3. **Staggered reveals** (label -> heading -> body -> CTA), never all at once.
4. **No glassmorphism cards** - hierarchy via type scale/weight/color on clean backgrounds.
5. **Direction variety**, **counter animations** (numbers count up from 0), **one oversized text marquee**
   (12vw+ sliding on scroll).
6. **Massive type** (hero 12rem+, headings 4rem+), **side-aligned text only** (outer 40% zones; product owns
   center) - exception: a stats section under a 0.88-0.92 dark overlay.
7. **Circle-wipe hero reveal** (`clip-path: circle()` as the standalone 100vh hero scrolls away).
8. **Generous scroll** (hero 20%+, 800vh+ total for ~6 sections). **Frame speed 1.8-2.2** (product animation
   done by ~55% scroll).

## Astro/Cloudflare integration (what changed from the original)
- **No bundler-free vanilla page + no Vercel.** Build it inside the client's Astro repo.
- **Frames:** extract to `public/frames/frame_%04d.webp` (served as static assets). For large sets, put them
  in **R2** and serve via the engine's `/media` route (which already does optimized delivery). 150-300 frames.
- **The scroll component:** a single client island - either a `.astro` page with an inline `<script>` or a
  small `client:load` component. GSAP + Lenis via `astro:assets`-friendly imports or CDN in the island only
  (keep the rest of the site static per `astro-patterns` - hydrate on purpose).
- **Deploy:** Cloudflare (Workers/Pages) via the normal `/new-site` deploy - NOT Vercel.
- **CSP:** if using CDN scripts, add them to the site CSP (see `astro-patterns` CSP-with-islands).

## Workflow
1. **Analyze:** `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration,r_frame_rate,nb_frames -of csv=p=0 VIDEO`.
   Target 150-300 frames (short <10s: original fps cap ~300; 10-30s: 10-15fps; 30s+: 5-10fps). Cap width 1920.
2. **Extract:** `ffmpeg -i VIDEO -vf "fps=FPS,scale=W:-1" -c:v libwebp -quality 80 public/frames/frame_%04d.webp`.
3. **Scaffold** the island: loader, fixed header, standalone hero (word-split heading), fixed `<canvas>`,
   dark overlay, marquee, and an 800vh+ scroll container with sections carrying `data-enter`/`data-leave`/
   `data-animation`.
4. **Wire the JS** (in the island): Lenis + GSAP ticker; two-phase frame preloader; canvas "padded cover"
   renderer (`IMAGE_SCALE` 0.82-0.90, sample bg color from frame edges); frame-to-scroll `ScrollTrigger`
   (`scrub:true`, `FRAME_SPEED` 2.0); per-section entrance timelines by `data-animation`; counters; marquee;
   dark overlay; circle-wipe hero. (Same technique as the original reference - the full animation code lives
   in `~/Downloads/temp/Video to Website.md` if you need the exact GSAP snippets.)
5. **Style** with `frontend-design` (distinctive, per brand). Mobile <768px: collapse side-align to centered
   with dark backdrops, reduce to ~550vh, frames <150 / 1280px.
6. **Test** on `astro dev`, then deploy to Cloudflare.

## Anti-patterns
Cycling cards in one pinned section (give each feature its own scroll section), pure cover mode (product
clips into header), FRAME_SPEED < 1.8 (sluggish), same animation back-to-back, scroll < 800vh for 6 sections,
serving frames from `file://` (must be HTTP). Keep the rest of the site static - this island is the exception.
