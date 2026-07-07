---
description: Build a client website end to end - pick the site type, pull the right base template + modules + guides from the build system, scaffold the client repo, fill variables, then run the build order (design pipeline, assets, SEO, legal, audits, deploy). Orchestrates /design and the build skills.
---

# New Site

Scaffold and build a client website using the build-templates system. `$ARGUMENTS` = client name +
site type + any brief. This command **reads the template repo as the spec and builds in the client
repo** - it never edits the build system itself.

**Build system location:** `~/projects/freelance/website-build-templates`
- base: `templates/static.md` | modules: `modules/*.md` | guides: `guides/SEO-GUIDE.md`, `guides/LEGAL-GUIDE.md`
**Business inputs:** `~/projects/freelance/business` (intake, tiers, Wompi/Stripe guides)

## Step 1 - Site type -> template + modules
Determine the type from `$ARGUMENTS`; if unclear, ask. Map it:
- **Content / marketing site** -> base only. (Statically rendered = fast + crawlable + AI-search-ready; "static" is the rendering, not a page count - it scales to a full content hub.)
- **Booking (pay in person)** -> base + `modules/booking.md`.
- **Booking + online payment** -> base + `modules/booking.md` + `modules/payments.md`.
- **Headless commerce** -> base + `modules/headless-commerce.md` + `modules/payments.md` (stays on the static base: SSG catalog + island cart + Worker/D1; own SSR base only if the client needs live multi-SKU inventory rendered into HTML or personalized SSR pages).

## Step 2 - Read the spec
Read the base template + the chosen module(s) + both guides. These are the binding instructions and
the pre-launch gate. Do not restate them; follow them.

## Step 3 - Intake (the full §0 - NOT a one-liner)
`$ARGUMENTS` is only a seed. Gather the **complete** §0 intake before building - pull what exists from
the client's brand system + the `business` intake docs, and **ask for everything missing**. When the
client's market / positioning / pricing is unclear, use the **`business-analyzer`** skill to structure the
discovery (audience, competitive, pricing-GTM).
Required:
- **Identity:** brand name, one-liner/positioning, audience, offerings + pricing, mascot (or none), signature color.
- **Jurisdiction (gate):** the client's country/region -> sets the LEGAL-GUIDE region AND the payment
  gateway (Colombia -> Habeas Data + DIAN + **Wompi**; international -> CCPA/GDPR + **Stripe**). Confirm this explicitly.
- **Existing design system:** do they already have a locked `brand-system.html`? (-> Step 4 gate)
- **Existing content/assets:** copy, logo, photos, domain, what's missing.
- **Content map (AI-SEO):** the real questions/searches the client's customer has before buying or hiring -
  this fuels the topical page plan (SEO-GUIDE §0.5). What do they ask? What are they deciding between?
  Build genuinely-helpful pages that answer those - **never** a page per keyword (Google scaled-content-abuse).
- **Contact & channels:** inbox email, personal email, primary CTA + phone/WhatsApp number, socials, locales.
- **Infra:** GitHub org, analytics/status hosts.

Do not proceed to build with gaps. Confirm the filled intake back to the user.

## Step 4 - Brand-system gate (HARD - no build without it)
A locked **`brand-system.html`** must exist and be signed off before any building (static template §1).
- **Exists + signed off** -> read it; it's the binding source of truth. Follow its **machine-readable
  tokens** (the `:root` CSS custom properties + the `#brand-tokens` JSON block) - exact values, not eyeballed.
- **Missing or not signed off** -> STOP and produce it first with **`/brand-system`** (fills
  `templates/brand-system.template.md` -> emits `brand-system.html`; the mascot/logo come from template
  §3 - Nano Banana is the user's manual step, `vtracer` post-process is in-session). Show the client, get
  **explicit sign-off**, then continue. Never build off-brand because the board wasn't locked.

## Step 5 - Scaffold the client repo
Create a NEW private repo for the client (use the `github-setup` skill or `gh`), Astro static output,
per the `astro-patterns` skill (islands only where needed, `trailingSlash: 'always'`, `astro:assets`,
Cloudflare Workers/Pages). One client = one repo (like `example.studio`). Never build in the template repo.

## Step 6 - Propose, then build (the template's build order)
Propose the asset list + section plan + chosen hero signature concept, and **wait for sign-off**
(template build-order step 2). Then run the template build order, invoking the skills it names:
- **`/design`** - lock direction -> source components (magic MCP) -> assemble (`frontend-design` + `impeccable`) -> motion (`design-motion-principles`) -> audit.
- **`astro-patterns`** - Astro conventions throughout.
- **Copy:** draft page copy with **`content-ops`** (Mode A - collaborative, client approves before code; the homepage answers the 7 questions, "why you" clear in 5s).
- Assets: user does the mascot; you source stock/cutouts/brand SVG (template section 13). Generate custom imagery with **`nano-banana`** (Gemini). For a premium scroll-hero built from a video, use **`video-to-website`**.
- Implement **SEO-GUIDE** (incl. §0.5 the AI-search era: helpful, topical content answering the customer's
  real questions, structured data, crawlable HTML; **no page-per-keyword**) + **LEGAL-GUIDE** across all pages.
- Build the module(s) per their docs:
  - **booking** - Workers + D1 + Durable Objects (no double-booking) + Resend + Google Calendar + `.ics`.
  - **payments** - multi-gateway (Wompi CO incl. integrity + events secrets + DIAN / Stripe intl); idempotent webhook is the correctness core; PSP-hosted checkout (SAQ-A).
  - **headless-commerce** - SSG catalog + island cart + Worker/D1; reuses the DO lock (no oversell) and payments' webhook; product page shows live price/stock, not stale SSG.

## Step 7 - Gate + launch
- Run **`/production-audit`** + the template section 15 pre-launch gate + module pre-launch additions.
- Run **`a11y-architect`** and **`security-review`** passes.
- Deploy to Cloudflare (`land-and-deploy` / `deployment-patterns`). Confirm Lighthouse green, no placeholders.
- **Index:** submit the sitemap in Google Search Console + Bing Webmaster, and ping **IndexNow** for the URL set.

## Step 8 - Hand off + offer the retainer
Point back to `business` for off-boarding/thank-you. **Then offer the monthly retainer** - Care base +
add-ons (`tiers.tex` / `MONTHLY-OPS-GUIDE.md`). The build is client acquisition; the retainer is the business.
If they take it, set the client's retainer scope and run their cycle with **`/monthly-ops`**.
