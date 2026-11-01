---
name: instagram-reels-design
description: Instagram Reels design layer for CapCut perfume and beauty videos. Covers platform rules (1080x1920, UI safe zones in px and CapCut units, length, cover/grid crop, captions, audio, 5-hashtag limit, ranking signals), hook writing in Spanish and English, on-screen text design (type scale, colour pairs, contrast, glow/sparkle), motion-graphics timing (in/hold/out, easing, stagger, density) and a pre-post QA checklist (safe-zone overlay, reading speed, flash check, -14 LUFS). Use when the user wants to adapt, design, review or QA a Reel or vertical video for Instagram, or says "Instagram", "Reel", "IG", "safe zone", "hook", "gancho", "texto en pantalla", "subtítulos", "portada", "cover", "hashtags", "animación de texto", "motion graphics", "is this ready to post", or asks how a TikTok edit should change for Instagram. For the full perfume edit pipeline (cutting, b-roll, presets), use the perfume-reel skill alongside this one.
---

# Instagram Reels design (CapCut, perfume niche)

The Instagram-specific layer for the user's perfume-review Reels: platform rules plus a text, hook and motion design
system tuned to their CapCut style. It does not cut footage or build the whole edit: the **perfume-reel** skill
(`~/.claude/skills/perfume-reel/`) owns the full pipeline. Use this one to make an edit right *for Instagram*.

| Need | Read |
|---|---|
| Write or judge a hook (ES/EN formulas, the 3-second structure) | `references/hooks.md` |
| Text sizes, positions, safe zones in px and CapCut units, colours, contrast | `references/text-design.md` |
| Animation timing, easing, staggering, layout rotation, density | `references/motion-graphics.md` |
| Check an export before posting | `references/qa-checklist.md` |

## The user's house style (measured from their CapCut projects, Sept to Oct 2026)

Keep these as defaults; change only what Instagram requires.
- Canvas 1080x1920, 30 fps; filter "Nativo" + one Adjust layer; talking head in one compound clip carrying the zoom.
- Fonts: **Scholar Regular** (key/hero words), **Montserrat Bold** (white support text, captions), **Montserrat Light**
  (notes/labels); Source Han Serif CN Heavy captions in some DJI videos.
- Two-colour neon key words: two stacked copies (neon + cream) revealed by "Dividir" masks, glow "neón brillante";
  default pair **#E11EFF + #FFF0E4**; also #EB72FF/#FFF0E4, #E11EFF/#FFAD5B, #FC8ED1/#FFE1C4.
- White sparkle ("Brillo 2") on hooks and bottle PNGs.
- Timing: wrapper fades 0.5 s in / 0.5 s out ("Aparición / Desaparición progresiva"); key word "Tipo 2" 0.13 s;
  lead-in words "Aparición progresiva" 0.13 s; group animations stretched over the card: "Caramelo explosivo",
  "Zoom 2", "Péndulo 1/2", "Caída hacia…"; captions "Rebote hacia fuera".
- Captions white, soft shadow, centred at CapCut y -0.14 to -0.21.
- Bottle PNG cutouts (auto background removal), circle-masked note videos in pairs, rectangle b-roll pairs/banners,
  cutout of the subject in front of b-roll.
- Zoom template 100 -> 102.6 -> 106.4 -> 100 % (0 / 1.27 / 2.27 / 4.5 s), peaks 103 to 110 %, max 117.8 %.
- Cuts: review edits every 2 to 3.7 s, reaction/ranking every 1.2 to 1.8 s; the hook is one take (first cut at ~2.8 s).
- SFX inside presets: Pop (low), Switch/Click, finger snap on the key word, Title Swoosh on pictures. Music one looped
  track at 3 to 13 % volume.

**CapCut units:** 1.0 = half the canvas, +y is up. `x_px = 540 * (1 + x)`, `y_px_from_top = 960 * (1 - y)`.

## Platform facts (checked October 2026)

Verified = read on an official Meta page or a direct report of an official statement. UNVERIFIED = third-party guides
only; treat as a working assumption.

