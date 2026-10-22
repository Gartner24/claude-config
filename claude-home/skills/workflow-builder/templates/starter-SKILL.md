<!-- follows icm-architect e16cafe6a664dcf6d787a726b452adba77d913f4 -->
---
name: {{name}}
description: {{What the workflow does, one sentence.}} Runs the {{name}} workflow (stage folders in ~/.claude/workflows/{{name}}).
argument-hint: "[--limit 1] {{named args}}"
---
Start the `{{name}}` workflow (spec 0076). Its stages and their checks: `~/.claude/workflows/{{name}}/CONTEXT.md`.

1. Before the run: {{each owner step before the run: a question with a recommended answer, a choice; or "none"}}.
   The answers fill the named args: {{named arg}}: {{where its value comes from}}.
2. Repo: `git rev-parse --show-toplevel` (absolute). Run id: `date +%Y%m%d-%H%M%S` (local time).
3. Keep runs out of git: `git -C <repo> check-ignore -q .workflow/x`. When it exits non zero, append the line
   `.workflow/` to the file `git -C <repo> rev-parse --git-path info/exclude` names (relative paths are under `<repo>`).
4. Call the Workflow tool with `scriptPath` `~/.claude/workflows/{{name}}/{{name}}.js` and `args`
   `{repo, runId, limit, {{named args}}}`: `limit` is `1` when the user typed `--limit 1`, else `null`.
5. After the run, for each stage show its output folder `<repo>/.workflow/runs/{{name}}/<run id>/NN_<stage>/output/`,
   the line under `## Human check` in `~/.claude/workflows/{{name}}/stages/NN_<stage>/CONTEXT.md`, and any `wf/...`
   branches the run returned. Say any stage marked `failed`. Count the folders in `<repo>/.workflow/runs/{{name}}/` and
   say "<n> run folders kept until you delete them".
6. After the run: {{each owner step after the run: push, merge, post, billing; each asks first; or "none"}}.
