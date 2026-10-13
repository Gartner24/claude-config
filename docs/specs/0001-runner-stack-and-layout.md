# 0001. Runner stack and layout: one stdlib Python CLI in runner/

**Date**: 2026-10-11
**Status**: Accepted
**Paths:** `runner/wf.py`, `runner/run.py`, `runner/ntfy.py`, `runner/tests/test_*.py`, `runner/tests/fixtures/**`, `install.sh`
**Amended**: 2026-10-12, architecture pass ([architecture](../architecture.md)): the Release 2 split is flat modules beside `wf.py` (`run.py`, `ntfy.py`), not a `runner/wf/` package. No behavior change.

## What you're agreeing to

- Nothing new: the amendment records how the runner was actually split when `wf run` landed.
- `wf.py` keeps the shared scope parsing and `next`; `run.py` holds `wf run`; `ntfy.py` holds the phone pings.

## Summary

The workflow runner is one Python 3 program using only the standard library (the modules that ship with Python, nothing to install). It lives in `runner/` in this repo and is called `wf`, with subcommands: `wf next` now, `wf run` and others in later releases. `install.sh` links it onto your PATH as `wf` and as a `next` shortcut, so edits in the repo are live. Tests are stdlib `unittest` runs on fixture scopes, and `install.sh` runs them as part of its checks.

## Context

The runner has to do four kinds of work over its releases. It parses scope markdown, runs and watches `claude` processes, reads their JSON output, and handles signals, locks and timers. Release 1 only parses and launches. Release 2 adds the unattended loop. Releases 3 and 4 add queues and a report. The stack chosen now carries all of them, so a choice that is fine for Release 1 but fragile for Release 2 costs a rewrite.

This repo is public and mostly markdown. Its code is small Bash and Python scripts with no package manager at root. Where it has tests, they are self checks that `install.sh` runs (`block-destructive.sh --test`, `test-ledger.sh`, `gen-agent-index.py --check`). `skills/` and `commands/` are symlinked into `~/.claude`, so an edit here is live. The settled requirements say runner code lives in `~/claude-config` (section 0 of `~/Documents/workflow-research/09-autonomous-runner-research.md`).

The runner is a personal tool for one desktop machine. It never runs on a server or in CI.

## Options considered

### Option 1: Python 3 stdlib, one CLI with subcommands (chosen)
`runner/wf.py`, with argparse subcommands, symlinked onto the PATH.

**Pros**:
- `subprocess`, `json`, `signal`, `fcntl` and `re` cover every release with no install step (basis: your AGENTS.md, stack lists Python 3 scripts already).
- One entry point keeps shared parsing in one place as releases add up.

**Cons**:
- Starts a Python interpreter on each call (about 30 ms), slower than a shell function.
- A single file grows; it needs splitting into modules when Release 2 lands.

### Option 2: Bash plus jq
Same command set as shell scripts, like `sync.sh` and the hooks.

**Pros**:
- Matches the repo's existing hooks; no interpreter beyond the shell.

**Cons**:
- Markdown parsing with nesting rules (milestones under boxes, sections, tags) and the Release 2 loop with locks, timers and JSON get fragile in Bash (basis: the hook false positives in personal scope item 10 come from regex matching on shell text).

### Option 3: TypeScript on Node
A typed CLI run with Node 24 (installed through mise).

**Pros**:
- Types help as the runner grows; good JSON handling.

**Cons**:
- Needs a package.json and a build or `tsx` step in a repo that has almost none, and mise must be active for the right Node.

### Option 4: Go
A compiled single binary.

**Pros**:
- Fast start, strong concurrency for Release 3 queues.

**Cons**:
- A compile step and a Go toolchain for a one machine tool; edits are not live.

## Decision

**Chosen option**: Option 1: Python 3 stdlib, one CLI with subcommands

The runner is `runner/wf.py`, stdlib only, called as `wf <subcommand>` and through a `next` shortcut, installed by symlink and tested with `unittest`.

## Rationale

