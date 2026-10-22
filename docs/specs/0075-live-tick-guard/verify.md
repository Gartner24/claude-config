# Verify 0075 (built 2026-10-22)

Run: `python3 -B claude-home/hooks/live-tick.py --test` (20 checks, all passed), `python3 -B tests/fast.py` (139 tests, 0 failed), `bin/install.sh --dry-run` (clean).
Drift output and both file trees are fakes in a temp folder (a fake `bin/claude-config.py` prints canned drift).

| AC | Evidence (check name in `--test`) | can fail |
|---|---|---|
| AC-1 | "unticking edit passes", "edit in a non scope file passes", "already ticked box left alone", "tick plus text change caught", "indented box caught", "replace_all caught", "MultiEdit caught" | `boxes = ticked(new)` without the old-text subtraction turns "already ticked" red; dropping the scope-folder test turns "non scope file" red; `n = 1` always turns "replace_all" red; `[ \t]*` removed turns "indented" red |
| AC-2 | "tick of a differing rule is refused", "passes once equal", "drift line refuses although bytes are equal", "hook missing live, not in drift, is refused", "typo path refused as not found", "install box ignores a live only extra", "install box refuses a missing file" | `direct()` returning `[]` turns the hook and typo checks red; `drift_matches` returning `[]` turns the drift-line check red; install filter `True` turns the live-only check red |
| AC-3 | "tick of a differing rule is refused" (deny JSON, `rule rules/x.md: differs`, hint line), "Write ticking two boxes lists both" | cutting the reason to one line turns the two-box check red |
| AC-4 | "box naming nothing passes" (drift fake lists a difference, edit still passes) | running the check on every live box turns it red |
| AC-5 | "failing drift refuses" (exit 2), "timed out drift refuses" (TIMEOUT 1, fake sleeps 3) | removing the `TimeoutExpired` branch turns the timeout check red |
| AC-6 | "crash passes", "crash logs one line" (`~/.claude/state/live-tick/errors.log` under a temp HOME) | removing the log call turns "logs one line" red |
| AC-7 | `hooks/live-tick.py` in `COPIED_FILES` (`bin/claude-config.py`); PreToolUse entry matcher `Edit|Write|MultiEdit`, timeout 65 in `claude-home/settings.json` (parses with `json.load`); `hooks/live-tick.py` in the `OPTIONAL` list of `bin/sync.sh`. Live copy steps are the owner's (see the build report). | n/a until live: `claude-config drift` shows `hook: hooks/live-tick.py: missing live` while the live copy is absent |
| AC-8 | the 20 checks above | each was mutation checked, see below |

## Mutants (all red, restored, green after)
new-vs-old, direct off, install reasons, timeout, replace_all, drift match, crash log, indent, multiedit, cap/dedupe, not-scope: 11 of 11 red. Two first ran green (replace_all, not-scope) because the test text could not tell the break; both tests were fixed and re-run red.

## Not covered
- A settings.json box is checked by drift only: the repo and live settings differ by design (`bin/sync.sh` strips them), so the byte compare of AC-2 (a) is skipped for `settings*.json`.
- Not run against the real `~/.claude` (sandbox, and the hook is not live yet).
