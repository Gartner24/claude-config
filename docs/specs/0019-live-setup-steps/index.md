# 0019. Live setup steps in one command

**Date**: 2026-10-13
**Status**: Accepted
**Paths:** `_archive/runner/finish.py`, `_archive/runner/wf.py`, `bin/install.sh`, `scripts/private-names.py`, `claude-home/rules/scope-contract.md`, `claude-home/rules/runner-handoff.md`
**Amends**: [0003](../0003-scope-contract/index.md) (new ` · live` tag), [0012](../0012-waiting-boxes-owed-to-you/index.md) (a live box is still a waiting box for `wf run`), architecture invariant 7 (`wf finish`, run by you, ticks boxes, writes verify.md and commits).

## Summary

Steps that touch your live setup (copy a file into `~/.claude`, run `./install.sh`, run a real claude check) stay out of unattended calls. Today they pile up as separate boxes you run by hand. With this spec they carry a ` · live` tag, and one command, `wf finish`, shows them all, waits for your Enter, backs up, copies, installs, runs the checks, writes each check result into the spec's verify.md, ticks the boxes that passed and commits those edits. `install.sh` also stops dropping your live `autoMode`.

## What you're agreeing to

- `wf finish` runs only boxes tagged ` · waits on you · live` whose every command is one of four fixed shapes; anything else stays yours.
- It runs at your keyboard after one Enter (`-y` skips it), and refuses while any `wf run` is going.
- A failed copy or install stops it before the checks; a failed check is recorded and the rest still run.
- It makes one local commit per repo with only the files it changed, never on `main`, never a push.
- `install.sh` keeps the `autoMode` already in your live settings.json.

## Requirements

**User stories**:
- As you, in the morning, I want to paste one line that does every live step and ticks the boxes, so the next run can `/sync`.
- As you, I want my live `autoMode` kept whatever installs.

**Acceptance criteria**:
- **AC-1** (the tag): an open box whose own text carries both ` · waits on you` and ` · live` (any order among its tags, `LIVE = ·\s*live\s*(?=·|$)` in `runner/wf.py`) is a live box, when its feature is not under `## Deferred` and not `done` or `dropped`. `wf run` treats it exactly as any waits-on-you box (spec 0012, spec 0014 AC-8). A box with ` · live` but no ` · waits on you` is never run by `wf finish`, which lists it with `live needs waits on you`.
- **AC-2** (allowed shapes): every backticked span of a live box is one step, split with `shlex.split`, and must match exactly one shape, else the whole box is listed as yours with `not a live step: <span>` and nothing in it runs. Paths resolve against the repo root after `~` expansion and `realpath`, and must stay inside the repo.
  - copy: `cp <src> <dst>`, no flags. `<src>` a regular file (not a link) inside the repo at relative path `<rel>`; `<dst>` resolves to `<live>/<rel>` where `<live>` is `$CLAUDE_LIVE_DIR`, else `~/.claude`; `<rel>` is not `settings.json`, `settings.local.json`, or under `private/`.
  - install: `./install.sh`, with `install.sh` present at the repo root.
  - end to end: `python3 runner/e2e/run.py` or `python3 runner/e2e/run.py --parallel`, the file present.
  - probe: `python3 docs/specs/<dir>/probes/<name>.py` or `bash docs/specs/<dir>/probes/<name>.sh`, no other arguments, the file present.
  A box with no backticked span is listed as yours. A live box holds exactly one step and no human step: any other backticked text (a `` `!` ``, a file path) makes it not a live step. A box that mixes a command with a human action is written without ` · live` (AC-10), since the command cannot know the human part is done.
