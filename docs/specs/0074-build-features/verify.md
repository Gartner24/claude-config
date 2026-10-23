# 0074 probes

## P1 a mod sees workflow agents (2026-10-22) - PASS
Full record in [the brief](../../briefs/build-features.md). A test mod logged `agent.spawn` with `workflow: {runId, agentIndex}` for both agents of a 2 agent Haiku workflow, and `turn.complete` with each `agentId`.

## P2 workflow agents in the agent panel (2026-10-22) - FAIL, AC-11 dropped
Live `subagentStatusLine` set to a capture script, then a workflow run with agents labelled `row 1 · probe`, `row 2 · probe` (and `row 3 · probe` for P3). The script was called 14 times and its `tasks[]` held only Agent tool subagents (labels such as "Probing block-destructive.sh edge cases"); no call carried a workflow agent label (`grep -c probe` = 0). Workflow agents get no agent panel row, so AC-11 is dropped and the band count (AC-12) is the only view, as the brief allows. The probe line was removed from live settings after the run.

## P2 original plan
Docs (code.claude.com statusline page, "Subagent status lines") give the `tasks[]` fields (`id`, `label`, `description`, `status`, `model`, `effort`) but do not say whether Workflow `agent()` calls get rows. Set a `subagentStatusLine` command that appends its stdin to a file, run a 2 agent workflow with labels `row 1 · probe` and `row 2 · probe`, and check that both appear in `tasks[]` with those labels. A FAIL drops AC-11 (the band count alone stays, as the brief allows).

## P3 a worktree workflow agent can build and push (2026-10-22) - PASS
Run in claude-config itself (owner answer: a worktree agent always copies the chat's own repo, so a scratch repo would need a separate chat). First launch refused by the auto mode classifier; the owner added `Workflow` to the live allow list. Then one `agent()` with `isolation: 'worktree'`: Skill tool (`ponytail:ponytail-help`) ok, file edit ok, commit ok (hooks ran, no `--no-verify`), `git -c protocol.version=0 push -u origin HEAD:probe/p3` ok, `gh pr create --draft` ok (PR #198, closed and branch deleted right after). Prompts seen: none.

## P3 original plan
On a scratch GitHub repo of the owner: one `agent()` with `isolation: 'worktree'` invokes a skill (Skill tool), edits a file, commits, pushes a branch and runs `gh pr create --draft`. Record whether a permission prompt appears and where. A FAIL goes back to `/architect`.
