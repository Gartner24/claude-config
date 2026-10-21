# 0035 · A layout a person can read: ~/.claude and claude-config

**Date**: 2026-10-14
**Status**: In Progress
**Paths:** `README.md`, `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`, `claude-home/` (new: today's `agents/`, `rules/`, `hooks/`, `commands/`, `skills/`, `settings.json`, `settings.local.json`, the global `CLAUDE.md` and `scripts/chroma-reaper.sh` move under it), the docs guides folder (new: `HOOKS.md`, `MCP.md`, `PLUGINS.md`, `SKILLS.md`, `SKILLS-EVALUATION.md`, `USAGE.md`, `DESIGN-PIPELINE.md` move there), `bin/sync.sh`, `bin/install.sh`, `scripts/check-routing.py`, `scripts/gen-agent-index.py`, `scripts/asciify.py`, `scripts/private-names.py`, `runner/tests/` (tests that read repo `rules/` paths, for example `runner/tests/test_one_command.py:12`)
**Amends**: none. Carries out the claude-config placement already decided in the dotfiles repo (its spec 0001 AC-16: claude-config becomes a git submodule of dotfiles at `claude-config/`).
**Amended by**: [0067](../0067-home-chat-in-claude-config/index.md) - AC-5: the home chat opens in `~/claude-config` and the runner rules live in the git ignored `CLAUDE.local.md`.

## What you're agreeing to
- One README in claude-config explains, in a few minutes of reading, what lives in `~/.claude`, what lives in claude-config, which copy wins for each kind of file, and how sessions, skills, hooks, rules, the runner and the private folder fit together.
- claude-config gets a clear shape: everything that is installed into `~/.claude` sits under one folder named `live/`, the runner and repo tools stay at the top, guides move to `docs/guides/`. The global instructions stop loading twice in claude-config sessions.
- claude-config becomes a child repo (git submodule) of dotfiles, like nvim, and `~/claude-config` keeps working as a link to it.
- Nothing is deleted. Leftovers in `~/.claude` move into a dated attic folder, one at a time, after a full backup, with a check after each move that `~/.claude` still works.

## Terms used below
- **Live dir**: `~/.claude`, the folder Claude Code reads at every session start (user memory `CLAUDE.md`, `settings.json`, `rules/`, `skills/`, `hooks/`, `agents/`, `commands/`) and writes its own state into (`projects/`, `sessions/`, `history.jsonl`, ...).
- **Copied file**: a file that exists in both places as two copies; the live one is edited and `sync.sh` copies it into the repo (`sync.sh:33-47`). **Linked file**: a live path that is a symlink into the repo, so the repo file is the one edited (`install.sh:42-55`).
- **Project memory**: a `CLAUDE.md` (or `.claude/CLAUDE.md`) in the folder a session starts in; Claude Code loads it on top of the user memory `~/.claude/CLAUDE.md`.
- **Submodule**: a git repo kept inside another repo's tree at a pinned commit; the parent records only which commit (dotfiles does this for nvim, `~/dotfiles/.gitmodules`).
- **Attic**: `~/.claude/backups/attic-<date>/`, where a leftover goes instead of being deleted.

## Acceptance criteria
- **AC-1** (README): `README.md` opens with a "Where things live" map: one table row per kind (copied, linked, runner, framework, private, Claude Code state), naming the folder, which copy is the source of truth, who writes it, and the command that moves it (`sync.sh`, `install.sh`, a framework's own installer, nothing). Then one diagram of a session: what loads at start (user memory, project memory, rules, settings, hooks), what a skill is and where it comes from, how `wf` starts `claude -p` calls. Under 1200 words, every technical term glossed at first use, ASCII only (`scripts/asciify.py --check` passes). The current sections ("Rules earned the hard way", "Stack overview", "Restore on a new machine") stay, shortened, below the map.
- **AC-2** (sources of truth, one rule per kind): copied kinds (`CLAUDE.md`, `settings*.json`, `agents/`, `rules/`, the hand written hooks and `chroma-reaper.sh`): live wins, `sync.sh` mirrors. Linked kinds (`skills/`, `commands/` authored here): repo wins. Runner: repo wins, `install.sh` copies it to `~/.local/share/wf/<fp>/` (spec 0020). Frameworks (gstack, jjstack, get-shit-done-cc, the JSM skills, plugins): their installer wins, never vendored. Private (`~/.claude/private/`): live only, never in any repo. Claude Code state: Claude Code only, never synced. The README table and `AGENTS.md` `## Rules` say exactly this and nothing contradicting it.
- **AC-3** (repo shape): everything `install.sh` puts into the live dir sits under `live/`, at the same relative path it has under `~/.claude` (`live/rules/x.md` goes to `~/.claude/rules/x.md`). The global instructions are `live/CLAUDE.md`. `sync.sh`, `install.sh` and every script naming those paths use `live/`. The repo top holds only `README.md`, `AGENTS.md`, `CLAUDE.md`, `NOTICE.md`, `LICENSE`, `install.sh`, `sync.sh`, `mcp-config.json`, `test-preferences.json`, `live/`, `runner/`, `scripts/`, `docs/`, `.claude/`, `.gitignore`. Guides move to `docs/guides/`, links to them updated (a link check: every relative markdown link in repo-owned markdown resolves).
- **AC-4** (no double load): the repo root `CLAUDE.md` holds only the import of `AGENTS.md`, and `.claude/CLAUDE.md` is removed. A session started in claude-config loads the global instructions once (as user memory) and `AGENTS.md` once (probe P1 before, the same probe after).
- **AC-5** (rules for one place only): rules that apply only to sessions started in `~/.claude` (the conductor sessions) live in `~/.claude/.claude/CLAUDE.md` (project memory for that folder, next to the `settings.local.json` already there). Rules that apply only to claude-config stay in `AGENTS.md`. The README says both. Probe P2 decides whether a session in `~/.claude` loads `~/.claude/CLAUDE.md` twice; if it does, `~/.claude/.claude/CLAUDE.md` says so and the README notes it as a known Claude Code behavior (the file cannot move: it is the user memory).
- **AC-6** (child repo): claude-config is a submodule of dotfiles at `~/dotfiles/claude-config`, keeping every local branch, tag, stash and worktree it had (the existing clone is moved into place, never recloned). `~/claude-config` is a symlink to it. The `wf` trust list, locks and queue name the new real path (`wf allow` rerun), and the session memory folder for the old path is copied, not moved, to the new key if Claude Code keys by real path (probe P3).
- **AC-7** (`~/.claude` tidy, nothing lost): every top level entry of the live dir appears in the README map or in `migrate.md`'s inventory with a destination: stays, attic, or framework-owned. Leftovers go to the attic one per step (the inventory lists them: old `settings.json.bak.*`, a stale `.claude.json.tmp.*`, old `.design-last-*` pointers no design run holds, `skills/.trash`). `install.sh` writes its future settings backups into `~/.claude/backups/settings/`, not the live dir top.
- **AC-8** (migration safety, `migrate.md`): the move is a numbered list of steps. Step 0 makes the backups: a `tar` of the whole live dir (mode 0600, outside `~/.claude`, `projects/` included), `git bundle create <file> --all` of claude-config, and the private folder copied separately. Every later step is one move, followed by its check (`./install.sh --dry-run` exits 0, `python3 -c 'import json; json.load(open(...))'` on both settings files, `claude -p` with a one word prompt exits 0, `wf queue` exits 0) and the exact command to undo it. Preconditions: no `wf` lock held, no `wf-auto` unit running, the release branch merged, `git worktree list` shows only the main checkout.
- **AC-9** (checks still pass): after the move every command in `AGENTS.md` `## Commands` passes with its new paths, and `python3 -m unittest discover -s runner/tests` passes.

## Build plan
1. Probes P1 to P4, results in `verify.md`. No file moves before they pass.
2. `migrate.md`: the inventory of both trees and the numbered steps with checks and undo commands. AC-7, AC-8.
3. Repo shape on a branch: `git mv` into `live/` and `docs/guides/`, path updates in `sync.sh`, `install.sh` and scripts, root `CLAUDE.md` as the `AGENTS.md` import, link check. AC-3, AC-4, AC-9.
4. README and `AGENTS.md` rewrite. AC-1, AC-2, AC-5.
5. Live steps, each a ` · waits on you` box (they write `~/.claude`, `~/dotfiles` and `~/.config/wf`, which no `wf` call may touch, spec 0021 AC-7): backups, attic moves one per box, `~/.claude/.claude/CLAUDE.md`, the submodule move and symlink, `wf allow`, memory folder copy. AC-5, AC-6, AC-7, AC-8.

## Probes
Run by you before the build (they call the real `claude`):
- **P1** double load in claude-config: `cd ~/claude-config && claude -p "/context"`; read the memory files list. Expected today: `~/.claude/CLAUDE.md` plus the repo root `CLAUDE.md` (the same text) plus `.claude/CLAUDE.md`.
- **P2** double load in `~/.claude`: `cd ~/.claude && claude -p "/context"`; does `~/.claude/CLAUDE.md` appear once or twice?
- **P3** memory key through a symlink: `mkdir -p /tmp/p3real && ln -s /tmp/p3real /tmp/p3link && cd /tmp/p3link && claude -p "say ok"`, then `ls ~/.claude/projects | grep p3`: is the folder named after `p3link` or `p3real`?
- **P4** submodule from an existing clone, on throwaway copies only: `git clone ~/dotfiles /tmp/p4dot && cp -a ~/claude-config /tmp/p4dot/claude-config && git -C /tmp/p4dot submodule add <claude-config GitHub URL> claude-config`; then `git -C /tmp/p4dot/claude-config branch -a` shows every branch and `git -C /tmp/p4dot status` shows the new `.gitmodules` entry. Remove both temp folders after.

## Follow-up
- Linked skills follow whichever branch the claude-config checkout is on, so a `wf` run on a feature branch already changes live skills for every session. Recorded, not changed here.
- The SessionStart hook `claude-mem-install.sh` still runs while claude-mem is off (personal plan row 1 decides claude-mem).
- The dotfiles side (`dot install` and `dot sync` calling claude-config's `install.sh` and `sync.sh`) is dotfiles' own spec 0001 AC-16 build, not this one.
