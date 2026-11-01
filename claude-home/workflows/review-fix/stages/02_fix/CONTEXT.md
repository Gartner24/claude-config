# 02_fix

Fixes one file group with a test and a mutation check, and commits it in its own worktree.

Model: sonnet medium

`<run>` below is `<repo>/.workflow/runs/review-fix/<run id>`; the prompt gives you both values.

## Inputs
- `<run>/01_sort/output/sorted.md`: only the entry for your group; the prompt names it
- The files your group names

## Process
1. If an input is missing or empty, stop and say which.
2. Fix each finding of your group, in order.
3. Add a test for each fix.
4. Mutation check each test: back up the file with `cp`, break the behavior the test covers, run only that test file and see it go red, restore from the backup and see it green (`~/.claude/rules/lessons.md`).
5. Commit in your worktree (the prompt names the branch).
6. Write the outputs below, then return the schema the prompt names.

## Outputs
- `<run>/02_fix/output/<group>.md`: the findings fixed, each test with its mutant and whether it went red, and the commit sha

## Check
Each test went red on its mutant.

## Do NOT load
- Other groups
- The full review report
