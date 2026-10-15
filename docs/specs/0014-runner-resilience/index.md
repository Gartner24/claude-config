# 0014. Runner resilience

**Date**: 2026-10-12
**Status**: Accepted
**Paths:** `runner/run.py`, `runner/wf.py`, `runner/e2e/run.py`, `runner/e2e/fixture/**`, `claude-home/rules/scope-contract.md`, `runner/tests/test_resilience.py`
**Amends**: [0003](../0003-scope-contract/index.md) (the `· later boxes go on` tag, a `/sync` box), [0004](../0004-headless-step-loop/index.md) (AC-4 argv gains `--session-id`, AC-11 final lines), [0008](../0008-failure-park-policy/index.md) (classification order gains the outage rule, AC-10 record fields), [0011](../0011-build-decision-queue/index.md) (AC-3 next box pick, AC-9 run stops `api_outage` and `crash_loop`, AC-10 `cap` on a timeout that ticked boxes), [0012](../0012-waiting-boxes-owed-to-you/index.md) (a tagged waiting box is skipped, not refused).

## Summary

Eight small changes that make `wf run` harder to break and easier to watch. An API outage now makes the run wait and retry instead of parking every feature in turn. The same failure in two features in a row ends the run. Each run counts its tokens and cost. A call that times out never passes silently: the boxes it ticked are named for you to recheck. A fixture repo gives `wf` a real end to end test. A live log shows what a hung call is doing. And two scope rules get fixed: a `/sync` box now runs (as the feature's last call), and a box that waits on you can let later boxes go on.

## What you're agreeing to

- During an API outage the run waits 1, 2, 4, 8, 16, then 30 minutes between tries, 91 minutes at most per run, then stops `api_outage`. Waiting does not count toward `--max-hours`.
- Two features in a row parking with the same call error, denial or app failure stop the run `crash_loop`.
- A timed out call that ticked boxes parks with those boxes named, and a bigger `--call-timeout` no longer clears that park by itself.
- Every call gets its session id from `wf` (`--session-id`), so `log.txt` in the run folder shows the live transcript path the moment a call starts.
- A `/sync` box runs as the feature's final `/sync` call, and ` · later boxes go on` after ` · waits on you` lets the build continue past that box.

## Requirements

**User stories**:
- As you, I want an outage or a broken install to cost one short wait or one early stop, not a night of parks.
- As you, I want to see what a run spent and what a hung call is doing, without waiting for it to end.
- As you, I want a call that was killed to never count as passed, and a fixture that proves `wf` still works after an upgrade.
- As you, I want a scope to end with a `/sync` box and to keep building past a manual step that later boxes do not need.

**Acceptance criteria**:
- **AC-1** (API outage): a failed call (spec 0008 AC-6 sense) that is not a usage limit (spec 0008 AC-8 is checked first) and whose JSON `api_error_status` is an integer of 500 or more, or whose `result`, subtype or stderr tail matches `OUTAGE`, is an outage call: recorded with `outage: true`, not counted toward `--max-calls`, and it neither sets nor clears the spec 0008 AC-6 `retried` flag. `wf` then runs the guard (spec 0008 rule 7) on a fresh reread, and waits `min(2 ** (k - 1), 30)` minutes, where `k` counts the outage calls in a row in this run (any call that is not an outage resets `k` to 0). Before a wait that would push this run's outage wait total past `OUTAGE_CAP` (120 minutes) the run stops `api_outage` (a run stop), detail the last error line. After each wait it rereads the scope, runs the guard again, then reruns the same command as a fresh call, or the same resume (`--resume`, same id and prompt). The wait is slept on the boot clock in `POLL` slices, keeps every lock and the inhibitor, ends early on Ctrl C, SIGHUP or SIGTERM (stop `interrupted`), and its time goes into `outage_waited_s`, which `--max-hours` subtracts along with `waited_s` and `limit_waited_s`. With the 120 minute cap the waits are 1, 2, 4, 8, 16, 30, 30 (91 minutes); the next 30 would pass the cap, so the run stops instead. Mechanics (cross check 2026-10-12): the rerun takes the spec 0008 AC-8 limit rerun path, so it keeps the call's kind, box, `last` values and debug snapshot, never counts as a new debug attempt, and never takes a new snapshot; the `--max-calls` count adds a call only when it is neither `limited` nor `outage`. Any spec 0009 app is stopped before the wait and started again by the rerun as a resume restarts it. The wait calls the spec 0011 AC-12 poll every 15 seconds, so phone answers still land. An outage during a resume keeps its Decision record (spec 0011 AC-13) until the rerun is classified.
- **AC-2** (crash loop): when a feature parks with reason `call_error`, `denied` or `app_failed`, and the previous entry in `run.json` `features` (by `n`, any repo) is a park of a different feature with the same reason and the same detail key, the run stops `crash_loop` (a run stop) right after the second park is handled as usual (recorded when its reason is recorded, spec 0011 AC-10), inside the same park step, before the next pick. Detail: `<reason>: <detail of the second park> (also in <first feature>)`. Detail key: the first 60 characters of `flat(detail)`, case folded. Any entry whose outcome is not one of these three reasons (`feature_done`, `decision_open`, a repo stop, another park reason) breaks the chain; a feature skipped at pick time with no entry neither breaks nor extends it; a resumed feature whose entry is reused counts with that entry's latest outcome. `call_timeout` never counts (AC-4).
- **AC-3** (tokens and cost): every call record gets `tokens`: `{input, output, cache_read, cache_write}` from the JSON `usage` fields `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens` (each an int, else null), or null when `usage` is missing or not an object. Each feature entry and the run get `cost_usd` (sum of the known call `cost_usd` values, the record field filled from the JSON `total_cost_usd`; null when none is known), `tokens` (each of the four fields summed over the calls where that field is known, a field null when no call knows it; the whole object null when every field is) and `usage_partial` (true when at least one call has a null `cost_usd`, a null `tokens`, or a null field inside it). A null never counts as 0. Right before the final `run folder:` line, on every exit path after the confirm (a raised stop and `internal_error` included), the terminal prints `spent: <cost> USD, <total> tokens`, where `<cost>` has 2 decimals and `<total>` is the plain integer sum of the known run token fields; each number gets a `+` after it when `usage_partial` is true, and shows `-` when it is null. On a subscription the dollar figure is the notional value Claude Code reports, shown as is.
- **AC-4** (a timeout is unknown): before every call of a feature, of any kind (box, debug, sync, a resume, a retry or rerun), `wf` keeps the feature's boxes as `(position, text, open)` from the last reread. When a call is classified `call_timeout`, `wf` compares them with the feature's boxes after the call, matched by position and text: every box open before and ticked after is unconfirmed, whoever ticked it (a tick you made by hand during the call counts too; `wf` cannot tell them apart). The call record gets `unconfirmed` (list of box texts, empty when none). With at least one, the park detail becomes `still running after <m>m; ticked before the timeout, recheck: <box 1>; <box 2>; then wf unpark` (each box text through `flat()`, first 80 characters) and the Park record's `cap` is null, so only a section edit (unticking the box counts) or `wf unpark` clears it, never a larger `--call-timeout`. After checking the boxes, `wf unpark` is how you accept them; unticking and ticking again restores the same section hash and the park holds. With none, the park is as today. A timeout never counts toward the crash loop (AC-2).
- **AC-5** (fixture end to end): `runner/e2e/fixture/` holds a tiny repo template: `docs/scope/scope.md` (`**Workflow:** Beta`, `**Autopilot:** allowed`, one feature `· auto` with its `(spec)` box ticked, then `/develop`, `/check verify`, `/test` and `/sync` boxes), the matching spec in `docs/specs/0001-add-function.md` (one function `add(a, b)` in `calc.py` and its unittest), and `AGENTS.md` with `## Standing answers` `run suite: yes` and `done: yes`. `runner/e2e/run.py` (Python stdlib, argument lists only) copies it into a new temp folder, runs `git init`, commits on branch `wf-e2e`, points `XDG_STATE_HOME` and `XDG_CONFIG_HOME` at temp folders, copies your `ntfy.json` there (mode 0600; the fixture never asks), runs `wf allow <temp repo>`, then `wf run <temp repo> -y --max-calls 10 --max-hours 1`, and prints `PASS` and exits 0 only when `wf` exits 0, `run.json` shows the feature `feature_done`, every box in the fixture scope is ticked, and `python3 -m unittest` passes in the temp repo. Otherwise it prints `FAIL: <which check>`, keeps the temp folders and prints their paths, and exits 1. On `PASS` it deletes them. It is never run by `install.sh` or the unittest suite: it makes real `claude` calls, so you run it yourself with `!` after a Claude Code upgrade or a runner change.
- **AC-6** (live log): every fresh call (box, debug, sync, their AC-6 retries and the AC-1 and spec 0008 AC-8 reruns) gets a new `uuid4` as `--session-id <uuid>`, placed right after `--output-format json` in the spec 0004 AC-4 argv; a resume keeps `--resume <id>` and gets no `--session-id`. The call record's `session_id` is set from that value at spawn and replaced by the JSON `session_id` when the JSON has one. Each run folder gets `log.txt` (mode 0600, appended, flushed after every line), one line per event, `<ISO time> <text>`, every text through `clean()`: `start <repo names>`; `call <seq> <repo> <feature>: <command>, transcript <config dir>/projects/*/<session id>.jsonl`; `end <seq> <subtype or error>, <cost> USD, <minutes>m`; `park <feature>: <reason>: <detail>`; `decision <id> <feature>`; `wait outage <minutes>m: <error>`; `wait limit until <reset>`; `wait answers`; `stop <reason>: <detail>`; `done`. `<config dir>` is `CLAUDE_CONFIG_DIR`, else `~/.claude` (the spec 0008 AC-5 source). The terminal prints `run folder: <path>` once right after the confirm as well as at the end, so `tail -f <path>/log.txt` works from the first call.
- **AC-7** (a `/sync` box): a box whose command's first word is `/sync` is a sync box. `box_refusal` no longer refuses it. A new `run_next(boxes)` in `run.py`, used by every `wf run` and `wf queue` place that reads a feature's next box today (`Feature.next`, the plan, the pick, classification, the entry of a picked feature), returns the first open box that is neither a sync box nor a skippable waiting box (AC-8); box refusals apply to it as today. `wf.pick_next` stays as it is for `next`, which is unchanged for sync boxes. When `run_next` finds no box: (a) if the feature still has an open skippable waiting box, the feature ends with park reason `waiting` (unrecorded, no Park record, never `feature_done`), detail that box's owed text, and the plan shows it as `skip: <feature>: waiting`, never `queued`; (b) else, if it has an open sync box, the run makes the feature's sync call with that box: kind `sync`, command the box command, `box_text` the box text (recorded on the call and on any Decision record, where a sync call with a box keeps its `box_text`), after the spec 0010 rule 14a design check, with one added prompt line `This call runs the feature's /sync box; when /sync is done, tick that box.`. That call is classified like any sync call, except that when it passes and its box is still open, the feature parks `no_progress`; (c) else, if the feature has any sync box (all ticked), it is finished: not `sync owed`, no call, not in the plan; (d) else (no sync box at all) the automatic `/sync` of spec 0004 AC-7 runs, unchanged, and still ends `feature_done` when it passes. Any sync box, ticked or open, turns off the automatic `/sync` for its feature.
- **AC-8** (skip ahead): a box carrying both ` · waits on you` and ` · later boxes go on` (in either order, as `·` segments, case insensitive) is a skippable waiting box. The tag counts only on the box's own text, never on a note box or a parent box; when the box has milestone sub boxes, they are passed over with it. `wf run` and `next` both pass over it to the next open box of the feature (AC-7; `next` through `wf.pick_next`); the feature reaches its sync call only once you tick it. A box text holding `later boxes go on` without the `·` segment shape gets a near miss warning like `waits on you` does (spec 0012). A waiting box without the tag stops the feature as today (spec 0012). `rules/scope-contract.md` gains the tag and two writer rules: `/architect` adds ` · later boxes go on` only when no later box of the feature needs that step done first; a feature's `/sync` box, when it has one, is its last box. `/scope` and `/architect` read the rule from `~/.claude/rules/`, so the live copy there is a step you do yourself.
- **AC-9** (probes): `verify.md` records P1 (`claude -p --session-id <uuid>` keeps that id in the JSON), P2 (the transcript at `~/.claude/projects/*/<uuid>.jsonl` grows while the call runs) and P3 (the JSON carries `usage` with the four token fields and `api_error_status`, null on success), all run 2026-10-12 on Claude Code 2.1.296 before accept. The outage shape is unconfirmed: `OUTAGE` is built from Claude Code's known error texts, and `verify.md` holds a one line probe for the next real outage. If that probe shows a shape both `api_error_status` and `OUTAGE` miss, AC-1 goes back to `/architect`; until then such a failure keeps today's retry once, then park.

## Decision

**Chosen option**: Fix in place, inside `runner/run.py` and `runner/wf.py`, one spec for all eight, each behind its own AC and test.

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model** (files only; `queue.json` keeps `version: 1`, no new field):

| Where | Field | Type | Notes |
|---|---|---|---|
| Call (`run.json` `calls`) | `outage` | bool | AC-1 |
| | `tokens` | object or null | `{input, output, cache_read, cache_write}`, ints or null, AC-3 |
| | `unconfirmed` | list of strings or null | timed out calls only, AC-4 |
| Feature entry | `cost_usd`, `tokens`, `usage_partial` | float or null, object or null, bool | AC-3 |
| Run | `cost_usd`, `tokens`, `usage_partial` | same | AC-3 |
| | `outage_waits` | list of `{started, minutes, error}` | AC-1 |
| | `outage_waited_s` | float | AC-1, subtracted by `--max-hours` |
| `stop_reason` enum | `api_outage`, `crash_loop` | run stops | AC-1, AC-2 |
| Park record | `cap` | null when a timeout ticked boxes | AC-4 |
| Run folder | `log.txt` | text, 0600 | AC-6 |

**Classification order** (spec 0008, one rule added): 5 usage limit (spec 0008 AC-8); **5a outage (AC-1)**; 6 retry or park `call_error`; the rest unchanged. Rules 5, 5a and 6 wait or rerun only after the rule 7 guard passes on a fresh reread. After the outcome of each feature, the AC-2 crash loop check runs before the next pick.

**Constants** (in `runner/run.py`):
- `OUTAGE` (case insensitive): `API Error: (5\d\d|Connection error)|overloaded_error|internal_server_error|ECONNRESET|ETIMEDOUT|ENOTFOUND|EAI_AGAIN|socket hang up`.
- `OUTAGE_CAP`: 120 minutes per run. Waits: 1, 2, 4, 8, 16, 30, 30, ... minutes.
- Crash loop reasons: `call_error`, `denied`, `app_failed`.
- `SKIP_AHEAD` (in `wf.py`): `·\s*later boxes go on\s*(?=·|$)`, case insensitive, matched like `OWED`.

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| outage | is outage | JSON `api_error_status` (int >= 500), else `OUTAGE` over `result`, subtype, stderr tail |
| outage | wait length, cap | `min(2 ** (k - 1), 30)` minutes, `k` outage calls in a row; `OUTAGE_CAP` |
| crash loop | previous outcome | the run's feature outcomes in order (`run.json` `features`) |
| crash loop | same failure | reason in the crash loop set, detail key (first 60 characters of `flat(detail)`, case folded) equal |
| tokens | per call | JSON `usage.input_tokens`, `.output_tokens`, `.cache_read_input_tokens`, `.cache_creation_input_tokens` (P3) |
| cost | per call | JSON `total_cost_usd` (spec 0004) |
| timeout | unconfirmed boxes | the feature's open box texts before the call vs after (`wf.pick_next` input, the feature's own boxes) |
| live log | session id | `uuid.uuid4()` per fresh call; resume keeps the record's id |
| live log | transcript path | `CLAUDE_CONFIG_DIR` else `~/.claude`, `projects/*/<id>.jsonl` (P2) |
| sync box | is sync box | first word of the box command is `/sync` |
| skip ahead | is skippable | `OWED` and `SKIP_AHEAD` both match the box text |
| fixture | ntfy config | your `ntfy.path()` file, copied to the temp config folder |
| fixture | branch, caps | `wf-e2e`, `--max-calls 10`, `--max-hours 1` (fixed in `runner/e2e/run.py`) |

