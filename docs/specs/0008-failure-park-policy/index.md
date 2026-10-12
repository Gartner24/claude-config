# 0008. Failure and park policy for `wf run`

**Date**: 2026-10-12
**Status**: Accepted
**Amended by**: [0009](../0009-headless-verify-test/index.md) - AC-1 park set gains `app_failed`, stop set gains `app_port_busy`; AC-3 snapshot is taken before the app starts and after it stops.

## Summary

Today `wf run` stops on any failure with a bare reason such as `no_progress` or `call_error`. This spec decides what happens instead. `wf` itself gives a failed `/check verify` two `/debug` attempts, retries a transient call error once, and waits through one usage limit reset per run. Everything else that only you can fix (sudo, a login, a hook denial, a debug call that touched the spec or a test) parks the feature with a reason you can read. A parked feature ends the run for now (feature 10 later moves on to the next one). Calls also lose every paid API key and cloud credential, and a repo must be on your own `wf allow` list before its `**Autopilot:** allowed` counts.

## What you're agreeing to

- A failed verify gets two `/debug` calls from `wf`, then parks. A debug call that edits the spec, `verify.md`, or deletes or skips a test parks right away.
- Sudo, logins, captchas, 2FA, hardware, hook denials and anything else you must fix park the feature with the reason in `run.json` and the terminal. Nothing pings you for a park.
- A usage limit makes the run sleep until the reset (at most 6 hours away, at most one reset per run), then it reruns the same call. A reset it cannot read, or a second limit, ends the run.
- Calls get no API keys, tokens, secrets or passwords in their env (your subscription login stays), and cannot read `~/.aws`, `~/.config/gcloud` or `~/.azure`.
- `wf run` refuses a repo you have not listed with `wf allow <repo>`, even when its scope says `allowed`.

## Requirements

**User stories**:
- As you, I want a failed verify to get a bounded fix attempt and then stop with a clear reason, so that a night is neither wasted on one stop nor burned in a loop.
- As you, I want anything only I can do (sudo, logins, a hook that said no) to park with the reason, so that the morning starts with what to fix, not with a bare `no_progress`.
- As you, I want a run that hits my session limit to pick up again after the reset, without eating the weekly usage I need by day.
- As you, I want no call to be able to bill me, and no cloned scope to start a run on its own say so.

