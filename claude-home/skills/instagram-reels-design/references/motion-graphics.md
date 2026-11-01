# Motion system for perfume Reels (CapCut)

Built from two sources: the timings measured in your own CapCut projects and presets (Sept to Oct 2026), and the
motion rules of the WeAreNoCode YouTube editor (MIT; rules re-expressed here for CapCut, no code reused).

## 1. The timing system: in / hold / out

| Element | In | Hold | Out | CapCut animation |
|---|---|---|---|---|
| Card wrapper (title, PNG, b-roll preset) | 0.5 s fade | D - 1.0 s | 0.5 s fade | "Aparición progresiva" / "Desaparición progresiva" |
| Title word inside a card | 0.13 s (4 frames) | until the wrapper fades | none (wrapper fades it) | "Tipo 2" for the key word, "Aparición progresiva" 0.13 s for lead-in words |
| Soft text entrance (notes, labels) | 0.47 to 0.5 s | | | "Onda hacia dentro" |
| Caption card | caption anim over the card | 1.3 to 2.3 s | cut to next | "Rebote hacia fuera" (your default) |
| Card "life" (whole card) | | 1.2 to 4.3 s total (median ~2.8 s) | | group anim stretched to full length: "Caramelo explosivo", "Zoom 2", "Péndulo 1/2", "Caída hacia…" |
| Bottle PNG | 0.5 s fade + x drift -0.046 -> 0 | 2.6 to 2.8 s with slow drift | 0.5 s fade + x drift 0 -> +0.046 | starts 0.5 to 0.65 s after its text card |
| Circle-note video | 0.43 s slide/fade | 1.1 to 2.4 s | 0.5 s | pairs start 0.1 to 1.1 s apart |
| Rect b-roll (top banner / pair) | 0.43 to 0.5 s | 1.3 to 5.0 s | 0.5 to 0.9 s | "Caída hacia la derecha/izquierda" |

Reference timings from the WeAreNoCode kit (16:9 YouTube, quieter style): entrances 0.40 s ease-out, exits 0.35 s
ease-in, cards hold 3 to 7 s, beyond 7 s a card needs internal motion. Your 0.5 / 0.5 s fades sit close to that;
keep them.

**Timing against speech**
- An element enters **0.10 to 0.25 s before** the word it belongs to (never after, never more than 0.6 s before).
  The kit enforced this with a script (`beat-check.py`, not copied: it reads HyperFrames HTML); in CapCut, check it by
  scrubbing: the text must be fully readable when the word is spoken.
- A word-by-word title cascade: chunks staggered 0.2 to 0.6 s (your hook: 0.0 / 0.2-0.5 / 0.7-1.1 / 1.4-1.6 s).
- The picture payoff (PNG, b-roll) lands 0.5 to 1.8 s after the text that names it. Text first, then picture.
- SFX start on the element's start frame; align the audible peak (trim leading silence from the SFX), not the file
  start, to within two frames.

## 2. Easing

| Motion | Ease | CapCut |
|---|---|---|
| Entrances (slide, scale-in) | ease-out (fast start, soft landing) | keyframe curve "FreeCurveOut" or a preset in-animation |
| Exits | ease-in | "FreeCurveIn" or a preset out-animation |
| Camera zoom ramps, slow drifts | ease-in-out | "FreeCurveInOut" |
| Settle / hold keyframes | linear | "Line" |

- **One gesture, not two moves.** Two consecutive moves on one subject read as a glitch: merge them into one ramp.
- A front-loaded ease on visible footage (fast then crawl) feels like a jump; use ease-in-out for anything that moves
  the whole frame.

## 3. Camera (zoom on the talking head)

Your template (6/6 projects): 100 % at 0 s -> 102.6 % at 1.27 s -> 106.4 % at 2.27 s -> 100 % at 4.5 s, then alternating
ramps: zoom-in 1.0 to 2.1 s (+3 to +6 points), zoom-out 1.9 to 2.7 s; peaks 103 to 110 %, one 117.8 % emphasis peak
around once a minute; never above 118 %, no position/rotation keyframes.

Keep it; add these rules:
- Anchor zooms so the head is never cropped: on a centred framing, zoom from the upper third (the kit always anchored
  zoom at the top edge). In CapCut, when the head gets near the top, add a small negative y on the zoomed compound.
- 1080p footage goes soft above ~112 %; 4K holds 150 % or more. Your DJI / camera footage: check the source resolution
  before using the 117.8 % peak.
