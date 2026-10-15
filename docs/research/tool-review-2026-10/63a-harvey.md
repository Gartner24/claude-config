# Harvey (ethanplusai/harvey) - research report, 2026-10-15

Verdict: REJECT as a way to run on the Claude subscription. If the user still wants to look at it, ADAPT the ideas (signals, profiler) or try in a throwaway VM with a separate mailbox. Do not install on the main machine.

## Sources read
- README.md (41 KB), CLAUDE.md (20 KB), pyproject.toml, Dockerfile, harvey/brain.py (claude call), harvey/integrations/quota.py, harvey/dashboard.py (endpoints), harvey/cli.py (install), grep of all URLs in harvey/*.py. Clone: /tmp/claude-1000/-home-santiago--claude/70f90533-2ef9-4556-bf7a-d2d3d12aed15/scratchpad/clones/harvey (nothing run).
- ~/Downloads/guia-harvey.pdf (NodeStudio guide, Spanish, 3 pages).
- https://localleadhub.com/harvey-ai (via Jina Reader; firecrawl was rate limited).
- Anthropic: https://code.claude.com/docs/en/legal-and-compliance and https://www.anthropic.com/legal/consumer-terms (via Jina Reader).

## What it does end to end
Python loop (`harvey run`), wakes every 15 min: handle replies > send > write campaigns > prospect > idle analytics. Stages: DISCOVER (OpenStreetMap free; DataForSEO/Serper paid), PROFILE (3 plain HTTP requests per site, regex: incumbent agency in footer, ad pixels, no schema, stale blog, no booking, NO_WEBSITE), ENRICH (names from team pages), VERIFY (email pattern + one candidate verified by Reoon/ZeroBounce/Hunter). Five agents (scout, writer, sender, handler, analyst) driven by editable Markdown in skills/ and prompts/. Writer makes 3-email sequences (<75, <75, <40 words). Outbox approval by default (dashboard localhost:5555, keys A/R/J/K). Pre-send gate is deterministic code. Handler classifies replies, honors opt-outs by keyword, bounce kill switch. SQLite data/harvey.db. 23 "signals", none collected until the user confirms. `harvey export` gives a CSV so it can be used list-only.
README quote: "Harvey finds businesses worth selling to, learns something specific about each one, writes cold email that references it, sends it, reads the replies, and works the conversation toward a meeting."

## Claude subscription use and Anthropic terms
Mechanism (brain.py): shells out `claude -p <prompt> --output-format json --tools "" --strict-mcp-config [--model]` as a subprocess, using the user's logged-in Pro/Max session. Tools are disabled (good against prompt injection from scraped pages and replies). CLAUDE.md still says `--dangerously-skip-permissions`; the code does not use it (docs stale).
Extra: quota.py reads the Claude Code OAuth token from ~/.claude/.credentials.json or the macOS keychain and calls the undocumented `https://api.anthropic.com/api/oauth/usage` with it, to throttle itself.
Terms:
- Consumer Terms, 3.7 verbatim: "Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it, to access the Services through automated or non-human means, whether through a bot, script, or otherwise."
- Claude Code legal page verbatim: "Developers building products or services that interact with Claude's capabilities, including those using the Agent SDK, should use API key authentication through Claude Console or a supported cloud provider." and "Advertised usage limits for Pro and Max plans assume ordinary, individual usage of Claude Code and the Agent SDK." and "OAuth authentication ... is designed to support ordinary use of Claude Code and other native Anthropic applications." and "Anthropic reserves the right to take measures to enforce these restrictions and may do so without prior notice."
- Reading: an unattended 24/7 loop that calls `claude -p` for a sales automation and pulls the OAuth token for a side API is not "ordinary, individual usage"; it is a bot/script on subscription credentials. Not explicitly allowed. Risk: account limits or ban (the user's whole Claude setup). Secondary sources (The Register Feb 2026, a GitHub issue on multica) read it the same way but are not primary and conflict on details; the primary text above is what to rely on. Not legal advice; the wf runner the user already runs has the same grey area, so this is a reason to be consistent about it, not a license.
- README itself hedges: "Harvey runs locally with your own login. Check the terms and usage limits of the provider you choose."

## Data sent where
- Claude (Anthropic): scraped business data, prospect names/emails, reply text, product knowledge, via the CLI.
- Gmail API / Microsoft Graph / SMTP+IMAP: mailbox OAuth tokens; Harvey reads the inbox (scope gmail.modify) and sends.
- Verifiers: Reoon, ZeroBounce, Hunter get every candidate email address.
- Discovery: Nominatim, Overpass mirrors, DataForSEO, Serper get queries/cities.
- Cloudflare API (optional crawl), LinkedIn login (optional, off, ToS violation).
- Optional Precleared (precleared.dev, third party): receives recipient address, sender country, address source and product description. Issues #13 (open) proposes an opt-in "Tellwing" handoff.
- No telemetry endpoint found in harvey/*.py URL grep. Dashboard has a /api/feedback endpoint (not inspected deeply; local).
- Everything else local: data/harvey.db, .env, harvey.yaml.

## Credentials needed
Claude login (+ OAuth token read), mailbox (Gmail OAuth client id/secret or SMTP password or M365), verifier key, optional DataForSEO/Serper/Hunter/Cloudflare/LinkedIn password. All in plaintext .env on disk.

## Legal exposure
- Harvey puts the legal burden on the sender: "you are the sender". CAN-SPAM needs a physical address and opt-out; grep of harvey/ and prompts/ finds no code that inserts an unsubscribe line or address in email bodies (only advice in setup text for Instantly; issue #13 "Add a compliance footer" is still open). Opt-out is handled only on inbound reply keywords.
- GDPR/PECR: README says B2B needs legitimate interest, you must know the data source. Applies if any EU/UK recipient.
- Colombia: Ley 1581 de 2012 (habeas data; prior, express, informed authorization for personal data processing, SIC supervises; sources found were thin, verify text at secretariasenado.gov.co). Ley 2300 de 2023 art. 3 par. 3 limits advertising by email/SMS/calls to set hours (Mon-Fri 7:00-19:00, Sat 8:00-15:00, none Sun/holidays) and art. 5 extends to commercial providers; RNE exclusion registry. Scraping contact data of sole traders (personal data) and mass-emailing them is where exposure sits. Corporate role addresses are lower risk but not zero. Sending to US/EU recipients adds their law.
- The user's quiet hours must be set by hand; guide says to set them.

## Install security
- Python package, `pip install -e .` of 12 deps (pyyaml, httpx, playwright, beautifulsoup4, dnspython, aiosmtplib, aiosqlite, pydantic, fastapi, uvicorn, python-dotenv, pytz), unpinned-upper-bounded, no lockfile. No install hooks, no curl|sh in the repo; the Dockerfile runs `curl -fsSL https://claude.ai/install.sh | sh || true` (official URL). `harvey install` runs pip and `playwright install chromium`.
- Dashboard binds 127.0.0.1:5555, no auth, no CSRF/Origin check on POST endpoints (approve-all, resume sending, set .env values via /api/settings/env). A malicious web page opened in the same browser could in principle hit them. Real but moderate; mitigated by localhost.
- Writes mailbox tokens and API keys to .env; reads Claude OAuth token. A compromise of this repo's dependencies or a malicious fork gets all of it. The setup flow in the PDF has Claude Code do everything with a permissive prompt on cloned third-party code.
- Prompt-injection surface is high (reply text, scraped pages) but tools are disabled, so worst case is bad email text, which the approval queue catches.

## Maintenance and community
Repo created 2026-03-12, MIT, 855 stars, 161 forks, 5 open issues (2026-10-15). Version 0.3.0 in pyproject (README says 0.2.1). Heavy recent activity (many commits 2026-10-13 to 10-15 from Ethan+, Gabe AO, others) but history before is sparse (Mar, Jul, Aug, Sep bursts). 242 tests, CI. Early; one main author; a commercial angle (Precleared, Tellwing, NodeStudio guide) around it. Not a track record of stability.

## What the localleadhub page and the PDF add
- localleadhub.com/harvey-ai is a DIFFERENT product: "Harvey AI Business Assistant" inside the "360 Growth OS" (voice, chat, CRM, content, GoHighLevel-style), "Book a Strategy Call". It has nothing to do with ethanplusai/harvey. Do not use it as evidence about the repo. Name collision.
- The NodeStudio PDF adds: a ready Claude Code install prompt; hardware/accounts checklist (Gmail/Workspace ~US$7/mo on a secondary domain, Reoon 600 free/mo or ZeroBounce 100 free, machine must stay on); warm-up 2 to 4 weeks, start 10-20/day; Windows install issues (pip "No matching distribution" is really a timeout, use `--timeout 300 --retries 10`; slow clone); tells Claude Code to run `harvey run` and `harvey dashboard` in background and autostart (Task Scheduler/launchd), i.e. always-on automation; use as list-builder only (`harvey export`). It says "No hay facturación por API" and does not mention Anthropic's terms at all. It also tells the user to avoid `harvey setup` because it is interactive.

## Real uses for the user's freelance business
Fit is partial. The strongest signals for selling web builds exist: NO_WEBSITE, INCUMBENT_AGENCY, NO_SCHEMA_MARKUP, NO_ONLINE_BOOKING, BLOG_STALE, TECH_STACK, SERP_RANK 11-30. But the default free source (OpenStreetMap) is thin for service trades and for Colombia; the good source is DataForSEO (paid, ~0.37 USD / 1000) or Serper. The email-verifier chain and signal list are US/EU-centric; Colombian SMEs often use WhatsApp/Instagram, not email. Cold email in Spanish is possible by editing skills/ but all prompts are English. Useful ideas to copy: the observation-row data model, the free HTTP profiler (3 requests: homepage, robots, sitemap + regex), "never lead with an offer" rule, deterministic pre-send gate, approval queue.

## Safer alternatives (fit with existing skills cro, offers, lead-magnets)
1. List-only, no sending: write a small script or use `/scrape`-style skills to audit local business sites (no site, no schema, slow Lighthouse) and keep a CSV; the user sends 10-20 hand-checked emails or WhatsApp messages himself. Claude is used interactively, which is ordinary use.
2. Use the existing offers skill to define a "free site audit" offer and lead-magnets for an inbound page; cro on his own portfolio site. Inbound avoids Ley 2300/CAN-SPAM cold-contact exposure.
3. If automation is wanted: run the loop on an Anthropic API key (Commercial Terms) with the Messages API, not the subscription; cost is small because Harvey is deterministic except writing/scoring. Or use an established sequencer (Instantly, Lemlist, Smartlead) which handles unsubscribe links, address footer and warm-up.
4. Throwaway VM trial only: separate Gmail account/domain, no personal Claude login (use an API-key-backed environment), no real recipients, to study the code. Not needed for the verdict.

## Risks, ranked
1. Anthropic ToS: bot on subscription credentials plus OAuth token reuse; ban risk affects his main Claude account.
2. Spam/legal: no auto footer or address; Ley 1581 and Ley 2300 in Colombia; CAN-SPAM per-email fines claimed in README ($53,088).
3. Domain/mailbox reputation: a new domain needs 2-4 weeks warm-up; one bad run burns it.
4. Supply chain and local exposure: plaintext secrets, unauthenticated local dashboard, ~12 deps, young single-author project.
5. Fit: wrong geography/channel for Colombian SMEs; weak free data.
