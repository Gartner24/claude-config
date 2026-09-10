# Stacks and tokens - detection, component sources, and the portable token layer

> Research reference for the design pipeline. Compiled 2026-09-09 from primary
> sources; every tool, endpoint and browser-support figure was verified at that
> date and carries its URL inline. Items that could not be confirmed are marked
> UNVERIFIED - treat those as leads, not facts. Re-verify prices and model IDs
> before quoting them to a client.

# Research C: making the /design pipeline stack-agnostic

Date of research: 2026-09-09. Every version/license below was read from the npm
registry (`npm view <pkg> version license`) or from the vendor's own docs on that
date. Anything I could not confirm is labelled UNVERIFIED inline.

---

## 1. Stack detection: an ordered decision procedure

Detection is a cascade, not a checklist. Meta-frameworks nest (Next depends on
react, Nuxt on vue, SvelteKit on svelte, Astro on all of them), so the only
correct order is most-specific-first, and each gate hands its answer to the next.

Run the gates in this order. Stop at the first match inside a gate, then move to
the next gate.

### Gate 0 - is this a JS project at all?

```
ls package.json
```

- Present -> Gate 1.
- Absent -> Gate 5 (server-rendered / static / non-JS).
- Present but with no UI framework dependency and a `templates/`, `views/`,
  `resources/views/` or `layouts/` directory -> it is an asset pipeline bolted to a
  server-rendered app. Do Gate 5, then come back to Gate 2 for the styling layer.

### Gate 1 - the framework

Read `dependencies` + `devDependencies` from package.json, then confirm with a
config file. First match wins.

| Order | package.json signal | Config-file confirmation | Result |
|---|---|---|---|
| 1 | `astro` | `astro.config.{mjs,ts,js}` | Astro. Then sub-detect islands: `@astrojs/react`, `@astrojs/vue`, `@astrojs/svelte`, `@astrojs/solid-js`. None present -> pure `.astro` components, no client runtime. |
| 2 | `next` | `next.config.{js,mjs,ts}` | Next.js (React). Sub-detect router: `app/` dir -> App Router; `pages/` -> Pages Router. `components.json` with `"rsc": true` confirms RSC. |
| 3 | `nuxt` | `nuxt.config.{ts,js}` | Nuxt (Vue). |
| 4 | `@sveltejs/kit` | `svelte.config.js` | SvelteKit. |
| 5 | `svelte` without kit | `svelte.config.js` + `vite.config.*` | Svelte SPA. |
| 6 | `@angular/core` | `angular.json` | Angular. |
| 7 | `react-router` >= 7 with `@react-router/dev`, or `@remix-run/*` | `react-router.config.ts` / `remix.config.js` | React Router framework mode / Remix. |
| 8 | `solid-js` / `@builder.io/qwik` / `preact` | `vite.config.*` | Solid / Qwik / Preact. |
| 9 | `react` alone | `vite.config.*` or `webpack.config.*` | React SPA. |
| 10 | `vue` alone | `vite.config.*` | Vue SPA. |
| 11 | none of the above | - | Node service or tooling. Go to Gate 5. |

### Gate 2 - the styling layer (this is the gate that decides the token target)

Precedence: whatever already owns the token surface wins. First match wins.

**2a. Tailwind, and which major version.** This is the single most misdetected
signal, so do it in this exact order:

1. Find the CSS entry. Candidates, in order: the `tailwind.css` path in
   `components.json`, then `src/**/{app,globals,global,index,main,styles}.css`,
   then `app/globals.css`, then `assets/css/*.css`.
2. Grep that file:
   - contains `@import "tailwindcss"` (or `@import 'tailwindcss'`) -> **Tailwind v4**. Confirmed: v4 replaced the three `@tailwind` directives with a single regular CSS `@import`.
   - contains `@tailwind base;` -> **Tailwind v3**.
3. Only if step 2 found nothing, fall back to package signals:
   - `@tailwindcss/vite`, `@tailwindcss/postcss` or `@tailwindcss/cli` in deps -> v4. (In v3 `tailwindcss` itself was the PostCSS plugin; in v4 the PostCSS plugin moved to its own package.)
   - `tailwindcss` semver range starting `^4`/`4.` -> v4. `^3` -> v3.

**Confirmed: Tailwind v4 needs no JS config file.** Configuration is CSS-first via
`@theme { ... }`. A `tailwind.config.js` may still be present in a v4 project, but
only if the CSS explicitly opts in with `@config "../../tailwind.config.js";`. So
**the presence of `tailwind.config.{js,ts,cjs,mjs}` does NOT mean v3** - always
grep the CSS entry first. Conversely a v4 project with a `@theme` block and no JS
config is the normal, expected shape.

