# 0004. Headless step loop: `wf run` builds one feature unattended

**Date**: 2026-10-11
**Status**: Accepted
**Amended by**: [0005](../0005-decision-parking-phone-pings/index.md) - AC-5 prompt, AC-6 rule 6 (`DECISION NEEDED:` parks, `decision_needed` leaves the `stop_reason` enum), and the "nothing is resumed" invariant (a resume call continues the asking session). Review 2026-10-12: AC-6 rules 7 and 8 (`branch_changed`, `autopilot_off`, with `scope_unreadable`) now run before rule 6 and again after each wait, so a parked call never pings and a resume never starts off Autopilot or off the run's branch; the push and PR deny patterns match any flags between the program and the subcommand; elapsed time is on `CLOCK_BOOTTIME`, the `waited_s` clock. Architecture pass 2026-10-12 ([architecture](../../architecture.md)): the body now states those amendments in place (Summary, AC-2 note, AC-5, AC-6 order, AC-7, AC-8, stop reasons, invariants, follow ups), with no behavior change.

## Summary

`wf run <repo>` builds one feature with nobody at the keyboard. It runs each open box of that feature as a fresh `claude -p` call inside the repo (a fresh call is the same as a `/clear`), rereads the scope after every call to find the next box, and ends with one `/sync` call. It refuses repos whose scope header is not `**Autopilot:** allowed`, refuses `main`, `master` and a detached checkout, runs only build, check, test, debug and document boxes, holds a lock so two runs never share a repo, keeps the laptop awake even with the lid closed, caps each call and the whole run, stops cleanly on Ctrl C or a closed terminal, and writes a record of every call. A step that needs your decision parks it, pings your phone and resumes with your answer (spec 0005).

## What you're agreeing to

- Nothing new: the 2026-10-12 amendment rewrites this spec's text to match what `wf run` already does after specs 0005 and 0006.
- A question from a step now waits for your phone instead of ending the run.
- After every call and every wait, the run checks Autopilot, the branch and the scope before it does anything else.
- Time spent waiting for you does not count toward the hour cap.

## Requirements

**User stories**:
- As you, I want `wf run claude-config` to take a feature from `/develop` to `/sync` with no typing, so that a build finishes while I am away.
- As you, I want a run to stop with a reason I can read (a question, a failure, a cap) rather than loop, guess, or push.

**Acceptance criteria**:
- **AC-1**: `wf run [path or name]` finds its repo exactly as `wf next` does (spec 0002 AC-1 to AC-4 and AC-11: path, exact then substring name match, current folder walk, fzf picker, cancelling the picker exits 0, a missing or failing fzf exits 1). The resolution moves out of `cmd_next` into a shared `resolve(args)` that both commands call. The run's feature is the display feature (spec 0002 `NextBox.feature`) of the first open box when the run starts; a first open box outside any `###` heading (feature `None`) is refused (AC-2). `wf run` ignores the `· auto` tag (spec 0003 AC-5); the queue (feature 10) owns it.
- **AC-2**: Before any call, checks run in this order, and the first that applies ends the command:
  1. no open box: `nothing to run in <name>`, with hub rows and warnings, exit 0 (spec 0002 AC-7 output, moved out of `launch` into a shared helper);
  2. a box with no command: spec 0002 AC-6 message, exit 3 (same shared helper);
  3. the box has no feature (`NextBox.feature` is `None`): refused, `no_feature`;
  4. the box command's first word is not one of `/develop`, `/check`, `/test`, `/debug`, `/document`: refused, `manual_box` (design, scope, audit, ship, PR, deploy and review stack boxes stay with you);
  5. the box is waiting (spec 0002 AC-6 `waiting`): refused, `waiting`;
  6. the scope's Autopilot value (spec 0003 AC-1 and AC-2, missing means `off`, read by a new `header_values(text)`; `header_warnings` keeps its return type) is not `allowed`: refused, `autopilot_off`;
  7. the branch read from the files (`head_branch`, spec 0002 AC-12) is `main`, `master`, `no git`, `-`, or starts with `detached`: refused, `branch`;
  8. `claude` missing from PATH: exit 1 (spec 0002 AC-14 message);
  9. another `wf run` holds this repo's lock (AC-9): refused, `locked`, naming the holder's pid and start time (`unknown` when the holder line is still empty).
  Two later checks join this list: `bad_answers` right after check 6 (spec 0006 AC-3) and `no_ntfy` right after check 8, before the lock (spec 0005 AC-2).
  A refusal prints `refused: <reason>: <detail>` and exits 5. Header warnings print as `warning: <text>` lines on every path, as in spec 0003 AC-3. No run folder is created and no call is made before the confirm. Ctrl C anywhere before the confirm exits 130 with no traceback.
