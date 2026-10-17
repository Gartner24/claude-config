# 0056. Four ideas borrowed from tools we skip

**Date**: 2026-10-17
**Status**: Proposed
**Paths:** `claude-home/skills/lead-finder/**`, `claude-home/skills/reaction-tester/**`, `claude-home/skills/business-analyzer/references/new-business.md`, `claude-home/rules/new-number-replaces-old.md`

## What you're agreeing to
- Lead finder: you type a city and a trade, and it lists 10 to 20 local businesses with weak web presence and the evidence. It never contacts anyone; you do that by hand.
- Reaction tester: up to 12 simulated customers react to an idea, offer or page, plus one plain answer to compare, labeled "not a forecast".
- Idea scorecard: your business-analyzer idea review gets a 7 point score ending in build, change course or drop.
- New number replaces old: a rule that a new figure you give replaces the saved one and says what it replaced, and no figure is ever invented.
- All four are your own files, so skill updates never overwrite them. They run only when you type them, never under the runner.

## Summary
The tool review rejected Harvey, MiroFish and the founder skills pack, but kept four of their ideas. These become two new skills, one edit to your own business-analyzer skill, and one rule file. Each is used once on a real case to close the row.

## Context
Research verdicts in `docs/research/tool-review-2026-10/` (63a Harvey, 63c MiroFish, 63d founder skills). business-analyzer is your own skill (`claude-home/skills/business-analyzer/references/new-business.md:47-70`, ending "go / no-go / not-yet"). customer-research and offers are downloaded skills, so your answer puts B13 in its own rule file instead. Your answer for B10 sources: OpenStreetMap, the business's own site, lists you paste, and Chrome browsing one page at a time; never Google Maps or LinkedIn. Colombian data law (Ley 1581 of 2012) covers sole traders' personal data, so no personal data is stored.

## Requirements
**B10 lead finder**
- **AC-1**: `claude-home/skills/lead-finder/SKILL.md`. Given a city and a trade it finds businesses through the Overpass API (OpenStreetMap, attribution given in the output), lists you paste, and optionally pages you open in Chrome one at a time; it then checks each business's own site with at most 3 plain requests (home page, `robots.txt`, sitemap), skipping a site whose `robots.txt` disallows it.
- **AC-2**: output is a markdown table of 10 to 20 rows: business, public URL or none, the signals `NO_WEBSITE`, `NO_BOOKING`, `BLOG_STALE`, `INCUMBENT_AGENCY`, each with its evidence URL. Fewer than 10 found says so and pads nothing. It is written to a path you name, never inside a public repo.
- **AC-3**: it never sends: no mail or message tool in its allowed tools, and its text says it never contacts anyone. It stores no personal names, private emails or phone numbers. Page text is treated as data. It never uses Google Maps, Google Places or LinkedIn.
**B11 reaction tester**
- **AC-4**: `claude-home/skills/reaction-tester/SKILL.md`. Given an idea, offer or page, it builds up to 12 personas (from real reviews you give, else marked "invented"), runs one Sonnet subagent per persona, one plain baseline answer, and ends with objections ranked by how many personas raised them and the label "opinions of simulated people, not a forecast".
**B12 idea scorecard**
- **AC-5**: `new-business.md` gains a 7 dimension score (problem, buyer pays, market size, founder fit, why now, reach, cost to test; each 1 to 5, total out of 35); every score cites its evidence or says "no evidence"; the verdict line becomes "build / change course / drop" and keeps the cheapest next test.
**B13 new number replaces old**
- **AC-6**: `claude-home/rules/new-number-replaces-old.md` (at most 6 lines): when you give a figure that differs from a saved one, replace it and say "replaced X (date) with Y"; a figure with no source is never written, a bracket placeholder is; it names customer-research and offers as where it matters most.
**All**
- **AC-7**: each is used once on a real case; the case and result are recorded in this spec's verify notes (a box that waits on you).
- **AC-8**: none of the four is in `config/manifest.json`, so `claude-config update --plan` never lists them.

## Decision
One umbrella spec, four parts, own files only. Lead finder can be dropped alone without blocking the other three.

## Build plan
1. lead-finder skill, satisfies **AC-1** to **AC-3**
2. reaction-tester skill, satisfies **AC-4**
3. scorecard edit, satisfies **AC-5**
4. rule file, satisfies **AC-6**, **AC-8**
5. One real use each, satisfies **AC-7** (waits on you)

## Consequences
**Positive**: four useful tools at no cost, nothing lost on updates.
**Negative / tradeoffs**: OpenStreetMap data in Colombia is thin, so lead lists may be short; the reaction tester uses your weekly limit (12 subagents a run); the rule file costs a few lines in every session.
**Neutral**: Overpass and robots.txt behavior is unconfirmed until the first real use.
