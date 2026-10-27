# watch-reels skill (owner request 2026-10-26)

## Agreed so far, do not ask again
- Owner: "In downloads/temp/watch-reels.zip I need to watch a really big batch of reels please install this skill and lets test with a reel ... tell me if you really can watch it, meaning the audio and the visual part, and tell me if you can see ... images or carrousels (all the images in the post) if not, improve the skill to do it too."
- The skill lives as our own skill in `claude-home/skills/watch-reels/` (branch `feat/watch-reels`), linked by install like build-features; add `watch-reels` to `tools/scripts/skill-keep.txt` so "watch this" plus a link triggers it.
- Logged out only, never cookies or the owner's accounts (kept from the original skill). The auto mode classifier refused a raw curl of the Instagram embed page with a browser user agent: do not scrape outside yt-dlp.
- Batch: the owner wants a really big batch. The original skill forbids batches; replace that rule with: a list of links the owner gives (never enumerate a profile or feed), a polite delay between posts, stop after 3 failures in a row (rate limit) and resume on rerun.

## Live state (2026-10-26)
- Original zip read in full, skillspector clean (0 serious), its own 4 tests pass. Unpacked at `~/.claude/jobs/fd2083a4/tmp/watch-reels-src/` (job scratch).
- Test 1, reel https://www.instagram.com/p/De-LGwIkzE9/: download works logged out; visual works (key frames read: talking head, captions, OpenMontage screenshots, OPEN CTA); audio worked only after the fix below: full timed transcript. Sound limit: speech + loudness only, no music or SFX description.
- Fix 1 (in branch): `breakdown.py` decodes audio with ffmpeg and passes samples to faster-whisper, because PyAV versions break faster-whisper (`metadata_errors` TypeError; pinning `av<15` fails to build on ffmpeg 8). Run with `uv run --with faster-whisper python3 ...` (no system install).
- Test 2, carousel https://www.instagram.com/p/DeUvb21jhH_/: the original skill cannot (yt-dlp errors on photo slides, gallery-dl hits the login wall). Fix 2 (in branch): `fetch.sh` takes every slide of one Instagram /p/ or /reel/ post with `--yes-playlist --ignore-no-formats-error --write-thumbnail` (a photo slide's thumbnail is the photo, 1080x1350), caption once to `caption.txt`. All 9 slides fetched (3 photos, 6 silent videos). New `post.py` writes `post.md` (caption, slide list, a breakdown per video slide, photos/ plus `photos.jpg` sheet); seen and correct.

## Review 2026-10-26 (/review, 4 lenses plus a second pass)
- Fixed: a post with any slide missing now fails and is fetched again on rerun (yt-dlp exits 1 on every photo slide, so the check reads the log: any ERROR other than "No video formats found", or a slide with no file); stale slides cleared before a fetch; every video and audio part deleted, also on failure; a done link after the 3-failure stop shows "skipped"; `fetch.sh --delete` refuses anything but .mp4; caption and transcript are fenced so their text cannot pass for our headings; spoken text left the summary line; a Whisper model error skips the transcript instead of failing the page; Instagram links with a user name in them take the whole-post path; the suite runs the skill's tests (`tests/test_watch_reels.py`).
- Open for the owner: whether `watch-reels` joins the always-described skill list (`tools/scripts/skill-keep.txt`, pinned at 37 names by spec 0050). Off the list, "watch this <link>" may pick the `watch` plugin instead; typing `/watch-reels` always works.

## Next
1. Owner answer on the skill list above.
