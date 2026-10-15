# Sourcing and coding assets - stock, icons, illustrations, shapes, optimization

> Research reference for the design pipeline. Compiled 2026-09-09 from primary
> sources; every tool, endpoint and browser-support figure was verified at that
> date and carries its URL inline. Items that could not be confirmed are marked
> UNVERIFIED - treat those as leads, not facts. Re-verify prices and model IDs
> before quoting them to a client.

# Research E: Non-generative asset sourcing (vectors, icons, shapes, stock photos)

Target: a Claude Code `/assets` skill.
Environment assumed: Arch Linux, node 24, Python 3.14 + uv.
Present: ImageMagick 7.1.2-31 (with `webp`, `heic`, `jxl`, `rsvg` delegates built in), ffmpeg,
avifenc (libavif), vtracer 0.6.5, potrace 1.16, inkscape, rsvg-convert.
Absent: cwebp, oxipng, svgo (svgo runs fine via `npx`; ImageMagick covers webp).
No API keys set.

Everything below marked as verified was checked by fetching the vendor's own docs or by
running the command locally in this environment on 2026-09-09. Anything not confirmed is
labelled `UNVERIFIED`.

---

## 1. Free-license stock photography

### 1.1 The five sources, verified

| Source | Key needed | Free? | Rate limit | License | Attribution | Hotlink rule |
|---|---|---|---|---|---|---|
| Unsplash | yes, `Client-ID` | yes | **50/hr demo, 1000/hr production** | Unsplash License | not legally required, but **required by the API guidelines** | **required** to hotlink `photo.urls.*` |
| Pexels | yes, `Authorization` | yes | **200/hr and 20,000/month** | Pexels License | not required by license; a "prominent link to Pexels" is required by the API terms | not required |
| Pixabay | yes | yes | **100 requests / 60 s** | Pixabay Content License | not required; must show users where results came from | **hotlinking prohibited**, must cache 24 h |
| Openverse | **no** | yes | **~5/hr, 100/day anonymous**; higher when registered | per-item (CC0 / CC BY / CC BY-SA / PDM) | **depends on item**, API returns the exact string | n/a |
| Wikimedia Commons | **no** | yes | no published hard cap; User-Agent policy applies | per-item (CC0 / CC BY / CC BY-SA / PD) | **usually required**, `extmetadata.AttributionRequired` says so | allowed via `upload.wikimedia.org` |

#### Unsplash (api.unsplash.com)

Verified against `https://unsplash.com/documentation` (raw HTML, so the numbers are exact) and
`https://help.unsplash.com/en/articles/2511245-unsplash-api-guidelines`.

- Base: `https://api.unsplash.com/`
- Auth header: `Authorization: Client-ID <ACCESS_KEY>` (or `?client_id=`).
- Rate limit, quoted from the docs: "For applications in demo mode, the Unsplash API currently
  places a limit of 50 requests per hour. After approval for production, this limit is increased
  to 1000 requests per hour." Response headers `X-Ratelimit-Limit` / `X-Ratelimit-Remaining`.
  Note: many blog posts claim 5000/hr for production. That is **wrong** as of the current docs.
- Demo -> production: upload screenshots showing correct attribution and the download trigger,
  then click "Request Approval". Approval reviews compliance with the API guidelines.
- **Hotlinking is mandatory**: "All API uses must use the hotlinked image URLs returned by the API
  under the `photo.urls` properties." Downloading the file to your own server and serving it from
  there is a guideline violation, which matters if a site is going to be public.
- **Download trigger is mandatory**: when a user actually selects a photo for use, fire
  `GET` on `photo.links.download_location` (equivalently `GET /photos/:id/download`).
- Attribution must credit Unsplash + the photographer + link to their profile, with
  `?utm_source=your_app_name&utm_medium=referral` on the links.
- License (`https://unsplash.com/license`): free for commercial and non-commercial, no permission
  needed, attribution appreciated but not legally required. Not allowed: selling unaltered copies,
  or compiling Unsplash images to replicate a competing service.
- Prohibited by the API guidelines: Unsplash branding in your app name or icon, unofficial clients
  or wallpaper apps, selling unaltered photos, excessive automated requests.

```bash
# UNTESTED here (no key set), but constructed straight from the documented endpoints.
export UNSPLASH_KEY=...   # https://unsplash.com/oauth/applications

# 1. search
curl -s "https://api.unsplash.com/search/photos?query=empty%20workshop%20morning%20light&per_page=12&orientation=landscape&content_filter=high&order_by=latest" \
  -H "Authorization: Client-ID $UNSPLASH_KEY" \
  -H "Accept-Version: v1" > u.json

# 2. inspect candidates: id, size, dominant colour, blur_hash, description
python3 - <<'PY'
import json
d=json.load(open('u.json'))
for r in d['results']:
    print(r['id'], r['width'], r['height'], r['color'], r.get('blur_hash'),
          (r.get('alt_description') or '')[:60],
          r['user']['name'], r['user']['links']['html'])
PY

# 3. REQUIRED before use: fire the download trigger (does not return the file)
PHOTO_ID=xxxxxxxx
curl -s "https://api.unsplash.com/photos/$PHOTO_ID/download" \
  -H "Authorization: Client-ID $UNSPLASH_KEY" | python3 -m json.tool

# 4. fetch the bytes for local processing (composition checks, LQIP). For a public site,
#    the rendered <img> must still point at the hotlinked photo.urls.raw/full URL.
curl -sL "$(curl -s "https://api.unsplash.com/photos/$PHOTO_ID" \
  -H "Authorization: Client-ID $UNSPLASH_KEY" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["urls"]["raw"])')&w=2000&q=80&fm=jpg" \
  -o hero.jpg
```

Unsplash raw URLs accept Imgix params (`&w=`, `&h=`, `&fit=crop`, `&crop=entropy`, `&q=`, `&fm=`,
`&dpr=`). That is how you satisfy the hotlink rule and still serve a right-sized image: build the
`srcset` out of the same raw URL with different `w=` values.

#### Pexels (api.pexels.com/v1)

Verified against `https://www.pexels.com/api/documentation/` and `https://www.pexels.com/license/`.

- Base `https://api.pexels.com/v1/`, header `Authorization: <API_KEY>` (no scheme prefix).
- 200 requests/hour, 20,000/month by default. Headers `X-Ratelimit-Limit`,
  `X-Ratelimit-Remaining`, `X-Ratelimit-Reset`.
- Search params: `query`, `orientation` (landscape|portrait|square), `size` (large|medium|small),
  `color` (named or hex), `locale`, `page`, `per_page` (max 80).
- Photo object `src`: `original, large2x, large, medium, small, portrait, landscape, tiny`.
  Also `avg_color` (useful as a placeholder background) and `alt`.
- License: free commercial use, **attribution not required**, modification allowed. Not allowed:
  identifiable people shown in a bad light, selling unaltered copies, implying endorsement,
  redistributing on another stock platform, using as a trademark.
- The API terms (separate from the license) do ask for a prominent link back to Pexels.

```bash
export PEXELS_KEY=...   # https://www.pexels.com/api/new/
curl -s "https://api.pexels.com/v1/search?query=concrete%20stairwell&orientation=landscape&per_page=15" \
  -H "Authorization: $PEXELS_KEY" -D headers.txt > p.json
grep -i ratelimit headers.txt
python3 - <<'PY'
import json
d=json.load(open('p.json'))
for p in d['photos']:
    print(p['id'], p['width'], p['height'], p['avg_color'], p['photographer'], p['url'])
PY
# download a specific one at full size
curl -sL "$(python3 -c "import json;print(json.load(open('p.json'))['photos'][0]['src']['original'])")" -o hero.jpg
```

#### Pixabay (pixabay.com/api)

Verified against `https://pixabay.com/api/docs/` and `https://pixabay.com/service/license-summary/`.

- Base `https://pixabay.com/api/`, key as `?key=`.
- **100 requests per 60 seconds** by default.
- **"Requests must be cached for 24 hours."** Permanent hotlinking of Pixabay URLs is prohibited:
  download to your own server. `webformatURL` is only valid for 24 hours.
- URL fields: `previewURL` (150px), `webformatURL` (640px), `largeImageURL` (1280px),
  `fullHDURL` (1920px), `imageURL` (original). **`fullHDURL`, `imageURL` and `vectorURL` are only
  returned if your account has been approved for full API access.**
- License: free commercial use, no attribution required. Not allowed: selling content standalone
  with no creative effort applied, commercial use of recognisable trademarks/logos in the frame,
  immoral/illegal use of content with recognisable people, misleading use, use as a trademark.
- Pixabay also hosts vectors: `image_type=vector` returns SVG/EPS. That is a genuinely useful
  non-photo channel and it is CC0-like under the same Content License.

```bash
export PIXABAY_KEY=...   # free account, key shown on https://pixabay.com/api/docs/
curl -s -G "https://pixabay.com/api/" \
  --data-urlencode "key=$PIXABAY_KEY" \
  --data-urlencode "q=rain on window" \
  --data-urlencode "image_type=photo" \
  --data-urlencode "orientation=horizontal" \
  --data-urlencode "min_width=2000" \
  --data-urlencode "editors_choice=false" \
  --data-urlencode "safesearch=true" \
  --data-urlencode "per_page=20" > px.json
python3 -c "
import json;d=json.load(open('px.json'))
[print(h['id'],h['imageWidth'],h['imageHeight'],h['user'],h['largeImageURL']) for h in d['hits']]"
curl -sL "$(python3 -c "import json;print(json.load(open('px.json'))['hits'][0]['largeImageURL'])")" -o hero.jpg
```

#### Openverse (api.openverse.org) - VERIFIED LIVE, no key

This one actually ran here. It is the only image search API in this list that works with zero
setup, which makes it the right default for an agent.

```bash
# verified working, returned 240 results, HTTP 200
curl -s "https://api.openverse.org/v1/images/?q=misty%20forest&license_type=commercial&page_size=2&aspect_ratio=wide" \
  -H "User-Agent: my-app/1.0"
```

- Base: `https://api.openverse.org/v1/`. Endpoints: `/images/`, `/images/{id}/`,
  `/images/{id}/related/`, `/images/{id}/thumb/`, plus `/audio/`.
- Useful params seen in live responses and the schema: `q`, `license` (e.g. `cc0,by`),
  `license_type` (`commercial`, `modification`, `commercial,modification`), `source` (`flickr`,
  `wikimedia`, ...), `extension`, `aspect_ratio` (`tall|wide|square`), `size`,
  `category` (`photograph|illustration|digitized_artwork`), `page_size`, `page`.
- Rate limits: anonymous is roughly **5/hour and 100/day** (reported in Openverse docs coverage;
  the throttling reference page describes standard/enhanced/exempt tiers but does not print the
  numbers, so treat the exact anonymous figure as `UNVERIFIED` and just register). Register via
  `POST /v1/auth_tokens/register/` then `POST /v1/auth_tokens/token/` with
  `grant_type=client_credentials` to get the standard tier.
- Every result carries a ready-made `attribution` string, e.g.
  `"Misty forest and twisting tree |" by *Arielle* is licensed under CC BY 2.0. ...`
  Use that string verbatim; it is the single best attribution ergonomics of any source here.
- Filter to `license=cc0,pdm` if you want to skip attribution entirely.
  Filter to `license_type=commercial,modification` for a safe default.

```bash
# CC0-only, wide, commercial, ready to drop into a hero with no credit line
curl -s -G "https://api.openverse.org/v1/images/" \
  --data-urlencode "q=fog over pine ridge" \
  --data-urlencode "license=cc0,pdm" \
  --data-urlencode "aspect_ratio=wide" \
  --data-urlencode "category=photograph" \
  --data-urlencode "page_size=20" \
  -H "User-Agent: assets-skill/1.0" > ov.json
python3 - <<'PY'
import json
d=json.load(open('ov.json'))
for r in d['results']:
    print(r['id'], r['width'], r['height'], r['license'], r['source'], r['title'][:50])
    print('   ', r['url'])
PY
curl -sL "$(python3 -c "import json;print(json.load(open('ov.json'))['results'][0]['url'])")" -o hero.jpg
```

#### Wikimedia Commons - VERIFIED LIVE, no key

Best for anything real and specific: architecture, machinery, places, historical material,
scientific imagery. It is the antidote to "stock photo look" because almost nothing on it was
shot to sell.

