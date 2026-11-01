# QA checklist before posting a Reel

Adapted from the WeAreNoCode YouTube editor's "verify and deliver" stage (MIT, see
`scripts/LICENSE-MIT-starter-kit.txt`): **check the exported file, not the timeline.** A CapCut preview can look right
while the export is wrong.

Set once per video: `R=~/Movies/Reels/<project>/<project>.mp4` (the CapCut export) and `SK=~/.claude/skills/instagram-reels-design`.
Never run anything on footage or projects from other people without reading it first. ffmpeg commands below only read
the file and write PNG/TXT next to it.

## 0. Export settings (CapCut)

- [ ] 1080 x 1920, 30 fps (constant), H.264, AAC stereo. Instagram re-encodes; a higher bitrate export (CapCut "High"
      or about 10 to 16 Mb/s) survives better than "Recommended".
- [ ] No TikTok/CapCut watermark or end card (Instagram reportedly makes watermarked Reels less discoverable).
- [ ] Probe: `ffprobe -v error -show_entries stream=width,height,r_frame_rate,codec_name -show_entries format=duration -of compact "$R"`

## 1. Frame contact sheet (read it, never assume)

```bash
ffmpeg -v error -y -i "$R" -vf "fps=1,scale=270:-2,tile=6x4" -fps_mode passthrough "${R%.mp4}-sheet_%02d.png"
```
One tile per second. Look for: a frame 0 that is a meaningful image, text over the face or the bottle, a card left on
screen too long, a missing PNG cutout edge, a black or white flash.

## 2. Safe-zone overlap

```bash
ffmpeg -v error -y -i "$R" -vf "fps=1/2,drawbox=x=65:y=269:w=950:h=979:color=red:t=8,drawbox=x=65:y=250:w=865:h=1250:color=yellow:t=8,scale=360:-2,tile=6x2" -fps_mode passthrough "${R%.mp4}-safe_%02d.png"
```
- Red box = strict Meta box (top 14 %, bottom 35 %, sides 6 %). Yellow = organic working zone (UNVERIFIED creator
  figures: top ~250 px, bottom ~420 px, right buttons ~150 px).
- [ ] Hook text, key words, captions, prices: inside red.
- [ ] Nothing readable outside yellow. PNGs and circle notes may cross red but not yellow.
- [ ] Optional: open the export on your phone in Instagram's Reel preview (before sharing) and look at the first
      frame and two text moments with the real UI on top.

## 3. Hook check (first 3 s)

- [ ] Frame 0 meaningful; promise readable muted; first spoken word not covered by an SFX peak or a cut.
- [ ] Hook copy 9 words or fewer, in 2 to 4 chunks; key word on screen at least 0.8 s.
- [ ] The promised payoff happens (note its time) before any call to action.
- See `hooks.md` for the full gate.

## 4. Reading speed

- [ ] Title / support cards: at most ~3 words per second of screen time.
- [ ] Burned-in captions follow speech; split any cue over ~4 words per second or over 2 lines.
- Export captions as SRT from CapCut (Text > captions > export, if available in your version) and run:
  `python3 -I "$SK/scripts/caption-speed.py" captions.srt` (flags cues over 3 w/s; treat 3 to 4 w/s as fine for
  speech-synced captions, over 4 as a split).

## 5. Contrast and legibility

- [ ] Every neon word has a dark shadow (alpha 0.45 to 0.60) or a scrim; check the sheet at phone size (the tiles are
      roughly what a thumbnail glance sees).
- [ ] No deep violet (#7A00FF family) fill on dark footage.
- [ ] Caption size at least ~56 px on the frame; labels never under 40 px.

## 6. Flash / strobe check (photosensitivity)

WCAG 2.3.1: no more than three general flashes in any one second. Your "Flash cálido" montages and sparkle effects are
the risk.
```bash
ffmpeg -v error -i "$R" -vf "scale=64:-2,format=gray,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=luma.txt" -f null -
python3 -I "$SK/scripts/flash-check.py" luma.txt
```
- [ ] No window flagged. (A jump of 25/255 in average luma is a heuristic for "a flash", not the full WCAG
      area/red-flash test; when flagged, look at those frames.)

## 7. Loudness and audio

```bash
ffmpeg -hide_banner -nostats -i "$R" -af ebur128=peak=true -f null - 2>&1 | tail -12
```
- [ ] Integrated loudness about **-14 LUFS** (±1), true peak at or below **-1 dBTP**. -14 LUFS is the common streaming
      target and the kit's master level; Instagram's own normalisation target is not published (UNVERIFIED), so -14 is
      a safe, loud-enough choice. Your projects raise the voice 1.9 to 5x in CapCut: check that this did not clip.
- [ ] Music 16 to 20 dB under the voice (your 3 to 13 % volume range does this), no music bed doubled with an
      Instagram library sound added at upload.
- [ ] SFX audible but not louder than the voice; no whoosh under plain text.
- [ ] Voice intelligible on a phone speaker (listen once on the phone).

## 8. Black frames and render faults

```bash
ffmpeg -hide_banner -nostats -i "$R" -vf "scale=320:-2,blackdetect=d=0:pix_th=0.08" -an -f null - 2>&1 | grep black_start || echo "no black frames"
```
- [ ] None, except a deliberate fade at the very end.
- Optional full check with the kit's script (see SKILL.md "Optional scripts"):
  `python3 -I "$SK/scripts/verify-render.py" --render "$R" --res 1080x1920 --min-mbps 24`
  (its bitrate floor scales from 4K: `--min-mbps 24` means 6 Mb/s at 1080x1920. Its BT.709 colour-tag check may FAIL
  on CapCut exports; that is informational unless colours look wrong. Duration vs composition is skipped without a
  HyperFrames index.)

## 9. Cover and post

- [ ] Cover frame chosen or uploaded (1080x1920); title and face inside the centred 1080x1440 grid area (CapCut y
      +0.75 to -0.75), ideally inside 1080x1350 (y +0.70 to -0.70) for the 4:5 feed crop.
- [ ] Caption: hook line first (it is the visible part), keywords for search (perfume name, brand, notes, "dupe",
      season), up to **5 hashtags**, specific (#perfumereview #vanillaperfume #arabianperfume), no #reels/#explore.
- [ ] Alt text / captions: Instagram auto-captions on, or burned-in captions present.
- [ ] Product mentions: tag the brand, use Paid partnership label when gifted or paid (local ad rules).
- [ ] Location / collaborators added when relevant (trip videos).

## 10. Edit-stage scans (optional, before export)

On the talking-head audio, before building overlays (see SKILL.md "Optional scripts" for inputs):
- Dead air: pauses over 0.40 s after a sentence end, 0.45 s elsewhere (`dead-air.py`).
- Stutters and retakes: "the the", "I- I", repeated sentences (`stutter-scan.py`, English-centric stop words).
- Static stretches: nothing changes for more than 3 s in the first 15 s, 5 s later (check by eye on the sheet from
  step 1 or with `teardown.py --video`, which also counts cuts per minute).
