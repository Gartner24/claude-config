# 0060. wf-dash panes: the plan, the agents, the runner, and safe actions

**Date**: 2026-10-17
**Status**: Proposed
**Paths:** `claude-home/mods/wf-dash/**`, `runner/wf.py`, `runner/questions.py`, `runner/telegram.py`, `runner/tests/test_wf_plan.py`
**Stacks on:** 0059

## What you're agreeing to
- `/plan` opens a pane with every plan you have: each repo and hub scope, each feature and its state (needs a design, designed and ready to build, building, in review, waits on you, done, dropped), its next step, and its spec's status. Plans not being worked on show too.
- `/agents` opens a pane with every agent and background task of this session and what each is doing; `/runner` shows each run, its current step, cost, last log lines and open questions.
- From the panes you can stop an agent or background task, answer a runner question, and start a feature's next step in this session. Each action asks you to confirm.
- It never pushes, merges or deletes anything.

## Summary
You want full control without asking where things stand. Hub scopes and your personal todo scope show their rows; repo scopes show their features. These panes show the whole plan and every worker live, and let you act on them with a few safe actions. The plan view comes from the same scope reader the runner uses, so what you see is what `wf` would do.

## Context
`runner/wf.py` already discovers repos and hub scopes (`discover`, `scan_roots`), loads scopes (`load_scope`, `sections`, `open_rows`) and finds the next box (`next_box`, `pick_next`); spec status is the `**Status**:` line of each linked spec. Runner questions are answered with `questions.answer('<id>', '<n>')` (conductor rule in `~/.claude/.claude/CLAUDE.md`). Mod surfaces `Pane`, `$.agent.list()`, task stop, and `$.prompt.submit` are read from the types only, unconfirmed. Your answers: the plan pane as described (brief "B3 plan pane"), show plus safe actions.

## Requirements
- **AC-1** (plan command): `wf plan --json` lists every scope `wf` can find (the `scan_roots` folders), one entry per repo: worktrees of one repo are merged into the plan checkout's entry. Each scope is read inside its own `try`, through a new wrapper (never changing `discover()`, which `wf run` uses); a scope that fails is listed with its error, and `epics()` warnings are shown. A repo scope lists its features: number, heading without tags, state, next box text, spec number and spec status. A hub scope lists its At a glance rows (`open_rows`), cells as written, with no state. State, first match wins:
  1. `building`: an `entry_running` entry of `active.json` for this repo whose feature equals the heading, both normalized the way `NextBox.feature` strips tags (`runner/wf.py:77`).
  2. `waits on you`: the next box is owed (`next_box`, `NextBox.owed`, `wf.py:72`, `:218-237`).
  3. `in review`: a `queue.json` `prs` record (read with `run.queue_transact()`) for this repo and feature with state `draft`, `ready` or `approved` (`pr.py:28`). A repo without `branches: per spec` has no records, so it shows `in review: unknown` when its next box is past build, never "not in review".
  4. `done`, `dropped`, `existing`: the heading tag (`GONE_TAG`, `wf.py:20`); a feature with every box ticked and no tag is `done (untagged)`.
  5. `needs a design`: the next box's command is `/architect`.
  6. `ready to build`: the next box's command is `/develop`.
  7. `in progress`: any other open box.
  Spec number: the first `specs/NNNN-` link on the feature's heading block (pointer and Spec lines, regex `specs/(?:[^/)]*/)?(\d{4})-`); spec status: the `**Status**:` line of `NNNN-*.md` or `NNNN-*/index.md`; a missing file shows `unknown`, never blank. Text taken from files and logs goes through `wf.clean()` (`wf.py:54`).
- **AC-2** (plan pane): `/plan` opens a Pane grouped by scope, features sorted by state (building, waits on you, in review, ready, needs a design, then done collapsed), each with its next step and spec status; refreshed every 10 s, never two `wf plan` calls at once (a tick is skipped while one runs); a failed or timed out call keeps the last good result marked `stale since HH:MM`, never an empty plan.
- **AC-3** (agents pane): `/agents` lists `$.agent.list()` entries and background tasks: name, type, state, running time, tokens.
- **AC-4** (runner pane): `/runner` lists runs from `wf status --json`, each with feature, current box, cost, the last 15 lines of its `log.txt` in its run folder under `~/.local/state/wf/runs/`, cleaned by `wf.clean()`, and its open questions with their options.
- **AC-5** (safe actions): from a pane, with a confirm: stop an agent or background task; answer a runner question (a `wf answer <id> <n>` command added to `runner/wf.py`, which checks `n` against the options with `telegram.answer_text` and calls `questions.answer`; an id already answered prints `already answered`); start a feature's next step, only when that command is one of `/architect`, `/develop`, `/check verify`, `/test`, `/sync`, `/debug`, `/scope` (your answer: safe list only), showing the exact text before you confirm, then submitting it as a prompt in this session. Nothing else: no push, merge, delete, settings change or spec edit is reachable from the mod, and other next steps show a `type it yourself` note.
- **AC-6** (probes, a box that waits on you before the build, since they need an interactive session): P6 a Pane draws at your terminal width; P7 `$.agent.list()` returns this session's agents; P8 stopping a background task from a mod works (no `$.agent.stop` is in the types; it may need `$.tool.call` of the TaskStop tool, unconfirmed); P9 `$.prompt.submit` runs as a turn. Each failed probe removes only its action or pane, and the spec records it.
- **AC-7** (tests): `wf plan --json` over fixture scopes covering every state and a broken scope; `wf answer` with a fake question store; a broken scope and two worktrees of one repo; `wf answer` with a fake question store, a wrong option and an answered id; a `*.test.ts` run by `claude plugin test` with `$` mocked, for sorting, the safe list and the confirm step; mutation checked.

## Decision
Python commands supply the facts (`wf plan`, `wf answer`); the mod draws panes and offers three confirmed actions.

## Build plan
1. Probes P6 to P9 (a box that waits on you), satisfies **AC-6**
2. `wf plan --json` and `wf answer`, satisfies **AC-1**, part of **AC-5**
3. Plan, agents and runner panes, satisfies **AC-2** to **AC-4**
4. Actions with confirm, satisfies **AC-5**
5. Tests, satisfies **AC-7**

## Consequences
**Positive**: the whole plan and every worker in one place, and the common actions one click away.
**Negative / tradeoffs**: more mod surface to retest after Claude Code updates; a wrong confirm can stop real work.
**Neutral**: B14 memory and B5 proposals can add panes later.
