# AI citation share (Bing AI Performance)

Loaded by the seo-ops AI citation share step, and alongside MONTHLY-OPS-GUIDE sec. 7 (AI-visibility check).
Turns the Bing Webmaster Tools AI Performance report into a ranked plan: where the client owns the
citation space, where it is losing it, and the one move per opportunity. The manual prompt check in sec. 7
shows WHETHER the client is named; this shows WHERE Copilot and Bing AI answers already cite the site.

## Definitions (use them exactly)
- CITATION SHARE: percentage of all citations shown for one grounding query that go to this site. It is
  observational, NOT a competitor scoreboard: Bing exposes no competitor domains, traffic or quality.
  Never present it as a leaderboard.
- GROUNDING QUERY: the short phrase the AI used to retrieve and cite content. Not the user's prompt.
- TOPICS: grounding queries clustered into themes.
- INTENTS: the category behind the citation (Informational, Commercial, Navigational, Learn and Solve,
  Research, Creation, Local, and more).
- COMPARE: the same metrics against a prior period.

## Input
Bing Webmaster Tools -> AI Performance -> date range (30 days is a sensible baseline) -> export grounding
queries with citation counts and Citation Share, plus Topics, Intents and the Compare deltas if shown, and
the pages-cited list. Counts without shares: rank by volume and say the own-vs-contested read is weaker.

## Procedure
1. **Parse** each grounding query: citations, share, Topic, Intent, Compare delta.
2. **Bucket** each query, rolled up to Topic. Set the cut-offs from this site's own share distribution
   (e.g. top quartile = OWNED, middle = CONTESTED, bottom = UNDER-REPRESENTED) and state them; fixed
   percentages are only a starting heuristic (roughly 40%+ owned, 10-40% contested, under 10% low).
   - OWNED: the site is the default source. Protect it.
   - CONTESTED: middling share on real citation volume. Biggest opportunities: already cited, so lifting
     share is a content and authority job.
   - UNDER-REPRESENTED: low share on a high-volume query.
   - ABSENT: a Topic or Intent with citation activity where the site does not appear.
3. **Weight by opportunity,** not raw share: citation volume x intent value. Commercial, Local and Learn
   and Solve usually sit closest to revenue. A 60% share on 3 citations is worth less than 15% on 300.
4. **Read Compare.** Falling share on an OWNED or CONTESTED commercial query is the most urgent finding.
5. **One move per opportunity:**
   - LIFT (contested): strengthen the cited page with the specific sub-answer, data or section the
     grounding query implies; add internal links and entity signals (SEO-GUIDE sec. 9).
   - ENTER (absent): expand the existing page that fits the Topic so it answers those grounding queries.
     A new page only when the Topic is a genuine customer question no page serves, and then one thorough
     page for the Topic, never a page per grounding query (SEO-GUIDE sec. 1-2, scaled content abuse).
   - DEFEND (falling): refresh the cited page and confirm it is still crawlable by AI and search bots
     (AGENT-READINESS-GUIDE sec. 3 robots AI groups, rendered HTML).
   - HARVEST (owned commercial): make sure the cited page converts.

## Output
```
CITATION SHARE AUDIT
Date range | grounding queries | Topics | average share | bucket cut-offs used | headline: Topics owned,
contested, absent

THE PATTERN (2-3 sentences: where citations concentrate, the biggest gap or leak)

PRIORITY MOVES (up to 8, leaks first, then biggest opportunity)
  GROUNDING QUERY / TOPIC: [...]
  INTENT: [...]
  CITATION SHARE: [x%] (Compare delta if known)
  BUCKET: [OWNED / CONTESTED / UNDER-REPRESENTED / ABSENT]
  MOVE: [one action, page or Topic named]

DO THIS MONTH (top 3, commercial intent first)
NOT CHECKED: competitor domains, traffic or rankings (Bing does not expose them); crawl access.
```
One line of it goes in the monthly report's AI-visibility section next to the sec. 7 prompt check.

## Rules
- Never a competitor leaderboard. Never invent queries, Topics or shares.
- One move per opportunity; surface leaks before chasing new wins.
- Zero citations across the board: the problem is upstream (crawl access, or the site is too new). Check
  that first; AI cannot cite what it cannot read.
- A handful of queries: soft read, suggest a wider date range. A single export is not a trend.
- Site-wide drop in Compare: check for a model or algorithm update window, a migration or a crawl
  regression before blaming content.
- All informational, no commercial share: the move is commercial-intent depth on existing service pages.
- Write in the client's language (en, or es-CO for Colombian clients).