| Topic | Fact | Status / source |
|---|---|---|
| Format | 9:16, 1080x1920; MP4/MOV, H.264, AAC, constant frame rate; 30 fps typical | Meta ads spec (verified); fps figure UNVERIFIED [1][2] |
| Max length | Reels up to 3 min since Jan 2025 | verified [3]; whether >90 s reaches fewer people: UNVERIFIED [4] |
| Safe zone, strict | keep text/logos out of top 14 % (269 px), bottom 35 % (672 px), sides 6 % (65 px) | Meta ads spec, verified [1] |
| Safe zone, organic | top ~250 px, bottom ~320 to 420 px, right buttons ~100 to 230 px | creator guides, UNVERIFIED [5] |
| Grid / cover | profile grid shows a taller rectangle since Jan 2025; guides give 3:4 (1080x1440, centred) | change verified [3]; exact 3:4 UNVERIFIED [6] |
| Ranking signals | Mosseri (Jan 2025): watch time, likes per reach, sends per reach are the top three; sends matter most for non-followers | verified via report [7] |
| Hook | Mosseri (Mar 2025): "the first three seconds of a reel are super important" | verified via report [8] |
| Length for engagement | under 15 s ~57 % completion vs ~36 % over 60 s; 15 to 30 s best engagement | third-party benchmarks, UNVERIFIED; nothing fragrance-specific [9] |
| Trial Reels | professional accounts can show a Reel to non-followers first and see results after ~24 h | verified via report [10] |
| Originality | accounts that mostly repost others' content are not recommended to non-followers (extended in 2026) | verified via report [11] |
| Watermarks | Reels with other apps' logos/watermarks (TikTok) or low resolution are less discoverable; avoid borders and Reels mostly covered by text | Instagram guidance 2021, verified via report [12] |
| Captions | subtitles "optional but recommended", sound "strongly recommended" (ads spec); in-app Captions sticker auto-transcribes; viewers can toggle auto-captions | verified [1]; app features via reports [13] |
| Text size / contrast | no official minimum | none found; this skill uses WCAG 4.5:1 as a target |
| Music | Business accounts are limited to Meta's commercially cleared library; creator accounts get the full library for non-commercial use; ads: use original or royalty-free audio | ads guidance verified [1]; account rules UNVERIFIED [14] |
| Edits app | Meta's free editor (Apr 2025): no watermark export, auto captions, skip-rate insights | verified via report [15] |
| Hashtags | max **5** per post/Reel since Dec 2025; Instagram advises fewer, targeted tags, not #reels/#explore | verified [16][17]; whether first-comment tags count: UNVERIFIED |
| Search | since 10 Jul 2025 public professional-account posts can be indexed by Google/Bing (opt-out available) | verified via report [18] |
| vs TikTok | TikTok skews 13 to 24, Reels stronger among 25+; TikTok tests every video on non-followers and re-tests old videos; Instagram weighs relationships and account history; Meta's 35 % bottom zone is larger than most TikTok figures | directional, UNVERIFIED [19][9] |

Sources: [1] facebook.com/business/ads-guide/update/video/instagram-reels · [2] postfa.st/sizes/instagram/reels ·
[3] engadget.com (3-minute Reels and rectangular grids, Jan 2025) · [4] onlinemarketing.de/social-media-marketing/instagram-erlaubt-laengere-reels ·
[5] inro.social/tools/instagram-reels-safe-zone-checker, postplanify.com/blog/social-media-safe-zones-2026-complete-guide ·
[6] hopperhq.com/blog/instagram-reel-size · [7] socialsamosa.com/news-2/instagram-reveals-key-factors-for-boosting-reach-8646916 ·
[8] news.inman.com/2025/03/07/head-of-instagram-reveals-secrets-to-social-media-success · [9] blitzcutai.com/blog/instagram-reels-vs-tiktok ·
[10] lindseygamble.com (Trial Reels) · [11] petapixel.com/2026/04/30/new-instagram-policies-target-reposted-content ·
[12] tubefilter.com/2021/02/10/instagram-reels-with-tiktok-watermark-less-discoverable · [13] kapwing.com/resources/instagram-reels-captions ·
[14] hellothematic.com/music-rules-tiktok-instagram-youtube · [15] smallbiztrends.com (Meta launches Edits) ·
[16] socialmediatoday.com/news/instagram-implements-new-limits-on-hashtag-use/808309 · [17] socialsamosa.com/news-2/instagram-hashtags-five-per-post-10923075 ·
[18] ppc.land/instagram-content-becomes-searchable-on-google-starting-july-10 · [19] benly.ai/learn/tiktok-ads/tiktok-vs-instagram-reels-2026

Re-check the UNVERIFIED rows when a decision depends on them; platform UI and rules change often.

## Checklist: adapt a perfume video for Instagram

Work through it in order; each step points to its reference.

### 1. Length and structure
- [ ] Target **15 to 45 s** for a single-perfume review or a hook-driven clip; 45 to 90 s for rankings, unboxings and
      trips; past 90 s only when the story holds (and accept possibly lower reach). Your current edits run 55 to 137 s:
      cut a 30 to 45 s Instagram version first, post the long one as a second Reel or a carousel follow-up.
