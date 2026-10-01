# Content decay

Loaded when the monthly report shows a page losing clicks over time (seo-ops output, or MONTHLY-OPS-GUIDE
sec. 3 when choosing what to refresh instead of what to write). Diagnoses why each page is decaying and
prescribes one treatment. For a sudden site-wide drop around a confirmed Google update use
`core-update-triage.md` instead: this doc is for gradual decay.

## Input
Two GSC Pages exports for periods of the same length: recent (e.g. last 3 months) and the same period a
year ago, or at least 6 months back. Performance -> Pages -> set range -> export, repeat; or Date ->
Compare for one export. Columns: page, clicks, impressions, position. Queries for the worst 2-3 pages
sharpen the diagnosis.

- GSC keeps 16 months, and only from when the property was added. Check both periods have data.
- The UI export caps at 1,000 rows per period, so a URL can appear in one export and not the other without
  having zero clicks. Treat a URL found in only one period as UNKNOWN, never zero: keep it out of the loss
  totals, list it separately, and check it with a page filter or the API. Report how many URLs matched.
- One period only: you can rank weak pages but not detect decay. Say so and ask for the comparison.
- Check Google's Search Console data anomalies page for any reporting change inside either window. A
  logging or reporting change can move impressions, CTR and position without a real loss; across such a
  change, judge decline on clicks and on the page's queries.

## Procedure
1. **Match pages** across periods and compute deltas: clicks, impressions, CTR, position. Flag pages with a
   meaningful click decline on real prior traffic. Starting heuristics: clicks down 25%+ on pages with 20+
   clicks in the earlier period; lower the floor for a small site and state the floor and threshold used.
2. **Diagnose** each decaying page by its pattern:
   - FRESHNESS: position slipping slowly, impressions roughly stable; the results now reward newer content.
   - DISPLACEMENT: position dropped in steps, impressions stable; a better page took the spot.
   - INTENT SHIFT: position and impressions hold, clicks and CTR collapse. Either the query now means
     something else or the results page changed (an AI Overview now answers it). A hypothesis until the
     page's queries and the live results are checked.
   - DEMAND: impressions falling across the query set at stable position; the topic is shrinking. Not
     fixable with content. Page-level data alone cannot fully separate this from intent shift; say so.
   - SEASONAL: the earlier period was the topic's peak. Check before calling it decay.
3. **One treatment per page:**
   - REFRESH: update facts, dates, screenshots, add missing subtopics. Freshness decay on a sound page.
     Change `dateModified` only when the content genuinely changed.
   - REWRITE: angle or depth lost to a better competitor. Rebuild against what now ranks, keep the URL.
   - CONSOLIDATE: overlaps a stronger sibling. Merge in and 301 (see `cannibalization.md`).
   - RETARGET: intent shifted; refocus the page on what the query now means, or a query it can win.
   - LEAVE: seasonal or demand decay. Write it down so nobody refreshes it.
   Never prune first. Delete only pages with no queries, no links and no salvageable overlap, after the
   merge option fails.
4. **Rank** by recoverable clicks (prior minus current), weighted toward treatable diagnoses (freshness,
   displacement).
5. **Top 3 refresh briefs:** stale sections, what now-ranking pages cover that this one does not, and what
   only this client can add (`content-ops` interview). Judge stale sections only if you read the page, and
   competitor coverage only if you saw the ranking pages; otherwise list what to check.

## Output
```
DECAY REPORT
Periods | pages analysed | URLs matched | decaying pages | clicks lost | recoverable share (estimate, show
the arithmetic) | thresholds used

THE SICK LIST (worst recoverable first)
  PAGE: [url]
  DECLINE: clicks X -> Y, impressions, position A -> B
  DIAGNOSIS: [FRESHNESS / DISPLACEMENT / INTENT SHIFT / DEMAND / SEASONAL] + one-line evidence
  TREATMENT: [REFRESH / REWRITE / CONSOLIDATE / RETARGET / LEAVE] + the specific action

TOP 3 REFRESH BRIEFS
LEAVE-ALONE LIST
UNKNOWN (URLs in only one export)
DO THIS WEEK (top 3 by recoverable clicks)
NOT CHECKED: backlink changes, update timing, actual SERP contents
```

## Rules and edge cases
- Decay is a trend, never a snapshot. One treatment per page. Seasonality before diagnosis.
- Say plainly when a topic is shrinking; no refresh recovers a market that left.
- Never invent pages, numbers or competitors.
- New site (under ~6 months of data): no decay yet; rank by underperformance and say so.
- Everything declining evenly: site-level event (update, migration, technical). Run
  `core-update-triage.md` and the step 1 audit before any content work.
- Redesign or URL change inside the window: the trend breaks there; mark unmeasurable.
- Branded queries decaying: brand demand or reputation, not content decay. Flag separately.
- Write in the client's language (en, or es-CO for Colombian clients).
