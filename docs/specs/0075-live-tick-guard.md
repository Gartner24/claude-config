# 0075. A live install box is ticked only when it is live

**Date**: 2026-10-22
**Status**: Accepted
**Paths:** `claude-home/hooks/live-tick.py`, `claude-home/settings.json`, `tools/bin/claude-config.py`

## What you're agreeing to
- In claude-config, an edit that ticks a scope box ending ` · live` is refused until `claude-config drift` shows that box's files are live and equal.
- A box that names files is checked for those files; a `bin/install.sh` box for every file that is missing or different live; other boxes are not checked.
- Extra files that exist only live (like today's `hooks/gsd-phase-boundary.sh`) never block a tick.
- If the hook itself breaks, it lets the edit through and logs one line.

## Summary
Rows 67, 69 and 71 each had a "copy live" box ticked while the files were not live, found by `claude-config drift` on 2026-10-20. This spec adds a PreToolUse hook (a script Claude Code runs before a tool call, which can refuse it) that refuses such a tick. It compares only what the box claims to have copied or installed.

## Context
`claude-home/` files reach `~/.claude` by a copy or a link (AGENTS.md Rules). A scope box for that step ends ` · live` (`rules/scope-contract.md`) and is ticked by an Edit of the scope file. Nothing checks the tick against the real `~/.claude`; a memory note ("drift before trusting ticks") did not stop the misses. `bin/claude-config.py drift` already lists every difference, grouped by kind, each line `  <name>: <reason>` with reasons `differs`, `missing live`, `live only...`, `in the repo, but live is not a link to it`, `live link is broken`. Owner answers: [brief](../briefs/live-tick.md).

## Requirements

**User stories**:
- As the owner, I want a live box ticked only when the copy really happened, so the plan never says live when it is not.

**Acceptance criteria**:
- **AC-1** (trigger): `claude-home/hooks/live-tick.py`, a PreToolUse hook on `Edit`, `Write` and `MultiEdit`, acts only when the target file is under `docs/scope/` or `.workflow/scope/` of a repo found by walking up from the target file to a folder holding `bin/claude-config.py` (`~/claude-config` and its realpath are the same repo; a worktree is its own checkout, and the verdict is for that checkout). It reads the file on disk as the old text and builds the new text: `Edit` replaces `old_string` (every match with `replace_all`), `MultiEdit` applies `edits[]` in order, `Write` is `content`. A live box is any line, at any indent, matching `^\s*- \[[ xX]\] .* · live( · .*)?$`. The boxes checked are those ticked in the new text whose text is not a ticked live box in the old text: a tick, a tick plus a text change, or a line added already ticked. No such box: the edit passes untouched.
- **AC-2** (what a box names): paths are taken with `(?:claude-home/|~/\.claude/)[\w./-]*[\w/-]`, trailing `.`, `,`, `:` or `)` dropped; in `cp <src> <dst>` only paths of that shape count, so the live side `~/.claude/...` is the one checked. Each path is made relative (`rules/x.md`) and compared two ways, both must pass: (a) direct: the repo file `claude-home/<rel>` and the live file `~/.claude/<rel>` both exist and are byte equal (a folder path compares every file under it; `skills/<n>/...` compares the live link `~/.claude/skills/<n>` resolving into this repo); a path that exists in neither place is refused as `not found`; (b) drift: no drift line matches it, matching by this table of what drift prints (`bin/claude-config.py:131-142`, `:87-128`, `:157-170`, `:185-211`):

  | box path | drift group | drift name |
  |---|---|---|
  | `rules/...`, `agents/...` | `rule`, `agent` | the full relative path |
  | `hooks/...`, `scripts/...` | `hook`, `script` | the full relative path |
  | `skills/<n>/...` | `skill` | `<n>` |
  | `commands/<f>` | `command` | `<f>`, with `.md` |
  | `CLAUDE.md` | `instructions` | `CLAUDE.md` |
  | `settings.json`, `settings.local.json` | `setting` | starts with `settings.json: ` (one line per differing key) |

  Drift prints `<group>:` headers and `  <name>: <reason>` lines; a line is split on its last `: `. A box containing `bin/install.sh` checks every drift line whose reason is `differs` or `missing live` (the owner's answer; other reasons such as `live only`, `live link is broken` or a patch note do not block it).
- **AC-3** (refuse): it runs `python3 <repo>/bin/claude-config.py drift`. Any failure from AC-2 refuses the edit as PreToolUse JSON `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": ...}}`, the reason `live box not live yet:` then one line per failure `<group> <name>: <reason>` (at most 5, then `and <k> more`), for the union of every checked box, and the hint `copy or install it, then tick again`. No failure: the edit passes.
- **AC-4** (not checked): a ` · live` box that names no such path and no `bin/install.sh` passes (5 of today's 21 live boxes: e2e runs and probes).
- **AC-5** (drift fails): drift exiting other than 0 or 1, or a timeout after 60 seconds (`TimeoutExpired` included), refuses with `drift did not run: <reason>` (unknown is not live). In the sandbox an unreadable `~/.claude/private` makes drift fail, which refuses; accepted.
- **AC-6** (hook breaks): any other error inside the hook lets the edit through and appends one line to `~/.claude/state/live-tick/errors.log`.
- **AC-7** (install): the hook is in `COPIED_FILES` in `bin/claude-config.py`; the live `~/.claude/settings.json` gets the PreToolUse entry (matcher `Edit|Write|MultiEdit`, `timeout` 65 seconds) first, parsed with `python3 -c "import json; json.load(open(...))"`, then `bin/sync.sh`.
- **AC-8** (tests): `live-tick.py --test` covers: a tick of a box naming a rule that differs is refused, and passes once equal (AC-2, AC-3); a named hook that drift does not list and that is missing live is refused (AC-2 a); a typo path is refused as not found; a `bin/install.sh` box ignores a live only extra but refuses a missing file (AC-2); a box naming nothing passes (AC-4); a failing and a timed out drift refuse (AC-5); an unticking edit and an edit in a non scope file pass (AC-1); a tick plus a text change, an indented box, `replace_all`, a `MultiEdit`, and a `Write` ticking two boxes (refusal lists both) are each caught (AC-1, AC-3); a crash passes and logs (AC-6). Drift output and both file trees are fakes in a temp folder; each test is mutation checked.

## Decision
**Chosen option**: a PreToolUse hook that runs drift and refuses the tick (owner pick).

## Options considered
- **Refuse the edit (chosen)**: the bad tick is never written. Con: one more hook on scope edits.
- **Catch at turn end in the row 92 Stop hook**: no new hook. Con: the wrong tick lands first; that hook is not built.
- **Rule line only**: nothing to build. Con: the same miss already happened with a memory note.

## Rationale
The row's Done when says "refuses the tick", which only a PreToolUse hook can do. Checking only what the box names keeps unrelated drift (today's two live only leftovers) from blocking work, while a `bin/install.sh` box, which claims everything, is checked for everything an install would fix. Recommended without asking: refuse on a drift failure but pass on a hook crash (an unknown drift is not live, but a broken hook must not block all scope edits; same split as spec 0070 AC-11); the 60 second drift timeout (drift reads local files, about a second today).

## Feature design
**Data model**: none (one error log line on a crash).

**Value sourcing**: box text from the edit's new and old content; drift items from `bin/claude-config.py drift` output; the mapping rules in AC-2.

**Security model**: read only; runs one local script.

**Critical test scenarios**: listed in AC-8.

## Build plan
Build after spec 0070 (row 92) merges: both add to `claude-home/settings.json` and `bin/claude-config.py`.
1. `live-tick.py` with `--test`, satisfies **AC-1** to **AC-6**, **AC-8**.
2. `COPIED_FILES`, live settings entry, `bin/sync.sh`, satisfies **AC-7**.

## Consequences
**Positive**: a live box can no longer claim a copy that did not happen.

**Negative / tradeoffs**: a box wording that names no path slips through (AC-4); ticks made through Bash (sed) are not seen; every tick of a live box costs one drift run.

**Neutral**: only claude-config has `bin/claude-config.py`, so other repos are untouched.