- [ ] Shape: hook (0 to 3 s) -> promise / name (3 to 8 s) -> 2 to 4 proof beats (notes, performance, compliments,
      price) -> verdict -> one CTA (save / send / follow). Close the hook's question before the CTA.
- [ ] Design for **sends and saves**: lists, "if you like X", dupes, season picks and prices are what people forward
      or keep. Say "guárdalo / save this" only after delivering the useful part.

### 2. Hook (references/hooks.md)
- [ ] Frame 0 meaningful; promise readable muted; one take for the first 2 to 3 s.
- [ ] 3 to 9 words of hook copy in 2 to 4 chunks; neon key word on screen at 0.7 to 1.1 s; picture payoff at 2.3 to 3 s.
- [ ] Pick the formula (curiosity, contrast, "si te gusta X", compliments, dupe, season, ranking, price…).

### 3. Safe zones (references/text-design.md)
- [ ] Critical text inside the strict box: x 65 to 1015 px, y 269 to 1248 px (CapCut x within ±0.88, y between +0.72
      and -0.30).
- [ ] Nothing readable below ~1500 px (y -0.56) or right of ~930 px (x +0.72) in the lower half.
- [ ] Move your bottom-corner circle notes and low bottle PNGs (y -0.45 to -0.76) up; logo top-right down to y +0.60.

