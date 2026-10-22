# 0072a. Reference check, tests split, runner archive

## Summary
First PR of phase 1. It adds the script that proves no path broke, moves the 8 tests for live code to `tests/`, and moves the retired runner and its old docs to `_archive/runner/`. Branch `feat/0072-ref-check-and-archive`, off `main`.

## Scope
Acceptance criteria AC-1 to AC-5 of [index.md](index.md); build plan tasks 1 to 4 and 9.

## Notes for the build
- Take the snapshot on `main` before the first `git mv`, and keep it outside the repo (`$CLAUDE_JOB_DIR/tmp` or the worktree's git dir).
- Moves are `git mv` only, so history follows the files.
- A runner spec whose decision is still in force stays live until that decision has a live home; list each one in the PR body (AC-4).
- Rationale: the reference check comes first because every later move is judged by it.
