# Cannibalization

Loaded when two of the client's own pages trade places for one query: spotted in seo-ops step 2 or 3,
during the step 1 audit, or when a ranking keeps swapping URLs. Separates true cannibalization from
harmless overlap and gives one fix per query.

Cannibalization is not "two pages mention the same keyword". It is two pages Google actually ranks and
rotates for the SAME query, neither winning because the signal is split.

## Input
GSC rows grouped by query AND page: Looker Studio (Search Console connector, dimensions Query + Landing
Page), Search Analytics for Sheets (group by query and page), or the GSC API. To check one query by hand:
Performance, filter by the query, open the Pages tab. Minimum columns: query, page, clicks, impressions,
position. Query-only data cannot detect cannibalization: stop and say how to get the page dimension.

## Procedure
1. **Parse and group** rows by query.
2. **Flag candidates:** queries where 2+ pages each have meaningful impressions. Ignore queries where one
   page takes nearly all impressions (that is a clear winner). Starting heuristics: each page 10+
   impressions, and no page above ~90% share. Tune to the site's volume and state what you used.
3. **Classify each candidate:**
   - TRUE CANNIBALIZATION: 2+ pages trading positions, both in the top 20, impressions split with no
     clear majority (e.g. no page above ~70%, heuristic). The real problem.
   - SECONDARY DRAG: one page clearly ranks (top 10, majority share), a second nibbles from deep
     positions. Minor: canonical or internal-link nudge.
   - HARMLESS OVERLAP: pages serve genuinely different intent (a guide and a service page). Keep both.
   - NEAR-DUPLICATE: two pages that should never both have existed. Consolidate regardless of positions.
4. **One fix per TRUE / NEAR-DUPLICATE query** (the strongest only):
   - CONSOLIDATE: merge the weaker into the stronger, 301 the weaker URL. Same intent, one clearly
     stronger. This is the default: SEO-GUIDE prefers fewer, deeper pages.
   - CANONICAL: weaker page's canonical points at the stronger. Both must exist but only one should rank.
   - DIFFERENTIATE: refocus one page on a distinct sub-intent (title, H1, opening). Both deserve to rank
     for different real questions.
   - DEMOTE INTERNAL LINKS: stop linking the wrong page with the target anchor; point those links at the
     keeper. Supporting move, or when the split is internal-link driven.
5. **Pick the keeper:** better position, more clicks, stronger links if known, best intent match. Say why.

## Output
```
CANNIBALIZATION REPORT
Date range | queries analysed | queries with multiple pages | true cannibalization count

TRUE CANNIBALIZATION (worst first by combined impressions)
  QUERY: [query]
  COMPETING PAGES: [url1] (pos X, N clicks, M impr) vs [url2] (...)
  WHY IT IS REAL: [one line on the split, e.g. "55/45 at positions 8 and 11"]
  KEEPER: [url] and why
  FIX: [CONSOLIDATE / CANONICAL / DIFFERENTIATE / DEMOTE INTERNAL LINKS] + the specific action
  EXPECTED: direction to check in GSC after 4-8 weeks (keeper's position and click share), never a
  promised position

SECONDARY DRAG (query, winner, nibbler, one-line action)
NOT CANNIBALIZATION (harmless different-intent overlap, so nobody wastes time)
NEAR-DUPLICATE PAGES (pairs to consolidate)
DO THIS WEEK (top 3 by combined impressions)
NOT CHECKED: on-page depth, per-page backlinks, true user intent, whether a 301 passes full equity.
Next move once consolidated: ref/striking-distance.md.
```

## Rules
- Single-page dominance is the goal, not a problem.
- One fix per query. Weight by combined impressions, not query count.
- Never invent pages or queries. Be honest about intent overlap.
- Missing positions: you can still flag multiple pages per query, but say the call is weaker.
- Branded queries (homepage + a service page) are usually harmless: flag separately.
- `?page=2`, `?sort=` and other parameters are canonical/parameter handling, not cannibalization.
- 3+ competing pages: pick one keeper; consolidate or differentiate the rest.
- Large export: focus on the top ~2,000 rows by impressions and say so.
- Write in the client's language (en, or es-CO for Colombian clients).