**2b. shadcn.** `components.json` at repo root with
`"$schema": "https://ui.shadcn.com/schema.json"`. Parse it, do not just test for
existence - it carries the whole map:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "styles/global.css",
    "baseColor": "zinc",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks",
    "utils": "@/lib/utils"
  },
  "registries": {
    "@shadcn": "https://ui.shadcn.com/r/{name}.json"
  }
}
```

Notes: `style` is immutable after init. `tailwind.cssVariables: true` means the
project is already token-driven and your token layer should overwrite those vars
rather than introduce a parallel set. `registries` tells you which extra
registries the CLI can already reach. shadcn-vue and shadcn-svelte also write a
`components.json`, so disambiguate the framework at Gate 1, never from this file.

**2c. everything else** - first match wins:

| Styling system | Detection signal |
|---|---|
| Panda CSS | `@pandacss/dev` in deps + `panda.config.ts` + a `styled-system/` dir |
| vanilla-extract | `@vanilla-extract/css` in deps + any `*.css.ts` file |
| StyleX | `@stylexjs/stylex` in deps + `stylex.create(` in source, or `*.stylex.ts` |
| styled-components | `styled-components` in deps |
| Emotion | `@emotion/react` or `@emotion/styled` in deps |
| UnoCSS | `unocss` in deps + `uno.config.ts` |
| Sass | `sass`/`sass-embedded` in deps + `*.scss` files |
| CSS Modules | glob hit on `**/*.module.{css,scss}` and no Tailwind |
| Plain CSS | none of the above; take the largest `.css` under `src/`, `styles/`, `assets/` |

Panda, vanilla-extract and StyleX are the three that will fight a raw
`:root { --x: y }` token drop, because they want tokens declared in their own
config/TS. Detecting them changes the *emit target*, not the token content
(see section 3).

### Gate 3 - existing component library

Grep deps against the table in section 2. If a library is already installed, the
pipeline extends it; it does not introduce a second one. Two libraries that both
patch Tailwind's base layer will collide - Skeleton's own docs say it cannot be
combined with Flowbite React, Flowbite Svelte or daisyUI for exactly this reason.

### Gate 4 - the interactivity layer (matters most for server-rendered stacks)

| Signal | Result |
|---|---|
| `alpinejs` in package.json, or `<script src=".../alpinejs` / `cdn.jsdelivr.net/npm/alpinejs` in a base template | Alpine.js |
| `htmx.org` dep or `<script src=".../htmx` | htmx |
| `@hotwired/stimulus` / `@hotwired/turbo` | Stimulus / Turbo (Rails) |
| `livewire/livewire` in composer.json | Livewire |
| `phoenix_live_view` in mix.exs | LiveView |
| none of the above | vanilla JS or web components |

### Gate 5 - non-JS and server-rendered

| Manifest / marker | Then grep for | Stack | Template glob |
|---|---|---|---|
| `Gemfile` | `rails` | Rails | `app/views/**/*.erb`; `view_component` gem -> `app/components/**/*.rb`; `phlex` gem -> Phlex |
| `composer.json` | `laravel/framework` | Laravel | `resources/views/**/*.blade.php` |
| `composer.json` | `symfony/framework-bundle` | Symfony | `templates/**/*.twig` |
| `pyproject.toml` / `requirements.txt` / `Pipfile` | `django` or `manage.py` + `settings.py` | Django | `**/templates/**/*.html` containing `{% extends %}` / `{% block %}` |
| same | `flask` / `jinja2` / `fastapi` + `jinja2` | Jinja | `templates/**/*.html`, `*.j2` |
| `mix.exs` | `phoenix` | Phoenix | `**/*.heex` |
| `go.mod` | `a-h/templ` | templ | `**/*.templ` |
| `go.mod` | `html/template` import | Go stdlib templates | `**/*.tmpl`, `**/*.gohtml` |
| `*.csproj` | - | ASP.NET | `**/*.cshtml`, `**/*.razor` |
| `wp-config.php` or `wp-content/` | `style.css` with a `Theme Name:` header comment; `functions.php` | WordPress classic theme | `*.php` template parts |
| same + `theme.json` at theme root | - | WordPress block theme (FSE) | `templates/**/*.html`, `parts/**/*.html` |
| `hugo.toml` / `config.toml` + `layouts/` | - | Hugo | `layouts/**/*.html` |
| `_config.yml` + `_layouts/` | - | Jekyll | `_layouts/**/*.html` |
| `.eleventy.js` / `eleventy.config.js` | - | Eleventy | `**/*.njk`, `**/*.liquid` |
| bare `index.html`, no manifest | - | Static HTML | `**/*.html` |

WordPress block themes are the one server-rendered stack with a native token
format: `theme.json` has its own `settings.color.palette`, `settings.typography`
and `settings.spacing` schema, which WordPress compiles into `--wp--preset--*`
custom properties. Emit into that, not into a separate `:root` block. (Schema
detail UNVERIFIED beyond the `--wp--preset--*` naming convention - confirm against
the current WordPress theme.json reference before emitting.)

---

## 2. Component sources per stack

Legend for the last three columns:
- **Delivery**: `copy` = source lands in your repo and you own it; `dep` = npm/composer package you import; `both` = hybrid (headless dep + copied styled layer).
- **Styled?**: `headless` = behaviour + a11y only, zero visual opinion; `styled` = ships a look.
- **Tailwind?**: does adopting it force Tailwind into the project.

### React + Tailwind

| Source | Version / license | Delivery | Styled? | Tailwind? | Notes |
|---|---|---|---|---|---|
| shadcn/ui (`shadcn` CLI) | CLI `shadcn@4.21.0`, MIT | copy | styled | yes | The reference implementation. CLI commands: `init`, `add`, `apply`, `preset`, `view`, `search`, `list`, `build`, `docs`, `info`, `migrate`, `eject`, `mcp`. `add` accepts a name, a URL, or a local path. https://ui.shadcn.com/docs/cli |
| Origin UI | MIT | copy | styled | yes | shadcn-compatible; moved to Tailwind v4 in Feb 2025. https://github.com/shadcn/originui |
| Aceternity UI | UNVERIFIED license (site does not state one on the pages fetched) | copy | styled | yes | 200+ animated components, React + TS + Tailwind v4 + Motion. https://ui.aceternity.com/ |
| Magic UI | UNVERIFIED license (widely reported MIT) | copy | styled | yes | 150+ animated components designed to drop into a shadcn codebase. |
| Tailwind Plus (ex Tailwind UI) | Commercial, terms UNVERIFIED - the license page is behind a login | copy | styled | yes | First-party marketing/app/e-commerce blocks. Check the licence text with the user before shipping any of it into a client repo. |
| 21st.dev catalogue | mixed, per-component | copy | styled | yes | See section 4. |

### React without Tailwind

| Source | Version / license | Delivery | Styled? | Tailwind? | Notes |
|---|---|---|---|---|---|
| Base UI | `@base-ui-components/react@1.0.0-rc.0`, MIT | dep | headless | no | Built by people from Radix, Material UI and Floating UI. Explicitly styling-agnostic - Tailwind, CSS Modules, plain CSS, CSS-in-JS. Still an RC as of today (npm dist-tag `latest` = `1.0.0-rc.0`); the docs site claims a higher number, npm is the authority. |
| Radix Primitives | `@radix-ui/react-dialog@1.1.23`, MIT | dep | headless | no | The mature default. Pair with CSS Modules or vanilla-extract. |
| Ark UI | `@ark-ui/react@5.39.1`, MIT | dep | headless | no | 45+ components, identical API across React, Vue, Solid and Svelte. State-machine driven. The best pick when one design has to ship to several frameworks. |
| React Aria Components | `react-aria-components@1.21.1`, Apache-2.0 | dep | headless | no | Adobe. Strongest a11y and i18n story of the group. |
| Mantine | `@mantine/core@9.6.1`, MIT | dep | styled | no | CSS-Modules-based, themes through CSS custom properties. The best answer for "React app, no Tailwind, want batteries included". |
| Park UI | `@park-ui/panda-preset@0.43.1`, MIT | both | styled | no (needs Panda CSS) | Ark UI + Panda CSS, shadcn-style copy-in. Correct only when Panda is already the styling layer. |

### Vue / Nuxt

| Source | Version / license | Delivery | Styled? | Tailwind? | Notes |
|---|---|---|---|---|---|
| Nuxt UI | `@nuxt/ui@4.11.1`, MIT | dep | styled | yes | v4 merged Nuxt UI Pro into the free open-source package (100+ components, Figma kit). Built on Reka UI + Tailwind CSS. Works in plain Vue/Vite/Inertia, not only Nuxt. **Default recommendation for Vue.** |
| shadcn-vue | `shadcn-vue@2.8.2`, MIT | copy | styled | yes | Direct shadcn port; also ships its own MCP server (https://www.shadcn-vue.com/docs/mcp). Pick this when the design direction is already expressed as shadcn tokens. |
| Reka UI | `reka-ui@2.10.4`, MIT | dep | headless | no | The renamed Radix Vue (v2+). Underlies both Nuxt UI and shadcn-vue. |
| Ark UI Vue | `@ark-ui/vue`, MIT | dep | headless | no | Same API as the React build. |
| PrimeVue | `primevue@5.0.1`, MIT (LICENSE.md confirms "The MIT License (MIT) ... PrimeTek") | dep | styled | no | Huge component count including data-heavy enterprise widgets. Themes are its own token system, not yours. |

### Svelte / SvelteKit

| Source | Version / license | Delivery | Styled? | Tailwind? | Notes |
|---|---|---|---|---|---|
| shadcn-svelte | `shadcn-svelte@1.6.1`, MIT | copy | styled | yes | Built on Bits UI. **Default when the direction is shadcn-shaped.** |
| Bits UI | `bits-ui@2.19.2`, MIT | dep | headless | no | Unstyled Svelte components, no CSS resets, no design-system assumptions. Styling via `class` props and `data-*` attributes. Architecturally inspired by Melt UI. |
| Melt UI | `melt@0.44.0` (Svelte 5 builder rewrite) and legacy `@melt-ui/svelte@0.86.6`, both MIT | dep | headless | no | Builder-based. Pick `melt` for Svelte 5. |
| Skeleton | `@skeletonlabs/skeleton@5.0.1`, MIT | dep | styled | yes | Tailwind-based, framework-agnostic core with Svelte, React and Astro installs. Its docs warn it cannot coexist with Flowbite or daisyUI. |

### Astro

Astro has three real paths, in this order of preference:

1. **Native `.astro` components + a CSS-only or web-component kit.** Zero client
   JS by default, which is the whole reason people choose Astro. Basecoat, Franken
   UI / 0build, Web Awesome and Pico all work here unchanged.
2. **Starwind UI** - `@starwind-ui/astro` (also React, and Vue in beta), v3.0,
   CLI-based source-first: you add a styled component and then own the code.
   License UNVERIFIED (not stated on the getting-started page). https://starwind.dev
3. **An island framework's library.** If `@astrojs/react` is already configured,
   shadcn/ui works verbatim inside `client:*` islands; same for shadcn-vue with
   `@astrojs/vue`. Cost: you pull that framework's runtime into the bundle for
   every island. Only correct when the component genuinely needs client state.
   daisyUI is the cheap middle ground - one Tailwind plugin that styles both
   `.astro` markup and every island framework identically.

### Angular

| Source | Version / license | Delivery | Styled? | Tailwind? | Notes |
|---|---|---|---|---|---|
| Angular Material | `@angular/material@22.1.6`, MIT | dep | styled | no | Since v18, Material 3 themes are pure CSS custom properties: the `mat.theme(...)` mixin emits `--mat-sys-*` tokens (`--mat-sys-primary`, `--mat-sys-surface`, ...) with no added selector specificity, so you can set them at `:root` and let them cascade. This makes Angular Material the *easiest* non-Tailwind stack to drive from a token file. |
| Spartan UI | `@spartan-ng/brain@1.4.1`, MIT | both | headless brain + copied helm | yes | Two layers: `@spartan-ng/brain` as an npm dep for a11y primitives, `helm` styles copied into your repo via CLI. Requires Tailwind. Uses shadcn-style OKLCH CSS variables (`--primary`, `--background`, `--foreground`) under `:root` and `.dark`. |
| PrimeNG | `primeng@22.1.1`, MIT for community versions (LICENSE.md declares "PRIMENG COMMUNITY VERSIONS LICENSE / The MIT License") | dep | styled | no | Enterprise widget breadth. |

### Plain HTML/CSS, no framework

| Source | Version / license | Delivery | Styled? | Tailwind? | Notes |
|---|---|---|---|---|---|
| Basecoat | `basecoat-css@1.0.2`, MIT | dep or CDN | styled | **yes (v4)** | A vanilla re-implementation of the shadcn/ui design system in HTML/CSS + minimal vanilla JS - shadcn's look with no React and no Radix. Compatible with shadcn themes and CSS variables, so a token file written for shadcn drives it unchanged. JS is vanilla with a lifecycle API (`window.basecoat.init()`, `initAll()`, `refresh()`), not Alpine. Ships optional Nunjucks and Jinja macros. Eight style bundles (Vega, Nova, Maia, Lyra, Mira, Luma, Sera, Rhea). **Best-in-class for any Tailwind-capable server-rendered stack.** |
| Franken UI | `franken-ui@2.1.2`, MIT, last publish 2026-01-18 | CDN or npm | styled | optional | HTML-first, built on UIkit 3 + LitElement web components, shadcn-inspired look. Works standalone as a CSS framework *or* as a Tailwind plugin. CAUTION: the GitHub repo carries a notice that "Franken is now 0build" pointing at https://0build.dev, and npm has not been published since January. Verify project status before adopting. |
| 0build | UNVERIFIED (license and npm package not found) | UNVERIFIED | styled | no ("plain CSS and semantic classes come first") | Apparent successor to Franken UI. Two parts: a "Kit" component library built on shadcn/ui and coss/ui, and semantic CSS utilities (`.z-card`, `.z-button-primary`). Framework-agnostic, CSS layers, AI-friendly markdown docs. Too new to be a default; watch it. |
| Pico CSS | `@picocss/pico@2.1.1`, MIT | CDN or npm | styled | no | Classless semantic CSS. ~60 lines of markup gets a whole readable page. The right answer when the deliverable is a document, an internal tool, or a docs site. |
| Open Props | `open-props@1.7.23`, MIT | CDN, npm or PostCSS | tokens only | no | Not a component kit - 500+ CSS custom properties. See section 3. |
| Kelp UI | UNVERIFIED version (npm `kelp-ui` does not exist; repo is `cferdinandi/kelp`, alpha) | CDN, no build step | styled | no | Modern CSS + web components kept in the **light DOM** so you can style them without piercing shadow roots. Cascade layers, CSS-variable theming. Alpha - do not default to it. |
| daisyUI | `daisyui@5.7.32`, MIT | Tailwind plugin | styled | **yes (v4)** | Installed as `@import "tailwindcss"; @plugin "daisyui";`. CDN option exists. 30+ prebuilt themes. Semantic class names mean the same markup works in `.astro`, `.jsx`, `.vue`, `.blade.php` - **the cheapest way to make one design serve many stacks when Tailwind is acceptable.** |
| Flowbite | `flowbite@4.0.2`, MIT | dep | styled | yes | Also ships React/Vue/Svelte wrappers. |
| Preline | `preline@5.0.0`, "MIT and Preline UI Fair Use License" | dep | styled | yes | The dual licence means: read it before using it in a paid client deliverable. |
| Pines UI | UNVERIFIED license (repo `thedevdojo/pines`) | copy | styled | yes | Alpine.js + Tailwind snippets, copy-paste HTML, no build step. |
| Web Awesome | `@awesome.me/webawesome@3.12.0`, MIT | CDN or npm | styled | no | The successor to Shoelace, from the Font Awesome team. Real custom elements (`<wa-button>`), framework-agnostic, with documented React/Vue/Angular/Svelte and plain-HTML paths. Freemium: a free open-source core plus a Pro tier. Themed through CSS custom properties + theme classes on `<html>`. |
| Shoelace | `@shoelace-style/shoelace@2.20.1`, MIT | CDN or npm | styled | no | The predecessor. Still fine; new work should start on Web Awesome. |
| Alpine.js | `alpinejs@3.17.2`, MIT | CDN or npm | n/a | no | Not a component kit. The behaviour layer for every server-rendered stack below. |

### Server-rendered templates (Django, Jinja, Blade, ERB, Phoenix, Go, WordPress)

The realistic answer: **there is no meaningful component "library" for these - the
component is a template partial you write.** What you actually pick is (a) a CSS
kit that styles semantic HTML, and (b) a sprinkle-JS layer. Web components and a
CSS-only kit are both viable, and they win in different situations:

- **A CSS kit wins** when the project already has a build step that can run
  Tailwind, and when the interactive surface is small (a dropdown, a modal, a
  tabset). Basecoat is the strongest option: shadcn's exact visual language and
  CSS variables, plain HTML markup you paste into any template engine, vanilla JS
  controllers, and shipped Jinja/Nunjucks macros. daisyUI is the runner-up when
  semantic class names matter more than shadcn fidelity.
- **Web components win** when there is no JS build step at all, or when the same
  widgets must appear inside several different host apps. Web Awesome and Kelp
  both drop in from a CDN and are styled entirely through CSS custom properties,
  so one token file themes them everywhere. The cost is a runtime and, for
  shadow-DOM components, styling that can only reach in through the parts and
  custom properties the author exposed. Kelp deliberately avoids that by keeping
  markup in the light DOM.

Per-stack ports that actually exist (each verified by URL, licences UNVERIFIED
unless noted):

| Stack | Option | URL |
|---|---|---|
| Django | shadcn/ui for Django - Tailwind + Alpine template tags | https://shadcn-django.com/ |
| Jinja / Flask / FastAPI | Basecoat Jinja macros (shipped with `basecoat-css`) | https://basecoatui.com/installation/ |
| Laravel Blade | `shadcn-blade/ui` and `bjnstnkvc/shadcn-ui` on Packagist; shadcn's own Laravel guide (Inertia + React) | https://packagist.org/packages/shadcn-blade/ui , https://ui.shadcn.com/docs/installation/laravel |
| Rails ERB | shadcn/ui on Rails | https://shadcn.rails-components.com/ |
| Phoenix | `pine_ui_phoenix` - all 42 Pines UI elements as LiveView components | https://github.com/jamesnjovu/pine_ui_phoenix |
| Go templ | shadcn-templ (formerly templUI), CLI-based, Alpine.js + Tailwind | https://shadcn-templ.com/docs/introduction , https://templui.io/ |
| Go stdlib templates | no port - use Basecoat or daisyUI markup directly | - |
| WordPress | no port - block themes should emit into `theme.json`; classic themes take Basecoat or a CSS kit | - |

Cross-cutting: **the shadcn registry is not React-only.** shadcn's own registry
docs state the registry "works with any project type and any framework, and is not
limited to React". That makes `registry-item.json` a viable distribution format
for your own components regardless of stack (see section 5).

---

## 3. The portable layer: design tokens

### The argument

Locking a direction as Tailwind classes locks it to Tailwind. Locking it as
tokens locks the *decision* and leaves the *emission* free. Three concrete
reasons, each backed by something that exists today:

1. **CSS custom properties are the only universal target.** Every stack in
   section 2 consumes them: Tailwind v4's `@theme` compiles *to* them, Angular
   Material 3 emits nothing but them (`--mat-sys-*`), shadcn stores its whole
   theme in them, Web Awesome and Kelp are themed exclusively through them, Open
   Props is nothing but them, and a Django template can read them with no build
   step at all. There is no second candidate.

2. **Tailwind v4 made this cheap.** In v4, `@theme { --color-brand: oklch(...) }`
   both defines the custom property at `:root` and generates the `bg-brand` /
   `text-brand` utilities. The Tailwind-specific artefact is now a thin naming
   convention over the same custom properties everyone else uses. `@theme inline`
   lets a theme variable reference another variable by value, which is exactly how
   you bridge a stack-neutral token to a Tailwind namespace.

3. **The format is finally standard.** The W3C Design Tokens Community Group
   shipped its first stable spec, **2025.10**, on 2025-10-28, backed by 40+
   organisations. The draft I read on 2026-09-09 is dated 2026-09-08 and is a
   *preview of in-progress changes past 2025.10* - it carries an explicit "do not
   implement anything in this document" banner. **Target 2025.10, not the live
   draft.**

Counter-argument, stated honestly: for a single-stack project that will never
leave Tailwind, a token file plus a generator is a build step producing forty
lines of CSS. Section 5 says when to skip it.

### Minimal token schema (DTCG 2025.10)

Nine groups. Everything the pipeline locks fits here.

```json
{
  "$schema": "https://www.designtokens.org/schemas/2025.10/format.json",

  "color": {
    "$type": "color",
    "bg":        { "$value": { "colorSpace": "oklch", "components": [0.99, 0.004, 106], "alpha": 1, "hex": "#fdfdfc" } },
    "fg":        { "$value": { "colorSpace": "oklch", "components": [0.21, 0.006, 286], "alpha": 1, "hex": "#27272a" } },
    "muted":     { "$value": { "colorSpace": "oklch", "components": [0.55, 0.014, 286], "alpha": 1, "hex": "#71717a" } },
    "surface":   { "$value": { "colorSpace": "oklch", "components": [0.97, 0.003, 106], "alpha": 1, "hex": "#f6f6f5" } },
    "border":    { "$value": { "colorSpace": "oklch", "components": [0.92, 0.004, 286], "alpha": 1, "hex": "#e4e4e7" } },
    "accent":    { "$value": { "colorSpace": "oklch", "components": [0.62, 0.19, 259], "alpha": 1, "hex": "#3b82f6" } },
    "accent-fg": { "$value": { "colorSpace": "oklch", "components": [0.99, 0.000, 0],   "alpha": 1, "hex": "#ffffff" } },
    "danger":    { "$value": { "colorSpace": "oklch", "components": [0.58, 0.22, 27],  "alpha": 1, "hex": "#dc2626" } }
  },

  "font": {
    "$type": "fontFamily",
    "sans":    { "$value": ["Inter", "ui-sans-serif", "system-ui", "sans-serif"] },
    "display": { "$value": ["Instrument Serif", "ui-serif", "Georgia", "serif"] },
    "mono":    { "$value": ["JetBrains Mono", "ui-monospace", "monospace"] }
  },

  "type": {
    "$type": "dimension",
    "_comment": "min/max pairs. The clamp() is computed at emit time - DTCG has no fluid primitive.",
    "step--1": { "min": { "$value": { "value": 0.833, "unit": "rem" } }, "max": { "$value": { "value": 0.9,  "unit": "rem" } } },
    "step-0":  { "min": { "$value": { "value": 1.0,   "unit": "rem" } }, "max": { "$value": { "value": 1.125,"unit": "rem" } } },
    "step-1":  { "min": { "$value": { "value": 1.2,   "unit": "rem" } }, "max": { "$value": { "value": 1.406,"unit": "rem" } } },
    "step-2":  { "min": { "$value": { "value": 1.44,  "unit": "rem" } }, "max": { "$value": { "value": 1.758,"unit": "rem" } } },
    "step-3":  { "min": { "$value": { "value": 1.728, "unit": "rem" } }, "max": { "$value": { "value": 2.197,"unit": "rem" } } },
    "step-4":  { "min": { "$value": { "value": 2.074, "unit": "rem" } }, "max": { "$value": { "value": 2.746,"unit": "rem" } } },
    "step-5":  { "min": { "$value": { "value": 2.488, "unit": "rem" } }, "max": { "$value": { "value": 3.433,"unit": "rem" } } }
  },

  "space": {
    "$type": "dimension",
    "base": { "$value": { "value": 0.25, "unit": "rem" } },
    "1":  { "$value": { "value": 0.25, "unit": "rem" } },
    "2":  { "$value": { "value": 0.5,  "unit": "rem" } },
    "3":  { "$value": { "value": 0.75, "unit": "rem" } },
    "4":  { "$value": { "value": 1,    "unit": "rem" } },
    "6":  { "$value": { "value": 1.5,  "unit": "rem" } },
    "8":  { "$value": { "value": 2,    "unit": "rem" } },
    "12": { "$value": { "value": 3,    "unit": "rem" } },
    "16": { "$value": { "value": 4,    "unit": "rem" } },
    "24": { "$value": { "value": 6,    "unit": "rem" } }
  },

  "radius": {
    "$type": "dimension",
    "sm": { "$value": { "value": 0.25,  "unit": "rem" } },
    "md": { "$value": { "value": 0.5,   "unit": "rem" } },
    "lg": { "$value": { "value": 0.75,  "unit": "rem" } },
    "xl": { "$value": { "value": 1.25,  "unit": "rem" } },
    "full": { "$value": { "value": 9999, "unit": "px" } }
  },

  "shadow": {
    "$type": "shadow",
    "sm": {
      "$value": {
        "color": { "colorSpace": "oklch", "components": [0.21, 0.006, 286], "alpha": 0.06 },
        "offsetX": { "value": 0, "unit": "px" },
        "offsetY": { "value": 1, "unit": "px" },
        "blur":    { "value": 2, "unit": "px" },
        "spread":  { "value": 0, "unit": "px" }
      }
    },
    "md": {
      "$value": {
        "color": { "colorSpace": "oklch", "components": [0.21, 0.006, 286], "alpha": 0.10 },
        "offsetX": { "value": 0,  "unit": "px" },
        "offsetY": { "value": 4,  "unit": "px" },
        "blur":    { "value": 12, "unit": "px" },
        "spread":  { "value": -2, "unit": "px" }
      }
    }
  },

  "duration": {
    "$type": "duration",
    "instant": { "$value": { "value": 80,  "unit": "ms" } },
    "fast":    { "$value": { "value": 150, "unit": "ms" } },
    "normal":  { "$value": { "value": 250, "unit": "ms" } },
    "slow":    { "$value": { "value": 400, "unit": "ms" } }
  },

  "ease": {
    "$type": "cubicBezier",
    "standard": { "$value": [0.2, 0, 0, 1] },
    "out":      { "$value": [0.16, 1, 0.3, 1] },
    "in":       { "$value": [0.4, 0, 1, 1] },
    "spring":   { "$value": [0.34, 1.56, 0.64, 1] }
  }
}
```

Everything in that file is verified against the DTCG spec:
- `color.$value` is an object with `colorSpace`, `components`, optional `alpha`
  (0-1) and optional `hex` (6-digit fallback). Valid `colorSpace` values are
  `srgb`, `srgb-linear`, `hsl`, `hwb`, `lab`, `lch`, `oklab`, `oklch`,
  `display-p3`, `a98-rgb`, `prophoto-rgb`, `rec2020`, `xyz-d65`, `xyz-d50`. For
  `oklch` the components are `[L, Chroma, Hue]` with L in `[0,1]`, Chroma in
  `[0, inf)`, Hue in `[0, 360)`.
- `dimension.$value` is `{ "value": <number>, "unit": "rem" | "px" }`.
- `duration.$value` is `{ "value": <number>, "unit": "ms" | "s" }`.
- `cubicBezier.$value` is a four-number array `[P1x, P1y, P2x, P2y]`; x is
  restricted to `[0,1]`, y is unrestricted.
- `shadow` is a composite of `color`, `offsetX`, `offsetY`, `blur`, `spread`.
- `$type` on a group is inherited by its children, which is why each group above
  declares it once.
- References use `"{group.token}"` syntax, e.g. `"$value": "{color.accent}"`.

**The one honest gap: DTCG cannot express `clamp()`.** There is no fluid-dimension
type. So fluid type is stored as min/max dimension pairs and the `clamp()` is
computed at emit time. That is the Utopia model, whose generated CSS looks exactly
like:

```css
--step-0: clamp(1.125rem, 1.0739rem + 0.2273vw, 1.25rem);
```

The middle term is `min + (max - min) * (100vw - minVw) / (maxVw - minVw)`,
algebraically flattened to `<rem> + <vw>`. Generate it once from the min/max pair
and the two viewport bounds; do not try to store it as a token.

### How each target consumes the same file

**Target A - plain CSS custom properties (the universal target).** This is what
every other target is built from, and for many projects it is the only artefact
you need.

```css
/* tokens.css - emitted, or hand-written */
:root {
  color-scheme: light dark;

  --color-bg:        oklch(0.99 0.004 106);
  --color-fg:        oklch(0.21 0.006 286);
  --color-muted:     oklch(0.55 0.014 286);
  --color-surface:   oklch(0.97 0.003 106);
  --color-border:    oklch(0.92 0.004 286);
  --color-accent:    oklch(0.62 0.19 259);
  --color-accent-fg: oklch(0.99 0 0);
  --color-danger:    oklch(0.58 0.22 27);

  --font-sans:    Inter, ui-sans-serif, system-ui, sans-serif;
  --font-display: "Instrument Serif", ui-serif, Georgia, serif;
  --font-mono:    "JetBrains Mono", ui-monospace, monospace;

  --step--1: clamp(0.833rem, 0.806rem + 0.136vw, 0.9rem);
  --step-0:  clamp(1rem,     0.949rem + 0.256vw, 1.125rem);
  --step-1:  clamp(1.2rem,   1.116rem + 0.421vw, 1.406rem);
  --step-2:  clamp(1.44rem,  1.31rem  + 0.651vw, 1.758rem);
  --step-3:  clamp(1.728rem, 1.536rem + 0.96vw,  2.197rem);
  --step-4:  clamp(2.074rem, 1.799rem + 1.376vw, 2.746rem);
  --step-5:  clamp(2.488rem, 2.101rem + 1.935vw, 3.433rem);

  --space-1: 0.25rem;  --space-2: 0.5rem;  --space-3: 0.75rem;
  --space-4: 1rem;     --space-6: 1.5rem;  --space-8: 2rem;
  --space-12: 3rem;    --space-16: 4rem;   --space-24: 6rem;

  --radius-sm: 0.25rem; --radius-md: 0.5rem; --radius-lg: 0.75rem;
  --radius-xl: 1.25rem; --radius-full: 9999px;

  --shadow-sm: 0 1px 2px 0 oklch(0.21 0.006 286 / 0.06);
  --shadow-md: 0 4px 12px -2px oklch(0.21 0.006 286 / 0.10);

  --duration-instant: 80ms;  --duration-fast: 150ms;
  --duration-normal: 250ms;  --duration-slow: 400ms;

  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --ease-out:      cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in:       cubic-bezier(0.4, 0, 1, 1);
  --ease-spring:   cubic-bezier(0.34, 1.56, 0.64, 1);
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-instant: 0ms; --duration-fast: 0ms;
    --duration-normal: 0ms;  --duration-slow: 0ms;
  }
}
```

`oklch()` is supported in Chrome 111+, Firefox 113+, Safari 15.4+ and Edge 111+,
around 90% global as of mid-2026 - so ship the `hex` fallback from the token file
where the audience demands it, either as a preceding declaration or via
`@supports not (color: oklch(0 0 0))`.

**Target B - Tailwind v4.** The token names map onto Tailwind's namespaces almost
one-to-one. Two ways to write it:

```css
/* theme.css - option 1: values live in @theme, :root gets them for free */
@import "tailwindcss";

