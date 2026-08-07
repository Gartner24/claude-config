---
name: seo-ops
description: >
  Run recurring SEO/AEO for a LIVE client site - monthly audit, page-2 internal-link lifts,
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
   audit manually against SEO-GUIDE's per-page-type checklists (sec. 15/sec. 16).*
2. **Page-2 internal-link lift** (highest ROI): GSC -> Search results -> Queries, sort by position -> find
   keywords ranking **11-20** with high impressions -> add 2-3 internal links with descriptive anchors from
   relevant pages to each target page.
3. **Language mining:** GSC -> "customize report using AI" -> "local-intent" / "comparison/evaluation" /
   "service-based" queries -> use that exact language more thoroughly on the page (sections/headings),
   never a new thin page.
4. **Structured-data check:** re-validate JSON-LD (Organization/LocalBusiness, Article, Product+Offer,
   AggregateRating). Skip FAQPage (deprecated May 2026).
5. **Technical hygiene:** broken links, orphan pages, redirect chains, truthful sitemap `lastmod`, sane
   robots. Fix per SEO-GUIDE.
6. **Re-index:** submit changed URLs via **IndexNow**; confirm the sitemap is fresh in GSC + Bing.

## Output
Feed the SEO/AEO section of the monthly report: audit-score delta, keyword movements (GSC), internal links
added, issues fixed.

## Install note
claude-seo is a plugin: `claude plugin marketplace add AgriciDaniel/claude-seo` then
`claude plugin install claude-seo@agricidaniel-claude-seo`. Audit-only (no account access). It complements
SEO-GUIDE - the guide stays canonical for anything build-time; if they ever conflict, the guide wins.

## Never
Page-per-keyword thin pages, auto-published bulk content, automated/reciprocal/bought/exchanged backlinks,
ranking guarantees. Backlinks are the separate EARNED-only runbook (MONTHLY-OPS-GUIDE sec. 5).
