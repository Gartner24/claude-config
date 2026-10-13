# 0020. One command: wf (verify)

## Probes (before accept)

### P1: what a running call sees when its config is swapped
Command: `python3 docs/specs/0020-one-command-wf/probes/p1-midcall-swap.py`. Run 2026-10-13, Claude Code 2.1.296. A temp `CLAUDE_CONFIG_DIR` (your login copied in, then removed; nothing of the live `~/.claude` touched). Its `settings.json` sets a PreToolUse Bash hook script that logs `v1`. The call runs six Bash tool calls, two of them `sleep 12`. About 15 s in, the hook script is renamed over with one logging `v2`, and `settings.json` is renamed over with one that adds a PostToolUse hook logging `post`.

Result, log in order: `v1`, `v1`, `swapped`, `post`, `v2`, `post`, `v2`, `post`, `v2`, `post`, `v2`, `post`. `RESULT hooks_per_tool_use=True settings_reread_mid_call=True`. The first `post` fired for a tool use whose PreToolUse had run under the old settings.

Rerun the same day with the call limited to `--allowedTools Bash(echo:*) Bash(sleep:*)` and the temp folder as its working folder (the first run used `bypassPermissions`, flagged by a security review): the same order and the same `RESULT` line.

Confirmed: a running call rereads `settings.json` mid call and runs hook scripts fresh on each tool use. So AC-4 renames `settings.json` last, and the spec accepts that an in flight call uses the new setup for its remaining tool uses. Rerun after a Claude Code upgrade.
