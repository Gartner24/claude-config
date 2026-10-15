# claude-config

A personal Claude Code setup, kept in git. Claude Code reads its setup from `~/.claude` (the
**live dir**). This repo keeps the hand written parts of that folder, plus `wf`, a runner that
builds queued features for you.

## Where things live

Each kind of file has one source of truth. The copy that wins is the one you edit; the other is
overwritten.

| Kind | Repo folder | Live path | Source of truth | Who writes it | What moves it |
|------|-------------|-----------|-----------------|---------------|---------------|
| Copied (`CLAUDE.md`, `settings*.json`, `agents/`, `rules/`, hand written hooks, `chroma-reaper.sh`) | `live/` | `~/.claude/<same path>` | live wins | you, in `~/.claude` | `./sync.sh` copies live into the repo; `./install.sh` copies back on a new machine |
| Linked (`skills/`, `commands/` authored here) | `live/skills/`, `live/commands/` | `~/.claude/skills/<name>` is a symlink (a pointer) into the repo | repo wins | you, in the repo | `./install.sh` makes the links |
| Runner (`wf`, `next`) | `runner/` | `~/.local/share/wf/<fp>/`, linked from `~/.local/bin/wf` | repo wins | you, in the repo | `./install.sh` copies it out |
| Repo tools | `scripts/` | none (two are linked into `~/.local/bin`) | repo wins | you, in the repo | nothing |
| Frameworks (gstack, jjstack, get-shit-done-cc, the JSM skills, plugins) | none, documented in `docs/guides/` | their own folders in `~/.claude` | their installer wins | their installer | their own installer; never copied here |
| Private (names, work rules, settings fragments) | none | `~/.claude/private/` | live only | you | nothing; never in any repo |
| Claude Code state (`projects/`, `sessions/`, `history.jsonl`, caches) | none | `~/.claude/...` | Claude Code only | Claude Code | nothing; never synced |

`live/` mirrors `~/.claude`: `live/rules/x.md` installs to `~/.claude/rules/x.md`. Guides live in
`docs/guides/`, specs (one per decision) in `docs/specs/`, the plan in `docs/scope/`.

**Rules for one place only.** Rules for sessions started in `~/.claude` (the conductor sessions)
go in `~/.claude/.claude/CLAUDE.md`, project memory for that folder. Rules for this repo only go
in [AGENTS.md](AGENTS.md); the root `CLAUDE.md` here is just the import of it, so a session in
this repo loads the global instructions once and `AGENTS.md` once.

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
                          loads; the body loads when the skill is invoked (/name or by match)

wf run (the runner)
  reads docs/scope/ of a trusted repo -> picks the next unticked box -> starts
  `claude -p "<the box's command>"` (one headless session per step) in a sandbox
  -> records the result, ticks the box or asks you on your phone
```

- **User memory** loads in every session. **Project memory** loads only in that folder.
- A **skill** is a folder with a `SKILL.md`. Ours are linked from `live/skills/`; the rest come
  from frameworks and `npx skills add`, listed in [docs/guides/SKILLS.md](docs/guides/SKILLS.md).
- A **hook** is a script Claude Code runs on an event; it can block a tool call. See
  [docs/guides/HOOKS.md](docs/guides/HOOKS.md).
- **Private** files hold work and client names. `sync.sh` and the commit hooks refuse any of
  them reaching this public repo.

## Guides

| Guide | What it covers |
|-------|----------------|
| [PLUGINS.md](docs/guides/PLUGINS.md) | Official plugins (`claude plugin install`) |
| [SKILLS.md](docs/guides/SKILLS.md) | Community skills and frameworks, with install commands |
| [MCP.md](docs/guides/MCP.md) | MCP servers (tools Claude can call) |
| [HOOKS.md](docs/guides/HOOKS.md) | Each hook script and where it comes from |
| [USAGE.md](docs/guides/USAGE.md) | Which skill to reach for, plus the routing table the intent router reads |
| [DESIGN-PIPELINE.md](docs/guides/DESIGN-PIPELINE.md) | Design pipeline setup notes |
| [SKILLS-EVALUATION.md](docs/guides/SKILLS-EVALUATION.md) | Skills tried and kept or dropped |

## Rules earned the hard way

Each rule below cost something on a real project.

| Rule | Where | Why it exists |
|------|-------|---------------|
| An absent answer rendered as a definite one | `live/rules/ecc/common/code-review.md` | A count that has not loaded is not zero; a failed fetch is not an empty list. One defaulted count switched off the guard on account deletion |
| Get the RED back when the test came second | `live/rules/ecc/common/testing.md` | Bug fixes skip watching the test fail, so break the source, see the test go red, restore |
| A test that reimplements the logic passes forever | `live/rules/ecc/common/testing.md` | A test with a local copy of the behaviour stays green when the real fix is reverted |
| A mock weaker than the real module passes anything | `live/rules/ecc/common/testing.md` | A mock missing one field hid a control that could never render |
| Shell discipline | `live/CLAUDE.md` | A stale `cd` looks like a deleted tree; `$(...)` does not expand in a quoted heredoc |
| Grep before writing against a symbol | `live/CLAUDE.md` | A helper that reads plausibly may not exist |

The ECC language rules are not auto loaded. Add one line to a project's `CLAUDE.md`, for example
`@~/.claude/rules/ecc/typescript/index.md` (or `python`, `golang`, `rust`, `java`, `web`, `common`).

## Stack overview

```
Plugins            superpowers, claude-mem, frontend-design, code-review, feature-dev,
                   code-simplifier, ralph-loop, clangd-lsp, ponytail, security-guidance
Skill frameworks   gstack, then jjstack on top; get-shit-done-cc pinned at 1.34.2, hooks only
Community skills   impeccable, graphify, the 21st.dev and Cloudflare sets, an ECC cherry pick
MCP servers        magic (21st.dev components), context7 (library docs)
```

## Restore on a new machine

1. Clone this repo and run `./install.sh --dry-run`, then `./install.sh`.
2. Install the frameworks and plugins from [docs/guides/SKILLS.md](docs/guides/SKILLS.md) and
   [docs/guides/PLUGINS.md](docs/guides/PLUGINS.md).
3. Merge [mcp-config.json](mcp-config.json) into `~/.claude.json`.
