# 0050 verify

## Probe P1: name only and the budget, observed 2026-10-15

Observed in the skill list of a real session (this /architect session, Claude Code, 2026-10-15):
- `build-fix` and `21st-ai` (both `name-only` in `~/.claude/settings.json`) are listed with no description: the setting works for commands and skills.
- `academic` and `industrial-brutalist-ui` (no override) are also listed with no description, while `architect`, `review` and `cro` keep theirs: Claude Code drops descriptions by its own budget.
- Result: passed. The design relies only on the first point.

## Steps (for /check verify)

1. `python3 scripts/skill-keep.py --dry-run` against the real `~/.claude` lists `name-only:` for the 46 described own skills off the list (83 described today, 37 kept) and no line for any keep list name. can fail: the script inverts the list, or reads plugin skills.
2. After the real run and `./sync.sh`, a new session's skill list shows a description for every keep list name it has room for, and none for a name off the list (check `build-fix`, `council`, `astro`). can fail: the write lands in the wrong file or the wrong key.
3. Type `/council` (a name only skill) in a session: it runs. can fail: the script wrote `off` instead of `name-only`.
