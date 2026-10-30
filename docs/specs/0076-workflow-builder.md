# 0076. Workflow builder skill (ICM pipelines run as Claude Code workflows)

**Date**: 2026-10-22
**Status**: Proposed
**Paths:** `claude-home/skills/workflow-builder/**`, `claude-home/workflows/**`, `tools/bin/install.sh`, `tools/bin/claude-config.py`, `tools/config/manifest.json`, `tests/test_claude_config.py`

## What you're agreeing to
- `/workflow-builder <name>` interviews you, then writes an ICM pipeline: numbered stage folders with a contract each, one Workflow script that runs them straight through, and a thin `/<name>` command that starts it.
- Workflows live in `claude-home/workflows/`, linked live so they work in every repo; I edit the repo copy when you ask.
- Each run writes every stage's output in the repo it ran on (`.workflow/runs/`, ignored by git); you read them after the run.
- A checker refuses a workflow whose script and stage folders disagree or that breaks the Workflow rules.
- icm-architect is installed through the manifest; when its pin moves, `/claude-config update` tells you to review the builder's templates.

## Summary
The owner wants more workflows (review-fix, restructure-check, later marketing) made the ICM way (Interpretable Context Methodology: numbered folders carry the order, each stage's contract says exactly what to read and write). This skill makes one: it asks what the job is, writes the stage folders and the script, checks them, and links them live. It carries its own short templates; icm-architect is installed alongside so its updates can be compared.

## Context
Research: [workflow-templates.md](../briefs/workflow-templates.md). Owner answers: [workflow-builder.md](../briefs/workflow-builder.md). A Claude Code Workflow script cannot ask the owner anything mid run, has no file access, and must not call `Date.now()`, `Math.random()`, bare `new Date()` or `import()`. ICM is sequential and gated by a human per stage; the owner chose one script per workflow with the checks read after the run. Spec 0074 (build-features) keeps its own layout (script in its skill folder) and is not rebuilt by this skill.

## Requirements

**User stories**:
- As the owner, I want to describe a repeating job once and get a runnable ICM workflow and a `/<name>` command for it.
- As the owner, I want every workflow built the same way, checked, and updated when ICM itself changes.

**Acceptance criteria**:
- **AC-1** (interview): `/workflow-builder <name>` (kebab case; refused, unless `--update`, when `<name>` is already a folder in `claude-home/workflows/` or `claude-home/skills/`, a name in `~/.claude/skills/` or `~/.claude/workflows/`, or a `config/manifest.json` entry) asks, one question at a time with a recommended answer each: the job and what done looks like; one real run walked through; the stages (it recommends 3 to 5; "three real stages beat seven imagined ones"); per stage: exact input paths, the process, one output, the one human check, what not to load, and model and effort (recommended by the rule: haiku lookup, sonnet edits and review, opus design and hard work; effort low to high); which stage fans out and over what; which owner steps sit before or after the run (questions, push, merge, billing); the named `args` the script needs, filled from the owner's answers before the run. If the whole job fits one prompt, it says so and writes a skill instead (ICM "no build" rule).
- **AC-2** (files): it writes, from its own templates in `claude-home/skills/workflow-builder/templates/` (no file copied from icm-architect): `claude-home/workflows/<name>/CONTEXT.md` (pipeline table: stage, job, input, output, human check; how to start; where runs write); `claude-home/workflows/<name>/stages/NN_<stage>/CONTEXT.md` per stage with the sections `Inputs`, `Process`, `Outputs`, `Human check` (exactly one line), `Do NOT load`, and a line `Model: <model> <effort>`; `stages/NN_<stage>/references/` only when the stage has reference files; `claude-home/workflows/<name>/<name>.js`; `claude-home/skills/<name>/SKILL.md`.
- **AC-3** (script): `<name>.js` checks that every named arg from the interview is present and throws `missing arg: <key>` otherwise. It starts with a literal `export const meta = {name, description, phases}` whose phase titles equal the stage folder names `NN_<stage>`; one `phase()` per stage in order; each `agent()` call has `label`, the stage's `model` and `effort` (copied from its `Model:` line), and a `schema`; results of `parallel()` and `pipeline()` are filtered for nulls; a fan out stage uses `pipeline()` over its items and `isolation: 'worktree'` only when its agents edit files. Each agent prompt says: read `~/.claude/workflows/<name>/stages/NN_<stage>/CONTEXT.md`, the repo is `<args.repo>`, the run id is `<args.runId>`, write outputs to `<args.repo>/.workflow/runs/<name>/<args.runId>/NN_<stage>/output/`, then return the schema. Each stage's `Inputs` line names the earlier stage's output files by their run path (`<run>/01_<stage>/output/<file>`), and the script also passes the earlier stage's schema summary into the next prompt. An agent with `isolation: 'worktree'` commits its code on a branch `wf/<name>-<runId>-<stage>` and writes its outputs to the main repo's absolute run path; pushing and merging those branches stays with the owner. The script returns one summary object per stage, with any branches.
- **AC-4** (starter skill): `claude-home/skills/<name>/SKILL.md` runs the owner steps listed before the run, makes the run id (`YYYYMMDD-HHMMSS`, local time), checks `git check-ignore -q .workflow/x` in the repo and, when it is not ignored, adds `.workflow/` to that repo's `.git/info/exclude`; calls the Workflow tool with `scriptPath` `~/.claude/workflows/<name>/<name>.js` and `args` `{repo, runId, limit, ...named args}` (`--limit 1` runs one item of a fan out stage; `limit` is null otherwise); then lists each stage's output folder, its human check and any `wf/...` branches for the owner, says how many run folders this workflow has kept (kept until the owner deletes them), and runs the owner steps listed after the run.
- **AC-5** (check): `python3 ~/.claude/skills/workflow-builder/check.py <name>` exits 1 with one line per problem, else prints `ok` and exits 0. It reads the script with `node --check` for syntax and a small node helper that walks the code (comments and strings skipped) to find the `meta` object and each `agent(` call across lines. Problems: meta not a literal or phase titles not equal to the stage folders in order; `Date.now(`, `Math.random(`, `new Date()` or `import(` in the script; an `agent(` call without `schema`, `label`, `model` or `effort`; a `Model:` line that differs from the script's values for that stage; a stage CONTEXT.md missing a section or with other than one `Human check` line; an input path under `claude-home/` or `~/.claude/` that does not exist (`~/.claude/workflows/...` resolved to the repo copy; paths holding `<` or `{` or under `.workflow/runs/` skipped); the root CONTEXT.md plus the largest stage CONTEXT.md over 8,000 tokens (characters / 4; `references/` files are left out on purpose); a stage folder named in the root table but missing, or the reverse. The builder runs it after writing and fixes every problem before it reports. `check.py --test` has one fixture per problem, each mutation checked.
- **AC-6** (link): `bin/install.sh` adds `workflows` to its live folder `mkdir` list (`bin/install.sh:37`) and a link loop like the skills one (`:65`), linking each `claude-home/workflows/<name>` to `~/.claude/workflows/<name>`; `bin/claude-config.py` `linked_kind` learns `workflows` (no manifest entries, label `workflow`) and `drift()` calls it beside skills and commands; a real folder already at `~/.claude/workflows/<name>` is reported by drift as `in the repo, but live is not a link to it`, never skipped silently. Tests in `tests/test_claude_config.py` (the path after spec 0072a moves the tests).
- **AC-7** (edits): `/workflow-builder <name> --update` rereads the existing folder, asks only what changes, rewrites, and reruns the check. Any edit to a workflow is made in `claude-home/workflows/<name>/` (the live folder through the link) when the owner asks; nothing writes to `~/.claude/workflows/` directly.
- **AC-8** (dry run): after a new workflow passes the check, the builder offers one run with `--limit 1` (one item of its fan out; a workflow with no fan out runs in full) and shows the outputs; the run starts only on the owner's yes (a run spends usage).
- **AC-9** (icm-architect installed): first, a scan and install step: `skillspector scan --no-llm` of a fresh clone, then a full `config/manifest.json` entry like the others (`source` `github:RinDig/icm-architect`, `kind` `skill`, `fetch` `git`, `path` and `install` as the clone shows them, `license`, `pinned` commit, `base_hash`, `status` `downloaded`, `publish`, `description`), added through `/claude-config`; `bin/claude-config.py build` installs it (run by the owner with `!` when the sandbox denies GitHub).
- **AC-10** (upstream check): every template file of the builder starts with a follows line, `<!-- follows icm-architect <commit> -->` (`// follows icm-architect <commit>` in the `.js` template), the commit reviewed last; the builder strips that line from every file it writes. A check run by both `bin/claude-config.py drift` and `update --plan` (separate from the upstream hash check, so it stays until the review) compares each follows commit with the manifest `pinned` commit and prints `review workflow-builder templates: they follow icm-architect <old>, the pin is <new>`; with no `icm-architect` entry it prints `icm-architect not installed, templates not compared`. After the review the follows lines are updated. Test in `tests/test_claude_config.py`.

## Amendment 2026-10-30: port to icm-architect 8bc2f56 (row 123)
Owner answer 2026-10-29: port the templates, do not stay on `e16cafe` (brief general D8). The owner asked to finish without him, so the four choices below are the recommended ones. Paths: `claude-home/skills/workflow-builder/**`, `claude-home/workflows/**`, `tests/test_claude_config.py`.

What you're agreeing to:
- Every template's follows line names `8bc2f5610d3843b3ffa31a142effe6b6337fef3c`, so drift stops saying "review workflow-builder templates".
- The stage section `Human check` becomes `Check`: one line naming who checks (a person, a script or a small model). A check that is not a person writes `check.md` whose first line is `pass` or `fail: <why>`; this is wording in the template only, the script does not gate on it.
- The root pipeline table becomes `Stage | Job`; inputs and outputs stay in each stage's CONTEXT.md.
- Each stage's Process starts with "If an input is missing or empty, stop and say which."
- `Do NOT load` stays its own section (upstream moved it into Inputs; ours keeps it separate so `check.py` can require it).
- Not taken: upstream's AGENTS.md entry file, scripts folder and examples.

Changed criteria: **AC-1** asks for "the one check" (who checks) instead of "the one human check". **AC-2** root table `Stage | Job`; stage sections `Inputs`, `Process`, `Outputs`, `Check` (exactly one line), `Do NOT load`, `Model:`. **AC-4** lists each stage's check line. **AC-5** "other than one `Check` line"; the root table check reads the `Stage` column. review-fix and restructure-check are rewritten to the new shape and pass `check.py`.

## Decision
**Chosen option**: our own builder skill with ICM stage folders and one Workflow script per workflow, linked live from `claude-home/workflows/`, with icm-architect installed beside it for upstream comparison.

## Options considered
- **Own builder plus icm-architect for comparison (chosen, owner's "both")**: fits our script, skill and Model lines; ICM changes still surface. Con: two skills to keep in mind.
- **Call icm-architect's Build mode**: exact ICM. Con: its output must be adapted every run; it knows nothing of scripts.
- **A single process card in `map/processes/`**: fewer files. Con: the owner wants the classic stage folders.

## Rationale
The owner chose the ICM stage folder tree for clarity and token use, the shared `claude-home/workflows/` so every repo gets the same workflows, one script per workflow so runs finish while away, per stage Model lines, and run outputs in the repo they belong to. The builder's job is mostly ours (script, starter skill, checks), so its own templates fit; the owner also wanted ICM updates noticed, which the manifest pin plus the template header line does without copying upstream files (AGENTS.md bans copying a downloaded skill). Recommended without asking: the run id made by the starter skill (a script cannot read the clock); the 8,000 token cap (ICM's 2,000 to 8,000 per stage context); one schema per agent and null filtering (every public template does it); the dry run gated on a yes (runs spend usage).

## Feature design
**Data model** (owner approved 2026-10-22): the file layout in AC-2 and the run outputs `<repo>/.workflow/runs/<name>/<runId>/NN_<stage>/output/`.

**Value sourcing**: stage names, inputs, outputs, checks: the interview; model and effort: the interview, by the rule; run id: the starter skill; repo: the starter skill (`git rev-parse --show-toplevel`); icm-architect commit: `config/manifest.json` `pinned`.

**Security model**: the script runs on the session's permissions; owner steps that push, merge, post or bill stay outside it (AC-1, AC-4).

**Critical test scenarios**: in AC-5, AC-6 and AC-10.

## Build plan
Build after spec 0072a (row 97: `tests/` move, `bin/install.sh`), spec 0070 and 0075 (rows 92, 87: `bin/claude-config.py`), spec 0073 (row 98: `bin/install.sh`). No stacking.
1. Templates and `check.py` with `--test`, satisfies **AC-2**, **AC-3**, **AC-5**.
2. The skill: interview, writing, check run, update mode, dry run offer, satisfies **AC-1**, **AC-4**, **AC-7**, **AC-8**.
3. `bin/install.sh` link and drift kind with tests, satisfies **AC-6**.
4. icm-architect manifest entry, scan, build (owner runs with `!` if needed), the template header lines and the update plan line with its test, satisfies **AC-9**, **AC-10**.
5. Proof: build `review-fix` (row 102) with it, which also checks AC-1 to AC-8 on a real case.

## Consequences
**Positive**: every workflow has the same shape, a checked script, and a command; ICM changes are noticed.

**Negative / tradeoffs**: checks happen after the run, not between stages; the Model values live in two places (kept equal by the check); two linked folders per workflow; icm-architect must be scanned and pinned like any download.

**Neutral**: spec 0074 build-features keeps its own layout; work outside repos (marketing, publicity) is later and will need a run output place outside `.workflow/`.
