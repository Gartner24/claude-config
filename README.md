# claude-config

For you, the owner of this Claude Code setup. Claude Code reads its setup from `~/.claude` (the
**live dir**). This repo keeps your own parts of that folder, names every downloaded skill, plugin and
framework with where it came from, and keeps the retired `wf` runner as history in `_archive/runner/`. An AI
working here reads [AGENTS.md](AGENTS.md) instead.

## Where things live

Each kind of file has one source of truth. The copy that wins is the one you edit; the other is
overwritten.

| Kind | Repo folder | Live path | Source of truth | Who writes it | What moves it |
|------|-------------|-----------|-----------------|---------------|---------------|
| Copied (`CLAUDE.md`, `settings*.json`, `agents/`, `rules/`, `rules-on-demand/`, `MAP.md`, your hooks and scripts) | `claude-home/` | `~/.claude/<same path>` | live wins | you, in `~/.claude` | `bin/sync.sh` copies live into the repo; `bin/install.sh` copies back on a new machine |
| Linked (`skills/`, `commands/` you wrote) | `claude-home/skills/`, `claude-home/commands/` | `~/.claude/skills/<name>` is a symlink (a pointer) into the repo | repo wins | you, in the repo | `bin/install.sh` makes the links |
| Downloaded (skills from GitHub and packages) | `config/manifest.json`, your edits in `config/patches/` | `~/.claude/skills/<name>` | upstream plus your patch | their installer, then you | `/claude-config update`, after your yes per skill |
| Runner (`wf`, `next`, retired 2026-10-21) | `_archive/runner/` | none: it was copied to `~/.local/share/wf/` until it retired | repo wins | nobody; kept as history | nothing |
| Repo tools | `bin/`, `scripts/` | none (a few are linked into `~/.local/bin`) | repo wins | you, in the repo | nothing |
| Frameworks (gstack, jjstack, ECC commands, the JSM skills, plugins) | named in `config/manifest.json` | their own folders in `~/.claude` | their installer wins | their installer | their own installer; never copied here |
| Private (names, work rules, settings fragments, private skills and patches) | none | `~/.claude/private/` | live only | you | nothing; never in any repo |
| Claude Code state (`projects/`, `sessions/`, `history.jsonl`, caches) | none | `~/.claude/...` | Claude Code only | Claude Code | nothing; never synced |

`claude-home/` mirrors `~/.claude`: `claude-home/rules/x.md` installs to `~/.claude/rules/x.md`.
`config/` holds the manifest, patches, the routing table and the MCP config. Guides live in
`docs/guides/`, specs (one per decision) in `docs/specs/`, the plan in `docs/scope/`, third party
notices in [docs/NOTICE.md](docs/NOTICE.md).

**Rules for one place only.** Rules for this repo only go
in [CLAUDE.md](CLAUDE.md), the entry file; `AGENTS.md` is a symlink to it, so a session in this repo
loads the global instructions once and the entry file once. The home chat opens in `~/claude-config`;
its private rules are in `CLAUDE.local.md` (git ignored, spec 0067).

## One session, start to finish

```
claude starts in a folder
  |
  +-- user memory ....... ~/.claude/CLAUDE.md (+ every @import in it, + ~/.claude/rules/*.md)
  +-- project memory .... <folder>/CLAUDE.md or <folder>/.claude/CLAUDE.md, if present
  +-- settings .......... ~/.claude/settings.json, then the folder's .claude/settings*.json
  +-- hooks ............. scripts settings.json names, run on events
  |                       (SessionStart, PreToolUse, Stop, ...)
  +-- skills ............ ~/.claude/skills/<name>/SKILL.md: only the one line description
  |                       loads; the body loads when the skill is invoked (/name or by match)
  +-- skill rules ....... when a skill starts, hooks/skill-rules.py adds its files from
                          ~/.claude/rules-on-demand/ (map.json); nothing else loads them
```

