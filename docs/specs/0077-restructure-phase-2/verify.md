# 0077 probes

## P1 a hook can add text when a skill starts (2026-10-22) - PASS
Scratch project with `.claude/settings.json` hooks and a project skill `probe-skill`; `claude -p --setting-sources project --strict-mcp-config --model claude-haiku-5-5`.
- Claude starts the skill (Skill tool): PreToolUse and PostToolUse with matcher `Skill` both fire, stdin carries `"tool_name":"Skill","tool_input":{"skill":"probe-skill"}`, and both `additionalContext` lines reached the model ("PreToolUse:Skill hook additional context: RULE-PROBE-PreToolUse ...").
- The owner types `/probe-skill`: no Skill tool hook fires. UserPromptSubmit fires with `"prompt":"/probe-skill"`. So the design needs both hooks (AC-4).

## P3 a mod-sent command reaches UserPromptSubmit (2026-10-22) - PASS
Cross check gap (spec 0070 verify probe (e) left it open). In a chat in a repo with the wf-handoff mod, log UserPromptSubmit stdin and open a chat: does the mod's chat-start `/scope` appear as a prompt? A FAIL changes only how the scope rules reach that start (Build plan step 1).
- Setup: throwaway git repo `/tmp/p3probe/repo` (`git init`, an `AGENTS.md`, no origin), an extra settings file `/tmp/p3probe/settings.json` whose only hook is UserPromptSubmit `bash /tmp/p3probe/log.sh` (appends stdin to `/tmp/p3probe/ups.log`). Live settings untouched: the probe file is passed with `--settings`, and the live wf-handoff mod is the one that ran.
- Command: `tmux new-session -d -s p3probe -x 200 -y 50 -c /tmp/p3probe/repo "claude --settings /tmp/p3probe/settings.json --model haiku"`, then the folder trust prompt answered with Down, Enter. Nothing was typed into the chat.
- Result: the mod logged `chat start: /scope in /tmp/p3probe/repo` (`~/.claude/state/auto-handoff/auto-handoff.log`), and `ups.log` holds one UserPromptSubmit event with `"hook_event_name":"UserPromptSubmit","prompt":"/scope"` for the same session id. The pane shows `/scope` ran.
- So the start skill reaches `skill-rules.py` like a typed one; the FAIL path (the mod prints the scope rules itself) is not built.

## Always loaded size (build step 1)
Measured with Python `len()` over `claude-home/CLAUDE.md` plus `claude-home/rules/*.md` (not `rules/ecc/`):
- Before, at base `e361b3d`: 52,699 characters in 20 files (live `~/.claude` the same day: 52,699 in 20 files).
- After 0077a in the repo: 16,325 characters in 6 files (`tests/test_rules_on_demand.py` fails above 20,000).
- Live after install: owed, the owner runs the real install (AC-1 verify step).

## P2 Claude edits ~/.claude without the repo map (2026-10-22) - YES
`rg -l` over `~/.claude/projects/*/*.jsonl` for `"file_path":"/home/santiago/.claude/(CLAUDE.md|rules/|hooks/|skills/*/SKILL.md|settings.json)`: 37 transcripts, from this repo and from work, freelance and university folders (reads and writes counted together). So AC-6 adds the pointer file.

## PR A verify (0077a, AC-1 to AC-9), head after merging main, 2026-10-22
Throwaway install: `HOME=/tmp/v77/home CLAUDE_LIVE_DIR=/tmp/v77/home/.claude WF_STAGE=1 bash bin/install.sh` (WF_STAGE=1 skips bin links and .git hooks; live rules seeded with `branch-pr.md` and `handoff.md`; `jjstack` skill linked and `private/patches` copied only so unrelated self checks can run). The real `~/.claude` was never touched.

