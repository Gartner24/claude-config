# 0027 · Several features of one repo at once

**Date**: 2026-10-13
**Status**: Proposed
**Paths:** `runner/run.py`, `runner/wf.py`, `runner/report.py`, `runner/e2e/run.py`, `runner/tests/test_parallel_repo.py`
**Amends**: [0017](../0017-several-repos-at-once/index.md) AC-3 (two children may share a git common dir when both are feature worktrees of one repo with disjoint Paths), [0008](../0008-failure-park-policy/index.md) AC-9 (a feature worktree is trusted through its repo), architecture invariant 6 (one feature at a time per repo, unless the repo says `parallel`). Builds on [0026](../0026-branch-pr-flow/index.md) (spec branches, `prs` records).

## What you're agreeing to
- A repo whose AGENTS.md says `- parallel: <n>` builds up to n of its features at the same time, each in its own folder (a git worktree) on its own spec branch; your own checkout is never switched.
- Two features whose specs name overlapping files (`**Paths:**`) never run at the same time; one waits for the other. A feature with no Paths line runs alone.
- Each branch holds only its own feature's work; nothing ever merges one feature into another, and a step cannot edit a sibling's folder.
- Features of one repo that share an app port still run one after another, and parallel calls use your usage window faster.

## Acceptance criteria
Today: bare `wf run` starts one child per repo (`runner/run.py:3684-3780`) and never two sharing a git common dir (`clashes`, `runner/run.py:3678-3681`); a child is `wf run <path> -y` plus caps and `--only-feature` (`:3707-3741`); the trust list matches the exact real path (`untrusted`, `runner/run.py:3063-3069`); locks are per path (`repo_lock`, `runner/run.py:3267-3270`); discovery already lists linked worktrees (`runner/wf.py:319-338`, `:460-463`).

- **AC-1** (opt in): `ANSWER_KEYS` (`runner/run.py:180`) gains `parallel`, a whole number 1 to 4. `read_answers` refuses it without `branches: per spec` (spec 0026 AC-1) with `parallel needs branches: per spec`, and refuses any other value. Without the key a repo runs as spec 0026 says (one feature at a time, in its own checkout).
- **AC-2** (a worktree per feature): in a `parallel` repo every feature builds in its own linked worktree at `~/.local/share/wf-trees/<repo folder name>-<first 6 hex of sha1 of the repo real path>/<branch with / as ->`. The parent (bare `wf`, bare `wf run`, or `wf run <repo>` on that repo) makes the spec branch as spec 0026 AC-2 and AC-3 do (`git branch <name> <base commit>`, no switch), then `git worktree add <path> <name>` with hooks off (`wf.git`), and reuses a worktree that already exists for that branch. A call never makes or removes a worktree. The repo's own checkout is never switched.
- **AC-3** (children): the parent starts one child per picked feature, `wf run <worktree> -y --only-feature <feature>` plus the caps, exactly as spec 0017 starts a repo child. A worktree passes `untrusted` when its real path is under that repo's wf-trees folder and its git common dir's main checkout is on the trust list. Each child locks its worktree path. In every record (`queue.json` parks, decisions and `prs`, `run.json` `repos` and `features`, the report) `repo` is the main checkout's real path and a new field `tree` holds the worktree path, so a question asked in a worktree is resumed in the same worktree and survives its removal.
- **AC-4** (how many): at most `<n>` children of one repo run at once, and `--jobs` still caps all children (spec 0017 AC-2). `clashes` lets two children share a git common dir only when both are worktrees of the same `parallel` repo and their features pass AC-5; a shared app port still keeps them apart (spec 0017 AC-3).
- **AC-5** (Paths never shared): a feature's globs are the backticked spans on its spec top file's `**Paths:**` line (the parse of `scripts/spec-paths.py:18`, `:95`). Two features overlap when a glob of one matches a glob of the other with `fnmatch` either way, or one is a folder prefix of the other. A feature with no spec link, no Paths line or no globs overlaps every feature. The scope folder, `AGENTS.md`, `CLAUDE.md` and `verify.md` files are left out (every feature's `/sync` and checks touch them; see Follow-up). An overlapping feature is not started while the other runs, plan line `waits: <feature>: shares <glob> with <other>`, and starts when the other's child exits.
- **AC-6** (drift): the parent writes `<state>/active.json` under `queue.lock`: each running child's repo, feature, tree and globs. After each call a child lists the files its branch changed since `base_sha` (`git diff --name-only <base_sha>` plus untracked files, the AC-5 exclusions left out); a file matching another running feature's globs opens case `paths_overlap`: "wait for <other> to finish, then go on" (recommended), "undo those files and try again", "skip". "wait" parks the feature with a retake when the other's child exits (spec 0020 AC-6 gains this signal). The case has its `CASES` row (`runner/run.py:212-243`).
- **AC-7** (never mixed): every call's Edit deny list (spec 0007 AC-5) adds `Edit(//<p>/**)` for the main checkout and every other worktree of the repo (from `runner/wf.py:319` at the child's start, plus `active.json` before each call). No code path merges, cherry picks or rebases one feature's branch onto a sibling's; the only rebase is onto a stacked base (spec 0026 AC-16). The squash (spec 0026 AC-5) runs in the feature's own worktree.
- **AC-8** (cleanup): a worktree is removed with `git worktree remove <path>` (never `--force`), then `git worktree prune`, when its `prs` record is `merged` or `closed`, or its feature was skipped with no commit beyond `base_sha`, and its tree is clean. A dirty one is kept and the report says `kept <tree>: uncommitted changes`. Review rounds (spec 0026 AC-12) of a PR in a `parallel` repo run in its worktree, never in the main checkout.
- **AC-9** (report and screen): each feature child is one row, named `<repo>: <feature>` in the spec 0017 summary and the `wf` screen's `build:` list; the morning report names the repo and the feature on each line (spec 0018 AC-2).
- **AC-10** (real check): `runner/e2e/run.py --same-repo` makes a fixture repo with `parallel: 2` and three queued features, A and B with disjoint Paths and C sharing a glob with A, runs `wf -y`, and prints `PASS` only when A's and B's calls overlap in time, each ends as its own branch whose diff from its base holds only its own files, C starts only after A's child exited, the main checkout's branch never changed, and no worktree is left for a feature with no commits; otherwise `FAIL: <check>`. You run it as a live step.