@theme {
  --color-bg: oklch(0.99 0.004 106);
  --color-accent: oklch(0.62 0.19 259);
  --font-sans: Inter, ui-sans-serif, system-ui, sans-serif;
  --text-step-0: clamp(1rem, 0.949rem + 0.256vw, 1.125rem);
  --spacing: 0.25rem;
  --radius-md: 0.5rem;
  --shadow-md: 0 4px 12px -2px oklch(0.21 0.006 286 / 0.10);
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
}
```

```css
/* option 2: tokens.css stays canonical, @theme just re-exports it as utilities */
@import "tailwindcss";
@import "./tokens.css";

@theme inline {
  --color-bg:     var(--color-bg);
  --color-accent: var(--color-accent);
  --font-sans:    var(--font-sans);
  --radius-md:    var(--radius-md);
}
```

Option 2 is the stack-agnostic one: `tokens.css` is the source of truth, works
untouched in a Django template, and `@theme inline` only exists to mint the
utility classes. `@theme inline` is the documented way to make the generated
utility use the referenced variable's value rather than a reference to the theme
variable. Confirmed namespaces that matter here: `--color-*`, `--font-*`,
`--text-*`, `--font-weight-*`, `--tracking-*`, `--leading-*`, `--breakpoint-*`,
`--container-*`, `--spacing-*`, `--radius-*`, `--shadow-*`, `--inset-shadow-*`,
`--drop-shadow-*`, `--blur-*`, `--perspective-*`, `--ease-*`, `--animate-*`.
`--color-*: initial;` clears a whole namespace; `--*: initial;` clears everything.

**Target C - Tailwind v3.** The config points at the same custom properties:

```js
// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{html,js,jsx,ts,tsx,vue,svelte}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--color-bg)",
        fg: "var(--color-fg)",
        accent: "var(--color-accent)",
      },
      fontFamily: { sans: "var(--font-sans)" },
      borderRadius: { md: "var(--radius-md)" },
      boxShadow: { md: "var(--shadow-md)" },
      transitionTimingFunction: { standard: "var(--ease-standard)" },
    },
  },
};
```

Caveat: opacity modifiers (`bg-accent/50`) do not work against a plain
`var(--x)` colour in v3 unless the variable holds bare channel values and the
config uses the `<alpha-value>` placeholder. If the project needs those, either
upgrade to v4 or store colours channel-wise. This is v3-only friction and is a
reason to prefer v4 where you have the choice.

**Target D - SCSS variables.** Emit alongside, never instead of, the custom
properties - SCSS values are compile-time and cannot respond to a theme switch:

```scss
// _tokens.scss
$color-accent: oklch(0.62 0.19 259);
$radius-md: 0.5rem;
$duration-fast: 150ms;
```

**Target E - shadcn registry theme item.** When the target is a shadcn project,
the tokens can be *installed* rather than pasted, because `registry-item.json`
carries a `cssVars` block:

```json
{
  "$schema": "https://ui.shadcn.com/schema/registry-item.json",
  "name": "acme-theme",
  "type": "registry:theme",
  "cssVars": {
    "theme": { "font-heading": "Instrument Serif, ui-serif, Georgia, serif" },
    "light": { "brand": "oklch(0.62 0.19 259)", "radius": "0.5rem" },
    "dark":  { "brand": "oklch(0.68 0.17 259)" }
  }
}
```

Valid `type` values: `registry:base`, `registry:block`, `registry:component`,
`registry:font`, `registry:lib`, `registry:hook`, `registry:ui`, `registry:page`,
`registry:file`, `registry:style`, `registry:theme`, `registry:item`. The item can
also carry `dependencies`, `devDependencies`, `registryDependencies` (bare names,
`@namespace/name`, or URLs), `files`, and a `css` block for `@layer`,
`@keyframes`, `@plugin` and `@utility` rules.

**Target F - Panda / vanilla-extract / StyleX.** These want tokens in their own
config, so emit into it rather than into `:root`:
- Panda: `defineConfig({ theme: { tokens: { colors: { accent: { value: "..." } } } } })` in `panda.config.ts`.
- vanilla-extract: `createGlobalThemeContract` / `createTheme` in a `*.css.ts`.
- StyleX: `stylex.defineVars({ ... })` in a `*.stylex.ts`.
(Exact call signatures UNVERIFIED in this pass - confirm against each library's
docs before emitting.)

**Target G - Angular Material 3.** Set `--mat-sys-*` at `:root` from the same
tokens - `mat.theme(...)` emits only CSS custom properties with no added selector
specificity, so plain overrides at `:root` cascade into every component.

**Target H - Web components (Web Awesome, Kelp, Franken UI).** They read CSS
custom properties directly; map your `--color-accent` onto the library's own
variable names at `:root`. No build step, no generator.

### One file, N targets: the tooling

| Tool | Version / licence | DTCG support | Emits | When to pick it |
|---|---|---|---|---|
| **Nothing** (hand-write `tokens.css`) | - | n/a | plain CSS custom properties | **Default.** One stack, one target. The output is ~50 lines; a generator that produces 50 lines is the build step you get paged about. |
| Terrazzo (ex Cobalt) | `@terrazzo/cli@2.7.1`, MIT | claims full DTCG including 2025.10 | CSS, Sass, JS/TS, CSS-in-JS, Tailwind v4 `@theme`, vanilla-extract, Storybook, Swift | **Pick this when you need Tailwind v4 `@theme` generated from tokens.** It is the only tool with a first-class Tailwind v4 plugin. |
| Style Dictionary | `style-dictionary@5.5.3`, Apache-2.0 | first-class since v4; v5 targets 2025.10 but **the docs state 2025.10 is not fully supported yet** | `css/variables`, `scss/variables`, `scss/map-flat`, `scss/map-deep`, `less/variables`, `stylus/variables`, `javascript/module`, `javascript/es6`, `javascript/esm`, `typescript/es6-declarations`, `typescript/module-declarations`, `android/resources`, `ios-swift/class.swift`, `flutter/class.dart`, `compose/object`, `json`, `json/nested`, `json/flat` | Pick this when native platforms (iOS/Android/Flutter/Compose) are in scope. Biggest ecosystem, but lagging on the newest spec revision. |
| Open Props | `open-props@1.7.23`, MIT | no (it is not a generator) | 500+ ready-made custom properties: `--size-1..15`, `--size-fluid-1..10`, `--font-size-00..8`, `--radius-1..6`, `--radius-round`, `--shadow-1..6`, `--ease-1..5`, `--gray-0..12`, `--animation-fade-in` etc. | Pick this instead of authoring a scale when the direction does not demand a bespoke one. `@import "open-props/style";` (npm) or `@import "https://unpkg.com/open-props";` (CDN). Framework-agnostic, pure CSS. |

Real Terrazzo config, verbatim from its docs:

```ts
// terrazzo.config.ts
import { defineConfig } from "@terrazzo/cli";
import css from "@terrazzo/plugin-css";
import tailwind from "@terrazzo/plugin-tailwind";

