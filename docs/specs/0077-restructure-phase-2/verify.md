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
