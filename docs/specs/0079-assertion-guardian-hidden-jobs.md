# 0079. Assertion Guardian: hidden background jobs and folder changes

**Date**: 2026-10-23
**Status**: Assumed (owner asleep 2026-10-23; confirm)
**Paths:** `tools/config/patches/assertion-guardian.patch`
**Amends:** [0068](0068-assertion-guardian-removed-checks.md) (AC-1 folder changes, AC-2 background runs)

## What you're agreeing to
- A shell command that starts a background job (`&`) anywhere, even inside `bash -c "..."`, `$(...)`, backticks, `eval` or a heredoc, is refused before it runs when it writes a test file.
- `env -C`, `env --chdir`, `builtin cd`, `command cd`, `eval`, `source` and `.` count as folder changes, like `cd`: a test file written after one is refused before running.
- `git -C` is not a folder change, and every command that ran before still runs.
- When the guard is too strict, you approve the command with `/allow-test-change`.

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

## Decision (Assumed)
- Strict reading: any bare `&` in any body, with a test target in the line, refuses before running. Rejected: tracking which body a target came from (more code, same outcome for the owner, who can approve with `/allow-test-change`).
- A heredoc body is read as shell text for the `&` check, so a test body holding a bare `&` (`&self` in Rust) is refused before running. Rejected: guessing whether the heredoc reader is a shell.
- `eval`, `source` and `.` are always folder changes, even when they do not `cd`. The sourced file itself is not read: a script that writes a test file it does not name stays the known gap of spec 0068 AC-2.
- `env -C` anywhere after `env` in the simple command counts, even when a later tool owns the `-C`; refusing is the safe direction.

## Consequences
- **Good**: the two ways around the rule found by the review are closed.
- **Bad**: a few harmless commands (a heredoc with a bare `&`, a `source` before a test edit) now need `/allow-test-change`.
- **Neutral**: the patch on upstream grows; spec 0048's merge keeps it.