export default defineConfig({
  outDir: "./tokens/",
  plugins: [
    css({ skipBuild: true, permutations: [{ theme: "light" }, { theme: "dark" }] }),
    tailwind({
      template: "tailwind.template.css",
      filename: "tailwind-theme.css",
      theme: {
        color: ["color.*"],
        font: { sans: "typography.family.base" },
        spacing: ["spacing.*"],
        radius: ["borderRadius.*"],
      },
    }),
  ],
});
```

which emits:

```css
@theme {
  --color-blue-0: #ddf4ff;
  /* ... */
}
```

CLI: `npx tz init`, `npx tz build`, `npx tz lint`, `npx tz check <file>`,
`npx tz bundle <file> --output <file>`.

Style Dictionary config shape:

```json
{
  "platforms": {
    "web": {
      "transformGroup": "web",
      "files": [
        { "format": "css/variables", "destination": "tokens.css" },
        { "format": "scss/variables", "destination": "_tokens.scss" },
        { "format": "javascript/es6", "destination": "tokens.js" }
      ]
    }
  }
}
```

---

## 4. The 21st.dev / magic MCP question

### What it is today

The `magic-mcp` repo (https://github.com/21st-dev/magic-mcp) is now **a thin
compatibility proxy**. The active project is a unified "21st MCP" maintained
separately. Its own README says the tool lets you "search 10,000+ React/Tailwind
components, generate new UI with AI, and publish your own - right from your
editor."

Critically for a rebuild: **the `/ui`, `/21` and `/logo` triggers were never
protocol features.** The README states they were "a convention of the legacy
tools' descriptions". Today you talk to it in natural language and it exposes
tools like `search`, `generate`, `get_inspiration`, plus tools for templates,
bookmarks and team libraries. `generate` and `iterate_generation` are only listed
when AI access is enabled on the account - so a pipeline step that assumes
`generate` exists will silently degrade to search-only on a free key.

### Framework coverage

**React and Tailwind CSS, explicitly.** That is the whole catalogue. For a
stack-agnostic pipeline this is disqualifying as a *primary* step - roughly half
the stacks in section 2 cannot consume its output without a rewrite.

### Pricing

Free tier: 100 credits/month, reported as roughly 5 component generations. Pro
$20/mo (about 50 generations), Pro Plus $40/mo; annual billing $16/$32. Credits
reset per billing cycle. Sources are third-party review sites plus
https://help.21st.dev/magic-chat/pricing - **the exact current numbers are
UNVERIFIED**, the help page itself was not fetched successfully in this pass.

### Current state for this user

The MCP is configured but failing to connect:
`Not authenticated - your API key is missing or was reset` from
https://21st.dev/mcp. That is a connection/auth failure, not an absent capability
- the key needs regenerating and the `x-api-key` / `Bearer` header updating in the
MCP config. But note what the failure demonstrates: **a paid, keyed, rate-limited,
single-framework third-party service is a single point of failure for the whole
design pipeline.** Today it takes the pipeline down.

### The alternative: shadcn's own MCP

**Confirmed: shadcn ships an official MCP server** (https://ui.shadcn.com/docs/mcp).

```bash
pnpm dlx shadcn@latest mcp init --client claude
```

Manual config:

```json
{
  "mcpServers": {
    "shadcn": { "command": "npx", "args": ["shadcn@latest", "mcp"] }
  }
}
```

It browses, searches and installs from registries, reads `components.json` for
registry configuration including namespaced and private registries, and installs
through the shadcn CLI so files land in the project's actual layout. No API key,
no credits, no rate limit, no vendor account. shadcn-vue ships its own MCP too
(https://www.shadcn-vue.com/docs/mcp). Community registry MCPs also exist
(`reuvenaor/shadcn-registry-manager`, `Rachidhssin/shadcn-registry-mcp`) but the
first-party one makes them unnecessary.

### Verdict

**Demote magic MCP to an optional React+Tailwind-only inspiration step. Promote
the shadcn MCP to the primary sourcing step where a registry exists.**

Reasoning:
- The pipeline must never hard-fail on a third-party auth error. Today it does.
- magic MCP's catalogue is React+Tailwind only, so it cannot be the primary step
  in a stack-agnostic pipeline by construction.
- shadcn's MCP is free, keyless, first-party, reads the project's own
  `components.json`, and reaches any registry - including registries you author -
  and shadcn's registry docs state the format "works with any project type and any
  framework, and is not limited to React".
- Keep magic MCP for what it is genuinely good at: *inspiration* and generation of
  novel React+Tailwind visuals that no registry has. Gate it behind
  `detected stack == React + Tailwind AND magic MCP connected`. If either is
  false, skip the step and continue; do not stop the pipeline.

Do not replace it outright - a 10,000-component visual catalogue has no free
equivalent, and for React+Tailwind marketing work it is still the fastest path
from "locked direction" to "something on screen".

---

## 5. What a stack-agnostic build step looks like

Given a locked token set and a detected stack, the agent runs a fixed cascade per
component. It is the ponytail ladder applied to UI:

1. **Does this component need to exist?** A `<details>` element is an accordion.
   `<dialog>` is a modal with a working focus trap and a backdrop. `<input
   type="date">` is a date picker. `popover` + anchor positioning is a dropdown.
   If a native element does the job, style it with the tokens and stop. This rung
   is skipped constantly and it is the biggest single source of bloat.

2. **Is it already in the repo?** Grep `aliases.ui` from `components.json`, or
   `src/components/ui/`, `app/components/`, `resources/views/components/`,
   `lib/components/`. Extend the existing one. Two Buttons is worse than one
   imperfect Button.

3. **Is it in an installed library?** If Gate 3 found Mantine, PrimeVue,
   Angular Material or Nuxt UI, use its component and retheme it through the
   token layer. Never introduce a second library to get one component.

4. **Copy from a registry.** In preference order:
   - shadcn MCP / `npx shadcn add <name|url>` when `components.json` exists.
   - The stack's own copy-in CLI: `shadcn-vue`, `shadcn-svelte`, Starwind,
     Spartan `helm`, shadcn-templ.
   - Basecoat / daisyUI / Pines markup for template stacks.
   Copying is preferred over depending because the copied source is then bound to
   your tokens and cannot drift on someone else's release schedule.

5. **Generate.** React+Tailwind only, and only if magic MCP is connected: use it
   for genuinely novel visuals with no registry equivalent. Then rewrite the
   result's hard-coded values to token references before it lands.

6. **Hand-roll.** Only now.

### The rule for when hand-rolling is correct

Hand-roll when **all four** hold:

1. Rungs 1-5 produced nothing that fits, or everything they produced needs more
   than about half its code rewritten to match the locked direction.
2. The component's behaviour is genuinely simple - no focus trap, no roving
   tabindex, no collision-aware positioning, no live region, no virtualisation.
   Any one of those means take a headless dependency (Base UI, Radix, Ark UI,
   React Aria, Reka UI, Bits UI) and hand-roll only the skin.
3. It is specific to this product. A bespoke pricing comparator is worth writing.
   A Select is not.
4. You can name the accessibility contract it must meet and test it. If you
   cannot, you are about to reimplement a combobox badly.

Corollary: **hand-rolling the *skin* is almost always right, hand-rolling the
*behaviour* almost always wrong.** The token layer exists precisely so the skin is
cheap.

### Where the tokens land, per emit target

Landing order, once per project, before any component work:

1. Write `tokens.css` (or the stack's native token home) with the `:root` block
   from section 3, Target A.
2. Wire it into the stack's global stylesheet import.
3. Emit the stack-specific bridge only if needed: `@theme inline` for Tailwind v4,
   `theme.extend` for v3, `mat.theme` overrides for Angular Material, `theme.json`
   for a WordPress block theme, a `panda.config.ts` token block for Panda.
4. Only then start components. Every component that lands after this point
   references `var(--...)` or a utility derived from it - **zero literal colour,
   radius, duration or font values in component source.** That is the single
   invariant that makes the direction portable, and it is checkable: grep the
   component tree for `#[0-9a-f]{3,8}`, `rgb(`, `oklch(`, `[0-9]+ms` and
   `cubic-bezier(` outside the token file and assert the count is zero.

