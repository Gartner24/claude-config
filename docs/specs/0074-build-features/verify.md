# 0074 probes

## P1 a mod sees workflow agents (2026-10-22) - PASS
Full record in [the brief](../../briefs/build-features.md). A test mod logged `agent.spawn` with `workflow: {runId, agentIndex}` for both agents of a 2 agent Haiku workflow, and `turn.complete` with each `agentId`.

## P2 workflow agents in the agent panel (2026-10-22) - FAIL, AC-11 dropped
Live `subagentStatusLine` set to a capture script, then a workflow run with agents labelled `row 1 · probe`, `row 2 · probe` (and `row 3 · probe` for P3). The script was called 14 times and its `tasks[]` held only Agent tool subagents (labels such as "Probing block-destructive.sh edge cases"); no call carried a workflow agent label (`grep -c probe` = 0). Workflow agents get no agent panel row, so AC-11 is dropped and the band count (AC-12) is the only view, as the brief allows. The probe line was removed from live settings after the run.

## P2 original plan
Docs (code.claude.com statusline page, "Subagent status lines") give the `tasks[]` fields (`id`, `label`, `description`, `status`, `model`, `effort`) but do not say whether Workflow `agent()` calls get rows. Set a `subagentStatusLine` command that appends its stdin to a file, run a 2 agent workflow with labels `row 1 · probe` and `row 2 · probe`, and check that both appear in `tasks[]` with those labels. A FAIL drops AC-11 (the band count alone stays, as the brief allows).

## P3 a worktree workflow agent can build and push (2026-10-22) - PASS
Run in claude-config itself (owner answer: a worktree agent always copies the chat's own repo, so a scratch repo would need a separate chat). First launch refused by the auto mode classifier; the owner added `Workflow` to the live allow list. Then one `agent()` with `isolation: 'worktree'`: Skill tool (`ponytail:ponytail-help`) ok, file edit ok, commit ok (hooks ran, no `--no-verify`), `git -c protocol.version=0 push -u origin HEAD:probe/p3` ok, `gh pr create --draft` ok (PR #198, closed and branch deleted right after). Prompts seen: none.

## AC-11 dropped (2026-10-22)
P2 failed, so AC-11 (the agent panel script `subagent-statusline.py` and its `subagentStatusLine` settings entry) is
not built: no hook file, no settings entry, no `COPIED_FILES` line. The chip band count (AC-12) is the only view. The
`.step` files are still written by each agent (AC-6); nothing reads them yet.

## P3 original plan
On a scratch GitHub repo of the owner: one `agent()` with `isolation: 'worktree'` invokes a skill (Skill tool), edits a file, commits, pushes a branch and runs `gh pr create --draft`. Record whether a permission prompt appears and where. A FAIL goes back to `/architect`.

# Verify: build-features · spec 0074 · updated 2026-10-22
_Steps derived from the acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._
## Commands
- [x] `python3 -B tests/fast.py test_build_features` -> 9 ok -> AC-1, AC-2, AC-5, AC-6, AC-8. can fail: a script without `isolation: 'worktree'` (KeyError, red), ready.py offering a `needs a decision` row (test_ready_list red) or ignoring an existing `feat/NNNN-*` branch (test_clashes red); run 2026-10-22
- [x] `claude plugin test claude-home/mods/chip-dash` -> 85 pass incl. the `build` band tests and the register count test -> AC-12. can fail: never dropping a workflow agent after 2 hours (band test red), or counting a plain subagent (register test red); run 2026-10-22
- [x] `python3 -B tests/fast.py` -> 167 ok, whole suite -> regression. can fail: any suite test broken by this diff; run 2026-10-22
## UI / manual (not run: a real run builds against live repos; read SKILL.md and build-features.js instead)
- [ ] `/build-features` with two non overlapping ready rows: pick panel, one Workflow run, band `build 2` then nothing -> AC-3, AC-5, AC-12 (manual)
- [ ] `start-gates` saying `wait:` lists the later rows as `not started` -> AC-4 (manual; SKILL.md step 4 matches the spec text)
- [ ] An APPROVE PR with every checklist item merges; a CAUTION one stays a draft -> AC-9; a work origin lists the PRs with no review -> AC-10 (manual; SKILL.md step 6 matches the spec text)
- [ ] `rules/when-to-switch-on.md` row 31 says to run `/build-features` -> AC-13: repo copy done (line 7); live copy and `bin/sync.sh` run after merge, by design
## Value sourcing
- ready rows: a `needs a design` row and a `· needs a decision` tagged row are left out (test_ready_list)
- clashes: `spec-paths --overlap` exit 1 shows the pair (test_clashes); a failed `gh pr list` says so on each row (test_pr_list_failed)
- tier: the row's `· GA` tag beats the header's `Beta` (test_ready_list)
- branch name: `feat/NNNN-<slug>`, `fix/` for a "Fix" heading, from the args, never the agent (test_results)
- band count: spawn, spawn, complete gives `build 1`; 2 hours with no end drops one (register.test.ts, band.test.ts)
## Acceptance-criteria coverage
- AC-1, AC-2: ready.py, tests above · AC-3, AC-4, AC-9, AC-10: SKILL.md steps 3, 4, 6, manual · AC-5 to AC-8: build-features.js, tests above · AC-11: dropped (P2) · AC-12: chip-dash band and register · AC-13: rule line
