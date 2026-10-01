---
name: seo-ops
description: >
  Run recurring SEO/AEO for a live client site - monthly audit, page-2 internal-link lifts,
  GSC language mining, structured-data upkeep, and re-indexing (IndexNow). The run-time counterpart to
  the build-time SEO-GUIDE. Use for the /monthly-ops SEO/AEO Ops add-on. Uses claude-seo for the audit
  when installed. Never page-per-keyword or automated/bought/exchanged backlinks.
---

# SEO Ops

Recurring SEO/AEO execution for a live client site. Build-time SEO is `SEO-GUIDE.md` (canonical, in
`~/projects/freelance/website-build-templates/guides/`); this is the monthly runbook, per
`MONTHLY-OPS-GUIDE.md` sec. 1.

## Monthly cycle
1. **Audit** with **claude-seo** (plugin - see install note) -> prioritized 0-100 action list (technical,
   E-E-A-T, schema, GEO/AEO, local). Fix quick wins now, log the rest. *If claude-seo isn't installed,
   audit manually against SEO-GUIDE's per-page-type checklists (sec. 17) and pre-launch QA (sec. 18).*
2. **Striking-distance lift** (highest ROI): GSC query+page rows at positions **4-20**. Score each query
   `impressions x (site median CTR at pos 1-3 - its CTR) x position weight`, sum per page, work the top
   pages. **11-20:** add 2-3 internal links with descriptive anchors from relevant pages + on-page depth.
   **4-10:** pages whose CTR sits well below the site's own median for that position get a title rewrite
   (keep the ranking query near the front, ~600px desktop width, real proof only). CTR baseline is always
   the site's own GSC data. Template: `ref/striking-distance.md`.
3. **Language mining:** GSC -> "customize report using AI" -> "local-intent" / "comparison/evaluation" /
   "service-based" queries -> use that exact language more thoroughly on the page (sections/headings),
   never a new thin page. Second source: the client's reviews (GBP, platforms) - phrases customers use
   that the pages do not, and repeated objections; map each to the existing page that should carry it.
4. **Structured-data check:** re-validate JSON-LD (Organization/LocalBusiness, Article, Product+Offer,
   AggregateRating only inside Product). Self-serving reviews (a LocalBusiness/Organization reviewing
   itself, on-site or embedded) never get review stars: for service clients reviews are trust content and
   a GBP signal, not schema. Skip FAQPage (deprecated May 2026).
5. **Technical hygiene:** broken links, orphan pages, redirect chains, truthful sitemap `lastmod`, sane
   robots. Fix per SEO-GUIDE.
6. **AI citation share:** Bing Webmaster Tools -> AI Performance export -> bucket grounding queries
   (owned / contested / under-represented / absent), one move each, leaks first. `ref/ai-citation-share.md`.
7. **Re-index:** submit changed URLs via **IndexNow**; confirm the sitemap is fresh in GSC + Bing.

## Reference docs - load only when the step needs it
| Step / situation | Load |
|---|---|
| Step 2, or high impressions with low clicks | `ref/striking-distance.md` |
| Two own pages swap for one query | `ref/cannibalization.md` |
| A page loses clicks over months; refresh vs rewrite vs merge | `ref/content-decay.md` |
| Step 6 (Bing AI Performance) | `ref/ai-citation-share.md` |
| Many pages move around a confirmed Google update | `ref/core-update-triage.md` |
| Reviews add-on: getting reviews, reviews page | `ref/review-engine.md` |
| A negative or suspicious Google review | `ref/review-removal.md` |
| Link-worthy asset, or results expect a tool | `ref/calculator-asset.md` |

## Output
Feed the SEO/AEO section of the monthly report: audit-score delta, keyword movements (GSC), internal links
added, titles rewritten, AI citation share line, issues fixed.

## Install note
claude-seo is a plugin: `claude plugin marketplace add AgriciDaniel/claude-seo` then
`claude plugin install claude-seo@agricidaniel-claude-seo`. Audit-only (no account access). It complements
SEO-GUIDE - the guide stays canonical for anything build-time; if they ever conflict, the guide wins.

## Never
Page-per-keyword thin pages, auto-published bulk content, automated/reciprocal/bought/exchanged backlinks,
ranking guarantees. Backlinks are the separate EARNED-only runbook (MONTHLY-OPS-GUIDE sec. 6).
