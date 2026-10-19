# 0060. wf-dash dashboard: the plan, the builds, the agents, the alerts, and safe actions

**Date**: 2026-10-17
**Status**: Accepted
**Paths:** `claude-home/mods/wf-dash/**`, `runner/wf.py`, `runner/questions.py`, `runner/telegram.py`, `runner/tests/test_wf_plan.py`
**Stacks on:** 0059
**Amended**: 2026-10-18 - one `/wf-dash` dashboard with Plan, Builds, Agents and Alerts views replaces the separate `/plan`, `/agents` and `/runner` panes (which also clash with Claude Code's own `/plan` and `/agents`); the plan gains a `to publish` state and eight filters. Source: the locked look in `claude-home/mods/wf-dash/design.md` (Dashboard) and the brief's "B3 wf-dash look" line.

## What you're agreeing to
- One dashboard, `/wf-dash` (or a click on the band's chip), with four views you switch with a letter: Plan, Builds, Agents and Alerts. You move inside it instead of typing a command per view.
- Plan shows every plan you have: each repo and hub scope, each feature and its state (needs a design, ready to build, building, to publish, in review, waits on you, built, dropped), its next step and its spec's status, with filters. Plans not being worked on show too.
- Builds shows what waits on you first, then each run, its current step and cost; Agents shows this session's agents; Alerts shows every alert in full.
- From the dashboard you can stop an agent or background task, answer a runner question, and start a feature's next step in this session. Each action asks you to confirm. It never pushes, merges or deletes anything.

## Summary
You want full control without asking where things stand. Hub scopes and your personal todo scope show their rows; repo scopes show their features. One dashboard shows the whole plan and every worker live, and lets you act on them with a few safe actions. The plan view comes from the same scope reader the runner uses, so what you see is what `wf` would do.

## Context
`runner/wf.py` already discovers repos and hub scopes (`discover`, `scan_roots`), loads scopes (`load_scope`, `sections`, `open_rows`) and finds the next box (`next_box`, `pick_next`); spec status is the `**Status**:` line of each linked spec. Runner questions are answered with `questions.answer('<id>', '<n>')` (conductor rule in `~/.claude/.claude/CLAUDE.md`). Mod surfaces `Pane`, `$.agent.list()`, task stop, and `$.prompt.submit` are read from the types only, unconfirmed. Your answers: the plan pane as described (brief "B3 plan pane"), show plus safe actions.

## Requirements
- **AC-1** (plan command): `wf plan --json` lists every scope `wf` can find (the `scan_roots` folders), one entry per repo: worktrees of one repo are merged into the plan checkout's entry. Each scope is read inside its own `try`, through a new wrapper (never changing `discover()`, which `wf run` uses); a scope that fails is listed with its error, and `epics()` warnings are shown. A repo scope lists its features: number, heading without tags, state, next box text, spec number and spec status. A hub scope lists its At a glance rows (`open_rows`), cells as written, with no state. State, first match wins:
  1. `building`: an `entry_running` entry of `active.json` for this repo whose feature equals the heading, both normalized the way `NextBox.feature` strips tags (`runner/wf.py:77`).
  2. `waits on you`: the next box is owed (`next_box`, `NextBox.owed`, `wf.py:72`, `:218-237`).
  3. `to publish` (amended 2026-10-18): a `queue.json` `prs` record (read with `run.queue_transact()`) for this repo and feature with state `local` (built on its branch, not pushed; `pr.py:27`).
  3b. `in review`: such a record with state `draft`, `ready` or `approved` (`pr.py:28`), with its PR number. A repo without `branches: per spec` has no records, so it shows `in review: unknown` when its next box is past build, never "not in review".
  4. `done`, `dropped`, `existing`: the heading tag (`GONE_TAG`, `wf.py:20`); a feature with every box ticked and no tag is `done (untagged)`.
  5. `needs a design`: the next box's command is `/architect`.
  6. `ready to build`: the next box's command is `/develop`.
  7. `in progress`: any other open box.
  Spec number: the first `specs/NNNN-` link on the feature's heading block (pointer and Spec lines, regex `specs/(?:[^/)]*/)?(\d{4})-`); spec status: the `**Status**:` line of `NNNN-*.md` or `NNNN-*/index.md`; a missing file shows `unknown`, never blank. Text taken from files and logs goes through `wf.clean()` (`wf.py:54`).
- **AC-2** (one dashboard, amended 2026-10-18): the mod registers one command, `/wf-dash`, and no `/plan`, `/agents` or `/runner`. It opens one Pane with focus (`$.ui.open`, `focus: true`, `closeOnEscape: true`, 21 rows asked), also from a click on the band's chip. Four views, switched by a letter: `p` Plan, `b` Builds, `a` Agents, `l` Alerts; the selected view is bracketed (`[Plan]`). Layout, widths, footer keys and wording follow `claude-home/mods/wf-dash/design.md` (Dashboard), the locked look. Data refreshes every 10 s while open, never two `wf plan` calls at once (a tick is skipped while one runs); a failed or timed out call keeps the last good result marked `stale since HH:MM`, never an empty plan.
- **AC-2a** (Plan view): features grouped by state across repos, eight filters on digit keys, each with its count: `1` Needs you, `2` Building, `3` To publish, `4` Ready, `5` Needs design, `6` In progress, `7` Built (the `done` state), `8` All open (adds hub rows, broken scopes and scope warnings). Each row: name, repo, next step and spec with its status; a `>` cursor on `j` / `k`, pages on `d` / `u`, `n` next group, `g` top; a detail block for the selected feature.
- **AC-3** (Agents view, amended): lists `$.agent.list()` entries (subagents only, probe P7): state word, description, type. An empty list says the mod API lists none (not proof of none), and says plainly that background shells are not listed while no API returns them.
- **AC-4** (Builds view, amended): first a `waits on you N` block with each open question (its ask and options, answered on the phone by id or with the AC-5 answer action) and each parked feature, then a `building N` block with each run from `wf status --json`: feature, repo, current step (read from the run's `log.txt` in its run folder under `~/.local/state/wf/runs/`, cleaned by `wf.clean()`), steps so far, cost and start time, and with 2 runs or fewer its last 3 steps.
- **AC-4a** (Alerts view, new): every alert of the session from spec 0059 AC-3's list, newest first: the kind word in its color (finished ok, stuck bad, question warn), the feature in bold, the time at the right, the full detail below. Empty, it says what will land there.
- **AC-5** (safe actions): from the dashboard, as hotkey buttons in the footer row, with a confirm: stop an agent or background task; answer a runner question (a `wf answer <id> <n>` command added to `runner/wf.py`, which checks `n` against the options with `telegram.answer_text` and calls `questions.answer`; an id already answered prints `already answered`); start a feature's next step, only when that command is one of `/architect`, `/develop`, `/check verify`, `/test`, `/sync`, `/debug`, `/scope` (your answer: safe list only), showing the exact text before you confirm, then submitting it as a prompt in this session from `$.clock.after` once the confirming hook has returned (probe P9). Nothing else: no push, merge, delete, settings change or spec edit is reachable from the mod, and other next steps show a `type it yourself` note.
- **AC-6** (probes, a box that waits on you before the build, since they need an interactive session): P6 a Pane draws beside the conversation (run 2026-10-18: the layout sizes from the pane body width, never from `viewport.columns`, which is the conversation width); P7 `$.agent.list()` returns this session's agents; P8 stopping a background task from a mod works (no `$.agent.stop` is in the types; it may need `$.tool.call` of the TaskStop tool, unconfirmed); P9 `$.prompt.submit` runs as a turn. Each failed probe removes only its action or view, and the spec records it. Results so far are in `0060-wf-dash-panes/verify.md` (P6 to P9 pass, run again 2026-10-18).
- **AC-7** (tests): `wf plan --json` over fixture scopes covering every state and a broken scope; a broken scope and two worktrees of one repo; `wf answer` with a fake question store, a wrong option and an answered id; a `to publish` and an `in review` record; a `*.test.ts` run by `claude plugin test` with `$` mocked, for grouping and filters, the view letters, no `/plan` `/agents` `/runner` command registered, the Alerts view order, the safe list and the confirm step; mutation checked.

## Decision
Python commands supply the facts (`wf plan`, `wf answer`); the mod draws one dashboard with four views and offers three confirmed actions.

## Build plan
1. Probes P6 to P9 (a box that waits on you), satisfies **AC-6**
2. `wf plan --json` and `wf answer`, satisfies **AC-1**, part of **AC-5**
3. The `/wf-dash` dashboard: Plan, Builds, Agents and Alerts views, satisfies **AC-2** to **AC-4a**
4. Actions with confirm, satisfies **AC-5**
5. Tests, satisfies **AC-7**

## Consequences
**Positive**: the whole plan and every worker in one place, and the common actions one click away.
**Negative / tradeoffs**: more mod surface to retest after Claude Code updates; a wrong confirm can stop real work.
**Neutral**: B14 memory and B5 proposals can add views later. Keys the dashboard does not bind are row 75 (spec 0062).
