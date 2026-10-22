# claude-config

For an AI agent working in this repo. This file only routes and holds the rules you must not break;
`AGENTS.md` is a symlink to it (edit this file, never replace the link). What the repo is and where things
live: [README.md](README.md). Everything else is a card in [map/](map/CLAUDE.md): open the card of the part
you change, not all of them. The runner's design is in [docs/architecture.md](docs/architecture.md), the
commands a person types in [docs/guides/DAILY-USE.md](docs/guides/DAILY-USE.md).

## Never break

- This repo is public. No client or employer names, repo names, domains, env-file names, keys, tokens or
  machine state. Private names live in `~/.claude/private/` and a commit that holds one fails closed.
- No Claude attribution in commits, PRs or files.
- ASCII only in repo-owned markdown: no em dashes, smart quotes, Unicode bullets. The middle dot is allowed
  (scope tag separator).
- Conventional Commits (`feat(scope):`, `fix(scope):`, `chore:`, `docs:`); a gsd hook enforces the format.
- Do not bypass hooks with `--no-verify`. Do not replace the `AGENTS.md` link.
- Rules for this repo only go in this file. The home chat's private rules are in `CLAUDE.local.md` (git ignored, spec 0067).
- Root `CLAUDE.md` is not the global one: the payload copy of `~/.claude/CLAUDE.md` is `claude-home/CLAUDE.md`.

## Commands

```bash
python3 tests/fast.py          # the suite: only tests for live code
bin/install.sh --dry-run       # repo -> ~/.claude (copies + symlinks), then self-checks
bin/sync.sh                    # ~/.claude -> repo; run before every commit, then git diff
python3 bin/claude-config.py drift   # exits 1 when the repo and ~/.claude differ
```

Every other command: [checks](map/processes/checks.md), [sync](map/processes/sync.md),
[install](map/processes/install.md), [land a feature](map/processes/land-a-feature.md).

## Map

| Change | Open |
|---|---|
| Anything | [map/CLAUDE.md](map/CLAUDE.md), then the card of the part |
| What a change also moves | [map/effects/CONTEXT.md](map/effects/CONTEXT.md) |

## Standing answers

- run suite: yes
- done: yes
- suite: python3 tests/fast.py

## Agent skills

Declined: Agent Skill and MCP discovery for this stack (2026-10-11)

## Context files

- [claude-home/skills/design/AGENTS.md](claude-home/skills/design/AGENTS.md): design and brand pipeline scripts, the run ledger, and its Stop hook
