# 0074 rationale

## Context
Building several ready scope rows at once is a hand recipe today (`rules/when-to-switch-on.md` rows 31 and 32): start one worktree agent per row, check free memory, compare spec Paths by eye, pick a model per agent. The retired runner did this in code. The owner asked for a saved workflow, `build-features`, plus a view of what runs, in the agent panel and on the chip band. All owner answers are in [the brief](../../briefs/build-features.md).

## Options considered
### Option 1: skill for the conversation, Workflow script for the fan out (chosen)
**Pros**: the panel and the review loop can ask the owner; the parallel part is deterministic. **Cons**: two pieces to keep in step.

### Option 2: one saved workflow does everything
**Pros**: one file. **Cons**: a workflow script cannot ask a question, so the pick panel and the CAUTION stop are impossible inside it.

### Option 3: the chat starts Agent tool calls itself, no workflow
**Pros**: no new tool. **Cons**: the order and limits depend on the model each time, the thing the owner wanted out of chat text.

## Rationale
The owner picked a list to tick, model per row proposed in that list, drafts pushed on the tick, and `/review` before an automatic merge. Those need the owner in the loop at two points, which a Workflow script cannot do, so the conversation parts sit in a skill and only the parallel build is a script. The script lives in the skill folder and runs by `scriptPath`, because a user level saved workflow folder (`~/.claude/workflows/`) does not exist here and its loading was not probed.

Recommended without asking: the step file for the panel (the only way a running agent can tell the panel which step it is on; runner up: the panel shows the row only); 3 rows per question (the panel hook allows at most 3 options); the band word `build` (it reads as what runs; runner up `wf`, which collides with the retired runner's name); reviews one after another (merges must be one at a time anyway).