- **AC-3**: The confirm line has the same shape as `next` (spec 0002 AC-8), with the branch from `head_branch` (the value the checks read, not `branch()`): name and label, branch, change count, feature, first command, note, then `caps: <budget> USD/call, <call timeout>m/call, <max calls> calls, <max hours>h`, then warnings (including `N session(s) already open here`, spec 0002 AC-10, which never refuses). An empty line starts the run. Anything else, Ctrl C or end of input exits 130. `-y` starts with no wait. With stdin not a terminal, `-y` is required, else exit 130. There is no tmux or exec mode: `wf run` stays in the foreground.
- **AC-4**: Each step is one call, with the repo as working folder, stdin from `/dev/null`, in a new session (`start_new_session=True`, so a terminal Ctrl C reaches `wf` only), stdout and stderr written straight to the run folder, argv exactly:
  `claude -p <command> --output-format json --permission-mode auto --permission-prompts none --max-budget-usd <budget> --disallowedTools AskUserQuestion,Bash(git push*),Bash(git * push*),Bash(gh pr create*),Bash(gh pr merge*),Bash(gh pr ready*),Bash(gh * pr create*),Bash(gh * pr merge*),Bash(gh * pr ready*) --append-system-prompt <UNATTENDED_PROMPT>`
  as an argument list, never through a shell, in exactly this order: the prompt comes right after `-p`, before the variadic `--disallowedTools`, which the next flag ends. `<budget>` is formatted with `%g`. No `--model` or `--effort`: your settings decide. `<command>` is the box command, or `/sync` for the final call. The deny list is a best effort guard (a push written another way can slip past it); AC-15 check 4 tests the common form. A spawn that fails (`OSError`) is classified `call_error`.
