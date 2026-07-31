# Skills

Skills installed outside the plugin system. Each needs to be reinstalled manually on a new machine.

## Installed versions (last verified 2026-07-29)

| Thing | Version | Update with |
|-------|---------|-------------|
| gstack | 1.60.1.0 | `git -C ~/.claude/skills/gstack merge --ff-only origin/main && ./setup` |
| jjstack | 0.36.0 | same, in `~/.claude/skills/jjstack` (stash the local `hooks/auto-approve-safe.sh` tweak first) |
| get-shit-done-cc | 1.34.2 **pinned** | do NOT run `npx get-shit-done-cc` - see below |
| impeccable | 4.0.3 | `npx skills add pbakaus/impeccable --skill impeccable -a claude-code -g -y` |
| graphify | 0.9.29 | `pipx upgrade graphifyy && graphify install claude` |
| @21st-dev/cli | 1.15.0 | `npm install -g @21st-dev/cli@latest` |
| Claude Code | 2.1.220 | `claude update` |

Everything else (skill-router, the three taste skills, design-motion-principles,
anthropic-security-review, getsentry-skills, the ECC cherry-picks) was verified against
upstream on 2026-07-29 and is current.

**Order matters on upgrade:** gstack's `./setup` overwrites the shared skill symlinks
(`qa`, `review`, `ship`, `office-hours`, …) to point at gstack. Always run gstack's setup
**first**, then jjstack's, which re-points them at the jjstack wrappers. `/jjstack-repair`
fixes it if you get the order wrong.

## Skill frameworks

These are full systems with many sub-skills. **You only need to install jjstack** - it installs gstack automatically as a declared dependency.

### jjstack (installs gstack automatically)
**Source:** https://github.com/JesperJurcenoks/jjstack
**Install:**
```bash
git clone git@github.com:JesperJurcenoks/jjstack.git ~/.claude/skills/jjstack
cd ~/.claude/skills/jjstack && ./setup
```
jjstack's setup script checks for gstack and clones + sets it up from `garrytan/gstack` if not present. You do not need to install gstack separately.

**What jjstack adds:** A product/UX layer on top of gstack. Adds opinionated skills for code quality, product thinking, and developer experience. All jjstack skills are symlinked into `~/.claude/skills/`.

**New in 0.36.0** (added 2026-07-29): `/antigravity` and `/deepseek` (second-opinion review
via Google AGY and DeepSeek/OpenCode, alongside the existing `/codex`), `/consensus`
(four-vendor panel), `/groom` (dedup and consolidate memories/skills), `/plan-edit`
(surgical, sectioned plan editing with track-changes diffs), `/qa-build-loop` (replaces the
removed `/qa-loop` - unattended TDD loop between iris-qa and a code worker),
`/reconnect-mcp`, and the session-continuity trio `/save-and-clear`, `/save-and-exit`,
`/resume-from-clear` plus `/rollover` that ties them together.