```bash
# verified working
curl -s -H "User-Agent: assets-skill/1.0 (you@example.com)" \
 "https://commons.wikimedia.org/w/api.php?action=query&format=json\
&generator=search&gsrsearch=filetype:bitmap%20brutalist%20concrete%20facade\
&gsrlimit=10&gsrnamespace=6&prop=imageinfo\
&iiprop=url|size|extmetadata&iiurlwidth=1600" > wc.json

python3 - <<'PY'
import json,re,html
d=json.load(open('wc.json'))
strip=lambda s: html.unescape(re.sub('<[^>]+>','',s or ''))
for p in d['query']['pages'].values():
    ii=p['imageinfo'][0]; em=ii.get('extmetadata',{})
    print(p['title'])
    print('  ', ii['width'],'x',ii['height'], em.get('LicenseShortName',{}).get('value'),
          '| attribution required:', em.get('AttributionRequired',{}).get('value'))
    print('   artist:', strip(em.get('Artist',{}).get('value'))[:60])
    print('   thumb :', ii.get('thumburl'))
PY
```

`iiurlwidth=N` makes the API render a thumbnail at that width for you, so you never have to pull
a 4032x3024 original just to evaluate a candidate. `extmetadata.AttributionRequired` is the field
to gate on: `true` means you must render a credit line. `License` gives the machine id
(`cc-by-4.0`, `cc-by-sa-4.0`, `cc0`, `pd`). **Avoid CC BY-SA for anything composited into a
derivative work**, since ShareAlike can reach your derivative.

#### Other genuinely-free sources worth knowing (no usable APIs)

- **Gratisography** - deliberately weird, un-stock-like, its own no-copyright-restrictions
  licence. Small library. No API.
- **Kaboompics** - each photo ships with an extracted colour palette, which is unusually useful
  when the whole point is matching a set to a palette. Free commercial, no redistribution. No API.
- **Picjumbo**, **Burst (Shopify)**, **StockSnap**, **Life of Pix** - free, no APIs.
- **Reshot** was the classic "authentic, non-stocky" recommendation. **It was retired by Envato
  and its assets stopped being downloadable in January 2026.** Do not point users at it.
- **Flickr** with `license=4,5,9,10` (CC BY, CC BY-SA, PDM, CC0) via the Flickr API is another
  route, but Openverse already indexes Flickr, so use Openverse and skip the extra key.

### 1.2 The harder half: picking images that do not scream "stock photo"

Synthesised from Shutterstock's own art-direction guidance, Modern Tribe, 99designs, and the
Harvard DCE photography guidelines. Every rule below is written so an agent can actually apply it.

**Rule 1 - never search the concept, search the scene.**
The worst stock photos are literal illustrations of their own keyword. Searching `teamwork`,
`success`, `business`, `innovation`, `happy` returns the most-downloaded, most-reused images on
the internet. Translate the concept into a physical scene before searching:
- "collaboration" -> `two people at a whiteboard shot from behind`, `messy desk sticky notes`
- "security" -> `steel door hinge macro`, `fog over a fence line`
- "growth" -> `scaffolding against sky`, `seedling in cracked pavement`
- "speed" -> `long exposure motorway at dusk`
Concrete nouns and materials beat abstractions every time.

**Rule 2 - reject the stock-pose vocabulary outright.**
Auto-reject a candidate whose description or visible content includes any of:
arms crossed, thumbs up, handshake, high five, jumping in the air, laughing while eating salad,
pointing at a laptop screen, a headset, a lone person in a suit against white seamless,
a diverse team in a glass meeting room, "isolated on white background".
These are the specific cliches named repeatedly in art-direction writing.

**Rule 3 - prefer environmental and candid over posed-to-camera.**
If the primary subject is a person looking directly into the lens with a performed expression,
skip it. Prefer: subject in profile, subject turned away, subject partially cropped by the frame,
hands only, back of head, mid-action with motion blur. A face performing an emotion reads as
staged; a face experiencing one reads as documentary.

**Rule 4 - light is the tell.**
Reject flat, evenly-lit, overexposed studio light. Prefer: directional natural light, visible
shadow shape, colour cast from a real source (window, sodium lamp, screen glow), lens artefacts
(slight flare, grain, shallow depth of field with an unclean bokeh). Perfect evenness is the
signature of both studio stock and image models.

**Rule 5 - negative space is a hard requirement for anything with text over it.**
Before accepting a hero candidate, verify it programmatically. Crop the region where the copy
will sit and measure the standard deviation of luminance there; high variance means the text will
not be legible without a scrim, which is a worse design than picking a better photo.

```bash
# Score the left 45% of an image (where hero copy usually goes) for text-overlay suitability.
# Low stddev = calm area = good. Also report mean luminance to choose light or dark type.
score_overlay() {
  local f="$1" region="${2:-45x100%+0+0}"
  magick "$f" -crop "$region" +repage -colorspace Gray \
    -format "file=%f  mean=%[fx:int(mean*100)]  stddev=%[fx:int(standard_deviation*100)]\n" info:
}
score_overlay hero.jpg            # left 45%
score_overlay hero.jpg "100%x40%+0+0"   # top band, for a nav overlay
# Heuristic: stddev < 12 is comfortably calm, 12-20 needs a gradient scrim,
# > 20 means pick a different photo. mean < 45 -> use light type, > 60 -> dark type.
```

**Rule 6 - test the crop the layout actually needs, not the crop the photographer chose.**
A 3:2 photo that is perfect will often die at 21:9 or on a 4:5 mobile hero. Check before you
commit, and check that the subject survives a centre crop.

```bash
# Does the subject survive the aspect ratios this layout uses?
# VERIFIED: ImageMagick 7's -extent accepts an aspect-ratio geometry directly,
# so the whole check is one line per ratio. -resize WxH^ fills, -extent crops.
for ar in 21:9 16:9 4:3 1:1 4:5 9:16; do
  magick test.jpg -gravity center -resize 1600x1600^ -extent "$ar" +repage \
         -resize 480x "crop-${ar/:/x}.jpg"
done
magick identify crop-*.jpg
# -> crop-21x9.jpg 480x206, crop-16x9.jpg 480x270, crop-1x1.jpg 480x480,
#    crop-4x5.jpg 480x600, crop-9x16.jpg 480x853
# Then actually Read the generated crops. Eyeballing 6 crops takes 10 seconds and
# catches the failure that a metadata-only pipeline never sees.
```

**Rule 7 - a set must share a colour temperature and a contrast level.**
The single most reliable "these came from a template" signal is three photos on one page shot in
three different lighting worlds. Measure it, do not eyeball it.

```bash
# Print mean hue/sat/lightness per candidate; reject outliers from the set's median.
for f in cand-*.jpg; do
  magick "$f" -resize 200x200! -colorspace HSL \
    -format "%f  H=%[fx:int(mean.r*360)]  S=%[fx:int(mean.g*100)]  L=%[fx:int(mean.b*100)]\n" info:
done
# Also grab the 5-colour palette so you can check it against the site tokens:
magick hero.jpg -resize 200x200 -colors 5 -unique-colors txt: | tail -n +2
```
Rule of thumb for a set of 3-6: keep mean L within +/-12 points, mean S within +/-15 points, and
mean H within a 60-degree arc unless you are deliberately doing a complementary pair.
If a candidate is right in content but wrong in temperature, correct it rather than reject it:

```bash
# Warm a cool image toward the set (mild, non-destructive)
magick cold.jpg -modulate 100,105,98 -channel R -evaluate multiply 1.04 \
  -channel B -evaluate multiply 0.97 +channel warmed.jpg
# Or push everything to a shared duotone so the set is unmistakably one system
magick any.jpg -colorspace Gray \
  \( -size 1x256 gradient:"#0b2b23-#f0e2c4" -rotate 90 \) -clut duotone.jpg
```
A duotone or a shared grade is the professional answer to "these free photos do not match".
It is also the fastest way to make free stock stop looking free.

**Rule 8 - no visible branding, no dated tech, no legible screens.**
Logos on clothing and props create both a legal problem (explicitly called out in Pixabay's
licence for commercial use) and an authenticity problem. A 2014-era laptop or phone dates a page
instantly. A legible UI on a screen inside the photo competes with your actual UI.

**Rule 9 - abstract for literal copy, literal for abstract copy.**
If the headline is concrete ("Ship in 4 weeks"), the image should be atmospheric. If the headline
is abstract ("Built for what comes next"), the image should be a specific, concrete object. Never
match the register of the copy; the doubling is what reads as cheap.

**Rule 10 - prefer sources whose corpus is not for sale.**
Wikimedia Commons and Openverse's Flickr corpus were shot to document, not to sell. That is a
structural advantage over any curated free-stock site, whose whole library was uploaded with
commercial appeal in mind.

### 1.3 Can you detect that an image is overused?

There is no free, unauthenticated "how many sites use this image" API. Here is the honest picture:

- **TinEye API**: the only real answer, and it is not free. Pricing starts around **$200/month
  for 5,000 searches** (also sold as bundles down to about $0.01/search at 1M volume). The web UI
  at tineye.com is free for manual, non-commercial checks. Suitable as an optional, key-gated
  step in a skill; not suitable as a default.
- **Google Lens / Google Images**: no public API for reverse image search. Do not build on it.
- **Unsplash `downloads` count - the practical free proxy.** `GET /photos/:id` returns a
  `downloads` field, and `GET /photos/:id/statistics?resolution=days&quantity=30` returns
  download and view series. Both verified in the Unsplash docs. Use it as a hard filter.

```bash
# Free overuse proxy on Unsplash: reject anything above a download threshold.
for id in $(python3 -c "import json;[print(r['id']) for r in json.load(open('u.json'))['results']]"); do
  n=$(curl -s "https://api.unsplash.com/photos/$id" -H "Authorization: Client-ID $UNSPLASH_KEY" \
      | python3 -c 'import json,sys; print(json.load(sys.stdin).get("downloads",0))')
  echo "$n $id"
done | sort -rn
# Heuristic: > 100,000 downloads means the image is on thousands of sites already.
# > 20,000 means it is common. Under ~5,000 is comparatively safe.
# One widely-cited example has been downloaded close to 400,000 times and shows up on
# websites, billboards and ads simultaneously.
```

- **Free structural mitigations that need no API at all**, and which matter more than detection:
  1. `order_by=latest` instead of the default `relevant` on Unsplash search. Relevance ranking is
     largely download-driven, so the default *is* the overused set.
  2. Page deeper. Never take from page 1 results 1-5. Take from page 2 or 3.
  3. Use long, specific, multi-noun queries. A query with 4+ concrete words rarely returns a
     top-100 image at all.
  4. Prefer Openverse and Commons, whose corpora are not download-ranked in the same way.
  5. Crop, grade, and composite. An image that has been re-cropped to 21:9, duotoned to the brand
     palette and grain-overlaid is no longer recognisable as the stock photo it came from, which
     is the actual goal.

---

## 2. Icons

### 2.1 Iconify API - VERIFIED LIVE, free, unauthenticated

Public API at `https://api.iconify.design`. From the Iconify docs: "Iconify project offers public
API servers, which host over 300k icons from more than 200 open source icon sets... It is a public
service, servers are free to use." No key, no account, no auth header. Version endpoint returned
`Iconify API version 3.2.0 (US-EAST)` here. `/collections` returned **238 icon sets**.

All of the following were run in this environment and returned HTTP 200.

```bash
# ---- single SVG ----------------------------------------------------------
# /{prefix}/{name}.svg
curl -s "https://api.iconify.design/lucide/arrow-right.svg?height=24" -o arrow.svg
# -> <svg ... viewBox="0 0 24 24"><path fill="none" stroke="currentColor"
#      stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
#      d="M5 12h14m-7-7l7 7l-7 7"/></svg>
# Note: stroke="currentColor" is preserved. This is the whole ballgame (see 2.4).

# params: color, width, height, flip, rotate, download, box
curl -s "https://api.iconify.design/lucide/arrow-right.svg?color=%23ff0000&width=32"
#   "#" MUST be percent-encoded as %23.
#   height=unset / height=none removes the width+height attrs, keeping viewBox.
#   box=1 adds a transparent rect matching the viewBox (for Figma/Sketch import).

# ---- bulk fetch (one request per icon set) --------------------------------
# /{prefix}.json?icons=a,b,c
curl -s "https://api.iconify.design/lucide.json?icons=arrow-right,check,x&pretty=1"
# -> {"prefix":"lucide","lastModified":...,"width":24,"height":24,
#     "icons":{"arrow-right":{"body":"<path .../>"}, ...}}
# You cannot mix prefixes in one query. Sort names alphabetically for cache hits.
# Keep the URL under ~500 chars; split into multiple queries beyond that.

# ---- CSS generation (icons as mask, colourable by currentColor) -----------
curl -s "https://api.iconify.design/lucide.css?icons=arrow-right,check,x"
# emits .icon--lucide { background-color: currentColor; mask-image: var(--svg) } plus
# one --svg data-URI rule per icon. Zero JS, zero runtime, zero extra requests.

# ---- search ---------------------------------------------------------------
curl -s "https://api.iconify.design/search?query=calendar&prefixes=lucide&limit=32"
# -> {"icons":["lucide:calendar", ...], "total":22, "limit":32, "start":0,
#     "collections":{"lucide":{...}}, "request":{...}}
# params: query (required), limit (min 32, default 64, max 999), start,
#         prefix, prefixes (comma list, trailing "-" matches families), category

# ---- discovery / housekeeping ---------------------------------------------
curl -s "https://api.iconify.design/collections"            # all 238 sets + licences
curl -s "https://api.iconify.design/collection?prefix=lucide"  # every icon name in a set
curl -s "https://api.iconify.design/last-modified?prefixes=lucide,tabler"
#   -> {"lastModified":{"tabler":1785257700,"lucide":1788788212}}  (cache invalidation)
curl -s "https://api.iconify.design/version"
```