### 4. Text (references/text-design.md)
- [ ] Captions 56 to 72 px on the frame, white, sentence case, two lines max, about 22 to 24 characters per line.
- [ ] Reading speed: cards ≤ 3 words/s; speech captions ≤ ~4 words/s.
- [ ] One accent pair per video (default #E11EFF + #FFF0E4); dark shadow alpha 0.45 to 0.60 behind every neon word.
- [ ] Burn captions in (most viewers start muted) or turn on Instagram auto-captions; never both visible at once.

### 5. Motion (references/motion-graphics.md)
- [ ] Entrances 0.10 to 0.25 s before their word; 0.5 s fades; key word 0.13 s "Tipo 2".
- [ ] No device twice in a row; one hero element at a time, max 3 overlays at once.
- [ ] Nothing static longer than 3 s in the first 15 s, 5 s afterwards.
- [ ] No strobe: at most one "Flash cálido", never a chain of flashes (≤ 3 flashes per second).

### 6. Audio
- [ ] Voice levelled to about -14 LUFS integrated, true peak ≤ -1 dBTP (qa-checklist.md step 7).
- [ ] Choose one: **original audio** (your voice + CapCut music at 3 to 13 %) or **an Instagram library track**
      added at upload (then export from CapCut with the music muted). Business accounts: only the commercially
      cleared library. Trending audio can help discovery but is not a confirmed ranking factor (UNVERIFIED); the
      verified signals are watch time, likes and sends.
- [ ] SFX: one per text chunk, no whoosh under plain text.

### 7. Cover
- [ ] Pick a frame or upload a 1080x1920 cover: bottle + face + a 2 to 5 word title (Scholar key word or Montserrat
      Bold, 110 to 160 px).
- [ ] Title and face inside the centred 1080x1440 grid crop (CapCut y +0.75 to -0.75), ideally 1080x1350
      (y +0.70 to -0.70); nothing important in the top/bottom 240 px.
- [ ] Keep covers consistent across the grid (same font, same position, same colour pair).

### 8. Caption, hashtags, posting
- [ ] First line = the hook in words (it shows before "more"); then 1 to 3 lines with searchable keywords: perfume
      and brand name, notes, "dupe", "reseña / review", season, price.
- [ ] Up to **5** specific hashtags (mix: niche + product + language), e.g. #perfumereview #reseñadeperfumes
      #vanillaperfume #perfumesarabes #ilmin. No #reels / #fyp / #explore.
- [ ] Tag the brand; "Paid partnership" label when gifted or paid.
- [ ] Optional: post as a **Trial Reel** to test a second hook on non-followers.
- [ ] Export clean from CapCut (no CapCut/TikTok watermark or end card). If the TikTok version had TikTok-only text
      ("link in bio" pointing to TikTok, duet prompts), remove it.

### 9. QA (references/qa-checklist.md)
- [ ] Contact sheet, safe-zone overlay sheet, reading speed, contrast, flash check, loudness, black frames.

## TikTok vs Instagram: what to change when re-using an edit

| | TikTok version | Instagram version |
|---|---|---|
| Bottom UI | shorter (third-party figures vary) | bigger: strict 35 % (672 px); move low elements up |
| Opening | can be faster, more chaotic | same fast hook, but a cleaner first frame works as the cover too |
| Length | longer storytime tolerated | 15 to 45 s first; long version optional |
| Audience | younger (13 to 24 skew) | 25+ stronger: price/value, quality, office/date use cases land well |
| Text | trend phrasing, slang | clearer, searchable wording (captions are indexed) |
| Hashtags | more allowed | 5 max |
| Watermark | n/a | must be clean (no TikTok logo) |
| Circle-note clips from TikTok | common | only short, credited, watermark-free; your own footage is safer for originality ranking |

## Optional scripts (`scripts/`, not run by default)

Copied unchanged from the WeAreNoCode YouTube Editor kit (MIT; licence in `scripts/LICENSE-MIT-starter-kit.txt`,
copyright notice "Nate Herk", the kit's starter-kit author). They expect the kit's file layout; adapt the inputs as
described. Run Python with `-I` and read a script before running it on new data.

| Script | What it is good for here | Needs | How to feed it from CapCut |
|---|---|---|---|
| `dead-air.py` | lists pauses over 0.40 s after a sentence end (0.45 s elsewhere) in the talking-head audio, with a proposed range to remove | Python 3, numpy | a folder with `audio.wav` (16 kHz mono export of the edited voice), `transcript.json` (word-level `{words:[{text,start,end}]}` from any transcriber) and `cut-map.json` (`{"cuts": [], "flat_duration": <seconds>}`); ignore the `patch-cut.py` hints and cut by hand in CapCut |
| `stutter-scan.py` + `find-cut-candidates.mjs` | word repeats ("the the"), retakes and false starts as a review list | Python 3, Node.js | `--transcript transcript.json --out-dir candidates/`; stop-word list is English and accented letters are trimmed at word edges, so Spanish results are rougher |
| `verify-render.py` | checks the exported file: resolution, black frames/flashes, A/V length, bitrate, a frame sheet | Python 3, ffmpeg/ffprobe | `--render reel.mp4 --res 1080x1920 --min-mbps 24`; its BT.709 tag check may fail on CapCut exports (informational) |
| `teardown.py` | measures a reference Reel you admire (or your own): hard cuts per minute, bursts, quietest stretches, loudness, contact sheets | Python 3, ffmpeg/ffprobe | `--video ref.mp4 --out teardown/ref/` (only on videos you are allowed to download; `--storyboard` mode is HyperFrames-only) |

Written for this skill (stdlib only): `caption-speed.py` (words per second per SRT cue) and `flash-check.py` (flash
heuristic from an ffmpeg luma dump); usage in `references/qa-checklist.md`.

## What was taken from the WeAreNoCode kit, and what was not

Reused as ideas (re-written for CapCut and Instagram): the hook gate (frame 0, muted promise, first word protected,
payoff time, one open loop); text entering 0.1 to 0.25 s before its word; one hero element at a time; never the same
device twice; one gesture instead of two moves; static-stretch limits and density budgets; zoom anchored so the head
is never cropped; "if the frame already says it, don't write it"; sound must have a cause on screen, never a whoosh
under text; dead-colour lesson (dark blue vanishing on dark footage = deep violet here); check the exported file, not
the timeline (contact sheet, black frames, loudness -14 LUFS, true peak -1); state sheets before building a new
device; "save this to the skill" learning loop. Its Shorts note (hero type 88 to 110 px, word-exact captions, a reason
to stay in 3 s) informed the type scale.

Not reused (YouTube / long-form / tool-specific): the HyperFrames + GSAP composer, storyboard JSON and its 40+ HTML
formats; glass cards and the DM Sans look (the user has their own fonts and presets); Tella screen-tutorial route;
4K / BT.709 / 45 Mb/s mastering and chapter assembly; Parakeet + auto-editor raw-take cut pipeline (paper-cut,
hand-cut, tighten, sliver, edge-audit, apply-cut); stock/AI b-roll sourcing for 16:9; YouTube end screens, subscribe
bars and description pointers; the strict "no bounces, silence by default" taste (softened: the user's bounce
captions and preset SFX are their style, kept within limits).

## Keeping the skill current

- When the user gives a note worth keeping ("the price text is too small", "move the bottles higher"), add it as one
  plain rule in the matching reference file; replace an old rule rather than keeping both.
- When Instagram changes a rule (safe zones, hashtag limit, length), update the "Platform facts" table with the date and
  the source, and mark it verified or UNVERIFIED.
- New CapCut preset worth reusing: add its timings to `motion-graphics.md` and its positions to `text-design.md`.
