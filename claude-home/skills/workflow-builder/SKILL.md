---
name: workflow-builder
description: Build or update an ICM style workflow - numbered stage folders with a contract each, one Workflow script that runs them straight through, and a /<name> command that starts it (spec 0076).
argument-hint: "<name> [--update]"
---
Build the workflow `<name>` (kebab case) the ICM way: numbered folders carry the order, each stage's `CONTEXT.md`
says exactly what to read and write, and one Workflow script runs the stages straight through. The owner reads the
outputs after the run; nothing asks mid run. Files go in the repo `~/claude-config` (linked live), never in
`~/.claude/workflows/` directly. Templates: `templates/` beside this file. Checker: `check.py` beside this file.

## 1. The name
- Refuse a name that is not kebab case (`^[a-z0-9]+(-[a-z0-9]+)*$`).
- Without `--update`, refuse when the name is already taken, and say where:
  `~/claude-config/claude-home/workflows/<name>`, `~/claude-config/claude-home/skills/<name>`,
  `~/.claude/skills/<name>`, `~/.claude/workflows/<name>` (`ls -d` each), or an entry in
  `~/claude-config/config/manifest.json` (`python3 -c "import json,sys; sys.exit(sys.argv[1] in json.load(open(sys.argv[2]))['entries'])" <name> ~/claude-config/config/manifest.json` exits 1 when taken).
- With `--update`, the folder `claude-home/workflows/<name>/` must exist; go to section 5.

## 2. The interview
One question at a time, each with your recommended answer first (`rules/plain-questions.md`). In order:
1. The job, and what done looks like.
2. One real run walked through, start to end.
3. The stages. Recommend 3 to 5: "three real stages beat seven imagined ones".
4. Per stage: the exact input paths (an earlier stage's output is `<run>/NN_<stage>/output/<file>`), the process,
   the one output, the one human check, what not to load, and model and effort. Recommend by the rule: haiku for
   lookup, sonnet for edits and review, opus for design and hard work; effort low to high.
5. Which stage fans out, and over what items (the earlier stage returns them as `items`). Recommend worktree
   isolation only when those agents edit files.
6. Owner steps before the run (questions, choices) and after it (push, merge, post, billing). These stay outside the
   script, in the starter skill: a script cannot ask anything and must not push, merge, post or bill.
7. The named `args` the script needs, and which answer from step 6 fills each before the run.

If the whole job fits one prompt (one stage, no fan out, nothing to hand between stages), say so and write a skill
instead of a workflow (ICM: "if the whole job fits in one saved prompt, don't build a workspace").

## 3. Write the files
From the templates, never from icm-architect's files. Strip the first line (`<!-- follows icm-architect ... -->` or
`// follows icm-architect ...`) from every file you write, and fill every `{{...}}`:
- `claude-home/workflows/<name>/CONTEXT.md` from `templates/CONTEXT.md`: the pipeline table (stage, job, input,
  output, human check; the first cell is the stage folder name in backticks), how to start, where runs write.
- `claude-home/workflows/<name>/stages/NN_<stage>/CONTEXT.md` from `templates/stage-CONTEXT.md`, one per stage:
  `Inputs`, `Process`, `Outputs`, `Human check` (exactly one line), `Do NOT load`, and `Model: <model> <effort>`.
  Add `stages/NN_<stage>/references/` only when the stage has reference files.
- `claude-home/workflows/<name>/<name>.js` from `templates/workflow.js`: meta phase titles equal to the stage folder
  names in order, one `phase()` per stage, and on every `agent()` the `label`, the stage's `model` and `effort`
  copied from its `Model:` line, and a `schema`. Keep the args check (`missing arg: <key>`) with every named arg.
  A fan out stage uses `pipeline()` over its items; drop `isolation: 'worktree'` and the branch lines when its
  agents only read. Results of `parallel()` and `pipeline()` are filtered for nulls and a failed item is logged.
- `claude-home/skills/<name>/SKILL.md` from `templates/starter-SKILL.md`: the owner steps, the run id, the
  `.workflow/` ignore check, the Workflow call, the after run listing.

## 4. Check, link, offer a dry run
1. Run `python3 ~/.claude/skills/workflow-builder/check.py <name>`. Fix every line it prints and run it again until
   it prints `ok`. Never report the workflow as built before that.
2. `python3 ~/claude-config/bin/claude-config.py docs` (the new starter skill changes `docs/guides/SKILLS.md`).
3. Link it live: show `python3 ~/claude-config/bin/claude-config.py install --dry-run`, and run it without
   `--dry-run` only on the owner's yes. It links `~/.claude/workflows/<name>` and `~/.claude/skills/<name>`.
4. Offer one dry run: `/<name> --limit 1` (one item of the fan out stage; a workflow with no fan out runs in full).
   Say that a run spends usage. Start it only on the owner's yes, then show each stage's outputs and human check.

## 5. Update mode (`--update`)
Reread `claude-home/workflows/<name>/` (root and stage `CONTEXT.md`, `<name>.js`) and
`claude-home/skills/<name>/SKILL.md`. Ask only what changes, one question at a time. Rewrite the touched files in
the repo copy, keep the Model lines and the script values equal, then run section 4 steps 1 and 2 again (the link
already exists). Every edit to a workflow, also one the owner asks for outside this skill, is made in
`claude-home/workflows/<name>/`; nothing writes to `~/.claude/workflows/` directly.

## Upstream
Each template's first line names the icm-architect commit it was last reviewed against. When
`claude-config.py drift` or `update --plan` prints `review workflow-builder templates`, read icm-architect at the
new pin (`~/.claude/skills/icm-architect`), carry over what applies, and update the follows lines to the new commit.
