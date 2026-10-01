# Striking distance and title CTR

Loaded by seo-ops step 2 (page-2 lift), and whenever a page has high impressions but low clicks. Finds
queries ranking at positions 4-20, scores them for click-gain potential against the site's OWN CTR curve,
and gives a per-page action plan. Positions 11-20 mostly need internal links and on-page depth; positions
4-10 mostly need a better title and snippet.

## Input
GSC rows with query AND page on the same row (the plain Performance export splits them). Get them from
Looker Studio with the Search Console connector (dimensions Query + Landing Page), the Search Analytics for
Sheets add-on (group by query and page), the GSC API, or by filtering Performance to one page and
exporting its Queries tab. Last 28 days or 3 months. Minimum columns: query, page, clicks, impressions,
position. Ask for the brand name so branded rows can be separated. No position column = cannot run, ask
for a re-export.

## Procedure
1. **Parse.** CTR = clicks / impressions per row (GSC writes CTR as a percentage, convert it). Drop rows
   with position > 100. Drop near-zero-impression rows as noise; state the floor you used.
2. **Build the site's CTR curve first,** from the full export before filtering, non-branded rows only:
   median CTR per position bucket (1-3, 4-6, 7-10, 11-20). This is the baseline everything is measured
   against. If a bucket has too few rows to trust (say under 20, a starting heuristic), widen the date
   range; if still thin, do not score the CTR gap for that bucket and say so in the header. Never fall
   back to industry CTR tables.
3. **Filter** to positions 4-20.
4. **Score each query:**
   ```
   lift = impressions x (target_ctr - current_ctr) x position_weight
   target_ctr      = site median CTR at positions 1-3 (step 2)
   current_ctr     = the row's CTR
   position_weight = a ranking weight that favours queries nearer the top 3, e.g. linear from 1.0 at
                     position 4 down to 0.5 at position 20 (a starting heuristic for ordering, not a
                     measured value)
   ```
   If current_ctr is already at or above target_ctr, lift = 0: the gain there is rank, not CTR. Scores are
   for ordering only, never a forecast.
5. **Group by page,** sum the lift, rank pages, take the top 10.
6. **CTR-gap check (titles).** For each page, compare its CTR with the site's median for its position
   bucket. A page well below its bucket median is a title/snippet problem before it is a ranking problem.
   AI Overviews and other SERP features can also pull CTR down; name one as the cause only if it was seen
   in the live results for that page's main queries, otherwise mark the cause unverified.
7. **Per-page plan** (template below). Read the current title, meta description, H1 and opening from the
   site source or the live page; never guess a current title.

## Title rewrite rules
- Google truncates by pixel width (about 600px on desktop), not characters. Roughly 50-60 characters is a
  starting point; wide letters and capitals run out sooner. Check with a SERP preview tool.
- The query the page already ranks for stays in the title, near the front. If it is already there, the
  change is ordering and prominence, not adding it again (no stuffing).
- Keep the title consistent with the H1 and the content; Google rewrites title links that are too long,
  stuffed or out of step with the page.
- One concrete detail (price, speed, proof, number) only if it is real: from the client or already on the
  page. Otherwise a bracketed placeholder such as [review count].
- Location for local businesses. Brand at the end after a pipe or hyphen. No ALL CAPS, no stacked
  punctuation.
- Patterns: keyword + benefit, keyword + proof, keyword + specificity, question + answer, number + keyword.
- Meta description about 140-155 characters (also pixel-truncated), primary query early.
- Write in the client's language (en, or es-CO for Colombian clients).

## Per-page output
```
PAGE: [URL]
PAGE LIFT SCORE: [n]   CTR vs site median at this position: [x% vs y%]
TOP QUERIES (up to 5): "[query]" - pos [X], imp [Y], score [Z]
THEME: [one sentence tying the queries together]

1 TITLE: current "[...]" ([chars]) -> proposed "[...]" ([chars]). Why: [one line]
  (offer 2-3 options when the CTR gap is the main finding; mark the recommended one)
2 META DESCRIPTION (only if the title alone will not move it): [...]
3 ON-PAGE ADDITION: [the specific H2/section/paragraph on THIS page that answers the queries. Never a new
  page for the query: expand the page that already ranks, per SEO-GUIDE sec. 1-2.]
4 INTERNAL LINK: [existing page on the site] -> this page, anchor "[descriptive anchor]"
Direction: from position [avg] toward the top 3. Not a forecast.
```

## Report
```
STRIKING DISTANCE REPORT
Date range | rows analysed | rows at 4-20 | pages | CTR baseline: site medians per bucket (list them)
TOP 10 PAGES (per-page plans above)
ALSO WORTH NOTING (pages 11-20: page, score, top query, one-line action)
QUERIES WITH NO PAGE MATCHED (ask which existing page should own each one)
QUICK WINS THIS WEEK (top 3 smallest-effort, biggest-lift; usually title swaps)
NOT CHECKED: whether the page deserves the top 3 (content quality), off-site signals, intent mismatch
(a 4-20 query with no clicks may be the wrong intent, not under-optimised), seasonality
```

## Rules
- Never invent queries or pages. Internal links only from pages that exist; if unsure, "from the relevant
  hub page" and let the operator resolve it.
- A page with 5+ queries in range is a content-depth job on that page, not a single tweak. Flag it.
- Mostly branded data: say so; branded queries need entity work (SEO-GUIDE sec. 9), not this.
- Low-impression queries at position 15+ are often noise. Do not promise fixes for them.
- After a title change, re-check the live SERP once Google recrawls; Google sometimes rewrites titles.
- Show any click maths as a scenario on the client's real impressions, never a promise.
- Over ~5,000 rows: sample the top 2,000 by impressions and say so.
