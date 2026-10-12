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
wf allow <repo>                                 # trust list (spec 0008); wf run refuses `untrusted` (exit 5) for a repo not in $XDG_CONFIG_HOME/wf/allowed.json, else ~/.config/wf/allowed.json
wf ntfy init|codes|test                         # phone pings for wf run decisions (spec 0005); config ~/.config/wf/ntfy.json (0600), wf run refuses without it
```

## Specs

`docs/specs/NNNN-title.md` (folder form `NNNN-title/index.md` for split specs): 0001 runner stack, 0002 `next`, 0003 scope contract, 0004 `wf run`, 0005 decision parking and phone pings, 0006 standing answers, 0007 push guard, 0008 failure and park policy, 0009 headless verify and test, 0010 design enforcement, 0011 build and decision queue, 0012 waiting boxes owed to you.

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
- The middle dot `·` is allowed in repo markdown despite the ASCII rule: it is the scope tag separator (`rules/scope-contract.md`) that `runner/wf.py` parses, and `asciify.py` keeps it.
- `jjstack/` is gitignored /review scratch; reports never enter the repo from there.
- Runner fixtures are flat files (`runner/tests/fixtures/*.md`) that tests copy into `docs/scope/` or `.workflow/scope/` trees in temp dirs: `.workflow/` is globally gitignored, so a fixture tree there would never be committed. Keep them trimmed and free of client names (public repo).
- Scripts hardcode `~/.claude/skills/...` paths: they run through the symlink, not from the repo path.
- `claude -p` (2.1.296) never offers AskUserQuestion, so `wf run` steps ask through `DECISION NEEDED:` plus `OPTION:` lines (spec 0005); rerun its verify.md check 1 probe after a Claude Code upgrade. The Android ntfy app cannot type into a topic; typed replies go through the topic page in a phone browser.
- A repo's `## Standing answers` takes `run suite`, `done` (spec 0006), and `app start` plus `app url` together (spec 0009): with both, `/check verify` and debug calls run the app in a `bwrap` jail and drive it through a pinned headless chrome-devtools MCP (`MCP_PACKAGE`); `app url` must be `http(s)://localhost|127.0.0.1|[::1]:<port>`. Bumping `MCP_PACKAGE` reruns spec 0009 probes P2 to P7 and updates `BROWSER_TOOLS`.
- Spec 0010 rests on `design-gate` (a `context: fork` skill) running inside `claude -p` and writing `.design/audit-report.md`; rerun its verify.md P1 and P2 after a Claude Code upgrade. Under `wf run` the prompt line stops a call from even trying `Skill(design)`, so the deny itself is only provable with a direct `claude -p` carrying `run.py`'s deny lists (P3).
- Every `wf run` call is guarded outside the model (spec 0007): stripped credentials, Claude Code's Bash sandbox, hashed hook and git config files. `wf run` refuses `no_sandbox` without `bwrap` and `socat` on PATH. After a Claude Code upgrade rerun `python3 docs/specs/0007-push-guard/probes/run-wf-probe.py` (about 2 minutes, run it yourself with `!`) and record it in that spec's `verify.md`. The model ignores the probe's step order sometimes; a classifier lockout then hides the sandbox result for later steps.

## Agent skills

Declined: Agent Skill and MCP discovery for this stack (2026-10-11)

## Context files

- [skills/design/AGENTS.md](skills/design/AGENTS.md): design and brand pipeline scripts, the run ledger, and its Stop hook

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