**Known upstream bug (0.36.0, not patched):** `bin/jjstack-gbrain-phi-lib.sh`'s
`reconstruct_cwd` cannot invert a Claude Code project slug whose path contains a dot-directory.
Claude Code encodes both `/` and `.` as `-`, so `-home-santiago--claude` should map back to
`/home/santiago/.claude` but resolves to `/home/santiago/-claude`. This surfaces as the one
`test/smoke.sh` failure ("reconstruct_cwd resolves a real path" - that test also hardcodes the
author's own `/home/jesper/...` path, so it cannot pass here either way). **Impact today: none.**
The only callers are `jjstack-memory-bridge` and `jjstack-memory-to-learnings`, both gbrain
paths, and gbrain is not installed on this machine. Left unpatched on purpose - a second local
diff inside the jjstack checkout is a maintenance cost for a dead code path. Re-check after any
jjstack upgrade, and before ever running `/setup-gbrain`.

**Local modification:** `hooks/auto-approve-safe.sh` is tuned so the Haiku safety rater only
returns HIGH for genuinely destructive commands, and MEDIUM auto-approves alongside LOW. The
diff is kept at `hooks/jjstack-auto-approve-safe.patch` in this repo so it survives an
upgrade - `git stash` before fast-forwarding jjstack, then `git stash pop`.

**What gstack adds (auto-installed):** The task management layer - `/autoplan`, `/investigate`, `/qa`, `/ship`, `/review`, `/office-hours`, `/retro`, and the browser automation system. NOT the gsd-* skills.

---

### get-shit-done-cc (GSD) - installs the gsd-* skills
**Source:** https://github.com/gsd-build/get-shit-done
**Package:** `get-shit-done-cc` on npm (by TÂCHES)
**Install:**
```bash
npx get-shit-done-cc
```
**Current version:** 1.34.2 - **deliberately pinned, do not upgrade blind.** Upstream is on
1.42.3, but the `gsd-*` skills were purged from this machine on purpose (commit `33f5b27`,
"purge dead GSD routes"). Re-running `npx get-shit-done-cc` would reinstall all 50+ of them
and undo that. Only what the hooks still need is kept.

**What is still installed and load-bearing:**
- `~/.claude/get-shit-done/` - workflow engine, references, templates (read by the `gsd-*` hooks)
- `~/.claude/gsd-file-manifest.json` - install manifest
- The `gsd-*` hooks in `~/.claude/hooks/` wired into `settings.json`

**What is NOT installed:** every `~/.claude/skills/gsd-*` skill. There are none on this
machine and that is intentional.

**Correction:** the sub-skills previously listed here (`/dev-philosophy`, `/heal`,
`/kano-model`, `/lean`, `/mcp-server`, `/new-submodule`, `/product-manager-review`,
`/python-coder`, `/qa-review`, `/receiving-code-review`, `/security-review`,
`/smart-context7`, `/smart-review`, `/smart-simplify`, `/state-doc`, `/two-stage-review`,
`/unit-test-builder`, `/verify-before-done`, `/work-order`, `/worktrees`, `/writing-skills`,
`/jj-qa`, `/github-setup`) come from **jjstack**, not GSD - they are symlinks into
`~/.claude/skills/jjstack/skills/`. Same for `/council`, which is no longer the standalone
`tsenart/council-skill` install.

---

## Routing

### skill-router
**Source:** https://github.com/chrishan17/skill-router
**Install:**
```bash
npx skills add chrishan17/skill-router/skills/skill-router -a claude-code -g -y
```
**What it does:** Organizes all installed skills into a single router entry point. Fixes trigger reliability (skills not firing when they should), reduces context bloat from too many skill descriptions loading at startup. Supports 40+ agents.
**When to use:** Always active. It intercepts skill selection so the right skill fires for each request.

---

### intent-router
**Source:** this repo — `skills/intent-router/SKILL.md`
**Install:**
```bash
mkdir -p ~/.claude/skills/intent-router
cp skills/intent-router/SKILL.md ~/.claude/skills/intent-router/SKILL.md
```
Or if cloning fresh:
```bash
git clone https://github.com/Gartner24/claude-config ~/claude-config
mkdir -p ~/.claude/skills/intent-router
cp ~/claude-config/skills/intent-router/SKILL.md ~/.claude/skills/intent-router/SKILL.md
```
**What it does:** Config-driven intent router that sits on top of `skill-router`. Reads `~/claude-config/USAGE.md` at runtime, scores the current prompt against every skill's `TRIGGERS/BLOCKS/PRIORITY` fields, and invokes the best match. Fires only on ambiguous prompts - silent pass-through otherwise.
**Requires:** `~/claude-config/USAGE.md` to exist (this repo cloned locally). Falls back to a built-in table if not found.
**Personal override rules baked in:**
- mem-search fires before anything else on memory-check signals
- council fires before implement skills on decision signals
- design-motion-principles wins over impeccable animate on motion-primary prompts
- investigate wins on all bug/error prompts
- brainstorming fires before gsd-plan-phase on vague/exploratory prompts

**To update routing when you add a skill:** add a routing block to `USAGE.md` and commit. The router reads it on next invocation.
**When to use:** Always active - fires automatically when Claude detects ambiguous intent.

---

## Decision-making

### council
**Source:** jjstack (`~/.claude/skills/jjstack/skills/council`) - **superseded** the standalone
`tsenart/council-skill` install. `~/.claude/skills/council` is now a symlink into jjstack, so it
updates with jjstack; there is nothing separate to install.
**What it does:** Runs a structured multi-perspective deliberation: independent analysis,
cross-examination, final verdict. As of jjstack 0.36.0 it also runs an automatic
"Competitor-did-it" pass when the panel returns an "impossible" verdict.
**When to use:** Architecture decisions, strategy tradeoffs, risk reviews, debugging hypotheses with multiple possible causes, launch decisions.
**Related (also jjstack):** `/consensus` runs the same idea across four *vendors* - Claude, Codex
(OpenAI), AGY/Antigravity (Google), DeepSeek - on flat-rate/free tiers.

---

## Design - typography and quality

### impeccable
**Source:** https://github.com/pbakaus/impeccable
**Install:**
```bash
npx skills add pbakaus/impeccable --skill impeccable -a claude-code -g -y
```
**What it does:** 23 design commands covering typography, color, spacing, motion, interaction, responsive, and UX writing. 27 deterministic anti-pattern rules. Built on top of `frontend-design`.
**Current version:** 4.0.3 (upgraded 2026-07-29 from a v3 snapshot)
**Key commands:** `/impeccable critique` (UX review), `/impeccable audit` (a11y/perf/responsive), `/impeccable polish`, `/impeccable shape`, `/impeccable bolder`, `/impeccable quieter`, `/impeccable distill`, `/impeccable animate`, `/impeccable live`
**When to use:** Any frontend UI work. Run `critique` **and** `audit` before shipping UI - in v4 they split: `audit` is technical only, `critique` carries the UX review.
**v4 breaking changes:** `teach` is gone - use `/impeccable init` (writes `PRODUCT.md`) and `/impeccable document` (writes `DESIGN.md` from existing code) once per project. `craft` is a deprecated alias. Subagents now ship as `.toml`/`.yaml` under `agents/` instead of `.md`.

---

## Design - motion

### design-motion-principles
**Source:** https://github.com/kylezantos/design-motion-principles
**Install:**
```bash
git clone --depth=1 https://github.com/kylezantos/design-motion-principles /tmp/dmp
mkdir -p ~/.claude/skills/design-motion-principles
cp -a /tmp/dmp/skills/design-motion-principles/. ~/.claude/skills/design-motion-principles/
rm -rf /tmp/dmp
```
> The old per-file `curl` loop was replaced on 2026-07-29 - upstream added
> `references/demo-shell.html` and `references/report-template.html`, which a fixed file list
> silently skips. Clone-and-copy picks up new files automatically.
**What it does:** Motion design through three lenses: Emil Kowalski (restraint), Jakub Krehel (production polish), Jhey Tompkins (creative). Two modes: build (create components with motion) and audit (review existing animations, generate HTML report with demos).
**When to use:** Any UI with transitions, animations, or interactive states. Run audit mode before shipping. The Emil Kowalski lens will cut unnecessary animation; use it to gut-check AI-generated motion slop.

---

## Design - visual taste

Three variants from the same repo. Install one, two, or all three depending on project direction.

### high-end-visual-design (soft)
**Source:** https://github.com/Leonxlnx/taste-skill
**Install:**
```bash
npx skills add https://github.com/Leonxlnx/taste-skill --skill "high-end-visual-design" -a claude-code -g -y
```
**Style:** Polished, calm, expensive. Soft contrast, whitespace, premium fonts, spring motion. Think Linear, Vercel, Stripe.

---

### minimalist-ui
**Source:** https://github.com/Leonxlnx/taste-skill
**Install:**
```bash
npx skills add https://github.com/Leonxlnx/taste-skill --skill "minimalist-ui" -a claude-code -g -y
```
**Style:** Editorial product UI. Restrained palette, crisp structure. Think Notion, Linear.

---

### industrial-brutalist-ui (BETA)
**Source:** https://github.com/Leonxlnx/taste-skill
**Install:**
```bash
npx skills add https://github.com/Leonxlnx/taste-skill --skill "industrial-brutalist-ui" -a claude-code -g -y
```
**Style:** Hard mechanical language. Swiss type, sharp contrast, experimental layout. BETA - use with intention.

---

## Design - comprehensive

### ui-ux-pro-max
**What it does:** 67 styles, 96 palettes, 57 font pairings, 25 chart types, 13 framework stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui). Broad design intelligence.
**When to use:** When you need style exploration or need a complete stack decision. Pairs with impeccable for quality control.

