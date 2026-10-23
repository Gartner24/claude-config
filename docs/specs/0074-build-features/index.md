# 0074. build-features: build ready rows in parallel, shown while they run

**Date**: 2026-10-22
**Status**: In Progress
**Paths:** `claude-home/skills/build-features/**`, `claude-home/hooks/subagent-statusline.py`, `claude-home/settings.json`, `claude-home/mods/chip-dash/**`, `claude-home/rules/when-to-switch-on.md`, `bin/claude-config.py`

## What you're agreeing to
- You type `/build-features` in a repo. It lists the rows ready to build, with clashes and a proposed model per row; you tick which to start.
- Each ticked row is built by its own agent in its own worktree, through `/develop`, `/check verify` and `/test`, and ends as a draft PR. Your tick is the push yes.
- After that, this chat runs `/review` on each PR and merges only an APPROVE that passes your self merge checklist (own repos only). CAUTION or REJECT waits for you.
- While they run, the agent panel shows `row 98 · test` style rows, and the chip band shows `build 2`.
- It needs row 98's `start-gates` and `spec-paths --overlap` and row 93's dashboard, so it is built after both merge.

## Summary
Today, building several scope rows at once means starting worktree agents by hand, checking memory and file clashes by eye, and watching a generic agent list. `/build-features` is a skill that finds the ready rows, asks you which to build, and starts one Claude Code workflow (a script that runs many agents) with one worktree agent per row. Each agent ends at a draft PR. The chat then reviews and merges what is safe. The agent panel and the chip band show what is running.

## Requirements

**User stories**:
- As the owner, I want one command that builds every ready row I pick, in parallel, safely, so I stop starting agents by hand.
- As the owner, I want to see which rows are building and at which step without opening anything.

