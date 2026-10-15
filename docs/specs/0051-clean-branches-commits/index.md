# 0051 · Clean branches, PRs and commits

**Date**: 2026-10-15
**Status**: In Progress
**Paths:** `runner/pr.py`, `runner/run.py`, `runner/wf.py`, `runner/plain.py`, `runner/report.py`, `runner/tests/test_pr.py`, `runner/tests/test_clean_branches.py`, `bin/docs-pr.sh`, `bin/repo-settings.sh`, `claude-home/rules/branch-pr.md`
**Amends**: [0026](../0026-branch-pr-flow/index.md) (standard rules 4 for unstacked branches, 5 and 6; AC-8, AC-9, AC-11), [0031](../0031-adopt-open-prs/index.md) (AC-9: two more merge paths), [0043](../0043-fast-runner/index.md) (AC-2 text, AC-3 removed, AC-6 plan commits now land by AC-15), and architecture invariants 1, 5 and 6.

## What you're agreeing to
- Code reaches `main` only through its own PR, squash merged into one commit; GitHub refuses a direct push to `main` in an opted in repo, and deletes the branch when its PR merges.
- The runner stops combining features into one branch: each feature gets its own PR, merged one at a time, and the runner removes its local branch and folder after the merge.
- In a repo you opt in privately, the runner merges a feature's PR itself when it is small and low risk and its checks pass, judged from `main`, never from the PR; anything else asks you "merge now?" after your `/review`.
- The runner's own plan commits reach `main` through a docs PR it merges itself, only when every changed file is in the plan folder; sessions use `bin/docs-pr.sh` the same way.
- A feature over about 400 changed lines, or a branch older than 2 days, gets a warning in the report and the PR, never a block.

## Summary
The repo's mess had three causes: code reached `main` by a local merge and push, so 12 of 14 PRs closed unmerged; spec 0043's combine step bundled features into `wf/combined-*` branches; nothing deleted a branch after it landed. This spec makes the PR the only way in, removes the combine step, adds a self merge for small low risk PRs in privately opted in repos, a docs PR for plan commits, cleanup after every merge, a one time settings script, and size and age warnings. Research: [docs/research/branch-pr-commit-workflow-2026-10-15.md](../../research/branch-pr-commit-workflow-2026-10-15.md). Agreed decisions, including the cross check answers: [docs/briefs/clean-branches-and-commits.md](../../briefs/clean-branches-and-commits.md).

## Requirements
- **AC-1** (opt in and trust): the self merge of AC-5 runs only when the repo's standing answers say `branches: per spec` and `push: draft PR` (spec 0026 AC-1) and its `~/.claude/private/pr.json` entry has `"auto_merge": true` (`flag(r, "auto_merge")`, `runner/pr.py:1102`). The switch lives where no call can write: `~/.claude/private` is in `SECRETS` (`runner/run.py:347`), so every call is denied it. A test asserts `SECRETS` holds `~/.claude/private` and that a call's deny arguments cover `~/.claude/private/pr.json`; probe P1 (verify.md) shows a real call's write to it is refused.
- **AC-2** (no combine step): `combine()`, `resolve()`, `COMBINE_PROMPT`, `combine_job()` and its caller, the hidden `--combine` flag in `runner/wf.py`, the `combine_conflict` rows in `CASES` and `runner/plain.py`, and `runner/tests/test_combine.py` are removed; `clean_suite()` stays (AC-4 uses it). A parallel run ends each feature on its own branch with its own PR. No branch named `wf/combined-*` is made again; an old record with `combined: true` is never published or merged.
- **AC-3** (small and low risk): `small_safe(r, rec, base, head)` in `runner/pr.py`, over `git diff --numstat <base>...<head>` and `git diff <base>...<head>`, where `<base>` is `origin/<default>` for an unstacked record and the base branch tip for a stacked one, is true only when:
  - added plus deleted lines are at most 200 and changed files at most 10;
  - no changed path matches `RISK_PATHS` (`fnmatch`, case folded, whole repo relative path): `*auth*`, `*login*`, `*payment*`, `*billing*`, `*invoice*`, `*migration*`, `*permission*`, `*crypto*`, `*secret*`, `*credential*`, `.github/*`, `*.env*`, `AGENTS.md`, `*/AGENTS.md`, `CLAUDE.md`, `*/CLAUDE.md`, `claude-home/settings*.json`, `claude-home/hooks/*`, `claude-home/rules/*`, `runner/*`, `bin/*`, `scripts/*`, `docs/scope/*`, `.workflow/*`, and the repo's scope folder. `*token*` and `*session*` are left out on purpose: they match harmless names, and auth code is caught by the others;
  - no test file (`test_*.py`, `*_test.py`, `*.test.*`, `*.spec.*`, or under `tests/` or `__tests__/`) is deleted, and no added line matches `@unittest.skip`, `pytest.mark.skip`, `\.skip\(` or `\bxit\(`;
  - no deleted line is a top level `def` or `class` line whose name is missing from the added lines, an `add_argument("--` flag missing from the added lines, or an `os.environ` key missing from the added lines.
  It returns `(ok, reasons)`, one short reason per failed rule (`312 lines`, `touches runner/pr.py`, `deletes a test`, `removes def run_step`).
