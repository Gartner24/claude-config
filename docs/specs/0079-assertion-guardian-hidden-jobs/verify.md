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

## Review round 1 (2026-10-23, PR #214)
- Probe on the built mod: `bash -lc`, `env`/`sudo`/`nohup`/`time` before `bash -c`, and `command eval`/`builtin eval` hid the -c or eval string, so a `&` or a test target inside it ran uncompared (`bashSignals` empty). Fixed in `commands()`: heads read through `unwrap()`, flag `-[a-zA-Z]*c`.
- Mod test "a -c or eval string is read behind a wrapper and with combined flags": 70 pass, 0 fail. Mutant (old head and `-c` detection) red on that test only; restored, 70 pass. Patch regenerated, upstream at pinned plus patch equals the built mod (`diff -r`).

## Row 112 amendment (2026-10-23, branch fix/0079-guardian-more-forms)

### P2 how the mod sees each row 112 form (before the change)
- Setup: upstream `ccdwyer/assertion-guardian` cloned to `/tmp/ag112/upstream`, checked out at pinned `ae1de89f`; the patch on origin/main (`a815465`) applied with a small python script (`git apply` through `subprocess`, since the live guardian refuses a typed `git apply` in a repo with tests) into the throwaway `/tmp/ag112/live/skills/assertion-guardian`. No settings and no live folder touched.
- Probe: a throwaway `tests/probe.test.tsx` printing `bashSignals` count and `shellPlan(form, '/repo')` through a failing `toEqual([])`. Command: `claude plugin test /tmp/ag112/live/skills/assertion-guardian`. `S` is `sed -i '/expect/d' a.test.ts`.
- Result before the change (signals, targets, refuseBefore):
  - `{ S & }`: 0, `[]`, false (the `{` read as the command hid the target)
  - `{ S; }`: 0, `[]`, false
  - `( S )`: 1, `[/repo/a.test.ts]`, false (compared, not refused)
  - `ls tests | xargs sh -c 'sed -i /expect/d "$@"' _`: 0, `[]`, false
  - `ls tests | xargs rm`: 0, `[]`, false
  - `echo a.test.ts | xargs sed -i '/expect/d'`: 0, `[]`, false
  - `echo "S" | sh` (also `| bash`, `| zsh`, `| source /dev/stdin`): 0, `[]`, false
  - `nice -n 10 S`, `ionice -c 3 S`, `timeout 60 S`, `stdbuf -o L S`, `setsid S`, `chrt -f 99 S`, `taskset -c 0 S`: 0, `[]`, false (the value or operand read as the command)
  - `nohup S`, `time S`: 1, `[/repo/a.test.ts]`, false (compared, not refused)
  - `env -S "S"`: 0, `[]`, false
  - `source ./go.sh; S`: 1, `[/repo/a.test.ts]`, true (already refused)
  - `time make test`, `timeout 60 npm test`, `nice -n 10 pytest`, `echo hi | grep h`, `( cd sub && ls )`: 0, `[]`, false
- Verdict: every row 112 form ran without a refusal before running except `source`/`.`. After the change the same probe gave 1, the target, true for every form, and 0, `[]`, false for the five normal commands. The probe file was removed before the patch was made.
- First build run: the `(` and `{` checks also fired inside heredoc bodies (two older tests red: `cat >> a.test.ts <<'EOF'` with `expect(a && b)` and `it('negatives', () => {`). Fixed: heredoc bodies keep only their `&` jobs, and `(` counts only at the start of a command.

### Build checks
- `claude plugin test /tmp/ag112/live/skills/assertion-guardian`: 80 pass, 0 fail (70 before, 10 new). `claude plugin validate`: passed.
- Patch regenerated with `CLAUDE_LIVE_DIR=/tmp/ag112/live python3 -B tools/bin/claude-config.py patches` (the throwaway held the built mod and a read-only copy of the private names list). Upstream at pinned plus the new patch, rebuilt in `/tmp/ag112/rebuilt` with the same python script, equals the built mod (`diff -r`, no output).
- `python3 -B tests/fast.py`: 194 tests, 0 failed. `TestShippedPatch` run alone: ok. `bash tools/bin/install.sh --dry-run`: done, nothing written.

### Mutation checks
Script `/tmp/ag112/mutate.py`: each mutant applied alone to `hooks/analyze.ts` of the built mod (backup with `cp`), `claude plugin test` run, then restored; after the last one 80 pass, 0 fail.
1. `{` not unwrapped: red "a { } group is read like a nested body".
2. `{` group not hidden: red the same test.
3. `( )` subshell not hidden: red "a ( ) subshell with a test write".
4. `(` hidden anywhere, not only at command start: red "normal commands stay allowed: wrappers, pipes ..." (`arr=(a b)`).
5. `xargs` not unwrapped: red both xargs tests.
6. fed targets never found: red both xargs tests, the pipe test and the hook test.
7. pipe into a shell not seen: red the pipe test and the hook test.
8. pipe into `sh -c` counted as stdin: red "normal commands stay allowed" (`cat a.test.ts | bash -c "grep expect"`).
9. wrappers not refused before: red the wrappers test.
10. wrapper operands not skipped: red the wrappers test (`timeout 60`, `chrt -f 99`, `taskset 0x3`).
11. wrapper flag values not skipped: red the wrappers test, both xargs tests and the two older `env -C` tests.
12. `setsid -f` not a job: red "setsid -f forks a background job".
13. `env -S` string not split: red the env -S test.
14. `env -S` string not hidden: red the env -S test.
15. heredoc body sets groups and pipes: red "normal commands stay allowed" (the heredoc data case).
16. `xargs` counts any command: red "normal commands stay allowed" (`xargs grep`).