- Do not start a punch-in within 0.3 s of a jump cut; let the cut do the work.
- Budget in a 30 to 60 s Reel: 1 slow ramp per 2 to 4 s is your rhythm; a fast punch (118 to 125 % in 0.3 s) at most
  once per 15 s, on the punchline or the price.

## 4. Staggering and layering

- Stagger multiple items of a group 0.1 to 0.6 s apart (circle-note pairs 0.1 to 1.1 s, title chunks 0.2 to 0.6 s,
  ranking bottles one per mention).
- **One hero element at a time.** At most one element at full brightness; a caption may coexist with one card or one
  PNG. Your projects peak at 3 to 6 simultaneous overlays; on Instagram's smaller clean box, cap it at 3.
- Subject in front of graphics (cutout duplicate of the head on a higher track, same zoom keyframes, muted): use it
  for the hook and for one or two big moments, not every card.

## 5. Layout rotation (variety)

Never use the same device twice in a row (the kit's composer warned on every repeat). Rotate through:

1. Neon title card (Scholar key word, two colours, Dividir reveal, "Caramelo explosivo")
2. Bottle PNG cutout with name card
3. Support text (white Montserrat Bold, "Zoom hacia la derecha")
4. Price / rating card
5. Rectangle b-roll pair (top-left + top-right) or top banner
6. Circle-note pair
7. Full-screen b-roll (hard cut, 1.1 to 3.5 s)
8. Ranking row / vs split (two bottles)
9. Notes pyramid (top / heart / base as three short labels arriving on their words)

Rules of thumb:
- After a full-screen b-roll, come back on your face for at least 1.5 s before the next full-screen insert.
- A list ("top notes are bergamot, pear and amber") becomes one device whose items appear on their words, not three
  separate cards.
- If the frame already says it (the label on the bottle is readable), do not write it again.

## 6. Density per minute

| Format | Your measured density | Recommended for Instagram |
|---|---|---|
| Review (1 perfume) | 20 to 26 overlay events/min, a new element every 2.1 to 2.8 s | 15 to 25 events/min; every 2 to 4 s something changes |
| Ranking / reaction | 30 to 61 events/min, every 1.0 to 2.0 s | 30 to 45/min, but fewer simultaneous items (max 3) |
| Cuts on the talking head | review 15 to 28/min, reaction 33 to 49/min | keep; first cut after the hook take (2 to 4 s) |
| SFX | 15 to 45/min | 10 to 25/min (see "Sound" below) |

Static-stretch rule (adapted from the kit's `gap-scan.py`): no stretch without a cut, a new element or a camera move
longer than **3 s in the first 15 s**, **5 s after that**, **8 s ever**.

## 7. Sound under motion

- One SFX per text chunk, not one per word; keep the Pop/Click at 0.3 to 0.55 volume, finger snap only on the key word.
- Swooshes: on a picture moving across the frame (b-roll banner, PNG falling in), never under plain text.
- Music: one track, 3 to 13 % volume in CapCut (your range); on Instagram, if you use a library sound added in the app,
  mute or remove the CapCut music first to avoid two beds.

## 8. What to avoid

- **Flash transitions in series** ("Flash cálido" every 0.33 s in the 1006 montage): more than 3 bright flashes per
  second is a photosensitivity risk and reads as a mistake (the kit rejected flash cuts outright). Use at most one
  flash, or hard cuts with the camera-shutter click.
- Bouncy animation on two elements at once (captions already bounce: keep titles on fades/"Tipo 2").
- Animating blur or glow intensity (shimmers on a phone look like compression noise).
- Idle wobble on every card ("Péndulo" on a card that holds over 3 s): use it on one card per section.
- Text sliding in from off-screen through the UI bands (top 269 px, bottom 672 px).
- Transitions that hide the bottle at the moment you name it.
- Carrying a fast punch-in across a jump cut.
- TikTok-downloaded clips with watermarks (Instagram reportedly down-ranks them) and footage that is not yours as
  the main content (originality rules).

## 9. New device checklist (state sheet)

Before building a new CapCut preset, write its states (from the kit's "state sheet" rule):
- every state: what is on screen, where (CapCut x/y), size, colour;
- every change: what moves, the property, the curve, the duration;
- save it as a preset ("Mis elementos predefinidos N") only after one snapshot of each state reads correctly on a phone.
