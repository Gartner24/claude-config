# 0035 rationale

## Why
Personal plan row 9: `~/.claude` (many sessions run from it, not a git repo) and claude-config (the public copy) are hard to read: which file is the real one, where a rule should go, what a folder is for. Row 9's notes add three asks: make claude-config a child repo like nvim, fix the global instructions loading twice in claude-config sessions, and decide where rules for only one of the two places live.

## Survey (2026-10-14, `ls` only, no file contents, `projects/` not opened)

### claude-config top level today
`AGENTS.md`, `CLAUDE.md` (the synced copy of the global instructions), `.claude/CLAUDE.md` (imports `AGENTS.md`), `README.md`, `NOTICE.md`, `LICENSE`, `install.sh`, `sync.sh`, `settings.json`, `settings.local.json`, `mcp-config.json`, `test-preferences.json`, seven guides at the top (`HOOKS.md`, `MCP.md`, `PLUGINS.md`, `SKILLS.md`, `SKILLS-EVALUATION.md`, `USAGE.md`, `DESIGN-PIPELINE.md`), and the folders `agents/`, `commands/`, `docs/`, `hooks/`, `rules/`, `runner/`, `scripts/`, `skills/`. Payload (what goes to `~/.claude`) and repo tooling sit side by side; `scripts/` mixes both (`chroma-reaper.sh` is payload, `private-names.py` is tooling).

### Why the global instructions load twice
The repo root `CLAUDE.md` is a byte copy of `~/.claude/CLAUDE.md` (`sync.sh:33`). A session started in the repo loads `~/.claude/CLAUDE.md` as user memory and the repo root `CLAUDE.md` as project memory, plus `.claude/CLAUDE.md` (`AGENTS.md` gotcha, `AGENTS.md:63`). Probe P1 confirms before the build.

### `~/.claude` top level today, by kind
| Kind | Entries | Destination |
|---|---|---|
| Copied (live wins) | `CLAUDE.md`, `settings.json`, `settings.local.json`, `agents/`, `rules/`, `hooks/block-destructive.sh`, `hooks/review-stack-pre-push`, `hooks/plain-panel.py`, `scripts/chroma-reaper.sh` | stay |
| Linked into claude-config | about 20 entries in `skills/` and 5 in `commands/` | stay (repointed to `live/` by `install.sh`) |
| Framework owned | `skills/jjstack`, `skills/gstack` and their links, `get-shit-done/`, `gsd-*` hooks, `vendor-jsm-skills/` and its 7 skill links, `plugins/`, `gsd-file-manifest.json`, `.skills-manifest.json`, `package.json`, the jjstack hook links in `hooks/` | stay, documented, never edited |
| Authored here, not in any repo | `conductor/`, `scripts/claude-ram-watch.sh`, `hooks/workflow-start.sh`, `hooks/claude-mem-install.sh`, a few skill folders that are neither links nor framework | listed in `migrate.md`; each one either joins `live/` (synced) or stays local with a reason |
| Private | `private/`, `.credentials.json`, `.claude.json` | stay, never synced |
| Claude Code state | `projects/`, `sessions/`, `history.jsonl`, `file-history/`, `shell-snapshots/`, `session-env/`, `paste-cache/`, `cache/`, `telemetry/`, `ide/`, `debug/`, `logs/`, `tasks/`, `jobs/`, `uploads/`, `downloads/`, `daemon*`, `bridge-spawn/`, `seed-admin/`, `dev-mods/`, `state/`, `security/`, `feedback/`, `chrome/`, `.cc-writes/` | stay, never touched |
| Leftovers | 8 `settings.json.bak*` files at the top, one `.claude.json.tmp.*` from September, `.design-last-*` pointers (12) and `.design-active`, `skills/.trash/`, `backups/` (11 dated folders) | attic, one per step, after checking nothing reads them (the design ledger reads `.design-last` and `.design-active`, `skills/design/scripts/ledger.sh`, so only pointers whose session is gone move) |

## Decided without asking (2026-10-14)
Per `docs/briefs/finish-runner-today.md`, the recommended option was taken for every question.

| Question | Options | Pick |
|---|---|---|
| Source of truth | (a) keep three kinds (copied, linked, runner) and document them; (b) repo wins for everything: link `agents/`, `rules/`, `CLAUDE.md` too; (c) live wins for everything | (a). (b) would make live rules change whenever the claude-config checkout switches branch, and `wf` hashes the live dir (spec 0007, spec 0021 AC-7), so a branch switch would stop runs in other repos. Settings cannot be linked anyway: `sync.sh` strips `autoMode` and private entries out of them (`sync.sh:21-31`). (c) would lose the runner and authored skills' single copy. |
| Repo shape | (a) payload under `live/`, mirroring `~/.claude`; (b) leave payload at the top, only fix `CLAUDE.md`; (c) `home/` like dotfiles | (a). The path answers "where does this go live" by itself, and repo tooling stops mixing with payload. `home/` would mean `$HOME` in dotfiles but `~/.claude` here; `live/` matches the word `AGENTS.md` already uses ("edit the live file"). |
| Double load fix | root `CLAUDE.md` becomes the `AGENTS.md` import and the global copy moves to `live/CLAUDE.md`; keep the copy and add a `claudeMdExcludes` setting | Move it. It also gives the repo the same pointer file every other repo has. |
| Rules only for `~/.claude` sessions | `~/.claude/.claude/CLAUDE.md`; a section in the global `CLAUDE.md`; a file in `rules/` | `~/.claude/.claude/CLAUDE.md`: it is project memory for that folder only, so other sessions never load it. A section in the global file or `rules/` would load everywhere. |
| Rules only for claude-config | `AGENTS.md`; a `rules/` file | `AGENTS.md`, as today. `rules/` here is the copy of the global rules and loads everywhere. |
| Child repo | submodule of dotfiles; stay separate | Submodule at `~/dotfiles/claude-config`: the dotfiles repo already decided it (its spec 0001 AC-16, and its program inventory lists claude-config as a submodule). `~/claude-config` stays as a symlink so every path in scopes, memories and settings keeps working. |
| How the submodule is made | move the existing clone into place and `git submodule add` it; clone fresh from GitHub | Move the existing clone: a fresh clone loses unpushed branches, stashes and worktrees. Probe P4 checks it first on copies. |
| Where conductor sessions run | keep `~/.claude`; move to claude-config | Keep `~/.claude`: their memory folder is keyed by that path, and their tools live in `~/.claude/conductor/`. The README says so. |
| Leftovers | delete; move to an attic | Attic, never delete (the ask: never lose a file). Deleting the attic later is your call. |
| Guides | `docs/guides/`; keep at top | `docs/guides/`: the top then holds only what a reader needs first. |
| README length | under 1200 words; no cap | Under 1200 words, about five minutes. Detail stays in the guides and `docs/architecture.md`. |

## Risks
- Moving payload paths breaks every open branch that touches them. Precondition in AC-8: the release branch is merged first and no worktree is open.
- A real path change resets `wf` state keys (trust list, locks, queue use the real path). AC-6 reruns `wf allow`; open questions in `queue.json` for the old path are answered or cleared before the move.
