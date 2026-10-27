# 0082. Mac support: claude-config on macOS and Linux

**Date**: 2026-10-27
**Status**: Proposed
**Paths:** `tools/bin/install.sh`, `tools/bin/sync.sh`, `tools/bin/docs-pr.sh`, `tools/bin/move-home-chat.sh`, `tools/bin/claude-config.py`, `tools/scripts/start-gates.py`, `tools/scripts/review-isolated.py`, `tools/scripts/ref-check.py`, `tools/scripts/skills-audit.sh`, `claude-home/hooks/**`, `claude-home/scripts/claude-ram-watch.sh`, `claude-home/settings.json`, `claude-home/skills/assets/scripts/gemini-key.sh`, `claude-home/skills/design/scripts/test-ledger.sh`, `claude-home/mods/wf-handoff/**`, `.github/workflows/**`, `tests/**`

## What you're agreeing to
- Every script, hook and test in claude-config is rewritten where needed so it runs on a stock Mac with Homebrew Python, as well as on Linux. No GNU tools or newer bash are required on the Mac.
- Features that only make sense on Linux (the RAM watcher) skip themselves on a Mac; the ones with a Mac equivalent (the notification sound, the key store) use it.
- A GitHub Actions job runs the suite and a real install (into temporary folders) on a Mac and on Linux for every PR, free for this public repo. It comes first as advisory, so each fix PR shows its Mac result, and becomes a required check (a red Mac run blocks a merge) once everything is green, on your yes.
- Hooks and skills that come from other projects (jjstack, gstack, plugins) are not changed here.

## Summary
Your partner uses a Mac, and about 30 places in claude-config assume Linux: GNU flags, bash 4 syntax, `/proc`, Linux only programs and `/home` paths. This spec makes each one portable, and adds a CI job on a real Mac so it stays that way.

## Requirements

**User stories**:
- As a person on a Mac, I want install and every hook to work with only Homebrew Python, so that I get the same setup as on Linux.
- As the owner, I want a change that breaks the Mac to fail its PR, so that I never break my partner's setup unseen.

**Acceptance criteria**:

### PR A (0082a): CI first, then portable shell
- **AC-0** `.github/workflows/portable.yml` (the AC-12 job) lands first in this PR as an advisory check: it runs, shows red or green, and is not required. Red Mac runs on PR A, B1 and B2 are expected until the last fix lands; each PR body names which Mac failures it removes.
- **AC-1** No bash 4 syntax in live shell code: `install.sh` `${name^^}` (line ~359) uses `tr`; `skills-audit.sh` `declare -A` becomes a `case` function.
- **AC-2** No GNU only flags in live shell code: `find -printf` (`install.sh`, `sync.sh`) becomes `find` piped to `sed 's|^\./||'`; `readlink -f` (`install.sh`) and `realpath` (`docs-pr.sh`) become one shared `python3 -c` realpath call or `cd` plus `pwd -P`; `flock` (`move-home-chat.sh`) becomes a `mkdir` lock, and is dropped from its tool check; `timeout` (`block-destructive.sh`, `workflow-start.sh`, `handover-start.sh`) runs through `timeout`, else `gtimeout`, else the command alone; `touch -d @epoch` (`test-ledger.sh:47`) and `touch -d '2 days ago'` (`handover-start.sh:60`, `test-ledger.sh:130`) become `python3` `os.utime`; the `timeout` fallback keeps passing standard input to the command (`block-destructive.sh:447` pipes into it). `test_move_home_chat.py` (its lock test at line ~171) is rewritten for the `mkdir` lock. File names with a newline stay unsupported, as today.
- **AC-3** A test (`tests/test_portable.py`) greps every live shell and Python file under `tools/`, `claude-home/hooks/`, `claude-home/scripts/` and `claude-home/skills/*/scripts/` (not `tests/`) for the constructs in AC-1 and AC-2 plus `sed -i` without a suffix, `date -d`, `touch -d`, `stat -c`, `grep -P`, `xargs -r`, `base64 -w`, `/proc/`, `sched_getaffinity` and `/home/santiago`, on non comment lines, by regular expression. Known test data (the `--test` blocks of `block-destructive.sh`, `test-ledger.sh` and similar) is excused through an allowlist file `tests/portable-allow.txt` (path, pattern, reason per line), the way `tests/test_tools_folder.py` keeps its allowlist; it prints each hit and the count, and the count must be 0.
- **AC-3b** Tests and checks that list repo files are updated in the same PR as each new file (`tests/test_tools_folder.py`, `tests/test_map.py`, the `map/` cards). Tests that compare temporary paths resolve them first (on a Mac `/var` is a link to `/private/var`).

### PR B1 (0082b1): memory, processes, Python version
(PR B is split in two to stay under about 400 lines.)
- **AC-4** `claude-ram-watch.sh` exits 0 at its start on Darwin, and uses `$HOME`, not `/home/santiago`, for its log and unit folder.
- **AC-5** `start-gates.py` reads memory on Darwin from `sysctl hw.memsize` (total) and `vm_stat`: the page size from its first line (`page size of N bytes`), and available = (`Pages free` + `Pages inactive` + `Pages speculative`) times the page size; on Linux from `/proc/meminfo` as today; thresholds unchanged. The CPU count comes from `os.cpu_count()` when `os.sched_getaffinity` is missing. Its self check covers both readers with fixture text (a Linux `meminfo` and an Apple silicon `vm_stat` with 16384 byte pages).
- **AC-6** `review-isolated.py` uses `tempfile.gettempdir()` resolved with `realpath` for its temp root, adds `/Users` and `/private` to its root deny list on Darwin, and checks a process with `ps -o stat= -p` instead of `/proc/<pid>/stat`.
- **AC-11** (moved here) `install.sh` checks `python3` is 3.10 or newer before anything else and, when not, exits 1 with `python3 3.10+ needed (on a Mac: brew install python)`.