**Key invariants**:
- `wf` still writes nothing in a repo; the timeout rule only names boxes, it never unticks them.
- An outage or limit wait never eats `--max-hours` or `--max-calls`; both waits are bounded per run.
- A successful call is never read as an outage, whatever its text says.
- A sync call never runs while any non sync box of the feature is open.
- No new ping: outage waits, crash loops and parks stay silent (architecture invariant 4).

**Security model**: no new input crosses a trust boundary. `log.txt` and `run.json` hold only cleaned text, in the 0700 state folder. The fixture script copies your ntfy config into a 0700 temp folder and deletes it on `PASS`; on `FAIL` it prints where the copy sits so you can delete it.

**Configuration required**: none new. `CLAUDE_CONFIG_DIR` is read as spec 0008 already does.

**Critical test scenarios** (unittest, fake `claude`):
- Outage: the fake fails with `api_error_status: 529` twice then succeeds; the calls are rerun after waits of 1 and 2 minutes (patched clock), not counted toward `--max-calls`, the `retried` flag untouched; a third kind of failure after that still gets its one retry; failures until the cap stop `api_outage` before the wait that would pass 120 minutes; `API Error: Connection error` in stderr with no status is an outage; a successful result containing `overloaded_error` is not; a usage limit text wins over an outage text; Autopilot set off during a wait stops `autopilot_off`; Ctrl C during a wait stops `interrupted`; the wait is subtracted from `--max-hours`, verifies **AC-1**
- Crash loop: features A and B both park `denied` with details whose first 60 characters match: the run stops `crash_loop` after B, B's park is recorded; A `denied`, then B `feature_done`, then C `denied` the same: no stop; two `call_timeout` parks in a row: no stop; A and B in different repos: stop, verifies **AC-2**
- Tokens: three calls, one with no `usage` and one with no `total_cost_usd`: per call `tokens`, feature and run sums, `usage_partial` true, terminal `spent: 1.23+ USD, 4567+ tokens`; a run with no usage at all prints `-` for both, verifies **AC-3**
- Timeout: the fake ticks the box, then sleeps past `--call-timeout`: park detail names the box, Park `cap` null, a rerun with a larger `--call-timeout` still skips it, unticking the box in the file makes it run again; a timeout that ticked nothing keeps today's `cap`, verifies **AC-4**
- Fixture: `runner/e2e/run.py` with a fake `wf` on PATH (exit 0 and a `feature_done` run.json, then exit 6) prints `PASS` and deletes the temp folders, then `FAIL: wf exit 6` and keeps them; the fixture scope parses with `wf queue` as one queued feature, verifies **AC-5**
- Live log: the fake records argv: a fresh call has `--session-id` right after `--output-format json` with a valid uuid4, its retry a different one, a resume none; `log.txt` holds the start, call, end, park and stop lines with the transcript path under a temp `CLAUDE_CONFIG_DIR`; mode 0600; `run folder:` printed right after the confirm, verifies **AC-6**
- Sync box: `/develop`, `/test`, `/sync` boxes: calls are develop, test, then a sync call with the box text and the prompt line; the fake ticks the sync box: `feature_done`; the fake does not tick it: park `no_progress`; a sync box placed second of four runs last; every box ticked with a ticked sync box: nothing to run for that feature; no sync box: the automatic `/sync` as today, verifies **AC-7**
- Skip ahead: a tagged waiting box between `/develop` and `/test` is passed, `/test` runs, then the feature is skipped `waiting` with the owed text and gets no sync call; after you tick it, the next run makes the sync call; an untagged waiting box still stops the feature; `next` launches the box after a tagged one and still refuses an untagged one; the near miss warning still fires for a misspelt marker, verifies **AC-7**, **AC-8**

