# 0043 · Fast runner

**Date**: 2026-10-14
**Status**: Accepted (built 90c9b20; verify and timing skipped, 2026-10-15)
**Paths:** `runner/run.py`, `runner/pr.py`, `runner/context.py`, `runner/telegram.py`, `runner/tests/fast.py`, `runner/tests/test_fast.py`, `runner/tests/test_shared_plan.py`, `runner/tests/test_combine.py`, `runner/tests/test_explain.py`, `AGENTS.md`
**Amends**: [0027](../0027-same-repo-parallel/index.md) AC-4 and AC-6 (no Paths overlap wait or stop; the open follow up on scope diffs between branches), [0042](../0042-questions-you-can-act-on/index.md) AC-3 (what a Telegram question keeps)

## What you're agreeing to
- claude-config builds up to 4 features at once, each on its own branch in its own copy of the repo, whatever files they touch; nobody waits for another feature because of a shared file.
- When a run ends, the runner combines the finished branches into one new branch with one draft PR. A clash is settled by one Claude call that keeps what each feature needs, then the tests must pass; a clash it cannot settle becomes one question to you.
- There is one plan file: after every step the runner copies that feature's boxes into the real plan, and feature branches carry no plan changes.
- A new command runs the whole test suite in about a minute instead of 15; test and check steps test only the feature's own files while they work, then run it once at the end.
- Telegram questions keep file names and commands, get room for the whole explanation, and lose the plan's tags and filler lines.

## Summary