> **Full design pipeline:** `ui-ux-pro-max` -> `21st.dev`/magic MCP -> `frontend-design` + `impeccable` -> `design-motion-principles` -> audit gate. Setup and the reusable kickoff prompt are in [DESIGN-PIPELINE.md](DESIGN-PIPELINE.md).

---

## Client site build system (custom)

Custom skills + commands for the freelance website business. The full how-to lives in the build
system repo: `~/projects/freelance/website-build-templates/WORKFLOW.md`.

### astro-patterns (skill)
**What it does:** Astro static-site conventions for the freelance stack (islands/client directives,
`astro:assets`, content collections, trailing-slash/canonical hygiene, CSP-with-islands, Cloudflare
Workers-vs-Pages). Grounded in official Astro docs.
**When to use:** building or reviewing any Astro site. Auto-fires; or invoke by name.

### /design (command)
**What it does:** Runs the design pipeline: lock direction (`ui-ux-pro-max`) -> source components
(magic MCP) -> assemble (`frontend-design` + `impeccable`) -> motion (`design-motion-principles`) ->
audit. You can supply style, brand, assets, or a Figma URL; anything omitted is proposed.

### /new-site (command)
**What it does:** Orchestrates a full client website build - picks the site type, pulls the right
base template + modules + guides from the build system, scaffolds the client repo, fills variables,
and runs the build order (firing `/design`, `astro-patterns`, SEO/legal, audits, deploy). One command
instead of a checklist. See `WORKFLOW.md`.

