# Editing imagery - background removal, matting, crops, grading

> Research reference for the design pipeline. Compiled 2026-09-09 from primary
> sources; every tool, endpoint and browser-support figure was verified at that
> date and carries its URL inline. Items that could not be confirmed are marked
> UNVERIFIED - treat those as leads, not facts. Re-verify prices and model IDs
> before quoting them to a client.

# Research F - image EDITING for the `/assets` skill

Scope: high-quality background removal first, then the surrounding edit operations a
design agent needs. Everything below was checked against the upstream repo, PyPI JSON
metadata, or run on this machine. Anything I could not confirm is labelled `UNVERIFIED`.


> **VERIFIED CORRECTION 2026-09-09 - read this before copying any request below.**
> Queried live against a real key: `gemini-3.1-flash-image` and `gemini-3-pro-image` both
> report `supportedGenerationMethods: ['generateContent','countTokens','batchGenerateContent']`.
> A working REST call is:
> `POST https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`
> with `{"contents":[{"parts":[{"text":"..."}]}]}` and an `x-goog-api-key` header. The image
> comes back as base64 in `candidates[0].content.parts[].inlineData.data`.
> Where this file says `/v1beta/interactions`, treat that as the newer SDK surface and
> UNVERIFIED against the REST API - `generateContent` is what was actually confirmed working.


## Environment, as actually measured (not as briefed)

Run on this box, 2026-09-09:

| Thing | Measured |
| --- | --- |
| GPU | `AMD Radeon 880M Graphics (RADV STRIX1)` - the brief said 890M. Vulkan 1.4.354, driver `radv`. |
| CPU | 20 threads, 22 GB RAM |
| Python | system `3.14.7`; `uv 0.11.4`; **`cpython-3.13.12` already installed under uv** |
| ImageMagick | `7.1.2-31 Q16-HDRI`, delegates include `lqr jxl heic webp lcms raw rsvg fftw openexr` |
| ffmpeg | present, has `lut3d lut1d haldclut curves colorbalance colorchannelmixer colorlevels noise eq` |
| Missing | `oxipng`, `pngquant`, `cwebp`, `exiftool` (ImageMagick covers webp/png output; add `oxipng` if you care about PNG size) |

The Vulkan stack works, which matters: it means **ncnn-Vulkan tools run on this iGPU
without ROCm**. That is the escape hatch for upscaling. It does *not* help rembg, which
is ONNX Runtime and would need `onnxruntime-rocm`.

---

## 1. State of the art in background removal / matting, 2026

### Licenses - verified via the GitHub API, not from memory

| Project | SPDX (repo) | Commercial? |
| --- | --- | --- |
| `ZhengPeng7/BiRefNet` | MIT | Yes |
| `PramaLLC/BEN2` | MIT | Yes |
| `plemeri/InSPyReNet` | MIT | Yes |
| `hustvl/ViTMatte` | MIT | Yes |
| `danielgatis/rembg` | MIT | Yes (code only - weights carry their own) |
| `xuebinqin/U-2-Net` | Apache-2.0 | Yes |
| `xuebinqin/DIS` (isnet-general-use) | Apache-2.0 | Yes |
| `SkyTNT/anime-segmentation` (isnet-anime) | Apache-2.0 | Yes |
| `ZHKKKe/MODNet` | Apache-2.0 - README says "code, models, and demos ... released under the Apache License 2.0" | Yes |
| `facebookresearch/sam3` | `NOASSERTION` - custom Meta licence, read it | Check |
| **BRIA RMBG-2.0** | **CC BY-NC 4.0** | **NO. "Commercial use is subject to a commercial agreement with BRIA."** |

Source for the BRIA clause: https://huggingface.co/briaai/RMBG-2.0

### The trap you must know about

**`bria-rmbg` (RMBG-2.0) is rembg's DEFAULT model.** Verified in
`rembg/commands/i_command.py`: `@click.option("-m","--model", default="bria-rmbg", ...)`.
So `rembg i in.png out.png` with no `-m` silently runs a non-commercial model. For any
client work the `/assets` skill must **always pass `-m`**. rembg's own README says so:
"Note that RMBG-2.0 is released under a BRIA license that requires a paid agreement for
commercial use."

### Ranking for this use case

**Tier 1 - best edges, MIT, runs here today**

- **BiRefNet** (`-m birefnet-general` in rembg). The reference architecture for
  high-resolution dichotomous segmentation; RMBG-2.0 is literally BiRefNet plus BRIA's
  proprietary data. MIT weights. rembg ships ONNX exports of seven BiRefNet checkpoints,
  so no torch needed. **This is the recommendation.**
- **BEN2** (Background Erase Network 2, MIT, `PramaLLC/BEN2`). Third-party 2026
  comparisons put it ahead of BiRefNet specifically on hair, because of its "Confidence
  Guided Matting" pass that re-processes only low-confidence pixels. But: it needs torch
  plus the repo's own `BEN2.py`, there is no ONNX export in rembg, and I did **not** run
  it here. `UNVERIFIED on this machine`. Keep it as the escalation path if BiRefNet+ViTMatte
  is not enough on a specific hero image.

**Tier 1 quality, licence-blocked**

- **RMBG-2.0 / `bria-rmbg`** - genuinely excellent, 1024x1024, ~977 MB, and slower than
  BiRefNet here, and no better on edges in my test. CC BY-NC 4.0. Use only for
  the user's own non-commercial work.
