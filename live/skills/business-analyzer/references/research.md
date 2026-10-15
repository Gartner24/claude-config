# Research & Current Data

This skill is only as good as the facts behind it. Market sizes, prices, regulations, and economic conditions change and differ by country - analyzing from memory produces confident-sounding nonsense. Use **web search** (and any connected data/MCP tools) to ground every checkable claim. If search is unavailable, say so explicitly and mark all figures as unverified estimates.

## What to gather (only what the decision needs)

- **Market size & growth** for the *exact* segment, in the *exact* country/region. A figure for "global SaaS" is useless when the question is "POS software for cafés in Colombia."
- **Competitors & their current pricing** - real prices from their sites/plans, positioning, and who they target. Include indirect competitors and the status quo ("spreadsheet," "do nothing").
- **Demand signals** - search volume trends, communities, reviews, complaints about existing solutions, evidence people already pay for a worse option.
- **Regulatory / tax / formation facts** - only those that affect the decision (licensing, VAT/IVA, who can sell what, data/privacy rules).
- **Macro/country indicators** - when entering/expanding: GDP per capita, inflation, currency stability, internet/smartphone/card penetration, ease of doing business (see `country-context.md`).

## Sizing a market with real data (bottom-up first)

Top-down ("1% of a $10B market") is a fantasy. Build bottom-up, then cross-check:

1. **Count the buyers.** How many businesses/people in the target country fit the ICP? (Search official statistics, industry associations, census/registry data.)
2. **x realistic price** they'd pay per year.
3. **= SAM** (serviceable addressable market). Then estimate the slice you could *Obtain* (SOM) given your channels - usually a small single-digit %.
4. **Cross-check** against any published market-size report; if they diverge wildly, dig into why (different definitions, geographies, or vendor inflation) rather than averaging them.

Match the result to the user's ambition: a $2M/yr obtainable niche is a great solo business and a poor venture bet.

## Sourcing discipline

- **Prefer primary, recent sources:** government statistics offices, central banks, regulators, company filings, reputable industry bodies. Treat marketing blogs and vendor "TAM" claims with suspicion (they inflate).
- **Date-stamp everything.** "As of [date/source]." Data goes stale; a 2021 figure may mislead in the current year.
- **Label confidence:** hard fact (sourced) vs. estimate (your calculation) vs. assumption (unverified input). Never blur these.
- **Cross-check conflicts.** If two sources disagree, say so and explain which you trust and why - don't silently pick one.
- **Note gaps.** For small/local/niche markets, hard data often doesn't exist. Triangulate (proxy markets, analogous countries, unit-level estimates) and be explicit that it's triangulation.

## Include a short data section in the output

End data-driven analyses with:

```
## Data & sources
- [Figure] - [source], as of [date] - [hard fact / estimate / assumption], confidence: [high/med/low]
- ...
- Gaps / couldn't verify: [what you'd want but couldn't find]
```

This lets the user see exactly what the conclusion rests on and where it's soft.
