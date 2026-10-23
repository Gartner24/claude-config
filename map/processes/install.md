# Install

## When
A new machine, or after changing a file under `claude-home/` that the repo ships.

## Steps
1. `tools/bin/install.sh --dry-run`: repo to `~/.claude` (copies and symlinks), then self-checks. Rerun without `--dry-run` to apply.
   The last self-check is `python3 tools/bin/claude-config.py hook-files`: exit 1 names each live `settings.json` hook command whose file is missing (hooks under `~/.claude/skills/` are skipped: jjstack and gstack install those).
2. After editing `tools/scripts/private-names.py`, rerun `tools/bin/install.sh` so the `pre-commit` and `commit-msg` hooks are refreshed: they are copies of the checker, not links.

## Done when
- The dry run prints no error and the hook copies are `cmp`-equal to `tools/scripts/private-names.py`.

## Also moves
- [install object](../objects/install.md): which kind is copied, linked or downloaded.

## Gotchas
- Private names live in `~/.claude/private/` (`names.txt`, `work.md`, `gitignore`, settings fragments), never in the repo (spec 0013). Without `names.txt`, `tools/bin/sync.sh` and every commit here fail closed. `tools/bin/sync.sh` moves name bearing settings entries into the fragments and `tools/bin/install.sh` merges them back. Hit lines print the `names.txt` line number, never the name.
- The pre-commit hook also refuses a commit where `AGENTS.md` is not a symlink to `CLAUDE.md` (spec 0072 AC-9); the repair command is in its message.