**Acceptance criteria**:
- **AC-1** (ready list): `/build-features` runs `python3 ~/.claude/skills/chip-dash/plan.py` and takes the one `repos` entry whose `path` equals the realpath of `git rev-parse --show-toplevel`; other repos are ignored. A feature is ready when its `state` is `ready to build`, `deferred` is false, its raw heading has no `needs a decision` tag, and `specStatus` is `Proposed`, `In Progress` or `Accepted`. The row number is the heading's leading number (`98.` in `98. Helper scripts ...`; `bare()` keeps it). A ready feature with no linked spec is listed as `no spec, not offered`. No ready row: it says `no ready rows` and stops.
- **AC-2** (clashes): for each pair of ready rows it runs `spec-paths --overlap A B`. For each ready row and each open PR of this repo (`gh pr list --json number,headRefName`): a head branch `feat/NNNN-*` or `fix/NNNN-*` is checked against spec `NNNN`; any other head branch is an unknown clash (`may clash with PR #<n>, branch has no spec number`). A ready row whose own branch (`feat/NNNN-*` or `fix/NNNN-*` for its spec, local or on origin) or PR already exists is listed as `already in progress` and not offered; this also covers a crashed run and two runs at once.
- **AC-3** (pick): it asks with multiSelect question panels that pass `claude-home/hooks/plain-panel.py`: 3 rows per question, up to 4 questions (at most 12 rows; more are listed in chat as `not offered this run: rows ...`). Each label is `row <n>` plus the first 3 words of the heading, the first label of each question ending ` (Recommended)`; each description (6 to 30 words, no spec numbers or AC codes) is the proposed model and effort with a short reason, by the rule (haiku lookup, sonnet edits and review, opus design and hard work; effort low to high, never above high), plus any clash note. The owner changes a model by typing in the panel's Other box (`row 92 sonnet medium`). After all answers, the chat checks clashes across every pick; a clashing pair is asked again alone.
- **AC-4** (start gates): for the picked rows it runs `start-gates --running <k>` for k = 0, 1, ... before adding each row; on `wait`, the rest are listed as `not started: <reason>` (an unknown 5 hour use says so plainly) and are not started this run. Every started agent gets the cores line of the final call, `start-gates --running <total - 1>`, as its suite core count.
- **AC-5** (run): it starts one Workflow call with `scriptPath` `~/.claude/skills/build-features/build-features.js` (a file in the skill folder, not a saved workflow: no user level workflow folder exists here and its loading was not probed) and `args` = the started rows (`row`, `feature` heading text, `spec`, `model`, `effort`, `cores`, `tier`, `base` branch). The script runs one `agent()` per row with `isolation: 'worktree'`, the row's `model` and `effort`, `label` `row <n> · <heading, cut to 30 characters>`, and its run id written into the prompt; all in parallel (no barrier between rows). The tier is read by the skill: the feature's own heading tag (`· GA`, `· Beta`, ...) first, else the scope header `**Workflow:**` line.
- **AC-6** (agent chain): each agent runs, in its worktree: `/develop <feature>`, then the tier chain (Alpha: `/check verify`; Beta: plus `/test`; GA: plus `/review` and `/document`), squashes to one Conventional Commit on branch `feat/NNNN-<slug>` per `rules/branch-pr.md`, pushes, and opens a draft PR with `gh pr create --draft` (body from `/document pr`). Before each step it writes the step name (`develop`, `verify`, `test`, `pr`) to `~/.claude/state/build-features/<runId>/row-<n>.step`, the run id taken from its prompt.
- **AC-7** (agent failure and owed decisions): a step that fails is handled by `/debug` under `rules/stop-and-reset.md` (2 failed fixes, then stop). A stopped agent pushes nothing and returns `failed` with the step and the reason; its worktree branch is kept. An agent whose `/develop` finds an owed decision (it would route to `/architect` or ask the owner) returns `skipped: needs a decision` with the question, and pushes nothing.
- **AC-8** (result): each agent returns `{row, status: pr|failed|skipped, branch, pr_url, step, reason}` (schema enforced). The workflow returns the list; the skill prints one line per row.
- **AC-9** (review and merge): after the workflow ends, for each draft PR in row order, the chat: brings the branch up to date with main (merge main into it, rule 4 of `rules/branch-pr.md`; a conflict stops that PR and lists it); runs `/review` (jjstack); fixes the fix now findings by `rules/review-fix.md` in a fresh worktree of the PR branch, one commit each, pushed (covered by the owner's merge yes), at most 2 review rounds; then, only when the verdict is APPROVE and the self merge checklist of `rules/when-to-switch-on.md` (row 38) holds, runs `gh pr ready` and `gh pr merge --squash --match-head-commit <sha> --delete-branch`. Checklist: own or personal repo (never a work or client origin, by `git remote get-url origin`), verify and test boxes ticked in the scope file on the PR branch, suite green on the PR head, all checks green (no check yet: wait 10 minutes for one). One merge at a time. CAUTION, REJECT, a third round needed, or a failed checklist item: the PR is not merged and is listed for the owner with the reason.
- **AC-10** (bot reviewed repos): in a repo whose origin is under the orgs in `~/.claude/private/work.md`, AC-9 runs no `/review` and no merge: the PRs are listed for the owner and the team bot.
- **AC-11** (agent panel): `claude-home/hooks/subagent-statusline.py`, set as `subagentStatusLine` in `claude-home/settings.json`, reads the `tasks` JSON on stdin. For each task whose `label` or `description` starts with `row <n> · `, it prints `{"id": <task id>, "content": "row <n> · <step> · <model> <effort>"}`, the step read from `row-<n>.step` in the newest run folder under `~/.claude/state/build-features/` (by folder modified time; `starting` when that folder has no file for the row). Other tasks get no line (default row kept). Any error prints nothing and exits 0. Self check `--test`. It is a copied file: added to `COPIED_FILES` in `bin/claude-config.py`; the live `~/.claude/settings.json` gets the `subagentStatusLine` entry first, then `bin/sync.sh`. If probe P2 fails, this AC is dropped and the band count (AC-12) is the only view, as the brief allows.
- **AC-12** (chip band): chip-dash counts running workflow agents: `agent.spawn` with `e.workflow` set adds its `agentId` with the time, `turn.complete` with that `agentId` removes it, and an entry with no event for 2 hours is dropped (a cancelled run may never send `turn.complete`). The band shows `build <n>` when n is above 0, nothing at 0. A mod reload starts the count at 0 (`$.agent.list()` does not list workflow agents); accepted and noted in a code comment. Mod test.
- **AC-13** (rule): `rules/when-to-switch-on.md` row 31 (parallel features), as spec 0073 left it, says: run `/build-features`, never hand started agents, for two or more ready rows. Copied live, then `bin/sync.sh`.

## Decision
**Chosen option**: a skill that does the listing, asking and merging in the main chat, and a script file that the Workflow tool runs for the parallel build.

A Workflow script cannot ask the owner anything, so the pick panel and the review and merge (which ask on CAUTION) live in the skill; the script does only the fan out. The script is a file in the skill folder passed as `scriptPath`, so no saved workflow registry is needed.

## Feature design

**Data model**: one small file per running row, `~/.claude/state/build-features/<runId>/row-<n>.step`, holding one word (`develop`, `verify`, `test`, `pr`). Written by the agent, read by the panel script. Folders older than 7 days are deleted by the skill at its next start. (Owner approved 2026-10-22.)

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| list | ready rows | `plan.py` feature state `ready to build` |
| list | clashes | `spec-paths --overlap` (spec 0073); open PRs from `gh pr list --json number,headRefName` |
| pick | model, effort | the rule in `rules/when-to-switch-on.md` row 31 and `rules/lessons.md`, applied by the chat per row; owner override in Other |
| start | allowed or not, cores | `start-gates` (spec 0073) |
| agent | tier chain | scope header `**Workflow:**` line (the feature's own tier tag wins) |
| agent | branch name | `rules/branch-pr.md` rule 1 |
| agent | base branch | the branch the scope is on (normally `main`) |
| merge | allowed | `/review` verdict plus the row 38 checklist |
| panel | row, step | task `label` (`row <n> · ...`); the `.step` file |
| band | running count | `agent.spawn` (`e.workflow`) and `turn.complete` (`agentId`), probe in `verify.md` |

**Key invariants**: nothing starts that the owner did not tick; no two running rows share Paths; nothing merges without APPROVE and the full checklist; a work or client repo is never merged.

**Critical test scenarios**: a scope with one `ready to build` and one `needs a design` row lists only the first (AC-1); two rows whose Paths meet show the clash and cannot both be picked (AC-2, AC-3); `start-gates` saying wait stops the later rows (AC-4); the script fakes `agent()` and passes `isolation`, `model`, `effort` and `label` per row (AC-5); a REJECT verdict leaves the PR a draft (AC-9); a work origin skips review and merge (AC-10); the panel script turns a `row 98 · ...` task plus a `test` step file into the right line and leaves another task alone (AC-11); spawn, spawn, complete gives `build 1` (AC-12).

## Build plan
Build after spec 0073 (row 98: `start-gates`, `spec-paths --overlap`) and spec 0071 (row 93: `claude-home/mods/chip-dash/**`) are merged. No stacking.

1. Probes P2 and P3 (`verify.md`) before any code. P2: workflow agents get rows in the agent panel and their `label` reaches `subagentStatusLine` (a FAIL drops AC-11, the band stays). P3: one worktree workflow agent runs a skill, commits, pushes and opens a draft PR on a scratch repo (a FAIL goes back to `/architect`). Satisfies the unknowns of **AC-6**, **AC-11**.
2. `build-features.js` and the skill's list, clash, pick and start part, with a fake run on this repo's scope, satisfies **AC-1** to **AC-8**.
3. Review and merge part of the skill, satisfies **AC-9**, **AC-10**.
4. `subagent-statusline.py` with `--test` and the settings entry, satisfies **AC-11**.
5. chip-dash band count and its mod test, satisfies **AC-12**.
6. Rule line copied live, `bin/sync.sh`, satisfies **AC-13**.

## Consequences
**Positive**: one command replaces the hand recipe; every gate (pick, clash, start gates, review, checklist) is in code or a fixed step.

**Negative / tradeoffs**: merging is automatic for APPROVE, so a review miss reaches main with nobody reading the code. Reviews run one after another, up to an hour each. The band count resets on a mod reload. The step shown in the panel is only as fresh as the agent's last write.

**Neutral**: workflow agents run on the session's permissions; the Workflow tool itself asks to start. Other repos than the current one are not covered.

## Rationale
See [rationale.md](rationale.md).
