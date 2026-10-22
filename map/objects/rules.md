# Rules and hooks

## What it is
The rule files every chat loads (`~/.claude/rules/`) and the hooks that enforce some of them.

## Where
- `claude-home/rules/`: copied kind, live wins (see [install](install.md)). `claude-home/rules/ecc/` is vendored.
- `claude-home/hooks/`: hand written hooks (guard, panel check, context monitor, handover start).
- `claude-home/CLAUDE.md`: the global instructions payload.

## Rules
- A figure the user gives replaces the old one in the skill's files; a figure with no source is a bracket placeholder (spec 0056, `claude-home/rules/new-number-replaces-old.md`; pinned by `tests/test_borrowed_ideas.py`).
- Cheap worker tier: `fb-ask <task> [--local] [--file PATH] < input` sends one text job to the free claude-fb models (spec 0023; `--local` = laptop model fb-local, client text allowed, spec 0053): summarize|triage|extract|classify|commit-msg. Exit 3 or 4 means do it yourself (`claude-home/rules/cheap-worker.md`). `fb-ask --test` runs its self checks; `bin/install.sh` links it to `~/.local/bin`.
- Do not edit vendored trees ([skills](skills.md)).

## Also moves
- Hook self checks: [checks](../processes/checks.md).
- A rule file edited here is overwritten on the next sync; edit it live, then sync ([sync](../processes/sync.md)).