The runner closed 6 features in 5.3 hours because it did one step at a time, made features that list the same file take turns, and ran a 15 minute suite one file after another. This spec runs every feature at once on its own branch (spec 0027's worktrees, without the same file wait), combines the branches at the end the way you do by hand (a third branch, clashes resolved by keeping what each needs), keeps one plan file, adds a parallel test command, and fixes the Telegram question text.

## Requirements

**User stories**:
- As the owner, I want features to build, check and test at the same time, each on its own branch, so a night's work finishes in hours.
- As the owner, I want the finished branches combined into one branch and one PR, with clashes resolved the way I would.
- As the owner, I want one plan file that always shows every feature's real state.
- As the owner, I want a test step to take minutes, not half an hour, and a Telegram question I can act on from the first read.

**Acceptance criteria**:
- **AC-1** (switches): claude-config's `AGENTS.md` `## Standing answers` say `- parallel: 4`, `- branches: per spec`, `- push: draft PR` and `- suite: python3 runner/tests/fast.py`. A bare `wf` with four or more open features starts 4 of them at once, each in its own worktree.
- **AC-2** (no same file wait): two worktree features of one repo run at the same time even when their `**Paths:**` overlap or a branch changes a file another feature's Paths name. `clashes()` keeps only the app port rule for worktrees, and the drift check no longer stops a feature (it logs a note naming the shared file instead).
- **AC-3** (combine at the end): when a parallel repo's run ends, the runner creates `wf/combined-<YYYYMMDD-HHMM>` from the start branch in its own worktree and merges each open feature branch of that repo (state `local`, `draft`, `ready` or `approved`, not left for you), in the order of their records, with `git merge --no-ff`; fewer than two such branches: no combine. On a conflict it runs one call in that worktree, sandboxed like a build call, given both features' spec top files and the conflicted files, told to keep what each feature needs (one side, the other, or both) and remove every conflict marker. Then it runs the main checkout's `suite` command (never a merged branch's) in the app jail with no network. Green: the merge is committed. Conflict markers left, the call failing, or the suite red: that merge is aborted, the branch is left out, and one question names the branch, the files and the suite output. With `- push: draft PR` the combined branch is pushed and gets one draft PR to the start branch, after the same private names and attribution scans; the per feature draft PRs stay.
- **AC-4** (one shared plan, main is the truth): when a worktree child starts or resumes a feature, the runner copies the main checkout's scope files over the worktree's. After every call it copies that feature's block of the worktree's scope file (its `###` heading line through the line before the next `##` or `###` heading) and its `## At a glance` row (the row whose first cell is the feature number from `### <N>.`) into the main checkout's scope file, replacing the same block and row there. It holds an exclusive lock (`state_dir()/scope-<sha1 of the main checkout path>.lock`) while it reads and writes, writes by temp file and `os.replace`, and changes no other feature's text. A worktree change outside that block and row is not copied; it is logged as a note. In an epic split scope, only the file holding the block and the file holding the table are written. The child reads and ticks its own worktree copy (`mark_box` and `reread` unchanged).
- **AC-5** (branches carry no plan): for a worktree feature branch, the runner's squash commit leaves the scope folder at the branch's `base_sha` (`git restore --source=<base_sha> --staged -- <scope folder>`, the worktree copy keeps its ticks), and before a push of review fix commits one commit puts it back, so `git diff <base_sha> <branch> -- <scope folder>` is empty after every runner commit and every push.
- **AC-6** (the plan is committed): when a worktree child's feature ends (done, parked, or stopped), the runner commits the main checkout's scope files on the start branch with `git commit --only -- <scope files>` as `docs(scope): <feature heading>`, under the AC-4 lock, retrying once. Other uncommitted edits in the main checkout stay as they were. A failed commit is a note and is tried again at the next feature end.
- **AC-7** (fast suite): `python3 runner/tests/fast.py` runs every test the loader finds in `runner/tests/test_*.py` in parallel processes (as many at once as the machine has cores), each with its own temporary `XDG_STATE_HOME` (HOME stays: tests read your git identity and the private names list from it), and exits 0 only when every test passed; on a failure it prints each failing test's output and a count. `fast.py <module>` or `fast.py <module.Class>` runs only that part. A full run on this machine takes under 90 seconds and fails exactly the tests the serial run (`python3 -m unittest discover -s runner/tests`) fails.
- **AC-8** (test and check steps use it): when the standing answers name `- suite: <command>`, the prompt of every `/test` and `/check verify` call adds this sentence: "While you work, run only the test files that cover this feature's changes; each mutation check runs only its own test file. This is in addition to the mutation and can fail rules, never instead of them. At the end of the step run the whole suite once with `<command>`; if it fails, the step fails." Without that answer the prompt is unchanged.
- **AC-9** (Telegram question text): on Telegram (never ntfy) the question and the explanation (`what`) keep file names and commands, through `context.safe(..., paths=True)`; the explanation may run to 1200 characters; the `step:` line drops the plan's tags (`· waits on you`, `· live`, `· later boxes go on`); a `waiting` or `manual_box` question that has an explanation shows no generic learn line and no `why recommended:` line. When the from block would pass its room in Telegram's 4096 characters, the step's own words (`did`) and `why recommended:` are cut first, then the steps, the explanation last. A field whose paths cannot be kept (no readable names list) falls back to the scrubbed text. ntfy messages are unchanged.
- **AC-10** (every question kind seen): before the change merges, one real example of each question kind (a step only you can do, a decision that grants nothing, an authorization question, a PR question) is rendered from the real code with a real explanation call and shown to you in chat, and you say yes to each.
- **AC-11** (a base for draft PRs): `feat/release-4` is on GitHub before the first parallel run, pushed only after the private names scan and the attribution scan of its outgoing commits are clean.
- **AC-12** (the batch runs): after the merge, `wf` runs features 39 to 48 with these settings, and the morning report shows the elapsed time, to compare with the 5.3 hours of 2026-10-14.

## Decision

**Chosen option**: Option 1: spec 0027's worktrees with no same file wait, a combine step at the end, one shared plan, and a parallel test command.

## Feature design

**Data model sketch**: none new. The standing answers gain `suite` (any value, kept as written, like `app start`). A run record gains `combined`: `{branch, merged: [feature], left_out: [{feature, files, why}], pr}`.

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| plan sync | main scope file | `key_of(r.c)` (main checkout) + `r.c.scope_dir`, the file `wf.SCOPE_FILES` finds |
| plan sync | the block, the row | worktree scope file; heading matched as `mark_box` does (`wf.DISPLAY_TAG` stripped); row by the number in `### <N>.` |
| plan sync, plan commit | the lock | `state_dir()/scope-<sha1 of main checkout path>.lock` |
| plan free commits | the base | `rec["base_sha"]` (spec 0026 record) |
| plan commit | the branch, the message | `r.repo["start_branch"]`; `docs(scope): ` + heading |
| combine | the branch name | `wf/combined-` + the run end time `%Y%m%d-%H%M` |
| combine | which branches, in what order | feature records of this run with state `local`, `pushed` or `pr`, by `ended` time |
| combine | the resolve call's input | both features' spec top files (`pr.spec_file`) and `git diff --name-only --diff-filter=U` |
| combine | the check after a resolve | the `suite` standing answer; none: the merge is committed without a suite run and the report says so |
| fast suite | the tests, the workers | the unittest loader over `runner/tests/test_*.py`; `os.cpu_count()` |
| prompt line | the command | the `suite` standing answer, as written |
| Telegram limits | 1200, 4096 | this spec; `telegram.MAX` |

