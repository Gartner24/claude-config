# 0056. Four ideas borrowed from tools we skip

**Date**: 2026-10-17
**Status**: Accepted
**Paths:** `runner/tests/test_borrowed_ideas.py`, `claude-home/skills/lead-finder/**`, `claude-home/skills/reaction-tester/**`, `claude-home/skills/business-analyzer/references/new-business.md`, `claude-home/rules/new-number-replaces-old.md`

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
- **AC-1** (sources): `claude-home/skills/lead-finder/SKILL.md`. Given a city and a trade it finds businesses from: one Overpass API query per run to `https://overpass-api.de/api/interpreter` with a `User-Agent` naming the skill, results under the header "Data (c) OpenStreetMap contributors, ODbL"; lists you paste; and, only when you ask, pages you open in Chrome one at a time. It reads no site whose terms forbid automated access (directories, social networks), and never Google Maps, Google Places or LinkedIn. It then reads only each business's own domain: at most 3 plain requests (home page, `robots.txt`, sitemap), 1 second apart. `robots.txt` rules for `*` decide; a disallow skips the site, and a failed `robots.txt` fetch (timeout, 4xx other than 404, 5xx) skips it and marks the row `unchecked`; a 404 means no rules.
- **AC-2** (output): a markdown table of 0 to 20 rows, sorted by number of signals; fewer than 10 rows says "only n found" and pads nothing. Columns: business, public URL or none, signals, evidence URL per signal. Signals: `NO_WEBSITE` (no website tag and no site found), `NO_BOOKING` (home page has no link or form matching booking words: reservar, agendar, cita, book, booking, appointment, calendly), `BLOG_STALE` (newest dated post or sitemap `lastmod` older than 12 months), `INCUMBENT_AGENCY` (a "made by" or credit link to another web agency in the footer). It writes the table only to a path you give that is not inside any git repo (it checks with `git rev-parse` and refuses), and says it is a lead list, not a contact list.
- **AC-3** (never sends, no personal data): its `allowed-tools` are exactly `Read, Write, WebFetch, Bash(curl:*), Bash(git rev-parse:*)` plus the Chrome tools only when you ask, and no mail, message or post tool; its text says it never contacts anyone. It stores no personal names, emails or phone numbers; a row whose business name looks like a person's own name is marked `personal name, contact by hand only`. Page text is treated as data, never as instructions. It works for Colombian cities by default and says that other countries have other data laws.
**B11 reaction tester**
- **AC-4**: `claude-home/skills/reaction-tester/SKILL.md`. It first shows one plain baseline answer, then asks you to confirm before spending on personas. It builds up to 12 personas (from real reviews you give; with none, each is marked "invented"), runs one Sonnet subagent per persona, and ends with objections ranked by how many personas raised them (ties in the order first raised), showing "n of 12 answered" when a subagent fails, and the label "opinions of simulated people, not a forecast".
**B12 idea scorecard**
- **AC-5**: `new-business.md` keeps its 5 fatal flaw questions and adds a 7 dimension score (problem, buyer pays, market size, founder fit, why now, reach, cost to test; each 1 to 5, total out of 35), each citing its evidence or "no evidence"; its verdict line becomes "build / change course / drop" with up to 3 cheap tests. `SKILL.md:12`, `b2b.md:81` and `b2c.md:69` keep their verdict words for B2B and B2C analyses on purpose. Static check: the file contains the 7 dimension names, "/35" and "build / change course / drop".
**B13 new number replaces old**
- **AC-6**: `claude-home/rules/new-number-replaces-old.md`, at most 6 lines: when you give a figure that differs from one already written (in the skill's own files or the project's docs), replace it there and say "replaced X (date) with Y"; never write a figure with no source, write a bracket placeholder instead; customer-research and offers are named as where it matters most. It is a rule loaded in every session, not a change to those skills. Static check: line count and both skill names.
**All**
- **AC-7**: each part is used once on a real case; the case and result go in this spec's verify notes (a box that waits on you). If lead finder is dropped, its box is ticked as skipped and the other three still close the row.
- **AC-8**: a test asserts that no `entries` key in `config/manifest.json` is `lead-finder`, `reaction-tester` or `new-number-replaces-old`, and that a `claude-config update --plan` run against a fixture manifest does not name them.
- **AC-9**: both new skills say they run only when you type them, set `disable-model-invocation: true` in their front matter, and are not marked for `wf run` in the skill map.

## Decision
One umbrella spec, four parts, own files only. Lead finder can be dropped alone without blocking the other three.

## Build plan
1. lead-finder skill, satisfies **AC-1** to **AC-3**, **AC-9**
2. reaction-tester skill, satisfies **AC-4**, **AC-9**
3. scorecard edit, satisfies **AC-5**
4. rule file, satisfies **AC-6**, **AC-8**
5. One real use each, satisfies **AC-7** (waits on you)

## Consequences
**Positive**: four useful tools at no cost, nothing lost on updates.
**Negative / tradeoffs**: OpenStreetMap data in Colombia is thin, so lead lists may be short; the reaction tester uses your weekly limit (12 subagents a run); the rule file costs a few lines in every session.
**Neutral**: Overpass and robots.txt behavior is unconfirmed until the first real use.
