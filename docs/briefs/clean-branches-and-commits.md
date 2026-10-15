# Clean branches, PRs and commits

Source: your messages of 2026-10-15 ("we have a lot of closed prs and non deleted branches that are useless", "a rule to not have a 100 commits per feature, like real commits by an engineer would do"), and the research in [docs/research/branch-pr-commit-workflow-2026-10-15.md](../research/branch-pr-commit-workflow-2026-10-15.md).

## Agreed so far, do not ask again

- The problem: 12 of 14 PRs closed unmerged because code reached `main` by a local merge and push; the runner made combined, land and lane branches; nothing deleted a branch after it landed; feature branches carried dozens of checkpoint commits.
- You approved designing these 8 rules (answer "Yes, design it now", 2026-10-15):
  1. `main` changes only through a merged PR, enforced by a GitHub ruleset (require a PR, 0 approvals, block force pushes, no bypass).
  2. Squash merge only: one spec = one branch = one PR = one commit on `main`; the PR title is that commit's Conventional Commit message.
  3. Delete on merge: GitHub "Automatically delete head branches" on; after each merge the runner prunes, deletes `[gone]` local branches, removes and prunes its worktree.
  4. No combined, land or lane branches; a spec needing another's unmerged code stacks on it (GitHub native stacked PRs), merged bottom up.
  5. No PR for work that may be dropped: the branch stays local until verify and test pass, then one draft PR updated by later pushes; a PR closed unmerged deletes its branch in the same step.
  6. Commits like an engineer: runner checkpoints stay local and are squashed before the first push into 1 to 5 commits, each one logical change that builds and passes its tests, code with its tests; never more than 15; after the first push only plain fix commits, and no rewrite except a rebase onto a changed base with `--force-with-lease`.
  7. Small and short lived: a diff under about 400 changed lines and a branch under 2 days; bigger specs split into stacked specs.
  8. Merge one at a time; after each merge rebase the next branch on the new `main` and run the full suite on the merged result.
- One time cleanup approved and done 2026-10-15: 36 branches whose work is in `main` deleted (13 on GitHub), their 23 worktrees removed, leftovers backed up in `~/claude-migration-2026-10-15/worktree-leftovers/`.

- Design answers (/architect interview, 2026-10-15), all the recommended option:
  - Combine step (spec 0043 AC-3): removed; each feature keeps its own branch and PR; after one merges, the runner brings the others up to date with the new `main` and tests again.
  - Plan updates: travel inside the feature's own PR; a planning only change (new spec, scope row, brief) goes in a small docs PR the runner may merge itself when it touches only `docs/`.
  - Commits: one squashed commit before the first push (rule 5 as it stands), review fixes as separate commits; `main` gets one commit per feature by squash merge.
  - Which repos: only repos whose AGENTS.md says `- branches: per spec` (today claude-config); work repos with the review bot keep their own rules.
  - Who merges: the runner merges a feature PR itself when it is green (verify, tests, scans pass), one at a time, and tells you after.
  - Review gate: it merges alone only a small low risk PR (your `/code-review` alone test: under about 200 lines and 10 files, no auth, payments, migrations, deletion, permissions, crypto or config, no changed contract, no deleted or skipped test); any other PR waits, the report says run `/review`, then it merges on "merge now".
  - GitHub settings (squash only, delete branch on merge, `main` needs a PR): one setup step per repo, then every run checks they are still on and reports if not.
  - Size limits (about 400 changed lines, branch older than 2 days): a warning in the report and the PR body, and `/architect` splits specs that look that big; never a block.
- Leftovers handled 2026-10-15: `wf/combined-20261015-0244` and `-0308` were fully in `main` and are deleted. `feat/seo-ops-refs` (2026-09-30, 703 lines not in `main`) and `sync-settings` (2026-07-21, clashes with `main`) hold real work and are kept for you to decide.
- Found in the code: the combine step is `combine()` and `combine_job()` in `runner/run.py` (spec 0043 AC-3); architecture invariants 1, 5 and 6 change with this spec.

## Open, for /architect
- How the runner's plan updates (scope ticks, verify notes; 38 direct commits to `main` on 2026-10-15) reach `main` once rule 1 blocks direct pushes.
- What happens to the branches kept on purpose: `feat/seo-ops-refs`, `sync-settings`, and the closed combined PRs' branches `wf/combined-20261015-0244` and `wf/combined-20261015-0308` (work not yet compared with `main`).