### /monthly-ops (command)
**What it does:** Runs one client's monthly **retainer** cycle - Care base + the add-ons they bought
(SEO/AEO, Content, GBP, Reviews, Backlinks) + AI-visibility, then drafts the monthly report and hard-stops
for your review. Executes the runbooks in `website-build-templates/guides/MONTHLY-OPS-GUIDE.md`.

### seo-ops (skill)
**What it does:** Recurring SEO/AEO for a live client site (claude-seo audit, page-2 internal links, GSC
language mining, structured-data upkeep, IndexNow re-index). Run-time counterpart to SEO-GUIDE. Used by
`/monthly-ops` SEO add-on.

### content-ops (skill)
**What it does:** Writes site copy + blog content that gets a client found, in their voice, never AI slop.
Build-time page copy (for `/new-site`) and the monthly blog add-on (for `/monthly-ops`). Uses voice-dna +
anti-ai-writing; obeys SEO-GUIDE topical rules.

### voice-dna (skill) + anti-ai-writing (skill)
**What they do:** voice-dna builds a per-client voice profile from ~20 samples; anti-ai-writing is the final
de-slop pass. Both feed `content-ops`. (3rd-party, `artemnovitckii/content-skills`, MIT; tracked in
claude-config.)

### nano-banana + video-to-website + business-analyzer (skills)
**What they do:** `nano-banana` generates controlled realistic imagery via Google's Gemini (in `/brand-system`
+ assets); `video-to-website` builds a premium scroll-hero from a video as an Astro island (in `/new-site`);
`business-analyzer` structures client market/pricing/competitive discovery (in `/new-site` intake). All in
`claude-config/skills`, symlinked.

> **Skills evaluation log:** every skill considered (adopted/rejected + why + where wired) is in
> `SKILLS-EVALUATION.md`. Plugins to install: see `PLUGINS.md` (claude-seo, security-guidance).

---

## Undocumented at install time (inventoried 2026-07-29)

These are installed and working but their install command was never recorded. Source is
listed as UNKNOWN where it could not be verified from the files themselves - do not guess a
URL when reinstalling, check `skills.sh` or the tool that shipped them.

### 21st.dev skill set (7 skills)
`21st-ai`, `21st-cli-use`, `21st-design-sync`, `21st-registry`, `21st-ui-build`,
`21st-ui-explore`, `21st-ui-review`. They all drive the `21st` CLI (`@21st-dev/cli`, global
npm, currently 1.15.0), so keep the CLI current with `npm install -g @21st-dev/cli@latest`.
Distinct from the `magic` MCP: the MCP generates, the CLI searches/installs/publishes.

