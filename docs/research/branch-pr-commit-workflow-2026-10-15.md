# Branches, PRs and commits for an agent built repo: research report
*Generated: 2026-10-15 | Sources: 29 | Confidence: High on the rules, Medium on the numbers (PR size data is vendor data)*

## Executive summary

The repo's mess has three causes: code reached `main` by a local merge and a push, so 12 of 14 PRs closed unmerged; the runner bundled features into "combined" branches; and nothing deleted a branch after it landed. Every source agrees on the fix: short lived branches cut from `main`, code that lands only through its own PR, squash merge, and deletion of the branch on merge. On commits, no source sets a fixed count per feature. The unit is one logical change that builds and passes tests. The Linux kernel caps a series at about 15 patches per posting. With squash merge, the branch's commit count does not reach `main` at all: each feature becomes one commit there.

## 1. Branch model

- Short lived feature branches should "only last a couple of days. Any longer than two days, and there is a risk of the branch becoming a long-lived feature branch"; they are "merged and deleted" ([trunkbaseddevelopment.com, Short-Lived Feature Branches](https://trunkbaseddevelopment.com/short-lived-feature-branches/)).
- The same page warns against "intermediate merges to main (trunk) - at least where the commit was not able to go live on its own", and prefers more, smaller PRs over bundles.
- Committing straight to trunk works for tiny teams, but only with "everyone running the full build before the commit/push" ([Committing straight to the trunk](https://trunkbaseddevelopment.com/committing-straight-to-the-trunk/)). For agent written code it drops the PR record and the review gate.
- GitHub ships native stacked PRs (public preview since 2026-07-30, `gh stack`): "Stacks let you record those dependencies explicitly instead of combining unrelated changes into a single branch"; merging a lower PR makes the ones above "automatically re-target the stack's base branch" ([GitHub Docs, About stacked pull requests](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs)).
- Stacked diffs at Meta and Google: "Working in many small diffs helps ease the burden of rebasing against trunk, compared to using large, long-lived branches" ([Pragmatic Engineer, Stacked Diffs](https://newsletter.pragmaticengineer.com/p/stacked-diffs); quote from a search excerpt, not a raw page).

Verdict: GitHub flow with trunk based lifetimes (cut from `main`, live 2 days or less, one PR each). Stack only when one spec needs another spec's unmerged code. Never bundle.

## 2. How code lands, and cleanup

- A ruleset can "Require a pull request before merging"; "The pull request doesn't necessarily have to be approved, but it must be opened", so a solo repo can require a PR with 0 approvals. "Require linear history" forces squash or rebase ([GitHub Docs, Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)).
- Squash merge: "the pull request's commits are squashed into a single commit"; "Work-in-progress commits are helpful when working on a feature branch, but they aren't necessarily important to retain in the Git history". The cost: "You lose information about when specific changes were originally made" ([GitHub Docs, About merge methods](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github)).
- "Automatically delete head branches" fires only on a merged PR; a PR closed unmerged keeps its branch ([GitHub Docs, automatic deletion of branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches)).
- `git branch --merged` misses squash merges: "Because squash-merging recreates commits, the local ... branches point at different versions of the commits to those on `main`". The fix is `git pull --prune`, then delete the branches whose upstream shows `[gone]` ([Adam Johnson](https://adamj.eu/tech/2022/10/30/git-how-to-clean-up-squash-merged-branches/)). Tools that do the same: `git town sync --gone` ([Git Town](https://www.git-town.com/commands/sync.html)), `gh poi` and git-delete-squashed (both from search excerpts only).
- Claude Code: "Non-interactive runs with `-p` have no exit prompt, so Claude doesn't clean up their worktrees ... To remove one, run `git worktree remove`" ([Claude Code, Worktrees](https://code.claude.com/docs/en/worktrees)). A `claude -p` runner has to clean up after itself.

## 3. Commit size

- "Separate each logical change into a separate patch"; "each patch should make an easily understood change that can be verified by reviewers"; the tree must build "after each patch in the series"; "only post say 15 or so at a time" ([Linux kernel, Submitting patches](https://www.kernel.org/doc/html/latest/process/submitting-patches.html)).
- "try to make each commit a logically separate changeset"; "You may want to use `rebase -i` to squash your work down to a single commit" ([Pro Git, Contributing to a Project](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project)).
- "make your commit history look the way you want before you share it with others"; "you should consider pushed work as final unless you have good reason to change it" ([Pro Git, Rewriting History](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History)).
- Conventional Commits only governs the message: "Go back and make multiple commits whenever possible", and fix mistakes "Prior to merging or releasing" with `git rebase -i` ([Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)).
- Review unit size: "100 lines is usually a reasonable size for a CL, and 1000 lines is usually too large"; tests go in the same change; refactors in a separate one ([Google eng practices, Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)).
- Vendor data: "50-line code changes are reviewed and merged ~40% faster than 250-line changes", with 25 to 100 lines recommended ([Graphite](https://graphite.com/blog/the-ideal-pr-is-50-lines-long)); "under 200 lines" ([Cubic](https://www.cubic.dev/blog/does-pr-size-actually-matter)).
- Gap: no source gives a measured "commits per PR". A rule of "1 to 5" is a working heuristic, not a finding.

## 4. How AI agent tools commit

- Copilot cloud agent pushes to one `copilot/` branch, and its "Draft pull requests ... must be reviewed and merged by a human" ([GitHub Docs, risks and mitigations](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations)). "By default, Copilot pushes commits directly to the pull request branch" ([make changes to an existing PR](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/make-changes-to-an-existing-pr)). This is the model of one draft PR updated by later pushes.
- Codex opens the PR after review, not on every step ([OpenAI Codex workflows](https://developers.openai.com/codex/workflows/)).
- Aider commits every edit ("Whenever aider edits a file, it commits those changes") and gives no squash advice ([Aider git docs](https://aider.chat/docs/git.html)). That design is what produces hundreds of tiny commits.
- Devin merges with "the repository's configured merge strategy" ([Devin Review](https://docs.devin.ai/work-with-devin/devin-review)).
- Practitioners: "An agent's stream of incremental edits becomes a single, reviewable commit" ([git-stint](https://github.com/rchaz/git-stint)); a merge steward "Creates a single squash commit" then "Deletes the task worktree, local branch, and remote branch" ([Stoneforge](https://docs.stoneforge.ai/guides/auto-merge/)); "opens a small PR, merges, and the branch gets deleted. Never share a branch" ([Jeff Liu](https://www.jeffkliu.com/articles/running-ai-agents-in-parallel)).
- Parallel agents: "Merge one branch. Then run the full suite on the merged result"; "Merge as things finish, not in a batch" ([Parallel Code](https://parallelcode.app/blog/merging-parallel-ai-agent-branches/)). One preprint found 27.67% of 107,000 agent PRs had textual merge conflicts ([Pranav Bobde](https://pranavb.xyz/blogs/merging-in-parallel), citing the AgenticFlict preprint; not verified at the primary source).

## Recommended rules

1. **Main changes only through a merged PR.** A ruleset on `main`: require a PR (0 approvals), block force pushes, no bypass. Local merge and push of `main` stops.
2. **Squash merge only.** One spec = one branch = one PR = one commit on `main`. The PR title is that commit's Conventional Commit message.
3. **Delete on merge.** GitHub "Automatically delete head branches" on; after each merge the runner runs `git pull --prune`, deletes `[gone]` local branches, `git worktree remove` and `git worktree prune`.
4. **No combined, land or lane branches.** A spec that needs another's unmerged code stacks on it (`**Stacks on:**`, GitHub native stack), merged bottom up.
5. **No PR for work that may be dropped.** The branch stays local until verify and test pass; then one draft PR, updated by later pushes. A PR closed unmerged deletes its branch in the same step.
6. **Commits like an engineer.** Runner checkpoints stay local and are squashed before the first push into 1 to 5 commits, each one logical change that builds and passes its tests, code and its tests together; never more than 15. After the first push, review fixes are plain extra commits (squashed at merge); no rewrites except a rebase onto a changed base with `--force-with-lease`.
7. **Small and short lived.** Aim for a diff under about 400 changed lines and a branch under 2 days; split a bigger spec into stacked specs.
8. **Merge one at a time.** After each merge, rebase the next branch on the new `main` and run the full suite on the merged result.

## Sources
1. [Short-Lived Feature Branches](https://trunkbaseddevelopment.com/short-lived-feature-branches/) - branch lifetime of 2 days, merged and deleted
2. [Committing straight to the trunk](https://trunkbaseddevelopment.com/committing-straight-to-the-trunk/) - when direct commits work
3. [About stacked pull requests](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs) - GitHub native stacks
4. [Stacked Diffs, Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/stacked-diffs) - Meta and Google practice
5. [Stacked PRs explained, pullnotifier](https://pullnotifier.com/tools/stacked-prs) - weak, says solo devs may not need stacks
6. [Git Town sync](https://www.git-town.com/commands/sync.html) - deletes shipped branches, squash aware
7. [About merge methods](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github) - squash, rebase, merge commit trade offs
8. [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets) - require a PR with 0 approvals
9. [Automatic deletion of branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches) - delete head branches on merge
10. [Clean up squash merged branches, Adam Johnson](https://adamj.eu/tech/2022/10/30/git-how-to-clean-up-squash-merged-branches/) - the `[gone]` method
11. [saveman71](https://saveman71.com/2025/cleaning-up-local-branches-after-squash-merges) - search excerpt only
12. [git-delete-squashed](https://github.com/not-an-aardvark/git-delete-squashed) - search excerpt only
13. [gh-poi](https://github.com/seachicken/gh-poi) - search excerpt only
14. [Claude Code, Worktrees](https://code.claude.com/docs/en/worktrees) - `-p` runs leave worktrees behind
15. [Claude Code, Common workflows](https://code.claude.com/docs/en/common-workflows) - PR flow, small increments
16. [Claude Code GitHub Actions](https://code.claude.com/docs/en/github-actions) - pushes to the PR branch
17. [Copilot cloud agent, risks](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations) - one branch, human merges
18. [Copilot, change an existing PR](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/make-changes-to-an-existing-pr) - later pushes update the PR
19. [Copilot, kick off a task](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/kick-off-a-task) - branch first, PR after review
20. [Aider git docs](https://aider.chat/docs/git.html) - commits every edit
21. [OpenAI Codex workflows](https://developers.openai.com/codex/workflows/) - PR after review
22. [Devin Review](https://docs.devin.ai/work-with-devin/devin-review) - repo merge strategy
23. [git-stint](https://github.com/rchaz/git-stint) - squash an agent's edits into one commit
24. [Stoneforge auto-merge](https://docs.stoneforge.ai/guides/auto-merge/) - squash, then delete worktree and branches
25. [Jeff Liu, parallel agents](https://www.jeffkliu.com/articles/running-ai-agents-in-parallel) - one worktree per agent, small PR, delete
26. [Parallel Code, merging agent branches](https://parallelcode.app/blog/merging-parallel-ai-agent-branches/) - merge one at a time
27. [Pranav Bobde, merging in parallel](https://pranavb.xyz/blogs/merging-in-parallel) - conflict rate data (secondary)
28. [Linux kernel, Submitting patches](https://www.kernel.org/doc/html/latest/process/submitting-patches.html) - one logical change per patch, about 15 per posting
29. [Pro Git, Contributing and Rewriting History](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project) - shape before sharing, pushed work is final
Also: [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/), [Google Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html), [Graphite, ideal PR size](https://graphite.com/blog/the-ideal-pr-is-50-lines-long), [Cubic, PR size](https://www.cubic.dev/blog/does-pr-size-actually-matter).

## Methodology
Three parallel research agents (branch model and landing; commit size; AI agent tools), firecrawl search and scrape, Hacker News via Algolia. Quotes are copied from scraped pages except where marked "search excerpt". Gaps: no official Cursor statement on commits (the docs page returned a model table); Codex and Devin commit granularity not documented; no measured "commits per PR" figure exists in any source found. Failed: one docs.github.com URL (404), the Cursor docs page; the SHAPE hook blocked chained shell calls, which were rerun one at a time.
