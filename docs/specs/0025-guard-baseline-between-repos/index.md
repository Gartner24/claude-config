# 0025 · Guard baseline between repos

**Date**: 2026-10-13
**Status**: Accepted (built f08c6a2)
**Paths:** `runner/run.py`, `runner/wf.py`, `runner/tests/test_parallel.py`
**Amends**: [0017](../0017-several-repos-at-once/index.md) AC-7 and its accepted gap (Consequences: "Each child takes its guard baseline at its own start..."), closed here.

## What you're agreeing to
- When `wf` builds in several repos, a repo that starts later first checks that its protected files (hooks, settings, git config) are still what they were when you confirmed the plan.
- If something changed them in between (usually another repo's run), that repo does not build yet: you get one phone question naming the file, "accept the new setup and go on" (recommended) or "stop this repo".
- Every other repo keeps building meanwhile. Your answer starts that repo the same night, or on the next `wf`.
- Changes `wf` made itself (its setup swap) never ask.

## Acceptance criteria
- **AC-1** (plan baseline handed over): the plan of bare `wf` and bare `wf run` already freezes each repo's guard before the confirm (`bare_checks` run.py:809-838 calls `repo_checks`, which ends in `freeze_guard`, run.py:869; `cmd_wf` runs it before its prompt, finish.py:951). `run.parallel` (run.py:3684), right before it starts a repo's child (run.py:3739), writes that repo's plan baseline `{"guarded_files", "absent_denied", "answers"}` (the plan's guard record and standing answers) to `<state>/baselines/<parent pid>-<sha1 of the repo real path>.json` (folder 0700, file 0600), and passes it to the child with a hidden flag `--plan-guard <path>` (wf.py, `argparse.SUPPRESS` like `--only-feature`, wf.py:655). The parent deletes its baseline files when it ends, however it ends (Ctrl C included). `wf run <repo>` without the flag behaves exactly as today.
- **AC-2** (the check): the child, in `run()` right after its run folder is made and saved (run.py:2748-2765) and before its first pick, reads the plan baseline and lists every path that `moved()` (run.py:3249) reports against it, leaving out each path a `swaps.jsonl` line accepts (`accepted_by`, run.py:548). It also compares the plan's standing answers with `read_answers` now. An unreadable or missing baseline file counts as one change with detail `plan baseline unreadable: <path>`.
- **AC-3** (a change asks, the rest goes on): with one or more changes, the child calls `end_repo("guard_changed", <detail>)` (run.py:1654), detail `<first path> changed after the plan, before this repo started` plus ` (and <n> more)` when several, or `standing answers changed after the plan`. That is spec 0021 U5: one repo level question with `accept the new setup and go on` first and `stop this repo`, pinged to your phone, no call made in this repo meanwhile (`pick` skips a repo whose repo level question is unanswered, run.py:1604-1608). Other repos are separate children and never wait on it.
- **AC-4** (the answer resumes): the child waits for the reply like any repo question (`end_wait`, run.py:2338-2340, up to `--max-wait`). `accept the new setup and go on` takes the files on disk as the new baseline (`repo_answer`, run.py:1684-1692) and the repo builds; `stop this repo` ends it for this run. Unanswered at the end of the wait, the question stays in `queue.json`, the morning report lists it (spec 0021 AC-6), and the next `wf` starts that repo's child, which waits on the same question (a newer change replaces it, `ask` keeps one per repo, run.py:1341).
- **AC-5** (no question when nothing changed): a repo whose protected files match the plan, or moved only by a ledger accepted swap, starts exactly as today with no question and no extra output line.
- **AC-6** (tests, fake claude, temp state and live dir): with `--jobs 1`, repo A's fake call rewrites a hook script both repos' guards hash; repo B then asks `guard_changed` naming that file and makes no call; a reply `1` builds B, a reply `2` ends B with A's result unaffected and the parent summary listing both. The same change written to `swaps.jsonl` by a fake swap asks nothing. A changed `## Standing answers` in B between plan and start asks. `wf run B -y` with no flag asks nothing. The parent's baseline files are gone after a normal end and after SIGINT. Mutation check: drop the AC-2 check and the first test goes red.

## Build plan
1. `--plan-guard` flag in `wf.py`; baseline files written in `run.parallel` before each child and removed at its end, satisfies **AC-1**
2. The check in `run()` and the `end_repo` call, satisfies **AC-2**, **AC-3**, **AC-5**
3. Tests per AC-6 in `runner/tests/test_parallel.py`, satisfies **AC-4**, **AC-6**

## Probes
None: the design rests only on the runner's own code (no outside tool behavior).

## Follow-up
- [ ] `/sync`: architecture page invariant 6 (a later child checks its guard against the plan before it starts) and spec 0017's accepted gap line marked closed by this spec.
