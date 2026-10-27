

### 117. watch-reels: on-screen text, Spanish offers, faster batches · done
You asked for the gaps people's usual posts expose, then a faster skill with nothing lost. Added: on-screen text read from every key frame and photo (RapidOCR through uv, each line listed once per slide), offers in Spanish and on screen, "link in bio" flagged, links and @handles listed, an offer split over two speech segments found at the right time. Faster: each page is built while the next download waits out the pause, and the speech and OCR models load once per batch.
**Done when:** the same two posts give every earlier section plus on-screen text, and a batch without OCR runs faster than before.
- [x] Build: `/develop watch-reels gaps and speed`
- [x] Verify it: `/check verify watch-reels gaps and speed` (live 2026-10-26: like-for-like 35.6 s down to 23.7 s; with OCR 45.5 s for 2 posts, 56 images read; carousel page 15.3 KB down to 7.3 KB after line dedupe)
- [x] Test it: `/test watch-reels gaps and speed` (12 tests added, 13 mutants red; suite 235 ok)
- [x] Sync: `/sync`
Source: your message 2026-10-26 ("Any gaps in the skill? ... optimize the skill so we dont loose anything").