- [x] Live rules that moved are backed up, not deleted: output lists `live only: rules/branch-pr.md -> backups/rules/2026-10-22/rules/branch-pr.md` (and handoff.md); `rules/` then holds only lessons, new-number-replaces-old, no-attribution, plain-questions, stop-and-reset (+ ecc); `rules-on-demand/` holds 17 files + map.json. can fail: install leaves `rules/handoff.md` in place, or deletes it with no backup. -> AC-7
- [x] Always loaded text in that install: `live always loaded text: 16834 characters (limit 20000)` from the install verify (CLAUDE.md + rules/*.md, 9664 + the CLAUDE.md part). can fail: a moved rule left in `rules/` pushes it past 20000 and verify exits 1 with the total. -> AC-1
- [x] `skill-rules.py` with `{"hook_event_name":"PreToolUse","tool_input":{"skill":"architect"}}` prints additionalContext with 9 `# rules for /architect: <file>` headers (spec-gate ... handoff). can fail: a map key renamed or a file missing prints nothing. -> AC-3, AC-4
- [x] Same hook with `{"hook_event_name":"UserPromptSubmit","prompt":"/architect x"}` prints the same 9 headers; `"what is a monad"` prints nothing; `code-review:code-review` prints nothing (no fallback after the colon). can fail: a hook that matches any prompt, or falls back to the part after the colon. -> AC-4
- [x] Install verify runs `skill rules hook: all self-checks passed` and `settings.json` wires `skill-rules.py` on PreToolUse matcher `Skill` and on UserPromptSubmit; no `chain-catch.py --prompt` entry and no `def prompt` / `--prompt` code in chain-catch.py (only the removal note). can fail: reminder entry still in settings. -> AC-4, AC-5
- [x] `MAP.md` (6 lines) is copied to live `MAP.md`. can fail: missing from COPIED_FILES. -> AC-6
- [x] AC-9: restructure-check run 20261022-230208, verdict "4 needs a look", all four fixed in 76da9db (cited, not rerun). -> AC-9
- AC-8 (docs rewritten) is covered by `tests/test_map.py` and the suite; see the /test report.
- Install self checks after the size check stopped on `DESIGN LEDGER SELF-CHECK FAILED`: 3 brand-board tests need the freelance kit under the throwaway HOME (`website-build-templates`), unrelated to 0077; 105 of 108 pass. The later hook file check was therefore not reached in the throwaway; the suite covers it (`TestHookFiles`).
- Owner boxes, not run: real install and live AC-1 measure; typed `/architect x` in a fresh chat vs a plain chat. · waits on you

## PR B build (0077b, AC-10 to AC-14), branch feat/0077-tools-folder, base 039220d, 2026-10-23
The real flag names (AC-14): `snapshot --repo <tree> [--home DIR] [--link-root DIR] --out FILE` and
`verify SNAPSHOT (--map FILE | --map-from-git BASE) [--repo <tree>] [--home DIR]`. Commands run, in this order, in the
worktree `W` (`.claude/worktrees/agent-a0f07608fec590167` of the clone); the live links point into the main checkout,
hence `--link-root`:
1. On the base tree, before any move:
   `python3 W/scripts/ref-check.py snapshot --repo W --link-root /home/santiago/dotfiles/claude-config --out /tmp/b77/before.json`
   printed `snapshot: 813 pointers {'text': 442, 'spec-paths': 332, 'link': 37, 'settings': 2}, 88 already dangling (left out)`.
2. `git mv bin tools/bin`, `git mv scripts tools/scripts`, `git mv config tools/config`; then every referrer (AC-11).
3. `python3 -B W/tools/scripts/ref-check.py verify --repo W /tmp/b77/before.json --map-from-git origin/main`
   (origin/main = 039220d): 31 broken, none of them a live pointer this PR should have moved:
   - 16 in `docs/scope/done.md` and 2 in `docs/research/SKILLS-EVALUATION.md`: history, kept by AC-11.
   - 9 live only (7 `~/.local/bin` links: spec-paths, fb-ask, skill-scan, start-gates, design-check, issue-reread,
     review-isolated; 2 `~/.claude/settings.json` permission strings): the real install after merge relinks and rewrites them.
   - 4 tokens that never pointed into this repo but matched a folder that existed at base: `scripts/` in
     `docs/guides/SETUP.md` (the ECC and turnstile-spin folders) and in `claude-home/skills/design/references/_architecture-2026-09-09.md`
     (a skill's own folder), and the ref-check self check fixtures `bin/**` and `scripts/*.py` in `tools/scripts/ref-check.py`.
   Two ref-check gaps the move exposed were fixed first, each with a self check case: a home spelled token
   (`~/claude-config/tools/scripts/x.py`) and a folder token (`bin/` to `tools/bin/`) counted as broken though the referrer
   named the new path.
4. `bash W/tools/bin/install.sh --dry-run`: exit 0; bin links now point at `tools/scripts/<name>.py`.
5. Real install, `claude-config.py drift` prints `drift: none`, `hook-files` clean: owed, the owner runs the real install after merge. · waits on you
6. `python3 -B W/tests/fast.py`: 184 tests, 0 failed (3 of them the new `tests/test_tools_folder.py`).