The deciding force is Release 2, not Release 1. The unattended loop needs process control, JSON parsing, a lock file and signal handling; Python's stdlib does all of these, while Bash makes each one a source of silent bugs (basis: boring technology, prefer what the repo already runs). Stdlib only keeps the repo free of a package manager and keeps a fresh clone working with no install step, the same property the design scripts protect by committing `node_modules` (basis: your AGENTS.md). Symlinking matches how `skills/` and `commands/` are already installed, so there is one copy of the truth and no reinstall after edits. `unittest` over pytest keeps that zero dependency promise.

## Proposed stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.11 or newer, standard library only | Covers parsing, subprocess, JSON, signals and locks for every release with nothing to install. |
| CLI | `argparse` with subcommands, one entry `wf` | One place for shared scope parsing; `wf next` now, `wf run`, `wf queue`, `wf report` later. |
| Shortcut | `next` symlink to the same file; when called as `next`, it behaves as `wf next` | Lets you type `next <repo>` as asked, with no second program. |
| Layout | `runner/wf.py` (executable, `#!/usr/bin/env python3`), `runner/tests/test_*.py`, `runner/tests/fixtures/` | One file until Release 2, then flat modules beside it: `runner/run.py` (`wf run`) and `runner/ntfy.py` (pings), imported lazily by `wf.py` (amended 2026-10-12). |
| Install | `install.sh` symlinks `runner/wf.py` to `~/.local/bin/wf` and `~/.local/bin/next` | Same symlink pattern as skills and commands; `~/.local/bin` is already on your PATH (claude lives there). |
| Tests | `python3 -m unittest discover -s runner/tests`, wired into the `install.sh` verify step | Stdlib, and it fails the install loudly like the other self checks. |
| Fixtures | Trimmed copies of real scopes (dotfiles, claude-config, a hub, a `.workflow/` scope) | Tests run against the shapes that exist, not invented ones. |
| External tools | `git`, `fzf` called with `subprocess.run` and argument lists, never a shell string; an interactive `claude` launch replaces the process with `os.execvp` | Already installed; argument lists avoid shell injection from scope text, and exec leaves Ctrl C and the exit code to claude. |

## Consequences

**Positive**:
- No dependency to install or update; a fresh clone plus `install.sh` gives a working `wf`.
- Later releases add subcommands to the same program instead of new scripts.

**Negative / tradeoffs**:
- `wf.py` grew; the Release 2 build split `wf run` and the pings into `run.py` and `ntfy.py` (amended 2026-10-12).
- `next` is a generic command name. Nothing on your PATH uses it today, but a future package could; the symlink would then need renaming.
- Python start time (about 30 ms) on each call, fine for a launcher, noticeable only if called in a tight loop.

**Neutral**:
- `runner/` is a third kind of file in the repo: neither a copy synced from `~/.claude` nor a skill. Root `AGENTS.md` needs a line saying so.

## Follow-up

- [x] Root `AGENTS.md`: add `runner/` (symlinked to `~/.local/bin`, edit here) to the Rules and the test command to Commands; `/sync` owns this.
- [x] `NOTICE.md`: list `runner/` as authored here.

## References

**Project sources**:
- `AGENTS.md` (stack, the copy vs symlink rule, self checks as tests)
- `install.sh` (symlink pattern and verify step)
- `~/Documents/workflow-research/09-autonomous-runner-research.md` section 0 (code lives in `~/claude-config`, stages)
- `docs/scope/scope.md` row 1

**Practices & standards**:
- Boring technology, prefer what the repo already runs
- Pass external commands as argument lists, never through a shell

**Links**:
- Python unittest (discover, `-s` start folder): https://docs.python.org/3/library/unittest.html
- Python subprocess (`subprocess.run` with an argument list, `shell=False` by default): https://docs.python.org/3/library/subprocess.html
- Claude Code CLI reference (`claude "query"`, `claude -p`, `--output-format`): https://code.claude.com/docs/en/cli-reference