- **User memory** loads in every session. **Project memory** loads only in that folder.
- A **skill** is a folder with a `SKILL.md`. Yours are linked from `claude-home/skills/`; the rest come
  from frameworks and downloads, all listed in [docs/guides/SKILLS.md](docs/guides/SKILLS.md).
- A **hook** is a script Claude Code runs on an event; it can block a tool call. See
  [docs/guides/HOOKS.md](docs/guides/HOOKS.md).
- **Private** files hold work and client names. `bin/sync.sh` and the commit hooks refuse any of
  them reaching this public repo.

## Guides

| Guide | Kind | What it covers |
|-------|------|----------------|
| [SETUP.md](docs/guides/SETUP.md) | how to | Install, restore on a new machine, frameworks, downloaded skills, plugins, MCP servers, keeping it current |
| [DAILY-USE.md](docs/guides/DAILY-USE.md) | how to | The workflow chain, `/claude-config`, picking a skill, and the retired `wf` commands |
| [SKILLS.md](docs/guides/SKILLS.md) | reference | Every skill with its source and license, plus the routing table (generated) |
| [HOOKS.md](docs/guides/HOOKS.md) | reference | Each hook script, where it comes from, the settings it relies on |
| [DESIGN-PIPELINE.md](docs/guides/DESIGN-PIPELINE.md) | how to | Setting up and running the design pipeline |

Also: [docs/architecture.md](docs/architecture.md) (how the chat workflow, hooks, mods, workflows and the setup
sync work) and [docs/research/](docs/research/) (skills tried and kept or dropped, reviews).

## Rules earned the hard way

Each rule below cost something on a real project.

| Rule | Where | Why it exists |
|------|-------|---------------|
| An absent answer rendered as a definite one | `claude-home/rules/ecc/common/code-review.md` | A count that has not loaded is not zero; a failed fetch is not an empty list. One defaulted count switched off the guard on account deletion |
| Get the RED back when the test came second | `claude-home/rules/ecc/common/testing.md` | Bug fixes skip watching the test fail, so break the source, see the test go red, restore |
| A test that reimplements the logic passes forever | `claude-home/rules/ecc/common/testing.md` | A test with a local copy of the behaviour stays green when the real fix is reverted |
| A mock weaker than the real module passes anything | `claude-home/rules/ecc/common/testing.md` | A mock missing one field hid a control that could never render |
| Shell discipline | `claude-home/CLAUDE.md` | A stale `cd` looks like a deleted tree; `$(...)` does not expand in a quoted heredoc |
| Grep before writing against a symbol | `claude-home/CLAUDE.md` | A helper that reads plausibly may not exist |

The ECC language rules are not loaded on their own; [DAILY-USE.md](docs/guides/DAILY-USE.md#language-rules-on-demand)
says how to load one per project.

## Stack overview

```
Languages          Markdown (skills, agents, rules), Bash, Python 3 stdlib, one Node ESM script
Key dependencies   jq (bin/sync.sh), fontTools (design font scripts), culori (build-ramp.mjs,
                   node_modules committed on purpose); no package manager at the root
Plugins            frontend-design, code-review, feature-dev,
                   code-simplifier, ralph-loop, clangd-lsp, ponytail, security-guidance
Skill frameworks   gstack, then jjstack on top;
                   ECC commands; the JSM skills; sentry skills; anthropic security review
Downloaded skills  about 175, each with its source and license in config/manifest.json
MCP servers        context7 (library docs), plus the design MCPs in DESIGN-PIPELINE.md
```

## Restore on a new machine

1. Clone this repo and run `bin/install.sh --dry-run`, then `bin/install.sh`.
2. Install the frameworks, plugins and downloaded skills as [SETUP.md](docs/guides/SETUP.md#restore-on-a-new-machine) says.
3. Merge [config/mcp-config.json](config/mcp-config.json) into `~/.claude.json`.
