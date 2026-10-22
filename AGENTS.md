# claude-config

For an AI agent working in this repo. Only the rules you would not guess from the code; what the repo
is and where things live is in [README.md](README.md), the runner's design in
[docs/architecture.md](docs/architecture.md), the `wf` commands a person types in
[docs/guides/DAILY-USE.md](docs/guides/DAILY-USE.md).

## Commands

```bash
bin/install.sh --dry-run                          # repo -> ~/.claude (copies + symlinks), then self-checks
bin/sync.sh                                       # ~/.claude -> repo; run before every commit, then git diff
python3 bin/claude-config.py drift|update --plan|update --apply <entry>  # spec 0048, behind the /claude-config skill: drift exits 1 when the repo and ~/.claude differ; update never asks, the skill asks per entry; tests in tests/test_claude_config.py
python3 bin/claude-config.py docs               # regenerate docs/guides/SKILLS.md after touching config/manifest.json, config/routing.md or any claude-home skill or command front matter; test_layout fails on a stale copy
python3 scripts/check-routing.py                # after editing config/routing.md or a skill's triggers
python3 scripts/gen-agent-index.py --check      # after touching claude-home/agents/ (drop --check to regenerate)
python3 scripts/asciify.py --check              # ASCII-only lint on repo-owned markdown
bash claude-home/hooks/block-destructive.sh --test     # guard hook self-checks
python3 claude-home/hooks/plain-panel.py --test        # panel hook self checks: at most 3 options, first "(Recommended)", short labels and descriptions, no internal codes (rules/plain-questions.md)
bash claude-home/hooks/handover-start.sh --test        # handover on /clear hook self checks (spec 0057); needs the real jjstack slot script
claude plugin test claude-home/mods/wf-handoff         # /handoff and auto handoff mod tests (spec 0057 AC-10, spec 0063, spec 0064 display and viewer); `claude plugin validate` beside it
claude plugin test claude-home/mods/chip-dash            # chip-dash (was wf-dash) band and panes tests (specs 0058 to 0060, 0064, 0065); `claude plugin validate` beside it; the band reads facts.py and the wf-handoff chain file, the Plan view plan.py, never the retired runner
node claude-home/hooks/context-monitor.js --test       # context warning hook self checks (spec 0037): fixture transcripts, and header numbers match the code and autoCompactWindow
bash claude-home/skills/design/scripts/test-ledger.sh  # design ledger + Stop hook assertions
node claude-home/skills/design/scripts/build-ramp.mjs --check
python3 tests/fast.py                              # the suite: only tests for live code
cd _archive/runner && python3 -m unittest discover -s tests    # retired wf runner self checks, by hand only (frozen; some fail, see docs/specs/0072-icm-restructure/verify.md)
python3 scripts/private-names.py --test         # private names checker self checks (spec 0013); `check` scans the repo, exits 0 when clean
python3 scripts/skill-keep.py --dry-run         # only skills in scripts/skill-keep.txt keep their description; others go name-only in ~/.claude/settings.json, plus a plugin report (spec 0050); without --dry-run it writes, then run bin/sync.sh right away or bin/install.sh undoes it; tests in tests/test_skill_keep.py
python3 scripts/spec-paths.py --test            # stale spec warner self checks (spec 0015); bin/install.sh links it as ~/.local/bin/spec-paths, which /sync runs as `spec-paths --spec NNNN`
skill-scan [static|llm|both] [path ...] [--accept]  # skillspector over every skill and plugin, only new HIGH/CRITICAL vs the baseline (spec 0054); a run with no path skips the trusted packs gstack, jjstack, ui-ux-pro-max and prints `skipped (trusted):`, an explicit path or `--against` still scans them (AC-13); reports and baseline in ~/.claude/state/skillspector/ (sandbox cannot write it, run with `!`); `update --apply` runs `--against`; tests in tests/test_skill_scan.py
bin/repo-settings.sh [--check] <owner/repo>       # spec 0051 AC-10: squash only, delete branch on merge, main only through a PR; --check only reads, exits 1 on a difference
bin/docs-pr.sh [slug]                           # spec 0051 AC-11: docs only commits on main reach origin by a small squash merged PR (a direct push is refused); refuses a commit outside docs/
fb-ask <task> [--local] [--file PATH] < input   # cheap worker tier (spec 0023; --local = laptop model fb-local, client text allowed, spec 0053): summarize|triage|extract|classify|commit-msg on the free claude-fb models, exit 3/4 = do it yourself (`claude-home/rules/cheap-worker.md`); `fb-ask --test` self checks, bin/install.sh links it to ~/.local/bin
```

## Rules

- Everything installed into `~/.claude` sits under `claude-home/`, at the same relative path (`claude-home/rules/x.md` is `~/.claude/rules/x.md`); guides are in `docs/guides/` (spec 0035). One source of truth per kind:
  - Copied (`claude-home/CLAUDE.md`, `claude-home/settings*.json`, `claude-home/agents/`, `claude-home/rules/`, the hand written hooks and scripts listed in `COPIED_FILES` in `bin/claude-config.py`): live wins. Edit the file in `~/.claude`, then `bin/sync.sh`; an edit made here is overwritten on the next sync.
  - Linked (`claude-home/skills/`, `claude-home/commands/`): repo wins. They are symlinked into `~/.claude`, so editing here is live.
  - Mods (`claude-home/mods/<name>/`): repo wins, and the one exception to the same path rule: each is linked as `~/.claude/skills/<name>` by hand after a `skillspector scan` (spec 0057), never by `bin/install.sh`.
  - Runner (`_archive/runner/`): repo wins; retired live 2026-10-22, so `bin/install.sh` no longer copies it to `~/.local/share/wf/<fp>/` (spec 0020).
  - Downloaded skills (spec 0048): named in `config/manifest.json` with source, pin, license and install command, never copied; an edited one is its pin plus `config/patches/<name>.patch` (a `publish: false` or private one keeps its patch in `~/.claude/private/patches/`). Never copy a downloaded skill's files into the repo.
  - Frameworks (gstack, jjstack, ECC commands, the JSM skills, plugins): their installer wins, never vendored; the manifest's `frameworks` names each.
  - Private (`~/.claude/private/`): live only, never in any repo.
  - Claude Code state (`projects/`, `sessions/`, `history.jsonl`, caches): Claude Code only, never synced.