---

## The stack matrix

| Stack | Detection signal (ordered) | Component source | Token target |
|---|---|---|---|
| Next.js + Tailwind v4 + shadcn | `next` dep + `next.config.*`; `components.json` w/ shadcn schema; CSS entry has `@import "tailwindcss"` | shadcn MCP / `npx shadcn add`; Origin UI, Magic UI, Aceternity; magic MCP optional | `tokens.css` `:root` + `@theme inline` bridge; or a `registry:theme` item's `cssVars` |
| Next.js / React + Tailwind v3 | `tailwind.config.*` w/ `content:` AND CSS entry has `@tailwind base;` | same as above (verify v3 compat) | `tokens.css` `:root` + `theme.extend` mapping to `var(--x)` |
| React + CSS Modules / plain CSS | `react` dep, no `tailwindcss`; `**/*.module.css` hits | Base UI (`@base-ui-components/react`, MIT, 1.0.0-rc.0) or Radix Primitives; Mantine if styled wanted | `tokens.css` `:root` only |
| React + Panda / vanilla-extract / StyleX | `@pandacss/dev` + `panda.config.ts` / `*.css.ts` / `stylex.create(` | Ark UI or Park UI (Panda); Radix or Base UI otherwise | library's own token config, generated from the same DTCG file |
| Vue / Nuxt | `nuxt` + `nuxt.config.*`, else `vue` + `vite.config.*` | **Nuxt UI 4** (MIT, free, Reka UI + Tailwind); shadcn-vue for shadcn parity; Reka UI or Ark UI Vue headless; PrimeVue for enterprise breadth | `tokens.css` `:root` + `@theme inline` (Nuxt UI/shadcn-vue are Tailwind v4) |
| Svelte / SvelteKit | `@sveltejs/kit` or `svelte.config.js` | **shadcn-svelte** (MIT) on Bits UI; Bits UI or `melt` headless; Skeleton if a full kit is wanted | `tokens.css` `:root` + `@theme inline` |
| Astro (no islands) | `astro` + `astro.config.*`, no `@astrojs/{react,vue,svelte}` | Starwind UI (`@starwind-ui/astro`); Basecoat; daisyUI; Web Awesome web components | `tokens.css` `:root`; `@theme inline` if Tailwind present |
| Astro (with islands) | `astro` + `@astrojs/react` / `@astrojs/vue` | the island framework's library, inside `client:*`; daisyUI for a shared skin across islands | one `tokens.css` shared by `.astro` and every island |
| Angular | `@angular/core` + `angular.json` | **Angular Material** (`--mat-sys-*` tokens, easiest to retheme); Spartan UI if Tailwind is wanted; PrimeNG for breadth | `:root` overrides of `--mat-sys-*`, generated from the same tokens |
| Plain HTML / no framework | bare `index.html`, no manifest | Basecoat (needs Tailwind v4); Pico CSS (classless); Web Awesome (web components); Kelp (alpha); Open Props for the scale | `tokens.css` `:root`, linked directly |
| Django | `manage.py` + `settings.py`, `django` in requirements/pyproject | shadcn-django (Tailwind + Alpine); Basecoat + Alpine; daisyUI | `tokens.css` in `static/`, `{% load static %}` into the base template |
| Jinja / Flask / FastAPI | `jinja2`/`flask` dep + `templates/**/*.html` | **Basecoat** (ships Jinja macros); daisyUI | `tokens.css` in `static/` |
| Laravel Blade | `composer.json` w/ `laravel/framework`, `resources/views/**/*.blade.php` | `shadcn-blade/ui` or `bjnstnkvc/shadcn-ui`; Basecoat; Flux if Livewire is present | `tokens.css` through Vite; `@theme` if Tailwind v4 |
| Rails ERB | `Gemfile` w/ `rails`, `app/views/**/*.erb` | shadcn.rails-components.com; Basecoat + Stimulus; ViewComponent for structure | `tokens.css` through Propshaft/Sprockets or cssbundling |
| Phoenix | `mix.exs` w/ `phoenix`, `**/*.heex` | `pine_ui_phoenix` (42 Pines elements as LiveView components); Basecoat | `tokens.css` in `assets/css/` (esbuild/Tailwind pipeline) |
| Go templates / templ | `go.mod`; `**/*.templ` vs `**/*.tmpl` | shadcn-templ (templ, Alpine + Tailwind); Basecoat markup for stdlib templates | `tokens.css` served as a static asset |
| WordPress block theme | `wp-config.php` + theme `theme.json` | core blocks + block patterns; Basecoat for custom parts | `theme.json` `settings.color.palette` / `typography` / `spacing` -> WP emits `--wp--preset--*` |
| WordPress classic theme | `style.css` with a `Theme Name:` header, `functions.php`, no `theme.json` | Basecoat or a CSS kit; Alpine for behaviour | `tokens.css` enqueued via `wp_enqueue_style` |
| Static site generator (Hugo / Jekyll / Eleventy) | `hugo.toml`+`layouts/` / `_config.yml`+`_layouts/` / `.eleventy.js` | Basecoat, daisyUI, Pico, Open Props | `tokens.css` in the assets pipeline |

