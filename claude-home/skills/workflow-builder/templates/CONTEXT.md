<!-- follows icm-architect e16cafe6a664dcf6d787a726b452adba77d913f4 -->
# {{name}}

{{The job in one or two sentences, and what done looks like.}}

## Pipeline
Numbered folders carry the order; each stage's `CONTEXT.md` says exactly what to read and write.

| Stage | Job | Input | Output | Human check |
|---|---|---|---|---|
| `01_{{stage}}` | {{job}} | {{input}} | {{output file}} | {{the one check}} |
| `02_{{stage}}` | {{job}} | `01_{{stage}}` output | {{output file}} | {{the one check}} |

## How to start
`/{{name}} {{named args}}` in the repo to run on (`--limit 1` runs one item of the fan out stage). The starter skill
`claude-home/skills/{{name}}/SKILL.md` makes the run id, then runs `{{name}}.js` with the Workflow tool. The run goes
straight through; nothing asks you mid run.

## Where runs write
`<repo>/.workflow/runs/{{name}}/<run id>/NN_<stage>/output/`, git ignored. Read each stage's output against its
human check after the run. Run folders stay until you delete them.

## Owner steps
- Before the run: {{questions, choices; or "none"}}
- After the run: {{push, merge, post, billing; or "none"}}
