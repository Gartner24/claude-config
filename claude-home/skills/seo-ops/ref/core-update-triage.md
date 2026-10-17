# Core update triage

Loaded when clicks drop (or jump) across many pages and the timing lines up with a confirmed Google update,
or the client asks "were we hit by the update". Classifies pages as winner, loser or flat around the update
window, then runs each significant loser through the intent-destination fit test: is this page still the
best default destination for its query, in its market, in the format the results now expect?

Core updates shift visibility toward the source type that best fits each query's dominant intent, market
and expected result format. Authority alone does not explain outcomes; pages that complete the task tend
to gain, derivative layers that summarise others tend to lose.

## Input
1. **The update window, as input.** Take the rollout start and end dates from the Google Search Status
   Dashboard (status.search.google.com). Never assume a date from memory. Check the dashboard for any other
   confirmed update (spam, etc.) inside either comparison window; if one overlaps, say the result mixes
   them.
2. **GSC comparison:** Performance -> Date -> Compare. Before = a few weeks ending the day before rollout
   start; after = the same length starting the day after rollout end (never mid-rollout). Pages tab, then
   Queries if possible. Minimum: page, clicks and impressions for both periods; position is a bonus.
3. Ask whether a migration, redesign, tracking or GSC property change happened inside the window; any of
   those invalidates the analysis.

## Procedure
1. **Parse.** Drop rows with negligible impressions in both periods (state the floor, e.g. under 10).
2. **Classify** (starting heuristic thresholds, tune to the site's normal week-to-week noise):
   - WINNER: clicks up 15%+ AND impressions or position improved
   - LOSER: clicks down 15%+ AND impressions or position declined
   - FLAT: everything else
   Rank by absolute click change, not percentage.
3. **Pattern scan across losers first:** same folder or template, same intent type, same market mismatch
   (wrong country signals for the queries), same format mismatch (text page where results now show tools,
   video or marketplaces).
4. **Fit test** for the top 10 losers by click impact. YES / PARTIAL / NO, or UNCHECKED:
   a. SOURCE-TYPE FIT: what type now ranks for the top lost query (reference, official, marketplace,
      local, tool, video, forum)? Is this page that type? If you cannot see the live results, ask the
      operator or mark UNCHECKED. Never describe a SERP you have not seen.
   b. TASK COMPLETION: can the user finish the task here, or does the page summarise something completed
      elsewhere?
   c. MARKET FIT: local entity for local queries; right country signals (currency, language, spelling,
      ccTLD or hreflang) for country-specific queries.
   d. FORMAT FIT: does the page format match what the results now expect?
5. **Verdict per loser:**
   - FIXABLE FIT GAP: one or two NOs with a concrete fix, shippable this month (add the tool, localise,
     restructure to complete the task). Fixes go on the existing page; a missing tool can become a
     calculator per `calculator-asset.md`, never a set of variant pages.
   - WRONG SOURCE TYPE: results now prefer a type the client cannot become. Stop investing in that query;
     redirect effort to queries where its type wins.
   - COLLATERAL FLAT: page is fine; demand or layout changed. Watch, do not rebuild.
6. **Winners:** name what they share (source type, intent, format). That is the site's strength; do more
   of it.

## Output
```
CORE UPDATE TRIAGE
Update (name + dashboard dates) | windows compared | pages | winners / losers / flat | net click change

THE PATTERN (2-3 sentences: what the losers share)

TOP WINNERS (up to 5: page, click change, common trait)

TOP LOSERS (up to 10)
  PAGE: [url]
  CLICKS: [before] -> [after] ([change])
  TOP LOST QUERY: [query]
  FIT: source-type [Y/P/N/U], task [Y/P/N], market [Y/P/N], format [Y/P/N/U]
  VERDICT: [FIXABLE FIT GAP / WRONG SOURCE TYPE / COLLATERAL FLAT]
  ACTION: [one shippable change, or "stop investing, redirect to X"]

DO THIS MONTH (top 3 by click recovery)
NOT CHECKED: technical issues, links, seasonality, tracking changes
```

## Rules
- Weight by absolute clicks, never percentages alone.
- Fewer than ~10 affected pages: could be query-level volatility; do not conclude "the site was hit".
- "Wait for the next update" is not an action; every loser gets a verdict.
- No recovery timelines. Core update recoveries usually surface at a later core update, if the fix
  addressed the real gap.
- Data overlapping the rollout itself is volatile: re-run after completion.
- Branded queries dominate: strip brand terms and re-run.
- All pages flat: say so; not every site is affected.
- Gradual decline with no update in the window: use `content-decay.md`.
- Write in the client's language (en, or es-CO for Colombian clients).
