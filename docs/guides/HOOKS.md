# Hooks
Type: reference

A hook is a script Claude Code runs on an event (session start, before a tool call, at stop); it can
block the call. Most hooks come from a framework and come back when you reinstall it. The ones marked
**yours** live in `claude-home/` and you maintain them. To set hooks up on a new machine, see
[SETUP.md](SETUP.md#restore-on-a-new-machine).

## Where each hook comes from

| Hook file | Source | What it does |
|-----------|--------|--------------|
| `auto-approve-safe.sh` | jjstack | Since jjstack 0.4x (upstream #36, 2026-09-09) an audit log and private tool relay only; it approves nothing |
| `permission-floor.py` | jjstack | PreToolUse deny for ten unbounded shapes: root or home targets, curl to shell, file upload, secret paths, block devices, fork bomb, power, sudo destructive, force push to trunk, push --mirror |
| `error-detector.sh` | jjstack | Records failed Bash commands to a JSONL log |
| `injection-guard.sh` | jjstack | Scans Write and Edit content of `.md` files for prompt injection |
| `mcp-reconnect.sh` | jjstack | Reconnects MCP servers on tool failure. Not linked into `~/.claude/hooks/`: `settings.json` calls it at `~/.claude/skills/jjstack/hooks/` |
| `block-destructive.sh` | **yours** (`claude-home/hooks/`) | PreToolUse gate on Bash: hard blocks `rm -rf` aimed at an absolute, `$HOME`, parent (`..`) or wildcard path, so you run it by hand. The backstop that survives auto mode. Self checks: `bash claude-home/hooks/block-destructive.sh --test` |
| `plain-panel.py` | **yours** (`claude-home/hooks/`) | Refuses a question panel without "Learn this first" last, with more than 3 real options, or with jargon (spec 0028). `python3 claude-home/hooks/plain-panel.py --test` |
| `context-monitor.js` | **yours**, derived from get-shit-done-cc (`claude-home/hooks/`) | PostToolUse on Bash, Edit, Write, MultiEdit, Agent and Task: reads the session transcript and tells the model at 150k tokens used (again every 100k) to finish the step and `/rollover`, and once at 650k that autocompact is 50k away. Silent under `wf`. `node claude-home/hooks/context-monitor.js --test` (spec 0037) |
| `claude-config-reminder.py` | **yours** (`claude-home/hooks/`) | SessionStart: prints one line when upstream was not checked for 7 days or more, "run /claude-config update" (spec 0048). Never fetches, never runs the drift check |
| `workflow-start.sh` | **yours** (`claude-home/hooks/`) | SessionStart (startup and clear): tells the session the repo's first workflow step (`/audit` without `AGENTS.md`, else `/scope`), plus a weekly reminder to review the hub scopes. Skips the `/scope` line after a `/clear` when a handover is waiting (spec 0057) |
| `handover-start.sh` | **yours** (`claude-home/hooks/`) | SessionStart (clear only): when a `/rollover` handover at most 1 day old waits for this folder, loads it (cut to 7,000 bytes) and tells the new session to run the `/resume-from-clear` steps, so you type only `/clear`. Never consumes the slot. Silent under `wf`. `bash claude-home/hooks/handover-start.sh --test` (spec 0057) |
| `review-stack-pre-push` | **yours** (`claude-home/hooks/`) | **A git hook, not a Claude Code hook.** Link it into a repo's `.git/hooks/pre-push`, never in a bot reviewed repo (the work orgs in your private `work.md`). It refuses to push a commit with no `/review-stack` receipt, or one whose receipt says `BLOCK`. Calls no model |
| `gate.sh` | **yours** (`claude-home/skills/design/scripts/`) | **Stop** hook, and the only one registered from SKILL.md front matter rather than `settings.json`: `design` and `brand-system` both declare it. Exits 0 at once unless `~/.claude/.design-active` exists, so it never touches an unrelated session. With a run open it exits 2 (blocking) with the unclosed ledger rows, at most twice; the third stop releases and marks the run `escaped:true`. An abandoned ledger (over 24 h) or an unreadable one also releases. Checked by `claude-home/skills/design/scripts/test-ledger.sh` |
| `claude-ram-watch.sh` | **yours** (`claude-home/scripts/`) | Keeps sessions alive under memory pressure: sets `OOMPolicy=continue` on every scope holding a claude process, and kills a leaking helper (never claude itself) before the kernel does |

## Settings the hooks rely on

| Setting | State | Why |
|---------|-------|-----|
| Autocompact | not overridden | `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: 100` used to sit in `settings.json` as "autocompact off", which was wrong: the threshold is `min(window * pct/100, window - 13000)`, so `100` resolves to the default `window - 13000`. The `min()` means the override can only make compaction fire earlier. Removed; the default leaves a 13k summary buffer |
| Model | not pinned | The `model: opus[1m]` pin was removed in commit 82fcf80; the model is chosen at runtime (`/model`, or the session default) |
| `permissions.defaultMode: auto` with `skipAutoPermissionPrompt: true` | on | The policy is `permissions.deny` in `settings.json` (jjstack's `permissions.policy.json` merged in) plus `permission-floor.py`. The old local Haiku prompt patch to `auto-approve-safe.sh` and its upstream PR #31 are retired: the mechanism they tuned is gone. The auto mode classifier still blocks some commands (`git reset --hard`, some `git merge` shapes); run those yourself with the `!` prefix, or use a narrower command |
| Status line | `wf auto bar` (`runner/statusbar.py`, yours) | Our own bottom bar, ported from jjstack's `statusline.sh` so it no longer needs jjstack (spec 0058) |
