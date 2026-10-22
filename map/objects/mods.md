# Mods

## What it is
Claude Code mods kept in this repo: `wf-handoff` (the `/handoff` command and the automatic handoff at the token line) and `chip-dash` (the band and panes).

## Where
- `claude-home/mods/wf-handoff/`: spec 0057, 0063, 0064.
- `claude-home/mods/chip-dash/`: specs 0058 to 0060, 0064, 0065. The band reads `facts.py` and the wf-handoff chain file; the Plan view reads `plan.py`, never the retired runner.

## Rules
- Repo wins, and this is the one exception to the same-path rule: each mod is linked as `~/.claude/skills/<name>` by hand after a `skillspector scan` (spec 0057), never by `bin/install.sh`.
- Tests: `claude plugin test claude-home/mods/wf-handoff` and `claude plugin test claude-home/mods/chip-dash`; run `claude plugin validate` beside each. Commands: [checks](../processes/checks.md).

## Also moves
- `plan.py` copies the scope parser: a change to the scope format ([scope](scope.md)) must reach it.
- Handoff behavior: [handoff](../processes/handoff.md).
