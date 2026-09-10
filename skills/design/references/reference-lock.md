# Reference sourcing - Mobbin, Refero, and the public galleries

> Research reference for the design pipeline. Compiled 2026-09-09 from primary
> sources; every tool, endpoint and browser-support figure was verified at that
> date and carries its URL inline. Items that could not be confirmed are marked
> UNVERIFIED - treat those as leads, not facts. Re-verify prices and model IDs
> before quoting them to a client.

# Research A: Design-Reference Sourcing for a `/design` Rebuild

Date of research: 2026-09-09. Every URL below was fetched (WebFetch or curl) unless
explicitly marked `UNVERIFIED`.

---

## 1. Mobbin MCP

### Verdict: an OFFICIAL, first-party, hosted MCP server exists. It is the real thing.

Launched 2026-05-13 (press release, verified via search result titles on
businesswire/morningstar/yahoo; the release headline is "Mobbin Launches MCP Server,
Giving AI Tools 621,500 Real App Screens to Reference").

| Fact | Value | Verified at |
|---|---|---|
| Endpoint | `https://api.mobbin.com/mcp` | https://github.com/mobbin/mobbin-mcp-server |
| Transport | Streamable HTTP | https://docs.mobbin.com/mcp/introduction |
| Auth | OAuth, browser sign-in, no API key | https://docs.mobbin.com/mcp/introduction |
| Plan gate | Pro, Team, Enterprise (paid) | https://docs.mobbin.com/mcp/introduction |
| Rate limit | 60 requests / 60 seconds per user | https://docs.mobbin.com/rate-limits.md |
| Local install | None. Nothing to clone or run. | https://github.com/mobbin/mobbin-mcp-server |
| Repo license | MIT (the repo is config/docs only, not server code) | same |

### Exact install command (verbatim from https://docs.mobbin.com/mcp/clients/claude-code)

```bash
claude mcp add mobbin --scope user --transport http https://api.mobbin.com/mcp
```

Then: start a session, run `/mcp`, select `mobbin`, choose Authenticate, sign in in the
browser window that opens.

Raw JSON form (verbatim from the repo README):

```json
{
  "mcpServers": {
    "mobbin": {
      "url": "https://api.mobbin.com/mcp"
    }
  }
}
```

Some clients need `"type": "streamableHttp"` stated explicitly (the README calls out Cline).

### Tools exposed (verified at https://docs.mobbin.com/mcp/features.md)

Exactly three:

| Tool | What it does |
|---|---|
| `search_screens` | Searches UI screens. |
| `search_flows` | Searches multi-step user flows such as onboarding and checkout. |
| `search_sections` | Searches website sections such as pricing pages and footers. |

Parameter schemas are NOT published in the docs. `UNVERIFIED`: exact parameter names.
The official Mobbin skill (see section 5) shows the call is driven by a natural-language
`query`, a `platform` value of `ios` or `web`, and a `limit` (default 5, up to ~15).

### What it returns

- Screen **images inline** in the tool response, as image blocks the model can actually
  look at. This is the key property: it is not a list of links, it is vision input.
  ("It returns screen images inline for AI consumption in its tool responses" -
  https://docs.mobbin.com/mcp/introduction)
- Metadata alongside each image: app name, Mobbin URL, platform.
- In clients supporting the MCP Apps spec (ChatGPT, Claude Desktop/Web, Codex App) it
  also renders an interactive gallery inline. Claude Code CLI is not on that list, so
  expect plain inline images there.

### There is also a REST API (Team/Enterprise only)

Verified at https://docs.mobbin.com/api/quickstart.md. Base `https://api.mobbin.com`,
Bearer key from Settings > API Keys, 60 req/60s per workspace.

```bash
curl -X POST https://api.mobbin.com/v1/screens/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "login screen with biometric authentication",
    "platform": "ios",
    "limit": 5
  }'
```

Returns image URLs, app names, and links back to Mobbin. Not useful for a Pro-tier user.

### Community / unofficial Mobbin MCPs

- https://github.com/pdcolandrea/mobbin-mcp - **ARCHIVED and deprecated.** The README
  now says "This repository is archived and no longer maintained" and points at the
  official server. It worked by reverse-engineering Mobbin's internal Supabase endpoints
  using a browser session cookie (`MOBBIN_AUTH_COOKIE`, persisted to
  `~/.mobbin-mcp/auth.json`). Do not use it.
- https://github.com/aos-engineer/mobbin-mcp and https://github.com/hassan0042/mobbin-mcp
  are byte-identical forks of the above (same description string). `UNVERIFIED`
  individually; they are the same archived cookie-scraping code.
- https://github.com/YonasValentin/design-inspiration-mcp-server - not a Mobbin client at
  all. It runs Google searches through the Serper API with `site:dribbble.com OR
  site:behance.net OR ...` filters. Returns search-result URLs, not curated screens. Needs
  a Serper key. Low value for this purpose.
- https://github.com/notsointresting/design-inspiration-mcp - claims 28 tools across
  Awwwards/Behance/Dribbble. README documents **no** access mechanism, no API keys, no
  auth. 2 stars. Treat as unproven; likely stubs. `UNVERIFIED` that its tools function.

### Does scraping Mobbin violate their ToS? YES, unambiguously.

Verbatim from https://mobbin.com/terms (Effective date: May 16, 2026):

> transfer to another person or aggregate, "mirror", cache, archive or re-host any
> materials or content retrieved from the Platform or the Services (including through the
> use of any scraper, robot, bot, spider, crawler or any other automated device or means)
> on any other website, server or platform without Mobbin's prior express written consent;

> unauthorised use of any scraper, robot, bot, spider, crawler or any other automated
> device or means to access, acquire, copy or monitor any portion of the Platform or any
> data or content found or accessed through the Platform

> You represent and warrant that you will not use any automated tools such as artificial
> intelligence or machine learning:
> to create derivative works of any materials, software or content contained on the Platform;
> to train, test, index, benchmark, or improve any generative AI, large language, or
> machine-learning tool or model, or similar technology; or
> for other commercial purposes,
> except as expressly permitted by these Terms of Service or the written consent of Mobbin.

There is a narrow crawler carve-out, conditional:

> If you operate a search engine, web crawler, bot, scraping tool, data mining tool, bulk
> downloading tool, wget utility, or similar data gathering or extraction tool, you may
> use the Platform, subject to the following additional conditions:
> you must use a descriptive user agent header;
> you must follow robots.txt at all times;
> your access must not adversely affect any aspect of the Platform's function; and
> you must make it clear how to contact you, either in your user agent string, or on your
> website if you have one.

And critically, the MCP itself carries an **explicit permission grant** that covers a
`/design` pipeline:

> Mobbin's API or MCP Services are provided for (i) your personal or internal business
> use, or (ii) integration into your own proprietary products or services ("Permitted
> Use"). You additionally warrant [...] that you will not:
> resell, sublicense or lease access to the API or MCP Services;
> create any service or product that is competitive to Mobbin's Platform or Services; or
> use any content retrieved via the API or MCP Services to create a standalone content
> repository, or otherwise use such content to build a service that substitutes for
> Mobbin's Platform or Services.

**Practical reading:** using the official MCP inside a personal `/design` command is
expressly Permitted Use. Caching its screenshots into a local reference library that
persists and substitutes for Mobbin is exactly what the last clause forbids. Design the
step to fetch fresh and not to hoard.

`https://mobbin.com/robots.txt` reads `User-Agent: * / Allow: /` with only `GPTBot`
disallowed. ClaudeBot is not blocked there. That does **not** grant scraping rights - the
ToS is the binding instrument and it requires "prior express written consent" independent
of robots.txt.

### Pricing

`https://mobbin.com/pricing` returns HTTP 403 to non-browser clients. Third-party
aggregators put Pro at roughly USD 40/seat/month billed annually. `UNVERIFIED` - treat
the number as approximate. What IS verified: MCP is gated to paid plans, and
`https://mobbin.com/mcp` states "Unlimited usage during beta but may require AI credits
in the future."

---

## 2. What Mobbin is and why it matters for a design pipeline

**Corpus.** 621,500+ screens and 142,200+ flows from shipped iOS, Android, and web
products; 200,000+ designers as users. Categories span fintech, e-commerce, health,
productivity, social, SaaS. The claimed differentiator is coverage of things you cannot
just go look at yourself: subscription-only products, region-locked finance apps, niche
apps. (Figures from the launch release; corpus figure corroborated on
https://mobbin.com/mcp.)

**Taxonomy.** Three axes, mirroring the three MCP tools:

- **Screens** - a single UI surface, tagged by app, platform, screen type.
- **Flows** - an ordered sequence of screens for one job: onboarding, checkout, KYC,
  cancellation, permission priming.
- **Sections** - web-page sections in isolation: pricing tables, footers, hero blocks.

The site itself additionally exposes patterns, elements, and UI copy as browse
dimensions, but the MCP surface is the three above.

**How a coding agent actually uses it.** Yes - the "show me 5 real onboarding flows
before designing one" framing is exactly right, and it is what both Mobbin's own skill
and Refero's skill implement. The mechanism that makes it worth anything is that
`search_screens` returns **images inline**, so the model literally sees the reference
rather than reading a description of it. The value is anti-averaging: an agent asked to
design a paywall from parametric memory produces the median paywall. An agent that has
just looked at 8 real shipped paywalls produces something with a specific point of view
it can cite.

Concrete uses that pay off:
- Before designing: pull 5-10 real examples of the exact screen type, extract what they
  share and where they diverge, pick a direction deliberately.
- Mid-design: settle a specific question ("where does the skip affordance go on a
  permission primer") with evidence instead of a guess.
- Reviewing: hold the generated screen next to real ones and name the drift.

**Realistic integration given auth constraints.** The blocker is not technical, it is
commercial: MCP requires a paid Mobbin plan and OAuth sign-in. So the `/design` step must
degrade gracefully. It cannot assume Mobbin. Design it as: try Mobbin, else try Refero,
else fall back to public galleries via the Chrome MCP. See section 6.

---

## 3. The rest of the real-UI reference corpus

All statuses probed 2026-09-09 with a desktop UA.

### Real-app / product-UI libraries (Mobbin's direct competitors)

| Name | URL | Free? | Programmatic access | Best for |
|---|---|---|---|---|
| **Refero** | https://refero.design | Free tier w/ limited results; Pro/Team/Lifetime paid | **Official MCP** at `https://api.refero.design/mcp` (paid), plus `llms.txt`, plus an official agent skill, plus a Figma plugin | The strongest Mobbin alternative and arguably the better agent citizen. Web + iOS screens, flows, and uniquely **styles** (extracted visual systems: tokens, type scale, spacing, surfaces). See section 4. |
| **ScreensDesign** | https://screensdesign.com | Not stated on homepage (`UNVERIFIED`) | No API/MCP found. `robots.txt` publishes an **explicit allow for ClaudeBot and user-directed assistants** while blocking training crawlers. Serves `/llms.txt` (HTTP 200). | iOS app teardowns with paywalls, price points, revenue estimates. ~2,634 apps from the top charts. Monetization-flavored. **Note: uisources.com now 301-redirects here** - UI Sources is gone/absorbed. |
| **Page Flows** | https://pageflows.com | Paid ("Plans & pricing" in nav) | No API. `robots.txt` allows crawl of content, blocks `/search` and query params. Ships an `image-sitemap.xml`. | Video recordings of real user flows, web and mobile. Best-in-class when the question is temporal ("what does the transition actually do"), which static screenshots cannot answer. |
| **Nicelydone** | https://nicelydone.club | Paid | No API/MCP/llms.txt found | 202,400+ screens from web apps (Linear, Notion, Stripe named on the homepage). Its own copy is explicitly agent-flavored. Strong for SaaS product UI specifically. |
| **SaaS Interface** | https://saasinterface.com | Has Pricing + Sign Up | No API/MCP/llms.txt found | SaaS app UI and UX examples. Narrow but deep in that one vertical. |
| **UI Sources** | https://uisources.com | - | - | **Defunct as an independent product.** Redirects to screensdesign.com. Do not wire it in. |

### Marketing-site / landing-page galleries

| Name | URL | Free? | Programmatic access | Best for |
|---|---|---|---|---|
| **Recent (formerly Godly)** | https://recent.design | Free | No API, no llms.txt (SPA soft-404). Scrapeable in principle. | **godly.website now 301-redirects to recent.design.** Rebranded and broadened: Design, Websites, OG Images, App Screenshots, App Icons, Resources, Tools, **Skills**, Jobs. Best for high-craft, award-adjacent web design, and it now runs a directory of design agent skills (see section 5). |
| **Land-book** | https://land-book.com | Freemium | **Blocked.** Cloudflare managed challenge; even `/robots.txt` returns the JS interstitial. No API. | Landing pages, huge and well-tagged by industry/style/type. But hostile to any headless access - needs a real browser session. |
| **Lapa Ninja** | https://www.lapa.ninja | Free | **RSS: `https://www.lapa.ninja/index.xml`**. `robots.txt` allows all, blocks `/api/`. | 7,300+ landing pages. The friendliest free landing-page corpus for automated access - RSS plus permissive robots. |
| **One Page Love** | https://onepagelove.com | Free (paid templates) | **RSS: `https://onepagelove.com/feed`** (WordPress) | Single-page sites. Good for tight, focused marketing pages. |
| **Curated** | https://curated.design | Freemium (some sections locked) | **RSS: `/rss.xml`**, plus `sitemap-index.xml` and `sitemap-content.xml`. `robots.txt` allows `/api/sections/` specifically because "the only image a locked section page has is served from here." | Live-site web design, organized **by section** (hero, pricing, footer). The section-level indexing is what makes it useful to an agent - it maps onto the same axis as Mobbin's `search_sections`. |
| **Httpster** | https://httpster.net | Free | No RSS found, no API | Deliberately non-corporate, trend-forward web design. Good antidote when everything else is converging on the same SaaS look. |
| **Minimal Gallery** | https://minimal.gallery | Free + paid templates | Weekly digest newsletter; no RSS found | Minimal/typographic web design. Narrow lens, high signal for restrained direction. |
| **Dark Mode Design** | https://darkmodedesign.com | Free | No RSS/API found | The one gallery organized around dark UI. Useful precisely because dark mode is where agent-generated design most often goes generic. |
| **siteInspire** | https://siteinspire.com | Free w/ paid tier | **Blocked.** Returned HTTP 429 "Vercel Security Checkpoint" on a plain request. | Long-running, tightly curated web design, excellent style/type/subject filters. Needs a real browser. |
| **Awwwards** | https://www.awwwards.com | Free to browse | No public API (searched; none found). `robots.txt` blocks `/gallery/`, `/search-websites`, `/inspiration/search`, `/websites/?`, `/directory/search/` - i.e. **every search and listing path is disallowed to crawlers**, only individual entries are open. | Award-winning, motion-heavy, experimental web. Best for ambition and craft ceiling. Worst for automation - the crawlable surface excludes exactly the browse paths an agent wants. |
| **Collect UI** | https://collectui.com | Free | No RSS/API found | Daily UI-challenge output. **Caveat: this is Dribbble-sourced concept work, not shipped product.** It is aspirational visual language, not evidence of what works. Rank it below every real-app source. |

### Design-system galleries (all free, all public docs, all HTTP 200 verified)

These are a different and complementary thing: not "what does a nice screen look like"
but "what are the actual rules, tokens, and component contracts of a system that ships at
scale." No auth, no rate limits, fetchable as plain docs, and stable enough to cite.

| System | URL | Best for |
|---|---|---|
| Vercel Geist | https://vercel.com/geist/introduction | The current reference for restrained developer-tool aesthetics; tokens and components documented together |
| Radix Themes | https://www.radix-ui.com/themes/docs/overview/getting-started | Color scales, semantic token roles, and accessible primitives you can actually install |
| GitHub Primer | https://primer.style | Mature system with explicit rationale; strong on density and information hierarchy |
| IBM Carbon | https://carbondesignsystem.com | Data-dense enterprise UI, grid discipline, thorough a11y guidance |
| Adobe Spectrum | https://spectrum.adobe.com | The most rigorous public writing on component states, sizing, and platform scaling |
| Atlassian Design | https://atlassian.design | Strong content/UX-writing guidance alongside components |
| Shopify Polaris | https://polaris.shopify.com (301 -> https://shopify.dev/docs/api/polaris) | Commerce/admin patterns and exemplary UX-writing rules |
| Stripe | https://docs.stripe.com/stripe-apps/style | Stripe has no open general design system; the Stripe Apps style guide is the closest public artifact. For the famous marketing craft, use https://stripe.com/blog and the Refero/Mobbin entries for stripe.com. |
| Linear | https://linear.app/docs | **No public design system.** Linear publishes product docs, not tokens. Treat Linear as a *reference to look at* (via Refero/Mobbin/Nicelydone), not a system to read. |

---

## 4. Is there any MCP server for design references at all?

Yes - two credible first-party ones, and a thin layer of low-quality community wrappers.

### Tier 1: first-party, real corpora, images inline

**Mobbin MCP** - covered in section 1.

**Refero MCP** - `https://api.refero.design/mcp`. This was the biggest find of the
research and it is a genuine peer to Mobbin, not an also-ran.

- Verified at https://doc.refero.design/mcp/getting-started.md and
  https://doc.refero.design/mcp/tools.md
- Install (verbatim):
  ```bash
  claude mcp add --transport http refero https://api.refero.design/mcp --header "Authorization: Bearer <token>"
  ```
  Omit `--header` if using OAuth and follow the sign-in flow. The bundled skill documents
  the simpler `claude mcp add --transport http refero https://api.refero.design/mcp`.
- Auth: OAuth or Bearer token. Requires a paid plan (Pro, Team, or **Lifetime** - a
  one-time purchase, which matters for a personal tool you do not want a subscription for).
- Ten tools (verified): `refero_search_site`, `refero_search_app`, `refero_search_styles`,
  `refero_get_style`, `refero_search_screens`, `refero_get_screen`,
  `refero_get_similar_screens`, `refero_get_screen_image`, `refero_search_flows`,
  `refero_get_flow`.
- Returns markdown **or** JSON (`response_format: "md" | "json"`), with
  `thumbnail_url` / `preview_url` per record, and `refero_get_screen_image` returns raw
  image content at `thumbnail` or `full` size.
- The differentiator vs Mobbin is **styles**: a style is a semantic design system
  extracted from a real page - visual thesis, tokens, typography, layout, section rhythm,
  spacing, elevation, surfaces, components, imagery treatment, implementation notes, and
  explicit do/don't rules. That is directly consumable by a coding agent in a way a
  screenshot is not. Documented limitation: styles currently cover web marketing/product
  pages only, not in-app dashboards or iOS screens.
- Refero publishes `https://refero.design/llms.txt` and
  `https://doc.refero.design/llms.txt` - machine-readable indexes written for agents. It
  is the most agent-native vendor in this entire space.
- Caveat: `https://styles.refero.design/robots.txt` **disallows ClaudeBot,
  anthropic-ai, and Claude-Web**. Refero wants agents on the MCP, not on the site. Do not
  browse Refero with the Chrome MCP as a workaround.

### Tier 2: generic URL screenshot MCPs

Several exist and work; they capture arbitrary public URLs. Verified example:

- https://github.com/sethbang/mcp-screenshot-server (published to npm as
  `universal-screenshot-mcp`, Apache-2.0, ~31 stars, active). `npm install -g
  universal-screenshot-mcp` or `npx universal-screenshot-mcp`. Tools: `take_screenshot`
  (url, width, height, fullPage, selector, waitForSelector, waitForTimeout, outputPath)
  and `take_system_screenshot`. Puppeteer-based, Node >= 18. **Important limitation:
  screenshots are saved to disk (`~/Documents/screenshots` by default), not returned
  inline as base64** - so the agent must then Read the file.
- Hosted commercial equivalents exist (ScreenshotOne, ScreenshotEngine, ScreenshotRun,
  Apify's MCP Screenshot). All require an account/API key. `UNVERIFIED` in detail -
  https://mcpservers.org/servers/screenshotone/mcp returned HTTP 403 to fetch.

For this user, all of these are **redundant**: claude-in-chrome already navigates and
screenshots any URL, with the added and decisive advantage of carrying the user's own
logged-in session.

### Tier 3: not worth wiring

- Awwwards MCP: none exists. Searched; nothing first-party or credible.
- Dribbble MCP / Behance MCP: only the Serper-search wrapper
  (https://github.com/YonasValentin/design-inspiration-mcp-server) and the unproven
  28-tool repo. Neither returns curated real-product UI.
- Figma Community MCP: the official Figma MCP (which this user has) reads and writes
  Figma files and design systems. It is not a Community-file discovery/browse surface.
  `UNVERIFIED` that any Community-browsing MCP exists.

### The concrete answer: least-friction path for THIS user today

Checked this machine: `~/.claude.json` has exactly **`magic`** globally (currently failing
auth) and **`21st`** scoped to one project. Plus the Claude-managed connectors: Figma,
claude-in-chrome, context7, claude-mem. **Neither Mobbin nor Refero is installed.** No
`refero-design` or `mobbin-search` skill in `~/.claude/skills/`.

So, ranked for today:

**(c) Chrome MCP against public galleries - available right now, zero setup, zero cost.**
`mcp__claude-in-chrome__navigate` to a gallery URL, then `computer` to screenshot. This
works this second. It costs one round-trip per reference and the agent must pick URLs
itself, so quality depends on the gallery's browse UX. Best targets are the ones that are
free, permissive, and section-indexed: Curated, Lapa Ninja, One Page Love, Recent,
ScreensDesign (which explicitly allows assistants in robots.txt). Avoid Land-book and
siteInspire in headless contexts - both fight back - though Chrome MCP with a real
profile handles them fine. Avoid Refero's site (robots blocks ClaudeBot).

**(a) An official MCP - strictly better once paid, and it is a one-command install.**
Mobbin: `claude mcp add mobbin --scope user --transport http https://api.mobbin.com/mcp`.
Refero: `claude mcp add --transport http refero https://api.refero.design/mcp`. Either
returns 5-10 curated, on-topic reference images in a **single** tool call, with app names
and URLs attached, having done the retrieval and ranking. That is a categorical
improvement over the agent guessing at gallery URLs. If only one: **Mobbin for breadth of
real shipped app screens and flows; Refero if you want extracted design *systems* and a
Lifetime license instead of a subscription.**

**(b) Driving Mobbin through Chrome MCP with the user's logged-in session - do not do
this.** It is the worst of the three. Technically it would work with a logged-in profile,
but: it is many round-trips per reference; it breaks on any UI change; and it is squarely
the "automated device or means to access, acquire, copy or monitor any portion of the
Platform" that the ToS prohibits, while the sanctioned MCP path costs one command and the
same subscription. There is no scenario where (b) beats (a) for a Mobbin subscriber, and
for a non-subscriber it is a ToS violation to get content they have not paid for.

---

## 5. Prior art on reference-first agent design workflows

This is a real, converged pattern with two production implementations, both first-party
from the reference vendors, both open source.

### Refero Skill - the most complete version

https://github.com/referodesign/refero_skill (default branch is `master`, not `main`).
Install: `npx skills add https://github.com/referodesign/refero_skill --skill refero-design`.
Ships `skills/refero-design/SKILL.md` plus `references/`: `anti-ai-slop.md`, `color.md`,
`copywriting.md`, `craft-details.md`, `example-workflow.md`, `icons.md`, `mcp-tools.md`,
`visual-workflow.md`. Also ships plugin manifests for Claude, Codex, Cursor, and Gemini.

Its non-negotiables, verbatim from SKILL.md, are the best statement of the pattern I found:

> - **Research before design work.** Every design must be grounded in references before
>   implementation. Do not rely on the model's generic design taste.
> - **Do not copy one reference.** Study several strong references and synthesize a new
>   direction for the user's product.
> - **Do not average references into a safe middle.** When references conflict, choose one
>   dominant direction and preserve its sharp traits. Secondary references may add narrow
>   details only.
> - **Do not change token meanings.** If a reference says a color, font, radius, shadow,
>   gradient, or component is for a specific role, use it only for that role or omit it.
> - **Research output must be specific.** Name the references, describe concrete choices,
>   and explain what will be adapted.
> - **No design from vibe memory.** Every major visual, layout, content, or interaction
>   decision must trace to Refero research, the user's brief, or a craft reference.
> - **Synthesize before implementation.** Turn research into a concept, token direction,
>   and concrete decision ledger before drawing or coding.
> - **A brief is not a build target.** Before implementation, lock either a user-provided
>   visual source, an existing product/design-system target, a selected generated mockup,
>   or an explicit reference-locked direction approved for direct build.
> - **Validate after building visual work.** Compare the rendered implementation against
>   the locked target/reference before handoff. Fix actionable design drift instead of
>   treating research as sufficient.

Its five-stage shape: Discovery (a short structured brief) -> Styles first -> Screens and
flows when needed -> Synthesis (pick ONE primary, borrow 1-2 narrow details, write a
**reference lock** / **decision ledger**) -> Implementation, then validate the render
against the lock.

Its research loop, verbatim:

> 1. Search 3-5 different visual angles.
> 2. Include one broad aesthetic query.
> 3. Include one domain/category query.
> 4. Include one known-brand or strong-product query when relevant.
> 5. Retrieve 3-4 strong styles with `refero_get_style`; full styles are large, so split
>    larger research into multiple batches.
> 6. Compare what each style contributes.
> 7. Choose one primary foundation and borrow 1-2 specific details from other styles.
> 8. Lock the primary reference's signature traits before implementation.

Notably it also has an opinion on turf: it tells the agent not to run generic
frontend/product-design skills as a parallel authority, because "generic design skills
tend to pull work back toward generic AI design." Relevant if `/design` currently chains
`ui-ux-pro-max` + `frontend-design` + `impeccable`.

### Mobbin Skill - the leaner version

https://github.com/mobbin/skills (MIT). Install: `npx skills add mobbin/skills`, or clone
and `cp -r skills/skills/* ~/.claude/skills/`. One skill, `mobbin-search`.

Its distinctive moves:
- **Trigger aggressively.** "Trigger aggressively for any design-related question - even
  if screenshots aren't explicitly requested."
- **Announce, then act without waiting.** State the plan tersely in one line, then call
  `search_screens` immediately without awaiting approval. This matters - a research gate
  that asks permission every time gets disabled by the user within a week.
- **Two response modes.** Mode A: direct answer from 1-3 screens for a concrete question.
  Mode B: build an **evidence board** - a self-contained HTML file, no frameworks, written
  to `./.mobbin/<slug>-<YYYYMMDD-HHMM>.html`, visuals dominant, every screen linked back
  to Mobbin with the app name shown.
- **Ground every observation in what is actually visible** - specific copy, spacing,
  colors - and avoid generic UX advice.
- Default 5 results, up to ~15 when variety is the point.

### Third-party ecosystem

https://recent.design/skills is a live directory of 13 "Interface" design agent skills
(anthropics/canvas-design, pbakaus/quieter, pbakaus/distill, pbakaus/critique,
pbakaus/polish, vercel-labs/web-design-guidelines, emilkowalski/prototype,
ibelick/ui-skills, emilkowalski/emil-design-eng, jakubkrehel/make-interfaces-feel-better,
raphaelsalaja/userinterface-wiki, jakubkrehel/oklch-skill,
arvindrk/extract-design-system) plus Research and Development categories. Worth noting:
**none of those 13 is reference-first.** They are craft, critique, and polish skills that
operate on what the model already produced. The only two skills anywhere that mandate
looking at real product UI *before* generating are Mobbin's and Refero's - the two written
by companies that own a corpus.

### What the good version looks like

Distilled from both:

1. **Mandatory, not optional.** "Research before design work" as a hard gate, with an
   explicit statement that model taste alone is not acceptable input.
2. **Cheap enough to always run.** One tool call, 5-10 images, announce-and-proceed rather
   than ask-permission. A gate with friction gets skipped.
3. **Several references, never one.** Copying one is plagiarism; averaging many is the
   generic mush the whole exercise exists to prevent.
4. **Pick a primary and preserve its sharp traits.** Secondary references contribute
   narrow details only. This is the single most valuable rule in either skill.
5. **Write the lock down before building.** A reference lock / decision ledger naming the
   sources and the specific adopted decisions. It makes the design auditable and gives the
   final validation step something to check against.
6. **Preserve token roles.** If the reference uses a color for one role, do not repurpose it.
7. **Cite specifically.** Name the app, quote the copy, give the URL. "Inspired by modern
   fintech apps" is worthless; "Revolut's KYC step 2 puts the skip as a text link below
   the fold" is a decision.
8. **Validate the render against the lock at the end**, and fix drift.
9. **Emit a durable artifact.** Mobbin's HTML evidence board is a good pattern - the
   research survives the conversation and the user can look at it.

---

## Recommendation for /design

### Where it goes

A new **Step 0: Reference Lock**, before the existing "lock direction" step. It runs
before `design-dna` / `ui-ux-pro-max`, and it feeds them. Everything downstream in the
current pipeline (magic MCP sourcing, frontend-design + impeccable assembly, motion,
audit) stays as it is - this step only changes what the direction is *grounded in*.

### What the step tells the agent to do

```
STEP 0 - REFERENCE LOCK (mandatory, runs before any direction is chosen)

Never design a screen type from model memory. Look at real shipped UI first.

0a. BRIEF (one line, no interrogation)
    Designing [WHAT] for [WHO] on [PLATFORM]. Goal: [GOAL]. Tone: [TONE].
    Screen types: [onboarding | pricing | dashboard | paywall | settings | ...].
    Ask only for what would materially change the result. Otherwise assume and proceed.

0b. RESEARCH - announce in one line, then act. Do not wait for approval.
    Run the highest-tier source available (see fallback ladder below).
    Issue 3-5 queries across different angles:
      - one broad aesthetic query
      - one domain/category query
      - one named-product query when a relevant one exists
    Collect 6-10 real references. Look at every image. Do not skim URLs.

0c. SYNTHESIS - write the lock to ./.design/reference-lock-<slug>-<YYYYMMDD-HHMM>.md
    - Sources: app/site name + URL for every reference used.
    - Primary: ONE reference is the foundation. Name its signature traits and keep them
      sharp. Do not average.
    - Borrowed: at most 2 narrow details from secondary references, each attributed.
    - Decision ledger: type scale, color roles, spacing rhythm, surface/elevation
      treatment, component feel, imagery role. Each line traces to a source or to the
      user's brief. Preserve token ROLES from the source - never repurpose a color.
    - Rejected: one line on the direction NOT taken and why. Prevents silent averaging.

0d. GATE
    If the lock cannot cite at least 3 real references with URLs, say so plainly and
    ask the user for a reference (a screenshot, a URL, a product name). Do not proceed
    on vibes and do not pretend the research happened.

0e. VALIDATE (at the end of the pipeline, folded into the existing step-5 audit)
    Screenshot the built UI. Put it next to the primary reference. Name the drift.
    Fix it. Report what was checked.
```

### Fallback ladder for 0b - try in order, stop at the first that works

1. **Mobbin MCP** if `search_screens` / `search_flows` / `search_sections` are available.
   Best breadth of real shipped app screens and flows; images come back inline.
   Use `search_flows` whenever the task has a before/after sequence.
2. **Refero MCP** if `refero_search_styles` etc. are available. Prefer it over Mobbin when
   the task is *visual direction for a web/marketing surface*, because
   `refero_get_style` returns an extracted design system - tokens, type scale, spacing,
   surfaces, do/don't rules - which fills the decision ledger directly instead of making
   the agent infer it from a picture.
3. **A user-supplied reference** - screenshot, URL, or product name. If the user pointed at
   something, that IS the primary; hand it to `design-dna` and skip discovery.
4. **Chrome MCP against public galleries.** `mcp__claude-in-chrome__navigate` +
   `computer` to screenshot. Pick by task:
   - web marketing / landing: **Curated** (https://curated.design, section-indexed:
     hero, pricing, footer - matches how the brief is phrased),
     **Lapa Ninja** (https://www.lapa.ninja, 7,300+, permissive robots + RSS),
     **Recent** (https://recent.design, high-craft)
   - iOS app screens and paywalls: **ScreensDesign** (https://screensdesign.com -
     its robots.txt explicitly welcomes user-directed assistants)
   - SaaS/web-app product UI: **Nicelydone** (https://nicelydone.club),
     **SaaS Interface** (https://saasinterface.com)
   - dark UI: **Dark Mode Design** (https://darkmodedesign.com)
   - flows over time: **Page Flows** (https://pageflows.com)
   With a real logged-in Chrome profile, Land-book and siteInspire also work; do not
   attempt them headless. **Never** point the Chrome MCP at Mobbin (ToS: no automated
   access) or at Refero's site (robots.txt disallows ClaudeBot).
5. **Design-system docs** - free, no auth, fetch as plain text and cite. Vercel Geist,
   Radix Themes, Primer, Carbon, Spectrum, Atlassian, Polaris. These answer "what are the
   rules" rather than "what does it look like," so they complement rather than replace a
   visual reference. Good enough alone for an admin/dashboard surface.
6. **Explicit degradation.** If none of the above produced 3 citable references, say so
   in one line and ask for a reference. Do not silently fall through to model taste - that
   failure mode is exactly what this step exists to prevent.

### What needs installing

Nothing is required - rung 4 onward works today with the Chrome MCP the user already has.

To get rungs 1-2, one command each, plus a paid plan:

```bash
# Mobbin - requires Pro/Team/Enterprise. Then: /mcp -> mobbin -> Authenticate
claude mcp add mobbin --scope user --transport http https://api.mobbin.com/mcp

# Refero - requires Pro/Team/Lifetime. OAuth or Bearer token.
claude mcp add --transport http refero https://api.refero.design/mcp
```

Optional, to borrow rather than rewrite the methodology:

```bash
npx skills add mobbin/skills                                                   # mobbin-search
npx skills add https://github.com/referodesign/refero_skill --skill refero-design
```

Reading `refero-design`'s `references/anti-ai-slop.md` before writing Step 0 is worth the
five minutes even if you never install it.

### Two design notes worth honoring

- **Keep it one call and no permission prompt.** Mobbin's skill is right that a research
  gate which asks approval every time gets turned off. Announce in one line, then act.
- **Do not build a local reference cache.** Mobbin's ToS specifically prohibits using MCP
  content "to create a standalone content repository." Write the *lock* (names, URLs,
  decisions) to disk. Do not hoard the screenshots.

### Compliance summary

| Path | Status |
|---|---|
| Mobbin MCP inside `/design` | Expressly Permitted Use: "personal or internal business use, or integration into your own proprietary products or services" |
| Caching Mobbin screenshots into a persistent local library | Prohibited - "standalone content repository" clause |
| Scraping mobbin.com (incl. via Chrome MCP) | Prohibited without prior express written consent |
| Chrome MCP on Refero's website | Disallowed by robots.txt (ClaudeBot, anthropic-ai, Claude-Web) |
| Chrome MCP on ScreensDesign | Explicitly welcomed in robots.txt |
| Chrome MCP on Curated / Lapa Ninja / One Page Love / Recent | Permissive robots.txt; RSS available on the first three |
| Crawling Awwwards search/browse paths | Disallowed by robots.txt; individual entry pages are open |
