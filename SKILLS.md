# Skills

Skills installed outside the plugin system. Each needs to be reinstalled manually on a new machine.

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

**What gstack adds (auto-installed):** The task management layer - `/autoplan`, `/investigate`, `/qa`, `/ship`, `/review`, `/office-hours`, `/retro`, and the browser automation system. NOT the gsd-* skills.

---

### get-shit-done-cc (GSD) - installs the gsd-* skills
**Source:** https://github.com/gsd-build/get-shit-done
**Package:** `get-shit-done-cc` on npm (by TÂCHES)
**Install:**
```bash
npx get-shit-done-cc
```
**Current version:** 1.34.2

This is what actually installs the 50+ `gsd-*` skills and the `~/.claude/get-shit-done/` directory (workflows, references, templates). It is completely separate from gstack. The two integrate - gstack hooks reference GSD state files - but neither installs the other.

**What it installs:**
- `~/.claude/get-shit-done/` - workflow engine, references, templates
- All `~/.claude/skills/gsd-*` directories - the slash commands
- `~/.claude/gsd-file-manifest.json` - install manifest

**Key skills:** `/gsd-new-project`, `/gsd-plan-phase`, `/gsd-execute-phase`, `/gsd-review`, `/gsd-debug`, `/gsd-ship`, `/gsd-discuss-phase`, `/gsd-validate-phase`, `/gsd-map-codebase`
**Key sub-skills:** `/dev-philosophy`, `/heal`, `/kano-model`, `/lean`, `/mcp-server`, `/new-submodule`, `/product-manager-review`, `/python-coder`, `/qa-review`, `/receiving-code-review`, `/security-review`, `/smart-context7`, `/smart-review`, `/smart-simplify`, `/state-doc`, `/two-stage-review`, `/unit-test-builder`, `/verify-before-done`, `/work-order`, `/worktrees`, `/writing-skills`, `/jj-qa`, `/github-setup`

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
**Source:** https://github.com/tsenart/council-skill
**Install:**
```bash
npx skills add tsenart/council-skill --skill council -a claude-code -g -y
```
**What it does:** Runs a structured 3-round multi-perspective deliberation: independent analysis, cross-examination, final verdict. For hard decisions where one answer isn't enough.
**When to use:** Architecture decisions, strategy tradeoffs, risk reviews, debugging hypotheses with multiple possible causes, launch decisions.

---

## Design - typography and quality

### impeccable
**Source:** https://github.com/pbakaus/impeccable
**Install:**
```bash
npx skills add pbakaus/impeccable --skill impeccable -a claude-code -g -y
```
**What it does:** 23 design commands covering typography, color, spacing, motion, interaction, responsive, and UX writing. 27 deterministic anti-pattern rules. Built on top of `frontend-design`.
**Key commands:** `/impeccable audit`, `/impeccable polish`, `/impeccable critique`, `/impeccable teach`, `/impeccable bolder`, `/impeccable quieter`, `/impeccable distill`, `/impeccable animate`
**When to use:** Any frontend UI work. Run `/impeccable audit` before shipping UI. Run `/impeccable teach` once per new project to set design context.

---

## Design - motion

### design-motion-principles
**Source:** https://github.com/kylezantos/design-motion-principles
**Install:**
```bash
mkdir -p ~/.claude/skills/design-motion-principles/references ~/.claude/skills/design-motion-principles/workflows
BASE="https://raw.githubusercontent.com/kylezantos/design-motion-principles/main/skills/design-motion-principles"
curl -s "$BASE/SKILL.md" -o ~/.claude/skills/design-motion-principles/SKILL.md
for f in accessibility.md anti-checklist.md audit-checklist.md creation-gotchas.md emil-kowalski.md jakub-krehel.md jhey-tompkins.md motion-cookbook.md output-format.md performance.md; do
  curl -s "$BASE/references/$f" -o ~/.claude/skills/design-motion-principles/references/$f
done
curl -s "$BASE/workflows/audit.md" -o ~/.claude/skills/design-motion-principles/workflows/audit.md
curl -s "$BASE/workflows/create.md" -o ~/.claude/skills/design-motion-principles/workflows/create.md
```
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
