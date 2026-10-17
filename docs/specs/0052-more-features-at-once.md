# 0052. Runner runs more than 4 features at once

**Date**: 2026-10-17
**Status**: Proposed
**Paths:** `runner/run.py`, `runner/wf.py`, `runner/pr.py`, `runner/tests/fast.py`, `runner/tests/test_parallel_repo.py`, `runner/tests/test_parallel.py`, `runner/e2e/run.py`, `runner/e2e/stress_git.py`, `AGENTS.md`
**Amends**: [0027](0027-same-repo-parallel/index.md) AC-1 (parallel is any whole number 1 to 8, not 1 to 4) and AC-4 (memory and usage brake); [0043](0043-fast-runner/index.md) AC-2 (the same files wait comes back, from each spec's Paths line)

## What you're agreeing to
- A repo's `parallel` can say any number from 1 to 8; the plan default you set in AGENTS.md becomes 6.
- A new feature starts only while over 4.5 GB of memory is free and the 5 hour use is under 80%; there is no weekly brake.
- Two features whose Paths lines overlap never run together; a feature with no Paths line runs alone, and one that says `Paths: none` runs with anything.
- Each running feature's test suite gets its share of the 20 cores, and short git lock refusals are retried 5 times.
- The build starts with a stress test of 8 worktrees at once and stops if git breaks.

## Summary
Today the runner refuses any `parallel` value above 4, and features that touch the same files run side by side. This spec lifts the cap to 8, adds a live brake (free memory and the 5 hour use) checked before each start, and brings back the rule that features sharing files wait for each other. It also splits the CPU between test suites and retries short git lock errors, so more features at once do not slow or break each other.

## Context
The 4 is validation only (`runner/run.py:236`, hint `:241`); nothing else caps the children (`--jobs` defaults to unlimited, `run.py:5869`). The scheduler (`parallel()`, `run.py:5835`, loop `:5898-5923`) starts one child at a time and checks only `clashes()` (`run.py:5616-5623`, app port and git common dir) and the per repo `limit` (`:5903`). Nothing reads free memory or usage before a start; each child sleeps on its own usage limit (`run.py:3735-3742`).

Spec 0043 AC-2 removed the Paths wait. `pr.globs()` (`pr.py:2051`) still reads each spec's Paths line into the job row (`run.py:5659`), and `pr.overlap()` (`pr.py:2068`) still exists but only tests call it. The research for plan item B2 (`docs/research/tool-review-2026-10/68-runner-n-parallel.md`) puts the real limits at the shared usage pool, memory (ram-watch kills helpers under 3 GB free), and CPU: the claude-config fast suite uses `os.cpu_count()` threads (`runner/tests/fast.py:46`), 20 here, so 6 suites at once oversubscribe the machine.

## Requirements

**User stories**:
- As the owner, I want the runner to build up to 8 features of one repo at once when the machine and the usage pool allow, so a night's queue finishes sooner.
- As the owner, I want features that edit the same files kept apart, so parallel work does not end in merge conflicts.

**Acceptance criteria**:
- **AC-1** (any number): the `parallel` value set in `ANSWER_KEYS` (`run.py:236`) is built from `range(1, MAX_PARALLEL + 1)` with `MAX_PARALLEL = 8`, so only the ASCII strings `1` to `8` pass; anything else gets the existing refusal (`run.py:4022-4025`). The hint (`run.py:241`) and AGENTS.md:68 say 1 to 8; claude-config's AGENTS.md:82 says `- parallel: 6`.
- **AC-2** (memory brake): before each child start, `parallel()` reads `MemAvailable` (on purpose, not `MemFree`) from `/proc/meminfo` (path injectable for tests). Under 4.5 GB (`MIN_FREE_GB = 4.5`), no child starts. Reads are optimistic: a just started child has not grown yet; starts stay one at a time (`run.py:5895`), and that is accepted.
- **AC-3** (usage brake): before each child start, `parallel()` calls `usage.read()` (`usage.py:105`, cached 60 s). A dict result gives `five_hour` used percent; at 80 or above (`MAX_FIVE_HOUR = 80`) no child starts. A tuple result (a failed read) is unknown, does not brake, and prints `usage unknown, not braking` once per run. Old samples in `usage.jsonl` are never used. There is no weekly brake.
- **AC-4** (brake loop): the read loop waits with `lines.get(timeout=POLL)` (`run.py:5924`, `POLL` `run.py:445`) and checks the brakes again on each timeout, so a held start is retried every 0.2 s even when no child is running. A brake waits with no time cap; it prints `waits: memory <x.x> GB free, needs 4.5` or `waits: 5 hour use <n>%, needs under 80` when the reason or its value changes, with the minutes waited so far, and Ctrl C (`r.interrupted`) still ends the run.
- **AC-5** (same files wait): in the pick (`run.py:5901`), after `clashes()`, two rows are tested with `pr.overlap()` only when both are worktree rows of the same repo (same `key`, both with `tree`); rows of other repos are never tested. Overlapping rows never run at once (0027 AC-5 rules and exclusions). A spec with no Paths line overlaps every feature and runs alone; `**Paths:** none` means it touches no code and overlaps nothing. A held feature prints `waits: <feature>: shares <glob> with <other>` once (the last printed line per row is kept on the row) and starts when the other's child exits. The drift note (0043 AC-2) stays and never stops a feature.
- **AC-6** (cores split): each child gets `WF_CORES=<k>`, `k = max(2, (os.cpu_count() or 4) // n)`, `n` = children running across all repos including the new one, fixed at the child's start (earlier children keep their larger share). The child passes it on to the suite process. claude-config's `runner/tests/fast.py:46` uses `WF_CORES` when set, else `os.cpu_count() or 4`.
- **AC-7** (git retry): `wf.git()` (`wf.py:266`) retries only when stderr matches `Unable to create '.*\.lock'` (git refused before changing anything), up to 5 times, 0.2 s apart, then fails as today. Other errors, including `cannot lock ref`, are not retried. Direct git calls outside `wf.git()` (`run.py:5668`, `:5682`) are out of scope.
- **AC-8** (stress test): `runner/e2e/stress_git.py` clones a scratch repo to a temp folder, starts 8 processes at once, each doing a `git worktree add` on its own branch and 50 commits through `wf.git()`, then runs `git fsck --full` and counts commits with `git rev-list --all --count`. It exits 0 only on a clean fsck and all 400 new commits present. It runs as build step 1 (stop the build on a failure) and again after the retry lands.

## Options considered
### Option 1: Ceiling plus live brake (chosen)
A higher fixed ceiling, with memory and usage checked before each start.
**Pros**: uses the machine when it is idle, backs off when it is not; small change in one loop.
**Cons**: thresholds are estimates until measured.

### Option 2: Fixed higher number only
Raise the tuple to 8 and nothing else.
**Pros**: one line.
**Cons**: ram-watch already kills helpers at the 3 GB floor; the usage pool drains with no brake.

### Option 3: Full clone per feature
**Pros**: no shared git locks.
**Cons**: rewrites the trust and guard model keyed on the git common dir; the research found no lock problem a retry cannot cover.

## Decision
**Chosen option**: Option 1: a ceiling of 8 with a memory and 5 hour usage brake, the Paths wait restored, cores split, and a git lock retry.

## Rationale
Your plan line (B2) fixed the ceiling, the thresholds and the Paths rule; the four choices made on 2026-10-17 settle the rest (no weekly brake, split cores, retry 5 times, stress test first). The brake sits in the existing start loop (`run.py:5898`), which gains a 0.2 s timeout on its read, so no new process or state is added. The Paths wait is cheaper than the conflict questions that grow with n at merge time (spec 0051 AC-6).

## Feature design

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| child start | ceiling | the repo's `parallel` standing answer (AC-1), capped by `--jobs` |
| child start | free memory | `MemAvailable` in `/proc/meminfo` |
| child start | 5 hour use | `usage.read()` (`usage.py:105`), `five_hour` used percent; a tuple result is unknown |
| child start | overlap | `pr.globs()` per job row (`run.py:5659`), `pr.overlap()`; `Paths: none` = no globs that overlap |
| child start | `WF_CORES` | `os.cpu_count() or 4` and children running across all repos |
| wait line | minutes waited | time of the first held check for that reason |
| git call | retry | stderr matching `Unable to create '.*\.lock'` |

**Key invariants**:
- Never more than `parallel` children of one repo, never two overlapping features, never a start under the memory or usage line.
- A brake only delays a start; it never stops or parks a running child.

**Critical test scenarios**:
- `parallel: 8` accepted; `9`, `0`, `08`, ` 5 ` and `x` refused, verifies **AC-1**
- fake meminfo at 4.0 GB: no start and the waits line; at 5.0 GB: start, verifies **AC-2** (the fake exposes every field the code reads)
- fake `usage.read()` returning 85: no start; 50: start; a tuple: start plus the unknown line, verifies **AC-3**
- brake held with no child running, then cleared: the job starts without any child output, and the loop exits; mutation: drop the timeout, the test hangs past its limit and fails, verifies **AC-4**
- 8 jobs: two overlapping, one with no Paths line, one with `Paths: none`, the rest disjoint: the overlapping pair never in `running` together, the no Paths job alone, the `none` job with others; mutation: drop the overlap clause, red, verifies **AC-5**
- 4 running on 20 cores: the new child gets `WF_CORES=5` and the suite process sees it; fast.py with `WF_CORES=3` uses 3 workers, verifies **AC-6**
- a fake git failing twice with `Unable to create '.../index.lock'` then passing: called 3 times, success; `cannot lock ref`: called once, verifies **AC-7**

## Build plan
1. Write and run `runner/e2e/stress_git.py` at n=8; stop the build if it fails, satisfies **AC-8**
2. Git lock retry in `wf.git()`, then run the stress test again, satisfies **AC-7**, **AC-8**
3. `parallel` 1 to 8, hint, AGENTS.md lines (`1 to 8`, `parallel: 6`), satisfies **AC-1**
4. Read loop timeout, memory and usage brake with wait lines, satisfies **AC-2**, **AC-3**, **AC-4**
5. Same repo overlap clause in the pick, `Paths: none` handling, restore the e2e `--same-repo` "C waits for A" assert with Paths lines in its fixture specs, satisfies **AC-5**
6. `WF_CORES` in the child and suite environment and in `fast.py`, satisfies **AC-6**
7. `--jobs` help text says it caps all children (`wf.py:658`) (the Amended by lines and architecture invariant 6 were updated with this spec), satisfies **AC-1**, **AC-5**

## Consequences
**Positive**:
- A full queue builds up to twice as fast when memory and usage allow.
- Fewer merge conflicts than today, because sharing features wait.

**Negative / tradeoffs**:
- The usage pool drains up to 8 times faster than one feature; the 80% brake only stops new starts.
- A spec with no Paths line runs alone, so badly tagged specs slow the queue.
- In claude-config most runner specs name `runner/run.py`, so they still run one after another; the gain is mostly for specs on other files.
- `WF_CORES` is honored only by suites that read it (claude-config's fast suite); other repos' suites still use every core.

**Neutral**:
- The merge lock (spec 0051) still lands one PR at a time, so finished features queue there.

## Follow-up
- [ ] After a few runs at 6, check run.json memory and timing; raise the ceiling past 8 only with that data.