- **AC-5**: `UNATTENDED_PROMPT` is the text of spec 0005 AC-3 (it replaced this spec's first prompt), and each call passes it with the repo's standing answers appended per spec 0006 AC-5.
- **AC-6**: After each call the loop rereads the scope and reads the branch again, then classifies the call. The reread builds only the next box and the header values from the scope files (no `git worktree` call); if the scope folder or its top file is gone or unreadable, the run stops with `scope_unreadable`. The first matching rule decides:
  1. the Ctrl C flag (AC-12) is set at classification time: stop, `interrupted`; the finished call is still recorded;
  2. the call hit its timeout and the SIGINT was actually sent: stop, `call_timeout` (AC-8);
  3. stdout is neither one JSON object nor a JSON array whose last element with `type` equal to `result` is taken as the object: stop, `call_error`;
  4. the JSON `subtype` contains `budget`: stop, `budget`;
  5. `is_error` is true, `subtype` is not `success`, or the exit code is not 0: stop, `call_error`;
  6. the guard, in this order: the scope is gone or unreadable: stop, `scope_unreadable`; the branch differs from the one at start: stop, `branch_changed`; the Autopilot value is no longer `allowed` (you flipped it, or a call edited it): stop, `autopilot_off`. The same guard runs again after every wait, before the resume call (spec 0005);
  7. the JSON `result` (null or missing reads as empty, `\r` stripped) holds a decision in the spec 0005 AC-4 shape: the decision is parked, pinged and waited on, and the answer resumes the same session (spec 0005 AC-6, AC-10);
  8. reserved (rule 8 moved into rule 6; numbers kept so older references still read);
  9. for a box step: the next box has the same feature, box text and note as the box just run: stop, `no_progress`;
  10. no open box is left, or the next box's feature differs from the run's feature: the feature is finished, go to AC-7;
  11. otherwise the next box gets start checks 2 to 5 of AC-2 (no command, `no_feature`, `manual_box`, `waiting`); one that applies stops the run with that reason; else the loop runs it.
  The `call_error` detail is the subtype, the first 200 characters of `result`, and the last 5 lines of stderr (a usage limit error shows only in `result`). Every question, result excerpt and stderr line goes through `clean()` before it is printed or stored as `detail`.
- **AC-7**: When the feature is finished, the loop makes one more call running `/sync` (AC-4), after the AC-8 cap checks like any call, and classified by rules 1 to 7 of AC-6. It has no box: `box_text` is null, no progress check applies, and its line prints `next: -`. A decision on it parks and resumes like any call (spec 0005 AC-11). If it passes, the run ends with `feature_done`, exit 0. The `/sync` call counts toward the call cap, so a feature with as many boxes as `--max-calls` stops with `max_calls` before `/sync`.
- **AC-8**: Caps, each with a flag and a default: `--budget` USD per call (default 20, passed as `--max-budget-usd`), `--call-timeout` minutes per call (default 60), `--max-calls` per run (default 20), `--max-hours` per run (default 8). Each flag takes a positive finite number (`math.isfinite`, so `nan` and `inf` are rejected; `--max-calls` a positive integer); anything else is a usage error, exit 2. Before each call, `/sync` included: if `max calls` calls have been made, stop, `max_calls`; if `max hours` have passed since the confirm, not counting time spent waiting for your answers (spec 0005 AC-9), stop, `run_limit`. A call still running past its timeout gets SIGINT to its process group, then SIGKILL to the group 30 seconds later if it has not exited, and is classified `call_timeout`. The run limit never cuts a running call short.
- **AC-9**: The lock is `fcntl.flock(LOCK_EX | LOCK_NB)` on `<state>/locks/<sha1 of the repo real path>.lock`, taken after the start checks and before the confirm, and held until the process exits. The file is opened without truncating (`os.open` with `O_RDWR | O_CREAT`, mode `0o600`); only after the lock is won is it truncated and the holder line `<pid> <ISO start time>` written. A loser reads that line for its refusal message. The `locks/` and `runs/` folders are created with mode `0o700`. The kernel releases the lock if `wf` dies. `<state>` is `$XDG_STATE_HOME/wf`, else `~/.local/state/wf`. A state folder that cannot be created or written is a refusal, `state_unwritable`, exit 5, before the confirm.
- **AC-10**: A started run writes `<state>/runs/<name>-<YYYYmmdd-HHMMSS>-<pid>/`: `run.json` (Data model sketch), rewritten after every call and at the end, each time atomically (write `run.json.tmp`, then `os.replace`), plus `call-NN.json` and `call-NN.stderr` per call (NN from 01). A run stopped by any reason still ends with `ended` and `stop_reason` set; an uncaught Python exception after the confirm is caught by a `try/finally` that records `internal_error` with the exception's last line as `detail`, cleans up (AC-12), and exits 6.
- **AC-11**: The terminal shows one line per call, `[<n>/<max calls>] <command> -> <subtype or error>, <cost> USD, <minutes>m, next: <next command>`, where cost has 2 decimals or `-` when `total_cost_usd` is absent, minutes has one decimal, and `next:` shows `-` when the call stopped the run or there is no next box. Then one final line: `done: <feature>` or `stopped: <reason>: <detail>`, then `run folder: <path>`.
- **AC-12**: The SIGINT handler is installed right after the confirm, before the lock holder line, the inhibitor and the first call; the flag is checked right after each spawn so a signal during spawn is not lost. SIGHUP and SIGTERM to `wf` are handled exactly like the first Ctrl C, so a closed terminal never leaves a call running without its lock. The first Ctrl C sets the flag, sends SIGINT to the running call's process group, and waits for it to exit up to the 30 second grace (AC-8), then SIGKILLs the group; the call is recorded, the run stops with `interrupted`, exit 130. A second Ctrl C kills the call's group at once. Ctrl C between calls, before the first call or during `/sync` stops with `interrupted`, exit 130. On every exit path after the confirm the lock is released, the inhibitor is stopped and `run.json` is final.
- **AC-13**: For the whole run (confirm to exit), `wf` keeps the machine awake, lid closed included, with its own child, started in a new session: `systemd-inhibit --what=idle:sleep:handle-lid-switch --who=wf --why=wf run <name> kde-inhibit --power --screenSaver tail --pid=<wf pid> -f /dev/null`. `tail --pid` ends the inhibitor on its own when `wf` dies, even by `kill -9`. With no `kde-inhibit`, it drops that part and warns `kde-inhibit not found, the screen may still blank`. With no `systemd-inhibit`, it runs without one and warns `systemd-inhibit not found, the machine may sleep`. At exit, on every path, it kills that child's process group. It never stops a `nosleep` you started yourself.
- **AC-14**: Exit codes: 0 nothing to run, picker cancelled, or `feature_done`; 1 no match, `claude` missing, or `fzf` missing or failing for a picker (spec 0002 AC-4); 2 usage error; 3 no command at start; 5 refused before start; 6 stopped after start for any reason except `interrupted`, `internal_error` included; 130 Ctrl C before or at the confirm, or `interrupted` at any point after it.
- **AC-15**: Manual checks against the real `claude`, recorded in `verify.md`, since every automated test uses a fake:
  1. `--budget 0.01` on a real step stops with `budget`; the exact `subtype` string and the real stdout shape (object or array) are recorded (AC-6 rules 3 and 4 assume an object and a `subtype` containing `budget`; if not, those rules are corrected in this spec first);
  2. a step asked to make a choice ends with a `DECISION NEEDED:` line and stopped with `decision_needed` (done before spec 0005; a decision now parks), and the call never used AskUserQuestion;
  3. the done when: in a scratch repo with `**Autopilot:** allowed`, on a work branch, a small feature runs from its `/develop` box to `/sync` with no typing and ends `feature_done` (this also proves `--permission-mode auto` works on your plan and model); a second `wf run` started on it meanwhile is refused `locked`; `--max-calls 1` on a feature with two open boxes stops with `max_calls`;
  4. a step told to run `git push` and `git -C . push` gets both denied, and nothing reaches the remote.

## Decision

**Chosen option**: Option 1: Own driver around `claude -p`, inside `wf`

`wf run` is a stdlib loop in a new `runner/run.py`: one fresh `claude -p` call per box, the next box recomputed from the files after each call, caps and a lock in the driver, ending with a `/sync` call.

## Feature design

**Data model sketch** (files only, no database):

| Entity | Field | Type | Notes |
|---|---|---|---|
| Run (`run.json`) | `repo` | string, required | real path |
| | `name`, `feature`, `branch` | string, required | feature as `next` displays it; branch at start |
| | `started` | ISO time, required | |
| | `ended` | ISO time, null while running | |
| | `stop_reason` | enum, null while running | `feature_done`, `no_feature`, `manual_box`, `waiting`, `no_command`, `no_progress`, `decision_timeout`, `ping_failed` (both spec 0005; `decision_needed` is a legacy value), `call_error`, `budget`, `call_timeout`, `max_calls`, `run_limit`, `branch_changed`, `autopilot_off`, `scope_unreadable`, `interrupted`, `internal_error` |
| | `detail` | string, nullable | the question, stderr tail, or cap that stopped it |
| | `caps` | object, required | `budget_usd`, `call_timeout_min`, `max_calls`, `max_hours` as used |
| | `calls` | list of Call, 1:N | |
| Call (in `calls`) | `n` | int, required | from 1 |
| | `command` | string, required | |
| | `box_text` | string, nullable | null for `/sync` |
| | `started`, `duration_s` | ISO time, number | |
| | `exit_code` | int, nullable | null when killed |
| | `session_id`, `subtype`, `is_error`, `cost_usd`, `num_turns` | from claude's JSON | null when stdout was not JSON |
| | `next_after` | string, nullable | next box command after the call, null when none |
| | `decision` | string, nullable | the `DECISION NEEDED:` question |

Specs 0005 and 0006 add `decisions`, `waited_s`, `caps.max_wait_h` and `answers` to the Run, and `resumes` and `last_box` to each Call.

Raw output sits beside it: `call-NN.json` (stdout), `call-NN.stderr`. The lock file holds `<pid> <ISO start time>` and nothing else.

**State transitions** (one run):
`resolving -> refused (exit 5) | cancelled (exit 130) | confirmed -> calling <-> classifying (<-> waiting for your answer, spec 0005) -> syncing -> feature_done`. Any classifying or cap check can end in `stopped` with a `stop_reason`; Ctrl C ends in `interrupted` from any state after confirm.

**API surface** (command line):

| Command | Key inputs | Key outputs | Exit codes |
|---|---|---|---|
| `wf run [path or name] [-y] [--budget USD] [--call-timeout MIN] [--max-calls N] [--max-hours H]` | target (opt), `-y` (opt), caps (opt, defaults 20, 60, 20, 8) | confirm line, one line per call, final line, run folder path | 0, 1, 2, 3, 5, 6, 130 (AC-14) |

`wf run` takes no `--list`. The `next` shortcut stays `wf next` only.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| resolve | repo, name, label, scope | spec 0002 discovery and matching, reused (`make_candidate`, `match`, `from_cwd`, `pick`) |
| resolve | run feature | `NextBox.feature` of the first open box at start |
| start checks | feature present | `NextBox.feature` is not `None` |
| start checks | manual box | first word of `NextBox.command` not in the allow list `/develop`, `/check`, `/test`, `/debug`, `/document` (fixed in `run.py`) |
| start checks | waiting | `NextBox.waiting` (spec 0002 AC-6) |
| start checks | Autopilot value | the scope top file header, read per spec 0003 AC-1 and AC-2 (`header_warnings` grows to return the values too) |
| start checks | branch | `head_branch(path)`, files only, no git run |
| start checks | lock holder | the lock file's `<pid> <start time>` |
| confirm | change count, open sessions | `changes()` and `open_sessions()` from spec 0002 |
| confirm, caps | caps | the four flags, else defaults 20 USD, 60 min, 20 calls, 8 h (decided with you, this spec) |
| call | argv, prompt | AC-4, AC-5 (fixed text in `run.py`) |
| call | state folder | `$XDG_STATE_HOME/wf`, else `~/.local/state/wf` |
| call | run folder name | candidate `name`, local start time `%Y%m%d-%H%M%S`, and `wf`'s pid |
| classify | subtype, is_error, result, cost, session id, turns | claude's JSON on stdout (one object, or the last `type: result` element of an array): `subtype`, `is_error`, `result`, `total_cost_usd`, `session_id`, `num_turns` |
| classify | decision | last line of `result` matching `^DECISION NEEDED:\s*(.+)$` (`re.M`, `\r` stripped, null result reads empty), passed through `clean()` |
| classify | Autopilot mid run | `header_values()` on the reread top file |
| classify | call_error detail | `subtype`, first 200 characters of `result`, last 5 lines of `call-NN.stderr`, all through `clean()` |
| classify | progress | `(feature, box_text, note)` of the next box before and after the call |
| classify | branch drift | `head_branch(path)` before the first call vs after each call |
| caps | elapsed time | `CLOCK_BOOTTIME` since the confirm, the clock `waited_s` uses (amended by review 2026-10-12) |
| timeout | grace before SIGKILL | 30 seconds, fixed |
| per call line | minutes, cost | `duration_s / 60` to one decimal, `total_cost_usd` to 2 places (`-` when absent) |
| inhibitor | command | AC-13: your `nosleep` inhibitors plus `handle-lid-switch` (asked for by you, unlike `nosleep`), `--who=wf`, held by `tail --pid=<wf pid>` |
| signals | stop triggers | SIGINT, SIGHUP, SIGTERM to `wf` (AC-12) |

**Key invariants**:
- At most one `wf run` per repo real path at a time (kernel lock).
- No call starts without `**Autopilot:** allowed` (checked before every call), a named branch other than `main` or `master`, an allow listed command, and an empty line or `-y` at the confirm.
- A call never outlives its `wf`: SIGHUP and SIGTERM stop it like Ctrl C, and the inhibitor ends with `wf` even on `kill -9`.
- Every box starts a fresh session; only a resume with your answer continues one (spec 0005).
- A box only counts as done when the files say so; nothing a call prints ticks a box.
- `wf` itself never commits, pushes, or edits a repo file; only the claude calls do.
- Every call is denied AskUserQuestion and the common forms of `git push`, `gh pr create`, `gh pr merge`, `gh pr ready` (best effort, AC-4).
- Every started run leaves a `run.json` with `stop_reason` set, and leaves no inhibitor child behind.

**Security model**:
- Local, one user. A scope is trusted only after you set `**Autopilot:** allowed` yourself; refusing cloned scopes that ship it set is feature 8.
- Calls run in auto mode with prompts denied, so anything your classifier would ask about is refused, not waited on. Your guard hooks still run inside `-p` calls, including the Bash shape hook and the design Stop hook; a denial there shows up as `no_progress` or `call_error` until feature 8 parks on it.
- Only allow listed commands run unattended, so a box that posts, bills, pushes or needs your design input (`/architect`, `/scope`, `/ship`, `/pr`, `/review-stack` and the like) stops the run.
- The unattended prompt marks web content as data. Push and merge are denied per call, not only by prompt.
- No credentials, no network of its own; `claude` uses your subscription login.

**Configuration required**:
- `XDG_STATE_HOME` (optional, standard): moves the state folder; tests point it at a temp folder.

**Critical test scenarios** (unittest, fake `claude` on PATH that reads a script file: which scope lines to tick, what JSON to print, what exit code, how long to sleep; plus a fake `systemd-inhibit`):
- Happy path: fixture feature with two open boxes, `wf run <fixture> -y`; fake ticks one box per call; three calls (two boxes, `/sync`), `feature_done`, exit 0, `run.json` has three calls with the right commands, verifies **AC-1**, **AC-6**, **AC-7**, **AC-10**, **AC-11**, **AC-14**
- Argv: the fake records argv; it equals AC-4 element for element (the prompt right after `-p`, before `--disallowedTools`) with the AC-5 prompt and the cap flags, cwd the repo, stdin not a terminal, verifies **AC-4**, **AC-5**, **AC-8**
- Start refusals: one fixture per check of AC-2 (no box, no command, a box outside any `###`, `/architect` and `/scope` boxes, waiting box, Autopilot missing and `off`, branch `main`, detached and no git, lock held by another process, unwritable state folder) gives the right message and exit code, makes no call, creates no run folder; the confirm line shows the `head_branch` value, verifies **AC-1**, **AC-2**, **AC-9**, **AC-14**
- Confirm: `n`, end of input, and no `-y` with stdin not a terminal exit 130; the line shows the caps and an open session warning, verifies **AC-3**
- Classification: fake prints non JSON; a JSON array ending in a `type: result` element (read as success); `subtype` with `budget`; `is_error` true while ticking a box; null `result`; a `DECISION NEEDED:` line with `\r\n` endings; switches `.git/HEAD`; flips `**Autopilot:**` to `off`; deletes the scope; ticks nothing. Each gives its stop reason (or success) and exit 6; a control character in the question is stripped, verifies **AC-6**
- Next box inside the feature: after a call, the next box is waiting, then `/architect`, then has no command; each stops with its reason, verifies **AC-6**
- Feature boundary: after the last box, the next open box belongs to another feature; the run calls `/sync`, not that box, with `box_text` null and `next: -`; a failing `/sync` stops `call_error`; a `/sync` printing `DECISION NEEDED:` parks like any call, verifies **AC-7**
- Caps: `--max-calls 1` stops `max_calls`; two boxes with `--max-calls 2` stop `max_calls` before `/sync`; `--max-hours` tiny stops `run_limit` before the second call; `--call-timeout` tiny with a sleeping fake gets SIGINT and stops `call_timeout`; a fake ignoring SIGINT is killed after the grace (the grace constant patched on the `run` module, short in the test); `0`, `-1`, `nan`, `inf` and `1.5` for `--max-calls` exit 2, verifies **AC-8**
- Lock: a second `wf run` while the first holds the lock is refused with the holder pid, and the holder line is still intact afterwards; after the first exits, a new run starts; folders are `0o700` and the lock file `0o600`, verifies **AC-9**
- Record: `run.json` is valid JSON after every call (no partial file is ever left); a forced exception in the loop records `internal_error`, exits 6, and leaves no inhibitor, verifies **AC-10**, **AC-14**
- Output: a 20 second call prints `0.3m`; absent cost prints `-`, verifies **AC-11**
- Signals: SIGINT to `wf` during a sleeping fake call forwards SIGINT to the group, records `interrupted`, exits 130, leaves no inhibitor process; two SIGINTs kill the call; SIGHUP and SIGTERM behave like the first SIGINT; a SIGINT between calls stops with no further call, verifies **AC-12**, **AC-13**
- Inhibitor: fake `systemd-inhibit` records argv; the argv contains `--what=idle:sleep:handle-lid-switch` and `tail --pid=<wf pid>`; it is gone after exit on success, stop and interrupt; with no `kde-inhibit` or no `systemd-inhibit` the warnings print, verifies **AC-13**
- Manual: the four real claude checks, verifies **AC-15**

## Build plan

Skateboard: milestone 1 is already a usable loop on your own repo (you watch it, Ctrl C kills it); each next milestone makes it safe to leave alone.

1. `runner/run.py` with `wf run` (imported lazily from `wf.py`): `resolve(args)`, the shared nothing to run and no command output, and `header_values()` extracted in `wf.py`; start checks 1 to 8, the confirm line, the call argv and prompt, classification rules 3 to 11, the `/sync` call, the per call and final lines, exit codes, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**, **AC-5**, **AC-6**, **AC-7**, **AC-11**, **AC-14**
2. Lock and run record: the state folder and modes, the non truncating flock and holder line, atomic `run.json`, the raw call files, the `internal_error` finally, satisfies **AC-2**, **AC-9**, **AC-10**, **AC-14**
3. Caps: the four flags and checks, budget subtype, call timeout with the SIGINT then SIGKILL grace on the group, satisfies **AC-6**, **AC-8**
4. Leaving it alone: SIGINT, SIGHUP and SIGTERM handling, the inhibitor child with the lid switch and `tail --pid`, branch drift, cleanup on every path, satisfies **AC-6**, **AC-12**, **AC-13**
5. Manual real claude checks in `verify.md`, satisfies **AC-15**

## Consequences

**Positive**:
- One feature goes from `/develop` to `/sync` with no typing, which is the Release 2 milestone.
- Every stop has a reason and a record; the morning report (feature 13) and queue (feature 10) build on `run.json` and the lock.

**Negative / tradeoffs**:
- Any panel without a fixed answer (spec 0005) or a standing answer (spec 0006) pings you, and the run waits up to `--max-wait` for it.
- The dollar budget is the notional cost Claude Code reports on a subscription; it limits size, not spend, and depends on `--max-budget-usd` behaving the same on a subscription login (checked in AC-15).
- `no_progress` stops at the first call that ticks nothing, so a step that needed two sessions for one milestone stops the run; retries are feature 8.
- If `/develop` already chained `/sync` inside its own call, `/sync` runs twice. It is surgical, so the cost is one call.
- The prompt can only ask a step to end with `DECISION NEEDED:`; a step that ignores it ends as `no_progress`, still a stop, with a less useful reason.
- The lid switch is inhibited for the run, unlike your `nosleep`, which leaves it alone so a laptop in a bag cannot overheat. A run with the lid closed in a bag keeps working and keeps heating.
- The allow list stops a run at any box whose command is not `/develop`, `/check`, `/test`, `/debug` or `/document`, even a harmless one; widening it is a spec change.
- The deny list catches the common ways to push and open, merge or ready a PR, not every spelling.
- Two boxes in a row with identical feature, text and note give a false `no_progress` after a real tick. A heading renamed mid run makes the feature look finished, so `/sync` runs early. Both are safe stops.
- `--permission-mode auto` may not be available on every plan or model; if not, every call fails with `call_error` (AC-15 check 3 shows it).
- Python adds a second copy of `wf` when `wf.py` runs as the main script and `run.py` imports `wf`; tests patch constants on `run`, never on `wf`.

**Neutral**:
- `wf.py` keeps the shared parsing; `run.py` imports it. Python resolves the `~/.local/bin/wf` symlink, so the import works from the repo folder.
- The loop does no git work. Checkpoint commits, squashing and draft PRs are feature 14; until then, a run leaves its work uncommitted on the branch, or committed however the skills commit.

## Follow-up

- [x] AC-15 step 1 records the real budget `subtype`: `error_max_budget_usd`, rule 4 holds (verify.md).
- [ ] Feature 8 (failure and park policy) replaces `no_progress` and `call_error` stops with its retry and park rules, and refuses an `allowed` you did not set yourself.
- [x] Feature 5 replaced the `DECISION NEEDED:` stop with parking and phone pings; the AskUserQuestion deny stays (spec 0005 invariants).
- [ ] Feature 10 (queue): skip waiting boxes instead of refusing on them.
- [ ] Root `AGENTS.md` Commands: `wf run` and the state folder; `/sync` owns this.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
