---
name: restructure-check
description: Prove a restructure PR changes no behavior by capturing outputs on base and head, diffing them and judging the differences. Runs the restructure-check workflow (stage folders in ~/.claude/workflows/restructure-check).
argument-hint: "<pr|branch> [--base <ref>]"
---
Start the `restructure-check` workflow (spec 0076). Its stages and their checks: `~/.claude/workflows/restructure-check/CONTEXT.md`.

1. Before the run: take the PR number or branch from the argument (ask if missing). A PR number: run
   `git -C <repo> fetch origin pull/<n>/head:refs/restructure-check/pr-<n>` and use that ref as `head`. A branch:
   `git check-ref-format --branch <branch>` must pass (refuse on failure), use it as `head`. `base` is the `--base`
   value, else `origin/main`; `git -C <repo> rev-parse --verify <base>` must pass. Then `git -C <repo> fetch origin` and
   use the full sha from `git -C <repo> merge-base <base> <head>` as `base`, so unrelated main commits are not diffed.
   The workflow runs the head's own code (install dry run, tests, self checks), so it only runs on your own PRs: for
   a PR number, `gh pr view <n> --json author --jq .author.login` must equal `gh api user --jq .login`; a branch must
   be a local branch (`git show-ref --verify refs/heads/<branch>`). Otherwise stop and say "restructure-check runs
   the head's code; it only runs on your own PRs". Run this check before the fetch.
   Trust model: the workflow runs the PR's own code, so it is for the owner's own PRs only.
   After the fetch, `headSha` = `git -C <repo> rev-parse <head>` (full 40 hex). Pass `ownerChecked: true` only after the
   author check above passed. The script refuses unless `head` is `refs/heads/<x>` or `refs/restructure-check/pr-<n>`
   (use the full ref names), `headSha` and `base` are 40 hex shas, and `ownerChecked` is true.
   The answers fill the named args: `head`: the ref above; `headSha`; `ownerChecked`; `base`: the base sha.
   The capture stage contract a run uses is the live (main) copy: when the PR touches
   `claude-home/workflows/restructure-check/`, say that the run used the old contract.
2. Repo: `git rev-parse --show-toplevel` (absolute). Run id: `date +%Y%m%d-%H%M%S` (local time).
3. Keep runs out of git: `git -C <repo> check-ignore -q .workflow/x`. When it exits non zero, append the line
   `.workflow/` to the file `git -C <repo> rev-parse --git-path info/exclude` names (relative paths are under `<repo>`).
4. Call the Workflow tool with `scriptPath` `~/.claude/workflows/restructure-check/restructure-check.js` and `args`
   `{repo, runId, head, headSha, ownerChecked, base}`.
5. After the run, for each stage show its output folder `<repo>/.workflow/runs/restructure-check/<run id>/NN_<stage>/output/`,
   the line under `## Human check` in `~/.claude/workflows/restructure-check/stages/NN_<stage>/CONTEXT.md`, and any `wf/...`
   branches the run returned. Say any stage marked `failed`. Count the folders in `<repo>/.workflow/runs/restructure-check/` and
   say "<n> run folders kept until you delete them".
6. After the run: write the `report` field of the `03_judge` stage result, as returned, to
   `<repo>/.workflow/runs/restructure-check/<run id>/03_judge/output/report.md` (the judge agent cannot write it), then show
   it, verdict line first. Push, merge and post nothing.
