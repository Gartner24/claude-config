# 0079 verify notes

## P1 how the mod sees each form (run 2026-10-23, Claude Code plugin test harness)
- Setup: the built mod in a throwaway folder `/tmp/ag0079/scratch` = upstream `ccdwyer/assertion-guardian` at pinned `ae1de89f` plus the patch on origin/main (`30386bf`); base hash checked equal to the manifest's. No settings and no live folder touched.
- Probe: a throwaway test file `tests/probe.test.tsx` that printed `shellPlan(form, '/repo')` for each form through a failing `toEqual([])`. Command: `claude plugin test /tmp/ag0079/scratch`.
- Result before the change (`targets`, `refuseBefore`):
  - `bash -c "sed -i '/expect/d' a.test.ts &"`: `[/repo/a.test.ts]`, false
  - `echo "$(sed -i '/expect/d' a.test.ts &)"`: `[/repo/a.test.ts]`, false
  - ``echo "`sed -i '/expect/d' a.test.ts &`"``: `[/repo/a.test.ts]`, false
  - `bash <<'EOF'` / `sed -i '/expect/d' a.test.ts &` / `EOF`: `[/repo/a.test.ts]`, false
  - `env -C sub sed -i '/expect/d' a.test.ts`: `[]`, false (the target is hidden: `sub` read as the command, so `bashSignals()` is empty and the hook runs it unchecked)
  - `env --chdir=sub sed ...`: `[/repo/a.test.ts]`, false (checked in the wrong folder)
  - `env --chdir sub sed ...`: `[]`, false
  - `builtin cd sub; sed ...`: `[/repo/a.test.ts]`, false
  - `command cd sub; sed ...`: `[/repo/a.test.ts]`, true (already refused: `unwrap()` drops `command`)
  - `eval cd sub; sed ...`: `[/repo/a.test.ts]`, false
  - `eval "sed -i '/expect/d' a.test.ts"`: `[]`, false (eval strings were not split)
  - `source ./go.sh; sed ...`: `[/repo/a.test.ts]`, false
  - `. ./go.sh; sed ...`: `[/repo/a.test.ts]`, false
- Verdict: the row's finding is confirmed for every form except `command cd`, which is pinned by a test now. The probe file was removed before the patch was made.

## Build checks (2026-10-23)
- `claude plugin test /tmp/ag0079/scratch`: 69 pass, 0 fail (56 before, 13 new). `claude plugin validate`: passed.
- Patch regenerated with `CLAUDE_LIVE_DIR=/tmp/ag0079/live python3 -B tools/bin/claude-config.py patches` (the throwaway live dir held the built mod and a temporary copy of the private names list; without that list the private-name check fails closed and the patch would go private). Upstream at pinned plus the new patch, rebuilt in `/tmp/ag0079/rebuilt`, equals the built mod (`diff -r`, no difference).
- `python3 -B tests/fast.py`: 184 tests, 0 failed (`TestShippedPatch` included). `bash tools/bin/install.sh --dry-run`: done, nothing written.

## Mutation checks (2026-10-23)
Each mutant applied to `hooks/analyze.ts` of the built mod alone (backup with `cp`), `claude plugin test` run, then restored; after the last one 69 pass, 0 fail.
1. job flag never set: red "a & job inside a -c string / $(...) / backtick / heredoc body", and the old "a heredoc body is not shell text, and a & job is refused".
2. bodies split without the job flag: red the `$(...)`, backtick and heredoc tests.
3. `-c` string split without the job flag: red the `-c` test.
4. eval strings not split: red "a & job inside an eval string" and "eval is a folder change, and the command it runs is seen".
5. env value not skipped: red "env -C and --chdir ..." and "the hook refuses env -C before running anything".
6. env -C not a folder change: red the same two.
7. `builtin` not unwrapped: red "builtin cd".
8. `command` not unwrapped: red "command cd".
9. `eval` not a folder change: red "eval is a folder change".
10. `source` not a folder change: red "source".
11. `.` not a folder change: red ". is refused".
12. `&&` counted as a job: red "normal commands stay allowed" and 5 older tests.

## /check verify (2026-10-23)
Behavior observed through the built mod with `claude plugin test` (69 pass). Each break was applied and the named test went red (mutants above).
1. AC-1 a `&` job inside a `-c` string, `$(...)`, backtick, heredoc or eval body is refused before running. can fail: the body recursion drops the job flag (mutants 1 to 4 red).
2. AC-2 `env -C`/`--chdir`/`-iC` is refused before running, and through the hook nothing runs (`w.runs` 0). can fail: the env value read as the command again, or env -C not counted as a move (mutants 5, 6 red).
3. AC-2 `builtin cd`, `command cd`, `eval`, `source`, `.` before a test target refuse before running. can fail: any one dropped from the unwrap list or the folder change regex (mutants 7 to 11 red).
4. AC-3 normal commands stay allowed, and the 56 older tests still pass. can fail: a looser job rule counting `&&` (mutant 12 red, 6 tests).
5. AC-4 upstream at pinned plus the patch equals the built mod; `TestShippedPatch` green in `python3 -B tests/fast.py`. can fail: a hunk dropped or edited makes the apply or `diff -r` fail.
6. Live install: done by the parent session after merge; not claimed here.
CAN FAIL CHECKED: 5
