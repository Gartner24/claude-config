# 0051 · Rationale

## Context
On 2026-10-15 the repo held about 48 merged but undeleted branches, 12 of its 14 PRs were closed unmerged, and the runner's combine step (spec 0043 AC-3) had opened combined PRs that were later closed because the work reached `main` by a local merge and push. You asked for a workflow with no useless branches or PRs and commits like a real engineer makes.

## Options considered
- **Trunk based, push to main directly**: no branches at all, but no PR record and no gate for agent written code. Rejected.
- **GitHub flow with short lived branches, PR only, squash merge, delete on merge** (chosen): every source in the research agrees; it matches spec 0026's branch per spec.
- **Keep the combine step as a local test merge**: early clash warnings, but more runner time; you chose to remove it, and AC-6's up to date merge plus the suite on the merged head catch clashes per feature.
- **Self merge every green PR**: fastest, but drops your rule that a change outside the small low risk test gets `/review`; you chose the small low risk gate.
- **Opt in through AGENTS.md alone**: a call can edit `AGENTS.md`, so it could switch self merging on; the switch lives in private `pr.json` instead, like spec 0031's `merge`.
- **Bring branches up to date by rebase**: needs a force push for a pushed branch, which rules/review-fix.md never does automatically; a merge of `origin/main` into the branch needs none, and squash merge flattens it anyway.

## Rationale
Squash merge makes `main` one commit per feature whatever the branch holds, so rule 5's one squashed commit before the first push stays as it is. The ruleset with no bypass is the only thing that stops a local merge and push; a rule in a markdown file did not. `RISK_PATHS` and the contract checks turn your `/code-review` alone rule into code; the runner's own guard files and `runner/pr.py` are in it, so the runner can never self merge a change to its own merge logic.

## References
See [docs/research/branch-pr-commit-workflow-2026-10-15.md](../../research/branch-pr-commit-workflow-2026-10-15.md) for the 29 sources.
