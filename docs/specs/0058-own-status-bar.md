# 0058. Our own status bar, without jjstack

**Date**: 2026-10-17
**Status**: Proposed
**Paths:** `runner/statusbar.py`, `runner/auto.py`, `runner/tests/test_statusbar.py`, `runner/tests/test_auto.py`
**Amends**: [0030](0030-autonomous-mode/index.md) AC-10 (the bar no longer runs jjstack's script)

## What you're agreeing to
- The bottom status bar stops calling jjstack's script; our own copy draws the same segments (model and effort, folder, git branch and changes, context use, 5 hour and weekly use).
- It looks the same as today, and still marks this chat as alive for the runner.
- Once the dashboard band exists (next spec), this bar can shrink to a short line; that switch is in the next spec.

## Summary
The status line in settings is `wf auto bar`, which runs jjstack's `statusline.sh` and adds the runner segment. Removing jjstack from it means porting that script's segments into the runner. The bar must keep writing the chat's `seen` time, because the per chat autonomous mode uses it to know a chat is alive.

## Context
`bar()` (`runner/auto.py:636-664`) runs `~/.claude/skills/jjstack/bin/statusline.sh` (237 lines) with `BAR_TIMEOUT` 2 s (`auto.py:25`, `:641`), then appends the AUTO segment and updates `seen` (spec 0046 AC-4). What the script draws: effort from stdin `.effort.level`, else `CLAUDE_CODE_EFFORT_LEVEL`, else `settings.local.json`, else `settings.json`, else "auto", with a color per level (`:18-29`, `:219-228`); folder and model; git branch and staged, modified and untracked counts or clean from 4 git calls (`:37-41`); context percent (`:102-107`); and usage in one of three modes (`:128-209`): through a provider (`ANTHROPIC_BASE_URL` not anthropic.com, as claude-fb) it prints `via <host>` and no usage; with your subscription login it reads `/tmp/claude-usage-cache.json` (300 s life), refreshed by a detached call to the usage endpoint with the token in `~/.claude/.credentials.json` (`:139-179`); with an API key it prints the cost with thresholds 1 and 5 dollars (`:193-209`). Bars come from `create_progress_bar` (`:55-100`): green under 70, yellow 70 to 89, red 90 and up, 5 wide centred label. The script turns a missing value into 0 (`:137`, `:181`, `:187`); the port does not. Plan B3 and row 57: the status line no longer needs jjstack. Your answer: get rid of the jjstack status bar.

## Requirements
- **AC-1** (port): `runner/statusbar.py` `render(data, short=False)` takes the status line stdin JSON and returns the bar with the segments above in the same order, colors and thresholds (effort fallback chain and colors, model, folder, git, context, usage in all three modes), stdlib and `git` only. It reads the usage cache and, when it is older than 300 s, starts the same detached refresh the script does (same token path, same cache file, so the two can run side by side), never waiting for it. It never raises into `bar()`.
- **AC-2** (no jjstack): `bar()` calls `statusbar.render` instead of the jjstack script; with no `~/.claude/skills/jjstack` folder at all, the bar still prints model, folder, branch and context.
- **AC-3** (unknown is not zero, unlike the script): a usage figure that cannot be read shows `5h ?` and `wk ?`, never `0%`; through a provider it shows `via <host>`; a failed git call shows no git segment rather than "clean".
- **AC-4** (liveness kept): `bar()` still updates the chat's `seen` exactly as today (`auto.py:654-655`) and still appends the AUTO segment.
- **AC-5** (speed): git runs once, `git status --porcelain=v1 -b` with a 1 s timeout, and the branch and the three counts come from its output; a timeout drops the git segment. `render` stays inside the 2 s budget; if it fails, `bar()` still prints the AUTO segment as today.
- **AC-6** (tests): fixtures for each segment, each effort source, the three usage modes, a stale cache (refresh started, old value shown), an unreadable cache (`?`), a missing jjstack folder, a git timeout, and a dirty and a clean repo; mutation checked.

## Decision
Port the segments into one runner module and call it from `bar()`.

## Build plan
1. `statusbar.py` with the ported segments and the unknown rules, satisfies **AC-1**, **AC-3**, **AC-5**
2. `bar()` switch and liveness kept, satisfies **AC-2**, **AC-4**
3. Tests, satisfies **AC-6**

## Consequences
**Positive**: row 57's status line part closes; one fewer outside script on every redraw.
**Negative / tradeoffs**: our copy will not get jjstack's future bar changes.
**Neutral**: jjstack itself stays installed (plan row 57 answer).
