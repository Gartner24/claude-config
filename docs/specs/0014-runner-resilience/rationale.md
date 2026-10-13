# 0014 rationale

## Context

`wf run` works through a queue of features across trusted repos (spec 0011) and parks a feature when it fails (spec 0008). Six weak spots came out of comparing it with other agent runners (brief `~/projects/docs/briefs/runner-ideas-2026-10-12.md`, spec A): an API outage parks every queued feature one after another, since spec 0008 retries a failed call once and then parks; a broken hook or install fails every feature the same way and nothing ends the run early; `run.json` holds a cost per call but no totals and no tokens; a call killed at its timeout may already have ticked boxes, and after `wf unpark` (or a larger `--call-timeout`, which clears a `call_timeout` park on its own) the next run trusts them; every runner test uses a fake `claude`, and the real end to end checks were done by hand on scratch repos; a call's output lands only when it ends, so a hung call shows nothing.

Two scope problems came from feature 21 (personal scope row 24): a `/sync` box is refused `manual_box`, because `wf` runs `/sync` only as its own final call, so a scope that writes a `/sync` box parks there; and a box that waits on you stops the whole feature even when the boxes after it do not need it.

The runner is Python stdlib in `runner/run.py` and `runner/wf.py`, single user, local. Threat model unchanged (architecture invariant 1).

## Options considered

### Option 1: Fix in place, one spec (chosen)

Each change is a rule or a field in the existing loop: a classification rule, a check after each feature outcome, record fields, one argv flag, a log file, two pick rules, a fixture folder.
- Pro: each piece is small and testable alone; no new process or dependency.
- Pro: one spec keeps the amendments to 0003, 0004, 0008, 0011 and 0012 in one place.
- Con: `run.py` grows further (already about 2700 lines).

### Option 2: A supervisor around `wf run`

A wrapper that restarts `wf run` after an outage, tails its folder and counts usage.
- Pro: leaves `run.py` untouched.
- Con: the wrapper cannot tell an outage from a park without reading the same JSON, so the logic lands twice; a restart loses the in memory retry and debug counters.

### Option 3: Stream the call output

`--output-format stream-json --verbose` for the live view instead of `--session-id`.
- Pro: every message lands in the run folder.
- Con: changes the output every classification rule and probe relies on; Claude Code already writes the transcript live (P2), so `--session-id` gives the same view with one flag.

## Rationale

Option 1. The forces are the overnight goal (a night should end with useful work or an early, named stop) and the architecture rule that `wf` decides from files and the call JSON, never from the model. Every change here reads a field Claude Code already prints (`api_error_status`, `usage`, `session_id`) or a scope file, so it stays inside that rule. You picked each behavior in the interview:

- Outage: wait, then stop (not park), because an outage is run wide; parking would only move the same failure to the next feature. The cap is 91 minutes of waiting so a broken install that looks like an outage does not idle the night (runner up: 6 hours like the usage limit).
- Crash loop: two parks in a row with the same reason and detail, in different features (runner up: any two in the run, which stops too often). The reason set is the failures that come from the environment, not the work: call errors, denials, app failures. A timeout is excluded, as you chose for AC-4.
- Timeout: name the ticked boxes and keep the park until you act, instead of a rerun (runner up), because `wf` must not untick boxes (it writes nothing in a repo) and a rerun doubles the time a stuck step burns.
- Cost: `run.json` plus one `spent:` line. Absent usage prints `-` or a `+`, never a zero (`rules/lessons.md`, an absent answer rendered as a definite one).
- Fixture: a real `claude` script you run on demand (runner up: fake only, which proves nothing about the real claude).
- Live log: `--session-id` plus `log.txt`, probed before accept.
- Skip ahead: an opt in tag written by `/architect`, because only the spec author knows whether a later box needs the manual step (runner up: always skip, which runs an install dependent step too early).
- `/sync` box: `wf` runs it as the feature's final sync call (runner up: never write one, which contradicts the scope layout you asked for).

Decided here without a question (smaller calls): the crash loop reason set and its 60 character detail key (the cross check found digit and path blanking likely to be wrong both ways); `next` follows the skip ahead tag (so `next` and `wf run` agree) but treats a `/sync` box as any box (you are at the keyboard), so `wf run` gets its own `run_next`; a feature whose boxes, sync box included, are all ticked is finished rather than `sync owed`, so `/sync` never runs twice; a sync call that leaves its box open parks `no_progress` like any box; the outage cap counts per run, not per outage, so it stays bounded.
