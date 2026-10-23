---
name: restructure-check
description: Prove a restructure PR changes no behavior by capturing outputs on base and head, diffing them and judging the differences. Runs the restructure-check workflow (stage folders in ~/.claude/workflows/restructure-check).
argument-hint: "<pr|branch> [--base <ref>]"
---
Start the `restructure-check` workflow (spec 0076). Its stages and their checks: `~/.claude/workflows/restructure-check/CONTEXT.md`.

1. Before the run: take the PR number or branch from the argument (ask if missing). A PR number: run
   `git -C <repo> fetch origin pull/<n>/head:refs/restructure-check/pr-<n>` and use that ref as `head`. A branch:
   `git check-ref-format --branch <branch>` must pass (refuse on failure), use it as `head`. `base` is the `--base`
   value, else `origin/main`; `git -C <repo> rev-parse --verify <base>` must pass.
   The answers fill the named args: `head`: the ref above; `base`: the base ref; `run`: the run id from step 2.
2. Repo: `git rev-parse --show-toplevel` (absolute). Run id: `date +%Y%m%d-%H%M%S` (local time).
3. Keep runs out of git: `git -C <repo> check-ignore -q .workflow/x`. When it exits non zero, append the line
   `.workflow/` to the file `git -C <repo> rev-parse --git-path info/exclude` names (relative paths are under `<repo>`).
4. Call the Workflow tool with `scriptPath` `~/.claude/workflows/restructure-check/restructure-check.js` and `args`
   `{repo, runId, limit, head, base, run}`: `limit` is `1` when the user typed `--limit 1`, else `null`.
5. After the run, for each stage show its output folder `<repo>/.workflow/runs/restructure-check/<run id>/NN_<stage>/output/`,
   the line under `## Human check` in `~/.claude/workflows/restructure-check/stages/NN_<stage>/CONTEXT.md`, and any `wf/...`
   branches the run returned. Say any stage marked `failed`. Count the folders in `<repo>/.workflow/runs/restructure-check/` and
   say "<n> run folders kept until you delete them".
6. After the run: show `03_judge/output/report.md`, verdict line first. Push, merge and post nothing.
