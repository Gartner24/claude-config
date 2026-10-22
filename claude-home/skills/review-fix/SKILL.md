---
name: review-fix
description: Fix the confirmed findings of a review on a PR with a test and mutation check each, then run suite, verify and test. Runs the review-fix workflow (stage folders in ~/.claude/workflows/review-fix).
argument-hint: "[--limit 1] <pr>"
---
Start the `review-fix` workflow (spec 0076). Its stages and their checks: `~/.claude/workflows/review-fix/CONTEXT.md`.

1. Before the run: take the PR number from the argument. Findings: the newest `docs/reviews/` file for the PR, else the
   PR's review comments (`gh pr view <pr> --comments`); write them to `<run>/input/findings.md` (a finding with no
   `file:line` is kept in the file; `01_sort` drops and counts it). Round: 1 plus the number of folders already in
   `<repo>/.workflow/runs/review-fix/` that start with `<pr>-`; a third round does not run, say so and stop.
   The answers fill the named args: `pr`: the argument; `branch`: `gh pr view <pr> --json headRefName`;
   `round`: 1 or 2 as counted; `suite`: the `suite:` standing answer in the repo's `AGENTS.md` (missing: stop with
   `missing arg: suite`).
2. Repo: `git rev-parse --show-toplevel` (absolute). Run id: `<pr>-<date +%Y%m%d>-<n>`, `n` the round (local time).
3. Keep runs out of git: `git -C <repo> check-ignore -q .workflow/x`. When it exits non zero, append the line
   `.workflow/` to the file `git -C <repo> rev-parse --git-path info/exclude` names (relative paths are under `<repo>`).
4. Call the Workflow tool with `scriptPath` `~/.claude/workflows/review-fix/review-fix.js` and `args`
   `{repo, runId, limit, pr, branch, round, suite}`: `limit` is `1` when the user typed `--limit 1`, else `null`.
5. After the run, for each stage show its output folder `<repo>/.workflow/runs/review-fix/<run id>/NN_<stage>/output/`,
   the line under `## Human check` in `~/.claude/workflows/review-fix/stages/NN_<stage>/CONTEXT.md`, and any `wf/...`
   branches the run returned. Say any stage marked `failed`. Count the folders in `<repo>/.workflow/runs/review-fix/` and
   say "<n> run folders kept until you delete them".
6. After the run: show `03_check/output/report.md`. In round 2, write the leftovers from `sorted.md` into the review
   brief's `## Leftovers` and add one scope row "Review leftovers <date>" whose `Source:` is that brief. When the report
   says `ready to push: yes` and no finding is in the ask group, push the PR branch (in a bot-reviewed repo that
   triggers the bot's re-review); a HIGH finding left asks. Otherwise do not push: ask one panel with every open choice
   (`rules/plain-questions.md`). Never merge, rewrite pushed history or bill.