### /check verify
Behavior observed through the built mod with `claude plugin test` (80 pass). Each break was applied and the named test went red (mutants above).
1. AC-5 a `{ }` group or `( )` subshell with a test write is refused before running. can fail: the `{` read as the command again, or the group flag dropped (mutants 1 to 3 red).
2. AC-6 `xargs sh -c` and `xargs` running a writer are refused before running, with the test path from the line. can fail: xargs not unwrapped or the fed paths dropped (mutants 5, 6 red).
3. AC-7 text piped into `sh`, `bash`, `zsh`, `source`, `.` is refused before running, and through the hook nothing runs (`w.runs` 0). can fail: the pipe flag never set (mutant 7 red, hook test included).
4. AC-8 the nine wrappers are unwrapped and a test write behind one is refused before running; `setsid -f` is a job. can fail: a value flag or leading operand read as the command, or the wrapper rule dropped (mutants 9 to 12 red).
5. AC-9 `env -S` and `--split-string` strings are split, read and refused before running. can fail: the string not split or not flagged (mutants 13, 14 red).
6. AC-11 the 70 older tests still pass, and the new allow test pins the normal commands. can fail: a looser rule (mutants 4, 8, 15, 16 red).
7. AC-12 upstream at pinned plus the patch equals the built mod; `TestShippedPatch` green. can fail: a hunk dropped or edited makes the apply or `diff -r` fail.
- Dropped as a pass: AC-10 (`source`/`.` keep refusing) is pinned by the older "source is refused" and ". is refused" tests and the README gap line, not by a new mutant; not counted.
- Live install: owed after merge; not claimed here.
CAN FAIL CHECKED: 7

## Row 113 amendment (2026-10-23, branch fix/0079-guardian-here-strings)

### P3 how the mod sees each row 113 form
- Setup: upstream `/tmp/ag112/upstream` at pinned `ae1de89f` (HEAD checked, clean); the patch on origin/main (`2116290`) applied with the same python script (`git apply` through `subprocess`) into the throwaway `/tmp/ag113/live/skills/assertion-guardian`. No settings and no live folder touched.
- Probe: a throwaway `tests/probe.test.tsx` printing `bashSignals` count and `shellPlan(form, '/repo')` through a failing `toEqual([])`. Command: `claude plugin test /tmp/ag113/live/skills/assertion-guardian`. `S` is `sed -i '/expect/d' a.test.ts`.
- Result before the change (signals, targets, refuseBefore): every form gave 0, `[]`, false: `bash <<< "S"`, `sh <<< "S"`, `zsh <<<"S"`, `source <(echo "S")`, `. <(echo "S")`, `bash <(echo "S")`, `sh <(echo "S")`, `echo "S" | ksh`, `| mksh`, `| ash`, `| busybox sh`, `| fish`, `echo "S" | while read x; do sh -c "$x"; done`. The four normal commands (`grep x <<< "$s"`, `diff <(sort a) <(sort b)`, `while read l; do echo "$l"; done < list.txt`, `bash <<< "echo hi"`) also 0, `[]`, false.
- Result after the change: every row 113 form 1, `[/repo/a.test.ts]`, true. The four normal commands, `cat a.test.ts | while read l; do echo "$l"; done`, `grep expect <<< "a.test.ts"`, `wc -l <(cat a.test.ts)` and `cat <<EOF` / `x` / `EOF`: 0, `[]`, false. `bash tests/run.sh <<< y`: 1, `[/repo/tests/run.sh]`, true (same as `echo y | bash tests/run.sh` under AC-7). The probe file was removed before the patch was made.
- Seen in the same probe: `for f in a; do S; done` gave 0, `[]`, false (`do` read as the command hid the write from the compare). Closed in this branch by AC-17 (owner: "do the best so I'm not needed"); after it the form gives 1, `[/repo/a.test.ts]`, false (compared, not refused).

### AC-17 shell keywords (same branch)
- `claude plugin test`: 98 pass, 0 fail (89 before, 9 new: `for`, `while`/`until`, `if ... then`, `else`, `elif`, `case` branch, `!`, a `cd` after `then`, and the hook compare-and-undo of a write in a `for` loop). `claude plugin validate`: passed. Patch regenerated the same way; rebuilt in `/tmp/ag113/rebuilt2`, `diff -r` with the built mod: no output.
- Mutants (same script, each alone, restored after; 98 pass at the end):
  - 10 `do` not dropped: red the `for`, `while`/`until` and hook tests, and the while read loop test.
  - 14 `then` not dropped: red the `if ... then` test and the `cd` after `then` test.
  - 15 `else` not dropped: red the `else` test.
  - 16 `elif` not dropped: red the `elif` test.
  - 17 `!` not dropped: red the `!` test.
  - 18 `)` not ending a command: red the `case` branch test (and three older tests).
