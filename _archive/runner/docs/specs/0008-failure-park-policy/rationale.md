# 0008. Failure and park policy: decision record

## Context

`wf run` (spec 0004) builds one feature with nobody at the keyboard. It stops safely on anything it does not understand, but the stop reasons say little: a `/check verify` that failed, a step that needed `sudo`, and a hook that denied a chained command all end as `no_progress`, and a transient API error ends the night as `call_error`. Spec 0004 left these for this feature on purpose.

Your rules for this are settled (research notes section 0, 2026-10-11): a `/check` FAIL gets 2 `/debug` attempts and then parks; BLOCKED, sudo and logins park; hook denials are logged with the reason and park the step; paid steps never run unattended. On 2026-10-12 the usage limit pause moved here from feature 12: a run that hits the limit waits for the reset instead of ending. Spec 0003 and 0006 also left one guard here: a cloned third party scope can write `**Autopilot:** allowed` (and standing answers) itself.

Forces: the run has no human to ask, so every rule must be decidable by `wf` from files and the call JSON; the model's text is not trusted to report its own success (architecture invariant 7). Feature 10 will move on after a park, so the line between "this feature is stuck" and "this run must end" has to be drawn now. Your weekly usage also covers your daytime work, so an overnight run must not drain it. The facts available: `/check verify` prints a verdict header but writes nothing to the scope on FAIL; `permission_denials` in the call JSON lists denied tool calls without a reason, while the session transcript holds the hook's message; the usage limit message is known only from interactive sessions.

## Options considered

### Option 1: `wf` owns the policy

`wf` reads a few prompt agreed marker lines (`BLOCKED:`, `VERIFY FAIL:`) and the call JSON, drives the retries itself as separate calls (`/debug` with no box, a call error rerun, a limit wait), checks a debug call's diff, and parks or stops with a named reason.

**Pros**:
- Every retry is a separate, capped call visible in `run.json`.
- The rules that matter (debug guard, limit only on failed calls, trust list) are computed by `wf`, not promised by the model.

**Cons**:
- Markers still depend on the model following the prompt; a missed marker degrades to a less specific park.
- More classification code in `run.py`.

### Option 2: the policy lives in the prompt

The unattended prompt tells each call to debug its own failures up to twice, to stop on sudo or logins, and to say why it stopped. `wf` keeps today's generic stops.

**Pros**:
- Almost no code.

**Cons**:
- One long session per verify plus debug, and nothing `wf` can count or bound.
- The model reports its own success, which is what invariant 7 rules out.

### Option 3: generic retry with caps

Any failed or stalled call is rerun up to N times, then the run stops.

**Pros**:
- Simple, uniform.

**Cons**:
- Reruns `sudo` and hook denials that cannot succeed, at full cost.
- No reason you can act on, and no debug step between verify attempts.

## Rationale

Option 1 is the only one that keeps the files and the call JSON as the truth while still giving each case its own handling. The debug loop needs a count and a diff check that only `wf` can make reliably; you added the debug guard (no spec, `verify.md` or test edits) precisely because a model under pressure to pass will weaken the check instead of fixing the code. The usage limit rule had to read only failed calls, since a feature that builds a rate limiter would otherwise look like a limit.

Small calls made at write time, each with its runner up:
- The verify FAIL kind comes from a `VERIFY FAIL: debug|develop` marker line, not from parsing the report body. Runner up: parse `/check verify`'s `Failing / owed` bullets, rejected because their wording is free model text and its `Next:` template line lists every branch at once.
- `call_timeout` parks and is not retried (a 60 minute call rerun doubles the cost for the same result). Runner up: treat it as a call error with one retry.
- A failure to start `claude` stops the run as `spawn_failed`, since no other feature could start either. Runner up: keep it under `call_error`, which is now a park.
- The denial reason is looked up by globbing `projects/*/<session_id>.jsonl` rather than computing the project folder name from the path. Runner up: compute the folder name, rejected because the slug rule is undocumented.
- The trust list holds real paths only (your pick); a remote pin was rejected because a renamed remote would need `wf allow` again.

## Evidence

- Denial shape, from past run records under `~/.local/state/wf/runs` (2026-10-11 and 12): `"permission_denials":[{"tool_name":"Bash","tool_use_id":"toolu_...","tool_input":{"command":"...","description":"..."}}]`, no reason field. These were your Bash shape hook, and those calls still completed.
- Reason source: the same `tool_use_id` in the session transcript carries `"toolUseResult":"Error: PreToolUse:Bash hook error: SHAPE: one command per Bash call. ..."`.
- Limit text, from interactive transcripts: `You've hit your session limit` (middle dot) `resets 6:20am (America/Bogota)` and the same with `weekly limit` and `resets 5pm`, error type `rate_limit`, HTTP 429. No `claude -p` sample exists yet.
- `/check verify` output: header `## /check verify <feature>` with `PASS`, `FAIL` or `BLOCKED`; on FAIL it ticks nothing and points to `/debug` or `/develop` (`~/.claude/skills/check/modes/verify.md`).