### Cloudflare skill set (11 skills)
**Source:** https://github.com/cloudflare/skills - Cloudflare's official skill bundle.
Installed as a batch on 2026-07-02; the source was traced back on 2026-07-29 from repo
references inside the SKILL.md files, since the install command was never recorded.

`agents-sdk`, `cloudflare`, `cloudflare-email-service`, `cloudflare-one`,
`cloudflare-one-migrations`, `durable-objects`, `sandbox-sdk`, `turnstile-spin`, `web-perf`,
`workers-best-practices`, `wrangler`.

**Install / update** (upstream's own recommendation - clone once, symlink, then `git pull`
updates all 11 at once instead of re-copying):
```bash
git clone https://github.com/cloudflare/skills ~/.config/cloudflare-skills
for s in agents-sdk cloudflare cloudflare-email-service cloudflare-one \
         cloudflare-one-migrations durable-objects sandbox-sdk turnstile-spin \
         web-perf workers-best-practices wrangler; do
  ln -sfn ~/.config/cloudflare-skills/skills/$s ~/.claude/skills/$s
done
```
The current install is a **copy**, not a symlink, so it does not self-update. Verified against
upstream on 2026-07-29: 10 of 11 byte-identical.

**`turnstile-spin` has drifted** and is the one exception. Upstream rewrote it (scripts are now
documented in the README, `SKILL.md` is canonical instead of mirroring the docs page). The local
copy also carries `scripts/fetch-secret.sh`, `scripts/worker-deploy.sh`, and a whole
`templates/worker/` scaffold that upstream no longer ships - almost certainly leftovers from the
older release, but not provably so. Refresh with:
```bash
cp -a ~/.config/cloudflare-skills/skills/turnstile-spin/. ~/.claude/skills/turnstile-spin/
```
That leaves the three orphans in place; delete them by hand once you have confirmed you did not
write them.

**Also in that repo, not installed:** `commands/build-agent.md`, `commands/build-mcp.md`,
`rules/workers.mdc`.

