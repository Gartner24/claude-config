# review-fix

Sorts the confirmed findings of a review by `rules/review-fix.md`, fixes the "fix now" ones with a test and a mutation
check each, then runs the suite, `/check verify` and `/test`. Done is a report that says "ready to push: yes" or "no".

## Pipeline
Numbered folders carry the order; each stage's `CONTEXT.md` says exactly what to read and write.

| Stage | Job | Input | Output | Human check |
|---|---|---|---|---|
| `01_sort` | Put every finding in one group (fix now, ask, never automatic) and split the fix now ones into file groups | `<run>/input/findings.md`, `rules/review-fix.md` | `sorted.md` plus the file groups as items | every finding in exactly one group |
| `02_fix` | Fix one file group, add a test, mutation check it, commit in its own worktree | its group from `01_sort`, the files it names | `<group>.md` | each test went red on its mutant |
| `03_check` | Merge the groups onto the PR branch, run the suite, `/check verify` and `/test` | the `02_fix` outputs | `report.md` | the suite line is green when it says ready |

## How to start
`/review-fix <pr>` in the repo to run on (`--limit 1` runs one file group of the fix stage). The starter skill
`claude-home/skills/review-fix/SKILL.md` makes the run id, then runs `review-fix.js` with the Workflow tool. The run goes
straight through; nothing asks you mid run. The script never pushes.

## Where runs write
`<repo>/.workflow/runs/review-fix/<run id>/NN_<stage>/output/`, git ignored. Read each stage's output against its
human check after the run. Run folders stay until you delete them.

## Owner steps
- Before the run: the PR number; the findings come from the newest `docs/reviews/` file for the PR, else the PR's review comments, and a finding with no `file:line` is dropped and counted.
- After the run: show the report. Ready and no "ask" finding means the starter pushes (in a bot-reviewed repo that triggers the bot's re-review); otherwise no push and one panel with every open choice. Never merge, rewrite pushed history or bill.