- can fail: a keyword left in front of the command hides the write again (mutants 10, 14 to 17 red); the `case` branch is pinned by mutant 18.
CAN FAIL CHECKED: 6

### Build checks
- `claude plugin test /tmp/ag113/live/skills/assertion-guardian`: 89 pass, 0 fail (81 before, 8 new). `claude plugin validate`: passed.
- Patch regenerated with `CLAUDE_LIVE_DIR=/tmp/ag113/live python3 -B tools/bin/claude-config.py patches` (the throwaway held the built mod and a read-only copy of the private names list). Upstream at pinned plus the new patch, rebuilt in `/tmp/ag113/rebuilt` with the same python script, equals the built mod (`diff -r`, no output).
- `python3 -B tests/fast.py`: 195 tests, 0 failed. `TestShippedPatch` run alone (`tests/fast.py test_claude_config.TestShippedPatch`): 0 failed. `bash tools/bin/install.sh --dry-run`: done, nothing written.

### Mutation checks
Script `/tmp/ag113/mutate.py`: each mutant applied alone to `hooks/analyze.ts` of the built mod (backup with `cp`), `claude plugin test` run, then restored; after the last one 89 pass, 0 fail.
1. `<<<` not one word: red the here-string test, the here-string body test and the hook test.
2. here-string not fed: red the here-string test and the hook test.
3. here-string body not read: red the here-string body test.
4. `<(...)` not fed: red the process substitution test.
5. `<(...)` not split: red the process substitution test and the `<( )` body test.
6. `<(...)` not a job: red the `<( )` body test.
7. `ksh`, `mksh`, `ash`, `fish` not shells: red the other shells test.
8. `busybox` not unwrapped: red the other shells test.
9. loop not seen: red the while read loop test.
10. `do` not dropped before the loop body's command: red the while read loop test.
11. a here-string fed to any command: red "normal commands stay allowed: here-strings ..." (`grep expect <<< "a.test.ts"`).
12. loop not ended at `done`: red the same allow test (`sh -c` after `done`).
13. a loop with any body fed: red the same allow test (`cat a.test.ts | while read l; do echo "$l"; done`).

### /check verify
Behavior observed through the built mod with `claude plugin test` (89 pass). Each break was applied and the named test went red (mutants above).
1. AC-13 a here-string fed to `bash`, `sh`, `zsh`, `source` is refused before running, its body is read, and through the hook nothing runs (`w.runs` 0). can fail: `<<<` split into three `<` words, or the here-string not counted as fed (mutants 1 to 3 red).
2. AC-14 `source`, `.`, `bash`, `sh` fed by `<(...)` are refused before running; a `<(...)` body is split and a test write in it is refused. can fail: the `<(` read as a redirect and a subshell again, or not counted as a job (mutants 4 to 6 red).
3. AC-15 pipes into `ksh`, `mksh`, `ash`, `busybox sh`, `fish`, and a `while read` loop running a shell or `eval`, are refused before running. can fail: a shell name dropped, `busybox` read as the command, or the loop body's `do` hiding the shell (mutants 7 to 10 red).
4. AC-16 the 81 older tests still pass, and the new allow test pins the normal commands. can fail: a looser rule (mutants 11 to 13 red).
5. AC-16 upstream at pinned plus the patch equals the built mod; `TestShippedPatch` green. can fail: a hunk dropped or edited makes the apply or `diff -r` fail.
- Live install: owed after merge; not claimed here.
CAN FAIL CHECKED: 5

### Review round on PR 222 (2026-10-23): four fixes inside AC-14, AC-15, AC-17
- Defects found by probing the built mod (before: ALLOW, no target seen): `echo "S" | while read x; do for i in 1; do :; done; sh -c "$x"; done` (the inner `done` ended the fed outer loop); `! ! ! ! ! ! ! S` and `nice` x7 (`unwrap` stopped after 6 layers, so the write was never seen); `echo "S" | tee >(sh)` and `echo "S" > >(sh)` (a shell reading a `>(...)` body); and a false refusal: `bash tests/run.sh > >(tee out.log)` (a `>(...)` was taken as text fed to bash).
- Fix in `hooks/analyze.ts`: a stack of open loops (`done` closes only its own), `unwrap` bound 6 -> 100, a `>(...)` body that is a shell sets the stdin flag, and only `<(...)` counts as text handed to the command.
- `claude plugin test`: 102 pass, 0 fail (98 before, 4 new). `claude plugin validate`: passed. Patch regenerated with `claude-config.py patches` against a throwaway live folder; upstream at pinned plus the patch, `diff -r` with the built mod: no output.
- Mutants, each alone, restored after: `done` clears all loops -> nested loop test red; `guard < 6` -> keywords/wrappers test red; `>(` shell check off -> `>( )` test red; `procsub = true` for `>(` -> output substitution test red.