- **AC-3** (the command): `wf finish [repo] [-y]` covers the named repo (resolved as `wf run <repo>` does, and refused `untrusted`, exit 5, when not on the trust list), else every repo on the trust list in its order; a trusted repo that is missing on disk or has no scope file prints `skipped: <repo>: <why>` and the rest go on. It refuses `unattended`, exit 5, when `WF_RUN` is set, and `no_tty`, exit 5, when stdin is not a terminal and `-y` is not given (as `Run.confirm`). It refuses `locked`, exit 5, while any lock file under `<state>/locks` is held (non blocking `flock` probe, as spec 0018 AC-6). Otherwise it takes the lock of every repo it covers for the whole command, prints the plan (each step by phase as `<phase>: <repo>: <feature>: <command>`, then each box listed as yours with its reason), and waits for an empty line (anything else, EOF or Ctrl C cancels, exit 130) unless `-y`. With no live step it prints `no live steps`, creates `<state>/report.seen` and exits 0.
- **AC-4** (phases and failure): steps run in three phases, each in trust list order, then scope file order: copies, then installs (once per repo however many boxes name it), then checks (end to end and probes, each distinct command once per repo). The phases are the whole ordering: a check may rely on any copy or install, never the reverse. Before the first copy, every existing `<dst>` is copied to `<state>/finish/<stamp>/claude/<rel>`; before the first install, `<live>/rules`, `<live>/agents`, `<live>/hooks`, `<live>/scripts` and `<live>/settings.json` (what `install.sh` overwrites) are copied under `<state>/finish/<stamp>/claude/` too, links kept as links. The folder is printed. A copy passes when the copied file is byte equal to `<src>`. An install or check runs as an argument list with the repo as working directory and your environment, its output shown live and saved to `<state>/finish/<stamp>/step-<NN>.log`, and passes on exit 0. A failed copy or install stops the command before the next phase: no check runs. A failed check is recorded and the next check still runs. Ctrl C sends SIGINT to the running step's process group, counts it as failed, runs no further step, and goes on to AC-5 to AC-7 for what already passed.
- **AC-5** (record): each check result is appended to the `verify.md` beside the feature's spec (the first link in the feature's section matching `specs/<dir>/index.md`), under a `## Live runs (wf finish)` heading added at the end when missing (the file is created with that heading when the spec folder has no `verify.md`): `- <YYYY-MM-DD>, Claude Code <version>: \`<command>\` PASS`, or `... FAIL (exit <code>): <last non blank output line, cleaned, at most 200 characters>`. `<version>` is the first word of `claude --version`, else `unknown`. A feature with no such link gets no record and a printed warning. The same check named by two features is recorded in both.
- **AC-6** (tick): a box whose every step passed gets its `[ ]` turned into `[x]`. The scope file is read again right before the edit; when the box's exact line is no longer in its feature section, it prints `box changed, not ticked: <text>` and leaves the file.
- **AC-7** (commit): per repo whose files `wf finish` changed, on a named branch other than `main` or `master`: `git add -- <files>`, then `git commit -m "chore(wf): wf finish ran <n> live step(s)" -- <files>`, hooks running as usual. On `main`, `master` or a detached head it commits nothing and prints `edits left uncommitted on <branch>`. A failed commit prints git's error and leaves the edits.
- **AC-8** (end): it prints one line per step `PASS` or `FAIL` and a last line `next: wf run` when every box passed, else `next: fix the FAIL lines, then wf finish`. It creates `<state>/report.seen` when it ran to its end (not after Ctrl C, a refusal or a cancel). Exit 0 when every step passed and every commit succeeded, 1 otherwise, 130 on Ctrl C or cancel, 5 on a refusal.
- **AC-9** (`autoMode`): `install.sh` reads `autoMode` from the existing `$LIVE/settings.json` before replacing it and, after the private settings merge, writes that value back into the new file; a live file with no `autoMode` yields none, an unreadable one prints `autoMode not kept: <error>` and installs on. `--dry-run` prints `would keep autoMode` when there is one. The `install.sh` self checks in `scripts/private-names.py --test` cover both cases.
- **AC-10** (rules and existing boxes): `rules/scope-contract.md` gains a bullet for the ` · live` tag (both tags, exactly one command in backticks and no other backticked text or human step per box, the four shapes, `/architect` writes them). `rules/runner-handoff.md` step 1 says: a step that writes `~/.claude` or `.git/hooks` is marked ` · waits on you`, and when it is one of the four shapes it is written one step per box with ` · live` too; a human step goes in its own box without ` · live`. Existing boxes are not converted: every waits-on-you box in `docs/scope/scope.md` is ticked today; the first live boxes are the ones specs 0018 and 0019 add.

## Decision

**Chosen option**: Option 1: a `wf finish` subcommand that reads live boxes from the scope files, runs only allowed shapes after your Enter, records, ticks and commits.

## Feature design

**Data model sketch** (files):
- Scope box text: ` · waits on you · live` (plus optional ` · later boxes go on`).
- `<state>/finish/<stamp>/`: `claude/<rel>` backups, `step-<NN>.log` outputs. `<stamp>` is `YYYYmmdd-HHMMSS`.
- `<spec dir>/verify.md`: `## Live runs (wf finish)` lines.
- `<state>/report.seen`: shared with spec 0018.

**State per box**: listed, then `passed` (every step passed: ticked), `failed` (left open), or `not run` (an earlier phase failed, or Ctrl C).

