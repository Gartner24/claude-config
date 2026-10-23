# 0079. Assertion Guardian: hidden background jobs and folder changes

**Date**: 2026-10-23
**Status**: Accepted (owner confirmed 2026-10-23; built in PR #214)
**Paths:** `tools/config/patches/assertion-guardian.patch`
**Amended**: 2026-10-23: row 112 forms (same rule)
**Amended**: 2026-10-23: row 113 here-strings and process substitution (owner: same rule)
**Amends:** [0068](0068-assertion-guardian-removed-checks.md) (AC-1 folder changes, AC-2 background runs)

## What you're agreeing to
- A shell command that starts a background job (`&`) anywhere, even inside `bash -c "..."`, `$(...)`, backticks, `eval` or a heredoc, is refused before it runs when it writes a test file.
- `env -C`, `env --chdir`, `builtin cd`, `command cd`, `eval`, `source` and `.` count as folder changes, like `cd`: a test file written after one is refused before running.
- `git -C` is not a folder change, and every command that ran before still runs.
- When the guard is too strict, you approve the command with `/allow-test-change`.
- Rows 112 and 113, same rule: a `{ }` group or `( )` subshell, `xargs`, text piped into any shell or fed to one by `<<<` or `<(...)`, `env -S`, and `nice`, `timeout` and similar wrappers are refused before running when a test file is or could be the target.

## Summary
Scope row 108: two ways around spec 0068's "refuse before running" rule, found by the automated security review of the PR #206 build. The `&` check read only the top line with quotes and heredoc bodies blanked, so a job inside a nested body ran uncompared. `env -C sub sed -i ... a.test.ts` hid the command (`unwrap()` read `sub` as the command), and `builtin cd`, `eval`, `source`, `.` were not folder changes, so a relative test path was checked in the wrong folder. The owner was asleep and asked for the row to be finished, so the design choice is Assumed and waits for the owner.

## Context
- `hooks/analyze.ts` (upstream at pinned plus our patch): `commands()` splits a line into simple commands and already splits heredoc bodies, `$(...)`/backtick bodies and `bash -c` strings. `shellPlan()` set `refuseBefore` for a `&` with a regex over the top line only, and for `cd|pushd|popd` before a target.
- `unwrap()` drops `env` flags one word at a time, so the value of `-C`/`--chdir`/`-u`/`--unset` stayed as the command head.
- `register.tsx` calls `shellPlan()` only when `bashSignals()` names a test target, so a hidden command never reached the plan.
- Probe P1 (built mod, 2026-10-23): [verify.md](0079-assertion-guardian-hidden-jobs/verify.md).

## Requirements
- **AC-1** (hidden jobs) `commands()` reports a bare `&` (not `&&`, `|&`, `&>`, `>&`, `<&`, not inside quotes) in the line and in every body it splits: `-c` strings, `eval` strings, `$(...)` and backtick bodies, heredoc bodies. `shellPlan()` sets `refuseBefore` when the line has a test target and any such `&`. Mod test per form.
- **AC-2** (folder changes) `shellPlan()` treats `env -C`/`--chdir` (also `-C` inside combined short flags), `builtin cd`, `command cd`, `eval`, `source` and `.` as folder changes like `cd`: a test target after one sets `refuseBefore`. `unwrap()` skips `builtin`, and the value of `env -C`/`--chdir`/`-u`/`--unset`, so the command behind them is still seen. `eval` strings are split as commands. `git -C` is not a shell folder change. Mod test per form, plus one through the hook.
- **AC-3** (nothing else changes) every command the mod's tests allowed before stays allowed; one more test pins `bash -c` without a job, `git -C`, a quoted `&`, `&&` in a heredoc body, `2>&1`, `&>` and `eval "$(mise env)"`.
- **AC-4** The patch is regenerated with `claude-config.py patches`; upstream at pinned plus the patch equals the built mod byte for byte; `TestShippedPatch` stays green.

Row 112 (amendment 2026-10-23, same rule: a form that can hide a job, a folder change or a test target is refused before running):
- **AC-5** (groups) a `{ ...; }` brace group (its `{` is unwrapped, so the body is read like other nested bodies) or a `( ... )` subshell opened at the start of a command, in a line with a test target, sets `refuseBefore`. A `(` inside a word (`arr=(a b)`) is not a subshell, and `(`/`{` lines in a heredoc body are data. Mod test per form.
- **AC-6** (xargs) `xargs` is unwrapped with its value flags (`-I`, `-n`, `-a`, ...). When it runs a writer, a shell or a script, every test path anywhere in the line (inside quoted words too) is a target and the line refuses before running. `xargs grep` stays allowed. Mod test for `xargs sh|bash -c` and for `xargs` running a writer.
- **AC-7** (pipe into a shell) a pipe into `sh`, `bash`, `zsh`, `dash` (with no `-c`), `source` or `.` makes every test path anywhere in the line a target and refuses before running. Mod test, plus one through the hook (nothing runs).
- **AC-8** (wrappers) `nice`, `ionice`, `nohup`, `time`, `timeout <n>`, `stdbuf`, `setsid`, `chrt`, `taskset` are unwrapped like `env`/`command`/`builtin`, with their value flags and leading operands, so the command behind them is seen; a test write behind one sets `refuseBefore`. `setsid -f`/`--fork` is a background job. Mod test.
- **AC-9** (`env -S`) the `-S`/`--split-string` string is split as a command (the words after it are its arguments) and read; a test target in it refuses before running. Mod test.
- **AC-10** `source` and `.` keep refusing before a test target; the contents of a sourced file are not read, and the README gap list says so.
- **AC-11** every command the mod's tests allowed before stays allowed; one more test pins `time make test`, `timeout 60 npm test`, `nice -n 10 pytest`, `echo hi | grep h`, `( cd sub && ls )`, `xargs grep`, `cat a.test.ts | bash -c "grep ..."`, `arr=(a b)` before a compared `sed`, and a heredoc test body with `(`, `{` and `| sh` text.
- **AC-12** the patch is regenerated as in AC-4; upstream at pinned plus the patch equals the built mod; `TestShippedPatch` green.

Row 113 (amendment 2026-10-23, owner: same rule, refuse before running):
- **AC-13** (here-strings) text fed to a shell or `source` by a here-string (`bash <<< "..."`, `sh <<<`, `zsh <<<`, `source /dev/stdin <<<`) makes every test path anywhere in the line a target and refuses before running. `<<<` is one word, and the here-string body fed to a shell is read like other nested bodies. Mod test, plus one through the hook (nothing runs).
- **AC-14** (process substitution) text fed by `source <(...)`, `. <(...)`, `bash <(...)`, `sh <(...)` refuses before running when the line names a test path. A `<(...)` or `>(...)` body is read like other nested bodies, and since it runs on without the line waiting for it, a test write in one refuses before running like a `&` job. Mod test per form.
- **AC-15** (other shells) a pipe into `ksh`, `mksh`, `ash`, `busybox sh` (`busybox` is unwrapped) or `fish` counts like a pipe into `sh` (AC-7); these shells' `-c` strings are split like `bash -c`. A `while`/`until` loop whose body runs a shell, `eval`, `source` or `.` (`... | while read x; do sh -c "$x"; done`) is fed text too. Mod test per form.
- **AC-16** every command the mod's tests allowed before stays allowed; one more test pins `grep x <<< "$s"`, `diff <(sort a) <(sort b)`, `while read l; do echo "$l"; done < list.txt`, `bash <<< "echo hi"`, `cat a.test.ts | while read l; do echo "$l"; done`, `grep expect <<< "a.test.ts"`, `wc -l <(cat a.test.ts)` and a shell `-c` after a loop's `done`. The patch is regenerated as in AC-4; upstream at pinned plus the patch equals the built mod; `TestShippedPatch` green.

## Decision (Assumed)
- Strict reading: any bare `&` in any body, with a test target in the line, refuses before running. Rejected: tracking which body a target came from (more code, same outcome for the owner, who can approve with `/allow-test-change`).
- A heredoc body is read as shell text for the `&` check, so a test body holding a bare `&` (`&self` in Rust) is refused before running. Rejected: guessing whether the heredoc reader is a shell.
- `eval`, `source` and `.` are always folder changes, even when they do not `cd`. The sourced file itself is not read: a script that writes a test file it does not name stays the known gap of spec 0068 AC-2.
- `env -C` anywhere after `env` in the simple command counts, even when a later tool owns the `-C`; refusing is the safe direction.
- Row 112: a wrapper refuses before running even though its command is now seen (the row's Done when; `timeout` can kill a write half done, `nohup`/`setsid` detach it). `env FOO=1`, `command`, `builtin`, `exec` and `sudo` keep the compare.
- Row 112: for `xargs` and a pipe into a shell the paths come from input the line does not split, so any test path the line names counts ("could be a target"). A line that names no test path (`git ls-files | xargs rm`, `cat go.sh | sh`) stays the known gap of spec 0068 AC-2.
- Row 113 (owner 2026-10-23: "I just want the easiest way for you to work without me so do the best", decided: same rule): a here-string or `<(...)` is read only when a shell or `source` is fed by it; a here-string to `grep` is data. A loop counts as fed whatever its input (a pipe, `<`, `<<<`), when its body runs a shell. Running a script in a test folder with input fed to it (`bash tests/run.sh <<< y`) is refused, the same as `echo y | bash tests/run.sh` under AC-7.

## Consequences
- **Good**: the two ways around the rule found by the review are closed.
- **Bad**: a few harmless commands (a heredoc with a bare `&`, a `source` before a test edit) now need `/allow-test-change`.
- **Neutral**: the patch on upstream grows; spec 0048's merge keeps it.
