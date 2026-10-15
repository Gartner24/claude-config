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
python3 hooks/plain-panel.py --test             # panel hook self checks (spec 0028): "Learn this first" last, at most 3 real options, no jargon
bash skills/design/scripts/test-ledger.sh       # design ledger + Stop hook assertions
node skills/design/scripts/build-ramp.mjs --check
python3 -m unittest discover -s runner/tests    # wf runner self checks (install.sh runs these)
python3 runner/e2e/run.py                       # real claude end to end on a temp fixture repo (spec 0014); run it yourself with `!` after a Claude Code upgrade or runner change, prints PASS or FAIL: <check>; `--parallel` checks two real repos build side by side (spec 0017); `--beside` checks a bare `wf -y` beside a running `wf run` (spec 0020); `--same-repo` checks three features of one `parallel: 2` repo build in their own worktrees (spec 0027)
python3 scripts/private-names.py --test         # private names checker self checks (spec 0013); `check` scans the repo, exits 0 when clean
python3 scripts/spec-paths.py --test            # stale spec warner self checks (spec 0015); install.sh links it as ~/.local/bin/spec-paths, which /sync runs as `spec-paths --spec NNNN`
fb-ask <task> [--file PATH] < input             # cheap worker tier (spec 0023): summarize|triage|extract|classify|commit-msg on the free claude-fb models, exit 3/4 = do it yourself (`rules/cheap-worker.md`); `fb-ask --test` self checks, install.sh links it to ~/.local/bin
wf run [repo] [--jobs N]                        # the queued `· auto` features of one repo, or of every trusted repo with no name (spec 0011); with no name it starts one `wf run <repo> -y` child per repo with work, side by side, `--jobs` caps them (spec 0017); locks, run records and queue.json in $XDG_STATE_HOME/wf, else ~/.local/state/wf
wf [-y] [--jobs N]                              # the one command you type (spec 0020): one confirm screen, then report, staged setup swap into ~/.claude, retakes, builds of every trusted repo and real checks beside them; a running run is skipped, never stopped; the subcommands below are its internals
wf queue [repo]                                 # read only plan: queued, parked, open and answered questions (spec 0011)
wf unpark <repo> [feature]                      # clear parks and open questions so the next wf run starts them fresh (spec 0011)
wf allow <repo>                                 # trust list (spec 0008); wf run refuses `untrusted` (exit 5) for a repo not in $XDG_CONFIG_HOME/wf/allowed.json, else ~/.config/wf/allowed.json
wf allow-writes <repo> <path>                   # standing write permission for that repo's wf run calls (spec 0021 AC-7), kept in ~/.config/wf/allow.json; a never writable set (secrets, live ~/.claude settings, hooks, rules, PATH dirs, git config) always wins; refused under WF_RUN; an AGENTS.md `- allow writes:` line is ignored now
wf finish [target] [-y]                         # run the ` · live` waits-on-you boxes (cp into ~/.claude, ./install.sh, e2e, probes) after one Enter, keep autoMode, tick them, record verify.md, commit (spec 0019); never from an unattended call, but a `wf run` that reaches a live copy box into `rules/`, `agents/`, `commands/` or `skills/` asks on the phone and runs exactly the approved copies itself, pinned by source hash (spec 0041)
wf report [--seen|--hook]                       # the last wf run's morning report, also sent to the phone at the end of every run (spec 0018); `--hook` is the settings.json SessionStart form, prints only an unseen report; `--seen` stops showing it; report.txt lives in the wf state folder
wf ntfy init|codes|test                         # phone pings for wf run decisions (spec 0005); config ~/.config/wf/ntfy.json (0600), wf run refuses without it
wf telegram init|test                           # your Telegram bot instead of ntfy (spec 0029): init asks for the BotFather token (hidden), binds your chat with a /start code, writes ~/.config/wf/telegram.json (0600); test sends one question
wf telegram fetch|timer on|off                  # keep Telegram answers while wf is off (spec 0039): fetch saves new updates once into the update log a run reads (same lock as a run), timer on writes and enables the wf-telegram-fetch user timer (every 5 minutes), off removes it
wf questions                                    # read only: every open question, its options (first recommended) and links (spec 0039); bare `wf` lists them first and lets you answer each at the keyboard, Enter skips, `-y` only lists
wf auto on|off|status|start|wait|hook|bar          # autonomous mode (spec 0030): `/auto on` (user only, `wf auto on` refuses under WF_RUN) makes that folder's sessions start `wf -y` as the `wf-auto` user unit and relay its questions; `off` lets the running build finish its current features, `off now` stops the unit; `hook` is the SessionStart and UserPromptSubmit hook, `bar` wraps jjstack's status line; state in <state>/auto.json
```

## Specs

`docs/specs/NNNN-title.md` (folder form `NNNN-title/index.md` for split specs): 0001 runner stack, 0002 `next`, 0003 scope contract, 0004 `wf run`, 0005 decision parking and phone pings, 0006 standing answers, 0007 push guard, 0008 failure and park policy, 0009 headless verify and test, 0010 design enforcement, 0011 build and decision queue, 0012 waiting boxes owed to you, 0013 work names out of the public repo, 0014 runner resilience, 0015 checks that cannot lie, 0016 guard hook false alarms, 0017 several repos at once, 0018 morning report, 0019 live setup steps, 0020 one command wf, 0021 never stop (every park reason asks a question instead). Every spec top file carries a `**Paths:**` line right after `**Status**:` (`rules/check-gates.md` gate 3).

## Rules

- Two kinds of file. `skills/` and `commands/` are symlinked into `~/.claude`, so editing here is live. `CLAUDE.md`, `settings*.json`, `agents/`, `rules/`, `hooks/block-destructive.sh`, `hooks/review-stack-pre-push`, `hooks/plain-panel.py`, `scripts/chroma-reaper.sh` are copies: edit the live file in `~/.claude`, then `./sync.sh`. An edit made here is overwritten on the next sync.
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
- Private names live in `~/.claude/private/` (`names.txt`, `work.md`, `gitignore`, settings fragments), never in the repo (spec 0013). Without `names.txt`, `sync.sh` and every commit here fail closed. `sync.sh` moves name bearing settings entries into the fragments and `install.sh` merges them back. The `pre-commit` and `commit-msg` hooks are copies of `scripts/private-names.py`, not links: after editing the checker, rerun `./install.sh` to refresh them. Hit lines print the `names.txt` line number, never the name.
- Runner fixtures are flat files (`runner/tests/fixtures/*.md`) that tests copy into `docs/scope/` or `.workflow/scope/` trees in temp dirs: `.workflow/` is globally gitignored, so a fixture tree there would never be committed. Keep them trimmed and free of client names (public repo).
- Scripts hardcode `~/.claude/skills/...` paths: they run through the symlink, not from the repo path.
- `claude -p` (2.1.296) never offers AskUserQuestion, so `wf run` steps ask through `DECISION NEEDED:` plus `OPTION:` lines (spec 0005); rerun its verify.md check 1 probe after a Claude Code upgrade. The Android ntfy app cannot type into a topic; typed replies go through the topic page in a phone browser.
- A repo whose scope header says `**Source of truth:** issues` or `mixed` has its linked issue reread by the `wf` runner process itself before every call (spec 0024): only `gh issue view` and one read only `gh api graphql` query, with the runner's own env, since `call_env` drops `GH_TOKEN` and calls keep their GitHub deny. A `scope` repo never runs `gh`. Baselines live in the wf state folder under `issues/`.
- A repo's `## Standing answers` takes `run suite`, `done` (spec 0006), and `app start` plus `app url` together (spec 0009): with both, `/check verify` and debug calls run the app in a `bwrap` jail and drive it through a pinned headless chrome-devtools MCP (`MCP_PACKAGE`); `app url` must be `http(s)://localhost|127.0.0.1|[::1]:<port>`. Bumping `MCP_PACKAGE` reruns spec 0009 probes P2 to P7 and updates `BROWSER_TOOLS`. `parallel: <n>` (1 to 4, needs `branches: per spec`) builds up to n features of the repo at once, each in its own worktree under `~/.local/share/wf-trees/<repo>-<hash>/` on its spec branch; the repo's own checkout is never switched (spec 0027).
- Spec 0010 rests on `design-gate` (a `context: fork` skill) running inside `claude -p` and writing `.design/audit-report.md`; rerun its verify.md P1 and P2 after a Claude Code upgrade. Under `wf run` the prompt line stops a call from even trying `Skill(design)`, so the deny itself is only provable with a direct `claude -p` carrying `run.py`'s deny lists (P3).
- Branches and PRs (spec 0026, `rules/branch-pr.md`): with `- branches: per spec` each spec builds on `feat/<NNNN>-<slug>`, squashed to one commit before its first push; with `- push: draft PR` too, the `wf` runner process (never a call) pushes it and opens a draft PR after the private names and attribution scans (`runner/pr.py`). A refusing pre-push hook keeps the branch local, never `--no-verify`. It never marks ready, and merges only on your "merge now" (spec 0031).
- Open PRs you opened by hand (spec 0031): `~/.claude/private/pr.json` keyed by `owner/name` or `owner/*`, never in a repo. `adopt: true` makes `wf` adopt and watch them, `merge: true` allows the "merge now" tap; `wf` merges itself, never a model.
- Phone channel (spec 0029): make the bot with BotFather, then `wf telegram init`. With `telegram.json` present `wf run` uses only Telegram and an invalid file refuses `no_telegram` (never falls back); without it, ntfy as before. Only your chat id can answer; a plain message gets a one line hint.
- Every `wf run` call is guarded outside the model (spec 0007): stripped credentials, Claude Code's Bash sandbox, hashed hook and git config files. `wf run` refuses `no_sandbox` without `bwrap` and `socat` on PATH. After a Claude Code upgrade rerun `python3 docs/specs/0007-push-guard/probes/run-wf-probe.py` (about 2 minutes, run it yourself with `!`) and record it in that spec's `verify.md`. The model ignores the probe's step order sometimes; a classifier lockout then hides the sandbox result for later steps. The `DENIED` push rules have their own probe, `bash docs/specs/0004-headless-step-loop/probes/push-rule.sh` (default mode with git allowed, so only deny rules can deny; run it yourself with `!`); rerun it after a Claude Code upgrade and record it in that spec's `verify.md`.

## Standing answers

- run suite: yes
- done: yes
- branches: per spec
- push: draft PR
- parallel: 4
- suite: python3 runner/tests/fast.py

## Agent skills

Declined: Agent Skill and MCP discovery for this stack (2026-10-11)

## Context files

- [skills/design/AGENTS.md](skills/design/AGENTS.md): design and brand pipeline scripts, the run ledger, and its Stop hook

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
