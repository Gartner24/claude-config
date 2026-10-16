# Setup
Type: how to

This page is for you, setting up or restoring this Claude Code setup on a machine. It covers the install, the frameworks, the downloaded skills, the plugins, the MCP servers and how to keep each one current.

## Install on this machine

1. Clone the repo. The clone lives at `~/dotfiles/claude-config`, and `~/claude-config` is a link to it.
2. Preview the install: `bin/install.sh --dry-run`.
3. Run it for real: `bin/install.sh`. It copies and links the repo into `~/.claude`, rebuilds edited downloaded skills, then runs the self-checks.
4. Before every commit, go the other way: `bin/sync.sh` copies `~/.claude` into the repo, then read `git diff`.

The `intent-router` skill is part of this repo. `bin/install.sh` links it, so there is nothing separate to install. It reads `config/routing.md` at runtime, and it falls back to a built-in table if the file is missing. To add routing for a new skill, add a block to `config/routing.md` and commit.

If you ever install it by hand, copy the one file:

```bash
mkdir -p ~/.claude/skills/intent-router
cp claude-home/skills/intent-router/SKILL.md ~/.claude/skills/intent-router/SKILL.md
```

Or from a fresh clone:

```bash
git clone https://github.com/Gartner24/claude-config ~/claude-config
mkdir -p ~/.claude/skills/intent-router
cp ~/claude-config/claude-home/skills/intent-router/SKILL.md ~/.claude/skills/intent-router/SKILL.md
```

## Land changes only through PRs (spec 0051)

Each of your own repos gets the same GitHub settings: squash merge only, branches deleted on merge, and a ruleset named "main only through a PR".

1. Set them once per repo: `bin/repo-settings.sh <owner/repo>`. Then `bin/repo-settings.sh --check <owner/repo>` must exit 0.
2. To let small, low risk runner PRs merge themselves once green, add the repo to `~/.claude/private/pr.json`, for example `"Gartner24/claude-config": {"merge": true, "auto_merge": true}`. Only you write that file. `merge: true` alone keeps the "merge now" question and no self merge.
3. Docs only commits made in a session go out with `bin/docs-pr.sh <slug>` from the repo, which opens and squash merges a small PR. Afterwards, check that `git diff HEAD origin/main` is empty, then `git reset --hard origin/main` (the script does not realign local main yet, plan item E3).

## Restore on a new machine

Do the steps in order. Hook paths in `settings.json` are hardcoded to the old home folder, so step 8 matters.

