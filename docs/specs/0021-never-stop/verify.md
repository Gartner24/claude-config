# Verify: ask, never stop · spec 0021

Run 2026-10-13 on `feat/release-4` (dee3519). Each step runs the real `wf run` (`runner/wf.py`) on scratch repos in a temp HOME, with the scripted claude, fake ntfy and fake bwrap from `runner/tests/test_run.py`. A real claude call is not part of this check. To rerun all of them:
`python3 -B docs/specs/0021-never-stop/probes/drive.py Drive.test_a_ac1_table Drive.test_b_ac2_ac3_ac6_blocked Drive.test_c_f1_always Drive.test_d_cli_allow_writes Drive.test_e_ac4_main Drive.test_f_ac5_guard Drive.test_g_ac8_names Drive.test_h_ac10_prune Drive2.test_i_f1_never Drive2.test_j_u6_crash_loop Drive2.test_k_u10_boom Drive2.test_l_ac9_include Drive2.test_m_ac9_hookspath`
The probe only prints. You read the output and judge it against the expected result below.

## Commands
- [x] `test_a_ac1_table` -> `missing: []`, and every reason in PARKS, REPO_STOPS, RUN_STOPS listed with its row and options -> AC-1
  can fail: a reason added to `PARKS` with no `CASES` entry shows up under `missing`.
- [x] `test_b_ac2_ac3_ac6_blocked` (run 1) -> `parked: 1. A: blocked`, `waiting: <id> ...` with `1 done, go on` and `2 skip`, then `done: 2. B` in the same run; the ping carries the same question; report.txt has `question <id>: 1. A: ... (recommended: done, go on)` -> AC-2, AC-6
  can fail: a park that still ends the feature silently prints no `waiting:` line and no `question` line in the report, or B never builds.
- [x] `test_b_ac2_ac3_ac6_blocked` (run 2, phone answer `1`) -> `answered: <id> 1. A: done, go on`, calls `/develop a`, `/test a`, `/sync`, the hint is in the rerun's prompt, the queue is empty after -> AC-3
  can fail: an answer that does not resume leaves A parked and the decision in queue.json.
- [x] `test_c_f1_always` -> a write denied under `~/.claude/docs` asks `allow <path> for demo?` with `allow once`, `always`, `skip`; answer `always` writes allow.json mode `0o600` with that one path, and the rerun's sandbox `allowWrite` holds it; the feature ends `done` -> F1, AC-3, AC-7
  can fail: `always` writing AGENTS.md or nothing leaves allow.json `(none)` and the rerun denied again.
- [x] `test_i_f1_never` -> a write denied under `~/.claude/rules` asks only `try again`, `skip`, `allow` is null -> F1, AC-7
  can fail: a never writable check that misses `rules/` offers `allow once` and `always`.
- [x] `test_d_cli_allow_writes` -> with `WF_RUN` set: exit 1 `runs only at your terminal`; `~/.bashrc`: exit 1 `never writable, refused`; a plain path: exit 0 and in allow.json; an AGENTS.md `- allow writes:` line prints `warning: demo: allow writes in AGENTS.md is ignored; it lives in .../allow.json now` -> AC-7
  can fail: a missing `WF_RUN` check exits 0 inside a run and writes allow.json.
- [x] `test_e_ac4_main` -> `branch: feat/a from main`, HEAD `refs/heads/feat/a`, no decisions, both features done -> AC-4
  can fail: the old `branch` refusal stops the repo with `branch` and builds nothing.
- [x] `test_f_ac5_guard` (bare `wf -y`, two repos) -> a call changing `~/.claude/settings.json` gives `stopped repo demo: guard_changed`, and the other repo `stopped repo other: guard_changed ... after the plan`. Each gets a question `accept the new setup and go on` / `stop this repo`. No `stopped: guard_changed` run stop. -> AC-5, U5
  can fail: guard_changed still in the run stop path prints `stopped: guard_changed` and asks nothing.
- [x] `test_j_u6_crash_loop` -> two features denied the same way: `stopped repo two: crash_loop`, a repo question `retry` / `stop this repo`, the run ends `queue done` -> AC-5, U6
  can fail: crash_loop as a run stop prints `stopped: crash_loop` with no question.
- [x] `test_k_u10_boom` -> `stopped repo demo: internal_error: RuntimeError: forced failure`, report line names `traceback.txt` in the run folder -> U10
  can fail: an internal error that ends the whole run or drops the traceback path from the report.
- [x] `test_g_ac8_names` -> with a names list that does not hold `demo`: `next: review and merge: demo`; repo `secretco-site` on the list: `next: review and merge: repo-<hash>` -> AC-8
  can fail: the old scrub prints `repo-<hash>` for demo too.
- [x] `test_l_ac9_include`, `test_m_ac9_hookspath` -> a call that changes the file `~/.gitconfig` includes, `.git/info/attributes`, or a hook under a `core.hooksPath` outside `.git/hooks` stops the repo with `guard_changed` naming that file -> AC-9
  can fail: an unhashed include target lets the call finish `done` with no guard stop.
- [x] `test_h_ac10_prune` -> 60 old dead run folders plus this run: 11 `pruned:` lines, 50 folders left, the oldest 11 gone -> AC-10
  can fail: pruning off or a wrong slice leaves 61 folders.

## Not exercised here
- The scope's Done when names a real claude-config night run. That needs a real claude call and is not a step of this verify.
- U2 run limit, U8 spawn retries, U9 ping retry, R2, R3, F5 to F12 resumes: these are not driven by this probe. `runner/tests/test_never_stop.py` holds their tests, which `/test` checks.

## Acceptance criteria coverage
- AC-1 met · AC-2 met · AC-3 met · AC-4 met · AC-5 met (U5, U6, U10 driven) · AC-6 met · AC-7 met · AC-8 met · AC-9 met · AC-10 met