- **RMBG-1.4** - the older BRIA model. Also non-commercial (`bria-rmbg-1.4` is not in
  rembg 2.x's model list; only `bria-rmbg` = 2.0 is). Ignore it.

**Tier 2 - good, cheaper, or better ergonomics**

- **InSPyReNet** via the `transparent-background` package. MIT. Its CLI has output modes
  rembg lacks (`--type green|white|blur|overlay|<hex>|<image path>`), and it does video
  and webcam. Cost: it pulls **torch** (see the pinning section). PyPI 1.3.4, released
  2025-05-14 - it has not moved in over a year, which is a maintenance signal.
- **`isnet-general-use`** (DIS, Apache-2.0). 171 MB, **4.1 s** here. A good "fast preview"
  model when you are iterating on composition and will re-cut at the end.

**Tier 3 - fastest, blocky**

- `u2net` / `u2netp` / `silueta` (Apache-2.0). **3.6 s** here. Firm, stair-stepped edges.
  rembg's README is explicit that these are the ones that actually benefit from `-a`.
  Fine for hard-edged products, wrong for hair.

**Not a background remover - do not reach for these**

- **SAM / SAM 2 / SAM 3.** SAM 3 (Meta, released 2025-11-19, ICLR 2026) adds
  Promptable Concept Segmentation - "segment every instance of `<text>`". That is
  *selection*, not *matting*: it returns hard instance masks with no soft alpha, so hair
  and glass come out stair-stepped. rembg does ship `-m sam` with a point prompt
  (`-x '{"sam_prompt":[{"type":"point","data":[724,740],"label":1}]}'`) - use it only
  when you need to pick one object out of a cluttered frame, then hand the mask to
  ViTMatte for the actual edge. Licence is `NOASSERTION` (custom Meta terms).
- **ViTMatte.** Not a segmenter at all - it is a trimap-to-alpha refiner. You do not run
  it standalone; **rembg already wires it in as `-vm`**. That is the single most useful
  fact in this whole document.
- **MODNet.** AAAI 2022, portrait-only, real-time. Superseded on quality by everything in
  Tier 1. Apache-2.0 including weights, so it is a fine fallback if you ever need
  30fps portrait matting on a potato. Not relevant here.

### Measured CPU speed on this machine

2000x1334 JPEG, `uv run` (so each row includes ~4s of venv + ONNX Runtime startup and
model load from page cache). Model already downloaded. **Wall clock, this box, CPU only:**

| Model | Flag | Warm wall clock | On disk |
| --- | --- | --- | --- |
| `u2net` | `-dc` | **3.6 s** | 168 MB (legacy `~/.u2net`) |
| `isnet-general-use` | `-dc` | **4.1 s** | 171 MB |
| `birefnet-general-lite` | `-dc` | **11.7 s** | 214 MB |
| `birefnet-general` | *(naive)* | **16.8 s** | 928 MB |
| `birefnet-general` | `-dc` | **15.9 - 17.6 s** | 928 MB |
| `bria-rmbg` (default, non-commercial) | `-dc` | **17.3 s** | 977 MB |
| `birefnet-general` | `-a` | **18.8 s** | + pymatting solver |
| `birefnet-general` | `-vm` | **17.4 - 19.7 s** | + 110 MB ViTMatte |

Three things this table says that I did not expect going in:

1. **`-vm` is nearly free.** ViTMatte adds only ~2-3 s on top of the model, not minutes.
   The README warns it is "slow", which is true relative to `-dc` but irrelevant next to
   BiRefNet's own 15 s. **On this machine there is no reason not to use `-vm`.**
2. **`-a` is not faster than `-vm`,** so `-a` has no remaining advantage - `-vm` recovers
   more strands and cannot fail to converge.
3. **The first invocation after a reboot costs ~2x.** My very first `birefnet-general -dc`
   took 31.2 s; warm it is 16-18 s. That is the 928 MB ONNX file coming off disk into page
   cache. Pre-warm if latency on the first request matters.

`birefnet-general-lite` at 11.7 s is only ~1.4x faster than the full model, not the
order of magnitude the name suggests - the ~3 s of uv + ONNX Runtime startup is a fixed
floor. If you want genuinely fast, drop to `isnet-general-use` (4.1 s).

First run of any model adds its download. Measured on-disk sizes:

```
928M  ~/.rembg/models/birefnet-general
977M  ~/.rembg/models/bria-rmbg
171M  ~/.rembg/models/isnet-general-use
110M  ~/.rembg/models/vitmatte
```

Honest summary: **BiRefNet with ViTMatte on this CPU is under 20 seconds per 2000px
image.** That is genuinely usable - fine for a design agent cutting 1-50 hero assets
interactively. It is still not a catalogue pipeline: 500 images is ~3 hours, so for that
use `isnet-general-use` for the contact sheet and only run BiRefNet on the ones that
ship, or pay Photoroom $0.02/image.

### Edge quality, verified visually

I cut the same tiger photo four ways and composited each on magenta at 300% zoom
(`bgtest/edge-compare.png` in the scratchpad). What is actually visible:

- **naive** (no flag): a grey/dark rim traces the top of the head. Ear tip is blunt.
  This is the fringe the user is complaining about.
- **`-dc`**: the rim is gone, fur edge reads at the correct brightness. Silhouette shape
  unchanged.
- **`-vm`** (ViTMatte): individual fur strands appear over the magenta at the ear and
  crown that are simply absent in naive and `-dc`. Best of the four.
- **`-a`** (closed-form): similar to `-vm`, slightly softer, a few fewer strands.

---

## 2. The verified runbook

All flags below were read out of `rembg/commands/i_command.py` at
https://github.com/danielgatis/rembg - not guessed.

```
-m,  --model                                default: bria-rmbg   (ALWAYS override)
-a,  --alpha-matting                        flag
-af, --alpha-matting-foreground-threshold   default: 240
-ab, --alpha-matting-background-threshold   default: 10
-ae, --alpha-matting-erode-size             default: 10
-om, --only-mask                            flag
-ppm,--post-process-mask                    flag  (binarises - do NOT combine with -dc)
-dc, --decontaminate                        flag
-vm, --vitmatte                             flag
-bgc,--bgcolor R G B A                      4 ints, flattens onto a colour
-x,  --extras '<json>'
```

Subcommands: `i` (file), `p` (folder), `s` (HTTP server), `b` (RGB24 stdin stream,
for ffmpeg pipes), `d` (pre-download models), `m` (migrate legacy `~/.u2net`).
`rembg p` takes every flag above plus `-w/--watch`.

### Python pinning - the good news

**rembg installs on Python 3.14. Do not pin.**

The README says `python: >=3.11, <3.14`. That is **stale**. The published wheel metadata
says otherwise, and it resolves and runs:

```
$ curl -s https://pypi.org/pypi/rembg/json | jq -r '.info.requires_python'
<4.0,>=3.11
```

I ran a real resolve against a 3.14.7 interpreter: `rembg==2.0.84` + `onnxruntime==1.29.0`
+ `numpy==2.5.3` + `pymatting==1.1.16`, 83 packages, no conflict, and then executed the
full matrix above on 3.14. onnxruntime 1.29.0 (2026-08-17) carries a
`Programming Language :: Python :: 3.14` classifier.

`transparent-background` also resolves on 3.14 (it needs torch, and torch 2.14.0 declares
3.14). **Nothing in this document requires a pinned Python.** If a future wheel gap
appears, `uv python list` shows `cpython-3.13.12` is already on disk, so the workaround
costs nothing: add `--python 3.13`.

### Recommendation 1 - rembg + BiRefNet (the default path)

No global install. `uv` builds and caches an ephemeral env per unique `--with` set.

```bash
# one-off, transparent PNG, fringe already handled
uv run --no-project --with "rembg[cpu,cli]" \
  rembg i -m birefnet-general -dc in.jpg out.png

# the good one: ViTMatte edge refinement, for hair / fur / hero shots
uv run --no-project --with "rembg[cpu,cli]" \
  rembg i -m birefnet-general -vm in.jpg out.png

# just the alpha, if you want to drive your own compositing
uv run --no-project --with "rembg[cpu,cli]" \
  rembg i -m birefnet-general -om in.jpg mask.png

# flatten straight onto a brand colour (R G B A), no separate ImageMagick step
uv run --no-project --with "rembg[cpu,cli]" \
  rembg i -m birefnet-general -dc -bgc 11 61 46 255 in.jpg on-brand.png

# batch a folder, reusing one session (much faster than N invocations)
uv run --no-project --with "rembg[cpu,cli]" \
  rembg p -m birefnet-general -dc ./in ./out
```

**Quote the extras.** The user's shell is zsh, where `rembg[cpu,cli]` is a glob
character class. Unquoted it expands to nothing and `uv run` fails instantly with a
confusing error - I hit this while benchmarking. Always write `--with "rembg[cpu,cli]"`.

Model choice cheat sheet, from rembg's own model list:

| Subject | `-m` |
| --- | --- |
| Anything general, commercial-safe | `birefnet-general` |
| Same but ~1.4x faster, slightly worse (214 MB vs 928 MB) | `birefnet-general-lite` |
| People | `birefnet-portrait` |
| Source image > ~1500px, fine structure | `birefnet-hrsod` |
| Low-contrast subject against similar background | `birefnet-cod` |
| Anime / illustration | `isnet-anime` |
| Fast preview pass | `isnet-general-use` |
| Hard-edged product, need speed | `u2net` |
| One object out of a cluttered frame | `sam` + `-x '{"sam_prompt":[...]}'` |

ViTMatte checkpoint override (default `small-distinctions-646`, ~110 MB):

```bash
uv run --no-project --with "rembg[cpu,cli]" rembg i \
  -m birefnet-general -vm -x '{"vitmatte_model":"base-distinctions-646"}' in.jpg out.png
```

`base-*` is ~380 MB and ~2.5x the runtime per the README. Not worth it on this CPU.

### Recommendation 2 - transparent-background / InSPyReNet

Worth having only for its output modes and video support. It pulls torch, so force the
CPU wheels or you download ~2.5 GB of unusable CUDA libraries.

`uv run` does **not** accept `--torch-backend` (verified: `uv run --torch-backend=cpu`
errors out, and `UV_TORCH_BACKEND=cpu uv run ...` was silently ignored - it installed
`torch 2.14.0+cu130`). The form that works is the explicit index:

```bash
uv run --no-project --index https://download.pytorch.org/whl/cpu \
  --with transparent-background \
  transparent-background --source in.jpg --dest ./out --type rgba
```

Verified: that index gives `torch==2.14.0+cpu` and drops 15 `nvidia-*` packages.
For a persistent venv the `uv pip` flag does exist and is cleaner:

```bash
uv venv ~/.cache/assets-tb --python 3.14
VIRTUAL_ENV=~/.cache/assets-tb uv pip install --torch-backend=cpu transparent-background
~/.cache/assets-tb/bin/transparent-background --source in.jpg --type rgba
```

CLI, verbatim from https://github.com/plemeri/transparent-background:

```
transparent-background --source [SOURCE] --dest [DEST] --threshold [THRESHOLD]
  --type [TYPE] --ckpt [CKPT] --mode [MODE] --resize [RESIZE] --format [FORMAT]
  (--reverse) (--jit)
```

- `--mode`: `base` (default), `base-nightly`, `fast`
- `--type`: `rgba`, `map`, `green`, `white`, `blur`, `overlay`, `'[255, 0, 0]'`, or a path to an image
- `--resize`: `static` or `dynamic` ("Dynamic will produce better results in terms of
  sharper edges but maybe unstable")
- `--source` accepts an image, a folder, a video, or an integer for a webcam

I did not benchmark it here (the torch download is ~1.5 GB and BiRefNet already wins on
edges). `speed UNVERIFIED on this machine`.

---

## 3. Halo and fringe removal - the craft part

The physics. On a soft edge the sensor captured a blend:

```
captured = alpha * foreground + (1 - alpha) * background
```

Writing that captured pixel out with a low alpha does **not** undo the blend. The old
background colour is still mixed into the RGB, so it shows as a coloured rim: green
against grass, blue against sky, grey against a studio wall. Photoshop calls the fix
*Decontaminate Colors*; Nuke calls it *decontamination*; the maths is
`foreground = (captured - (1-alpha)*background) / alpha`.

### The four levers, in the order you should reach for them

**1. Foreground estimation - `-dc`. This is the one that actually kills fringing.**

rembg's `decontaminate_cutout()` calls `pymatting.estimate_foreground_ml()`, a
multi-level solver that recovers the unblended foreground colour for every
semi-transparent pixel. It touches **colour only, never alpha**, costs almost nothing
next to inference, and cannot fail. Leave it on for whole batches.

**2. Re-estimate coverage - `-vm` (ViTMatte) or `-a` (closed-form).**

Use these when the *shape* of the matte is wrong, not just its colour - the model cut
through hair strands, or left a stair-stepped edge on something genuinely soft.

Both build a trimap from the mask first, and **both are steered by the same three
flags**: `-af` (definite-foreground threshold, default 240), `-ab` (definite-background,
default 10), `-ae` (erode size, default 10). Read from `matting.py`:

```python
is_foreground = mask_array > foreground_threshold   # -af
is_background = mask_array < background_threshold   # -ab
# both eroded by an erode_size x erode_size box     # -ae
trimap = 128 everywhere else   # <- the "unknown" band the solver works on
```

So: **raising `-ae` widens the unknown band**, which gives the matter more room to find
strands but costs time and can eat into solid areas. That is your one real tuning knob
for wispy hair. `-a`'s solver can fail to converge (rembg catches `ValueError` and falls
back to a `-dc` cutout); `-vm` cannot.

`-vm` runs at a fixed 1024x1024 and resizes the alpha back out. That is deliberate, not
sloppy - the VitDet backbone builds position tables from the input dims and a dynamic
export "silently returns wrong alphas at any other size".

**They are alternatives, not layers.** `-a` decontaminates internally, so `-a -dc` is
the same as `-a`. And `-ppm` binarises the mask, so `-ppm -dc` is pointless.

**3. Decontaminating a cutout you did NOT make with rembg.**

Generic unmix against a known background colour, ~10 lines, verified working here:

```python
# unmix.py IN.png OUT.png "#00FF00"
import sys, numpy as np
from PIL import Image
inp, out, hexbg = sys.argv[1], sys.argv[2], sys.argv[3].lstrip('#')
bg = np.array([int(hexbg[i:i+2], 16) for i in (0, 2, 4)], np.float32) / 255.0
im = np.asarray(Image.open(inp).convert('RGBA'), np.float32) / 255.0
rgb, a = im[..., :3], im[..., 3:4]
fg = np.where(a > 1e-3, (rgb - (1.0 - a) * bg) / np.maximum(a, 1e-3), rgb)
Image.fromarray((np.concatenate([np.clip(fg, 0, 1), a], -1) * 255 + 0.5)
                .astype(np.uint8)).save(out)
```
```bash
uv run --no-project --with pillow --with numpy python unmix.py cut.png clean.png "#3B8E4A"
```

Green-screen despill only, pure ImageMagick, 0.04s (verified):

```bash
magick in.png -alpha set -channel G -fx "min(g,(r+b)/2)" +channel despilled.png
```

If you have the original *and* a mask, prefer running `pymatting.estimate_foreground_ml`
directly - it is strictly better than either of the above because it does not assume a
single flat background colour.

**4. Choke vs feather - the last resort, and usually the wrong answer.**

Both verified on ImageMagick 7.1.2-31:

```bash
# choke: pull the matte in by ~1px. Hides a rim by deleting it, and eats hair with it.
magick in.png -channel A -morphology Erode Disk:1 +channel out.png

# feather: soften the alpha. Hides a stair-step, blurs a good edge.
magick in.png -channel A -blur 0x1 +channel out.png

# matte contrast: crush near-0 and near-255 alpha, keep the middle. Kills the faint
# grey wash some models leave across the whole background.
magick in.png -channel A -level 5%,95% +channel out.png
```

Rule: **decontaminate first, always. Only choke if fringing survives `-dc`, and never
more than 1px.** Choking is how you get a subject with a shaved outline.

### Compositing without a visible rim

Two things cause a rim at composite time even from a perfect matte:

1. **Premultiply confusion.** PNG alpha is straight (unpremultiplied). If a downstream
   tool assumes premultiplied you get a dark halo. Force a proper RGBA PNG:
   `magick in.png -define png:color-type=6 out.png`
2. **Resizing an unpremultiplied cutout.** Resampling mixes transparent pixels' RGB into
   opaque ones. ImageMagick 7 handles this correctly by default when the alpha channel is
   active; the failure mode is a pipeline that strips alpha mid-chain. Keep alpha to the
   end and write PNG/WebP, not JPEG.

Composite onto a brand ground:

```bash
magick -size 2000x2000 xc:"#0B3D2E" cut.png -compose over -composite flat.png
# or skip the step entirely: rembg ... -bgc 11 61 46 255
```

---

## 4. The other edit operations

Every command below was executed on this machine's ImageMagick 7.1.2-31 / ffmpeg.

### Smart crop to an aspect ratio, keeping the subject

Three options, in increasing order of how much I trust them:

**(a) ImageMagick `-gravity` alone: does not do this.** `-gravity` picks a fixed anchor
(center/north/...). It has no idea where the subject is. It is fine when the subject is
already centred and nothing else.

**(b) `smartcrop` (PyPI 0.5.0, `requires_python >=3.10`, deps just numpy + pillow).**
The Python port of smartcrop.js - edge/saliency/skin heuristics, no ML. Verified here:

```bash
uv run --no-project --with smartcrop --with pillow \
  smartcroppy --width 1080 --height 1350 in.jpg out.jpg
```

Installed in 30 ms, ran in 1.4 s. **Two gotchas I hit:** it dumps a large JSON blob of
every candidate crop to stdout (redirect it), and `--width/--height` are treated as a
*ratio*, not a size - I asked for 1080x1350 and got 1066x1325. You still need a
`magick -resize` after it.

**(c) Crop from the alpha bounding box. This is the right answer for `/assets`,**
because the skill has already run background removal, so it knows exactly where the
subject is - no heuristic needed. ImageMagick reports the bbox with `%@`. Verified script:

```bash
#!/usr/bin/env bash
# subjectcrop.sh CUTOUT.png ORIGINAL.jpg W H OUT.jpg
set -uo pipefail
cut=$1; src=$2; W=$3; H=$4; out=$5
sw=$(magick identify -format "%w" "$src"); sh_=$(magick identify -format "%h" "$src")
bbox=$(magick "$cut" -format "%@" info:)          # e.g. 1707x771+133+387
bw=${bbox%%x*}; r=${bbox#*x}; bh=${r%%+*}; r=${r#*+}; bx=${r%%+*}; by=${r#*+}
cx=$(( bx + bw/2 )); cy=$(( by + bh/2 ))
if [ $(( sw * H )) -gt $(( sh_ * W )) ]; then cw=$(( sh_ * W / H )); ch=$sh_
else cw=$sw; ch=$(( sw * H / W )); fi
x=$(( cx - cw/2 )); y=$(( cy - ch/2 ))
if [ $x -lt 0 ]; then x=0; fi
if [ $y -lt 0 ]; then y=0; fi
if [ $(( x + cw )) -gt $sw  ]; then x=$(( sw  - cw )); fi
if [ $(( y + ch )) -gt $sh_ ]; then y=$(( sh_ - ch )); fi
magick "$src" -crop "${cw}x${ch}+${x}+${y}" +repage \
  -resize "${W}x${H}^" -gravity center -extent "${W}x${H}" "$out"
```

Verified output: 1080x1350 and 1920x1080 from the same source, subject centred both times.

Bare-minimum version when you only need the subject tight with padding:

```bash
magick cut.png -trim +repage -resize 800x1000 -background none \
  -gravity center -extent 800x1000 out.png     # verified
```

ImageMagick also has **seam carving** (`lqr` delegate present, verified):
`magick in.png -liquid-rescale 300x400! out.png`. It changes aspect without cropping, but
it warps geometry. Use on textures and backdrops, never on a product or a face.

### Upscaling

**Real-ESRGAN on this CPU: don't.** The Python implementation is the slow path and it is
why every guide says "use a GPU". But this box has a working Vulkan 1.4 / RADV stack,
and **ncnn-Vulkan does not need CUDA or ROCm** - it runs on the 880M directly.

In the AUR (verified via the AUR RPC):

```
realesrgan-ncnn-vulkan-bin   0.2.5.0-1   (16 votes)   <- take this one
realesrgan-ncnn-vulkan       0.2.0-7     (5 votes)
upscayl-bin                  2.15.0-10   (64 votes)   <- GUI over the same engine
```

And already in the official `extra` repo: `waifu2x-ncnn-vulkan 20250915-2` (illustration
upscaling, no AUR needed).

```bash
# after installing realesrgan-ncnn-vulkan-bin
realesrgan-ncnn-vulkan -i in.png -o out.png -n realesrgan-x4plus -s 4
```
`flags and model names UNVERIFIED - not installed here.` Check `realesrgan-ncnn-vulkan -h`
before wiring into the skill.

For a 2x with no dependency at all, ImageMagick's Lanczos is fine for photos that are
only slightly under-size:
`magick in.jpg -filter Lanczos -resize 200% -unsharp 0x0.75+0.75+0.008 out.jpg`

### Colour grading / LUTs

ffmpeg reads the format designers actually hand you (`.cube`). Both verified here:

```bash
# 3D LUT from a .cube file
ffmpeg -i in.png -vf "lut3d=file=grade.cube" -y out.png

# Hald CLUT (identity generated by ImageMagick, edit it in any photo app, re-apply)
magick hald:8 hald8.png                      # identity, verified
magick in.png hald8.png -hald-clut out.png   # ImageMagick side, verified
ffmpeg -i in.png -i hald8.png -filter_complex "[0][1]haldclut" -y out.png   # verified
```

Also present and verified in `ffmpeg -filters`: `lut1d curves colorbalance
colorchannelmixer colorlevels eq`.

### Film grain

```bash
magick in.png -attenuate 0.35 +noise Gaussian out.png              # verified
ffmpeg -i in.png -vf "noise=alls=12:allf=t+u" -y out.png            # verified
```
`-attenuate` scales the noise; 0.2-0.5 is the usable band. Add grain **last**, after
grading, or the LUT redistributes it and it stops looking like film.

### A drop shadow that looks real

The one-liner everyone uses is `-shadow`, and it is what makes composites look like
stickers: a uniform offset blur of the *whole* silhouette, including the head, floating
in space. I built both and compared them side by side (`bgtest/shadow-compare3.png`).

What makes it read as an object on a surface:

1. Derive the shadow from the **bottom ~25% of the silhouette** (the contact footprint),
   not the whole shape.
2. **Two layers**: a wide soft ambient shadow, and a tight dark contact shadow right at
   the base. Real shadows get sharper and darker the closer to contact.
3. Squash vertically - the shadow lies on the ground plane, it is not a copy of the front view.

Verified:

```bash
H=$(magick identify -format %h subj.png); FOOT=$(( H * 25 / 100 ))
magick -size 1000x700 xc:"#EFE9E1" \
  \( subj.png -alpha extract -gravity south -crop 100%x${FOOT}+0+0 +repage \
     -background black -alpha shape -resize 106%x55% -blur 0x20 -evaluate multiply 0.38 \) \
     -gravity south -geometry +10+178 -composite \
  \( subj.png -alpha extract -gravity south -crop 100%x${FOOT}+0+0 +repage \
     -background black -alpha shape -resize 100%x22% -blur 0x4 -evaluate multiply 0.62 \) \
     -gravity south -geometry +0+188 -composite \
  subj.png -gravity south -geometry +0+190 -composite out.png
```

Knobs: ambient `-blur 0x20` / `multiply 0.38`, contact `-blur 0x4` / `multiply 0.62`, and
the `+X` offset on the ambient layer sets the light direction. The naive version, for
reference and for when you genuinely want a sticker:

```bash
magick subj.png \( +clone -background black -shadow 55x18+0+18 \) +swap \
  -background none -layers merge +repage out.png     # verified
```

### Flatten onto a brand-coloured background

```bash
magick -size 2000x2000 xc:"#0B3D2E" cut.png -compose over -composite out.png   # verified
```
Or do it inside rembg with `-bgc 11 61 46 255` and skip a process.

### Duotone in brand colours

```bash
magick in.jpg -colorspace gray -auto-level +level-colors "#0B3D2E,#F2E9DE" duo.png
```
Verified. `+level-colors "shadow,highlight"` maps black to the first colour and white to
the second. `-auto-level` before it is what stops muddy source photos producing a flat,
low-contrast duotone. For a tritone, insert `-sigmoidal-contrast 4,50%` before the
`+level-colors`.

### Batch to a consistent look

The trick is not the batch loop, it is deriving the grade once and applying it
identically. Generate a Hald CLUT, grade **that single file** to taste, then apply it to
everything - the transform is then provably identical across the set:

```bash
magick hald:8 grade.png            # identity; grade this file, save it back
for f in in/*.jpg; do
  magick "$f" grade.png -hald-clut -resize 2000x2000\> \
    -attenuate 0.3 +noise Gaussian "out/$(basename "$f" .jpg).jpg"
done
```

And for the cutouts, `rembg p` reuses one ONNX session across the folder, which is much
faster than N `uv run` invocations:

```bash
uv run --no-project --with "rembg[cpu,cli]" rembg p -m birefnet-general -dc ./in ./out
```

---

## 5. Generative editing as an alternative

### Gemini (Nano Banana)

Current model IDs, from https://ai.google.dev/gemini-api/docs/image-generation:
`gemini-3-pro-image`, `gemini-3.1-flash-image`, `gemini-3.1-flash-lite-image`,
`gemini-2.5-flash-image`.

Note this is the **`/v1beta/interactions` endpoint**, not `generateContent` - the docs
have moved on from the shape in the existing `nano-banana` skill:

```bash
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gemini-3.1-flash-image",
    "input": [
      {"type": "text", "text": "Replace the background with a seamless studio backdrop in #0B3D2E. Keep the subject, its lighting and its edges exactly as they are."},
      {"type": "image", "mime_type": "image/jpeg", "data": "<BASE64>"}
    ]
  }'
```

```python
from google import genai
import base64
client = genai.Client()
with open("in.png", "rb") as f:
    image_bytes = f.read()
interaction = client.interactions.create(
    model="gemini-3.1-flash-image",
    input=[
        {"type": "text", "text": "..."},
        {"type": "image", "data": base64.b64encode(image_bytes).decode("utf-8"),
         "mime_type": "image/png"},
    ],
)
```

Supported edits: add/remove elements, **semantic masking** (change one element, keep the
rest), style transfer, multi-image composition, multi-turn iterative editing.
**There is no mask input parameter** - masking is prompt-driven only.
Resolutions 512px/1K/2K/4K (3.1 Flash Lite is 1K only); aspect ratios 1:1, 3:2, 2:3, 3:4,
4:3, 4:5, 5:4, 9:16, 16:9, 21:9.

Pricing per image (https://ai.google.dev/gemini-api/docs/pricing), **no free tier**:

| Model | 1K | 2K | 4K |
| --- | --- | --- | --- |
| gemini-3-pro-image | $0.134 | $0.134 | $0.24 |
| gemini-3.1-flash-image | $0.067 | $0.101 | $0.151 |
| gemini-3.1-flash-lite-image | $0.0336 | - | - |
| gemini-2.5-flash-image | $0.039 flat (batch $0.0195) | | |

### OpenAI `POST /v1/images/edits`

The only one of the three with a **real mask parameter**. Verified against
https://developers.openai.com/api/docs/guides/image-generation:

```bash
curl -X POST "https://api.openai.com/v1/images/edits" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -F "model=gpt-image-2.5-sunburst" \
    -F "mask=@mask.png" \
    -F "image[]=@sunlit_lounge.png" \
    -F 'prompt=A sunlit indoor lounge area with a pool containing a flamingo'
```

```python
from openai import OpenAI
client = OpenAI()
result = client.images.edit(
    model="gpt-image-2.5-sunburst",
    image=open("sunlit_lounge.png", "rb"),
    mask=open("mask.png", "rb"),
    prompt="...",
)
```

- Current edit-capable models: **`gpt-image-2.5-sunburst`** and **`gpt-image-2.5-flare`**.
  The `gpt-image-1` family is the previous generation.
- Parameters on the edits endpoint: `image` (note the `image[]` array form in the curl),
  `mask`, `prompt`, `model` (all required), plus `size`, `quality`, `background`,
  `output_format`, `n`.
- Mask requirements, quoted: "The image to edit and mask must be of the same format and
  size (less than 50MB in size). The mask image must also contain an alpha channel."
  Transparent (alpha 0) marks the region to regenerate.
- `input_fidelity` (`high`/`low`) is **not listed for the edits endpoint** in the current
  guide, though it exists on the older `gpt-image-1` / `gpt-image-1.5` generation path
  and is unsupported on `gpt-image-1-mini`. Do not rely on it for edits without testing.
- `background: transparent` worked on `gpt-image-1`; `gpt-image-2` /
  `gpt-image-2-2026-04-21` **error** on it. `status on the 2.5 models UNVERIFIED` -
  if you need transparency, cut locally, do not ask the API for it.

### FLUX

- **FLUX.1 Fill** - true mask-based inpainting: source image + mask (white = regenerate)
  + prompt. This is the one to use when you have a precise region.
- **FLUX.1 Kontext (pro/max)** - instruction-based editing, no mask; "apply localized
  edits ... while leaving untouched regions of the image pixel-stable". ~$0.04/image for
  Kontext Pro.
- FLUX.2 is current for generation and editing; klein/dev weights are self-hostable via
  Hugging Face (and would be far too slow on this iGPU).

`endpoint URLs and exact model strings UNVERIFIED` - docs.bfl.ai's index page did not
carry them. Read https://docs.bfl.ml/llms.txt before wiring.

### When local matting is right, and when generative is right

**Use the local matting model when the answer must be the original pixels.**

- The subject must survive byte-identical: a real product, a real person, a logo.
- You need a genuine alpha channel to composite over arbitrary future backgrounds.
- Volume, or offline, or no API key. (Right now: **no keys are set on this box**, so this
  is the only path that works today.)
- Anything that will be presented as a photograph of a real thing. A generative edit
  hallucinates detail - re-rendered fabric weave, a slightly different logo - and that is
  a factual problem, not an aesthetic one.

**Use generative editing when the answer is new pixels that never existed.**

- Removing an object and needing plausible content *behind* it.
- Replacing a background with a *scene* rather than a colour - matting gives you a
  cutout, it cannot invent a studio.
- Extending a frame (outpainting) to hit an aspect ratio the crop cannot reach.
- Relighting the subject to match a new environment.

**The combination beats either.** Cut with BiRefNet + `-vm` so the subject is exactly the
original pixels, generate the backdrop separately, composite locally. You keep the real
subject *and* get an invented scene, and you never pay a model to redraw a face.

---

## 6. Hosted APIs as the escape hatch

| Service | Price | Free tier | Endpoint |
| --- | --- | --- | --- |
| **Photoroom** | **$0.02/image**, plans from $20/mo | **10 free credits/month** | `docs.photoroom.com`, header `x-api-key` |
| Clipdrop | 1 credit per success; 100 free credits for dev; 60 req/min | 100 credits | `POST https://clipdrop-api.co/remove-background/v1`, header `x-api-key` |
| remove.bg | ~$0.20-0.27/image on subscription ($9/40, $39/200, $89/500) | first 50 API calls/month | `POST https://api.remove.bg/v1.0/removebg`, header `X-API-Key` |
| withoutBG | built into rembg as `-m withoutbg` | 50 free credits on signup | set `WITHOUTBG_API_KEY` |

```bash
curl -H 'X-API-Key: $KEY' -F 'image_file=@in.jpg' -F 'size=auto' \
  -f https://api.remove.bg/v1.0/removebg -o out.png                       # verified from remove.bg/api

curl -X POST https://clipdrop-api.co/remove-background/v1 \
  -H 'x-api-key: $KEY' -F 'image_file=@in.jpg' -o out.png                 # verified from clipdrop docs
```

remove.bg's own useful extras: `bg_color`, `type`, `crop`, `scale`, `position`,
`add_shadow`, `shadow_type`, `shadow_opacity`, `semitransparency`. PNG output capped at
10 MP; up to 50 MP via JPG/ZIP. Clipdrop caps at 25 MP / 30 MB.

**Has open source caught up? Mostly, yes - with one asterisk.**

The honest 2026 read across several independent comparisons: remove.bg still edges out
the open models on the hardest hair and translucency, but the gap is now small enough
that it is "less retouching afterward", not "works vs doesn't". BiRefNet produces
"noticeably cleaner masks" than the older open models on hair and translucent elements,
and for product photography with clean edges the difference is marginal. BEN v2 is
reported to lead BiRefNet specifically on hair.

For this machine the decision is not quality, it is **throughput**. BiRefNet is free and
30s/image on this CPU. Photoroom is $0.02 and ~1s. The crossover is around a few thousand
images a month, or the moment a deadline matters more than $20. remove.bg at 10x
Photoroom's price is hard to justify unless you specifically need `add_shadow` and
`semitransparency` doing the work for you.

**Recommendation for `/assets`: default to local BiRefNet. Add a Photoroom fallback only
if the user ever complains about throughput.** No key is set today, so hosted is not an
option at all right now - say so rather than writing a runbook nobody can execute.

---

## Sources

Repos and package metadata (all read directly, not summarised from a blog):

- rembg: https://github.com/danielgatis/rembg - README, `rembg/commands/i_command.py`,
  `rembg/commands/p_command.py`, `rembg/commands/d_command.py`, `rembg/bg.py`, `rembg/matting.py`
- rembg on PyPI: https://pypi.org/project/rembg/ (2.0.84, `requires_python <4.0,>=3.11`)
- onnxruntime on PyPI: https://pypi.org/project/onnxruntime/ (1.29.0, declares 3.14)
- torch on PyPI: https://pypi.org/project/torch/ (2.14.0, declares 3.14)
- BiRefNet: https://github.com/ZhengPeng7/BiRefNet (MIT)
- BRIA RMBG-2.0: https://huggingface.co/briaai/RMBG-2.0 (CC BY-NC 4.0)
- InSPyReNet / transparent-background: https://github.com/plemeri/transparent-background
  and https://pypi.org/project/transparent-background/ (1.3.4, 2025-05-14)
- BEN2: https://huggingface.co/PramaLLC/BEN2 , https://github.com/PramaLLC/BEN2 (MIT)
- SAM 3: https://github.com/facebookresearch/sam3 (custom Meta licence)
- ViTMatte: https://github.com/hustvl/ViTMatte (MIT)
- MODNet: https://github.com/ZHKKKe/MODNet (Apache-2.0, code *and* models)
- smartcrop: https://pypi.org/project/smartcrop/ (0.5.0, `>=3.10`, numpy + pillow only)
- Real-ESRGAN: https://github.com/xinntao/Real-ESRGAN ; AUR `realesrgan-ncnn-vulkan-bin`

APIs:

- Gemini image generation/editing: https://ai.google.dev/gemini-api/docs/image-generation
- Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- OpenAI image editing: https://developers.openai.com/api/docs/guides/image-generation
  (note: https://platform.openai.com/docs/api-reference/images/createEdit returns 403 to
  an unauthenticated fetch)
- FLUX: https://docs.bfl.ml/flux_1_fill , https://docs.bfl.ai/
- remove.bg: https://www.remove.bg/api
- Photoroom: https://www.photoroom.com/api/remove-background ,
  https://docs.photoroom.com/remove-background-api-basic-plan/pricing
- Clipdrop: https://clipdrop.co/apis/docs/remove-background

Comparisons used for the 2026 quality read (secondary sources, treated as opinion):

- https://invideo.io/blog/ai-background-removal-models/
- https://huggingface.co/spaces/bgsys/background-removal-arena (live Elo leaderboard -
  worth checking before the skill hardcodes a ranking)

Artefacts produced while researching, still on disk under this scratchpad:
`bgtest/edge-compare.png` (naive / -dc / -vm / -a at 300% on magenta),
`bgtest/shadow-compare3.png` (naive `-shadow` vs the two-layer ground shadow),
`bgtest/subjectcrop.sh`, `bgtest/bench.sh`, `im/unmix.py`.

---

## The background removal runbook

The single recommended path. No global installs, no pinned Python, no API key, nothing
sent to a third party.

**Step 0 - pick the model. Never omit `-m`.** The rembg default is `bria-rmbg`, which is
CC BY-NC 4.0. One forgotten flag turns a client deliverable into a licence problem.

| Subject | `-m` |
| --- | --- |
| Anything general | `birefnet-general` |
| A person | `birefnet-portrait` |
| Anime / illustration | `isnet-anime` |
| Subject and background similar in tone | `birefnet-cod` |
| Contact sheet / you will re-cut later | `isnet-general-use` (4 s) |

**Step 1 - cut it with ViTMatte.** `-vm` costs only ~3 s more than `-dc` on this machine
and recovers hair and fur strands that `-dc` alone leaves cut off flat. It also
decontaminates internally, so do not add `-dc`.

```bash
uv run --no-project --with "rembg[cpu,cli]" \
  rembg i -m birefnet-general -vm in.jpg cut.png
```

17-20 s warm for a 2000px image. ~31 s on the first run after a reboot, while the 928 MB
ONNX file pages in. The very first run ever adds a 928 MB + 110 MB download.

Quote `"rembg[cpu,cli]"` - in zsh the brackets are a glob and the command fails otherwise.

If the subject is hard-edged (a bottle, a phone, a logo) there is nothing soft to
refine, so use the cheaper flag and save the 3 s:

```bash
uv run --no-project --with "rembg[cpu,cli]" \
  rembg i -m birefnet-general -dc in.jpg cut.png
```

**Step 2 - look at it on magenta.** This is the step people skip and it is the whole
game. Magenta is the worst-case ground for the grey or green rim you are hunting.

```bash
magick cut.png -background magenta -flatten \
  -crop 400x300+X+Y +repage -filter point -resize 300% check.png
```

Then actually open `check.png`. Three failure modes, three different fixes:

| What you see | Fix |
| --- | --- |
| A coloured rim tracing the silhouette | You forgot `-dc`/`-vm`. Re-cut. If it survives `-vm`, go to step 3. |
| Hair or fur cut off flat | Widen the trimap's unknown band: add `-ae 20` (default 10). |
| A hard stair-stepped edge on something soft | `-vm` should fix it. If not, the model is wrong for the subject - try `birefnet-hrsod` or `birefnet-cod`. |
| A faint grey wash across the whole transparent area | `magick cut.png -channel A -level 5%,95% +channel cut.png` |

**Step 3 - only if a rim survived `-vm`, choke by exactly 1 px.** This is a last resort:
it hides the rim by deleting it, and it eats hair on the way past.

```bash
magick cut.png -channel A -morphology Erode Disk:1 +channel cut.png
```

**Step 4 - composite.** Flatten onto the brand ground; if the subject is meant to sit on
a surface, use the two-layer ground shadow from section 4, not `-shadow`.

```bash
magick -size 2000x2500 xc:"#0B3D2E" cut.png -gravity center -composite final.png
# or skip a process entirely, at cut time:  rembg i ... -bgc 11 61 46 255
```

**Step 5 - crop to the deliverable ratios** with `subjectcrop.sh` (section 4). It reads
the subject position out of `cut.png`'s alpha bounding box, so it needs no saliency
heuristic and cannot decapitate anyone.

```bash
./subjectcrop.sh cut.png in.jpg 1080 1350 out-4x5.jpg
./subjectcrop.sh cut.png in.jpg 1920 1080 out-16x9.jpg
```

**Batch variant.** `rembg p` reuses one ONNX session across the folder, which is far
faster than N `uv run` invocations:

```bash
uv run --no-project --with "rembg[cpu,cli]" \
  rembg p -m birefnet-general -vm ./in ./out
```

Spot-check three outputs at step 2 rather than all of them. Budget ~20 s per image:
a 500-image set is about 3 hours, at which point Photoroom at $0.02/image is the
better trade.

---

## Install once

Nothing here needs a global Python install and nothing needs a pinned Python. `uv` caches
each `--with` set, so the second run of a command is instant.

**Already present, no action:** ImageMagick 7.1.2-31 (with `lqr`, `jxl`, `heic`, `lcms`),
ffmpeg (with `lut3d`, `haldclut`, `curves`, `noise`), inkscape, rsvg-convert, avifenc,
uv 0.11.4, Python 3.14.7, and a Vulkan 1.4 RADV stack on the 880M.

**Downloaded on first use, cached forever:**

| What | Size | Where |
| --- | --- | --- |
| rembg + onnxruntime + numpy + pymatting (83 pkgs) | ~250 MB | `~/.cache/uv` |
| `birefnet-general` ONNX | **928 MB** | `~/.rembg/models/birefnet-general` |
| `vitmatte` small-distinctions-646 | **110 MB** | `~/.rembg/models/vitmatte` |
| `isnet-general-use` (optional fast preview) | 171 MB | `~/.rembg/models/isnet-general-use` |
| `bria-rmbg` (default - avoid, non-commercial) | 977 MB | `~/.rembg/models/bria-rmbg` |
| `smartcrop` + pillow + numpy (optional) | ~30 MB | `~/.cache/uv` |

**Total for the recommended path: ~1.3 GB** (uv cache + birefnet-general + vitmatte).
Measured on-disk after this research:

```
928M  ~/.rembg/models/birefnet-general
214M  ~/.rembg/models/birefnet-general-lite
977M  ~/.rembg/models/bria-rmbg          <- the default; you do not want it
171M  ~/.rembg/models/isnet-general-use
110M  ~/.rembg/models/vitmatte
168M  ~/.u2net                            <- u2net still lands in the legacy dir
```

Pre-warm so the first real request is not a 1 GB download. `rembg d` takes model names
as positional arguments (verified in `d_command.py`); it does **not** fetch the ViTMatte
weights, which download lazily on the first `-vm`, so do one real cut too:

```bash
uv run --no-project --with "rembg[cpu,cli]" rembg d birefnet-general
magick -size 800x800 xc:gray -fill white -draw "circle 400,400 400,150" /tmp/warm.png
uv run --no-project --with "rembg[cpu,cli]" \
  rembg i -m birefnet-general -vm /tmp/warm.png /tmp/warm.out.png   # pulls ViTMatte
```

Models live under `$REMBG_HOME`, defaulting to `$XDG_DATA_HOME/rembg` or `~/.rembg`.
Set `OMP_NUM_THREADS` if you want to stop ONNX Runtime saturating all 20 threads.

**Optional, only if you need upscaling:** `yay -S realesrgan-ncnn-vulkan-bin` (~80 MB
with weights) - runs on the 880M through Vulkan, no ROCm. `waifu2x-ncnn-vulkan` is in
`extra` if you only ever upscale illustration.

**Deliberately not installed:** `transparent-background` (pulls ~1.5 GB of torch, and
BiRefNet already covers the job - I did not benchmark InSPyReNet's edge quality here, so
this is a cost decision, not a measured quality verdict), BEN2 (torch plus a manual repo
checkout), any hosted-API client (no keys set).

