# A live install box is ticked only when it is live (scope row 87)

## Agreed so far, do not ask again
- 2026-10-22: the refusal happens on the edit itself: a PreToolUse hook sees an Edit, Write or MultiEdit that ticks a box ending ` · live` (or ` · live · later boxes go on`) in a scope file, runs `claude-config drift`, and refuses the edit with the drift lines for that box's files.
- 2026-10-22: a box naming `claude-home/` or `~/.claude/` paths is checked against drift lines for those paths only; a box naming `bin/install.sh` is checked against every "different" or "missing live" drift item, "live only" extras ignored; a box naming neither (a real check, an e2e run) is not checked.
- 2026-10-22: spec 0075 written; cross check (Sonnet) found 9 points, owner picked "apply the recommended fixes": every named file is also compared byte for byte (a file drift does not list cannot pass), the install box keeps exactly "differs" and "missing live", newly ticked live boxes are found by comparing old and new text.
