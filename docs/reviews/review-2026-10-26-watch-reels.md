## /review: main...feat/watch-reels

**Verdict:** APPROVE after fixes - the one P1 (a half-fetched post marked done) is fixed and pinned by a test
**Coverage:** 4/4 lenses (correctness, security, coverage + absence, design + context) plus a second pass · 14 findings kept, 13 fixed, 1 owner question; second pass 10 of 10 dropped
**Not read:** none

### Findings and fixes
| Sev | Location | Finding | Fix |
|---|---|---|---|
| P1 | scripts/fetch.sh | Slides missing after a rate limit still made a "done" post, never retried | Fail when the log has an ERROR other than "No video formats found" (yt-dlp exits 1 on every photo slide, so its exit code cannot be used) or a slide has no file; clear stale slides first |
| P2 | scripts/batch.py | Only `.mp4` deleted; `.part`, `.m4a`, `.webm` left | Delete everything except `.jpg`, `.txt`, `.log`, also on failure |
| P2 | scripts/fetch.sh | `--delete` removed any path an injected caption could name | Refuse anything but `.mp4` |
| P2 | scripts/post.py, breakdown.py | Caption and transcript could forge our headings; spoken text sat in the summary | `fence()` with a fence longer than any backtick run; summary names only when speech starts |
| P2 | tests/fast.py | The suite never ran the skill's tests | `tests/test_watch_reels.py` |
| P2 | coverage | No test of the page, the Whisper audio shape or fetch.sh | 15 tests added, each mutation checked |
| P2 | SKILL.md | Local file path ran without Whisper | Same `uv run --with faster-whisper` prefix |
| P3 | scripts/batch.py | Done link after the stop shown "not run" | Shown "skipped" |
| P3 | scripts/batch.py | Failure text in index.md unlabeled | Labeled as data |
| P3 | scripts/breakdown.py | Whisper model error failed the whole page | Skips the transcript |
| P3 | scripts/fetch.sh | `/<user>/p/<id>` links missed the whole-post path | Wider case pattern |
| P3 | prompts/STYLE_CARD.md | Inputs and a "Phase 6" reference that do not exist | Trimmed |
| P3 | SKILL.md | "every photo of a carousel" for any site | "Instagram carousel"; long batches run in the background |

### Owner question
`watch-reels` is not on the always-described skill list (`tools/scripts/skill-keep.txt`, 37 names pinned by spec 0050 and its test). Off the list, "watch this <link>" may pick the `watch` plugin; `/watch-reels` always works.

### Guardrails
- Holds while yt-dlp reports a photo slide as "No video formats found"; a new wording would fail every carousel loudly, not silently.
