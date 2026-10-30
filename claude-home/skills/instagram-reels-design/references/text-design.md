# Text design for 1080x1920 Reels (CapCut)

## Coordinate systems

CapCut transform units: **1.0 = half the canvas, +y is up**, (0, 0) is the centre.

| From CapCut to pixels (from the top-left) | From pixels to CapCut |
|---|---|
| `x_px = 540 * (1 + x)` | `x = x_px / 540 - 1` |
| `y_px = 960 * (1 - y)` | `y = 1 - y_px / 960` |

Examples: y +0.72 = 269 px from the top; y -0.17 = 1123 px; y -0.30 = 1248 px; y -0.56 = 1498 px; x +0.72 = 929 px.
Positions inside a compound clip multiply through the parent's scale and position; check the exported frame.

## Safe zones (Instagram Reels, 1080x1920)

Two tiers. Sources and verification status are in SKILL.md "Platform facts".

| Zone | Strict (Meta ads spec: top 14 %, bottom 35 %, sides 6 %) | Organic working zone (creator guides, UNVERIFIED) |
|---|---|---|
| Top UI (tabs, camera icon, "Reels") | 0 to 269 px (CapCut y above +0.72) | 0 to ~250 px |
| Bottom UI (username, caption, audio, progress bar) | 1248 to 1920 px (y below -0.30) | ~1500 to 1920 px (y below about -0.56) |
| Right column (like, comment, send, save, audio) | 1015 to 1080 px (x above +0.88) | ~930 to 1080 px from about y 900 px down (x above +0.72) |
| Left margin | 0 to 65 px (x below -0.88) | 0 to 65 px |
| Clean box | x 65 to 1015, y 269 to 1248 (950 x 979 px) | x 65 to 930, y 250 to 1500 |

**Rules**
- **Critical text (hook, key word, captions, prices, ratings) lives in the strict box.** Your current caption and title
  positions already do: subtitles at y -0.14 to -0.21 (1094 to 1162 px), titles at y -0.06 / -0.17 (1018 / 1123 px).
- **Decorative or redundant elements** (bottle PNGs, circle notes, b-roll banners) may use the organic zone, but nothing
  readable below 1500 px or right of 930 px in the lower half.
- **Flags from your projects** (fix when adapting for Instagram):
  - Bottle PNGs at y -0.45 to -0.70 (centre 1392 to 1632 px) dip into the caption area. Keep the PNG centre at or above
    y -0.45 and its lower edge above ~1500 px; scale down rather than slide down.
  - Circle-note videos at the bottom corners (y -0.41 to -0.76) sit under the username/caption text and, on the right,
    under the button column. For Instagram, lift them to y -0.30 to -0.45 or move the pair up to y +0.20 to +0.45
    when your face sits low in frame.
  - Logo top-right at y +0.72 (24 septiembre) is exactly on the top boundary: use y +0.60 to +0.65 and x no more than
    +0.60.
  - Caption y -0.43 (0925 project, 1373 px) is outside the strict box: move to y -0.15 to -0.25.
- TikTok differs: its right column is similar, its bottom UI is usually reported shorter than Meta's 35 %. Designing
  to Meta's strict box is safe for both.
- Overlay check: export a still (or use `qa-checklist.md` step 2) and lay a 1080x1920 safe-zone PNG over it.

## Type scale (pixel heights at 1080x1920)

CapCut's "size" field is not pixels. Calibrate once: put one line of each style on a black frame, export a PNG still,
measure the cap height of a capital "H" in pixels, and note "size 15 x scale 1.2 = N px" here. Until calibrated, judge
by the rendered frame against this scale:

| Role | Font (your system) | Font size on the frame | Case | Max words per card |
|---|---|---|---|---|
| Hook key word | Scholar Regular, neon + cream double layer, glow | 120 to 170 px | the word as written; ALL CAPS for a 1-word punch | 1 to 2 |
| Hook lead-in / support line | Montserrat Bold (white) or Montserrat Light | 60 to 80 px | sentence case | 2 to 4 |
| Subtitles / captions | Montserrat Bold, white, soft dark shadow | 56 to 72 px | sentence case; ALL CAPS only for ranking/reaction edits of 1 to 4 words | 3 to 6 (two lines max) |
| Captions (alternative serif) | Source Han Serif CN Heavy (your DJI projects) | 56 to 72 px | sentence case | 3 to 6 |
| Price / rating / number | Montserrat Bold, white | 80 to 120 px | "$180" / "10/10" | 1 to 3 |
| Notes / labels (notes pyramid, "top notes") | Montserrat Light | 44 to 56 px, never under 40 | lowercase or sentence case | 1 to 3 |
| Cover title | Scholar or Montserrat Bold | 110 to 160 px | short | 2 to 5 |

The WeAreNoCode kit used 88 to 110 px hero type for 9:16 Shorts and found 1040-px-wide screenshots unreadable on a
phone (it went to 1560 px on a 16:9 frame): when in doubt, bigger and fewer words.

**Line length:** at 64 px Montserrat Bold a line holds about 22 to 24 characters inside the 950 px strict box.
Captions: two lines at most, split at a phrase boundary, never leave one word alone on line 2.