## Build plan
1. Run probe P1 and record it in `verify.md` (no AC).
2. Standing answer, worktree making and reuse, trust and lock per worktree, `repo` and `tree` in records (AC-1, AC-2, AC-3).
3. Scheduling: per repo limit, Paths overlap, `clashes` change, plan lines (AC-4, AC-5).
4. Drift check and its case, sibling Edit denies (AC-6, AC-7).
5. Cleanup, review rounds in the worktree, report and screen rows (AC-8, AC-9).
6. `runner/e2e/run.py --same-repo` (AC-10) · waits on you · live.

## Probes
- **P1** (local, no network): two worktrees committing at once share one object store and refs without lost commits. In a temp dir: `git init r && git -C r commit --allow-empty -m base && git -C r worktree add ../a -b a && git -C r worktree add ../b -b b`, then run `for i in $(seq 50); do echo $i > f; git add f; git commit -qm $i; done` in `a` and in `b` at the same time; both `git -C a rev-list --count a` and `git -C b rev-list --count b` print 51, and `git -C r fsck` is clean. Any `index.lock` or `ref lock` failure goes back to `/architect` (a retry rule like spec 0020 AC-8).
- No new Claude Code probe: Edit deny rules on paths and the sandbox write paths of a linked worktree are already confirmed by spec 0007 (probes 7, 8 and its worktree tests).

## Follow-up
- [ ] Shared files left out of AC-5 (scope, `AGENTS.md`, `verify.md`) can conflict when two PRs merge; if that happens often, `/sync` in a `parallel` repo could write its lines only at merge.
- [ ] One app port per worktree would let web app features run side by side (today they wait, AC-4).
- [ ] Residual, same threat model as spec 0007: calls of sibling features share the git common dir as a write path, so a call could move a sibling's branch ref through git; accidental only, not hardened.
