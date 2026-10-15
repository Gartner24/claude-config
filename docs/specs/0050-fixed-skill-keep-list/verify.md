# 0050 verify

## Probe P1: name only and the budget, observed 2026-10-15

Observed in the skill list of a real session (this /architect session, Claude Code, 2026-10-15):
- `build-fix` and `21st-ai` (both `name-only` in `~/.claude/settings.json`) are listed with no description: the setting works for commands and skills.
- `academic` and `industrial-brutalist-ui` (no override) are also listed with no description, while `architect`, `review` and `cro` keep theirs: Claude Code drops descriptions by its own budget.
- Result: passed. The design relies only on the first point.

## Steps (for /check verify)

- [x] 1. `python3 scripts/skill-keep.py --dry-run` against the real `~/.claude` lists `name-only:` for the 46 described own skills off the list (83 described today, 37 kept) and no line for any keep list name. can fail: the script inverts the list, or reads plugin skills.
- [ ] 2. After the real run and `./sync.sh`, a new session's skill list shows a description for every keep list name it has room for, and none for a name off the list (check `build-fix`, `council`, `astro`). can fail: the write lands in the wrong file or the wrong key.
- [ ] 3. Type `/council` (a name only skill) in a session: it runs. can fail: the script wrote `off` instead of `name-only`.

## Results, /check verify 2026-10-15

- Step 1, passed: `python3 -B scripts/skill-keep.py --dry-run` exit 0, 46 `name-only:` lines (council, astro, academic, industrial-brutalist-ui among them), no line for any keep list name, no `warning:` line, `described: 37 own skills`. `~/.claude/settings.json` sha256 `5b1162ba...` the same before and after. Every plugin reported: claude-mem and claude-seo `off`, sentry-skills `27 skills` (from `skills/*/.claude-plugin`), 10 others with counts, `total described: 87`. Can fail shown: a scratch copy with `if name in keep` inverted printed `name-only:` for all 37 keep names and `described: 255 own skills`.
- Write path (AC-3, AC-4, AC-7), passed on a copy: a temp `CLAUDE_LIVE_DIR` with a copy of the real `settings.json` (mode 0640) and links to the real `skills/`, `commands/`, `plugins/`. Real run exit 0, last line `next: run ./sync.sh now, before any install.sh`; every key but `skillOverrides` equal and in the same order; old override order kept; `off` and `user-invocable-only` values unchanged; 46 new `name-only` entries (council, build-fix, astro all `name-only`), no keep name `name-only`; mode 0640 kept, trailing newline; one backup `backups/settings/settings.json.bak.20261015-123947`; a second dry run lists no change.
- AC-8: `python3 -B -m unittest runner/tests/test_skill_keep.py` 11 tests OK (mutation checks belong to `/test`).
- AC-9: `python3 scripts/private-names.py check scripts/skill-keep.txt scripts/skill-keep.py runner/tests/test_skill_keep.py` exit 0, no hit. (A whole repo `check` in the sandbox stops on the masked dotfiles, `Permission denied`, not on a name.)
- Step 2: left to the box: Run `python3 scripts/skill-keep.py --dry-run`, then without it, then `./sync.sh` right away (AC-7)
- Step 3: left to the box: Run `python3 scripts/skill-keep.py --dry-run`, then without it, then `./sync.sh` right away (AC-7)
