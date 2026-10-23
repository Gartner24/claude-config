# Rules and hooks

## What it is
The rule files every chat loads (`~/.claude/rules/`), the rules loaded only when a skill or situation needs them
(`~/.claude/rules-on-demand/`, spec 0077), and the hooks that enforce or load some of them.

## Where
- `claude-home/rules/`: always loaded, copied kind, live wins (see [install](install.md)). `claude-home/rules/ecc/` is vendored and excluded from loading.
- `claude-home/rules-on-demand/`: copied kind, live wins, never auto loaded. `claude-home/rules-on-demand/map.json` maps a skill name to its files.
- `claude-home/hooks/skill-rules.py`: the skill rules hook (PreToolUse `Skill` and UserPromptSubmit) prints a starting skill's mapped files; `--test` runs its self checks.
- `claude-home/hooks/`: hand written hooks (guard, panel check, context monitor, handover start, chain catch, skill rules).
- `claude-home/CLAUDE.md`: the global instructions payload; its Routing block names the on-demand file for each situation (pointer lines).

## Rules
- Always loaded text (`CLAUDE.md` plus `rules/*.md`) stays at most 20,000 characters; a rule moved to `rules-on-demand/` keeps its text word for word, and needs a `map.json` key or a pointer line (`tests/test_rules_on_demand.py`).
- A figure the user gives replaces the old one in the skill's files; a figure with no source is a bracket placeholder (spec 0056, `claude-home/rules/new-number-replaces-old.md`; pinned by `tests/test_borrowed_ideas.py`).
- Cheap worker tier: `fb-ask <task> [--local] [--file PATH] < input` sends one text job to the free claude-fb models (spec 0023; `--local` = laptop model fb-local, client text allowed, spec 0053): summarize|triage|extract|classify|commit-msg. Exit 3 or 4 means do it yourself (`claude-home/rules-on-demand/cheap-worker.md`). `fb-ask --test` runs its self checks; `tools/bin/install.sh` links it to `~/.local/bin`.
- Do not edit vendored trees ([skills](skills.md)).

## Also moves
- Hook self checks: [checks](../processes/checks.md).
- A rule file edited here is overwritten on the next sync; edit it live, then sync ([sync](../processes/sync.md)).
