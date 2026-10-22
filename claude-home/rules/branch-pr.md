# Branch and PR standard (spec 0026, all repos, people and agents alike)

1. **One branch per spec.** Name `feat/<NNNN>-<slug>` (`fix/...` when the feature heading starts with "Fix"), `NNNN` the spec number, `<slug>` the feature heading in lower case with runs of other characters as `-`. A feature with no spec: `feat/<slug>`.
2. **Off the planning branch by default.** A spec branch is cut from the branch the spec and scope were committed on (normally `main`). It stacks on another spec's branch only when its spec top file says `**Stacks on:** NNNN`.
3. **Max stack depth 3.** A chain counts the branch itself plus every unmerged spec branch below it. A fourth waits until the bottom one merges, or is built off the planning branch.
4. **Rebase when the base changes.** When a base branch gets new commits, or merges, each branch above it is rebased onto the new base (`git rebase --onto <new base> <old base commit> <branch>`), bottom first, and its PR is retargeted after a merge. A pushed branch is force pushed only with `--force-with-lease` naming the commit last pushed, and only after a yes. An unstacked branch is brought up to date by merging the default branch into it, never a rebase (spec 0051).
5. **One commit per feature.** Checkpoint commits on a spec branch are squashed into one Conventional Commit before its first push. After the first push nothing is squashed or rewritten except by rule 4: review fixes are separate commits, squashed at merge.
6. **One PR per spec branch.** A person merges, or Claude on that person's explicit yes in own repos. It opens as a draft, base = the branch it was cut from.
7. **Code reaches the default branch only through a merged PR**, squash merged, never a local merge and push. The plan only changes through a docs PR (`bin/docs-pr.sh`).
8. **A merged or closed PR's branch and worktree are deleted.**
9. **No combined, land or lane branches.** A spec that needs another's unmerged code stacks on it and merges after it.
10. **Small and short lived.** Keep a feature under about 400 changed lines and 2 days; `/architect` splits a spec that looks bigger.

## For `/architect`

Write `**Stacks on:** NNNN` on the line after `**Paths:**` only when the build needs code from spec NNNN that is not merged yet. Needing only a decision from another spec is not a reason to stack.