Watch out: the prefix is **not** the marketing name. Phosphor is `ph`, not `phosphor`. Remix Icon
is `ri`. Bootstrap Icons is `bi`. Radix is `radix-icons`. A search with a wrong prefix silently
returns fewer results rather than erroring. Always resolve the prefix from `/collections` first.

### 2.2 The major open sets, with licences and grids read from `/collections` (verified)

| Prefix | Name | Icons | Licence | Grid | What it is stylistically for |
|---|---|---|---|---|---|
| `lucide` | Lucide | 1816 | ISC | 24 | The safe default. Feather's successor, actively maintained. 2px stroke, round caps/joins, geometric but friendly. Reads as "well-made modern product". Smallest set here, which is a feature: it forces consistency. |
| `ph` | Phosphor | 9072 | MIT | 24 | The one to pick when weight is a design tool. Six cuts per concept: thin, light, regular, bold, fill, duotone. Slightly softer and more humanist than Lucide. Use `ph:x` for regular, `ph:x-bold`, `ph:x-fill`, `ph:x-duotone`. |
| `tabler` | Tabler | 6184 | MIT | 24 | Dashboard workhorse. Same 24/2px/round philosophy as Lucide, slightly lighter stroke, 6px corner radius, and roughly 3.5x the coverage. Pick it when Lucide will run out of icons. |
| `heroicons` | Heroicons | 1288 | MIT | mixed (20/24) | Tailwind's official set. Two grids on purpose: 24px outline for UI, 20px and 16px solid for dense/inline. Cleanest match for a Tailwind-native design language. |
| `radix-icons` | Radix Icons | 332 | MIT | **15** | The 15px grid is the point. Crisp, tiny, editorial, very restrained. Excellent for dense developer tooling UI. Do not mix with a 24px set: the optical mismatch is unmissable. |
| `iconoir` | Iconoir | 1671 | MIT | 24 | Hand-tuned, more idiosyncratic line work than Lucide. A bit more character, a bit less neutral. Good when Lucide feels too default. |
| `ri` | Remix Icon | 3188 | Apache-2.0 | 24 | Neutral, systematic, ships both `-line` and `-fill` for nearly everything. Strong for apps that need a filled active state. |
| `material-symbols` | Material Symbols | 15618 | Apache-2.0 | 24 | The variable-font set. Four axes: FILL 0..1, wght 100..700, GRAD -50..200, opsz 20..48. Correct choice for Android-adjacent or Material-native products, wrong choice for anything trying not to look like Google. |
| `bi` | Bootstrap Icons | 2078 | MIT | **16** | 16px grid, heavier and blockier. Right when the rest of the page is Bootstrap. Otherwise dated. |
| `feather` | Feather | 286 | MIT | 24 | **Effectively frozen.** Lucide is the maintained fork. Use Lucide instead unless you are matching an existing Feather codebase. |
| `hugeicons` | Hugeicons | 5979 | MIT | 24 | Large, modern, multiple stylistic families (stroke rounded / sharp / twotone / bulk / solid). Useful when you want a distinct look without leaving open licensing. |
| `solar` | Solar | 7608 | **CC BY 4.0** | 24 | Soft, rounded, slightly playful, many variants (linear/bold/broken/duotone/outline). **Attribution required** - the only set in this table that is not a permissive code licence. Check before shipping. |

Also worth knowing: `mingcute` (3320, Apache-2.0, 24), `carbon` (2618, Apache-2.0, **32** grid),
`fluent` (19757, MIT, mixed), `octicon` (749, MIT), `line-md` (1218, MIT, animated),
`streamline` (3000, **CC BY 4.0**), `pixelarticons` (1036, MIT).

Licence gotcha to encode: **`solar` and `streamline` are CC BY 4.0**, everything else in the table
is MIT / ISC / Apache-2.0. `/collections` exposes `license.spdx` per set, so a skill can gate on it
mechanically rather than from a hardcoded list:

```bash
curl -s https://api.iconify.design/collections | python3 -c "
import json,sys
d=json.load(sys.stdin)
for k,v in sorted(d.items()):
    spdx=(v.get('license') or {}).get('spdx','?')
    if spdx not in ('MIT','ISC','Apache-2.0','CC0-1.0','Unlicense'):
        print(f'{k:24} {spdx:16} {v[\"name\"]}')
" | head -30
```

### 2.3 Mixing icon sets is a visible AI tell

This is the single most common giveaway in generated UI, and it is trivially avoidable.

Why it shows: each set is drawn on a fixed grid with a fixed stroke width, a fixed terminal style
(round vs butt caps), a fixed corner radius, and a fixed optical density. Put a Lucide chevron
(24 grid, 2px round) next to a Radix chevron (15 grid, ~1px butt) next to a Material Symbols
chevron (24 grid, variable weight, filled counters) in the same row, and a human reads
"assembled from whatever was to hand" before they can name why.

The rules an agent should follow, in priority order:

1. **One icon set per project. Not per page, per project.** Declare the prefix once and never
   deviate. If the set lacks an icon, the correct move is to redraw a substitute in the same set's
   idiom, or change the UI so the icon is not needed. It is never to grab one from another set.
2. **Brand marks are the only exception**, and they get their own bucket. GitHub, Google, Slack,
   X, Stripe logos come from `simple-icons` (CC0-1.0, `si:`) or the vendor's own brand kit. They
   are not UI icons and they are not held to the UI icon's stroke rules. Keep them visually
   separated from the UI icon set (different size, different container).
3. **One weight per set.** Phosphor's six cuts are six sets for this purpose. Choose regular, and
   use exactly one other cut (usually `-fill`) for a single specific meaning such as active tab
   state. Never sprinkle bold and thin at random.
4. **If a set is 15px or 16px grid (Radix, Bootstrap), do not put it beside a 24px set.**
5. **Enforce it mechanically.** A grep over the codebase for prefixes is a real test:

```bash
# Fails the build if more than one Iconify prefix appears in the source.
grep -rhoE '\b(lucide|ph|tabler|heroicons|radix-icons|iconoir|ri|material-symbols|bi|feather|hugeicons|solar|mdi|fa6-solid|fa-solid):[a-z0-9-]+' src/ \
  | cut -d: -f1 | sort -u > /tmp/prefixes.txt
n=$(grep -vc '^si$' /tmp/prefixes.txt)   # simple-icons excluded, brand marks are allowed
[ "$n" -le 1 ] || { echo "FAIL: mixed icon sets:"; cat /tmp/prefixes.txt; exit 1; }
```

### 2.4 Stroke width, optical size, and sizing against text

**`currentColor` is the convention and it is non-negotiable.** Every well-made open icon set
emits `stroke="currentColor"` or `fill="currentColor"` (verified above in the raw Lucide response).
That single token means the icon inherits `color` from its parent, so it themes for free: dark
mode, hover states, disabled states, and `:focus-visible` all work with zero extra CSS.

```html
<!-- correct: icon follows the text colour, including on hover -->
<a class="link">
  <svg width="1em" height="1em" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
    <path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
          stroke-linejoin="round" d="M5 12h14m-7-7l7 7l-7 7"/>
  </svg>
  <span>Continue</span>
</a>
```
```css
.link { color: var(--fg); display: inline-flex; align-items: center; gap: .5ch; }
.link:hover { color: var(--accent); }   /* icon recolours automatically */
```

Never hardcode `stroke="#111"` into an inline icon. If you fetch from the Iconify API with
`?color=`, you have deliberately baked in a palette and given up theming; only do that for an
`<img src>` or a CSS `content:` URL, where `currentColor` cannot reach.

**Sizing against text.** Set the icon box to `1em` and let the type scale drive it. This is the
whole trick and it removes a whole class of manual tuning.

```css
.icon {
  width: 1em; height: 1em;
  flex: none;                 /* never let flexbox squash an icon */
  vertical-align: -0.125em;   /* optical baseline correction: icons are centred on the
                                 em box, text sits on the baseline. -0.125em is the
                                 standard nudge for a 24-grid icon at typical line-height. */
}
/* an icon that must read as a peer of the text, not a decoration */
.icon--lead { width: 1.25em; height: 1.25em; }
```

For standalone (non-inline) icons, size on the 4px grid and pin the stroke:

| Context | Box | Stroke on a 24 grid |
|---|---|---|
| Inline with body text | 1em (~16px) | 2 (Lucide default reads correctly here) |
| Buttons, list rows, inputs | 20px | 2 |
| Nav, toolbars | 24px | 2 |
| Section headers, feature cards | 32px | 1.5 |
| Hero / empty-state | 48px+ | 1.25 - 1.5 |

**Optical size is the rule most generated UI gets wrong.** Stroke width is expressed in the
icon's own viewBox units, so it scales with the box. A 2px stroke on a 24 grid rendered at 48px
becomes a visually 4px stroke, which is far heavier than the 48px type beside it. Real icon
systems compensate. Two ways:

```css
/* 1. Set-agnostic: override stroke-width as the box grows. Works on any stroke-based set
      (lucide, tabler, feather, iconoir, ri -line, heroicons outline). */
.icon      { width: 1.5rem; height: 1.5rem; stroke-width: 2; }
.icon--lg  { width: 2rem;   height: 2rem;   stroke-width: 1.75; }
.icon--xl  { width: 3rem;   height: 3rem;   stroke-width: 1.5;  }
.icon--2xl { width: 4rem;   height: 4rem;   stroke-width: 1.25; }
/* requires the <svg> to inherit stroke-width, i.e. the path must NOT hardcode it.
   Strip it once at build time: sed -i 's/ stroke-width="2"//g' icons/*.svg
   and set stroke-width on the .icon class instead. */

/* 2. Material Symbols only: the font has a real opsz axis for exactly this. */
.ms {
  font-family: 'Material Symbols Outlined';
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
.ms--sm { font-size: 20px; font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 20; }
.ms--lg { font-size: 40px; font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 40; }
/* Match opsz to the rendered px size. Axes verified from
   https://developers.google.com/fonts/docs/material_symbols :
   FILL 0..1, wght 100..700, GRAD -50..200, opsz 20..48. Defaults wght 400, opsz 48, GRAD 0, FILL 0. */
```

Also pin stroke geometry so it matches across every icon you touch: `stroke-linecap: round`,
`stroke-linejoin: round`, `fill: none` for Lucide/Tabler/Feather/Iconoir. If you hand-draw a
missing icon, matching those three plus the grid is what makes it invisible in the set.

**Accessibility, non-negotiable:** decorative icons get `aria-hidden="true" focusable="false"`;
an icon that *is* the only label needs an accessible name on the control
(`<button aria-label="Close">`), not on the svg.

### 2.5 Zero-runtime icon delivery

Best default for a static site or an SSR app: fetch the SVG bodies at build time and inline them.
No client JS, no extra request, `currentColor` intact.

```bash
# Build a local icon sprite/module from one set, at build time, from the verified API.
ICONS="arrow-right,check,x,chevron-down,external-link,search,menu"
curl -s "https://api.iconify.design/lucide.json?icons=$ICONS" > icons.json
python3 - <<'PY'
import json
d = json.load(open('icons.json'))
vb = f"0 0 {d.get('width',24)} {d.get('height',24)}"
parts = ['<svg xmlns="http://www.w3.org/2000/svg" style="display:none"><defs>']
for name, ic in sorted(d['icons'].items()):
    body = ic['body']
    w = ic.get('width', d.get('width', 24)); h = ic.get('height', d.get('height', 24))
    parts.append(f'<symbol id="i-{name}" viewBox="0 0 {w} {h}">{body}</symbol>')
parts.append('</defs></svg>')
open('sprite.svg','w').write(''.join(parts))
print('wrote sprite.svg with', len(d['icons']), 'symbols')
PY
```
```html
<!-- inline the sprite once in the document, then reference by id -->
<svg class="icon" aria-hidden="true"><use href="#i-arrow-right"/></svg>
```
`<use>` from an *inlined* sprite inherits `currentColor`. `<use href="sprite.svg#id">` from an
external file does **not** inherit page CSS in all engines, so inline the sprite.