### Loose extras
`review-stack` (dispatches security + database + language + code reviewers in parallel),
`docs-sync` (private doc ecosystem re-sync). **Source: UNKNOWN / hand-written locally.**
(`web-perf` was previously listed here - it is Cloudflare's, see above.)

### graphify
**Source:** https://github.com/safishamsi/graphify - a Python package, not a skill repo.
**Install / update:**
```bash
pipx install graphifyy     # note the package name is graphifyy, the CLI is graphify
pipx upgrade graphifyy
graphify install claude    # (re)writes ~/.claude/skills/graphify + registers it in CLAUDE.md
```
The skill carries its own `.graphify_version`; if it drifts from the package version the CLI
warns on every run. Turns any folder into a navigable knowledge graph. Trigger: `/graphify`.

---

## Specialized

### inboundsavvy-webmaster
**What it does:** Custom skill for InboundSavvy CMS. Edit pages, sections, design system, images via natural language.
**When to use:** Only for InboundSavvy website work.

### anthropic-security-review
**What it does:** Python-based security review toolkit from Anthropic. Not a SKILL.md skill - a standalone tool.
**Location:** `~/.claude/skills/anthropic-security-review/`

### getsentry-skills
**What it does:** Sentry integration skills - agents aware of Sentry error tracking.
**Location:** `~/.claude/skills/getsentry-skills/`

---

## ECC cherry-pick (affaan-m/ecc)

**Source:** https://github.com/affaan-m/ecc
**Install method:** Manual cherry-pick - NOT using install.sh. Cloned to /tmp/ecc and copied selected files only.
**What was NOT installed:** hooks/, scripts/, settings.json, MCP configs, ECC-specific skills (configure-ecc, security-scan agent, instinct system, continuous-learning). All of those conflict with jjstack/gsd/claude-mem.

### Agents installed (~/.claude/agents/)

Language reviewers and build resolvers:
- `go-reviewer.md`, `go-build-resolver.md`
- `python-reviewer.md`
- `typescript-reviewer.md`
- `rust-reviewer.md`, `rust-build-resolver.md`
- `java-reviewer.md`, `java-build-resolver.md`
- `build-error-resolver.md` (generic)

General purpose:
- `architect.md`, `code-architect.md`, `code-reviewer.md`, `code-explorer.md`
- `planner.md`, `tdd-guide.md`, `security-reviewer.md`
- `refactor-cleaner.md`, `doc-updater.md`, `docs-lookup.md`
- `e2e-runner.md`, `loop-operator.md`
- `database-reviewer.md`, `performance-optimizer.md`
- `silent-failure-hunter.md`, `chief-of-staff.md`
- `pr-test-analyzer.md`, `a11y-architect.md`

### Rules installed (~/.claude/rules/ecc/)

Language-specific "must always / must never" guidelines. Not auto-loaded - add @imports to project CLAUDE.md:
```
@~/.claude/rules/ecc/common/coding-style.md
@~/.claude/rules/ecc/<language>/coding-style.md
```
Languages: common, typescript, python, golang, rust, java, web

### Skills installed (~/.claude/skills/)

Language patterns: `golang-patterns`, `golang-testing`, `python-patterns`, `python-testing`, `rust-patterns`, `rust-testing`, `java-coding-standards`, `jpa-patterns`, `fastapi-patterns`, `django-patterns`

Frontend/Backend: `frontend-patterns`, `backend-patterns`, `api-design`, `nextjs-turbopack`, `nestjs-patterns`, `vite-patterns`, `prisma-patterns`

Infrastructure: `deployment-patterns`, `docker-patterns`, `postgres-patterns`, `database-migrations`, `redis-patterns`

Architecture: `hexagonal-architecture`, `architecture-decision-records`, `coding-standards`, `error-handling`, `git-workflow`

Workflow: `tdd-workflow`, `e2e-testing`, `search-first`, `autonomous-loops`, `iterative-retrieval`, `deep-research`, `production-audit`, `codebase-onboarding`

Tools: `mcp-server-patterns`, `github-ops`, `benchmark`, `api-connector-builder`, `article-writing`

### Commands installed (~/.claude/commands/)

Language-specific: `/go-review`, `/go-test`, `/go-build`, `/python-review`, `/rust-review`, `/rust-build`, `/rust-test`, `/gradle-build`, `/fastapi-review`

Multi-agent: `/multi-plan`, `/multi-execute`, `/multi-workflow`, `/multi-backend`, `/multi-frontend`

General: `/plan`, `/build-fix`, `/refactor-clean`, `/quality-gate`, `/test-coverage`, `/update-docs`, `/checkpoint`, `/skill-create`, `/security-scan`, `/pr`, `/project-init`, `/review-pr`, `/plan-prd`

### Reinstall on new machine
```bash
git clone --depth=1 https://github.com/affaan-m/ecc /tmp/ecc

# Agents
for agent in go-reviewer.md go-build-resolver.md python-reviewer.md typescript-reviewer.md \
  rust-reviewer.md rust-build-resolver.md java-reviewer.md java-build-resolver.md \
  build-error-resolver.md architect.md code-architect.md code-reviewer.md code-explorer.md \
  planner.md tdd-guide.md security-reviewer.md refactor-cleaner.md doc-updater.md \
  docs-lookup.md e2e-runner.md loop-operator.md database-reviewer.md performance-optimizer.md \
  silent-failure-hunter.md chief-of-staff.md pr-test-analyzer.md a11y-architect.md; do
  cp /tmp/ecc/agents/$agent ~/.claude/agents/
done

# Rules
mkdir -p ~/.claude/rules/ecc
for lang in common typescript python golang rust java web; do
  cp -r /tmp/ecc/rules/$lang ~/.claude/rules/ecc/
done

# Skills
for skill in coding-standards backend-patterns frontend-patterns api-design \
  deployment-patterns docker-patterns golang-patterns golang-testing \
  python-patterns python-testing rust-patterns rust-testing \
  java-coding-standards jpa-patterns fastapi-patterns django-patterns \
  tdd-workflow e2e-testing database-migrations postgres-patterns redis-patterns \
  prisma-patterns vite-patterns nextjs-turbopack nestjs-patterns \
  hexagonal-architecture architecture-decision-records error-handling git-workflow \
  codebase-onboarding production-audit autonomous-loops iterative-retrieval \
  deep-research mcp-server-patterns article-writing github-ops benchmark \
  api-connector-builder search-first; do
  cp -r /tmp/ecc/skills/$skill ~/.claude/skills/
done

# Commands
mkdir -p ~/.claude/commands
for cmd in go-review.md go-test.md go-build.md python-review.md \
  rust-review.md rust-build.md rust-test.md gradle-build.md fastapi-review.md \
  multi-plan.md multi-execute.md multi-workflow.md multi-backend.md multi-frontend.md \
  plan.md build-fix.md refactor-clean.md quality-gate.md test-coverage.md \
  update-docs.md checkpoint.md skill-create.md security-scan.md \
  pr.md project-init.md review-pr.md plan-prd.md; do
  cp /tmp/ecc/commands/$cmd ~/.claude/commands/
done

rm -rf /tmp/ecc
```

### Available but not installed (safe to add anytime)

These were skipped to keep the initial install focused. No conflicts with any existing tools. To install any of them, clone ECC and copy the specific file/directory.

**Agents** - copy to `~/.claude/agents/`:
```bash
git clone --depth=1 https://github.com/affaan-m/ecc /tmp/ecc
# then copy what you want:
cp /tmp/ecc/agents/fastapi-reviewer.md ~/.claude/agents/       # Python FastAPI review
cp /tmp/ecc/agents/django-reviewer.md ~/.claude/agents/        # Python Django review
cp /tmp/ecc/agents/django-build-resolver.md ~/.claude/agents/  # Django build errors
cp /tmp/ecc/agents/code-simplifier.md ~/.claude/agents/        # Simplification subagent
cp /tmp/ecc/agents/comment-analyzer.md ~/.claude/agents/       # Code comment quality
cp /tmp/ecc/agents/type-design-analyzer.md ~/.claude/agents/   # TypeScript type analysis
cp /tmp/ecc/agents/harness-optimizer.md ~/.claude/agents/      # Claude Code config tuning
rm -rf /tmp/ecc
```

**Skills** - copy to `~/.claude/skills/`:
```bash
git clone --depth=1 https://github.com/affaan-m/ecc /tmp/ecc
# then copy what you want:
cp -r /tmp/ecc/skills/code-tour ~/.claude/skills/                        # Walkthrough of unfamiliar codebases
cp -r /tmp/ecc/skills/benchmark-optimization-loop ~/.claude/skills/      # Perf benchmarking loops
cp -r /tmp/ecc/skills/frontend-a11y ~/.claude/skills/                    # Accessibility patterns
cp -r /tmp/ecc/skills/product-lens ~/.claude/skills/                     # Product thinking for code decisions
cp -r /tmp/ecc/skills/context-budget ~/.claude/skills/                   # Context window management
cp -r /tmp/ecc/skills/regex-vs-llm-structured-text ~/.claude/skills/     # Regex vs LLM decision framework
cp -r /tmp/ecc/skills/agentic-engineering ~/.claude/skills/              # Patterns for building agents
cp -r /tmp/ecc/skills/ai-first-engineering ~/.claude/skills/             # AI-first dev workflow
cp -r /tmp/ecc/skills/blueprint ~/.claude/skills/                        # Project scaffolding blueprints
cp -r /tmp/ecc/skills/prompt-optimizer ~/.claude/skills/                 # Prompt quality improvement
cp -r /tmp/ecc/skills/exa-search ~/.claude/skills/                       # Research with Exa API
cp -r /tmp/ecc/skills/design-system ~/.claude/skills/                    # Design system patterns
cp -r /tmp/ecc/skills/plan-orchestrate ~/.claude/skills/                 # Orchestration planning
rm -rf /tmp/ecc
```

**Commands** - copy to `~/.claude/commands/`:
```bash
git clone --depth=1 https://github.com/affaan-m/ecc /tmp/ecc
cp /tmp/ecc/commands/feature-dev.md ~/.claude/commands/     # /feature-dev - feature dev workflow
cp /tmp/ecc/commands/skill-health.md ~/.claude/commands/    # /skill-health - check skill quality
cp /tmp/ecc/commands/update-codemaps.md ~/.claude/commands/ # /update-codemaps - update project codemaps
rm -rf /tmp/ecc
```