**API surface**:
| Command | Inputs | Output | Exit |
|---|---|---|---|
| `wf finish [repo] [-y]` | trust list, locks, scope files, spec links, `claude --version` | backups, logs, live files, verify.md lines, ticks, one commit per repo, report.seen | 0, 1, 5, 130 |
| `./install.sh` | live settings.json `autoMode` | new settings.json with that `autoMode` | unchanged |

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| plan | repos | named repo, else `allowed.json` (spec 0008) |
| plan | steps | backticked spans of live boxes (AC-1, AC-2) |
| copy | destination root | `$CLAUDE_LIVE_DIR`, else `~/.claude` (same override as install.sh) |
| copy | backup path | `<state>/finish/<stamp>/claude/<rel>` |
| record | verify.md path | the feature section's first `specs/<dir>/index.md` link |
| record | date, version | today local, `claude --version` first word |
| record | fail line | last non blank line of the step's output |
| commit | files | the files this command changed in that repo |
| commit | message | fixed `chore(wf): wf finish ran <n> live step(s)` |
| install | `autoMode` | the live settings.json before it is replaced |

**Key invariants**:
- No `wf run` call ever writes `~/.claude` or `.git/hooks`; only `wf finish`, after your Enter or `-y`.
- No shell: every step is an argument list, every copy is done in Python.
- Nothing outside the four shapes runs, whoever wrote the box.
- Never pushes, never commits on `main` or `master`.
- `settings*.json` and `private/` are never copied by a copy step.

**Security model**: a live box may come from an unattended call (prompt injection included). The fixed shapes limit it to copying a repo file to the same path under `~/.claude`, the repo's own `install.sh`, and repo scripts under two fixed folders, all shown before your Enter. The repo must be on your trust list. A probe or install script edited by a call still runs as you; that is the same trust you give it when you run it by hand today, and the plan names each one.

**Configuration required**: none new.

**Critical test scenarios** (fake `claude`, temp live dir, temp repos):
- Two features with copy, install and probe boxes: one plan, Enter, copies backed up and equal, install once, checks run, verify.md lines, boxes ticked, one commit with only those files: AC-3 to AC-7.
- A box with a span outside the shapes (`rm -rf x`, `cp` with a flag, `cp` to another path, a probe with an argument, `cp settings.json`) runs nothing and is listed: AC-2.
- A failing copy stops before checks; a failing probe is recorded `FAIL (exit 1): <line>`, the next probe runs, its box stays open: AC-4, AC-5.
- A held lock refuses; an untrusted repo refuses; `WF_RUN` set refuses; no terminal without `-y` refuses; a missing trusted repo is skipped; `main` leaves edits uncommitted: AC-3, AC-7.
- A box with a command plus a `` `!` `` or a path in backticks is listed as yours: AC-2.
- Before the install, the backup holds `rules`, `agents`, `hooks`, `scripts` and `settings.json`: AC-4.
- A box edited between the plan and the tick is not ticked: AC-6.
- `wf run` refuses a live box as `waiting`: AC-1.
- `install.sh` into a temp live tree keeps `autoMode`, adds none when absent: AC-9.

## Build plan

Skateboard: the tag and plan first (useful as a read only list), then running, then recording and committing, then install.sh.

1. `LIVE` in `runner/wf.py`; `runner/finish.py` plan: repos, locks, live boxes, shapes, the printed plan and confirm, `wf finish` in the parser. Tests in `runner/tests/test_finish.py`, satisfies **AC-1**, **AC-2**, **AC-3**
2. Run phases: backup, copies, installs, checks, logs, failure policy, Ctrl C, satisfies **AC-4**
3. Record, tick, commit, end lines, report.seen, exit codes, satisfies **AC-5** to **AC-8**
4. `install.sh` keeps `autoMode`, self checks in `scripts/private-names.py --test`, satisfies **AC-9**
5. Repo copies of `rules/scope-contract.md` and `rules/runner-handoff.md` (copy files: never run `./sync.sh` before the live steps below, or it overwrites them); the architecture row for `wf finish` is already added by this spec's commit, satisfies **AC-10**
6. Live steps, one per box, each ` · waits on you · live`: `cp ~/claude-config/rules/scope-contract.md ~/.claude/rules/scope-contract.md`, `cp ~/claude-config/rules/runner-handoff.md ~/.claude/rules/runner-handoff.md`, satisfies **AC-10**

## Consequences

**Positive**:
- The morning's manual list becomes one command and one Enter.
- Check results land in verify.md the same way every time.
- `./install.sh` by hand is safe again for `autoMode`.

**Negative / tradeoffs**:
- A step shape not on the list (a phone check, a login, a real commit) stays a manual box; widening the list needs `/architect`.
- `wf finish` writes git history, an exception to "wf runs no git write command" that holds for `wf run` only.
- Checks can take many minutes; you wait at the keyboard or leave it running.

**Neutral**:
- Architecture invariant 7 and the components table name `wf finish`.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
