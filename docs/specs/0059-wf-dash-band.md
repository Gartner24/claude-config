# 0059. wf-dash: a live band above the prompt, and alerts

**Date**: 2026-10-17
**Status**: Proposed
**Paths:** `claude-home/mods/wf-dash/**`, `runner/statusbar.py`, `runner/auto.py`, `runner/wf.py`, `runner/tests/test_wf_status.py`, `bin/install.sh`
**Stacks on:** 0058

## What you're agreeing to
- Our own mod, wf-dash, draws a band above the prompt with everything the status bar shows plus the runner: features running, parked, and questions waiting.
- It pops a short alert when a run finishes, a feature parks, or a question appears.
- The bottom bar shrinks to a short line, and keeps marking the chat alive.
- A test proves each mod feature works on this machine before it is built; mods are early access and are retested after every Claude Code update.

## Summary
Claude Code mods can draw a band above the prompt and show toasts. wf-dash uses them for a live view of this session and the runner. It reads the runner's state through one read only `wf status --json` command, so the counting logic stays in tested Python.

## Context
Mod surfaces (types in the plugin-authoring skill for Claude Code 2.1.301: AbovePrompt band, `$.ui.toast`, `$.ui.status`, `$.session.usage()` with rate limits, `$.clock.every`, `$.process.run`) are read from the type file only, unconfirmed by running. A mod cannot remove the settings status line (`$.ui.status` sits beside it). Runner state: `~/.local/state/wf/active.json` (a stale entry is filtered by its held lock, `auto.py:169-171`), `queue.json` parks and decisions. Your answers: band full, bottom bar short; mods are our own code, scanned and retested after upgrades.

## Requirements
- **AC-1** (status command): `wf status --json` prints, across all repos, `{"running": [...], "parked": [...], "questions": [...]}` or `null` per field. `running`: entries of `~/.local/state/wf/active.json` kept by `entry_running` (`runner/auto.py:335`, the stale lock filter), each `{id: <run folder name>, repo, feature}`, read by a new strict reader that returns `null` on a missing or broken file (not `read_active()`, which returns `[]`). `parked`: decisions in `queue.json` with `parked` set and no answer, each `{id, repo, feature}`. `questions`: unanswered decisions (`auto.open_questions`, `null` on `QueueError`), each `{id, repo, feature, title}`. Read only.
- **AC-2** (band): `claude-home/mods/wf-dash/` registers an AbovePrompt band (terminal surface only) showing model and effort, folder, branch and changes, context percent and 5 hour and weekly percent from `$.session.usage()` (`rateLimits[]` items `{kind: "five_hour" | "seven_day", percentUsed}`, `context.percent` null until the first reply; probe P3), and `wf: N running, M parked, K questions` from AC-1, refreshed every 5 s. A `null` shows `?`; with no subscription rate limits it shows `5h ?`, and through a provider `via <host>`, as spec 0058.
- **AC-3** (alerts): a toast when a run id leaves `running`, a decision id appears in `parked`, or a decision id appears in `questions`, comparing id sets between ticks; none on the first tick; a tick whose `wf status` fails or returns `null` for a field is skipped for that field, never read as empty; each id toasts once (remembered in `$.state`, and in a small file next to the marker if `$.state` does not persist, per probe P5).
- **AC-4** (short bar): each tick the mod touches a marker named by its session id under its own state folder (mtime only, no content). `wf auto bar` reads the session id from its stdin JSON and prints `statusbar.render(short=True)` (folder and the AUTO segment) only when that session's marker is under 15 s old; otherwise the full bar, so a second chat without the mod keeps its full bar. `seen` is updated either way.
- **AC-5** (never writes runner state): the mod writes nothing under `~/.local/state/wf`; its only file is its marker under its own state folder.
- **AC-6** (probes, a box that waits on you before the build, never while wf builds, since they need an interactive session): in a scratch mod run with `claude --plugin-dir`: P1 band draws; P2 toast shows; P3 `$.session.usage()` rate limits match the status line's within a few points; P4 `$.process.run("wf", ["status", "--json"])` returns; P4b the status line stdin JSON carries a session id the mod also sees; P5 a mod under `~/.claude` loads in a new session (and how often the hot reload question appears). Results go in verify notes. A failed P1 stops the build; a failed P3 means the band runs `wf status --bar` for usage instead.
- **AC-7** (tests and scan): `claude plugin validate`, a `*.test.ts` run by `claude plugin test` with `$` mocked, for the id diff, the skipped tick and the `null` display, a Python test for `wf status --json`; `skill-scan` (spec 0054) on the mod folder before its live install, which is a box that waits on you.

## Decision
A small TypeScript mod for display, a Python status command for facts.

## Build plan
1. Probes P1 to P5 (a box that waits on you), satisfies **AC-6**
2. `wf status --json`, satisfies **AC-1**
3. Band and alerts, satisfies **AC-2**, **AC-3**, **AC-5**
4. Short bar switch, satisfies **AC-4**
5. Tests, scan, live install box, satisfies **AC-7**

## Consequences
**Positive**: one live view of the session and the runner, and you hear about parks and questions without asking.
**Negative / tradeoffs**: the mod API is early access and can break on an update; the shell bar is the fallback.
**Neutral**: panes and actions come in spec 0060.
