---
name: deep-research
description: Multi-source deep research. Searches the web and the academic literature, synthesizes findings, and delivers cited reports with source attribution. Use when the user wants thorough research on any topic with evidence and citations.
origin: ECC
---

# Deep Research

> **Drift-prone skill.** MCP tool names, quotas, and result shapes change.
> Run `claude mcp list` and verify what is actually configured before
> promising coverage or quoting live source counts. Never claim a tool ran
> that is not in your tool list.

Produce thorough, cited research reports from multiple sources.

## When to Activate

- User asks to research any topic in depth
- Competitive analysis, technology evaluation, or market sizing
- Due diligence on companies, investors, or technologies
- Any question requiring synthesis from multiple sources
- User says "research", "deep dive", "investigate", or "what's the current state of"

## Tools

**Nothing here is required.** `WebSearch` and `WebFetch` are always present and
are enough to run this skill. Everything below is an upgrade, not a gate. If a
tool is absent, say so once and continue; never stall waiting for one.

### Always available
- **WebSearch** - the default search. US-only results.
- **WebFetch** - fetches a URL and answers a prompt against it. It summarises
  through a small model, so **it paraphrases and sometimes gets details wrong**.
  For any number, date, quote or citation that will be written down, re-fetch
  with `curl` and `grep` the raw text instead.
- **curl + pdftotext -layout** - the verification path. A verbatim quote comes
  from here, not from a search summary.
- **Jina Reader** - `curl https://r.jina.ai/<URL>` turns a page or PDF into
  markdown. No key, no account, 20 req/min. Use when `curl` gets a 403, a 502,
  or JavaScript-only HTML.

### Academic (installed 2026-10-09)
- **paper-search-mcp** - searches arXiv, PubMed, PMC, Europe PMC, bioRxiv,
  medRxiv, Semantic Scholar, Crossref, OpenAlex, CORE, dblp, and **downloads the
  PDF** via an open-access fallback chain. No API key. Prefer it over a web
  search whenever the target is a paper.
  **Never enable its Sci-Hub fallback.** Paywalled work goes through the user's
  institutional access, not around it.
  Install it as `uv tool install paper-search-mcp --with 'mcp<2'`. Version 0.1.4
  imports `mcp.server.fastmcp`, which mcp 2.x renamed, so a plain install builds
  an env that crashes on startup and shows up only as CONNECTION_CLOSED.
- **zotero-mcp** - reads the user's local Zotero library and the full text of
  PDFs already in it. Local mode, no key. Check here before searching the web:
  the paper may already be downloaded. The server starts and reports connected
  even with no Zotero installed; every query then fails. Confirm the local API
  answers (`curl 'http://localhost:23119/api/users/0/items?limit=1'`) before
  relying on it.
- **Crossref API** - `https://api.crossref.org/works/<DOI>` with a `mailto` in
  the User-Agent. The fastest way to confirm authors, year, volume, pages and
  ISBN. No key.

### Paywalls
No tool here crosses a paywall, free or paid. Springer, Elsevier, ACM and IEEE
go through the user's institutional access. When a source is paywalled, **give
the user the DOI and the exact title to pull manually** rather than substituting
a worse open source.

### Video and non-paper sources
- **yt-dlp** - downloads existing subtitles:
  `yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "es.*,en.*"`
- **whisper-cpp** - transcribes when there are no subtitles. Multilingual model,
  never the `.en` variants, which do not work for Spanish.
- Treat auto-generated subtitles as **weak evidence**: verify any verbatim quote
  against the audio before writing it down.

### Web, code and forum search (installed 2026-10-11, free tiers only)
- **exa** MCP - semantic web search plus code context search. Keyless; free credits.
- **tavily** MCP - general web search, 1,000 credits a month (OAuth login via `/mcp`).
- **firecrawl** MCP - search, scrape and parse to clean markdown. Keyless tier is rate
  limited; crawl and map need a key.
- **deepwiki** MCP - questions and docs about any public GitHub repo. Free, no key.
- **searxng** MCP (if running at `http://localhost:8888`) - self hosted meta search, no limits.
- **Hacker News** - no MCP needed: `curl 'https://hn.algolia.com/api/v1/search?query=<q>&tags=story'`
  (Algolia, public, no key). Threads: `https://hn.algolia.com/api/v1/items/<id>`.
- **GitHub** - `gh search repos|code|issues` and `gh api`.

**Which tool for which question:**

| The question is about | Start with | Why |
|---|---|---|
| A paper, citation, prior academic work | zotero, then paper-search | Already in your library, or real bibliographic records |
| "What exists / what is the current state" (tools, products, approaches) | exa | Searches by meaning, finds the good page even when your keywords are off |
| A plain factual web lookup, news, a price, a date | tavily | Fast keyword search with short extracted answers |
| A query you want with no quota at all, or many variations | searxng | Self hosted, no limits; only up while a session has it open |
| How a GitHub project or library works inside | deepwiki | Answers from the repo's code and docs, not from blog posts |
| Real usage of an API in code, or comparing projects (stars, activity) | `gh search code`, `gh api`, exa code search | Evidence from real repos |
| What practitioners think, launches, complaints | Hacker News via Algolia curl | Opinion from people who used it |
| Reading a page you found (docs, pricing, long article) | firecrawl, then Jina Reader or curl | Clean markdown; firecrawl also crawls a whole docs site |
| A library's current API for code you are writing | context7 (not this skill) | Version accurate docs |