## Build plan

Skateboard: each step leaves `wf run` usable and better than before.

1. Tokens and cost per call, feature and run, `usage_partial`, the `spent:` line, tests, satisfies **AC-3**
2. Live log: `--session-id` on fresh calls, `log.txt` events, `run folder:` after the confirm, tests, satisfies **AC-6**
3. Timeout unconfirmed boxes: open boxes before each call, `unconfirmed`, park detail, `cap` null, tests, satisfies **AC-4**
4. Outage rule 5a: detection, backoff waits, cap, guard around the wait, `outage_waits`, `outage_waited_s`, `api_outage`, tests, satisfies **AC-1**
5. Crash loop: detail key, the check after each feature outcome, `crash_loop`, tests, satisfies **AC-2**
6. Sync box and skip ahead in `wf.py` and `run.py` (pick, refusal, sync call with a box, finished feature, `next`), the repo copy of `rules/scope-contract.md`, the architecture page table, tests, satisfies **AC-7**, **AC-8**
7. Live rule file: `cp ~/claude-config/rules/scope-contract.md ~/.claude/rules/scope-contract.md` (you, since `~/.claude` is outside a call's reach), satisfies **AC-8**
8. Fixture repo and `runner/e2e/run.py` with its fake `wf` test, satisfies **AC-5**
9. Run `python3 runner/e2e/run.py` for real and record it in `verify.md` (you, with `!`), satisfies **AC-5**, **AC-9**

## Consequences

**Positive**:
- An outage costs at most 91 minutes of waiting and no parks; a broken hook or install stops after two features.
- A hung run can be read live, and every run says what it spent.
- A killed call can no longer slip a ticked verify or test box past you.
- Scopes can end with a `/sync` box, and a manual step no longer blocks the boxes that do not need it.

**Negative / tradeoffs**:
- The outage shape is a guess until a real outage; a shape it misses keeps today's behavior (retry once, then park, and the crash loop then stops the run on the second feature).
- A real outage longer than 91 minutes of waiting still ends the run; you restart it.
- The crash loop can stop a run one feature early when two features truly fail the same way.
- Comparing only the first 60 characters can make two different failures look the same when their details share a long prefix.
- The token count on a subscription is information only; the dollar figure is notional.
- The fixture run uses real subscription usage (a few minutes) and copies your ntfy config into a temp folder for its length.
- A skippable waiting box depends on `/architect` judging "nothing later needs it" correctly; a wrong tag runs a later box too early, which then fails or parks.
- Until this feature is built, a `/sync` box parks `manual_box`, so features queued with one (25, 28, 29) park at their last box in a run that starts before this code lands.

**Neutral**:
- Amends specs 0003, 0004, 0008, 0011 and 0012 as listed at the top; `/develop` notes each when it builds the step.
- Architecture page: invariant 8 gains the outage wait bound; the command table gains the `/sync` box row change.

## Follow-up

- [ ] Run the outage probe in `verify.md` at the next real API outage; if the shape differs, `/architect runner resilience` again. · waits on you
- [ ] Run folders still pile up in the state folder; prune them only if it ever matters.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
