# Architecture

For `/architect` and for you when a decision touches how this setup works. One page view of today's system: a chat
driven workflow, the hooks and mods around it, the workflows, and how this repo reaches `~/.claude`. `/architect`
reads this first (rule `spec-gate.md`) and updates it in the same commit when a decision changes an invariant. The
retired `wf` runner's design is kept as history in [_archive/runner/docs/architecture.md](../_archive/runner/docs/architecture.md).

## Components

| Part | What it is | Where |
|---|---|---|
| Global instructions | `~/.claude/CLAUDE.md` plus every `*.md` directly in `~/.claude/rules/`, loaded into every chat (spec 0077 AC-1: at most 20,000 characters). The code rules, the two review questions and one Routing block of one line per situation | `claude-home/CLAUDE.md`, `claude-home/rules/` |
| Rules on demand | rules tied to a skill or a situation, not loaded until needed (spec 0077) | `claude-home/rules-on-demand/`, its `map.json` |
| Skill rules hook | `skill-rules.py`: when a skill starts (PreToolUse `Skill`) or the owner types `/<name>` (UserPromptSubmit), prints that skill's mapped files from `map.json` as context | `claude-home/hooks/skill-rules.py` |
| Pointer lines | a situation rule (a merge, a commit, a "done" claim) keeps one Routing line in `CLAUDE.md` naming the file to read | `claude-home/CLAUDE.md` |
| Workflow skills | `/scope`, `/architect`, `/develop`, `/check`, `/test`, `/sync` (the JSM skills), `/debug`, `/document`; downloaded, overwritten on every pull, so never patched for our rules | `config/manifest.json` |
| Plan and decisions | `docs/scope/` (the plan: features, boxes, tags), `docs/specs/` (one spec per decision), `docs/briefs/` (agreed items between chats), `docs/reviews/` | each repo |
| Hooks | scripts `settings.json` runs on events: the Bash guard (`block-destructive.sh`), the panel check (`plain-panel.py`), the context monitor, the chat start hooks (`workflow-start.sh`, `handover-start.sh`), the Stop hook that refuses to end a turn while a planned step is owed (`chain-catch.py`, spec 0070), the live tick guard (`live-tick.py`, spec 0075), the skill rules hook | `claude-home/hooks/`, [HOOKS.md](guides/HOOKS.md) |
| Mods | `wf-handoff`: starts `/audit` or `/scope` when a chat opens in a repo, `/handoff`, and the automatic handoff at the token line. `chip-dash`: the band and panes | `claude-home/mods/` |
| Workflows | numbered stage folders with a contract each, run straight through by one Workflow script and started by a `/<name>` command (spec 0076); built with `workflow-builder` | `claude-home/workflows/` |
| Install and sync | `bin/install.sh` (repo to `~/.claude`), `bin/sync.sh` (live copies back), `bin/claude-config.py` (`drift`, `hook-files`, `update`, `docs`), spec 0048 | `bin/` |
| Repo tools | helper scripts, some linked into `~/.local/bin` (`spec-paths`, `fb-ask`, `skill-scan`, the switch-on helpers) | `scripts/` |

## Data flow

```
chat opens in a repo
  |-- CLAUDE.md + rules/*.md load (always)
  |-- wf-handoff mod sends /audit or /scope  --> UserPromptSubmit --> skill-rules.py adds that skill's rules
  v
owner types /architect x  --> UserPromptSubmit --> skill-rules.py adds architect's rules
Claude starts a skill      --> PreToolUse Skill --> skill-rules.py adds its rules
  |
  v
skills read and write docs/scope/, docs/specs/, docs/briefs/, code
  |
  v
turn ends --> chain-catch.py (Stop): a planned step still owed? block, name it (at most 3 times)
```

Probe P3 (spec 0077 verify.md) showed the mod's chat start `/scope` reaches UserPromptSubmit as `"prompt":"/scope"`,
so the start skill gets its rules the same way a typed one does.

## Invariants (hold everywhere)

1. **One source of truth per kind.** Copied files (`CLAUDE.md`, `settings*.json`, `agents/`, `rules/`,
   `rules-on-demand/`, the listed hooks, `MAP.md`): live wins, edit in `~/.claude`, then `bin/sync.sh`. Linked files
   (`skills/`, `commands/`, `workflows/<name>/`) and mods: repo wins. Downloaded skills: upstream plus a patch.
   Private files: `~/.claude/private/`, live only.
2. **Downloaded skills are never patched for our rules.** A rule a workflow skill must follow lives in
   `rules-on-demand/` and reaches the skill through `map.json` and the skill rules hook, or in an always loaded file.
3. **State lives in repo files**, never only in chat: the scope, the specs, the briefs, `AGENTS.md`.
4. **Nothing pushes, merges, posts or bills without the owner's yes**, except the self merge checklist in own repos
   (`rules-on-demand/when-to-switch-on.md`).
5. **Hooks fail open.** A hook that breaks (bad input, missing file) prints nothing and exits 0, so a broken hook
   never stops a chat; its `--test` self check runs in install verify.
6. **The repo is public.** No client or employer names, keys or machine state; the commit hooks and `bin/sync.sh`
   refuse a private name.

## Setup sync

Spec [0048](specs/0048-organize-and-sync/index.md). `bin/claude-config.py`, driven by the `/claude-config` skill,
keeps `claude-home/` and `~/.claude` in step: `sync` (live to repo, through `bin/sync.sh`), `install` (repo to live,
through `bin/install.sh`), `drift` (everything in one place and not the other, exit 1 when any), `update --plan` and
`update --apply <entry>`, `docs` (writes `docs/guides/SKILLS.md`). Install moves a live file in `rules/` or
`rules-on-demand/` with no repo source to `~/.claude/backups/rules/<date>/`, so a moved rule stops auto loading
(spec 0077 AC-7). `~/.claude/MAP.md` points a chat that edits `~/.claude` back to this repo (AC-6).

## Specs

`docs/specs/NNNN-title.md`, or the folder form `NNNN-title/index.md`. Each names the files it governs on its
`**Paths:**` line; `spec-paths` warns when a governed file changed after the spec.
