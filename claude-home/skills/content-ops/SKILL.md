---
name: content-ops
description: >
  Write website copy and blog content for clients that gets them FOUND in Google and AI
  answers - not generic AI slop. Two modes: build-time page copy (collaborative, sounds like the
  client) for /new-site, and recurring blog content (topical authority from the customer's real
  questions) for the /monthly-ops Content add-on. Uses voice-dna + anti-ai-writing, obeys SEO-GUIDE
  topical rules. Never bulk/daily auto-AI content (scaled-content-abuse) or page-per-keyword.
---

# Content Ops

The content engine. Two modes - pick by the job. Quality-first and penalty-safe. Grounded in the
build-templates guides: **`CONTENT-GUIDE.md`** (canonical for what a page says + the 7 homepage questions +
scan structure + the copy method), `SEO-GUIDE.md` (technical + AEO/GEO), and `MONTHLY-OPS-GUIDE.md` sec. 2
(recurring blog cadence).

## Mode A - build-time page copy (in `/new-site`)
Collaborative, not done-for-you. Frame to the client: *"we work through your copy together - placement
guidance + editing support - so it sounds like you and sells."*
1. Interview one page at a time (Charlie Hills' COPY.md method): draft every word into a copy doc; the
   client approves before any code.
2. Each page answers its intent. The homepage answers the 7 questions: what do you do / who is it for /
   why it matters / why trust you / services / proof / what to do next. "Why you" clear in 5 seconds.
3. Draft with **voice-dna** (the client's voice) + **anti-ai-writing** (strip AI tells). Benefits before
   features, one clear CTA, concise + scannable.
4. Optimize per SEO-GUIDE (unique title/description, one H1, semantic structure).

## Mode B - recurring blog content (in `/monthly-ops` Content add-on)
Sell "getting found," not "writing blogs." Per MONTHLY-OPS-GUIDE sec. 2:
1. **Pick real questions** the customer Googles: AnswerThePublic (free) + GSC queries + the client's FAQ.
   One clear intent each. **Never** a page per keyword.
2. **Get the expertise.** Interview the client (prompt: *"ask me anything you'd need to write a truly
   helpful, unique answer - my experience, examples, opinions; 10 questions, one at a time"*). Makes it
   theirs, not generic.
3. **Draft** with voice-dna + anti-ai-writing. Genuinely helpful, answer-first, specific. Anything that
   needs a real number, story, price or credential the interview did not supply becomes an inline
   `[EXPERTISE GAP: <specific question for the client>]` - never invented. The client fills every gap
   before publish.
   - **List format?** Only if the query wants one (top results are lists); otherwise the guide or
     comparison shape. Each item: a descriptive H2 that states the point + a self-contained first line
     that can be lifted alone. Cut shallow items. One honest list, never "best X for Y" variants.
4. **Review the draft before optimizing.**
   - Information gain: tag each major point CONSENSUS (on every page for the query), PARTIAL (common point,
     one specific detail) or ORIGINAL (first-hand, own data, expert take). Compress consensus, expand
     partials with the client's specifics, and front-load the original value. Mostly consensus with no
     first-hand input = go back to step 2, do not rewrite the words.
   - Pre-publish warning signs (any one present = fix first): made mainly for search engines; off the
     site's focus or outside the client's expertise; mostly summarising others; chasing a trend outside the
     audience; leaves the reader needing to search again; written to a word count; promises an answer that
     does not exist; dates changed or content shuffled only to look fresh.
5. **Optimize** per SEO-GUIDE: Article/BlogPosting JSON-LD, `dateModified`, real image + alt (use the
   `nano-banana` skill for imagery).
6. **Internal links:** 3 from the new post to money/service pages, 1-2 from existing pages into it.
7. **Publish -> ping IndexNow -> confirm rendered in HTML** (not JS-only).

## Tools
- **voice-dna** (skill) - build a `voice-dna.md` per client from ~20 of their samples. If none, capture
  voice manually from 2-3 samples.
- **anti-ai-writing** (skill) - the final de-slop pass on every written piece.
- AnswerThePublic (free), `nano-banana` (images), SEO-GUIDE (canonical optimization).

## Never
Bulk/daily auto-published AI articles (scaled content abuse), page-per-keyword stubs, FAQPage/HowTo markup
(deprecated), ranking guarantees. That is the getautoseo/distribb trap - we are the human, penalty-safe
alternative.
