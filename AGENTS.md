# claude-config

For an AI agent working in this repo. Only the rules you would not guess from the code; what the repo
is and where things live is in [README.md](README.md), the runner's design in
[docs/architecture.md](docs/architecture.md), the `wf` commands a person types in
[docs/guides/DAILY-USE.md](docs/guides/DAILY-USE.md).

## Commands

```bash
bin/install.sh --dry-run                          # repo -> ~/.claude (copies + symlinks), then self-checks
bin/sync.sh                                       # ~/.claude -> repo; run before every commit, then git diff
python3 bin/claude-config.py drift|update --plan|update --apply <entry>  # spec 0048, behind the /claude-config skill: drift exits 1 when the repo and ~/.claude differ; update never asks, the skill asks per entry; tests in runner/tests/test_claude_config.py
python3 bin/claude-config.py docs               # regenerate docs/guides/SKILLS.md after touching config/manifest.json, config/routing.md or any claude-home skill or command front matter; test_layout fails on a stale copy
python3 scripts/check-routing.py                # after editing config/routing.md or a skill's triggers
python3 scripts/gen-agent-index.py --check      # after touching claude-home/agents/ (drop --check to regenerate)
python3 scripts/asciify.py --check              # ASCII-only lint on repo-owned markdown
bash claude-home/hooks/block-destructive.sh --test     # guard hook self-checks
python3 claude-home/hooks/plain-panel.py --test        # panel hook self checks (spec 0028): "Learn this first" last, at most 3 real options, no jargon
bash claude-home/hooks/handover-start.sh --test        # handover on /clear hook self checks (spec 0057); needs the real jjstack slot script
claude plugin test claude-home/mods/wf-handoff         # /handoff and auto handoff mod tests (spec 0057 AC-10, spec 0063, spec 0064 display and viewer); `claude plugin validate` beside it
claude plugin test claude-home/mods/wf-dash            # wf-dash band, alerts and panes tests (specs 0058 to 0060, 0064, 0065); `claude plugin validate` beside it; the band reads `wf status --json`
node claude-home/hooks/context-monitor.js --test       # context warning hook self checks (spec 0037): fixture transcripts, and header numbers match the code and autoCompactWindow
bash claude-home/skills/design/scripts/test-ledger.sh  # design ledger + Stop hook assertions
node claude-home/skills/design/scripts/build-ramp.mjs --check
python3 -m unittest discover -s runner/tests    # wf runner self checks, run by hand (the runner is retired live, bin/install.sh no longer runs them)
python3 runner/e2e/run.py                       # real claude end to end on a temp fixture repo (spec 0014); run it yourself with `!` after a Claude Code upgrade or runner change, prints PASS or FAIL: <check>; `--parallel` checks two real repos build side by side (spec 0017); `--beside` checks a bare `wf -y` beside a running `wf run` (spec 0020); `--same-repo` checks three features of one `parallel: 2` repo build in their own worktrees (spec 0027); `python3 runner/e2e/stress_git.py` checks 8 worktrees commit at once with a clean fsck (spec 0052)
python3 scripts/private-names.py --test         # private names checker self checks (spec 0013); `check` scans the repo, exits 0 when clean
python3 scripts/skill-keep.py --dry-run         # only skills in scripts/skill-keep.txt keep their description; others go name-only in ~/.claude/settings.json, plus a plugin report (spec 0050); without --dry-run it writes, then run bin/sync.sh right away or bin/install.sh undoes it; tests in runner/tests/test_skill_keep.py
python3 scripts/spec-paths.py --test            # stale spec warner self checks (spec 0015); bin/install.sh links it as ~/.local/bin/spec-paths, which /sync runs as `spec-paths --spec NNNN`
wf insights                                     # spec 0061: baselines and repeating problems from past runs; also runs at the end of each wf run, proposals go to an inbox, never applied; tests in runner/tests/test_insights.py
skill-scan [static|llm|both] [path ...] [--accept]  # skillspector over every skill and plugin, only new HIGH/CRITICAL vs the baseline (spec 0054); a run with no path skips the trusted packs gstack, jjstack, ui-ux-pro-max and prints `skipped (trusted):`, an explicit path or `--against` still scans them (AC-13); reports and baseline in ~/.claude/state/skillspector/ (sandbox cannot write it, run with `!`); `update --apply` runs `--against`; tests in runner/tests/test_skill_scan.py
bin/repo-settings.sh [--check] <owner/repo>       # spec 0051 AC-10: squash only, delete branch on merge, main only through a PR; --check only reads, exits 1 on a difference; you run it, never wf
bin/docs-pr.sh [slug]                           # spec 0051 AC-11: docs only commits on main reach origin by a small squash merged PR (a direct push is refused); refuses a commit outside docs/
fb-ask <task> [--local] [--file PATH] < input   # cheap worker tier (spec 0023; --local = laptop model fb-local, client text allowed, spec 0053): summarize|triage|extract|classify|commit-msg on the free claude-fb models, exit 3/4 = do it yourself (`claude-home/rules/cheap-worker.md`); `fb-ask --test` self checks, bin/install.sh links it to ~/.local/bin
```

