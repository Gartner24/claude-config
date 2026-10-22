# Install

## When
A new machine, or after changing a file under `claude-home/` that the repo ships.

## Steps
1. `bin/install.sh --dry-run`: repo to `~/.claude` (copies and symlinks), then self-checks. Rerun without `--dry-run` to apply.
2. After editing `scripts/private-names.py`, rerun `bin/install.sh` so the `pre-commit` and `commit-msg` hooks are refreshed: they are copies of the checker, not links.

## Done when
- The dry run prints no error and the hook copies are `cmp`-equal to `scripts/private-names.py`.

## Also moves
- [install object](../objects/install.md): which kind is copied, linked or downloaded.

## Gotchas
- Private names live in `~/.claude/private/` (`names.txt`, `work.md`, `gitignore`, settings fragments), never in the repo (spec 0013). Without `names.txt`, `bin/sync.sh` and every commit here fail closed. `bin/sync.sh` moves name bearing settings entries into the fragments and `bin/install.sh` merges them back. Hit lines print the `names.txt` line number, never the name.
- The pre-commit hook also refuses a commit where `AGENTS.md` is not a symlink to `CLAUDE.md` (spec 0072 AC-9); the repair command is in its message.