### PR B2 (0082b2): mod, sound, key store, home paths
- **AC-7** The wf-handoff mod's `register.ts` reads a process command line with `ps -o command= -p` instead of `/proc/<pid>/cmdline`; its test mocks that call.
- **AC-8** The `paplay /usr/share/sounds/ocean/stereo/outcome-success.oga` hook command in `settings.json` (line ~501) becomes `bash ~/.claude/hooks/notify-sound.sh` (install's home rewrite still applies), a new copied hook that plays `afplay /System/Library/Sounds/Glass.aiff` on Darwin and that same `paplay` file on Linux, and exits 0 when neither exists.
- **AC-9** `gemini-key.sh` stores and reads the key with `security add-generic-password` / `security find-generic-password -w` on Darwin and `secret-tool` on Linux; the `pgrep -x gnome-keyring-d` check runs only on Linux.
- **AC-10** `claude-config.py` (`AUTHOR_HOME`, line 49) and `install.sh`'s `sed "s|/home/santiago|$HOME|g"` rewrite (lines ~220-241) take the home prefix from the repo's `settings.json` hook paths or `$HOME`, not the constant; `ref-check.py` matches `/home/<user>` and `/Users/<user>`; tests build home paths from `Path.home()`.

### Proof on a Mac (the job from AC-0)
- **AC-12** `.github/workflows/portable.yml` runs on every pull request, a matrix of `macos-latest` and `ubuntu-latest`, each with `actions/setup-python` at 3.10 and `actions/setup-node` at 18, and `PATH=/bin:/usr/bin` first for the shell steps so the Mac runs its own bash 3.2 (a step prints `bash --version` and fails on the Mac when it is not 3.2). Steps: `python3 tests/fast.py`; the TypeScript mod tests with `node --test`; a real `tools/bin/install.sh` with `HOME` and `CLAUDE_LIVE_DIR` set to temporary folders (so the hook self checks run). No `gh`, `claude`, jjstack or private names list on the runner; tests that need them stub or skip as today. Both jobs green on PR B2.
- **AC-13** After PR B2 is green on both systems, the job becomes a required status check on `main`. That is a repo settings change, done only on your yes. · waits on you

## Decision

**Chosen option**: Portable code plus a Mac CI job (your answers 2026-10-27).

Every Linux only construct is rewritten to work on both systems, true Linux only features get a per OS branch or skip, and a GitHub Actions matrix proves it on every PR.

## Feature design

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| OS branch | which system | `uname -s` in shell, `sys.platform` in Python, `process.platform` in TypeScript |
| install | home prefix to rewrite | the repo `settings.json` hook paths, else `$HOME` (AC-10) |
| start-gates | free memory on Mac | `sysctl hw.memsize` and `vm_stat` |
| notify-sound | sound file | `/System/Library/Sounds/Glass.aiff` on Darwin; today's Linux file |
| CI | Python version | the runner's default `python3` (3.10 or newer on both images) |

**Key invariants**: hooks still fail open (invariant 5) on both systems; no behavior changes on Linux except the code paths named here.

**Critical test scenarios**:
- The AC-3 grep finds 0 hits, verifies **AC-1**, **AC-2**, **AC-3**.
- `start-gates --test` passes with both the Linux and the Mac memory fixtures, verifies **AC-5**.
- The CI matrix is green on both systems, verifies **AC-12**.

## Build plan
Skateboard: each PR is usable alone; the CI job comes first as advisory (your answer), so each PR shows its Mac result.

1. PR A: the advisory workflow, AC-1, AC-2 edits, the AC-3 test and allowlist, satisfies **AC-0** to **AC-3b**, **AC-12**.
2. PR B1: RAM watcher, start-gates, review-isolated, Python check, satisfies **AC-4**, **AC-5**, **AC-6**, **AC-11**.
3. PR B2: mod, sound, key store, home paths; both jobs green, satisfies **AC-7** to **AC-10**, **AC-12**.
4. Make the job required, on your yes, satisfies **AC-13**.

## Consequences
**Positive**: your partner installs with only Homebrew Python; a Mac regression fails its PR.

**Negative / tradeoffs**:
- The first CI in this repo: every PR now waits a few minutes for two jobs before the self merge.
- Small per OS branches in several scripts to keep in mind when editing them.

**Neutral**: hooks from jjstack, gstack and plugins (`error-detector.sh`, `permission-floor.py` and others) are not checked here.

## Follow-up
- [ ] Check the framework hooks (jjstack, gstack) on the Mac once your partner installs; report problems upstream.

## Rationale
Options: portable code, or requiring Homebrew GNU tools and bash 5 on the Mac. Portable code won because hooks run on every tool call and must not depend on PATH order, and most fixes are one line. Proof: a CI job on every PR, or your partner running it once. CI won because hooks change often, and a one time check would not catch a later break. A Sonnet cross check found 11 gaps (bash 3.2 hidden by the runner's newer bash, a dry run that skips the hook self checks, missed `touch -d`, PR size and others); you applied all fixes and chose CI first as advisory. Inventory: a read only scan on 2026-10-27 listed 2 bash 4 uses, 10 GNU only flag uses, 9 Linux only program or `/proc` sites and 8 hardcoded home or `/tmp` sites; each is named in an AC above.