## Rules

- Everything installed into `~/.claude` sits under `claude-home/`, at the same relative path (`claude-home/rules/x.md` is `~/.claude/rules/x.md`); guides are in `docs/guides/` (spec 0035). One source of truth per kind:
  - Copied (`claude-home/CLAUDE.md`, `claude-home/settings*.json`, `claude-home/agents/`, `claude-home/rules/`, the hand written hooks and scripts listed in `COPIED_FILES` in `bin/claude-config.py`): live wins. Edit the file in `~/.claude`, then `bin/sync.sh`; an edit made here is overwritten on the next sync.
  - Linked (`claude-home/skills/`, `claude-home/commands/`): repo wins. They are symlinked into `~/.claude`, so editing here is live.
  - Mods (`claude-home/mods/<name>/`): repo wins, and the one exception to the same path rule: each is linked as `~/.claude/skills/<name>` by hand after a `skillspector scan` (spec 0057), never by `bin/install.sh`.
  - Runner (`runner/`): repo wins; retired live 2026-10-22, so `bin/install.sh` no longer copies it to `~/.local/share/wf/<fp>/` (spec 0020).
  - Downloaded skills (spec 0048): named in `config/manifest.json` with source, pin, license and install command, never copied; an edited one is its pin plus `config/patches/<name>.patch` (a `publish: false` or private one keeps its patch in `~/.claude/private/patches/`). Never copy a downloaded skill's files into the repo.
  - Frameworks (gstack, jjstack, ECC commands, the JSM skills, plugins): their installer wins, never vendored; the manifest's `frameworks` names each.
  - Private (`~/.claude/private/`): live only, never in any repo.
  - Claude Code state (`projects/`, `sessions/`, `history.jsonl`, caches): Claude Code only, never synced.
- Rules for this repo only go in this file. The home chat opens in `~/claude-config` and its private runner rules are in `CLAUDE.local.md` (git ignored, spec 0067).
- `runner/` is `wf`, the workflow runner (spec 0001). It is retired live (2026-10-22): `bin/install.sh` no longer links `wf` or `next` into `~/.local/bin`; the code stays here. Python 3 stdlib only, tests are `unittest`, external commands go through `subprocess` with argument lists, never a shell string. `bin/claude-config.py` follows the same rules.
- This repo is public. No client or employer names, repo names, domains, or env-file names. `bin/sync.sh` strips `autoMode` from settings.json; client skills are gitignored.
- Do not edit vendored trees: `claude-home/agents/` (27 of 31 from ECC), `claude-home/rules/ecc/` (except the 7 `index.md` and the local additions in `common/code-review.md`, `common/testing.md`), `claude-home/skills/anti-ai-writing/`. Provenance lives in `docs/NOTICE.md`; update it when adding an authored or redistributed path. Its `manifest:start` block is written by `bin/claude-config.py build`.
- `docs/guides/SKILLS.md` is generated: edit `config/manifest.json`, `config/routing.md` or the front matter, then `python3 bin/claude-config.py docs`.
- Every spec top file carries a `**Paths:**` line right after `**Status**:` (`claude-home/rules/check-gates.md` gate 3).
- A figure the user gives replaces the old one in the skill's files; a figure with no source is a bracket placeholder (spec 0056, `claude-home/rules/new-number-replaces-old.md`; pinned by `runner/tests/test_borrowed_ideas.py`).
- ASCII only in repo-owned markdown: no em dashes, smart quotes, Unicode bullets.
- Conventional Commits (`feat(scope):`, `fix(scope):`, `chore:`, `docs:`); a gsd hook enforces the format.
- Comments explain why, usually naming the past failure ("this used to..."). Keep that style when fixing a script.
- Self-checks are the tests. A change to a script ships with its assertion in the matching `--test` / `--check` / `test-*.sh`.
- A test or probe that needs a banned attribution phrase as input builds it from two joined string halves (`"Co-Authored-" + "By: ..."`), so no file holds the whole phrase; the push scan (`pr.attribution_hits`) is never relaxed for tests (spec 0045).

