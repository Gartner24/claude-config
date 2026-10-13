# Verify: several repos at once · spec 0017 · updated 2026-10-13
_Steps derived from spec 0017 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [x] `python3 -m unittest discover -s runner/tests` -> OK, including `test_parallel.py` -> AC-1 to AC-7
- [x] `python3 -m unittest runner/tests/test_parallel.py -k test_two_repos` -> plan ends with `jobs: 2 at once`, the first `[rb]` line comes after `[ra] run folder:`, the two first calls overlap, every child line is prefixed, summary has two `exit 0, done: 1. A` lines -> AC-1, AC-4
- [x] `wf run -y --jobs 0`, `--jobs 1.5` -> exit 2; `wf run <repo> -y --jobs 3` -> no `jobs:` line, no prefix, no summary -> AC-2
- [x] `test_one_at_a_time` -> with `--jobs 1` the second child confirms after the first ended -> AC-2
- [x] `test_common_dir_and_nested`, `test_same_port`, `test_clashes` -> a shared git common dir, a nested repo and the same `app url` port each run one after the other; ports default to 80 and 443 by scheme -> AC-3
- [x] `test_streaming` -> `[ra] run folder:` arrives while the child still runs -> AC-4
- [x] `test_skip_and_names` -> `onmain: skipped: branch: ...`, `[x/same]` and `[y/same]` prefixes, exit 0 -> AC-4, AC-6
- [x] `test_sigint_reaches_both` -> both fake calls record one INT, both children `exit 130, stopped: interrupted`, parent 130 -> AC-5, AC-6
- [x] `test_not_started` -> SIGTERM with `--jobs 1` leaves `rb: not started`, parent 130 -> AC-5
- [x] `test_locked_child` -> lock taken after the parent let it go: `[rb] refused: locked: ...`, `rb: exit 5, - | run folder: -`, parent 6 -> AC-1, AC-6
- [x] `test_open_only`, `test_each_resumes_own` -> an unanswered decision alone starts a child that re-pings it; two children each resume their own answer -> AC-1, AC-7
- [x] `test_repo_stop`, `test_guard_scope` -> a repo stop or guard change ends only that child; `~/.claude` settings stop each child -> AC-6, AC-7
- [ ] `python3 runner/e2e/run.py --parallel` with `!` (real claude) -> `PASS` -> AC-8

## Value sourcing
- [x] repos with work: a repo whose plan shows only `parked:` or `skip:` lines gets no child and `<name>: nothing to run` in the summary (`test_parked_only`); one with only `open:` gets a child (`test_open_only`)
- [x] child started: a child whose start checks are slow delays the next child until its `run folder:` line (`test_two_repos`, slow git)
- [x] git common dir, real path: a linked worktree and a nested repo serialize (`test_common_dir_and_nested`)
- [x] child argv: a child's run.json `caps` equals the parent's `--budget`, `--call-timeout`, `--max-calls`, `--max-hours`, `--max-wait`
- [x] jobs: `jobs: <n>` equals `--jobs`, else the count of repos with work (`test_two_repos`, `test_one_at_a_time`)
- [x] port: `http://localhost` -> 80, `https://...` -> 443, explicit port wins (`test_clashes`)
- [x] repo name: duplicate names get `<parent folder>/<name>` (`test_skip_and_names`)
- [x] summary final line: last `done:`/`parked:`/`stopped:`/`nothing to run` line, else `-`; run folder from the child's `run folder:` line, else `-`
- [x] exit: 130 on a signal or a 130 child, else 6 on any non zero child, else 0

## Acceptance-criteria coverage
- AC-1 test_two_repos, test_open_only, test_parked_only, test_locked_child, test_trust_list · AC-2 test_one_at_a_time, test_bad_values · AC-3 test_common_dir_and_nested, test_same_port, test_clashes · AC-4 test_two_repos, test_streaming, test_skip_and_names · AC-5 test_sigint_reaches_both, test_not_started · AC-6 test_locked_child, test_repo_stop, test_skip_and_names · AC-7 test_each_resumes_own, test_guard_scope, test_repo_stop · AC-8 e2e `--parallel` (yours to run)
