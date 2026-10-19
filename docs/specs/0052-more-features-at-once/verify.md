# Verify: runner runs more than 4 features at once · spec 0052

Run 2026-10-18 by `/check verify` under `wf run`. Scratch scripts: `/tmp/claude/v0052/probe.py` (calls the real
`run`, `wf`, `pr` modules) and `/tmp/claude/v0052/mutate.py` (breaks one behavior, runs its check, restores).

## Commands
- [x] `python3 runner/e2e/stress_git.py` -> `PASS: 8 worktrees, 400 commits, fsck clean` -> AC-8
  - can fail: a lost commit under 8 writers. Mutant: `wf.git` silently skips worker 3's last commit -> `FAIL: 399 new commits, expected 400`.
- [x] `read_answers` on `- parallel: <v>` -> 1, 6, 8 accepted; 9, 0, 08, x, 4.0 refused with `AGENTS.md:3: <v> is not allowed for parallel` -> AC-1
  - can fail: the old cap. Mutant `MAX_PARALLEL = 4` -> 8 refused.
- [ ] `AGENTS.md` Standing answers says `- parallel: 6` -> AC-1. Deferred by your answer (2026-10-18): stays `- parallel: 4` until this spec merges and `bin/install.sh` runs, because the installed old runner refuses anything above 4.
- [x] `run.free_gb()` on the real `/proc/meminfo` -> 14.06 GB, matching `MemAvailable: 14740088 kB` while `MemFree` is 1.1 GB -> AC-2
  - can fail: reading MemFree. Mutant `MemFree:` -> `TestBrakes.test_brake` red.
- [x] `usage.read()` in this sandbox returns a tuple (no login) -> `brake()` returns None twice and prints `usage unknown, not braking` once -> AC-3
- [x] `TestBrakeRun.test_usage` (a real `wf -y` process, usage cache at 85 then 50) -> held with no call, `waits: 5 hour use 85%, needs under 80, 0 min so far`, then all three build -> AC-3, AC-4
  - can fail: a wrong line. Mutant `MAX_FIVE_HOUR = 90` -> red.
- [x] `TestBrakeRun.test_memory` (real `wf -y`, fake meminfo 4.0 then 5.0 GB) -> held with no child, one waits line, starts after the clear -> AC-2, AC-4
  - can fail: no retry while nothing runs. Mutant `lines.get()` without timeout -> red.
- [x] `TestPick` and `TestSameRepo.test_three_features` -> overlapping pair never together, no Paths alone, `Paths: none` with others, `waits: 3. C: shares a.txt with 1. A` once, C starts after A ends -> AC-5
  - can fail: the overlap clause dropped. Mutant `and True` in `pick()` -> red.
- [x] `TestBrakeRun.test_memory` WF_CORES -> first child `20`, second `10` on 20 cores; `WF_CORES=3` -> `fast.workers()` 3 -> AC-6
  - can fail: the env var not passed. Mutant renames it -> red.
- [x] Real git lock: `.git/index.lock` held 0.5 s -> `wf.git(add)` exit 0 after 0.61 s; a lock never released -> 128 after 1.01 s; a non lock error -> no wait -> AC-7
  - can fail: no retry. Mutant `GIT_LOCK_TRIES = 0` -> held lock gives 128.
- [x] `python3 -B -m unittest discover -s runner/tests -p "test_parallel*.py"` -> 43 tests OK
- [ ] `python3 runner/e2e/run.py --same-repo` (real claude, C waits for A) -> AC-5. Not run: needs a logged in `claude`, which this sandbox lacks; run it yourself with `!`.

## Acceptance-criteria coverage
- AC-1 code met, AGENTS.md line deferred to after merge (your answer) · AC-2 met · AC-3 met · AC-4 met · AC-5 met (real claude e2e not run) · AC-6 met · AC-7 met · AC-8 met