Built in WebSearch stays the last search fallback; WebFetch paraphrases, so quote numbers only from curl or firecrawl.

**Fallback rule (never leave research undone):** when a tool errors, rate limits or runs out
of free credit, continue the same sub-question with the next tool in the search order,
write down which sub-question and which tool failed, and before delivering, rerun each
failed slice with a different tool (or a subagent using one). The Methodology section lists
every tool that failed and what replaced it.

### Not installed, and deliberately so
Brave Search (needs a card and bills past the free credit), Perplexity, Kagi (paid).
The local deep-research agents (gpt-researcher, STORM, open-deep-research and the rest)
duplicate what subagents already do here and bill their own LLM calls.

## Workflow

### Step 1: Understand the Goal

Ask 1-2 quick clarifying questions:
- "What's your goal - learning, making a decision, or writing something?"
- "Any specific angle or depth you want?"

If the user says "just research it" - skip ahead with reasonable defaults.

### Step 2: Plan the Research

Break the topic into 3-5 research sub-questions. Example:
- Topic: "Impact of AI on healthcare"
  - What are the main AI applications in healthcare today?
  - What clinical outcomes have been measured?
  - What are the regulatory challenges?
  - What companies are leading this space?
  - What's the market size and growth trajectory?

### Step 3: Execute Multi-Source Search

For EACH sub-question, search with whatever is configured. Order:

1. **zotero-mcp** - is it already in the library?
2. **paper-search-mcp** - if the target is a paper.
3. **exa**, then **tavily**, then **searxng**, then **WebSearch** - general web (fallback order).
4. **deepwiki** and `gh search` - how a project or library works, real code usage.
5. **Hacker News** (Algolia curl) - practitioner opinion and launches.
6. **firecrawl**, **Jina Reader** or **curl** - to actually read what you found.

**Search strategy:**
- Use 2-3 different keyword variations per sub-question
- Mix general and news-focused queries
- Aim for 15-30 unique sources total
- Prioritize: academic, official, reputable news > blogs > forums

### Step 4: Deep-Read Key Sources

For the most promising URLs, fetch full content:

```
curl -sL --max-time 60 -A 'Mozilla/5.0' '<url>'          # first choice
curl -sL 'https://r.jina.ai/<url>'                        # when curl is blocked
pdftotext -layout file.pdf - | grep -n -i -B2 -A6 '<term>'  # for PDFs
```

Read 3-5 key sources in full. Do not rely on search snippets, and never on a
`WebFetch` summary, for anything that will be quoted or cited.

### Step 5: Synthesize and Write Report

Structure the report:

```markdown
# [Topic]: Research Report
*Generated: [date] | Sources: [N] | Confidence: [High/Medium/Low]*

## Executive Summary
[3-5 sentence overview of key findings]

## 1. [First Major Theme]
[Findings with inline citations]
- Key point ([Source Name](url))
- Supporting data ([Source Name](url))

## 2. [Second Major Theme]
...

## 3. [Third Major Theme]
...

## Key Takeaways
- [Actionable insight 1]
- [Actionable insight 2]
- [Actionable insight 3]

## Sources
1. [Title](url) - [one-line summary]
2. ...

## Methodology
Searched [N] queries across web and news. Analyzed [M] sources.
Sub-questions investigated: [list]
```

### Step 6: Deliver

- **Short topics**: Post the full report in chat
- **Long reports**: Post the executive summary + key takeaways, save full report to a file

## Parallel Research with Subagents

For broad topics, use Claude Code's Task tool to parallelize:

```
Launch 3 research agents in parallel:
1. Agent 1: Research sub-questions 1-2
2. Agent 2: Research sub-questions 3-4
3. Agent 3: Research sub-question 5 + cross-cutting themes
```

Each agent searches, reads sources, and returns findings. The main session synthesizes into the final report.

## Quality Rules

0. **Verbatim or nothing.** A quotation must be copied from the raw source you
   opened, never reconstructed from a summary. If you did not open it, write
   "referencia localizada pero no leida" and say so in the report.
1. **Every claim needs a source.** No unsourced assertions.
2. **Cross-reference.** If only one source says it, flag it as unverified.
3. **Recency matters.** Prefer sources from the last 12 months.
4. **Acknowledge gaps.** If you couldn't find good info on a sub-question, say so.
5. **No hallucination.** If you don't know, say "insufficient data found."
6. **Separate fact from inference.** Label estimates, projections, and opinions clearly.

## Examples

```
"Research the current state of nuclear fusion energy"
"Deep dive into Rust vs Go for backend services in 2026"
"Research the best strategies for bootstrapping a SaaS business"
"What's happening with the US housing market right now?"
"Investigate the competitive landscape for AI code editors"
```
