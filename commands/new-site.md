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
- **Static brochure** -> base only.
- **Booking (pay in person)** -> base + `modules/booking.md`.
- **Booking + online payment** -> base + `modules/booking.md` + `modules/payments.md`.
- **Headless commerce** -> base + `modules/headless-commerce.md` + `modules/payments.md` (stays on the static base: SSG catalog + island cart + Worker/D1; own SSR base only if the client needs live multi-SKU inventory rendered into HTML or personalized SSR pages).

## Step 2 - Read the spec
Read the base template + the chosen module(s) + both guides. These are the binding instructions and
the pre-launch gate. Do not restate them; follow them.

## Step 3 - Intake (the full §0 - NOT a one-liner)
`$ARGUMENTS` is only a seed. Gather the **complete** §0 intake before building - pull what exists from
the client's brand system + the `business` intake docs, and **ask for everything missing**.
Required:
- **Identity:** brand name, one-liner/positioning, audience, offerings + pricing, mascot (or none), signature color.
- **Jurisdiction (gate):** the client's country/region -> sets the LEGAL-GUIDE region AND the payment
  gateway (Colombia -> Habeas Data + DIAN + **Wompi**; international -> CCPA/GDPR + **Stripe**). Confirm this explicitly.
- **Existing design system:** do they already have a `brand-system.md`? (-> Step 4 gate)
- **Existing content/assets:** copy, logo, photos, domain, what's missing.
- **Contact & channels:** inbox email, personal email, primary CTA + phone/WhatsApp number, socials, locales.
- **Infra:** GitHub org, analytics/status hosts.

Do not proceed to build with gaps. Confirm the filled intake back to the user.

## Step 4 - Brand-system gate (HARD - no build without it)
A locked **`brand-system.md`** must exist and be signed off before any building (static template §1).
- **Exists + signed off** -> read it; it's the binding source of truth (Claude follows the `.md`, not any HTML board).
- **Missing or not signed off** -> STOP and produce it first: fill `templates/brand-system.template.md`
  (run `/design` for direction + template §3 for the mascot/logo assets - Nano Banana is the user's
  manual step, `vtracer` post-process is in-session), show the client, get **explicit sign-off**, then
  continue. Never build off-brand because the system wasn't locked.

## Step 5 - Scaffold the client repo
Create a NEW private repo for the client (use the `github-setup` skill or `gh`), Astro static output,
per the `astro-patterns` skill (islands only where needed, `trailingSlash: 'always'`, `astro:assets`,
Cloudflare Workers/Pages). One client = one repo (like `example.studio`). Never build in the template repo.

## Step 6 - Propose, then build (the template's build order)
Propose the asset list + section plan + chosen hero signature concept, and **wait for sign-off**
(template build-order step 2). Then run the template build order, invoking the skills it names:
- **`/design`** - lock direction -> source components (magic MCP) -> assemble (`frontend-design` + `impeccable`) -> motion (`design-motion-principles`) -> audit.
- **`astro-patterns`** - Astro conventions throughout.
- Assets: user does the mascot; you source stock/cutouts/brand SVG (template section 13).
- Implement **SEO-GUIDE** + **LEGAL-GUIDE** across all pages.
- Build the module(s) per their docs:
  - **booking** - Workers + D1 + Durable Objects (no double-booking) + Resend + Google Calendar + `.ics`.
  - **payments** - multi-gateway (Wompi CO incl. integrity + events secrets + DIAN / Stripe intl); idempotent webhook is the correctness core; PSP-hosted checkout (SAQ-A).
  - **headless-commerce** - SSG catalog + island cart + Worker/D1; reuses the DO lock (no oversell) and payments' webhook; product page shows live price/stock, not stale SSG.

## Step 7 - Gate + launch
- Run **`/production-audit`** + the template section 15 pre-launch gate + module pre-launch additions.
- Run **`a11y-architect`** and **`security-review`** passes.
- Deploy to Cloudflare (`land-and-deploy` / `deployment-patterns`). Confirm Lighthouse green, no placeholders.

## Step 8 - Hand off
Point back to `business` for the off-boarding/thank-you/renewal step. Done.
