---
name: astro-patterns
description: >
  Astro static-site patterns for the freelance client stack (Astro + React islands +
  Tailwind + shadcn on Cloudflare). Use when building or reviewing an Astro site - islands
  and client directives, astro:assets images, content collections, trailing-slash/canonical
  hygiene, CSP-with-islands, fonts, sitemaps, and the Cloudflare Workers vs Pages deploy
  gotcha. Grounded in official Astro docs. Skip for Next.js/Vite/other stacks.
---

# Astro Patterns

Conventions for the freelance website stack: **Astro static output + React islands only where
needed + Tailwind + shadcn/ui, deployed on Cloudflare.** Defaults are static and fast; you opt
into JavaScript deliberately. Grounded in https://docs.astro.build.

## 1. Static first - hydrate on purpose, not by default

Astro renders every component to plain HTML + CSS and strips all client JS unless you explicitly
mark it. Keep it that way. Reach for a React island only for genuine interactivity (hero canvas,
multi-step form, FAQ accordion). One big monolithic island defeats the point - keep each island
small and self-contained so only the part that needs JS ships JS.

## 2. Client directives - pick the cheapest that works

Default is no JS. When a component must hydrate, choose by *when the user actually needs it*:

| Directive | Hydrates when | Use for |
|-----------|---------------|---------|
| `client:load` | immediately on page load | above-the-fold, must be instantly interactive (rare) |
| `client:idle` | browser goes idle after load | non-critical interactivity that can wait |
| `client:visible` | component scrolls into viewport | anything below the fold (carousels, accordions, charts) - **the default choice** |
| `client:media={query}` | a media query matches | mobile-only or desktop-only widgets |
| `client:only="react"` | never SSR'd; client-only | components that break during SSR (browser-only APIs) |

Official guidance: don't reflexively use `client:load`. For an expensive component below the fold,
`client:visible` so it only loads when seen. The hero canvas is usually the only `client:load`.

## 3. Server islands for dynamic bits (keep the page static)

If one piece needs server-side/personalized rendering but the rest is static, use a **server island**
(`server:defer`) so that island renders on demand with a placeholder while the static page ships
immediately. Lets you stay static-output without an SSR adapter for the whole site.

## 4. Images - always `astro:assets`, never raw `<img>` for local art

- `<Image />` for a single optimized image; `<Picture />` to emit multiple formats (AVIF/WebP + fallback).
- Both **auto-set width/height to prevent layout shift (CLS)** and add `loading`/`decoding`. Always pass `alt`.
- **`src/` = optimized** (transformed, hashed, bundled). **`public/` = raw passthrough** (no processing) - use only for files that must keep an exact path/name (favicon, `security.txt`, `robots.txt`, OG image).
- Hero/LCP image: `loading="eager"` + `fetchpriority="high"`. Everything else: lazy by default.
- Responsive: set `layout` on `<Image />` to auto-generate `srcset`/`sizes`; enable `image.responsiveStyles: true` in config (adds build time, worth it).
- Remote images only optimize if authorized via `image.domains` / `image.remotePatterns` in `astro.config.mjs`.
- Sharp is the built-in optimizer (ships with Astro - nothing to install). For turning a raster mascot into an SVG, that's `vtracer` (a separate CLI), not Astro.

## 5. Content collections for any repeated content

Blog posts, case studies, FAQ entries -> a **content collection** with a Zod schema, not ad-hoc
files. Build-time collections cache between builds, scale to thousands of entries, and give you
typed frontmatter + image optimization for free. Use them whenever content is static and repeated.

## 6. URL + canonical hygiene (this stack's recurring bug)

- Set `trailingSlash: 'always'` and `site: 'https://{{DOMAIN}}'` in `astro.config.mjs`.
- Then make **canonical, hreflang, sitemap, and every internal link** use trailing slashes too, so
  they match what Cloudflare serves and you avoid the `/x` -> `/x/` 307 redirect mismatch.
- `@astrojs/sitemap` for the sitemap; exclude noindex pages (e.g. `/thank-you`) from it.

## 7. CSP with islands (the security gotcha)

- A site with **no islands** can be strict: `script-src 'self'` + hashes for any inline script.
- A site **with Astro/React islands needs `script-src 'unsafe-inline'`** - islands hydrate via inline
  bootstrap scripts, so a strict hash-only CSP will break hydration. Alternative: Astro's experimental
  CSP feature. Keep `font-src` allowing `data:` if Turnstile is present (it injects data: fonts).
- Keep the CSP identical if it's declared in two places (`_headers` + a meta fallback).

## 8. Fonts

Self-host (no Google Fonts request): drop the files in `src/`, `@font-face` with `font-display: swap`,
preload only the one critical weight. Max two families unless the brand system says otherwise.

## 9. Cloudflare deploy - Pages vs Workers

- **Pages:** simplest. `npm run build`, output `dist`, no extra config.
- **Workers:** commit a `wrangler.jsonc` with **static assets only** (`assets.directory = ./dist`, no
  `main`) so `wrangler deploy` does **not** auto-add the SSR adapter and silently turn your static
  site into a server one. Keep it static unless a server endpoint is truly required.

## Quick checklist

- [ ] Static by default; islands only where interactive, each one small.
- [ ] Cheapest client directive (`client:visible` unless it must be instant).
- [ ] `astro:assets` Image/Picture for local art; `alt` always; hero eager+high priority.
- [ ] Repeated content in a typed content collection.
- [ ] `trailingSlash: 'always'` + `site` set; canonical/hreflang/sitemap/links all trailing-slashed.
- [ ] CSP allows `unsafe-inline` for scripts if islands exist; `font-src data:` if Turnstile.
- [ ] Fonts self-hosted, `swap`, one preload.
- [ ] Workers deploy: static-only `wrangler.jsonc`, no SSR adapter.