**Reading speed:** title and support cards at most ~3 words per second of on-screen time (2-word card >= 0.7 s,
6-word card >= 2.0 s); the key word of a hook holds at least 0.8 s after its entrance ends. Captions synced to speech
may run up to ~4 words per second; above that, split the cue. Your projects average 3.7 to 7.7 words per subtitle over
1.3 to 2.3 s: 7-word cards shown for under ~1.8 s are too fast; split them into two cards.

## Case rules

- Sentence case reads fastest for captions longer than 4 words.
- ALL CAPS for one to three words, ranking labels, numbers with units ("100 ML").
- Never mix ALL CAPS and lowercase inside one caption card.
- Brand and perfume names keep their official spelling (Baccarat Rouge 540, Ilmin, Creed Aventus).
- Spanish: keep accents (más, también, olfato); check the font renders them (Scholar and Montserrat do; some display
  fonts drop "ñ").

## Colour pairs (from your presets) and contrast

Your two-layer key word (neon copy + cream copy revealed through "Dividir" masks) is the signature. Keep one pair per
video, at most two.

| Pair | Neon | Fill | Use |
|---|---|---|---|
| Violet -> cream (default) | #E11EFF | #FFF0E4 | brand/perfume name, hook key word |
| Light violet -> cream | #EB72FF | #FFF0E4 / #FFE6B6 | secondary key words |
| Violet -> amber | #E11EFF | #FFAD5B | badges: "Vegan", "Cruelty free", price drops |
| Pink -> peach | #FC8ED1 | #FFE1C4 | soft, feminine, gourmand reviews |
| Orange (warm fall) | #FF8600 / #FAAC7F | white | autumn / amber / woody themes |
| Support | #FFFFFF | (none) | lead-in, captions, prices |

Measured WCAG contrast ratios (computed for this skill):

| Colour | vs black | vs mid-grey #808080 | vs skin tone #C8A080 |
|---|---|---|---|
| #FFFFFF | 21.0 | 3.9 | 2.4 |
| #FFF0E4 | 18.8 | 3.5 | 2.1 |
| #E11EFF | 5.8 | 1.1 | 1.5 |
| #EB72FF | 8.4 | 1.6 | 1.0 |
| #7A00FF | 3.3 | 1.6 | 2.7 |
| #FF8600 | 8.7 | 1.6 | 1.0 |

What follows:
- **Neon colours have almost no contrast against mid-tone footage or skin (1.0 to 1.6).** They only read because of
  the dark shadow and the glow. Never place a neon word without a dark shadow (raise shadow alpha from your 0.30 to
  0.45 to 0.60 for Instagram, distance 4 to 6, slight blur) or a soft dark scrim behind the text block
  (black at 25 to 40 %, feathered).
- **Deep violet #7A00FF disappears on dark footage** (3.3:1 against black), the same lesson the WeAreNoCode kit
  learned with dark blue. Use it only as the glow tint or on bright backgrounds, never as the main fill on a dark room.
- **White and cream are the readable layers.** In the two-layer word, make sure the cream half covers at least half
  of each letter's height so the word still reads if the neon half drowns.
- **One accent colour per frame** for emphasis (neon on the key word); captions stay white.
- Avoid pure red on purple, and green/red pairs (colour-blind viewers).

## Glow and sparkle

- "neón brillante" (bloom): keep range around 0.3 and strength 0.25 to 0.35 (your preset values). Higher values blur
  the letter edges on a phone screen and lower legibility; never apply bloom to captions.
- "Brillo 2" sparkle: on the key word or the bottle PNG only, one sparkle element on screen at a time, luminance
  0.16 to 0.5. White sparkle text over a bright window or a white wall loses contrast: add the dark scrim.
- Sparkles and glows must not flash: sparkle cycles under 3 flashes per second (see qa-checklist.md, flash check).

## Layout patterns (positions in CapCut units)

| Pattern | Position | Notes |
|---|---|---|
| Caption line | x 0, y -0.15 to -0.25 | your default; inside the strict box |
| Hook title stack | lead-in y -0.06, key word y -0.17 | the key word below the face, above the caption |
| Price / rating card | x 0, y -0.06 to +0.10 | swap with the caption, never both at the same height |
| Bottle PNG (single) | x 0 to +0.10, y -0.30 to -0.45, scale 0.4 to 0.7 | fade 0.5 s, small x drift |
| Bottle PNG pair (vs / dupe) | x -0.45 and +0.40, y -0.30 to -0.40 | keep the right one left of x +0.60 |
| Ranking row (3 slots) | x -0.52 / 0 / +0.50, y -0.30 to -0.40 | your 24 septiembre row moved up from y -0.70 |
| Logo / brand mark | x up to +0.60, y +0.55 to +0.65 | not in the top UI band |
| Rectangle b-roll pair | x -0.40 / +0.42, y +0.38 to +0.50 | upper half, clear of the top band |
| Circle notes pair | x -0.45 / +0.30, y -0.30 to -0.45 or y +0.20 to +0.45 | raised from the bottom corners |

Never cover your face or the bottle with text; when copy does not fit the safe box, shorten it or make it a caption
line, do not shrink it below the type scale.
