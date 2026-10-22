# 0074 probes

## P1 a mod sees workflow agents (2026-10-22) - PASS
Full record in [the brief](../../briefs/build-features.md). A test mod logged `agent.spawn` with `workflow: {runId, agentIndex}` for both agents of a 2 agent Haiku workflow, and `turn.complete` with each `agentId`.

## P2 workflow agents in the agent panel - owed, build step 1
Docs (code.claude.com statusline page, "Subagent status lines") give the `tasks[]` fields (`id`, `label`, `description`, `status`, `model`, `effort`) but do not say whether Workflow `agent()` calls get rows. Set a `subagentStatusLine` command that appends its stdin to a file, run a 2 agent workflow with labels `row 1 · probe` and `row 2 · probe`, and check that both appear in `tasks[]` with those labels. A FAIL drops AC-11 (the band count alone stays, as the brief allows).

## P3 a worktree workflow agent can build and push - owed, build step 1
On a scratch GitHub repo of the owner: one `agent()` with `isolation: 'worktree'` invokes a skill (Skill tool), edits a file, commits, pushes a branch and runs `gh pr create --draft`. Record whether a permission prompt appears and where. A FAIL goes back to `/architect`.
