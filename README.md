# claude-config

Personal Claude Code setup: plugins, skills, MCP servers, and global config.

This repo is the source of truth for the hand-maintained parts of this setup. The frameworks (gstack, jjstack, get-shit-done-cc, plugins) are documented, not vendored, and client skills are deliberately excluded - see `.gitignore` and NOTICE.md. Use it to
restore a new machine, remember what you have, or decide which tool to reach for.

## Quick map

| File | What it covers |
|------|----------------|
| [PLUGINS.md](PLUGINS.md) | Official plugins (installed via `claude plugin install`) |
| [SKILLS.md](SKILLS.md) | Community skills (installed via `npx skills add` or manually) |
| [MCP.md](MCP.md) | MCP servers (magic + context7) |
| [HOOKS.md](HOOKS.md) | Hook scripts - what each does and where it comes from |
| [USAGE.md](USAGE.md) | Decision guide + machine-readable routing rules (read by personal-router) |
| [skills/intent-router/SKILL.md](skills/intent-router/SKILL.md) | intent-router skill - reads USAGE.md, scores prompts, invokes the right skill |
| [CLAUDE.md](CLAUDE.md) | Global Claude behavior config (`~/.claude/CLAUDE.md`) |
| [settings.json](settings.json) | `~/.claude/settings.json` minus the `autoMode` block, which `sync.sh` strips (hooks, model, env, plugins) |
| [settings.local.json](settings.local.json) | `~/.claude/settings.local.json` (MCP connectors) |
| [mcp-config.json](mcp-config.json) | `~/.claude.json` mcpServers block |
| [agents/](agents/) | Copy of `~/.claude/agents/` - 29 subagent definitions - the 27 from ECC plus review-stack's two (see NOTICE.md) |
| [rules/](rules/) | Copy of `~/.claude/rules/` - the ECC per-language rule files, plus the rules below |
| [hooks/](hooks/) | Hand-written hooks + the jjstack `auto-approve-safe.sh` patch |
| [scripts/](scripts/) | `chroma-reaper.sh` (session script, synced from live); `check-routing.py` and `asciify.py` (repo-only tooling: routing-table regression test, ASCII linter) |
| [sync.sh](sync.sh) | Pulls the live `~/.claude` config into this repo. Run before committing. |

## Keeping this repo honest

`agents/`, `rules/`, `hooks/`, `scripts/`, `CLAUDE.md`, and `settings.json` are **copies**, not
symlinks (unlike `skills/` and `commands/`, which are symlinked into `~/.claude`). They drift.
Run `./sync.sh` then `git diff` before committing to pull the live state back in.

Edit the live files in `~/.claude/`, never the copies here. `sync.sh` copies live over repo, so an
edit made directly in this repo is silently overwritten on the next sync.

## Rules earned the hard way

The ECC rule files started as a cherry-pick of someone else's defaults. These additions did not:
each is here because it cost something on a real project, and each is written so a future session
does not pay again. Provenance is recorded so it is possible to judge later whether a rule still
earns its place.

| Rule | Where | Why it exists |
|------|-------|---------------|
| An absent answer rendered as a definite one | `rules/ecc/common/code-review.md` | The highest-yield defect class found across a twelve-layer console redesign, in new and pre-existing code alike. A count that has not loaded is not zero; a failed fetch is not an empty list. One instance had a defaulted count switching off the guard on account deletion |
| Get the RED back when the test came second | `rules/ecc/common/testing.md` | The TDD section assumes you watched the test fail. Bug fixes skip that, so the fix gets mutation-checked instead: break the source, confirm that test goes red, restore |
| A test that reimplements the logic passes forever | `rules/ecc/common/testing.md` | Caught twice on one project. A test that defines a local copy of the behaviour and never imports the module stays green when the real fix is reverted |
| A mock weaker than the real module passes anything | `rules/ecc/common/testing.md` | A hook mocked without one field meant a control that could never render, with every test passing |
| Shell discipline | `CLAUDE.md` | The Bash cwd persists between calls, so a stale `cd` looks exactly like a deleted tree. `$(...)` does not expand in a quoted heredoc, which once put an unexpanded placeholder into a public PR comment |
| Grep before writing against a symbol | `CLAUDE.md` | A helper that reads plausibly may not exist. Only running the test caught it |

Project-specific findings stay in that project's own `CLAUDE.md`. Only rules that transfer to any
codebase belong here.

**Turning them on.** The rules are not auto-loaded. Add one line to the project's `CLAUDE.md`:

```
@~/.claude/rules/ecc/typescript/index.md
```

Swap `typescript` for `python`, `golang`, `rust`, `java`, `web`, or `common`. Each index pulls in
the ten shared rules plus that language's set - 15 to 17 files. Import a single `coding-style.md`
instead and you get two files, none of them the ones in the table above.

## Stack overview

The setup is layered:

```
Plugins (official, auto-update)
  superpowers          - skill execution framework
  claude-mem           - persistent memory across sessions (pairs with superpowers)
  frontend-design      - UI/design agents
  code-review          - PR and diff review agents
  feature-dev          - feature planning agents
  code-simplifier      - refactor agent
  ralph-loop           - autonomous loop runner
  clangd-lsp           - C/C++ LSP
  ponytail             - "lazy senior dev" code-minimization mode
  security-guidance    - passive security net (Edit/Write warnings, Stop + commit review)

Skill frameworks (git checkouts + setup scripts - run gstack's setup BEFORE jjstack's)
  gstack               - project management system (garrytan/gstack)
  jjstack              - Product/UX layer on top of gstack (disciplin-run-org/jjstack)
  get-shit-done-cc     - PINNED at 1.34.2, hooks only, gsd-* skills deliberately purged

Community skills (installed manually or via npx skills add)
  skill-router         - Routes prompts to the right skill automatically
  impeccable           - Frontend design system: /impeccable critique + audit
  design-motion-principles - Emil Kowalski motion design
  high-end-visual-design   - Soft/premium UI taste
  minimalist-ui            - Minimalist UI taste (Notion/Linear)
  industrial-brutalist-ui  - Brutalist UI taste (BETA)
  ui-ux-pro-max            - 67 styles, 96 palettes, design intelligence
  graphify                 - Any input -> navigable knowledge graph (pipx: graphifyy)
  21st.dev set (7)         - drive the `21st` CLI: search/install/publish components
  Cloudflare set (11)      - cloudflare/skills: workers, wrangler, durable objects, zero trust
  ECC cherry-pick          - ~40 language/pattern skills + 27 agents + rules/

Moved into jjstack (no longer separate installs)
  council              - Multi-agent deliberation; /consensus adds a 4-vendor panel

MCP servers
  magic (21st-dev)     - Component generation with 21st.dev design system
  context7             - Live library documentation fetcher
```

## Restore on a new machine

See [SKILLS.md](SKILLS.md) and [PLUGINS.md](PLUGINS.md) for exact install commands.
Copy [CLAUDE.md](CLAUDE.md) to `~/.claude/CLAUDE.md`.
Copy [mcp-config.json](mcp-config.json) and merge into `~/.claude.json`.