## Gotchas

- Root `CLAUDE.md` only imports this file. The payload copy of `~/.claude/CLAUDE.md` is `claude-home/CLAUDE.md`, which `bin/sync.sh` overwrites and `bin/install.sh` ships (spec 0035 AC-4: it used to sit at the root and load twice).
- `asciify.py` skips `claude-home/agents/`, `claude-home/rules/`, `anti-ai-writing` and `node_modules/`. Without `--check` it rewrites files; always run `--check` first.
- The middle dot `·` is allowed in repo markdown despite the ASCII rule: it is the scope tag separator (`claude-home/rules/scope-contract.md`) that `runner/wf.py` parses, and `asciify.py` keeps it.
- `jjstack/` is gitignored /review scratch; reports never enter the repo from there.
- The clone lives at `~/dotfiles/claude-config` as a submodule of dotfiles; `~/claude-config` is a link to it (spec 0035 migrate step 9). Session memory and `wf` trees are keyed by the real path, and links that leave the repo climb four levels to reach `~` (`../../../../projects/...` from `docs/scope/`).
- `live` at the top is a temporary link to `claude-home` (spec 0048 AC-15) so old `~/.claude` links keep resolving until `bin/install.sh` relinks them; it is removed in its own live step.
- Private names live in `~/.claude/private/` (`names.txt`, `work.md`, `gitignore`, settings fragments), never in the repo (spec 0013). Without `names.txt`, `bin/sync.sh` and every commit here fail closed. `bin/sync.sh` moves name bearing settings entries into the fragments and `bin/install.sh` merges them back. The `pre-commit` and `commit-msg` hooks are copies of `scripts/private-names.py`, not links: after editing the checker, rerun `bin/install.sh` to refresh them. Hit lines print the `names.txt` line number, never the name.
- Runner fixtures are flat files (`runner/tests/fixtures/*.md`) that tests copy into `docs/scope/` or `.workflow/scope/` trees in temp dirs: `.workflow/` is globally gitignored, so a fixture tree there would never be committed. Keep them trimmed and free of client names (public repo).
- Scripts hardcode `~/.claude/skills/...` paths: they run through the symlink, not from the repo path.
- `bin/claude-config.py build` and `update` fetch from GitHub; a sandboxed session is denied github.com, so run them yourself with `!`. Clones are cached in `~/.cache/claude-config/`.
- `claude -p` (2.1.296) never offers AskUserQuestion, so `wf run` steps ask through `DECISION NEEDED:` plus `OPTION:` lines (spec 0005); rerun its verify.md check 1 probe after a Claude Code upgrade. The Android ntfy app cannot type into a topic; typed replies go through the topic page in a phone browser.
- A repo whose scope header says `**Source of truth:** issues` or `mixed` has its linked issue reread by the `wf` runner process itself before every call (spec 0024): only `gh issue view` and one read only `gh api graphql` query, with the runner's own env, since `call_env` drops `GH_TOKEN` and calls keep their GitHub deny. A `scope` repo never runs `gh`. Baselines live in the wf state folder under `issues/`.
- A repo's `## Standing answers` takes `run suite`, `done` (spec 0006), and `app start` plus `app url` together (spec 0009): with both, `/check verify` and debug calls run the app in a `bwrap` jail and drive it through a pinned headless chrome-devtools MCP (`MCP_PACKAGE`); `app url` must be `http(s)://localhost|127.0.0.1|[::1]:<port>`. Bumping `MCP_PACKAGE` reruns spec 0009 probes P2 to P7 and updates `BROWSER_TOOLS`. `parallel: <n>` (1 to 8, needs `branches: per spec`) builds up to n features of the repo at once, each in its own worktree under `~/.local/share/wf-trees/<repo>-<hash>/` on its spec branch; the repo's own checkout is never switched (spec 0027). A new feature starts only above 4.5 GB free memory and under 80% 5 hour use, never beside one whose spec Paths overlap, and its suite gets `WF_CORES`, its share of the cores (spec 0052).
- Spec 0010 rests on `design-gate` (a `context: fork` skill) running inside `claude -p` and writing `.design/audit-report.md`; rerun its verify.md P1 and P2 after a Claude Code upgrade. Under `wf run` the prompt line stops a call from even trying `Skill(design)`, so the deny itself is only provable with a direct `claude -p` carrying `run.py`'s deny lists (P3).
- Branches and PRs (spec 0026, `claude-home/rules/branch-pr.md`): with `- branches: per spec` each spec builds on `feat/<NNNN>-<slug>`, squashed to one commit before its first push; with `- push: draft PR` too, the `wf` runner process (never a call) pushes it and opens a draft PR after the private names and attribution scans (`runner/pr.py`). A refusing pre-push hook keeps the branch local, never `--no-verify`. It never marks ready, and merges only on your "merge now" (spec 0031), or itself, squash and one at a time, when the PR is small, low risk and green judged from main and the repo's pr.json entry has `"auto_merge": true` (spec 0051 AC-5); a PR with no checks at all waits 10 minutes for a first one (AC-4).
- Open PRs you opened by hand (spec 0031): `~/.claude/private/pr.json` keyed by `owner/name` or `owner/*`, never in a repo. `adopt: true` makes `wf` adopt and watch them, `merge: true` allows the "merge now" tap; `wf` merges itself, never a model.
- Review requests (spec 0032) turn on only through `"review_requests": true` on that repo's entry in `~/.claude/private/pr.json`, never from a repo file. The draft call reads only `pr.diff` and `files.txt` in a fresh `<run folder>/review-<n>/`, never a checkout, and the one review post (`reviews.post`) runs only on the exact `post as my review` answer.
- Phone channel (spec 0029): make the bot with BotFather, then `wf telegram init`. With `telegram.json` present `wf run` uses only Telegram and an invalid file refuses `no_telegram` (never falls back); without it, ntfy as before. Only your chat id can answer; a plain message gets a one line hint.
- Every `wf run` call is guarded outside the model (spec 0007): stripped credentials, Claude Code's Bash sandbox, hashed hook and git config files. `wf run` refuses `no_sandbox` without `bwrap` and `socat` on PATH. After a Claude Code upgrade rerun `python3 docs/specs/0007-push-guard/probes/run-wf-probe.py` (about 2 minutes, run it yourself with `!`) and record it in that spec's `verify.md`. The model ignores the probe's step order sometimes; a classifier lockout then hides the sandbox result for later steps. The `DENIED` push rules have their own probe, `bash docs/specs/0004-headless-step-loop/probes/push-rule.sh` (default mode with git allowed, so only deny rules can deny; run it yourself with `!`); rerun it after a Claude Code upgrade and record it in that spec's `verify.md`.

## Standing answers

- run suite: yes
- done: yes
- branches: per spec
- push: draft PR
- parallel: 6
- suite: python3 runner/tests/fast.py

An `- allow writes:` line here is ignored now (spec 0021 AC-7); standing write permission is `wf allow-writes <repo> <path>`.

## Agent skills

Declined: Agent Skill and MCP discovery for this stack (2026-10-11)

## Context files

- [claude-home/skills/design/AGENTS.md](claude-home/skills/design/AGENTS.md): design and brand pipeline scripts, the run ledger, and its Stop hook