**Acceptance criteria**:
- **AC-1** (park vs stop): every `stop_reason` is either a park (only this feature is stuck) or a stop (the whole run must end). Parks: `verify_failed`, `blocked`, `denied`, `debug_touched`, `no_progress`, `call_error` (including the one `wait()` raises when a call has no session id), `call_timeout`, `budget`, `decision_timeout`, `manual_box`, `waiting`, `no_command`, `no_feature`. Stops: `interrupted`, `max_calls`, `run_limit`, `usage_limit`, `spawn_failed`, `branch_changed`, `autopilot_off`, `scope_unreadable`, `guard_changed`, `ping_failed`, `internal_error`. `run.json` gets `parked: true` for a park, `false` for a stop, `null` for `feature_done`. The terminal prints `parked: <reason>: <detail>` or `stopped: <reason>: <detail>`. Exit codes stay as spec 0004 sets them (0, 130, 6): a park and a stop both exit 6, and only `parked` in `run.json` tells them apart. Start time refusals (exit 5) are not runs and get no `parked`. Nothing pings you for either.
- **AC-2** (verify FAIL loop): the unattended prompt asks a `/check verify` call that ends in FAIL to end its final message with `VERIFY FAIL: debug` when every failure is a bug, or `VERIFY FAIL: develop` when anything specced is missing or not applied. Any value other than `debug` reads as `develop`. On `VERIFY FAIL: debug`, with fewer than 2 debug attempts made in this run (counted across the whole run, never reset), `wf` makes one call running `/debug` followed by the verify box command minus its first two words, then the text `-- the last /check verify failed:` and the last 1500 characters of that verify call's `result` through `clean()` (newlines kept); when the verify call was resumed after a decision, that is the resume's `result`. A verify box with no arguments gives `/debug -- the last ...`. That call has kind `debug` (calls carry a kind: `box`, `debug` or `sync`; `box None` no longer means `/sync`), `box_text` null and no progress check; a resume of it keeps kind `debug`. The next call is whatever the scope's next box is (normally the same verify box). A `VERIFY FAIL: debug` after 2 debug attempts parks `verify_failed`, detail `2 debug attempts made`. `VERIFY FAIL: develop` parks `verify_failed` right away; detail is the marker line plus the 5 non empty lines before it, through `flat()`, first 300 characters. A debug call's own failures go through every other rule like any call.
- **AC-3** (debug guard): just before each debug call (not before its retry or resume), `wf` snapshots the guarded files: every file from `git ls-files -co --exclude-standard` that lies under the repo's specs folder (`docs/specs/`, or `.workflow/specs/` when the scope lives in `.workflow/`) or is a test file, as a map of path to sha256, plus each test file's text in memory. Changes left by earlier calls (an uncommitted `verify.md`, new tests from `/develop`) are part of the snapshot and never trip the guard. When the debug call (with its retry and any resumes) has finished, `wf` snapshots again and parks `debug_touched` (detail: the offending paths) when: a specs folder file was changed, added or deleted; a test file was deleted (a renamed or moved test file counts as deleted); an added line in a test file (a new test file read whole) matches a skip marker; or a test file has fewer test definition lines than before. Commits made by the call are covered because only file contents are compared. Patterns are the constants in Feature design. This runs before the BLOCKED, decision and progress rules.
- **AC-4** (BLOCKED marker): the unattended prompt says: never run `sudo`, never try to log in anywhere; when the step needs sudo, a login, a captcha, 2FA or hardware, and when `/check verify` ends BLOCKED, stop and end the final message with one line `BLOCKED: <what you need>`. `wf` reads the last such line (same line shape rules as `DECISION NEEDED:`) and parks `blocked` with that text. A `BLOCKED:` line wins over a `DECISION NEEDED:` line in the same result, and then no decision is recorded (`decision` is set only when a decision is parked).
- **AC-5** (denials): every call record gets `denials`: one entry per item of the JSON `permission_denials` with `tool` (`tool_name`), `input` (the `command` field, else the whole `tool_input` as JSON, cleaned, first 200 characters) and `reason` (the `toolUseResult` text for that `tool_use_id` in the call's session transcript, read line by line up to the first line holding the id, cleaned, first 200 characters; null when not found or on any read error). A box call that makes no progress and has at least one denial parks `denied`, detail `<tool>: <reason or input>` of the first denial whose tool is not `AskUserQuestion`, else the first. With no denials it parks `no_progress` as before. A call that progressed keeps going whatever it was denied.
- **AC-6** (call error retry): a failed call (no JSON, `is_error` true, a subtype other than `success`, or a nonzero exit) is a usage limit (AC-8), the budget cap, `error_max_turns` (parks `call_error`, never retried), or otherwise retryable. A retryable failure sets a `retried` flag and reruns once: a box, debug or sync call as a fresh call with the same command, a resume as `--resume` with the same session id and prompt. It is recorded with `retry_of: <n>` and counts toward `--max-calls`. Any call that does not fail clears the flag; a failure while the flag is set parks `call_error`. Before the rerun, `wf` rereads the scope and runs the guard (rule 7), as after a decision wait. A failure to start `claude` at all stops `spawn_failed`, with no retry.
- **AC-7** (no paid keys): on top of spec 0007 AC-1, one `call_env()` used by every call and resume removes every env var whose upper cased name ends in `_API_KEY`, `_API_TOKEN`, `_TOKEN`, `_SECRET`, `_ACCESS_KEY`, `_PASSWORD`, or contains `SECRET`, plus `AWS_ACCESS_KEY_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`. `CLAUDE_CODE_OAUTH_TOKEN` is kept (the login may need it). `~/.aws`, `~/.config/gcloud` and `~/.azure` join the spec 0007 `denyRead` list and get `Read(//<path>/**)` denies. The prompt adds: never run anything that bills (paid APIs, image generation, paid services).
- **AC-8** (usage limit): a failed call (AC-6 sense, never a successful one, checked after the budget subtype) whose `result`, subtype or stderr tail matches the limit pattern is a limited call: recorded with `limited: true`, not counted toward `--max-calls`. Then, in order:
  1. if this run already waited once for a limit, stop `usage_limit` with the limit text (one wait per run, fixed, no flag);
  2. if the reset does not parse (no match, or an unknown zone name), stop `usage_limit`;
  3. if the reset is more than 6 hours away, stop `usage_limit`, detail the reset time;
  4. else sleep until 2 minutes after the reset (a reset up to 2 minutes in the past sleeps 2 minutes), reread the scope and run the guard (rule 7), then rerun the same command, or the same resume (`--resume` with the same id and prompt), as a new call.
  The sleep length is worked out once from the wall clock, then slept on the boot clock in `POLL` slices. It keeps the inhibitor on, ends early on Ctrl C, SIGHUP or SIGTERM (stop `interrupted`), and its time goes into `limit_waited_s`, which `--max-hours` subtracts along with `waited_s`.
- **AC-9** (trust list): `wf allow <repo>` resolves the target with `wf.resolve` (its exit codes on failure) and adds `c.path`'s real path to `allowed.json` in the same config folder `ntfy.py` uses (`$XDG_CONFIG_HOME/wf`, else `~/.config/wf`; folder 0700, file 0600, written atomically), printing `allowed: <path>`. Running it again changes nothing. A worktree or a second clone has its own real path and needs its own `wf allow`; for a hub scope the path is the hub. `wf run` start checks, right after the Autopilot check, refuse `untrusted` (exit 5, no lock, no run folder) when the repo's real path is not in that file, the file is missing, or it is unreadable or not a JSON list of strings (the detail says which). `next` does not read it.
- **AC-10** (record): `run.json` gets `parked`, `debug_attempts`, `limit_wait` (`{started, reset, resumed, waited_s}` or null: `reset` the parsed wall clock time, `resumed` when the rerun starts, `waited_s` boot clock seconds) and `limit_waited_s`. Each call gets `kind` (`box`, `debug`, `sync`), `seq` (the call file number, every call) separate from the `--max-calls` count (calls not `limited`, shown as `[count/max]`), `denials`, `marker` (`blocked`, `verify_fail_debug`, `verify_fail_develop` or null), `limited`, `retry_of` and `touched` (list, debug calls only, else null).
- **AC-11** (probes): `verify.md` records the denial shape and the transcript reason source (both run 2026-10-12). The usage limit JSON shape is unconfirmed: the AC-8 pattern is built from the interactive message, and `verify.md` holds a one line probe for the next real limit. If that probe shows a shape the pattern misses, AC-8 goes back to `/architect`. With no readable reset the run stops, so a wrong guess costs a night, not your weekly usage.

## Decision

**Chosen option**: Option 1: `wf` owns the policy. It reads markers and the call JSON, drives the retries itself, and parks with a named reason.

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (no new storage besides the trust file):
- `~/.config/wf/allowed.json`: a JSON list of absolute real paths. Written only by `wf allow`; read by `wf run` at start.
- `run.json` additions (AC-10): record `parked` (bool or null), `debug_attempts` (int), `limit_wait` (object or null), `limit_waited_s` (float). Call `kind`, `seq`, `denials` (list of `{tool, input, reason}`), `marker`, `limited` (bool), `retry_of` (int or null), `touched` (list or null).

**Classification order after a call** (replaces spec 0004 AC-6; rule numbers here are this spec's):
1. Ctrl C or a stop signal: stop `interrupted`.
2. Timed out: park `call_timeout`.
3. `claude` did not start: stop `spawn_failed`.
4. Budget subtype: park `budget`.
5. Failed call (AC-6 sense) matching the limit pattern: AC-8.
6. Any other failed call: AC-6 retry, else park `call_error`.
7. Guard (`scope_unreadable`, `branch_changed`, `autopilot_off`, and spec 0007's `guard_changed`): stop.
8. Kind `debug` call (resumes included): AC-3 check, park `debug_touched`.
9. `BLOCKED:` line: park `blocked`.
10. `DECISION NEEDED:` line: park, ping, wait, resume (spec 0005, unchanged).
11. `VERIFY FAIL:` line on a `/check verify` call: AC-2.
12. Kind `sync` call: `feature_done`.
13. Box still open: park `denied` or `no_progress` (AC-5).
14. Next box in another feature: a `sync` call next. Next box refused (`manual_box`, `waiting`, `no_command`, `no_feature`): park with that reason.

Rules 4 to 6 rerun or sleep only after the rule 7 guard passes on a fresh reread.

**State transitions** (one run):
`running` -> (`call` -> classify) -> `running` | `waiting_decision` -> `running` | `waiting_limit` -> `running` | `parked` (end) | `stopped` (end) | `feature_done` (end).

**API surface** (CLI only):
| Surface | Inputs | Output | Errors |
|---|---|---|---|
| `wf allow <repo>` | target (path, folder name or scope title) | `allowed: <real path>`, exit 0 | `wf.resolve` exit codes (1 no match, picker cancel); unwritable file: message, exit 1 |
| `wf run <repo>` start | trust file | as today | `refused: untrusted: <detail>`, exit 5 |
| each call | env, argv | `call_env()` (AC-7), prompt with the AC-2, AC-4, AC-7 lines | |
| run end | | `parked: <reason>: <detail>` or `stopped: ...` | |

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| debug call | command | `/debug` + verify box command minus its first two words (scope box) |
| debug call | failure text | last 1500 characters of the verify call's `result`, through `clean()` |
| debug guard | guarded file list | `git ls-files -co --exclude-standard`, filtered to the specs folder and test files |
| debug guard | before and after | sha256 per file, plus test file text in memory, taken before the first debug attempt and after it ends |
| debug guard | specs folder | parent of the scope folder (`c.scope_dir`) joined with `specs/` |
| debug guard | added lines, definition counts | `difflib` over the before and after text of each test file; a new test file read whole |
| denial | tool, input | call JSON `permission_denials[].tool_name`, `.tool_input` |
| denial | park detail | first denial not `AskUserQuestion`, else the first |
| denial | reason | `toolUseResult` of the line with that `tool_use_id` in `<config dir>/projects/*/<session_id>.jsonl`, config dir `CLAUDE_CONFIG_DIR` else `~/.claude` |
| limit | reset time | limit pattern group in `result`, subtype or stderr tail; zone from the parenthesis via `zoneinfo`, next occurrence after now |
| limit | wait cap | fixed: one wait per run, 6 hours, 2 minutes margin |
| trust | listed or not | `os.path.realpath(c.path)` vs `allowed.json` in the `ntfy.py` config folder |
| max calls | count | calls not `limited`; `seq` numbers the files |
| max hours | elapsed | boot clock since start minus `waited_s` and `limit_waited_s` |
| park or stop | `parked` | the AC-1 sets, constants in `run.py` |

**Constants** (in `runner/run.py`):
- Limit pattern (case insensitive): `rate_limit|hit your (session |weekly )?limit|usage limit`. Reset: `resets (\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*\(([^)]+)\)`.
- Test file: a path segment `test`, `tests`, `__tests__` or `spec`, or a basename matching `test_*`, `*_test.*`, `*.test.*`, `*.spec.*`.
- Skip marker (added lines): `\b(skip|skipIf|skipUnless|xfail|xit|xdescribe|xtest)\b|\.skip\(|t\.Skip|@Disabled|@Ignore`.
- Test definition (removed lines): `^\s*(async\s+)?def test|^\s*(it|test|describe)\(|^\s*func Test|^\s*#\[test\]`.
- Paid env: suffixes `_API_KEY`, `_API_TOKEN`, `_TOKEN`, `_SECRET`, `_ACCESS_KEY`, `_PASSWORD`, substring `SECRET`, the AC-7 names; kept: `CLAUDE_CODE_OAUTH_TOKEN`.
- Cloud credential paths: `~/.aws`, `~/.config/gcloud`, `~/.azure`.

**Key invariants**:
- `wf` still writes nothing in a repo; a park is only `run.json` and the terminal.
- A successful call is never read as a usage limit, whatever its text says.
- The debug loop is bounded: at most 2 debug calls per run, and each verify FAIL after them parks.
- No retry ever repeats a call that parked or stopped for a reason other than AC-6 or AC-8.
- No ping for a park or a stop (architecture invariant 4 unchanged).

**Security model**: AC-7 closes the billing door the same way spec 0007 closes the push door: no credential in the call. AC-9 makes Autopilot opt in on your machine, not in the repo, so a cloned scope (and its standing answers, spec 0006) cannot start a run. Transcripts are read locally for the denial reason; only `run.json` holds the cleaned excerpt.

**Configuration required**: none new besides `wf allow`. `ANTHROPIC_API_KEY` is stripped by the AC-7 rule; calls use your subscription login.

**Critical test scenarios**:
- Park vs stop: each AC-1 reason ends with the right `parked` value, prefix and exit code, verifies **AC-1**
- Verify loop: fake claude prints `VERIFY FAIL: debug` three times; calls are verify, debug, verify, debug, verify, then park `verify_failed`; the debug command and the 1500 character tail match, verifies **AC-2**
- Develop: `VERIFY FAIL: develop` parks at once with no debug call, verifies **AC-2**
- Debug guard: a debug call that edits `docs/specs/x.md`; one that deletes `tests/test_a.py`; one that adds `@unittest.skip`; one that removes `def test_b` from a kept file; one that renames a test function inside one file and adds a new test passes; an uncommitted `verify.md` and new test left by earlier calls do not trip it; a debug call that commits a spec edit still parks, verifies **AC-3**
- BLOCKED: a `BLOCKED: sudo pacman -S stow` line parks `blocked` with that text, and wins over a `DECISION NEEDED:` in the same result, verifies **AC-4**
- Denials: a call JSON with two `permission_denials` and a fake transcript gives two records with reasons; with no progress it parks `denied`; with progress it continues; a missing transcript gives `reason: null`; an AskUserQuestion denial first and a Bash one second gives the Bash detail, verifies **AC-5**
- Retry: one `is_error` then success continues with `retry_of`; two in a row park `call_error`; a failed resume retries with the same session id; `error_max_turns` parks with no retry; a branch change before the retry stops `branch_changed`; a spawn failure stops `spawn_failed`, verifies **AC-6**
- Env: `GEMINI_API_KEY`, `AWS_SECRET_ACCESS_KEY`, `MY_SECRET_THING`, `ANTHROPIC_API_KEY`, `HF_TOKEN`, `AWS_ACCESS_KEY_ID`, `CLAUDE_CODE_USE_BEDROCK`, `DB_PASSWORD` absent from the call and resume env, `PATH` and `CLAUDE_CODE_OAUTH_TOKEN` present; the deny list and `denyRead` hold the three cloud paths, verifies **AC-7**
- Limit: a failed call with `You've hit your session limit` (U+00B7 middle dot) `resets 6:20am (America/Bogota)` sleeps (patched clock) to 6:22 and reruns the same command; a successful result containing `rate_limit` is not a limit; a budget subtype is not a limit; a second limit in the run stops `usage_limit`; a reset 30 hours away stops; an unparsed message or unknown zone stops; a reset 1 minute past sleeps 2 minutes; Autopilot set off during the sleep stops `autopilot_off`; Ctrl C during the sleep stops `interrupted`; limited calls do not count toward `--max-calls` and the sleep not toward `--max-hours`, verifies **AC-8**
- Trust: `wf allow` twice leaves one entry, mode 0600, under `XDG_CONFIG_HOME` when set; a repo not listed, a missing file and a broken file each refuse `untrusted` exit 5 with no lock, verifies **AC-9**
- Record: `run.json` fields after a mixed run, verifies **AC-10**
- Real claude: the verify.md checks, verifies **AC-11**

## Build plan

Skateboard: each step leaves `wf run` usable and stricter than before. Spec 0007 (feature 20) is built first; step 7 extends its env and deny lists.

1. Trust list: `wf allow`, `allowed.json`, the `untrusted` refusal, an `allowed.json` fixture for every existing `wf run` test, tests, satisfies **AC-9**
2. Call kinds (`box`, `debug`, `sync`) and `seq` vs counted calls, park vs stop sets, `parked` in `run.json`, `parked:` and `stopped:` lines, `call_timeout` and mid run box refusals as parks, `spawn_failed`, tests, satisfies **AC-1**, **AC-10**
3. Call error retry with `retry_of`, tests, satisfies **AC-6**
4. Prompt lines and the `BLOCKED:` reader, park `blocked`, tests, satisfies **AC-4**
5. Denials: `denials` per call, transcript reason lookup, park `denied`, tests, satisfies **AC-5**, **AC-10**
6. Verify loop and debug guard: `VERIFY FAIL:` reader, debug call, `debug_attempts`, the diff checks, tests, satisfies **AC-2**, **AC-3**, **AC-10**
7. Paid key strip and cloud `denyRead` on the spec 0007 lists, tests, satisfies **AC-7**
8. Usage limit: detection on failed calls only, reset parse, one sleep per run, guard after the sleep, `limit_wait` record, clock rules, tests, satisfies **AC-8**, **AC-10**
9. Manual checks in `verify.md` on the real claude (a `BLOCKED:` and a `VERIFY FAIL:` from a real call, the env strip), and the limit probe when a real limit happens, satisfies **AC-11**

## Consequences

**Positive**:
- A night ends with a named reason per feature instead of `no_progress`, and feature 10 can move on from every park without reopening this list.
- Architecture invariant 3 (no paid steps unattended) holds below the model, and the Autopilot opt in lives on your machine.

**Negative / tradeoffs**:
- The `VERIFY FAIL:` and `BLOCKED:` markers depend on the model following the prompt; a call that forgets them falls back to `no_progress` or `denied`, a park with less detail.
- The debug guard reads patterns, so an unusual test framework's skip or definition can slip past it, and a legitimate test rename across files parks.
- Stripping every `SECRET` named var can remove one a build step legitimately needs; that step then fails and parks.
- The limit pattern is unconfirmed for `claude -p` until a real limit happens, and a reset it cannot read ends the run instead of waiting.
- Repo files such as `.env` stay readable by a call; only env vars and the listed credential folders are removed.

**Neutral**:
- Amends spec 0004 (AC-6 order and the stop reason list, follow up on `no_progress` and `call_error`) and spec 0007 (AC-1 env list, AC-2 `denyRead`, AC-5 `Read` denies). `/develop` notes both amendments when it builds steps 2 and 7.
- Architecture page: invariant 3 loses its open gap, invariant 6 gains the trust list, invariant 8 gains the limit wait bound.

## Follow-up

- [ ] Run the limit probe in `verify.md` (Follow-up, check 3) at the next real usage limit; if the shape differs, `/architect failure and park policy` again. · waits on you
- [ ] Feature 10 moves on after a park (`parked: true`) and ends the run on a stop.
- [ ] Spec 0003 follow up (cloned scope writing `allowed`) and spec 0006 follow up (cloned scope with standing answers) close when AC-9 ships.
- [ ] `/test` has no parseable verdict, so a red suite parks `no_progress`; give it the two debug attempts only if that turns out to be common.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
