# 0052. Runner runs more than 4 features at once

**Date**: 2026-10-17
**Status**: Proposed
**Paths:** `runner/run.py`, `runner/wf.py`, `runner/pr.py`, `runner/tests/fast.py`, `runner/tests/test_parallel_repo.py`, `runner/tests/test_parallel.py`, `runner/e2e/run.py`, `AGENTS.md`
**Amends**: [0027](0027-same-repo-parallel/index.md) AC-1 (parallel is any whole number 1 to 8, not 1 to 4) and AC-4 (memory and usage brake); [0043](0043-fast-runner/index.md) AC-2 (the same files wait comes back, from each spec's Paths line)

## What you're agreeing to
- A repo's `parallel` can say any number from 1 to 8; the plan default you set in AGENTS.md becomes 6.
- A new feature starts only while over 4.5 GB of memory is free and the 5 hour use is under 80%; there is no weekly brake.
- Two features whose Paths lines overlap never run together, and a feature with no Paths line runs alone.
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
- **AC-1** (any number): `ANSWER_KEYS` accepts `parallel` as a whole number 1 to 8 (`MAX_PARALLEL = 8`, one constant); 0, 9, and non integers are refused with `parallel is a whole number 1 to 8`. The hint text and the AGENTS.md standing answers line say 1 to 8. claude-config's AGENTS.md says `- parallel: 6`.
- **AC-2** (memory brake): before each child start, `parallel()` reads `MemAvailable` from `/proc/meminfo`. Under 4.5 GB (`MIN_FREE_GB = 4.5`), no child starts; the plan line `waits: memory <x.x> GB free, needs 4.5` is printed once per change, and the check repeats on the loop's next poll.
- **AC-3** (usage brake): before each child start, `parallel()` reads the newest `five_hour` percent from the usage state (`runner/usage.py`). At 80 or above (`MAX_FIVE_HOUR = 80`), no child starts; plan line `waits: 5 hour use <n>%, needs under 80`. A missing or unreadable sample does not block (the existing per child usage limit sleep still applies) and prints `usage unknown, not braking` once. There is no weekly brake.
- **AC-4** (same files wait): two worktree features of one repo are never running at once when `pr.overlap()` says their globs overlap (rules of 0027 AC-5, its exclusions kept). A feature with no Paths line or no globs overlaps every feature, so it runs alone. A held feature prints `waits: <feature>: shares <glob> with <other>` and starts when the other's child exits. The drift note after each call (0043 AC-2) stays as a net and still never stops a feature.
- **AC-5** (cores split): each child gets `WF_CORES=<k>` in its environment, `k = max(2, cpu_count // running)` where `running` counts children including the new one, fixed at the child's start. claude-config's `runner/tests/fast.py` uses `WF_CORES` when set, else `os.cpu_count()`.
- **AC-6** (git retry): `wf.git()` retries a command whose stderr matches a git lock error (`Unable to create '...\.lock'` or `cannot lock ref`) up to 5 times, 0.2 seconds apart, then fails as today with the last error. Other failures are not retried.
- **AC-7** (stress test first): a probe `docs/specs/0052-probes/stress.py` makes 8 worktrees of a scratch clone, makes 50 commits in each at once through `wf.git()`, then runs `git fsck --full`; it exits 0 only on a clean fsck and 400 commits present. The build runs it first and stops on a failure.

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
Your plan line (B2) fixed the ceiling, the thresholds and the Paths rule; the four choices made on 2026-10-17 settle the rest (no weekly brake, split cores, retry 5 times, stress test first). The brake sits in the one loop that already polls (`run.py:5898`), so no new process or state is added. The Paths wait is cheaper than the conflict questions that grow with n at merge time (spec 0051 AC-6).

## Feature design

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| child start | ceiling | the repo's `parallel` standing answer (AC-1), capped by `--jobs` |
| child start | free memory | `MemAvailable` in `/proc/meminfo` |
| child start | 5 hour use | newest sample in the usage state read by `runner/usage.py` |
| child start | overlap | `pr.globs()` per job row (`run.py:5659`), `pr.overlap()` |
| child start | `WF_CORES` | `os.cpu_count()` and the running count |
| git call | retry | stderr text of the failed git command |

**Key invariants**:
- Never more than `parallel` children of one repo, never two overlapping features, never a start under the memory or usage line.
- A brake only delays a start; it never stops or parks a running child.

**Critical test scenarios**:
- `parallel: 8` accepted, 9 and 0 and `x` refused, verifies **AC-1**
- fake `/proc/meminfo` at 4.0 GB: no start and the waits line; at 5.0 GB: start, verifies **AC-2** (the fake exposes every field the code reads)
- fake usage sample at 85: no start; at 50: start; missing file: start plus the unknown line, verifies **AC-3**
- 8 jobs, two with overlapping globs and one with none: the overlapping pair never in `running` together, the no Paths job alone, the disjoint ones together; mutation: drop the overlap clause, the test goes red, verifies **AC-4**
- 4 running on 20 cores: the new child gets `WF_CORES=5`; fast.py with `WF_CORES=3` uses 3 workers, verifies **AC-5**
- a fake git that fails twice with a lock error then passes: called 3 times, success; a non lock failure: called once, verifies **AC-6**

## Build plan
1. Write and run the stress probe at n=8; stop the build if it fails, satisfies **AC-7**
2. Git lock retry in `wf.git()`, satisfies **AC-6**
3. `parallel` 1 to 8, hint, AGENTS.md lines (`1 to 8`, `parallel: 6`), satisfies **AC-1**
4. Memory and usage brake in the `parallel()` start loop with plan lines, satisfies **AC-2**, **AC-3**
5. Paths overlap clause in the pick at `run.py:5901`, restore the e2e `--same-repo` "C waits for A" assert, satisfies **AC-4**
6. `WF_CORES` in the child environment and in `fast.py`, satisfies **AC-5**
7. Amended by lines on 0027 and 0043, architecture invariant 6 if it names 4, satisfies **AC-1**, **AC-4**

## Consequences
**Positive**:
- A full queue builds up to twice as fast when memory and usage allow.
- Fewer merge conflicts than today, because sharing features wait.

**Negative / tradeoffs**:
- The usage pool drains up to 8 times faster than one feature; the 80% brake only stops new starts.
- A spec with no Paths line runs alone, so badly tagged specs slow the queue.
- `WF_CORES` is honored only by suites that read it (claude-config's fast suite); other repos' suites still use every core.

**Neutral**:
- The merge lock (spec 0051) still lands one PR at a time, so finished features queue there.

## Follow-up
- [ ] After a few runs at 6, check run.json memory and timing; raise the ceiling past 8 only with that data.