---

## Recommended pipeline steps

Instructions for the agent. Run in order; do not skip step 1 or step 3.

**Step 1 - Detect.** Run the Gate 0-5 cascade from section 1. Write the result to
the session as a five-line block and do not proceed until it is filled in:

```
framework:   <e.g. SvelteKit | Django | Astro(no islands) | none>
styling:     <Tailwind v4 | Tailwind v3 | CSS Modules | Panda | plain CSS | ...>
tokens live: <path to the CSS entry, theme.json, or "none yet">
components:  <existing lib or "none"> at <aliases.ui or discovered dir>
behaviour:   <Alpine | htmx | Stimulus | Livewire | framework runtime | none>
```

If two gates disagree (for example `tailwind.config.js` exists but the CSS entry
says `@import "tailwindcss"`), the CSS entry wins and you say so in one line.

**Step 2 - Lock the direction.** Unchanged from today: `design-dna` when the user
points at a reference, otherwise `ui-ux-pro-max` for style + palette + font
pairing. Reuse a saved project direction if one exists; otherwise propose two and
wait. The output of this step is *not* Tailwind classes - it is the nine token
groups from section 3.

**Step 3 - Emit the token layer, once, before any component work.**

1. Write `tokens.css` with the full `:root` block (section 3, Target A). Use OKLCH
   with hex fallbacks. Include the `prefers-reduced-motion` duration override.
