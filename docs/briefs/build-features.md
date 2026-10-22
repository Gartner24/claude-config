# build-features workflow (scope row 100)

## Agreed so far, do not ask again
- From [icm-restructure.md](icm-restructure.md) (owner, 2026-10-22): build `build-features` first, a saved Claude Code workflow that builds every ready scope row whose questions are answered, one worktree agent each, model and effort per row. Running agents show in both places: the agent panel (`subagentStatusLine`, one row per agent with its scope row and step) and a short count on the chip band.
- 2026-10-22: owner approved the probe (a test mod plus a 2 agent Haiku workflow) and it passed, see below. The band count is possible, so the "agent panel only" fallback is not needed.
- 2026-10-22: one run shows the ready rows (next box a Build it `/develop` box, design ticked, no needs a decision tag) with their Paths clashes, the owner ticks which to build, then only those start.
- 2026-10-22: each agent ends by pushing a draft PR; ticking a row in the pick panel is the push yes. Then whatever is safe and ready is merged without asking (owner: "Push drafts and what is safe and ready you can merge it"): the self merge checklist in rules/when-to-switch-on.md row 38 (own or personal repos only, never work or client; verify and test boxes ticked; suite green on the PR head; all checks green; squash with --match-head-commit, one PR at a time).
- 2026-10-22: before the automatic merge, the main chat runs /review (jjstack) on each draft PR in turn, fixes the fix now findings (rules/review-fix.md), and merges only an APPROVE that also passes the self merge checklist; CAUTION or REJECT waits for the owner.
- 2026-10-22: model and effort per row are proposed by the main chat in the pick list, each with a one line reason, by the rule (haiku lookup, sonnet edits and review, opus design and hard work; effort low to high); the owner changes one by typing in the panel Other box.
- 2026-10-22: data model approved: `~/.claude/state/build-features/<run id>/row-<n>.step`, one word (develop, verify, test, pr), written by the agent before each step, read by the panel script; run folders older than 7 days deleted when /build-features starts.
- 2026-10-22: spec 0074 written; cross check (Sonnet) found 17 points, owner picked "apply the recommended fixes": ready also needs not deferred, no needs a decision tag, a spec; rows with an existing branch or PR are "already in progress"; panel labels are row number plus 3 words; owed decisions return skipped; review rounds capped at 2; gh pr ready before merge; probe P3 (worktree agent builds and pushes) before code.

## Probe: a mod sees workflow agents (2026-10-22) - PASS
Test mod `wfprobe` (session dev-mods folder, removed after) hooked `agent.spawn` and `turn.complete` and wrote each to a file. Workflow run `wf_60d337e3-a1d`, two Haiku agents, `parallel`.
- `agent.spawn` fired twice with `workflow: {runId: "wf_60d337e3-a1d", agentIndex: 1}` and `agentIndex: 2`, `agentId` `abc1cb7538d5474f7` and `ac7ef32b5fbf07cd6`.
- `turn.complete` fired with each of those two `agentId`s, plus one with no `agentId` (the main chat's turn).
- Docs: `$.agent.list()` leaves workflow agents out (`claude-code.d.ts:3274` on 2.1.308), so a count must come from these two events.
