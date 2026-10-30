<!-- follows icm-architect 8bc2f5610d3843b3ffa31a142effe6b6337fef3c -->
# {{name}}

{{The job in one or two sentences, and what done looks like.}}

## Pipeline
Numbered folders carry the order; each stage's `CONTEXT.md` says exactly what to read, write and check.

| Stage | Job |
|---|---|
| `01_{{stage}}` | {{job}} |
| `02_{{stage}}` | {{job}} |

## How to start
`/{{name}} {{named args}}` in the repo to run on (`--limit 1` runs one item of the fan out stage). The starter skill
`claude-home/skills/{{name}}/SKILL.md` makes the run id, then runs `{{name}}.js` with the Workflow tool. The run goes
straight through; nothing asks you mid run.

## Where runs write
`<repo>/.workflow/runs/{{name}}/<run id>/NN_<stage>/output/`, git ignored. A stage is done when its `output/` holds
its file and any `check.md` there says `pass`; read each output against its stage's check after the run. Run folders
stay until you delete them.

## Owner steps
- Before the run: {{questions, choices; or "none"}}
- After the run: {{push, merge, post, billing; or "none"}}
