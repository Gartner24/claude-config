# claude-config

Personal Claude Code setup: plugins, skills, MCP servers, and global config.

This repo is the source of truth for everything installed on this machine. Use it to
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
| [settings.json](settings.json) | Full `~/.claude/settings.json` (hooks, model, env, plugins) |
| [settings.local.json](settings.local.json) | `~/.claude/settings.local.json` (MCP connectors) |
| [mcp-config.json](mcp-config.json) | `~/.claude.json` mcpServers block |

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

Skill frameworks (self-updating via setup scripts)
  gstack               - GSD project management system (garrytan/gstack)
  jjstack              - Product/UX layer on top of gstack (JesperJurcenoks/jjstack)

Community skills (installed manually or via npx skills add)
  skill-router         - Routes prompts to the right skill automatically
  council              - Multi-agent deliberation for hard decisions
  impeccable           - Frontend design system with /impeccable audit
  design-motion-principles - Emil Kowalski motion design
  high-end-visual-design   - Soft/premium UI taste
  minimalist-ui            - Minimalist UI taste (Notion/Linear)
  industrial-brutalist-ui  - Brutalist UI taste (BETA)
  ui-ux-pro-max            - 67 styles, 96 palettes, design intelligence

MCP servers
  magic (21st-dev)     - Component generation with 21st.dev design system
  context7             - Live library documentation fetcher
```

## Restore on a new machine

See [SKILLS.md](SKILLS.md) and [PLUGINS.md](PLUGINS.md) for exact install commands.
Copy [CLAUDE.md](CLAUDE.md) to `~/.claude/CLAUDE.md`.
Copy [mcp-config.json](mcp-config.json) and merge into `~/.claude.json`.
