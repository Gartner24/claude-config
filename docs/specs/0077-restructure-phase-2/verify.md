# 0077 probes

## P1 a hook can add text when a skill starts (2026-10-22) - PASS
Scratch project with `.claude/settings.json` hooks and a project skill `probe-skill`; `claude -p --setting-sources project --strict-mcp-config --model claude-haiku-5-5`.
- Claude starts the skill (Skill tool): PreToolUse and PostToolUse with matcher `Skill` both fire, stdin carries `"tool_name":"Skill","tool_input":{"skill":"probe-skill"}`, and both `additionalContext` lines reached the model ("PreToolUse:Skill hook additional context: RULE-PROBE-PreToolUse ...").
- The owner types `/probe-skill`: no Skill tool hook fires. UserPromptSubmit fires with `"prompt":"/probe-skill"`. So the design needs both hooks (AC-4).

## P3 a mod-sent command reaches UserPromptSubmit - owed, build step 1
Cross check gap (spec 0070 verify probe (e) left it open). In a chat in a repo with the wf-handoff mod, log UserPromptSubmit stdin and open a chat: does the mod's chat-start `/scope` appear as a prompt? A FAIL changes only how the scope rules reach that start (Build plan step 1).

## P2 Claude edits ~/.claude without the repo map (2026-10-22) - YES
`rg -l` over `~/.claude/projects/*/*.jsonl` for `"file_path":"/home/santiago/.claude/(CLAUDE.md|rules/|hooks/|skills/*/SKILL.md|settings.json)`: 37 transcripts, from this repo and from work, freelance and university folders (reads and writes counted together). So AC-6 adds the pointer file.
