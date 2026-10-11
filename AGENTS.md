# claude-config

Public snapshot of a personal Claude Code setup (`~/.claude`): global instructions, settings,
agents, rules, hooks, and authored skills. Frameworks (gstack, jjstack, get-shit-done-cc,
plugins) are documented in `SKILLS.md` / `PLUGINS.md`, never vendored.

## Stack

- **Language / Runtime**: Markdown (skills, agents, rules), Bash, Python 3, Node (one ESM script)
- **Framework**: none; files are read by the Claude Code harness
- **Key dependencies**: `jq` (sync.sh), `fontTools` (design font scripts), `culori` (build-ramp.mjs, `node_modules` committed on purpose)
- **Package manager**: none at root; `skills/design/scripts/package.json` only

## Build approach

Skateboard (each stage is usable on its own, and each next stage grows the same tool).

## Commands

```bash
./install.sh --dry-run                          # repo -> ~/.claude (copies + symlinks), then self-checks
./sync.sh                                       # ~/.claude -> repo; run before every commit, then git diff
python3 scripts/check-routing.py                # after editing USAGE.md or a skill's triggers
python3 scripts/gen-agent-index.py --check      # after touching agents/ (drop --check to regenerate)
python3 scripts/asciify.py --check              # ASCII-only lint on repo-owned markdown
bash hooks/block-destructive.sh --test          # guard hook self-checks
bash skills/design/scripts/test-ledger.sh       # design ledger + Stop hook assertions
node skills/design/scripts/build-ramp.mjs --check
python3 -m unittest discover -s runner/tests    # wf runner self checks (install.sh runs these)
wf run <repo>                                   # one feature unattended (spec 0004); locks and run records in $XDG_STATE_HOME/wf, else ~/.local/state/wf
```

## Specs

None yet. When they exist: `docs/specs/NNNN-title.md`.

## Rules

- Two kinds of file. `skills/` and `commands/` are symlinked into `~/.claude`, so editing here is live. `CLAUDE.md`, `settings*.json`, `agents/`, `rules/`, `hooks/block-destructive.sh`, `hooks/review-stack-pre-push`, `scripts/chroma-reaper.sh` are copies: edit the live file in `~/.claude`, then `./sync.sh`. An edit made here is overwritten on the next sync.
- `runner/` is a third kind: `wf`, the workflow runner (spec 0001). `install.sh` symlinks `runner/wf.py` to `~/.local/bin/wf` and `~/.local/bin/next` (called as `next`, it acts as `wf next`), so edit it here. Python 3 stdlib only, tests are `unittest`, external commands go through `subprocess` with argument lists, never a shell string.
- This repo is public. No client or employer names, repo names, domains, or env-file names. `sync.sh` strips `autoMode` from settings.json; client skills are gitignored.
- Do not edit vendored trees: `agents/` (27 of 31 from ECC), `rules/ecc/` (except the 7 `index.md` and the local additions in `common/code-review.md`, `common/testing.md`), `skills/anti-ai-writing/`. Provenance lives in `NOTICE.md`; update it when adding an authored or redistributed path.
- ASCII only in repo-owned markdown: no em dashes, smart quotes, Unicode bullets.
- Conventional Commits (`feat(scope):`, `fix(scope):`, `chore:`, `docs:`); a gsd hook enforces the format.
- Comments explain why, usually naming the past failure ("this used to..."). Keep that style when fixing a script.
- Self-checks are the tests. A change to a script ships with its assertion in the matching `--test` / `--check` / `test-*.sh`.

## Gotchas

- Root `CLAUDE.md` is NOT this repo's context. It is the payload copy of `~/.claude/CLAUDE.md` that `sync.sh` overwrites and `install.sh` ships. Repo context is this file, loaded via `.claude/CLAUDE.md`.
- `asciify.py` skips only `agents/`, `rules/` and `anti-ai-writing`, so it flags the committed `culori` README. Never run it without `--check` first.
- `jjstack/` is gitignored /review scratch; reports never enter the repo from there.
- Runner fixtures are flat files (`runner/tests/fixtures/*.md`) that tests copy into `docs/scope/` or `.workflow/scope/` trees in temp dirs: `.workflow/` is globally gitignored, so a fixture tree there would never be committed. Keep them trimmed and free of client names (public repo).
- Scripts hardcode `~/.claude/skills/...` paths: they run through the symlink, not from the repo path.

## Agent skills

Declined: Agent Skill and MCP discovery for this stack (2026-10-11)

## Context files

- [skills/design/AGENTS.md](skills/design/AGENTS.md): design and brand pipeline scripts, the run ledger, and its Stop hook

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