---

## 3. Illustrations

### 3.1 Licences, verified where a licence page exists

| System | Licence | Attribution | Notes |
|---|---|---|---|
| **unDraw** | own open licence (verified at undraw.co/license) | **not required** | Commercial OK, modification OK. Explicitly **prohibits use for AI/ML training or fine-tuning without written permission**, prohibits redistributing as packs, prohibits building a competing service, prohibits scraping. |
| **Open Peeps** | **CC0** (verified at openpeeps.com) | not required | Pablo Stanley. Hand-drawn, mix-and-match. ~584k combinations. |
| **Humaaans** | CC0-style, no attribution (`UNVERIFIED` - could not reach a formal licence page) | not required | Pablo Stanley. Geometric mix-and-match bodies. |
| **Blush** | mixed per-pack; free tier gives commercial rights, paid tiers unlock more | varies by artist | Also Pablo Stanley. Each pack has its own artist and terms - **check per pack**. |
| **Popsy** | free for commercial use (`UNVERIFIED` in detail) | not required | Notion-adjacent hand-drawn style. |
| **Storyset** | free tier requires attribution (verified at storyset.com/terms) | **required** unless you buy a Flaticon Premium subscription | Animated + static, per-scene colour customisation. |
| **DrawKit** | free set: no attribution required for free or paid | not required | Paid packs are the bulk of the catalogue now. |
| **IRA Design** | MIT (`UNVERIFIED` - claimed MIT by Creative Tim, not confirmed on a licence page) | - | Gradient-blob + character builder. Aesthetically very 2019. |
| **Absurd Illustrations** | free tier **requires** attribution, verbatim: "Illustration(s) from absurd.design" (verified) | **required** on free tier; paid removes it | Surrealist hand-drawn. Genuinely distinctive. |
| **Glaze** | free, hand-drawn (`UNVERIFIED`) | - | |
| **Croods** | free (`UNVERIFIED`) | - | Character constructor. |

### 3.2 Which of these are themselves an AI/template tell

Bluntly: **unDraw and Humaaans are the tell.** Both are the canonical sources of "Corporate
Memphis" (also called Alegria / Big Tech flat art) - flat geometric people with elongated limbs,
no facial features, and a two-to-three-colour brand-accented palette. It was the dominant
aesthetic of late-2010s tech, it became a meme, and the brands that popularised it (Airtable,
Zendesk, Asana, Hinge) have all since moved to photography or 3D. Any 2026 site with unDraw
illustrations reads as either a 2019 template or an unsupervised generation.

Ranked by how strong the tell is:

- **Strongest tell**: unDraw (the default accent colour `#6c63ff` is itself a fingerprint),
  Humaaans, IRA Design's gradient blobs.
- **Medium**: Storyset (very common on free-tier marketing pages), Open Peeps (heavily used but
  the hand-drawn line saves it somewhat), generic Popsy scenes.
- **Weak / still usable**: Absurd Illustrations (distinctive enough that it reads as a choice),
  Blush packs from a specific artist, DrawKit's more recent hand-drawn sets, Croods.

Note also that unDraw's own licence now forbids using its assets for AI/ML training. That is a
separate reason to keep them out of any pipeline that might feed a model.

### 3.3 What to do instead for a project that needs a consistent illustration style

In descending order of how well it works, and all of them are code-or-craft, not stock:

1. **Do not use illustrations.** The most common correct answer. Most pages reaching for spot
   illustrations are trying to fill space that wants typography, real product screenshots, or a
   photograph. A cropped screenshot of the actual product beats any illustration for a SaaS site.
2. **Code-generated abstract geometry** (Section 4). A consistent system of blobs, gradient
   meshes, grain and shapes, generated from a seeded function with the project's palette, is
   automatically consistent, automatically unique, weighs a few hundred bytes, and cannot be
   traced to a stock library. This is the strongest general-purpose alternative and it is the
   reason Section 4 is the longest section here.
3. **One artist, one pack.** If illustration is genuinely needed, pick a single Blush pack by a
   single artist, or a single DrawKit set, and use only that. The failure mode is never "the
   illustration style is bad"; it is "three illustrations on the page come from three libraries".
   Consistency of character proportion, line weight, palette and perspective is what makes a set
   read as one system.
4. **Recolour whatever you pick to the project palette, mechanically.** Almost every free
   illustration ships as SVG with hardcoded hex fills. Rewrite them to CSS custom properties so
   they cannot drift and so they theme:

```bash
# Turn a downloaded illustration into a themeable component.
# 1. see what colours it actually uses
grep -oE '#[0-9a-fA-F]{3,6}' scene.svg | tr 'A-F' 'a-f' | sort | uniq -c | sort -rn
# 2. map the top N onto tokens (unDraw's signature accent is #6c63ff)
sed -i -e 's/#6c63ff/var(--ill-accent)/g' \
       -e 's/#3f3d56/var(--ill-ink)/g' \
       -e 's/#f2f2f2/var(--ill-surface)/g' \
       -e 's/#ffffff/var(--ill-bg)/g' scene.svg
# 3. add fallbacks so the file still renders standalone
sed -i 's/var(--ill-accent)/var(--ill-accent,#6c63ff)/g' scene.svg
```
```css
:root { --ill-accent: var(--brand-600); --ill-ink: var(--neutral-800);
        --ill-surface: var(--neutral-100); --ill-bg: var(--surface); }
@media (prefers-color-scheme: dark) {
  :root { --ill-ink: var(--neutral-100); --ill-surface: var(--neutral-800); }
}
```
Note this only works when the SVG is **inlined** into the DOM. CSS custom properties do not cross
into an `<img src="scene.svg">`.

5. **Commission or draw a small set.** Six spot illustrations from one illustrator is often
   cheaper than the design debt of a template look. Out of scope for an agent, but the honest
   recommendation to surface to the user when illustration is load-bearing for the brand.

---

## 4. Shapes, blobs, patterns, textures and backgrounds generated by CODE

This is the section that matters most. Everything here is deterministic, seedable, tiny, themeable
via `currentColor` or CSS custom properties, and impossible to trace to a stock library. That last
property is why it beats fetching an asset for most decorative needs.

### 4.1 SVG blob generation (organic closed bezier shapes) - VERIFIED, renders

The math: place `n` points evenly around a circle, jitter each point's radius, then join them with
a **closed Catmull-Rom spline converted to cubic beziers**. Catmull-Rom is the right primitive
because it passes *through* every control point and closes cleanly, so the shape is exactly as
irregular as your jitter and no more.

The conversion is one line of algebra. For four consecutive points P0, P1, P2, P3, the cubic
bezier segment from P1 to P2 has control points:

```
C1 = P1 + (P2 - P0) / 6
C2 = P2 - (P3 - P1) / 6
```

That `/6` is the uniform (alpha = 0) Catmull-Rom tension. Smaller divisor = tighter, more angular;
larger = looser. Wrapping the indices modulo `n` gives a seamless closed loop.

```python
#!/usr/bin/env python3
"""blob.py - deterministic organic blob -> SVG path. Verified: renders via rsvg-convert."""
import math, random, sys

def blob_path(n=7, radius=100, jitter=0.25, cx=128, cy=128, seed=1):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = radius * (1 + rnd.uniform(-jitter, jitter))
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d = [f"M{pts[0][0]:.2f},{pts[0][1]:.2f}"]
    for i in range(n):
        p0, p1 = pts[(i - 1) % n], pts[i]
        p2, p3 = pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}")
    return "".join(d) + "Z"

if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    print('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">'
          f'<path d="{blob_path(seed=seed)}" fill="currentColor"/></svg>')
```

Verified run:
```
$ python3 blob.py 7 > blob.svg && rsvg-convert -w 256 blob.svg -o blob.png
$ magick identify blob.png
blob.png PNG 256x256 256x256+0+0 8-bit sRGB 3616B
# opaque coverage 38%, bbox (34,36)-(220,234) - a real closed shape, not a degenerate path
```

Tuning that actually matters:
- `n = 5..8`. Below 5 it reads as a rounded polygon; above ~10 the jitter averages out and it
  reads as a wobbly circle.
- `jitter = 0.12..0.30`. Above 0.35 the spline starts self-intersecting and the fill goes wrong.
- **Always emit `fill="currentColor"`** so the blob themes from CSS.
- Seed from something stable (a slug hash) so the same page always gets the same blob.

Two things you get almost free once you have `blob_path`:

```python
# Concentric blobs from one seed, for a layered/depth background.
layers = [(blob_path(n=6, radius=r, jitter=0.22, seed=7), op)
          for r, op in ((118, .10), (96, .16), (74, .26))]

# Animate between two blobs with the SAME n: the path strings have identical
# command structure, so SMIL/CSS can morph them directly.
a = blob_path(n=6, seed=1); b = blob_path(n=6, seed=2)
```
```html
<svg viewBox="0 0 256 256" style="color:var(--brand-500)">
  <path fill="currentColor" opacity=".25">
    <animate attributeName="d" dur="14s" repeatCount="indefinite"
             values="A_PATH;B_PATH;A_PATH" calcMode="spline"
             keySplines=".4 0 .2 1;.4 0 .2 1" keyTimes="0;0.5;1"/>
  </path>
</svg>
```
Morphing only works when both paths have the same number and type of segments. Same `n` guarantees
it. Respect `prefers-reduced-motion` by wrapping the animate in a media query or dropping it.

**When to code a blob vs fetch one:** always code it. Haikei and Blobmaker produce the same math
through a UI. Coding it takes 20 lines, is seedable, is parameterisable at build time, and does
not put the same five Haikei blobs on your site that are on everyone else's.

### 4.2 Wave / divider generation - VERIFIED, renders

```python
#!/usr/bin/env python3
"""wave.py - sine section divider -> closed SVG path. Verified: renders via rsvg-convert."""
import math

def wave(width=1440, height=120, amp=28, periods=1.5, phase=0.0, steps=64, flip=False):
    mid = height / 2
    pts = []
    for i in range(steps + 1):
        x = width * i / steps
        y = mid + amp * math.sin(2 * math.pi * periods * i / steps + phase)
        pts.append((x, height - y if flip else y))
    d = [f"M0,{pts[0][1]:.2f}"] + [f"L{x:.2f},{y:.2f}" for x, y in pts[1:]]
    d.append(f"L{width},{height}L0,{height}Z")
    return "".join(d)

print(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 120" '
      f'preserveAspectRatio="none"><path d="{wave()}" fill="currentColor"/></svg>')
```
Verified: `rsvg-convert -w 720 wave.svg -o wave.png` -> `720x60 PNG`.

`preserveAspectRatio="none"` is the load-bearing attribute: it lets the divider stretch to any
container width without changing its height. Stack two or three waves at different `phase`,
`amp` and `opacity` for the layered look, and use `flip=True` for the mirrored bottom edge.

```html
<div class="section">
  <svg class="divider" viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true">
    <path d="..." fill="currentColor" opacity=".35"/>   <!-- phase 0.0, amp 22 -->
    <path d="..." fill="currentColor" opacity=".6"/>    <!-- phase 1.1, amp 30 -->
    <path d="..." fill="currentColor"/>                  <!-- phase 2.4, amp 26 -->
  </svg>
</div>
```
```css
.divider { display:block; width:100%; height:clamp(48px,7vw,120px); color: var(--next-section-bg); }
```
Colouring the divider with the *next* section's background is what makes it read as a shape cut
out of the boundary rather than a decal sitting on it.

For a straight angled divider or a notch, skip SVG entirely - `clip-path` is one line (4.6).

### 4.3 Grain and noise: `feTurbulence` - VERIFIED, renders

Verified locally: the filter chain below rendered through rsvg-convert and produced real pixel
variance (stddev 0.0305 at slope 0.5, min 0.114 / max 0.471) against a flat control of exactly 0.

Grain is the highest-value-per-byte technique on this list. It is what Linear, Vercel, Apple and
most design-forward sites use to stop large flat fills and gradients from looking like a CSS
default. It costs about 300 bytes.

