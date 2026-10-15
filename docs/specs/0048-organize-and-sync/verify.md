# 0048. Probes

## P1 three way merge (2026-10-15, git 2.56.0): pass
Files: base `a b c d e`, mine changes line 2, theirs_clean changes line 5, theirs_conflict changes line 2.
- `git merge-file -p mine base theirs_clean` exit 0, output keeps both edits (`B-mine`, `E-up`).
- `git merge-file -p mine base theirs_conflict` exit 1, output has `<<<<<<< mine` / `=======` / `>>>>>>>` markers around line 2.

## P2 fetch by commit (2026-10-15): pass
- `git ls-remote https://github.com/greensock/gsap-skills.git HEAD` gave `aed9cfd3277740755f6bfc1155c7aa645403b760`.
- `git fetch -q --depth 1 <url> aed9cfd...` into an empty repo exit 0.
- `git show FETCH_HEAD:skills/gsap-core/SKILL.md | sha256sum` = `3887b47e...12b3`, equal to `sha256sum ~/.claude/skills/gsap-core/SKILL.md`.

## Build rerun (2026-10-15, /develop under wf run)
- P1: rerun, pass. `git merge-file -p mine base theirs_clean` exit 0 with `B-mine` and `E-up`; `theirs_conflict` exit 1 with `<<<<<<< mine`, `||||||| base`, `=======`, `>>>>>>> theirs_conflict` around line 2 (git 2.56.0).
- P2 (2026-10-15, docs slice session): still not rerun inside a call, the sandbox still denies github.com. The manifest commit `1bb9e93` was built with network outside the sandbox (its clones sit in `~/.cache/claude-config/`), which fetched every traced source; a by commit `git fetch --depth 1` is first exercised live by `update --apply` (migrate.md).
- P2: not run. The build session's sandbox denies github.com (`deny network-outbound github.com:22 (host is on the deny list)` on `git ls-remote https://github.com/greensock/gsap-skills.git HEAD`). Rerun it in a session with network before the manifest pin walk (build plan slice 3) and `update` (slice 4).

## /check verify (2026-10-15, under wf run): FAIL

Ran in the feature worktree with scratch trees under `/tmp/claude/v0048/` (scratch live dirs, a local upstream git repo, `git archive` exports). GitHub is denied in this sandbox.