- **AC-4** (green, judged from main): `green(r, rec, head)` is true when all hold: the feature's verify and test boxes are ticked in the main checkout's plan (the one plan of spec 0043 AC-4, never the branch's copy); the suite command is the `suite` standing answer read from `origin/<default>`'s `AGENTS.md` (`git show origin/<default>:AGENTS.md`), never the branch's, and it exits 0 through `clean_suite()` on a tree of `<head>`; both scans of spec 0026 AC-6 pass on `pushed_sha..<head>`; and every check GitHub reports for the PR (`gh pr view --json statusCheckRollup`) is `SUCCESS`, `NEUTRAL` or `SKIPPED` (none is fine). No `suite` answer on `origin/<default>` means not green. `RISK_PATHS` and these rules live in the installed runner copy, so a branch cannot change them.
- **AC-5** (self merge): `merge_green(r, rec)` holds the repo's merge lock (`<state>/locks/merge-<sha1 of repo path>.lock`, `fcntl.LOCK_EX`) from AC-6 to the merge, and in that lock: `git fetch origin`; AC-6; `small_safe`; `green`; `gh pr view <n> --json state,isDraft,headRefOid,mergeable`: state `OPEN`, head equal to the tested head, `mergeable` `MERGEABLE` (`UNKNOWN` is read again after 10 seconds, at most 3 times, then counts as not mergeable); `origin/<default>` still at the commit AC-6 merged in (else AC-6 runs again, once); then `gh pr ready` if it is a draft, and `gh pr merge <n> --repo <o/r> --squash --delete-branch --match-head-commit <tested head>`. Success sets `state: merged`, runs AC-7, adds `merged: <feature>: PR #<n> (small and low risk)` to the report. In an AC-1 repo `publish` opens the PR as a draft as today, then calls `merge_green` at once; a stacked record merges only after its base record is `merged` (bottom up). Not small and low risk opens AC-8. Any other failure leaves the PR open with one report note, and the next poll tries `merge_green` again.
- **AC-6** (up to date, no force push): a branch whose base is the start branch and that does not contain `origin/<default>` is brought up to date by `git merge --no-edit origin/<default>` with plain git, never a rebase (this replaces standard rule 4 for unstacked branches; stacked ones keep spec 0026 AC-16). Then, in order: both scans on `pushed_sha..HEAD`, a fast forward push (spec 0026 AC-7), `pushed_sha` updated. Commits reachable from `origin/<default>` never count for spec 0031 AC-3's foreign change check. A conflict runs `git merge --abort` and asks `merge_conflict`: "leave it for you" (recommended), "try again at the next run".
- **AC-7** (cleanup after a merge or close): whenever a record becomes `merged` (AC-5, AC-8, "I merged it", or a poll) or `closed`, `wf` runs, in order: `git fetch --prune origin`; `git worktree remove <tree>` when the feature's worktree is clean (else the note `left: <tree>: uncommitted changes`); `git branch -D <branch>` only when `gh pr view` says `MERGED` or `CLOSED` and the local tip equals the PR's `headRefOid` or is its ancestor (else the note `kept: <branch>: commits after the PR`); for `CLOSED`, `git push origin --delete refs/heads/<branch>` when the ref still exists, with spec 0026 AC-7's refusals (never `main`, `master` or the default branch, `origin` unchanged since the run started); `git worktree prune`. A failed step is one note; none asks.
- **AC-8** (waits for your review): in an AC-1 repo, a green PR that is not small and low risk stays a draft; the report says `next: run /review on PR #<n> (<reasons>), then answer merge now`, and case `merge_ready` asks `PR #<n> passed its checks but needs your review (<reasons>). Merge it now? (head <7 chars>)`, options "merge now" (recommended), "later". The question stores `asked_head`. `answer()` (`runner/pr.py:788`) handles `merge_ready` before its option fallback: only `chose(d, MERGE_NOW)` and `strong(r, d)` (`runner/pr.py:844`, `:850`) merge, through `merge_green` with `--match-head-commit <asked_head>` and green judged again; a head that moved asks again naming the new head; "later" or any other reply merges nothing.
- **AC-9** (allow list): `allowed()` (`runner/pr.py:60`) gains exactly these, each tested to raise from any other caller and with any extra flag (`--admin`, `--auto` never allowed): `pr merge <n> --repo <o/r> --squash --delete-branch --match-head-commit <sha>` (9 items) and `pr ready <n> --repo <o/r>` only with `green=True` from `merge_green` and `land_plan`; `pr create --repo <o/r> --base <default> --head docs/plan-<stamp> --title <t> --body-file <f>` without `--draft` only with `plan=True` from `land_plan`; `api` GET of `repos/<o>/<r>/rulesets` for AC-10. Spec 0031's `pr merge` entry is unchanged.
- **AC-10** (repo settings): `bin/repo-settings.sh <owner/repo>`, run by you or a session (never by `wf`), sets through `gh api`: `allow_squash_merge=true`, `allow_merge_commit=false`, `allow_rebase_merge=false`, `delete_branch_on_merge=true`, `squash_merge_commit_title=PR_TITLE`, `squash_merge_commit_message=PR_BODY`; and one branch ruleset named `main only through a PR` on `~DEFAULT_BRANCH` with rules `pull_request` (0 approvals), `non_fast_forward` and `deletion`, enforcement `active`, no bypass actors. `--check` only reads and exits 1 on any difference. At each run start, for every AC-1 repo, `wf` reads `gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed,deleteBranchOnMerge` and the rulesets; any difference is one report line `settings: <repo>: <what is off>; run bin/repo-settings.sh <owner/repo>`, and AC-5 is off for that run.
- **AC-11** (docs PR helper): `bin/docs-pr.sh [slug]`, run in a repo on its default branch, refuses (exit 2, one line) when the tree has tracked changes, when no commit is ahead of `origin/<default>`, or when any commit ahead touches a path outside `docs/`. Otherwise: `scripts/private-names.py check-range` and the attribution scan of spec 0026 AC-6 on the range, then a `docs/<date>-<slug>` branch at HEAD, push, `gh pr create --base <default> --fill`, `gh pr merge --squash --delete-branch --match-head-commit <HEAD>`, back to the default branch, `git fetch --prune`, and `git reset --keep origin/<default>` only after `git diff --quiet <old HEAD> origin/<default> -- docs`; else it stops and keeps the local commits. It prints the PR URL.
- **AC-12** (size, age, title): the PR body and the `built:` report line add `large: <n> lines changed (over 400)` above 400 added plus deleted lines, and `old: branch <d> days (over 2)` when the first commit after `base_sha` is more than 2 days old; never a block. The PR title stays spec 0026 AC-5's subject `<feat|fix>: <heading> (spec NNNN)`, a Conventional Commit, which AC-10 makes the squash commit's title.
- **AC-13** (never stop): `merge_ready` and `merge_conflict` get their rows in `CASES` and `runner/plain.py`, so the spec 0021 AC-1 completeness test covers them; neither holds back another feature.
- **AC-14** (rules and docs): `claude-home/rules/branch-pr.md` rule 4 adds "an unstacked branch is brought up to date by merging the default branch into it, never a rebase"; rule 6 reads "One PR per spec branch. `wf` merges it itself only under spec 0051 AC-5; otherwise a person merges, or `wf` on that person's explicit merge now"; new rules: 7, code reaches the default branch only through a merged PR, squash merged, never a local merge and push, and plan only changes through a docs PR; 8, a merged or closed PR's branch and worktree are deleted; 9, no combined, land or lane branches, a spec that needs another's unmerged code stacks on it and merges after it; 10, keep a feature under about 400 changed lines and 2 days, and `/architect` splits a spec that looks bigger. `docs/architecture.md` invariants 1, 5 and 6 say the same, and specs 0026, 0031 and 0043 get an `**Amended by**: 0051` line.
- **AC-15** (plan commits by docs PR): at the end of every run of a repo with `push: draft PR` whose start branch is its default branch, `land_plan(r)` takes the commits on it ahead of `origin/<default>`; when there are none, or any of them touches a path outside the repo's scope folder, it does nothing (a note for the second case). Otherwise, under the merge lock: both scans on the range, `git push origin <HEAD>:refs/heads/docs/plan-<YYYYmmdd-HHMM>`, `gh pr create` (AC-9), `gh pr merge --squash --delete-branch --match-head-commit <HEAD>`, `git fetch --prune`, then `git reset --keep origin/<default>` only when `git diff --quiet <old HEAD> origin/<default> -- <scope folder>`. A failed step is one note and leaves the local commits. No `auto_merge` needed: only plan files can land this way.

## Decision
Remove the combine step, make the PR the only way code lands, squash merge, delete on merge, self merge only small low risk PRs that are green by main's own checks in a privately opted in repo, land plan commits through a plan only docs PR, and enforce it on GitHub with a ruleset set once by a script and checked each run.
**Implementation skills**: none.

## Feature design
### Value sourcing
| Value | Source |
|---|---|
| self merge on | `~/.claude/private/pr.json` entry `auto_merge` (AC-1) |
| lines, files, paths changed | `git diff --numstat` and `git diff` of `<base>...<head>` (AC-3) |
| risk paths | `RISK_PATHS` in the installed runner copy (AC-3, AC-4) |
| verify and test ticked | the main checkout's plan (AC-4) |
| suite command | `git show origin/<default>:AGENTS.md`, the `suite` answer (AC-4) |
| PR checks, state, head, mergeable | `gh pr view --json statusCheckRollup,state,isDraft,headRefOid,mergeable` (AC-4, AC-5) |
| approved head | `asked_head` stored with the `merge_ready` question (AC-8) |
| repo settings | `gh repo view --json ...` and `gh api repos/<o>/<r>/rulesets` (AC-10) |
| branch age | commit date of the first commit after `base_sha` (AC-12) |

### Edge cases
- Two features finish together: the lock serializes them; the second sees `origin/<default>` moved, merges it in, pushes, and runs main's suite again before it merges.
- A feature edits `AGENTS.md` to make the suite pass trivially: `AGENTS.md` is a risk path (no self merge), and the suite is read from `origin/<default>` anyway.
- A reply that is not an option to `merge_ready`: nothing merges.
- A PR you merge on GitHub: the next poll sets `merged`, and AC-7 cleans up.

## Build plan
0. Run probe P1 first; a write to `~/.claude/private/pr.json` that a call can make stops the build and goes back to `/architect` (AC-1).
1. Remove the combine step and its tests (AC-2); suite green.
2. `small_safe`, `RISK_PATHS`, `green` from main, size, age and title lines (AC-3, AC-4, AC-12).
3. Merge lock, up to date by merge with scan and push, `merge_green`, `merge_ready`, `merge_conflict`, allow list (AC-5, AC-6, AC-8, AC-9, AC-13).
4. Cleanup after merge or close (AC-7); `land_plan` (AC-15).
5. Settings check at run start (AC-10); `bin/repo-settings.sh` and `bin/docs-pr.sh` (AC-10, AC-11); `SECRETS` test and probe P1 (AC-1).
6. Rule text, architecture invariants, Amended by lines (AC-14).
7. Run `bin/repo-settings.sh Gartner24/claude-config`, then `--check` exits 0.
8. Add `"auto_merge": true` to the claude-config entry in `~/.claude/private/pr.json`.

## Probes
- **P1**: a real `wf` call (`python3 runner/e2e/run.py` style, or a scratch repo run) whose step tries to write `~/.claude/private/pr.json` is refused by the sandbox, and the file is unchanged. Recorded in verify.md.

## Consequences
**Positive**: every change on `main` has a PR; no stale branches or worktrees; parallel features merge one by one, each retested on the new `main`; small low risk changes land without waiting for you.
**Negative**: sessions can no longer push to `main`; they use `bin/docs-pr.sh`. Ruleset changes live in GitHub settings, checked each run, not versioned. In claude-config almost every runner change touches `runner/` or `claude-home/`, so it asks "merge now" rather than self merging.
**Known risk**: `small_safe` is a text heuristic; a risky change that avoids every pattern can self merge. The private switch, main's suite, the scans and GitHub's checks are the backstop, and `auto_merge` turns off in one line.

## Follow-up
- [ ] The personal row "Branch, PR and stacked PR standard" closes when this ships.
- [ ] GitHub native stacked PRs (`gh stack`) could replace spec 0026 AC-16's own rebase.
- [ ] The kept branches `feat/seo-ops-refs` and `sync-settings` are yours to land or delete (master list).

## Rationale
See [rationale.md](rationale.md).