- Rules for this repo only go in this file. The home chat opens in `~/claude-config` and its private runner rules are in `CLAUDE.local.md` (git ignored, spec 0067).
- `_archive/runner/` is `wf`, the workflow runner (spec 0001). It is retired live (2026-10-22): `bin/install.sh` no longer links `wf` or `next` into `~/.local/bin`; the code stays here. Python 3 stdlib only, tests are `unittest`, external commands go through `subprocess` with argument lists, never a shell string. `bin/claude-config.py` follows the same rules.
- This repo is public. No client or employer names, repo names, domains, or env-file names. `bin/sync.sh` strips `autoMode` from settings.json; client skills are gitignored.
- Do not edit vendored trees: `claude-home/agents/` (27 of 31 from ECC), `claude-home/rules/ecc/` (except the 7 `index.md` and the local additions in `common/code-review.md`, `common/testing.md`), `claude-home/skills/anti-ai-writing/`. Provenance lives in `docs/NOTICE.md`; update it when adding an authored or redistributed path. Its `manifest:start` block is written by `bin/claude-config.py build`.
- `docs/guides/SKILLS.md` is generated: edit `config/manifest.json`, `config/routing.md` or the front matter, then `python3 bin/claude-config.py docs`.
- Every spec top file carries a `**Paths:**` line right after `**Status**:` (`claude-home/rules/check-gates.md` gate 3).
- A figure the user gives replaces the old one in the skill's files; a figure with no source is a bracket placeholder (spec 0056, `claude-home/rules/new-number-replaces-old.md`; pinned by `tests/test_borrowed_ideas.py`).
- ASCII only in repo-owned markdown: no em dashes, smart quotes, Unicode bullets.
- Conventional Commits (`feat(scope):`, `fix(scope):`, `chore:`, `docs:`); a gsd hook enforces the format.
- Comments explain why, usually naming the past failure ("this used to..."). Keep that style when fixing a script.
- Self-checks are the tests. A change to a script ships with its assertion in the matching `--test` / `--check` / `test-*.sh`.
- A test or probe that needs a banned attribution phrase as input builds it from two joined string halves (`"Co-Authored-" + "By: ..."`), so no file holds the whole phrase; the push scan (`pr.attribution_hits`) is never relaxed for tests (spec 0045).

## Gotchas

- Root `CLAUDE.md` only imports this file. The payload copy of `~/.claude/CLAUDE.md` is `claude-home/CLAUDE.md`, which `bin/sync.sh` overwrites and `bin/install.sh` ships (spec 0035 AC-4: it used to sit at the root and load twice).
- `asciify.py` skips `claude-home/agents/`, `claude-home/rules/`, `anti-ai-writing` and `node_modules/`. Without `--check` it rewrites files; always run `--check` first.
- The middle dot `·` is allowed in repo markdown despite the ASCII rule: it is the scope tag separator (`claude-home/rules/scope-contract.md`) that `_archive/runner/wf.py` parses, and `asciify.py` keeps it.
- `jjstack/` is gitignored /review scratch; reports never enter the repo from there.
- The clone lives at `~/dotfiles/claude-config` as a submodule of dotfiles; `~/claude-config` is a link to it (spec 0035 migrate step 9). Session memory and `wf` trees are keyed by the real path, and links that leave the repo climb four levels to reach `~` (`../../../../projects/...` from `docs/scope/`).
- `live` at the top is a temporary link to `claude-home` (spec 0048 AC-15) so old `~/.claude` links keep resolving until `bin/install.sh` relinks them; it is removed in its own live step.
- Private names live in `~/.claude/private/` (`names.txt`, `work.md`, `gitignore`, settings fragments), never in the repo (spec 0013). Without `names.txt`, `bin/sync.sh` and every commit here fail closed. `bin/sync.sh` moves name bearing settings entries into the fragments and `bin/install.sh` merges them back. The `pre-commit` and `commit-msg` hooks are copies of `scripts/private-names.py`, not links: after editing the checker, rerun `bin/install.sh` to refresh them. Hit lines print the `names.txt` line number, never the name.
- Runner fixtures are flat files (`_archive/runner/tests/fixtures/*.md`) that tests copy into `docs/scope/` or `.workflow/scope/` trees in temp dirs: `.workflow/` is globally gitignored, so a fixture tree there would never be committed. Keep them trimmed and free of client names (public repo).
- Scripts hardcode `~/.claude/skills/...` paths: they run through the symlink, not from the repo path.
- `bin/claude-config.py build` and `update` fetch from GitHub; a sandboxed session is denied github.com, so run them yourself with `!`. Clones are cached in `~/.cache/claude-config/`.

## Standing answers

- run suite: yes
- done: yes
- suite: python3 tests/fast.py


## Agent skills

Declined: Agent Skill and MCP discovery for this stack (2026-10-11)

## Context files

- [claude-home/skills/design/AGENTS.md](claude-home/skills/design/AGENTS.md): design and brand pipeline scripts, the run ledger, and its Stop hook
