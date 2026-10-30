# 03_check

Merges the fixed groups onto the PR branch, runs the suite, `/check verify` and `/test`, and says whether it is ready to push.

Model: sonnet medium

`<run>` below is `<repo>/.workflow/runs/review-fix/<run id>`; the prompt gives you both values.

## Inputs
- `<run>/02_fix/output/<group>.md`: one per fixed group, with its commit sha and branch
- `<run>/01_sort/output/sorted.md`: only to learn whether any ask finding is open

## Process
1. If an input is missing or empty, stop and say which.
2. Merge the group branches onto the PR branch in a git worktree of that branch. Never push.
3. Run the suite (the prompt gives the command), then `/check verify` and `/test`.
4. Write the report with the line `ready to push: yes` only when the suite is green, else `ready to push: no` with the reason.
5. Write the outputs below, then return the schema the prompt names.

## Outputs
- `<run>/03_check/output/report.md`: the merge result, the suite line, the verify and test results and the line `ready to push: yes` or `ready to push: no`

## Check
The suite line is green when the report says ready.

## Do NOT load
- The raw review report