2. Wire it into the stack's global stylesheet.
3. Emit the stack bridge only if the detection says one is needed:
   - Tailwind v4 -> `@theme inline { --color-x: var(--color-x); ... }`
   - Tailwind v3 -> `theme.extend` entries pointing at `var(--...)`
   - Angular Material -> `:root` overrides of `--mat-sys-*`
   - WordPress block theme -> `theme.json` presets
   - Panda / vanilla-extract / StyleX -> that library's token config
4. Write `tokens.json` (DTCG 2025.10) **only if** there are two or more emit
   targets, a native platform is in scope, or the user asked for a portable token
   file. One stack, one target, no generator - hand-written CSS is the correct
   rung. When you do need a generator, use Terrazzo if Tailwind v4 output is
   required, Style Dictionary if iOS/Android/Flutter output is required.

**Step 4 - Source components, per component, down the ladder in section 5.**
Native element -> existing repo component -> installed library -> registry copy ->
generate -> hand-roll. Log which rung each component came from; if more than about
a third were hand-rolled, stop and say why, because that usually means the wrong
component source was chosen at step 4.

Registry commands by stack: `npx shadcn add <name|url>` (React, and any project
with `components.json`), `npx shadcn-vue@latest add`, `npx shadcn-svelte@latest
add`, `npx starwind@latest add` (Astro), `npx @spartan-ng/cli add` (Angular; CLI
name UNVERIFIED - check `spartan.ng` docs), copy-paste HTML for Basecoat / daisyUI
/ Pines.