```html
<!-- Standalone, tileable grain layer. seed makes it reproducible. -->
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <defs>
    <filter id="grain" x="0" y="0" width="100%" height="100%"
            color-interpolation-filters="sRGB">
      <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3"
                    stitchTiles="stitch" seed="7" result="noise"/>
      <feColorMatrix in="noise" type="saturate" values="0" result="mono"/>
      <feComponentTransfer in="mono">
        <feFuncA type="linear" slope="0.18" intercept="0"/>
      </feComponentTransfer>
    </filter>
  </defs>
  <rect width="400" height="300" fill="#1b3a2f"/>
  <rect width="400" height="300" filter="url(#grain)" style="mix-blend-mode:overlay"/>
</svg>
```

Every attribute here earns its place (all confirmed on MDN's `feTurbulence` page):
- `type="fractalNoise"` gives smooth film grain. `type="turbulence"` (the default) gives a harsher,
  more marbled/veined result. For grain you want `fractalNoise`; for smoke or marble, `turbulence`.
- `baseFrequency` sets grain size. `0.6-0.9` is film grain. `0.15-0.3` is cloud/mist.
  `0.02-0.06` feeds `feDisplacementMap` for organic edge distortion.
- `numOctaves` adds detail by summing octaves. **2-4 is the whole useful range.** Going to 8
  multiplies cost with no visible gain and will drop frames on mobile.
- `seed` makes it reproducible across builds.
- `stitchTiles="stitch"` makes the noise tile seamlessly, required if you repeat it.
- `color-interpolation-filters="sRGB"` - **the attribute everyone forgets.** SVG filters default to
  linearRGB, which makes the grain look washed out and wrong. Always set sRGB.
- `feColorMatrix type="saturate" values="0"` desaturates the noise so it does not tint the layer.
- `feComponentTransfer`/`feFuncA slope` controls intensity. **0.06-0.20 for a real design.**
  Above 0.3 it stops being texture and becomes a visible effect.

**The production form: a CSS pseudo-element overlay** so one rule grains any surface.

```css
.grain { position: relative; isolation: isolate; }
.grain::after {
  content: "";
  position: absolute; inset: 0;
  pointer-events: none;
  z-index: 1;
  opacity: .14;                 /* the real intensity dial: .05 subtle, .2 strong */
  mix-blend-mode: overlay;      /* soft-light is gentler, overlay is punchier */
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 180px 180px; /* tile: keeps the filter area small and cheap */
}
@media (prefers-reduced-transparency: reduce) { .grain::after { display: none; } }
```

Percent-encoding rules for an inline SVG data URI (these are the ones that bite):
`#` -> `%23`, `%` -> `%25`, `<` -> `%3C`, `>` -> `%3E`, `"` -> use single quotes inside instead.
Do **not** base64-encode it - percent-encoded SVG is smaller and gzips better.

**Performance.** Live `feTurbulence` is GPU-expensive, especially on mobile, and especially over a
large area. Three mitigations, in order:
1. Tile it (`background-size: 180px 180px`), so the filter only ever renders 180x180 px.
2. Pre-render to PNG at build time and ship that. This is the safest option for a full-page grain:

```bash
# Bake the grain to a tileable PNG once, at build time. Verified locally.
cat > /tmp/grain-tile.svg <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <filter id="n" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3"
                  stitchTiles="stitch" seed="3"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
  <rect width="256" height="256" filter="url(#n)"/>
</svg>
EOF
rsvg-convert -w 256 -h 256 /tmp/grain-tile.svg -o grain.png
magick grain.png -alpha off -colorspace Gray -depth 8 PNG8:grain8.png   # ~15-25 KB
magick grain8.png -quality 60 grain.webp                                 # smaller still
```
```css
.grain::after { background-image: url(/img/grain.webp); background-size: 256px 256px; }
```
3. Restrict it to the hero and above-the-fold surfaces rather than `body`.

**CSS-only alternatives to feTurbulence** (no SVG at all). These are cheaper but coarser:

```css
/* (a) Repeating conic dither - the cheapest "not flat" texture that exists. */
.dither {
  background-image:
    conic-gradient(from 0deg at 50% 50%,
      rgb(255 255 255 / .035) 0deg 90deg, transparent 90deg 180deg,
      rgb(0 0 0 / .035) 180deg 270deg, transparent 270deg 360deg);
  background-size: 3px 3px;
}

/* (b) Crossed repeating-linear-gradients: a woven micro-texture. */
.weave {
  background-image:
    repeating-linear-gradient(45deg,  rgb(0 0 0 / .03) 0 1px, transparent 1px 3px),
    repeating-linear-gradient(-45deg, rgb(255 255 255 / .03) 0 1px, transparent 1px 3px);
}

/* (c) Multi-layer offset radial dots as a stochastic-looking speckle. */
.speckle {
  background-image:
    radial-gradient(circle at 20% 30%, rgb(0 0 0 / .05) .5px, transparent .5px),
    radial-gradient(circle at 70% 80%, rgb(0 0 0 / .05) .5px, transparent .5px),
    radial-gradient(circle at 45% 60%, rgb(255 255 255 / .05) .5px, transparent .5px);
  background-size: 7px 7px, 11px 11px, 13px 13px;  /* coprime sizes = long visual period */
}
```
The coprime `background-size` trick in (c) is the key detail: 7, 11 and 13 only re-align every
1001px, so a viewer never perceives the tile.

**When to fetch instead:** never. A grain PNG from a stock site is the same bytes with a licence
attached and a worse tile.

### 4.4 Mesh gradients

**Status check, 2026:** there is still **no native CSS mesh gradient**. What exists:
- `conic-gradient()` is Baseline and widely supported (Chrome 69+, Firefox 83+, Safari 12.1+,
  ~95% of users). Verified on MDN.
- Gradient **colour interpolation spaces** are real and worth using:
  `linear-gradient(90deg in oklch, blue, red)`, plus `in oklab`, `in lab`, `in hsl longer hue`,
  and hue methods `shorter | longer | increasing | decreasing`. Default space is sRGB. Verified on
  MDN's linear-gradient page. Exact Baseline date for the interpolation syntax: `UNVERIFIED`.
- SVG `<meshgradient>` from SVG 2 is **not implemented in any shipping browser**. Do not use it.

So a "mesh gradient" in 2026 means one of two real techniques.

**(a) Stacked radial gradients - the CSS way. Best default.**

```css
.mesh {
  background-color: var(--mesh-base, oklch(22% .04 250));
  background-image:
    radial-gradient(at 12% 18%,  oklch(72% .17 28  / .55) 0px, transparent 55%),
    radial-gradient(at 86% 12%,  oklch(68% .15 200 / .50) 0px, transparent 50%),
    radial-gradient(at 72% 82%,  oklch(60% .19 305 / .45) 0px, transparent 55%),
    radial-gradient(at 22% 88%,  oklch(78% .14 95  / .40) 0px, transparent 45%);
}
```
Why this shape of rule works:
- **`at X% Y%` with `transparent NN%`, not colour stops at 100%.** Letting each blob fade out well
  before the edge is what produces smooth overlap instead of visible rings.
- **oklch, not hex.** Blending two saturated sRGB hexes through their midpoint goes grey and muddy.
  oklch keeps chroma through the blend. This one change is most of the difference between a mesh
  that looks designed and one that looks like a 2012 gradient.
- **4-6 blobs.** Fewer reads as a plain radial; more turns to mud.
- **Always grain it.** `.mesh.grain` from 4.3. A clean CSS mesh is instantly recognisable as a
  CSS mesh; a grained one is not.

Animate it by moving the positions, not by animating `background-image` (which is not
interpolable). Use `@property` so custom properties are actually animatable:

```css
@property --mx1 { syntax: "<percentage>"; inherits: false; initial-value: 12%; }
@property --my1 { syntax: "<percentage>"; inherits: false; initial-value: 18%; }
.mesh--live {
  background-image: radial-gradient(at var(--mx1) var(--my1), oklch(72% .17 28/.55) 0, transparent 55%), /* ... */;
  animation: drift 24s ease-in-out infinite alternate;
}
@keyframes drift { to { --mx1: 34%; --my1: 40%; } }
@media (prefers-reduced-motion: reduce) { .mesh--live { animation: none; } }
```

**(b) SVG with blurred shapes - the way to get a real mesh look, exportable as a static asset.**

```html
<svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <defs>
    <filter id="soften" x="-30%" y="-30%" width="160%" height="160%"
            color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="90"/>
    </filter>
    <filter id="grain" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
      <feComponentTransfer><feFuncA type="linear" slope="0.16"/></feComponentTransfer>
    </filter>
  </defs>
  <rect width="800" height="600" fill="#101a2b"/>
  <g filter="url(#soften)">
    <ellipse cx="140" cy="120" rx="260" ry="200" fill="#f0603a"/>
    <ellipse cx="690" cy="90"  rx="230" ry="190" fill="#2fb6c8"/>
    <ellipse cx="560" cy="500" rx="280" ry="220" fill="#8a4bd8"/>
    <ellipse cx="150" cy="530" rx="240" ry="180" fill="#e8c05a"/>
  </g>
  <rect width="800" height="600" filter="url(#grain)" style="mix-blend-mode:overlay"/>
</svg>
```
```bash
# Bake it so the browser never runs the blur, and ship AVIF.
rsvg-convert -w 1600 mesh.svg -o mesh.png
avifenc -q 55 -s 4 --sharpyuv mesh.png mesh.avif   # a mesh gradient AVIF is typically 10-40 KB
```
A blurred-ellipse mesh has no high-frequency detail, so AVIF crushes it. Baking is almost always
right for a hero background: it removes a 90px Gaussian blur from the render path.

**When to fetch instead:** Haikei's "blurry gradient" generator does exactly (b) through a UI, for
free, exporting SVG and PNG. Fine for a one-off in a design conversation, but the same handful of
Haikei outputs are all over the web. Generate your own from the project palette.

### 4.5 Dot, grid and line patterns via `background-image`

These are pure CSS, weigh nothing, theme through custom properties, and are the correct answer for
essentially every "we need some texture in the background" request.

```css
:root {
  --pat-color: color-mix(in oklab, currentColor 12%, transparent);
  --pat-size: 24px;
  --pat-dot: 1.5px;
  --pat-line: 1px;
}

/* Dot grid (the Notion / Figma canvas look) */
.pat-dots {
  background-image: radial-gradient(var(--pat-color) var(--pat-dot), transparent var(--pat-dot));
  background-size: var(--pat-size) var(--pat-size);
}

/* Offset / staggered dots - two layers half a cell apart */
.pat-dots-offset {
  background-image:
    radial-gradient(var(--pat-color) var(--pat-dot), transparent var(--pat-dot)),
    radial-gradient(var(--pat-color) var(--pat-dot), transparent var(--pat-dot));
  background-size: var(--pat-size) var(--pat-size);
  background-position: 0 0, calc(var(--pat-size)/2) calc(var(--pat-size)/2);
}

/* Graph-paper grid */
.pat-grid {
  background-image:
    linear-gradient(to right,  var(--pat-color) var(--pat-line), transparent var(--pat-line)),
    linear-gradient(to bottom, var(--pat-color) var(--pat-line), transparent var(--pat-line));
  background-size: var(--pat-size) var(--pat-size);
}

/* Two-level grid: fine cells plus a heavier major line every 5 cells */
.pat-grid-major {
  background-image:
    linear-gradient(to right,  var(--pat-color) 1px, transparent 1px),
    linear-gradient(to bottom, var(--pat-color) 1px, transparent 1px),
    linear-gradient(to right,  color-mix(in oklab, currentColor 22%, transparent) 1px, transparent 1px),
    linear-gradient(to bottom, color-mix(in oklab, currentColor 22%, transparent) 1px, transparent 1px);
  background-size: 24px 24px, 24px 24px, 120px 120px, 120px 120px;
}

/* Diagonal hatch */
.pat-hatch {
  background-image: repeating-linear-gradient(45deg,
    var(--pat-color) 0 var(--pat-line),
    transparent var(--pat-line) 10px);
}

/* Crosshatch */
.pat-crosshatch {
  background-image:
    repeating-linear-gradient( 45deg, var(--pat-color) 0 1px, transparent 1px 9px),
    repeating-linear-gradient(-45deg, var(--pat-color) 0 1px, transparent 1px 9px);
}

/* Checkerboard, 2 gradients */
.pat-checker {
  background-image:
    linear-gradient(45deg,  var(--pat-color) 25%, transparent 25% 75%, var(--pat-color) 75%),
    linear-gradient(45deg,  var(--pat-color) 25%, transparent 25% 75%, var(--pat-color) 75%);
  background-size: 20px 20px;
  background-position: 0 0, 10px 10px;
}

/* Vertical stripes / "ruled paper" */
.pat-stripes {
  background-image: repeating-linear-gradient(90deg,
    var(--pat-color) 0 1px, transparent 1px 8px);
}
```

**The three details that separate a designed pattern from a default one:**

1. **Fade it out.** A pattern that runs edge to edge at uniform strength looks like a placeholder.
   Mask it so it dissolves.

```css
.pat-dots {
  mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 30%, transparent 75%);
}
/* or a simple top-to-bottom fade */
.pat-grid { mask-image: linear-gradient(to bottom, #000, transparent 70%); }
```
`mask` and `mask-image` are Baseline widely available since **December 2023** (verified on MDN),
and the `-webkit-` prefix is no longer required in modern browsers.

2. **Drive it from `currentColor` via `color-mix`**, as above, so the pattern automatically
   inverts in dark mode with no second rule.

3. **Scale it with the layout**, not in fixed px: `--pat-size: clamp(16px, 2vw, 32px)`.

**When to fetch instead:** Hero Patterns (CC BY 4.0, over 100 SVG patterns by Steve Schoger) is
worth reaching for when you need an *illustrative* repeating motif - jigsaw, bamboo, topography,
circuit board - that would be tedious to write by hand. Copy the SVG, do not hotlink. MagicPattern
is a paid subscription ($10-20/month), skip it. pattern.css is a small dependency-free CSS library
covering the same ground as the rules above; not worth a dependency for what fits in 30 lines.
Haikei is free and good for one-off layered-wave and low-poly backgrounds.

### 4.6 `clip-path`, the `shape()` function, and masks

**`clip-path` with `polygon()`** is the workhorse and has been safe for years:

```css
.diagonal-top    { clip-path: polygon(0 4vw, 100% 0, 100% 100%, 0 100%); }
.diagonal-both   { clip-path: polygon(0 4vw, 100% 0, 100% calc(100% - 4vw), 0 100%); }
.notch           { clip-path: polygon(0 0, 42% 0, 46% 12px, 100% 12px, 100% 100%, 0 100%); }
.arrow-right     { clip-path: polygon(0 0, calc(100% - 24px) 0, 100% 50%, calc(100% - 24px) 100%, 0 100%); }
.hex             { clip-path: polygon(25% 0, 75% 0, 100% 50%, 75% 100%, 25% 100%, 0 50%); }
.squircle-ish    { clip-path: inset(0 round 28%); }
```

**`shape()` - VERIFIED, Baseline newly available since February 2026.** From MDN: "Since February
2026, this feature works across the latest devices and browser versions." Chrome, Firefox, Safari
and Edge all ship it. This is the big change since `path()`: `shape()` uses real CSS syntax, so it
accepts `%`, `rem`, `calc()` and custom properties, which `path()` never could.

Commands, verified from MDN: `move`, `line`, `hline`, `vline`, `curve ... with ...`, `smooth`,
`arc ... of ... [cw|ccw] [large|small] [rotate <angle>]`, `close`. Each takes `by` (relative) or
`to` (absolute).

```css
/* A responsive curved bottom edge, impossible with path() because path() cannot use %. */
.hero {
  clip-path: shape(
    from 0% 0%,
    hline to 100%,
    vline to 82%,
    curve to 0% 82% with 66% 100% / 33% 64%,
    close
  );
}

/* A blob-ish card corner that scales with the element */
.card-organic {
  clip-path: shape(
    from 0% 12%,
    arc to 12% 0% of 12% cw,
    hline to 100%,
    vline to 88%,
    arc to 88% 100% of 12% cw,
    hline to 0%,
    close
  );
}
```

Progressive enhancement, because "newly available" is not "safe for every visitor" yet:
```css
.hero { clip-path: polygon(0 0, 100% 0, 100% 88%, 0 100%); }   /* fallback */
@supports (clip-path: shape(from 0% 0%, close)) {
  .hero { clip-path: shape(from 0% 0%, hline to 100%, vline to 82%,
                           curve to 0% 82% with 66% 100% / 33% 64%, close); }
}
```

**Masks** do what `clip-path` cannot: soft, gradient, and image-driven edges.

```css
/* Feathered image edge - no PNG alpha needed */
.feather { mask-image: linear-gradient(to bottom, #000 60%, transparent 100%); }

/* Text-shaped window onto a mesh gradient (the classic "gradient text" done right) */
.gradient-text {
  background: linear-gradient(92deg in oklch, oklch(70% .19 25), oklch(72% .16 260));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

/* An arbitrary SVG shape as a mask, so any element can be blob-shaped */
.blob-photo {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256'%3E%3Cpath d='M219,128C219,149 198,175 179,192...Z' fill='%23000'/%3E%3C/svg%3E");
  mask-size: 100% 100%;
  mask-repeat: no-repeat;
}

/* Scroll-fade on an overflow container - two masks composited */
.scroller {
  mask-image: linear-gradient(to right, transparent, #000 24px,
                              #000 calc(100% - 24px), transparent);
}
```

`clip-path` vs `mask`, decided in one line: **hard edge -> `clip-path` (cheaper, crisper,
animatable between same-shape polygons); soft or gradient edge -> `mask`.**

### 4.7 The generative-pattern libraries, ranked for an agent

| Tool | Licence / cost | Use it when |
|---|---|---|
| **Hero Patterns** | CC BY 4.0, free | You need an illustrative repeating motif (topography, jigsaw, circuits) that is tedious to hand-write. Copy the SVG into your repo. |
| **Haikei** | free, no signup; asset licence not stated on the site (`UNVERIFIED`) | One-off layered waves, blob scenes, low-poly grids, blurry gradients. ~15 generators, exports SVG and PNG. Good for exploration; regenerate rather than reuse the defaults. |
| **SVG Backgrounds** | freemium | Browsing for ideas. Most of what it sells is reproducible in 10 lines of CSS. |
| **pattern.css** | MIT | Almost never - a CSS dependency for what Section 4.5 does inline. |
| **MagicPattern** | **paid, $10-20/month** | Do not put a subscription in an agent's default path. |
| **your own code** | - | Everything else, which is most things. |

---

## 5. Vectorizing and cleaning

### 5.1 vtracer - VERIFIED, ran here (v0.6.5)

Full verified flag list from `vtracer --help`:
`--colormode {color|bw}`, `-p/--color_precision`, `-c/--corner_threshold`,
`-f/--filter_speckle`, `-g/--gradient_step`, `--hierarchical {stacked|cutout}`,
`-i/--input`, `-m/--mode {pixel|polygon|spline}`, `-o/--output`, `--path_precision`,
`--preset {bw|poster|photo}`, `-l/--segment_length`, `-s/--splice_threshold`.

Accepts PNG/JPG directly. No PBM conversion step, unlike potrace.

**(a) Generated raster logo -> clean SVG** (verified: 512x512 PNG -> 5562-byte SVG, renders):
```bash
vtracer --input logo.png --output logo.svg \
  --colormode bw \
  --mode spline \
  --filter_speckle 4 \
  --corner_threshold 60 \
  --path_precision 2
```
- `--colormode bw` for a single-colour mark. Use `color` only if the logo is genuinely multicolour.
- `--mode spline` gives curves. `polygon` gives straight segments (right for a geometric mark),
  `pixel` traces every pixel edge (almost never what you want).
- `--filter_speckle 4` drops sub-4px islands: this is what removes JPEG/anti-alias dirt.
- `--corner_threshold 60` - lower keeps more sharp corners, higher rounds them. 60 is a good
  starting point for a logo; drop to 30-40 for something angular.
- `--path_precision 2` caps decimals in the path data and cuts file size substantially.

**Gotcha, verified:** vtracer emits `width="512" height="512"` and **no `viewBox`**. That SVG will
not scale. Fix it before anything else touches the file (see 5.3).

**(b) Photo -> stylized vector**:
```bash
# Posterised, poster-art look
vtracer --input photo.jpg --output poster.svg \
  --preset poster --mode spline --filter_speckle 8 --color_precision 6 --path_precision 1

# Higher fidelity, much larger file
vtracer --input photo.jpg --output photo.svg \
  --colormode color --mode spline --hierarchical stacked \
  --color_precision 8 --gradient_step 10 --filter_speckle 4 --path_precision 2
```
Reduce the source before tracing or the SVG will be megabytes:
```bash
magick photo.jpg -resize 900x -colors 12 -dither None -quality 92 flat.png
vtracer --input flat.png --output photo.svg --colormode color --mode spline \
        --filter_speckle 8 --color_precision 6 --path_precision 1
ls -l photo.svg   # sanity-check: over ~200 KB means back off color_precision
```
`--color_precision` is the main size lever: it is the number of significant bits per RGB channel,
so 4-6 gives a bold posterised look, 8 approaches the original and explodes the file.
`--hierarchical cutout` produces non-overlapping regions (better for editing in Illustrator),
`stacked` (default) layers them (smaller, renders correctly as-is).

### 5.2 potrace - VERIFIED, ran here (v1.16)

potrace is **bitonal only**, and it **only reads PNM (pbm/pgm/ppm) and BMP**. You must convert
first. It is better than vtracer at one specific job: clean, minimal curves from crisp black and
white input, which is exactly what a logo or a lettermark is. Verified output was 2126 bytes vs
vtracer's 5562 for the same source.

```bash
# (a) generated raster logo -> clean SVG. Verified end to end.
magick logo.png -colorspace gray -threshold 55% logo.pbm      # tune 45-65%
potrace -s -o logo.svg --turdsize 5 --alphamax 1 --opttolerance 0.2 logo.pbm
# -s / --svg          : SVG backend (default is EPS - the most common mistake)
# -t / --turdsize N   : drop speckles up to N px (default 2)
# -a / --alphamax N   : corner threshold. 0 = all corners, 1.0 default,
#                       1.334 = maximum smoothing (all corners become curves)
# -O / --opttolerance : curve-fitting tolerance, default 0.2. Higher = fewer segments
# -n / --longcurve    : disable curve optimisation entirely (bigger, more faithful)
# -u / --unit N       : output quantisation, default 10. Raise for finer coordinates
# -i / --invert       : trace white-on-black instead
# --flat              : emit the whole image as one <path> (handy for a single-colour mark)
# -k / --blacklevel   : threshold if you feed a greyscale pgm instead of pre-thresholding

# (b) photo -> stylized vector: potrace is single-level, so posterise into layers yourself.
magick photo.jpg -resize 1200x -colorspace gray -normalize -blur 0x1 g.png
for lvl in 25 45 65 85; do
  magick g.png -threshold ${lvl}% -negate lay-$lvl.pbm
  potrace -s --flat -t 8 -a 1.2 -o lay-$lvl.svg lay-$lvl.pbm
done
# then stack lay-85 (darkest) to lay-25 (lightest) as <g> layers with decreasing opacity
# into one SVG. Gives a screen-print / risograph look, which is usually what "stylized
# vector from a photo" actually means. For full colour, use vtracer instead.
```

**vtracer vs potrace, decided:**
- Colour input, or you want one command with no conversion -> **vtracer**.
- Crisp bitonal logo, lettermark, stamp, silhouette, and you want the smallest cleanest path ->
  **potrace**. It produced a 2.6x smaller file here on identical input.
- A photo you want in full colour -> **vtracer** with `--preset poster`.
- A photo you want as a screen-print -> **potrace** with manual level layers.

**Neither is the right tool for a logo you can redraw.** If the mark is geometric (circles,
rounded rects, straight strokes), hand-writing 6 SVG primitives beats any trace: it will be
100 bytes instead of 5 KB, it will have perfect geometry, and it will be editable.

### 5.3 SVG cleanup

**Run SVGO without a global install - VERIFIED here via npx:**
```bash
npx -y svgo@latest --multipass -p 2 -i in.svg -o out.svg
# verified reduction on the vtracer output: 5.432 KiB -> 2.513 KiB (-53.7%)
# verified on the potrace output:           2.076 KiB -> 1.678 KiB (-19.2%)
```
Full verified CLI (from `npx svgo --help`):
`-i/--input <...>` ("-" = stdin), `-s/--string`, `-f/--folder`, `-r/--recursive`,
`--exclude <pattern...>`, `-o/--output <...>` ("-" = stdout), `-p/--precision <int>`,
`--config <file>` (.js/.mjs/.cjs only), `--datauri <base64|enc|unenc>`, `--multipass`,
`--pretty`, `--indent <int>`, `--eol <lf|crlf>`, `--final-newline`, `-q/--quiet`,
`--show-plugins`, `--no-color`.

```bash
npx -y svgo@latest -f ./src/icons -r --multipass -p 2 -q     # whole folder, in place
cat in.svg | npx -y svgo@latest -i - -o - --datauri enc      # straight to a CSS data URI
```

**The metadata that generators emit and what removes it.** `preset-default` already runs
`removeMetadata`, `removeComments`, `removeDoctype`, `removeXMLProcInst`, `removeDesc`,
`removeEditorsNSData` (Inkscape/Illustrator namespaces), `removeUnusedNS`, `cleanupIds`,
`removeEmptyAttrs`, `removeUselessDefs`, `convertPathData`, `sortAttrs` - all confirmed in
`--show-plugins`. So the default pass handles Inkscape's `sodipodi:`/`inkscape:` cruft, the
`<!-- Generator: visioncortex VTracer 0.6.5 -->` comment, and potrace's DOCTYPE without config.

What `preset-default` does **not** do, and you usually want:

```js
// svgo.config.js  - the config for UI icons
module.exports = {
  multipass: true,
  js2svg: { indent: 0, pretty: false },
  plugins: [
    { name: 'preset-default',
      params: { overrides: {
        removeViewBox: false,      // NEVER remove viewBox. It is not in preset-default's
                                   // default-on set in current SVGO, but pin it explicitly.
        cleanupIds: { minify: true },
      }}},
    'removeDimensions',            // strip width/height, keep viewBox -> CSS controls the size
    'removeXMLNS',                 // ONLY for SVGs inlined into HTML. Breaks standalone files.
    'removeScripts',
    'removeStyleElement',          // if you are moving styles to presentation attributes
    { name: 'convertColors',
      params: { currentColor: true } },   // rewrites explicit fills to currentColor
    { name: 'addAttributesToSVGElement',
      params: { attributes: [{ 'aria-hidden': 'true' }, { focusable: 'false' }] } },
  ],
};
```
```bash
npx -y svgo@latest --config svgo.config.js -f ./src/icons -r
```
`convertColors` with `currentColor: true` is the single most useful non-default plugin for icons.
`removeXMLNS` is the classic footgun: it makes the file smaller but the standalone `.svg` will not
render in a browser tab or an `<img>`. Only apply it to a build output that is inlined.

**viewBox normalization.** Any trace or export that lacks a `viewBox` cannot scale. Fix it:

```bash
# Add a viewBox derived from width/height when it is missing (the exact vtracer case).
python3 - "$@" <<'PY'
import re, sys, pathlib
for p in map(pathlib.Path, sys.argv[1:]):
    s = p.read_text()
    if 'viewBox' in s:
        continue
    w = re.search(r'\bwidth="([\d.]+)', s)
    h = re.search(r'\bheight="([\d.]+)', s)
    if not (w and h):
        print('SKIP (no width/height):', p); continue
    s = s.replace('<svg', f'<svg viewBox="0 0 {w.group(1)} {h.group(1)}"', 1)
    p.write_text(s)
    print('added viewBox to', p)
PY
```
```bash
# Or let Inkscape compute a tight viewBox around the actual drawing:
inkscape --export-area-drawing --export-plain-svg --export-filename=tight.svg messy.svg
# And to normalise everything to a common 24x24 grid:
inkscape --export-area-drawing --export-width=24 --export-height=24 \
         --export-plain-svg --export-filename=icon-24.svg icon.svg
```
Verified gotcha: potrace's SVG has `width="682.67" height="682.67" viewBox="0 0 512 512"` after
SVGO - correct viewBox, but odd px dimensions because potrace works in points (512pt at 96dpi =
682.67px). Strip the dimensions with `removeDimensions` and size it from CSS.

**Converting stroke to path.** Needed when an icon must be scaled non-uniformly, filled with a
gradient, boolean-combined, or shipped to a tool that ignores `stroke-width`.

```bash
# Inkscape 1.x: Path > Stroke to Path, from the CLI
inkscape --actions="select-all;object-stroke-to-path;export-plain-svg;export-filename:out.svg;export-do" in.svg
# verify the strokes are gone:
grep -c 'stroke=' out.svg    # expect 0 (or only stroke="none")
```
**Do this only when you must.** Converting stroke to path permanently destroys the
`stroke-width` control described in 2.4, so you can no longer thin the stroke as the icon grows.
For UI icons, keep them as strokes.

**Making an SVG themeable - the two-layer approach.**

Layer 1, `currentColor` for the single-colour case:
```bash
# Every explicit fill becomes currentColor. Handles the common single-colour icon.
npx -y svgo@latest --multipass \
  --config <(echo "module.exports={plugins:[{name:'preset-default'},{name:'convertColors',params:{currentColor:true}}]}") \
  -f ./icons -r
# Verify it worked:
grep -L 'currentColor' icons/*.svg    # should print nothing
```

Layer 2, custom properties with fallbacks for the multi-colour case:
```bash
# Map each distinct hex to a token, keeping the original as the fallback so the file
# still renders correctly when opened standalone or used in an <img>.
python3 - illustration.svg <<'PY'
import re, sys, pathlib, collections
p = pathlib.Path(sys.argv[1]); s = p.read_text()
hexes = collections.Counter(m.lower() for m in re.findall(r'#[0-9a-fA-F]{6}', s))
for i, (hx, _) in enumerate(hexes.most_common(6), 1):
    s = re.sub(hx, f'var(--art-{i},{hx})', s, flags=re.I)
p.write_text(s)
print({f'--art-{i}': hx for i, (hx, _) in enumerate(hexes.most_common(6), 1)})
PY
```
```css
/* now themeable, and dark mode is 4 lines */
.art { --art-1: var(--brand-600); --art-2: var(--neutral-800); --art-3: var(--neutral-100); }
@media (prefers-color-scheme: dark) { .art { --art-2: var(--neutral-100); --art-3: var(--neutral-800); } }
```

**Non-negotiable:** CSS custom properties and `currentColor` **only work on inlined SVG**. An
`<img src="art.svg">` is a separate document with its own cascade; page CSS never reaches it. If
the SVG must be an `<img>`, bake the colours in or use a `mask-image` with a solid background.

---

## 6. Asset optimization pipeline

Every command below was run in this environment.

### 6.1 Size for the rendered dimensions, not the source

The single biggest win, and the one most often skipped. A 2400px source in an 800px slot wastes
about 90% of the bytes. Cap at 2x the largest rendered CSS width; beyond 2x DPR the returns are
invisible.

```bash
# Verified: 2400x1600 source, 62 KB at 1200px wide q82 progressive JPEG
magick src.jpg -resize 1200x -strip -quality 82 \
  -sampling-factor 4:2:0 -interlace JPEG -colorspace sRGB out-1200.jpg
```
- `-strip` removes EXIF/GPS/thumbnails. Privacy and bytes.
- `-sampling-factor 4:2:0` is standard chroma subsampling for photos. Use `4:4:4` for images with
  saturated text or fine red detail.
- `-interlace JPEG` makes it progressive: it renders low-res first instead of top-to-bottom.
- `-colorspace sRGB` guards against a wide-gamut source rendering wrong in older browsers.

### 6.2 AVIF and WebP with fallback

**ImageMagick already has a `webp` delegate in this environment (verified in `magick -version`),
so `cwebp` is not required.**

```bash
# WebP via ImageMagick - verified: 1200x800 -> 8.9 KB
magick out-1200.jpg -quality 78 -define webp:method=6 out-1200.webp
# method=6 is the slowest/best. Add -define webp:lossless=true for logos/screenshots.

# AVIF via avifenc - verified: 1200x800 -> 10 KB
magick out-1200.jpg out-1200.png                       # avifenc takes jpg/png/y4m
avifenc -q 60 -s 4 --sharpyuv -y 420 out-1200.png out-1200.avif
# -q/--qcolor 0..100 (100 = lossless). 50-65 is the photo sweet spot.
# -s/--speed 0..10 (0 slowest/best, default 6). Use 3-4 for builds, 8-9 for previews.
# --sharpyuv improves 4:2:0 chroma noticeably on saturated edges. Costs nothing at runtime.
# -y 420 for photos; -y 444 for graphics with hard colour edges.
# -l/--lossless for a lossless AVIF.
# --target-size BYTES hits a byte budget (up to 7x slower).
```

Measured on a real gradient+noise test image at 1200x800: **JPEG q82 = 84 KB, WebP q78 = 8.8 KB,
AVIF q58 = 19 KB.** The ordering flips depending on content - synthetic gradients favour WebP,
photographic detail favours AVIF - which is exactly why you should measure per image rather than
assume, and why the `<picture>` fallback chain is not optional.

### 6.3 Build the full ladder plus `srcset` / `sizes`

```bash
#!/usr/bin/env bash
# build-responsive.sh <source> <basename> [widths...]
set -euo pipefail
src="$1"; base="$2"; shift 2
if [ "$#" -gt 0 ]; then widths=("$@"); else widths=(400 800 1200 1600 2000); fi
outdir="dist/img"; mkdir -p "$outdir"

read -r SW SH < <(magick identify -format "%w %h\n" "$src")
for w in "${widths[@]}"; do
  [ "$w" -gt "$SW" ] && continue
  magick "$src" -resize "${w}x" -strip -quality 82 \
    -sampling-factor 4:2:0 -interlace JPEG -colorspace sRGB "$outdir/$base-$w.jpg"
  magick "$outdir/$base-$w.jpg" -quality 78 -define webp:method=6 "$outdir/$base-$w.webp"
  magick "$outdir/$base-$w.jpg" "$outdir/tmp-$w.png"
  avifenc -q 58 -s 6 --sharpyuv -y 420 "$outdir/tmp-$w.png" "$outdir/$base-$w.avif" >/dev/null
  rm -f "$outdir/tmp-$w.png"
done

largest=$(ls "$outdir/$base-"*.jpg | sort -t- -k2 -n | tail -1)
read -r LW LH < <(magick identify -format "%w %h\n" "$largest")

emit() { local ext=$1 out="" f w
  for f in $(ls "$outdir/$base-"*."$ext" | sort -t- -k2 -n); do
    w=$(magick identify -format "%w" "$f"); out+="/img/$(basename "$f") ${w}w, "
  done; echo "${out%, }"; }

cat <<HTML
<picture>
  <source type="image/avif" srcset="$(emit avif)" sizes="SIZES_HERE">
  <source type="image/webp" srcset="$(emit webp)" sizes="SIZES_HERE">
  <img src="/img/$base-1200.jpg" srcset="$(emit jpg)" sizes="SIZES_HERE"
       width="$LW" height="$LH" alt="" loading="lazy" decoding="async">
</picture>
HTML

# VERIFIED end to end here. Two bugs this script had to fix, both worth knowing:
#  1. `magick identify -format "%w %h"` emits NO trailing newline, so `read` returns
#     non-zero and `set -e` kills the script silently. Always add \n to the format.
#  2. The default-widths idiom `widths=("${@:-400 800 ...}")` does not expand to an
#     array; use an explicit `if [ "$#" -gt 0 ]`.
# Verified run: ./build-responsive.sh test.jpg shot 400 800 1200 3200
#   -> built 400/800/1200 in all three formats, correctly SKIPPED 3200 (no upscale),
#      and emitted width="1200" height="800" from the largest variant.
```
Verified output ladder from the test image:
```
hero-400.avif  1163   hero-400.webp  1170   hero-400.jpg    4978
hero-800.avif  4166   hero-800.webp  3406   hero-800.jpg   24105
hero-1200.avif 19141  hero-1200.webp 8784   hero-1200.jpg  84316
hero-1600.avif 56163  hero-1600.webp 31316  hero-1600.jpg 213515
hero-2000.avif 139053 hero-2000.webp 101402 hero-2000.jpg 426074
```

**`sizes` is the part that gets faked, and getting it wrong wastes everything above.** `sizes`
must describe the image's **layout width**, not the viewport. Verified semantics from MDN: with
`w` descriptors, `sizes` is **mandatory**; the browser evaluates the media conditions left to
right, takes the first match, divides each `w` by that width to get an effective density, and
picks the closest candidate. Default when omitted is `100vw`, which over-fetches badly for
anything that is not full-bleed.

```html
<!-- full-bleed hero -->            sizes="100vw"
<!-- centred article body, 720px -->sizes="(min-width: 760px) 720px, 100vw"
<!-- 3-col card grid, 32px gaps -->  sizes="(min-width: 1024px) calc((100vw - 96px) / 3),
                                            (min-width: 640px) calc((100vw - 64px) / 2),
                                            100vw"
<!-- fixed avatar -->                sizes="48px"    (or just use x descriptors: "a.jpg 1x, a@2x.jpg 2x")
```
Rules to encode: mixing `w` and `x` descriptors in one `srcset` is invalid. `<source>` elements
inside `<picture>` each need their own `sizes`. The browser picks the **first** `<source>` whose
`type` it supports, so order must be AVIF, then WebP, then the `<img>` fallback.

### 6.4 Placeholders: LQIP, BlurHash, ThumbHash

**LQIP as an inline data URI - verified.** A 24px-wide WebP came out at **96 bytes**, giving a
151-character data URI. That fits in the HTML with no extra request.

```bash
magick src.jpg -resize 24x -strip -quality 40 lqip.webp
echo "data:image/webp;base64,$(base64 -w0 lqip.webp)"
# verified: 96 B file -> 151-char data URI
```
```html
<img src="/img/hero-1200.jpg" srcset="..." sizes="..." width="2400" height="1600"
     alt="" loading="lazy" decoding="async"
     style="background-image:url('data:image/webp;base64,UklGRlgA...');
            background-size:cover; background-position:center;">
```
The browser paints the blurred background immediately and the real image covers it on load. No JS,
no library. Add `filter: blur(...)` on a wrapper if you want it softer, though at 24px the
upscaling already blurs it.

**Dominant colour, the cheapest placeholder of all - verified:**
```bash
magick src.jpg -resize 1x1\! -format "%[pixel:p{0,0}]" info:
# -> srgb(47.6488%,50.198%,32.9354%)
magick src.jpg -resize 1x1\! txt: | tail -1
# -> 0,0: (122,128,84)  #7A8054  srgb(...)
```
Unsplash returns this for free as `photo.color`; Pexels as `avg_color`.

**ThumbHash - verified end to end.** 21 bytes, 28 base64 chars, encodes aspect ratio, alpha and
better colour than BlurHash in the same space. Preferred over BlurHash for new work.

```bash
npm i thumbhash
```
```js
// th.mjs  - verified: printed "dims [100,67] bytes 21 b64 W/kNLYiHeHeAd4iHeGiHeIeAeAiI"
import { rgbaToThumbHash } from 'thumbhash';
import { execSync } from 'node:child_process';
const src = process.argv[2];
const [w, h] = execSync(`magick "${src}" -resize 100x100 -format "%w %h" info:`)
  .toString().trim().split(' ').map(Number);          // ThumbHash wants <= 100x100
const raw = execSync(`magick "${src}" -resize 100x100 -depth 8 RGBA:-`, { maxBuffer: 1 << 26 });
const hash = rgbaToThumbHash(w, h, new Uint8Array(raw));
console.log(Buffer.from(hash).toString('base64'));
```
Decode client-side with `thumbHashToDataURL(bytes)` from the same package, or precompute the data
URL at build time and inline it exactly like the LQIP above - which is usually better, because it
removes the client-side decode entirely.

**BlurHash** is still worth knowing for one reason: **the Unsplash API returns `blur_hash` on
every photo for free**, so if you are on Unsplash you get a placeholder with zero extra work.
Otherwise choose ThumbHash.

### 6.5 Explicit dimensions, CLS, and priority

```html
<img src="hero-1200.jpg" srcset="..." sizes="100vw"
     width="2400" height="1600"        <!-- INTRINSIC px of the source, not the CSS size -->
     alt="" fetchpriority="high" decoding="async">
```
```css
img { max-width: 100%; height: auto; }   /* the pair that makes width/height responsive */
```
- `width` and `height` must be the **intrinsic** dimensions. The browser divides them to get the
  aspect ratio and reserves the box before the bytes arrive. With `height: auto` in CSS, the
  attributes control aspect ratio only, not the rendered size. Omitting them is the number one
  cause of CLS.
- **`loading="lazy"` on the LCP hero is a bug.** It delays the largest paint. Use
  `fetchpriority="high"` on the hero and `loading="lazy"` on everything below the fold.
- Preload the hero in `<head>` when it is the LCP element, matching the `<picture>` selection:
```html
<link rel="preload" as="image"
      imagesrcset="/img/hero-800.avif 800w, /img/hero-1600.avif 1600w"
      imagesizes="100vw" type="image/avif" fetchpriority="high">
```
- For a CSS-background image or an unknown ratio, reserve with `aspect-ratio: 3 / 2`.
- Wrap in a container with `overflow: hidden` plus `object-fit: cover` when the layout ratio
  differs from the asset ratio, so a mismatch crops instead of shifting the page.

### 6.6 PNG and SVG in the same pipeline

```bash
# PNG: quantise and strip. oxipng is not installed; ImageMagick covers most of the win.
magick in.png -strip -define png:compression-level=9 PNG8:out.png   # palette, big win for UI art
magick in.png -strip -colors 64 -dither FloydSteinberg out.png
# If you install oxipng, it is strictly better for the lossless pass:
#   oxipng -o 4 --strip safe --alpha out.png

# SVG: always the last step, always with a size check
npx -y svgo@latest --multipass -p 2 -f ./dist/img -r -q
find dist/img -name '*.svg' -size +20k -printf '%s %p\n'   # flag anything suspiciously large
```

---

## Decision tree: generate, fetch, or code it?

| Asset need | Source | Why |
|---|---|---|
| **Hero photograph, real place/object/person** | **Openverse** (`license=cc0,pdm`) first - no key, works immediately. **Unsplash** when a key exists and the site is public (hotlink + download-trigger obligations). **Wikimedia Commons** for anything specific, technical, architectural or historical. | Free, licensed, and Commons/Openverse corpora were not shot to sell, so they read as documentary rather than stock. |
| **Photograph of a generic business concept** | **Do not fetch one.** Replace with a product screenshot, typography, or a coded abstract background. | Every free source's "business" corpus is the overused set. This is where the stock-photo tell lives. |
| **UI icon** | **Iconify API**, one prefix for the whole project. `lucide` default, `tabler` when coverage runs short, `ph` when weight is a design tool, `radix-icons` for dense 15px UI. | Free, unauthenticated, verified. `currentColor` preserved. One set = no mixing tell. |
| **Brand / company logo mark** | `simple-icons` (`si:` prefix, CC0) via the same API, or the vendor brand kit. | Separate bucket from UI icons; never held to the UI stroke rules. |
| **Spot illustration** | **Code it (Section 4) or omit it.** If genuinely required: one artist, one pack, recoloured to tokens. **Never unDraw or Humaaans.** | Corporate Memphis is the strongest template/AI tell on the list. |
| **Organic blob, wave, divider** | **Code it.** `blob.py` / `wave.py`, 20 lines each, seeded. | Verified renders. Seedable, themeable, tiny, untraceable to a library. Haikei does the same math with less control. |
| **Grain / noise / anti-flatness** | **Code it.** `feTurbulence` overlay at 6-20% opacity, tiled at 180-256px, or baked to a WebP tile. | Verified. ~300 bytes. Highest visual return of any technique here. Never fetch a grain PNG. |
| **Mesh / atmospheric gradient** | **Code it.** Stacked `radial-gradient(at X% Y%, ... , transparent NN%)` in **oklch**, plus grain. Bake blurred-ellipse SVG to AVIF for a hero. | No native CSS mesh exists in 2026. oklch interpolation is what stops the blend going muddy. |
| **Dot grid, graph paper, hatch, stripes** | **Code it.** `background-image` gradients + `background-size`, driven by `color-mix(in oklab, currentColor N%, transparent)`, faded with `mask-image`. | Zero bytes, auto dark-mode, scales with the layout. |
| **Illustrative repeating motif (topography, circuits, jigsaw)** | **Hero Patterns** (CC BY 4.0), copied into the repo. | The one pattern case where hand-writing SVG is genuinely not worth it. Attribution required. |
| **Angled section, notch, curved edge** | **Code it.** `clip-path: polygon()` with a `@supports` upgrade to `shape()` (Baseline Feb 2026). | One line. `shape()` finally accepts `%` and `calc()`. |
| **Soft/feathered/gradient edge** | **Code it.** `mask-image` (Baseline Dec 2023). | `clip-path` cannot do soft edges. |
| **Raster logo that must become SVG** | **potrace** if bitonal (smallest, cleanest). **vtracer** if colour or you want one command. **Redraw by hand** if the mark is geometric. | Verified: potrace 1.7 KB vs vtracer 2.5 KB post-SVGO on identical input. |
| **Photo that must become a vector** | **vtracer** `--preset poster` for colour; **potrace** with manual threshold layers for a screen-print look. | Reduce the source to ~900px and 12 colours first or the SVG will be megabytes. |
| **Any SVG about to ship** | `npx svgo --multipass -p 2`, plus `removeDimensions`, `convertColors {currentColor:true}`, and a viewBox check. | Verified 19-54% reduction. vtracer emits no viewBox - always check. |
| **Any raster about to ship** | Resize to 2x rendered -> AVIF + WebP + JPEG ladder -> `<picture>` with real `sizes` -> ThumbHash or 24px LQIP -> intrinsic `width`/`height`. | Verified pipeline; ImageMagick alone covers webp, so cwebp is optional. |

---

## One-time setup

### Install (Arch Linux)

Already present and verified working: `imagemagick` (with webp/heic/jxl/rsvg delegates),
`libavif` (`avifenc`), `ffmpeg`, `vtracer`, `potrace`, `inkscape`, `librsvg` (`rsvg-convert`),
node 24 (`npx`), python 3.14, `uv`.

```bash
# Nothing here is strictly required. Each is a marginal improvement.
sudo pacman -S --needed libwebp   # cwebp/dwebp/gif2webp. ImageMagick already does webp,
                                  # but cwebp gives -near_lossless and better animation control.
sudo pacman -S --needed oxipng    # strictly better lossless PNG than ImageMagick's pass
sudo pacman -S --needed jpegoptim # optional extra lossless JPEG pass
sudo pacman -S --needed python-pillow  # only if you want image analysis in Python
                                       # (ImageMagick covers everything in this doc)
```
```bash
# Node tools: run on demand, do NOT install globally.
npx -y svgo@latest --version     # verified working
npm i thumbhash                  # verified working, per-project
# sharp is only worth adding inside a JS build (Astro/Next/Vite already bundle it);
# for a shell pipeline ImageMagick + avifenc is equivalent and already installed.
```

### Free API keys to get

| Service | Needed? | Where | Notes |
|---|---|---|---|
| **Openverse** | **no** | - | Works anonymously right now. Register at `POST https://api.openverse.org/v1/auth_tokens/register/` only if you hit the anonymous throttle. **Best default for an agent.** |
| **Wikimedia Commons** | **no** | - | Set a descriptive `User-Agent` with a contact address. That is the whole policy. |
| **Iconify** | **no** | - | Public API, free, unauthenticated. Verified. |
| **Unsplash** | yes | https://unsplash.com/oauth/applications | Free. Starts in **demo (50 req/hr)**. Apply for production (**1000 req/hr**) by submitting screenshots proving correct attribution and the download trigger. Approval typically ~48 h. |
| **Pexels** | yes | https://www.pexels.com/api/new/ | Free. 200/hr, 20,000/month immediately, no approval step. **Lowest-friction keyed option.** |
| **Pixabay** | yes | https://pixabay.com/api/docs/ (key shown when logged in) | Free account. 100 req/60 s. Must cache 24 h and must not hotlink. `fullHDURL`/`imageURL`/`vectorURL` need separate "full API access" approval. |
| **TinEye** | optional, paid | https://services.tineye.com/ | Only overuse-detection API that exists. From ~$200/month. Do not put it in a default path. |

### Environment variables the skill should read

```bash
export UNSPLASH_ACCESS_KEY=...   # optional; enables Unsplash + the downloads-count overuse filter
export PEXELS_API_KEY=...        # optional
export PIXABAY_API_KEY=...       # optional
export OPENVERSE_CLIENT_ID=...   # optional; raises the anonymous throttle
export OPENVERSE_CLIENT_SECRET=...
# With none of these set the skill must still work: Openverse anonymous + Wikimedia Commons
# + Iconify + everything in Section 4 need no credentials at all.
```

### Project-level conventions to write once

```
assets/
  icons/            # one Iconify prefix only; enforce with the grep test in 2.3
  photos/
    _src/           # originals, gitignored
    *.avif *.webp *.jpg   # generated ladder, committed or built
  art/              # code-generated SVG (blobs, waves, dividers); commit the generator too
  generators/
    blob.py  wave.py  grain.py  mesh.py
svgo.config.js      # removeDimensions + convertColors{currentColor} + viewBox pinned on
```