1. Clone the repo (see above) and run `bin/install.sh --dry-run`, then `bin/install.sh`. It also rebuilds edited downloaded skills from upstream plus their patch, through `bin/claude-config.py restore`.
2. Install jjstack. It installs gstack and creates the hook symlinks. See [Frameworks](#frameworks).
3. Install get-shit-done-cc, pinned at 1.34.2. It ships 8 `gsd-*` hooks, and `settings.json` references 6 of them. Without this step the session starts with dead hook entries.
4. Install the plugins in the [Plugins](#plugins) table, except claude-mem: it stays off for good (decided 2026-10-15, see `docs/briefs/tool-review-2026-10.md`).
5. Reinstall the downloaded skills. Run each manifest entry's `install` command from `config/manifest.json`, or use the `/claude-config` skill.
6. Merge `config/mcp-config.json` into `~/.claude.json` (see [MCP servers](#mcp-servers)). Put your own key in `API_KEY`.
7. In Claude Code settings, go to MCP and enable the context7 connector.
8. Copy `settings.json` and change the old home folder paths to match the new username and home folder.
9. Copy `settings.local.json` as it is.
10. If you ever need the agents, rules, hook and script by hand, they come from this repo, not from upstream ECC:

```bash
cp -a claude-home/agents/. ~/.claude/agents/
mkdir -p ~/.claude/rules
cp -a claude-home/rules/. ~/.claude/rules/
cp -a claude-home/hooks/block-destructive.sh ~/.claude/hooks/
cp -a claude-home/scripts/chroma-reaper.sh ~/.claude/scripts/
chmod +x ~/.claude/hooks/block-destructive.sh ~/.claude/scripts/chroma-reaper.sh
bash ~/.claude/hooks/block-destructive.sh --test   # must print "all self-checks passed"
```

Copying `cp -a <dir>/.` takes the contents, so new files are picked up and no list goes stale. Re-copying upstream ECC would overwrite the additions in `rules/ecc/common/code-review.md` and `common/testing.md`, and drop the two hand-written agents.

11. The ECC skills and commands are not copied from this repo. They come from upstream (the manifest lists each one). The loop below is the by-hand way:

```bash
git clone --depth=1 https://github.com/affaan-m/ECC /tmp/ecc

for skill in coding-standards backend-patterns frontend-patterns api-design \
  deployment-patterns docker-patterns golang-patterns golang-testing \
  python-patterns python-testing rust-patterns rust-testing \
  java-coding-standards jpa-patterns fastapi-patterns django-patterns \
  tdd-workflow e2e-testing database-migrations postgres-patterns redis-patterns \
  prisma-patterns vite-patterns nextjs-turbopack nestjs-patterns \
  hexagonal-architecture architecture-decision-records error-handling git-workflow \
  codebase-onboarding production-audit autonomous-loops iterative-retrieval \
  mcp-server-patterns article-writing github-ops benchmark \
  api-connector-builder search-first; do
  cp -r /tmp/ecc/skills/$skill ~/.claude/skills/
done

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

12. Rebuild the packshot virtual environment (see [Downloaded skills](#downloaded-skills)):

```bash
cd ~/.claude/skills/packshot && python3 -m venv .venv && ./.venv/bin/pip install fal-client requests
```

## Frameworks

Frameworks are full systems with many sub-skills. Their own installer wins, and none of them is copied into this repo. Each has an entry under `frameworks` in [`../../config/manifest.json`](../../config/manifest.json) with its source, pinned commit, license and install command.

| Framework | Source | Install |
|-----------|--------|---------|
| jjstack | private, listed in `~/.claude/private/work.md` | `git clone <jjstack source from ~/.claude/private/work.md> ~/.claude/skills/jjstack` then `cd ~/.claude/skills/jjstack && ./setup` |
| gstack | `github:garrytan/gstack` | installed by jjstack's `./setup` |
| get-shit-done-cc | `npm:get-shit-done-cc` | `npx get-shit-done-cc` (pinned at 1.34.2, read the notes below first) |
| ECC (everything-claude-code) | `github:affaan-m/everything-claude-code` | manual cherry-pick, see below |
| JSM skills | `github:JavaScript-Mastery-Pro/skills` | `git clone https://github.com/JavaScript-Mastery-Pro/skills ~/.claude/vendor-jsm-skills`, then link each `skills/<name>` into `~/.claude/skills` |
| Sentry skills (`getsentry-skills`) | `github:getsentry/skills` | `git clone https://github.com/getsentry/skills ~/.claude/skills/getsentry-skills` |
| Anthropic security review | `github:anthropics/claude-code-security-review` | `git clone https://github.com/anthropics/claude-code-security-review ~/.claude/skills/anthropic-security-review` |

### jjstack and gstack

You only need to install jjstack. Its setup script checks for gstack, and it clones and sets up `garrytan/gstack` if gstack is missing. You do not install gstack separately.

- jjstack adds a product and UX layer on top of gstack: opinionated skills for code quality, product thinking and developer experience. All jjstack skills are symlinked into `~/.claude/skills/`.
- gstack adds the task layer: `/autoplan`, `/investigate`, `/qa`, `/ship`, `/review`, `/office-hours`, `/retro` and the browser automation. It does not add the `gsd-*` skills.
- Many skills that look like they belong to GSD come from jjstack. They are symlinks into `~/.claude/skills/jjstack/skills/`: `/dev-philosophy`, `/heal`, `/kano-model`, `/lean`, `/mcp-server`, `/new-submodule`, `/product-manager-review`, `/python-coder`, `/qa-review`, `/receiving-code-review`, `/security-review`, `/smart-context7`, `/smart-review`, `/smart-simplify`, `/state-doc`, `/two-stage-review`, `/unit-test-builder`, `/verify-before-done`, `/work-order`, `/worktrees`, `/writing-skills`, `/jj-qa`, `/github-setup`. The same goes for `/council`.
- The permission gate is jjstack's `permission-floor.py` plus the deny rules from `hooks/permissions.policy.json` (see [HOOKS.md](HOOKS.md)). No local jjstack diff is kept any more.

Known jjstack 0.36.0 bug, left unpatched on purpose:

- `bin/jjstack-gbrain-phi-lib.sh` has a function `reconstruct_cwd` that cannot undo a Claude Code project slug whose path has a dot folder.
- Claude Code writes both `/` and `.` as `-`, so `-home-santiago--claude` should map to `/home/santiago/.claude` but resolves to `/home/santiago/-claude`.
- This causes the one `test/smoke.sh` failure. That test also hardcodes the jjstack author's own path, so it cannot pass here either way.
- Impact today: none. Only `jjstack-memory-bridge` and `jjstack-memory-to-learnings` call it, both are gbrain paths, and gbrain is not installed.
- It stays unpatched because a second local diff inside the jjstack checkout costs more than it saves for a dead code path. Re-check after any jjstack upgrade, and before you ever run `/setup-gbrain`.

### get-shit-done-cc (GSD)

- Source: https://github.com/gsd-build/get-shit-done. The npm package is `get-shit-done-cc`.
- It is pinned at 1.34.2 on purpose. Upstream is further ahead, but the `gsd-*` skills were purged from this machine on purpose (commit `33f5b27`, "purge dead GSD routes"). Running `npx get-shit-done-cc` again reinstalls all 50+ of them and undoes the purge.
- Only what the hooks still need is kept, and it is load-bearing:
  - `~/.claude/get-shit-done/`, the workflow engine, references and templates, read by the `gsd-*` hooks.
  - `~/.claude/gsd-file-manifest.json`.
  - The `gsd-*` hooks in `~/.claude/hooks/`, wired into `settings.json`.
- No `~/.claude/skills/gsd-*` skill is installed, on purpose.

### ECC (everything-claude-code)

- The ECC cherry-pick is deliberately frozen. Upstream has 41 more agents and 15 more language rule folders than we have.
- The local rules carry hand-earned additions. Re-copying upstream would overwrite them. Adopt ECC changes selectively by hand, or not at all.
- Install method: manual cherry-pick, not `bin/install.sh`. The manifest `ecc` entry owns the copied commands and records no single pin, because the installed copies match several upstream commits.
- Not installed: `hooks/`, `scripts/`, `settings.json`, MCP configs, `configure-ecc`, the `security-scan` agent, the instinct system and continuous-learning. They conflict with jjstack, GSD and claude-mem.
- Agents and rules come from this repo (`claude-home/agents/`, `claude-home/rules/ecc/`), and the ECC skills and commands come from upstream (see [Restore on a new machine](#restore-on-a-new-machine)).

Available in ECC but not installed. They were skipped to keep the install focused, and they conflict with nothing. To add one, clone ECC and copy it:

```bash
git clone --depth=1 https://github.com/affaan-m/ecc /tmp/ecc
cp /tmp/ecc/agents/<name>.md ~/.claude/agents/
cp -r /tmp/ecc/skills/<name> ~/.claude/skills/
cp /tmp/ecc/commands/<name>.md ~/.claude/commands/
rm -rf /tmp/ecc
```

| Kind | Name | What it does |
|------|------|--------------|
| Agent | `fastapi-reviewer` | Python FastAPI review |
| Agent | `django-reviewer` | Python Django review |
| Agent | `django-build-resolver` | Django build errors |
| Agent | `code-simplifier` | Simplification subagent |
| Agent | `comment-analyzer` | Code comment quality |
| Agent | `type-design-analyzer` | TypeScript type analysis |
| Agent | `harness-optimizer` | Claude Code config tuning |
| Skill | `code-tour` | Walkthrough of unfamiliar codebases |
| Skill | `benchmark-optimization-loop` | Performance benchmarking loops |
| Skill | `frontend-a11y` | Accessibility patterns |
| Skill | `product-lens` | Product thinking for code decisions |
| Skill | `context-budget` | Context window management |
| Skill | `regex-vs-llm-structured-text` | Regex versus LLM decision framework |
| Skill | `agentic-engineering` | Patterns for building agents |
| Skill | `ai-first-engineering` | AI-first dev workflow |
| Skill | `blueprint` | Project scaffolding blueprints |
| Skill | `prompt-optimizer` | Prompt quality improvement |
| Skill | `exa-search` | Research with the Exa API |
| Skill | `design-system` | Design system patterns |
| Skill | `plan-orchestrate` | Orchestration planning |
| Command | `feature-dev` | `/feature-dev`, feature dev workflow |
| Command | `skill-health` | `/skill-health`, check skill quality |
| Command | `update-codemaps` | `/update-codemaps`, update project codemaps |

### JSM skills, Sentry skills, Anthropic security review

- The JSM skills are cloned to `~/.claude/vendor-jsm-skills` and linked into `~/.claude/skills` one by one.
- `getsentry-skills` is Sentry's skills, for agents that know Sentry error tracking. It lives at `~/.claude/skills/getsentry-skills/`.
- `anthropic-security-review` is a Python security review toolkit from Anthropic. It is a standalone tool, not a `SKILL.md` skill. It lives at `~/.claude/skills/anthropic-security-review/`.

## Downloaded skills

Every skill that came from outside this repo is listed in [`../../config/manifest.json`](../../config/manifest.json). The file records, per skill:

- the source (a GitHub repo, or private),
- the pinned commit (some are unpinned, which means they follow the upstream default branch),
- the license,
- the `install` command, and
- a status: `downloaded` (a clean copy of upstream), `edited` (upstream at the pin plus a patch, kept in the entry's `patch` field), `unpinned`, or `source-unknown`.

Rules for the manifest:

- Edited skills are rebuilt from upstream at the pin plus their patch. `bin/install.sh` does this for you with `bin/claude-config.py restore`.
- A skill that was never copied into this repo is cited by its manifest entry only.
- A skill with an unknown source, and any private one, lives only under `~/.claude/private/skills/`. Back it up before you wipe a machine.
- The list of every skill with its source, status, license and description is generated into [SKILLS.md](SKILLS.md).

To update downloaded skills, use the `/claude-config` skill. It runs `python3 bin/claude-config.py update --plan`, shows what changed upstream for each skill, and asks yes or no per skill before it applies anything. For daily use, see [DAILY-USE.md](DAILY-USE.md).

Some skills were first installed as a set. The notes below say what each set is and how it was installed. Where the manifest and an older note disagree, the manifest wins: skills that older notes called "not installed" or "undocumented" are listed there as downloaded or unpinned, with a working `install` command.

### Router skills

| Skill | Source | Install | What it does |
|-------|--------|---------|--------------|
| skill-router | `github:chrishan17/skill-router` | `npx skills add chrishan17/skill-router/skills/skill-router -a claude-code -g -y` | Puts all installed skills behind one router entry point. Fixes skills that do not fire when they should, and cuts the context spent on skill descriptions at startup. Always active. |
| intent-router | this repo, `claude-home/skills/intent-router/SKILL.md` | linked by `bin/install.sh` | Scores an ambiguous prompt against every skill's `TRIGGERS`, `BLOCKS` and `PRIORITY` fields in `config/routing.md` and invokes the best match. Silent on clear prompts. |

intent-router sits on top of skill-router and has these personal rules baked in:

- `mem-search` fires before anything else on memory-check signals.
- `council` fires before implement skills on decision signals.
- Motion dispatches by kind: `animate` (build), `transitions-dev` (CSS), `gsap-*` (scroll), `apple-design` (gesture), `review-animations` (audit).
- `investigate` wins on runtime and logic bugs, but build, compile and type errors go to `build-fix` and the toolchain resolvers.

`council` comes from jjstack (`~/.claude/skills/jjstack/skills/council`). It replaced the standalone `tsenart/council-skill` install, so it updates with jjstack and there is nothing separate to install.

### Design and motion sets

| Set | Source | Install | Notes |
|-----|--------|---------|-------|
| impeccable | `github:pbakaus/impeccable` | `npx skills add pbakaus/impeccable --skill impeccable -a claude-code -g -y` | v4: `teach` is gone, use `/impeccable init` (writes `PRODUCT.md`) and `/impeccable document` (writes `DESIGN.md`) once per project. `craft` is a deprecated alias. Subagents ship as `.toml` or `.yaml` under `agents/`. |
| design-motion-principles | `github:kylezantos/design-motion-principles` | clone and copy, below | Kept for its audit mode, which writes an HTML report with looping demos. The emilkowalski set below is the primary source. |
| emilkowalski/skills (12 upstream, 9 installed) | `github:emilkowalski/skills` | `git clone --depth=1 https://github.com/emilkowalski/skills /tmp/emil`, then `for s in /tmp/emil/skills/*/; do cp -a "$s" ~/.claude/skills/"$(basename "$s")"; done`, then `rm -rf /tmp/emil` | `animate`, `review-animations`, `improve-animations`, `find-animation-opportunities`, `animation-vocabulary`, `apple-design`, `emil-design-eng`, `prototype`, `pick-ui-library`. |
| gsap-skills (8) | `github:greensock/gsap-skills` | same loop with `/tmp/gsap` | `gsap-core`, `gsap-timeline`, `gsap-scrolltrigger`, `gsap-react`, `gsap-frameworks`, `gsap-plugins`, `gsap-performance`, `gsap-utils`. Use for scroll animation and timelines. Use `transitions-dev` for simple CSS transitions. |
| transitions.dev (2) | `github:Jakubantalik/transitions.dev` | same loop with `/tmp/tdev` | `transitions-dev`, `transitions-polish`. |
| design-dna | `github:zanwei/design-dna` | clone, then `mkdir -p ~/.claude/skills/design-dna` and `cp -a SKILL.md references docs` into it | Turns a screenshot, image or URL into a Design DNA JSON. Use it at design step 1 when a client shows a site they like. |
| threejs-skills (10) | `github:CloudAI-X/threejs-skills` | same loop with `/tmp/tjs` | `threejs-fundamentals`, `-geometry`, `-materials`, `-lighting`, `-textures`, `-shaders`, `-loaders`, `-animation`, `-interaction`, `-postprocessing`. Only for real WebGL work. |
| taste skills (3) | `github:Leonxlnx/taste-skill` | `npx skills add https://github.com/Leonxlnx/taste-skill --skill "<name>" -a claude-code -g -y` | `high-end-visual-design`, `minimalist-ui`, `industrial-brutalist-ui` (beta). All three are `edited` in the manifest: upstream at the pin plus a patch. Install one, two or all three. |
| ui-ux-pro-max | `github:nextlevelbuilder/ui-ux-pro-max-skill` | manifest `install` | 67 styles, 96 palettes, 57 font pairings, 25 chart types, 13 framework stacks. |

The design-motion-principles install:

```bash
git clone --depth=1 https://github.com/kylezantos/design-motion-principles /tmp/dmp
mkdir -p ~/.claude/skills/design-motion-principles
cp -a /tmp/dmp/skills/design-motion-principles/. ~/.claude/skills/design-motion-principles/
rm -rf /tmp/dmp
```

Clone and copy, not a `curl` list of files, because upstream adds new files (`references/demo-shell.html`, `references/report-template.html`) that a fixed list skips. The same reasoning applies to the loops above: `git clone --depth=1` has no pinned version, so re-clone to update. The full design flow is in [DESIGN-PIPELINE.md](DESIGN-PIPELINE.md).

### Writing and client site skills

- `humanizer` (`github:blader/humanizer`): clone it, then `mkdir -p ~/.claude/skills/humanizer` and `cp -a SKILL.md scripts` into it. It rewrites 33 named AI-writing tells. It overlaps `anti-ai-writing` on purpose: humanizer is the mechanical pattern sweep, `anti-ai-writing` is the voice-aware final pass.
- `voice-dna` and `anti-ai-writing` come from `artemnovitckii/content-skills` (MIT) and are tracked in this repo. `nano-banana`, `video-to-website` and `business-analyzer` live in this repo and are symlinked.
- `astro` comes from `github:astrolicious/agent-skills`. `astro-patterns`, `seo-ops` and `content-ops` are this repo's own skills.
- marketingskills (`github:coreyhaines31/marketingskills`, 12 of 50 installed):

```bash
git clone --depth=1 https://github.com/coreyhaines31/marketingskills /tmp/mkt
for n in marketing-psychology cro signup onboarding popups paywalls pricing offers \
         ab-testing launch lead-magnets customer-research; do
  cp -a /tmp/mkt/skills/$n ~/.claude/skills/$n
done
rm -rf /tmp/mkt
```

The rest of the 50 are left out on purpose (`copywriting`, `copy-editing`, `content-strategy`, `social`, `emails`, `seo-audit`, `ai-seo`, `programmatic-seo`, `schema`, `site-architecture`, `image`, `video` and others). Your own `content-ops`, `article-writing`, `seo-ops`, `voice-dna` and `business-analyzer` cover them, and `image` and `video` would collide by name. The install line takes a skill name, so add one if a client job needs it.

### packshot (no public source)

The manifest marks `packshot` as `source-unknown`: it came as a zip, and there is no public repo.

- The original archive is at `~/Downloads/PACKSHOT CLAUDE SKILL-*.zip`.
- It is not vendored. It lives only in `~/.claude/skills/packshot/`, so back it up before wiping a machine. There is nowhere to download it again.
- It renders on FAL through `fal-ai/nano-banana-2/edit`, at about $0.12 per image, and needs a `FAL_KEY` in the env or a `.env` at the project root. The skill stops without it.
- Its Python dependencies live in a venv at `~/.claude/skills/packshot/.venv` (25 MB). This is required: Arch follows PEP 668 and refuses system-wide `pip install`, and pipx cannot help because `fal-client` is a library with no command line entry point. Rebuild it with the command in step 12 of the restore steps.
- The skill uses `~/.claude/skills/packshot/.venv/bin/python`, never the system `python3`.
- Local changes made to the upstream skill:
  - Step 1 now reads `brand-system.html` from `/brand-system`, instead of a file from a `/brand` skill that does not exist here. "No brand system found" is a valid result, not a hard stop.
  - Output moved to `./packshots/[output-name]/`.
  - The script path is fixed to `~/.claude/skills/packshot/generate-packshot.py`.
  - A Requirements section and a cost note per generation were added.
- Use `nano-banana` first for general imagery (free, Gemini). Use packshot for commercial product shots.

### 21st.dev skills

The seven skills `21st-ai`, `21st-cli-use`, `21st-design-sync`, `21st-registry`, `21st-ui-build`, `21st-ui-explore` and `21st-ui-review` come from `github:21st-dev/claude-code-plugin`. Install each with `npx skills add 21st-dev/claude-code-plugin/plugins/21st/skills/<name>`. They drive the 21st CLI, `@21st-dev/cli` (global npm). Keep it current under [Keep it current](#keep-it-current).

### Cloudflare skills

Source: https://github.com/cloudflare/skills, Cloudflare's official bundle. The manifest has 14 of them: `agents-sdk`, `cloudflare`, `cloudflare-email-service`, `cloudflare-one`, `cloudflare-one-migrations`, `durable-objects`, `nextjs-on-cloudflare`, `sandbox-stable`, `sandbox-next`, `sandbox-migrate-to-next`, `turnstile-spin`, `web-perf`, `workers-best-practices`, `wrangler`.

- Each has an `install` command in the manifest, for example `npx skills add cloudflare/skills/skills/wrangler`.
- Upstream's own way is to clone once and symlink, so `git pull` updates all of them at once:

```bash
git clone https://github.com/cloudflare/skills ~/.config/cloudflare-skills
for s in agents-sdk cloudflare cloudflare-email-service cloudflare-one \
         cloudflare-one-migrations durable-objects sandbox-stable sandbox-next turnstile-spin \
         web-perf workers-best-practices wrangler; do
  ln -sfn ~/.config/cloudflare-skills/skills/$s ~/.claude/skills/$s
done
```

- A copy install, which is what this machine has, does not update itself.
- `turnstile-spin` has drifted from upstream. The local copy carries `scripts/fetch-secret.sh`, `scripts/worker-deploy.sh` and a `templates/worker/` scaffold that upstream no longer ships, almost certainly leftovers from an older release. Refresh it with:

```bash
git clone --depth=1 https://github.com/cloudflare/skills /tmp/cfs \
  && cp -a /tmp/cfs/skills/turnstile-spin/. ~/.claude/skills/turnstile-spin/ \
  && rm -rf /tmp/cfs
```

That leaves the orphan files in place. Delete them by hand once you are sure you did not write them.

### graphify

`graphify` is a Python package, not a skill repo (`github:Graphify-Labs/graphify`). The package is `graphifyy` and the command is `graphify`.

```bash
pipx install graphifyy
graphify install claude    # (re)writes ~/.claude/skills/graphify and registers it in CLAUDE.md
```

The skill carries its own `.graphify_version`. If that drifts from the package version, the CLI warns on every run. Update it under [Keep it current](#keep-it-current).

### Private and in-repo skills

- A client CMS skill and a private doc re-sync skill stay local. They are not vendored, and the client skills are gitignored.
- `review-stack` is hand-written and lives in this repo (`claude-home/skills/review-stack`, linked to `~/.claude/skills/review-stack`). It runs the reviewer set plus a blind lane over the same diff, and a completed run writes a receipt that `claude-home/hooks/review-stack-pre-push` checks before a push. See [HOOKS.md](HOOKS.md).

## Plugins

Plugins install with `claude plugin install` and update on Claude Code launch.

superpowers and claude-mem were installed together as a unit. superpowers gives the skill workflows (debugging, TDD, review, planning). claude-mem gives memory across sessions. Neither is useful without the other: without claude-mem, superpowers forgets context between sessions, and without superpowers, claude-mem has no structured workflows to remember outcomes from.

| Plugin | Source | Install | What it adds |
|--------|--------|---------|--------------|
| superpowers | `claude-plugins-official/superpowers` | `claude plugin install superpowers` | 13 skills: `/brainstorming`, `/test-driven-development`, `/systematic-debugging`, `/writing-plans`, `/executing-plans`, `/subagent-driven-development`, `/dispatching-parallel-agents`, `/requesting-code-review`, `/receiving-code-review`, `/finishing-a-development-branch`, `/using-git-worktrees`, `/verification-before-completion`, `/writing-skills`. The foundation: always loaded, and other skills integrate with it. |
| claude-mem | `thedotmack/claude-mem` | `claude plugin install claude-mem` | 15 skills: `/mem-search`, `/learn-codebase`, `/smart-explore`, `/knowledge-agent`, `/make-plan`, `/do`, `/babysit`, `/weekly-digests`, `/timeline-report`, `/pathfinder`, `/wowerpoint`, `/oh-my-issues`, `/how-it-works`, `/design-is`, `/version-bump`. Run `/learn-codebase` on a new repo and `/mem-search` to recall past work. |
| frontend-design | `claude-plugins-official/frontend-design` | `claude plugin install frontend-design` | `/frontend-design`. Anthropic's baseline UI skill. impeccable and the taste skills build on it. |
| code-review | `claude-plugins-official/code-review` | `claude plugin install code-review` | `/code-review:code-review` reviews a GitHub pull request with parallel agents and posts one comment. Effort levels, `ultra`, `--comment` and `--fix` belong to the built-in `/code-review`, which has no file on disk. `CLAUDE.md` says which to use. Use it as a focused diff review before merging, next to gstack `/review`. |
| feature-dev | `claude-plugins-official/feature-dev` | `claude plugin install feature-dev` | Agents `code-architect`, `code-explorer`, `code-reviewer`. Skills that need codebase analysis use them as subagents. |
| code-simplifier | `claude-plugins-official/code-simplifier` | `claude plugin install code-simplifier` | A subagent that refactors recent code. Run it after a feature, before review. |
| ralph-loop | `claude-plugins-official/ralph-loop` | `claude plugin install ralph-loop` | `/ralph-loop` and `/cancel-ralph`. An autonomous loop runner for long background tasks. |
| clangd-lsp | `claude-plugins-official/clangd-lsp` | `claude plugin install clangd-lsp` | C and C++ language server integration. |
| ponytail | `DietrichGebert/ponytail` (third-party marketplace) | `claude plugins marketplace add DietrichGebert/ponytail` then `claude plugins install ponytail@ponytail` | `/ponytail`, `/ponytail-audit`, `/ponytail-debt`, `/ponytail-gain`, `/ponytail-help`, `/ponytail-review`. |
| security-guidance | `claude-plugins-official/security-guidance` (Anthropic) | `claude plugin install security-guidance@claude-plugins-official` | A passive security net: regex warnings on Edit and Write, a diff review on Stop, a flow analysis on commit. It complements the on-demand `review-stack`. |

Notes:

- ponytail is a lazy senior dev mode with a YAGNI ladder that prefers the shortest working diff. It is active every session through a SessionStart hook, and its state is in `~/.claude/.ponytail-active`. Levels are `lite`, `full` (default) and `ultra`: switch with `/ponytail <level>`, stop with "stop ponytail".
- security-guidance: set `ENABLE_STOP_REVIEW=0` to skip the per-turn Stop review (and keep the commit-time review) if the per-message cost bites.

Marketplace added, plugin not installed:

| Plugin | Source | Install when ready | What it adds |
|--------|--------|--------------------|--------------|
| claude-seo | `AgriciDaniel/claude-seo` (MIT) | `claude plugin install claude-seo@agricidaniel-claude-seo` | A runnable SEO and AEO audit engine: 25 sub-skills and 18 GEO/AEO agents. Audit only, no account access, no auto-publish. |

The marketplace is already registered as `agricidaniel-claude-seo` in `settings.json` and `~/.claude/plugins/known_marketplaces.json`. claude-seo complements the build-time `SEO-GUIDE.md` (the guide is the spec, the plugin is the audit). It is wired into the `seo-ops` skill and the `/monthly-ops` SEO add-on. The evaluation behind it is in `../research/SKILLS-EVALUATION.md`.

## MCP servers

Two MCP servers are active. `magic` is configured by hand in `~/.claude.json`. `context7` is enabled in `settings.local.json` and declared in `~/.mcp.json`.

### context7

- Source: the claude.ai MCP connectors, plus a stdio entry in `~/.mcp.json` that jjstack's `./setup` writes (`npx -y @upstash/context7-mcp`). Setup skips when a `context7` key already exists, so running it again is safe.
- Enabled in `settings.local.json` with `enabledMcpjsonServers: ["context7"]`.
- It fetches live documentation for any library, framework, SDK or CLI. Your training data may be stale, and context7 has the current docs.
- Use it for API syntax, configuration, version migration and CLI usage, even for well-known libraries. Claude reaches for it on its own when you ask about a library.
- On a new machine: Claude Code settings, then MCP, then enable the context7 connector.

### magic (21st-dev)

- Package: `@21st-dev/magic@latest`. Type: stdio through npx.
- It generates UI components from the 21st.dev library. Use it when you want a production-quality component as a starting point.
- Get an API key at https://21st.dev.
- Add this to `~/.claude.json` under `mcpServers` (the same block is in `config/mcp-config.json`):

```json
{
  "mcpServers": {
    "magic": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@21st-dev/magic@latest"],
      "env": {
        "API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

The 21st CLI (`@21st-dev/cli`) is a different thing from the magic MCP. The MCP generates components. The CLI searches, installs and publishes them.

### Adding an MCP server

Edit `~/.claude.json` directly and add the server under `mcpServers`, or use the Claude Code settings screen with `/config`.

## Keep it current

Versions below were last verified on 2026-09-02. The pinned commits in [`../../config/manifest.json`](../../config/manifest.json) are the current truth for downloaded skills and frameworks.

| Thing | Version | Update with |
|-------|---------|-------------|
| gstack | 1.79.0.0 | `git -C ~/.claude/skills/gstack merge --ff-only origin/main && ./setup` |
| jjstack | 0.36.0 | the same steps, in `~/.claude/skills/jjstack`. Stash the local `hooks/auto-approve-safe.sh` tweak first. |
| get-shit-done-cc | 1.34.2, pinned | Do not run `npx get-shit-done-cc` (see [Frameworks](#frameworks)). |
| impeccable | 4.1.3 | `npx skills add pbakaus/impeccable --skill impeccable -a claude-code -g -y` |
| graphify | 0.9.53 | `pipx upgrade graphifyy` then `graphify install claude` |
| @21st-dev/cli | 1.17.0 | `npm install -g @21st-dev/cli@latest` |
| Claude Code | 2.1.259 | `claude update` |
| superpowers | v6.3.0 | plugin update, below |
| claude-mem | v13.24.0 | plugin update, below |
| code-simplifier | v1.0.0 | plugin update, below |
| ralph-loop | v1.0.0 | plugin update, below |
| clangd-lsp | v1.0.0 | plugin update, below |
| ponytail | v4.9.0 | plugin update, below |
| security-guidance | v2.0.7 | plugin update, below |

The 21st skills drive the 21st CLI, so keep it current with `npm install -g @21st-dev/cli@latest`.

Upgrade order for gstack and jjstack matters:

1. gstack's `./setup` overwrites the shared skill symlinks (`qa`, `review`, `ship`, `office-hours` and others) so they point at gstack. Run it first.
2. Then run jjstack's setup. It re-points those symlinks at the jjstack wrappers.
3. If you got the order wrong, run `/jjstack-repair`.
4. After any jjstack upgrade, re-check the `reconstruct_cwd` bug in [Frameworks](#frameworks).

Plugins:

```bash
for m in claude-plugins-official thedotmack ponytail agricidaniel-claude-seo; do
  claude plugin marketplace update "$m"
done
claude plugin list
claude plugin update <plugin>@<marketplace>
```

Restart Claude Code afterwards. Updates are staged, not applied live.

Downloaded skills: run `/claude-config`, or `python3 bin/claude-config.py update --plan`, and answer yes or no per skill. The clone-and-copy sets have no pin, so re-clone them to update.