### Commands
- [x] `git ls-tree --name-only HEAD` -> only `.gitignore AGENTS.md CLAUDE.md LICENSE README.md bin claude-home config docs live runner scripts` (`live` is the AC-15 link) -> AC-1. can fail: `install.sh` or `NOTICE.md` left at the top.
- [x] `readlink live` -> `claude-home`; `claude-home/skills/` holds 17 own skills, none with a manifest entry -> AC-2. can fail: a downloaded skill copied in.
- [x] `git grep` for `live/`, `./install.sh`, `./sync.sh`, top level `mcp-config.json`/`test-preferences.json` outside specs, reviews, briefs -> 2 hits, both on purpose: `bin/install.sh:72` relinks old `*/live/*` links (AC-15), `runner/tests/test_finish.py:402` is a refused shape -> AC-3. can fail: a runner file still naming `./install.sh`.
- [x] `finish.shape()` on the real worktree: accepts `bin/install.sh`, `cp claude-home/rules/lessons.md ~/.claude/rules/lessons.md`, `python3 runner/e2e/run.py`; refuses `./install.sh`, `cp live/rules/...` (even through the live link), `cp claude-home/settings.json ...`; `rules/scope-contract.md` names `bin/install.sh` and the `claude-home/` drop -> AC-4. can fail: the parser still accepting `./install.sh`.
- [ ] Manifest audit over all 175 entries: fields, status rules, patch iff edited, framework keys pass, but no `kind: plugin` entry exists for the 12 installed plugins (`~/.claude/plugins/installed_plugins.json`), and `bin/claude-config.py` has no plugin code -> AC-5 specced but missing.
- [ ] 7 entries have a broken `description` (`21st-ai`, `21st-cli-use`, `21st-design-sync`, `21st-registry`, `design-dna`: `>-.`; `skill-router`: `>.`; `humanizer`: `|.`), shown in `docs/guides/SKILLS.md` lines 71-74, 146, 390. The current `description()` returns the right sentence for each (fixed in d995074); `config/manifest.json` was built earlier (1bb9e93) and never refreshed -> AC-5 bug.
- [x] 23 cite only or unknown license entries = the 23 names under "Not redistributed" in `docs/NOTICE.md`; no public patch, so the public patch section is empty; packshot, project-finder and the 3 taste skills have copies in `~/.claude/private/skills/`, their patches in `~/.claude/private/patches/` -> AC-6, AC-7. can fail: a figma skill missing from the list.
- [x] `drift` on a scratch live dir with an unknown `zz-nobody` skill -> `zz-nobody: live only: not in the repo, the manifest, a framework or the private store`, exit 1; on the real `~/.claude` no skill is unaccounted (only the 22 links install would move, the new hook, the new skill, and settings) -> AC-6 accounting, AC-9. can fail: an unknown skill passing silently.
- [x] `scripts/private-names.py check` on a `git archive HEAD` export -> exit 0 -> AC-8. can fail: a private name in the manifest or a doc.
- [x] Local upstream scenario (`/tmp/claude/v0048/update.sh`): `patches` writes `config/patches/s1.patch` and marks `edited`; upstream line 5 change: `update --plan` lists it with `+1 -1 SKILL.md` and writes `last_upstream_check`; `--apply` exit 0 keeps both edits (`a B-mine c d E-up`), pin moves; upstream line 2 change: exit 2, conflicts folder with markers, live and manifest byte equal; `--resolved` with markers exit 2, after the fix exit 0 and the conflicts folder is gone; `restore` after removing the skill rebuilds an equal hash; unreachable source exit 1, nothing changes -> AC-7, AC-10. can fail: a conflict that installs anyway.
- [x] Reminder hook with `CLAUDE_CONFIG_DIR` scratch: missing state prints the never checked line, 8 days prints `upstream not checked for 8 days`, 6 days prints nothing; registered in `claude-home/settings.json` -> AC-11. can fail: the 7 day threshold off by one.
- [x] `wc -l AGENTS.md` -> 92; README and AGENTS open with their reader; docs-map has 1150 rows, none nowhere, 15 dropped with reasons, spot checks land (wf run table in `docs/architecture.md`, plugins in `docs/guides/SETUP.md`). Note: rows R1 to R8 name a README heading `What this is` that does not exist; the facts sit in README's untitled opening paragraph -> AC-12.
- [x] `docs/guides/` holds exactly the 5 guides, each with a `Type:` second line; `SKILLS-EVALUATION.md` in `docs/research/`; `bin/claude-config.py docs` then `git diff --exit-code docs/guides/SKILLS.md` -> no diff -> AC-13. can fail: a stale generated file.
- [x] `migrate.md`: preconditions, standard check of the 5 AC-14 checks, the skill names check by name, step 0 backups, each step one move with check and undo -> AC-14 (text). Note: steps 3 (manifest build with network) and 4 (drift none, retire `skills-audit.sh`) have no box in the plan.
- [x] AC-16: `bin/install.sh --dry-run` exit 0 (would relink exactly the 22 drift items); `bin/sync.sh` round trip on an exported repo and a scratch live dir exit 0, `claude-home/` unchanged; `check-routing`, `gen-agent-index --check`, `asciify --check`, `block-destructive --test`, `plain-panel --test`, `context-monitor --test`, `test-ledger.sh` (107 pass), `build-ramp --check`, `private-names --test`, `spec-paths --test`, `fb-ask --test` all exit 0.
- [ ] `python3 runner/tests/fast.py` -> 903 tests, 1 failed: `test_never_stop.TestRepoAndRun.test_run_limit_keep_going` (exit 6, second keep going question arrives after feature B's `/sync`). It fails the same way on a `main` export, so it predates this branch.

## /check verify rerun (2026-10-15, under wf run, after 483eea4 and 59f521a): FAIL

Scratch in `/tmp/claude/v0048b/`; the committed branch tested from a `git archive HEAD` export made into a throwaway git repo.

### Commands
- [x] Manifest audit (`/tmp/claude/v0048b/audit.py`): 187 entries, 175 `skill` and 12 `plugin`; the 12 plugin keys equal the 12 keys of `~/.claude/plugins/installed_plugins.json`; every entry has all AC-5 fields, allowed `kind` and `status`, patch iff `edited`; plugins are `fetch: manual`, `publish: false`, `install: claude plugin install <key>` -> AC-5 (was missing). can fail: an installed plugin with no entry.
- [x] The 7 broken descriptions are gone: `21st-ai`, `design-dna`, `humanizer`, `skill-router` rows in `docs/guides/SKILLS.md` show their real sentence; `clangd-lsp` shows `no description` (its plugin has no `plugin.json` description) -> AC-5, AC-13. can fail: a `>-.` row left.
- [x] `bin/claude-config.py docs` then `git diff --stat -- docs/guides/SKILLS.md` -> empty -> AC-13. can fail: a stale generated file.
- [ ] Plugin `base_hash`: a fresh `plugin_entries()` differs from `config/manifest.json` for 10 of 12 plugins, on `base_hash` only. Cause: Claude Code writes `.in_use/<pid>` marker files into each plugin's install folder for every running session (e.g. `cache/claude-plugins-official/code-review/8f814f49002f/.in_use/1169238`, written 15:31, after the 15:28 build), and `folder_hash` counts them (`SKIP` in `bin/claude-config.py:39` lacks `.in_use`). The 10 differing plugins are exactly the 10 whose `.in_use` changed after the build. So a plugin's `base_hash` describes the sessions running at build time, not the plugin, and every `build` rewrites it -> AC-5 bug, run `/debug`.
- [x] `python3 -B -m unittest runner.tests.test_claude_config runner.tests.test_layout` on the export -> 30 tests OK -> AC-1, AC-3, AC-5 to AC-13. In the worktree the same run fails `test_old_paths` with 14 hits, all in `docs/scope/scope.md`, whose uncommitted working copy is byte equal to `main`'s (put there by the runner, not by this branch); this shows the old path test can fail.
- [x] `drift` on the real `~/.claude` -> exit 1 with the 26 items `bin/install.sh` would fix (22 links, the new hook, the new skill, `scope-contract.md`, two settings keys); no plugin listed, no unaccounted skill -> AC-9. can fail: an unknown skill passing silently.
- [x] `private-names.py check` on the export exit 0 (AC-8); `asciify.py --check` 0 changes; `check-routing.py` routing OK; `bin/install.sh --dry-run` exit 0 -> AC-16.
- [ ] `python3 runner/tests/fast.py` -> 904 tests, 1 failed: `test_old_paths`, only from the runner's `main` copy of `docs/scope/scope.md` described above. The earlier keep going failure is fixed (17ecbaa).

## /check verify rerun (2026-10-15, under wf run, after dd9329d): FAIL

Scratch in `/tmp/claude/v0048c/`; `git archive HEAD` export committed into a throwaway git repo.

### Commands
- [x] Plugin `base_hash` (`/tmp/claude/v0048c/plugins.py`): fresh `plugin_entries()` on the real `~/.claude` against `config/manifest.json` -> 12 plugins, 0 differences, with 66 `.in_use` markers present -> AC-5 (was a bug). can fail: with `.in_use` dropped from `SKIP` in the export, the same script reports 10 of 12 `base_hash` differences and `test_in_use_marker_not_hashed` goes red; restored after.
- [x] `python3 -B runner/tests/fast.py` on the committed export -> 905 tests, 0 failed -> AC-1 to AC-13, AC-16. can fail: `test_old_paths` went red in the worktree on the runner's `main` copy of `docs/scope/scope.md` (14 hits).
- [x] `bin/claude-config.py docs` on the export -> `git status` clean -> AC-13. can fail: a stale generated file.
- [x] `drift` on the real `~/.claude` -> exit 1, the same 26 items `bin/install.sh --dry-run` lists (22 links, the new hook, the new skill, `scope-contract.md`, settings `hooks` and `skillOverrides`), no unaccounted skill -> AC-9. can fail: an unknown skill passing silently.
- [x] `private-names.py check` on the export exit 0 -> AC-8; `bin/install.sh --dry-run` exit 0 -> AC-16.
- [ ] Merge with `main`: `main` gained spec 0050 (`65662ff`, `64be625`) after this branch was cut. `git merge-tree --write-tree HEAD main` conflicts in `AGENTS.md` and `docs/scope/scope.md`, and the merged tree names the old paths outside the doc folders: `scripts/skill-keep.py:6` and `:139` (it prints "next: run ./sync.sh now, before any install.sh", a command that no longer exists after this branch), `runner/tests/test_skill_keep.py:116`, `:132`. `main`'s `AGENTS.md` also still has the old `live/` command list. So AC-3 does not hold once this lands, and `test_old_paths` would fail on `main` -> AC-3 not applied. Fix: bring `main` into the branch (rule 4: rebase, the branch is not pushed), move the 0050 lines to `bin/sync.sh` / `bin/install.sh`, keep main's `skillOverrides` in `claude-home/settings.json`, resolve the two conflicts with the branch's paths.

### Not run here
- `update --plan` against GitHub: the sandbox denies github.com; the tool reported every source unreached and wrote no state (the specced no network path).
- `python3 runner/e2e/run.py`: needs a real `claude -p`.
- AC-14 live run and AC-15: left to the boxes "Back up `~/.claude` and the repo, as `migrate.md` step 0 says (AC-14)", "Install the new layout by running `bin/install.sh` yourself (the old runner copy does not know this path yet)", "Check every skill name still opens, then remove the temporary `live` link (AC-15)".

## /check verify rerun (2026-10-15, under wf run, after the main merge b22ef6c): PASS on the branch copy (your answer)

Scratch in `/tmp/claude/v0048d/`; `git archive HEAD` export committed into a throwaway git repo.

### Commands
- [x] Merge with `main` landed with the new paths: `git grep` for `./install.sh`, `./sync.sh`, `live/` on `HEAD` outside the three doc folders -> only the 2 intended hits (`bin/install.sh:72`, `runner/tests/test_finish.py:402`); `scripts/skill-keep.py:6`, `:139` and `runner/tests/test_skill_keep.py:116`, `:132` now name `bin/sync.sh` / `bin/install.sh`; committed `docs/scope/scope.md` has 0 old path hits; `claude-home/settings.json` `skillOverrides` equals `main:live/settings.json` (251 keys), no main key lost -> AC-3 (was not applied). can fail: mutant `skill-keep.py` printing `./sync.sh` turned `test_skill_keep.test_write` and `test_layout.test_old_paths` red; restored, green.
- [x] `python3 -B runner/tests/fast.py` on the export -> 917 tests, 0 failed -> AC-1 to AC-13, AC-16. can fail: a tracked stray top level `install.sh` turned `test_layout.test_top` red (`1 top level entries outside spec 0048 AC-1: ['install.sh']`); removed, green.
- [x] `bin/claude-config.py docs` on the export -> `git status` clean -> AC-13. `docs/guides/` 5 guides, each with a `Type:` line; `AGENTS.md` 93 lines -> AC-12. can fail: a stale generated file.
- [x] `drift` on the real `~/.claude` -> exit 1, 25 items, all ones `bin/install.sh` fixes (22 links still into the old path, the new hook, the new skill, `scope-contract.md`, settings `hooks`); `skillOverrides` no longer differs after the merge; 0 unaccounted skills -> AC-9. can fail: an unknown skill passing silently (exercised in the first verify).
- [x] `private-names.py check` exit 0 (AC-8); `asciify.py --check` 0 changes; `check-routing.py` routing OK; `gen-agent-index.py --check` OK; `bin/install.sh --dry-run` exit 0 -> AC-16.
- [ ] `python3 runner/tests/fast.py` in the worktree -> 917 tests, 1 failed: `test_old_paths`, 14 hits, all in `docs/scope/scope.md`. The working copy is byte equal to `main` (the runner overlays the planning branch's scope); the committed branch copy is clean. It stays red in every `wf` worktree of this branch until `main`'s `docs/scope/scope.md` names the new paths. Your answer (2026-10-15): accept it, pass on the branch copy; the merge brings the new paths to `main`.

### Not run here
- `update --plan` against GitHub (sandbox denies github.com); `python3 runner/e2e/run.py` (needs a real `claude -p`).
- AC-14 live run and AC-15: left to the boxes "Back up `~/.claude` and the repo, as `migrate.md` step 0 says (AC-14)", "Install the new layout by running `bin/install.sh` yourself (the old runner copy does not know this path yet)", "Check every skill name still opens, then remove the temporary `live` link (AC-15)".