**Key invariants**:
- The main scope file is written only under the lock, and only the running feature's block and row change.
- No feature branch carries a scope folder change after any runner commit.
- A combined branch never holds a conflict marker and never lands a merge whose suite run failed.
- ntfy text keeps scrubbing paths (a public server); only Telegram keeps them.

**Security model**: as spec 0027 and spec 0026. Calls cannot write the main checkout or sibling worktrees; only the runner process writes the main scope file. The resolve call runs with the build call's sandbox inside the combine worktree only. Every push keeps the private names and attribution scans; a refused push stays local.

**Critical test scenarios**:
- Two features with overlapping Paths start together; a branch touching another's Paths logs a note and keeps going (AC-2).
- Two branches editing different lines of one file combine cleanly; two editing the same lines go to the resolve call; a resolve that leaves a marker or a red suite leaves that branch out with a question (AC-3).
- Two children tick a box at the same moment: both ticks land in main, nothing else changed; a child starting after main gained ticks sees them (AC-4).
- A branch whose calls ticked scope boxes has no scope diff after the squash and after a later fix commit (AC-5).
- A feature end commits only the scope files; an unrelated edit in main stays uncommitted (AC-6).
- `fast.py` exits non zero when one test fails and prints it; `fast.py test_explain` runs only that file (AC-7).
- With `- suite: x` the `/test` and `/check verify` prompts carry the sentence; without it they do not (AC-8).
- The 1zim question renders with its file name, the full explanation and no tags on Telegram, under 4096; ntfy still scrubs (AC-9).

## Build plan

1. `runner/tests/fast.py` and its test; time it against the serial run, satisfies **AC-7**
2. The `suite` standing answer and the prompt sentence, satisfies **AC-8**
3. No same file wait: `clashes()` and the drift note, satisfies **AC-2**
4. The shared plan: copy in at start, sync after each call, plan free commits, the plan commit at feature end, satisfies **AC-4**, **AC-5**, **AC-6**
5. The combine step and its draft PR, satisfies **AC-3**
6. The Telegram text fixes, satisfies **AC-9**
7. Render every question kind and show it to you, satisfies **AC-10**
8. Merge `fix/questions-explained` into `feat/release-4`, set the standing answers, scan and push `feat/release-4`, satisfies **AC-1**, **AC-11**
9. Run `wf` on 39 to 48 and read the elapsed time in the report, satisfies **AC-12**

## Migration plan

**Strategy**: no data migration. The running `wf` stopped after feature 35's test step (2026-10-14 18:51).
**Phases**:
1. Build and test on `fix/questions-explained`, then merge into `feat/release-4`.
2. Set the standing answers, push `feat/release-4`, run `wf`.
**Rollback**: remove `- parallel: 4`, `- branches: per spec` and `- push: draft PR` from `AGENTS.md`; the runner goes back to one feature at a time on the current branch.
**Risks**: 4 calls at once use the usage limit about 4 times faster (the runner already waits and resumes); a resolve call can keep the wrong side of a clash, which the suite and your PR review are there to catch.

## Consequences

**Positive**:
- Features run 4 at a time; a test step drops from 16 to 42 minutes toward a few minutes.
- One plan file with every feature's real state; one combined PR to review.

**Negative / tradeoffs**:
- Up to 4 times the usage per hour.
- Clashes move from "never run together" to "resolve at combine time"; a wrong resolution is possible and is caught only by the suite and review.
- More branches and draft PRs; the runner commits scope files on the start branch in the main checkout.
- `fast.py` assumes tests do not share state across processes.

**Neutral**:
- `/check verify` also gets the suite sentence, an extension of your "once per feature" answer for the test step.
- Web app ports per worktree stay an open follow up of spec 0027; claude-config has no app.

## Follow-up

- [ ] A port per worktree, so web features of one repo can check in parallel (spec 0027 follow up).
- [ ] A `suite` standing answer for the other repos once they have a fast command.
- [ ] Ideas from docs/research/runner-landscape-2026-10-14.md: a status board, failed CI and review comments fed back as a fix step, cleaning issue text before prompts, free form guidance by Telegram reply, a wall clock cap per call.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
