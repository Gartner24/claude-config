# restructure-check

Proves a restructure PR changes no behavior. It records every behavior output of the repo on the base and on the PR
head, diffs them, and has one regression agent judge only the differences. Done is a report that lists each
difference as "expected from the move" or "needs a look".

## Pipeline
Numbered folders carry the order; each stage's `CONTEXT.md` says exactly what to read and write.

| Stage | Job | Input | Output | Human check |
|---|---|---|---|---|
| `01_capture` | Run the fixed command list in a scratch worktree of `base` and of `head`, one agent each | the script args `base` and `head` | `output/<side>/<command-slug>.txt` | every command has an output file on both sides or a recorded failure |
| `02_diff` | Normalize noise and list every real difference between the two sides | `01_capture` output, both sides | `differences.md` | no difference dismissed as noise without the rule that removed it |
| `03_judge` | Mark each difference "expected from the move" or "needs a look" | `differences.md`, `git diff <base>...<head>` | `report.md` | every "needs a look" names a file:line or a command |

## How to start
`/restructure-check <pr|branch> [--base <ref>]` in the repo to run on. The starter skill
`claude-home/skills/restructure-check/SKILL.md` makes the run id, then runs `restructure-check.js` with the Workflow
tool. The run goes straight through; nothing asks you mid run. The script never pushes, merges or posts.

## Where runs write
`<repo>/.workflow/runs/restructure-check/<run id>/NN_<stage>/output/`, git ignored. Read each stage's output against its
human check after the run. Run folders stay until you delete them.

## Owner steps
- Before the run: name the PR number or the branch (and a base other than `origin/main`, if any).
- After the run: read the report. Nothing is pushed, merged or posted.