**Step 5 - The magic MCP step is optional and gated.** Run it only when the
detected stack is React + Tailwind AND the MCP is connected. If it is not
connected, print one line ("21st magic MCP not connected - skipping inspiration
step; regenerate the key at 21st.dev/mcp") and continue. Never block the pipeline
on it. Prefer the shadcn MCP (`pnpm dlx shadcn@latest mcp init --client claude`)
as the primary sourcing tool - it is free, keyless, first-party, reads
`components.json`, and reaches any registry.

**Step 6 - Assemble.** `frontend-design` + `impeccable`, unchanged.

**Step 7 - Motion.** Only where it earns its place. All durations and easings come
from `--duration-*` and `--ease-*`; no literal `300ms` or `ease-in-out` in
component source.

**Step 8 - Audit before presenting.** `/impeccable critique` (UX) AND `/impeccable
audit` (a11y/perf/responsive) AND a motion audit. Add one stack-agnostic check
that did not exist before:

```
grep -rEn '#[0-9a-fA-F]{3,8}\b|rgba?\(|oklch\(|hsl\(|[0-9]+ms\b|cubic-bezier\(' \
  <component dirs> --include='*.tsx' --include='*.jsx' --include='*.vue' \
  --include='*.svelte' --include='*.astro' --include='*.html' \
  --include='*.blade.php' --include='*.erb' --include='*.heex' --include='*.templ' \
  | grep -v tokens.css
```

Assert the match count is zero and print the offenders on failure. A non-zero
count means the direction is not actually portable, whatever the screenshots look
like.
