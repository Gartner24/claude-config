# 0068 rationale

## Evidence: what the mod refused (all chats, counted 2026-10-20)
62 distinct refusals; one refusal can carry several signals.
- 37 "test files changed through the shell". Commands: sed 30, rm 21, cp 10, cat 9, git 5, python3 5, mv 3, tee 2, perl 1. Mostly `sed -i` edits, `cat >>` appending new tests, `rm` of scratch `zz-*.test` files, and `cp` restores during mutation checks. Most of these were harmless.
- 23 "expected values changed", 7 "assertions removed", 4 "test cases deleted", 4 "polarity flipped". These stay refused.
Counted with two scripts over the chat files (`tally.py`, `shellhits.py` in the conductor job's tmp folder); one work repo accounts for many of them.

## Why run, compare, undo
The edit tools already compare before and after with `weakening()`, which passes additions. The shell path refuses blind because it cannot know what a command will do. After the command has run, it can: the same compare then applies to every file the command names. Undoing puts the file back, so a weakening edit never stays.

## Why a patch, not a copy in claude-home/mods
The owner wants our change kept and each author update merged into it (spec 0048's `edited` entry and three way merge). An `edited` entry lives at `~/.claude/skills/<name>` as a plain folder; `update --apply` swaps that folder with `install_folder()`, which would remove a link into the repo. So the change is the patch, and the repo holds the patch.

## Not done
- Glob, folder, git and mv targets stay refused before running (no cheap exact undo: git also changes the index, mv leaves its new file behind).
- Cross check (another model, 2026-10-20) found nine holes; the owner picked "apply all fixes": path resolution, a named `shellPlan()` helper, mv refused before, try/finally, allow once spent only on use, undo only when unchanged since, text only, the notice and drift fixes in `claude-config.py`, the patch made from a scratch export, and no sync before the live install.
- A script that writes a test file it does not name is not caught, as today.
