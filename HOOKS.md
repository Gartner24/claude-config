# Hooks

All hooks in `settings.json` are auto-managed - they come from gstack, jjstack, or claude-mem.
You do not maintain these manually. Reinstalling those frameworks restores them.

## Where each hook comes from

| Hook file | Source | Purpose |
|-----------|--------|---------|
| `gsd-check-update.js` | gstack | Checks for gstack updates on session start |
| `gsd-session-state.sh` | gstack | Injects project state reminder at session start |
| `gsd-context-monitor.js` | gstack | Monitors context usage after Bash/Edit/Write/Agent/Task |
| `gsd-phase-boundary.sh` | gstack | Detects .planning/ file writes to track phase progress |
| `gsd-prompt-guard.js` | gstack | Guards against prompt issues on Write/Edit |
| `gsd-read-guard.js` | gstack | Enforces read-before-edit on Write/Edit |
| `gsd-workflow-guard.js` | gstack | Enforces GSD workflow rules on Write/Edit |
| `gsd-validate-commit.sh` | gstack | Enforces Conventional Commits format on Bash |
| `claude-mem-install.sh` | claude-mem | Ensures claude-mem node_modules are installed |
| `auto-approve-safe.sh` | jjstack | Smart permission gate using Claude Haiku for safe ops |
| `error-detector.sh` | jjstack | Records failed Bash commands to JSONL log |
| `injection-guard.sh` | jjstack | Scans Write/Edit content for prompt injection in .md files |
| `mcp-reconnect.sh` | jjstack | Reconnects MCP servers on tool failure |

## Key behaviors these enable

**`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: 95`** - Context is not compacted until 95% full (default is lower).
Keeps more conversation context alive before Claude summarizes. Useful for long sessions.

**`model: opusplan`** - Uses Opus model for planning operations instead of default Sonnet.

**`auto-approve-safe.sh`** - Uses Haiku to evaluate permission requests and auto-approve
safe operations. Reduces permission prompts for read-only and low-risk tool calls.

Modified from jjstack default: Haiku prompt tightened to rate HIGH only for truly
destructive/irreversible commands (rm, force-push, drop database, system package installs,
exfiltration). MEDIUM is now auto-approved alongside LOW. Only HIGH defers to the user.
This means ~90% of prompts are silently approved without interrupting the session.

**`gsd-read-guard.js`** - This is what produces the "READ-BEFORE-EDIT REMINDER" you see before
file edits. Enforces that Claude reads a file before modifying it.

**Status line** - Powered by `jjstack/bin/statusline.sh`. Shows project state in the terminal.

## Restoring on a new machine

Hooks are file paths hardcoded to `/home/santiago/`. On a new machine:
1. Install jjstack (installs gstack + creates hook symlinks)
2. Install claude-mem plugin
3. Copy `settings.json` and update the `/home/santiago/` paths to match the new username/home
4. `settings.local.json` can be copied as-is
