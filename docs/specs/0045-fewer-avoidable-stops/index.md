# 0045 · Fewer avoidable stops

**Date**: 2026-10-15
**Status**: Proposed
**Paths:** `_archive/runner/run.py`, `_archive/runner/plain.py`, `AGENTS.md`, `_archive/runner/tests/test_fewer_stops.py`

## What you're agreeing to
- A check step that needs something its locked room cannot give (a real Claude session, a real `claude -p` call, your phone, days of real use) leaves that part to the feature's later "waits on you" box instead of failing the whole check.
- When a step says it could not reach something, the runner recommends skip, not try again, because a retry runs in the same locked room.
- Tests that need the banned Claude credit phrases build them from two joined halves; the push scan stays exactly as strict.

## Summary

Tonight's run stopped on features 46 and 47 because their checks needed days of use or a real Claude session, though their plans already had a later box for exactly that; the runner then recommended a paid retry that could not help. The attribution scan also stopped feature 39 on a test that quotes the banned phrase on purpose. Source: [brief](../../briefs/fewer-stops.md).

## Requirements

**Acceptance criteria**:
- **AC-1** (left to the box): when the feature has later unticked boxes whose text ends with `· waits on you` (wf's `OWED` tag, after the current box in the feature's section), the prompt of a `/check verify` call adds, after the unattended prompt: `Some checks may need what this sandbox cannot give: a real interactive Claude session, a real claude -p call, the user's phone, or days of real use. A check like that which belongs to one of this feature's later boxes listed below is not a failure: record it in verify.md as "left to the box: <box text>", end your final message with one line LEFT TO BOX: <the exact box text from the list> for each, and tick the Verify box when every other check passed. Later boxes that wait on the user:` followed by each such box's text, plan tags removed (`context.untagged`), control characters out (`norm`), cut to 200 characters, one per line, at most 5, between `BEGIN BOXES-DATA-n` and `END BOXES-DATA-n` lines whose `n` is the lowest the text does not contain. No such box: no sentence. The runner reads `LEFT TO BOX:` lines from the call's result and ignores any whose text is not one of the listed boxes (after `norm` and the 200 character cut). The CAN FAIL gate (spec 0015) still parks a verify that says `CAN FAIL CHECKED: 0`, except when the call ticked the Verify box and gave at least one valid `LEFT TO BOX:` line: then every check was left to a box and the call passes.
- **AC-2** (unreachable): the prompt of every `/check verify` and `/test` call adds: `When a check cannot run because it needs something this sandbox cannot reach, end your final message with one line per such check that starts with UNREACHABLE: and names it.` The runner keeps `self.unreachable`, a list reset at the start of every call and set from the result of every `/check verify` and `/test` call (each `UNREACHABLE:` line `norm`, cut to 120 characters, at most 3); a `/debug` call in between does not reset it. When the feature then parks as `verify_failed` or `no_progress` and the list is not empty, `ask_case` offers `skip` first, then `try again`; its detail is `could not reach: <the lines joined by "; ">; ` followed by the detail it had before (the failure text is kept); and it sets the why line to `a retry runs in the same sandbox, so it cannot reach this either` in place of `plain.WHY[reason]`. Without UNREACHABLE lines the question is unchanged.
- **AC-3** (test values): `AGENTS.md` (conventions) gains one line: a test or probe that needs a banned attribution phrase as input builds it from two joined string halves, so no file holds the whole phrase; the push scan (`pr.attribution_hits`) is never relaxed for tests. Tests prove the scan still flags the whole phrase, at the start of a line, in both forms it reads: commit and PR text, and an added line of a test file in the diff.
- **AC-4** (tests): AC-1 with and without later waiting boxes, the data markers and the 5 box cap; AC-2 parsing, the option order with and without UNREACHABLE lines, the cut and the 3 line cap; AC-3's scan test. Each mutation checked.

## Cross check

Another model read this spec on 2026-10-15. Each gap took its recommended fix (your standing answer for tonight):
- A step could call any check "left to the box": it must now name the exact box in a `LEFT TO BOX:` line, and the runner ignores names not in the list (AC-1).
- A verify with every check left to a box would hit the CAN FAIL gate: it passes only with a valid `LEFT TO BOX:` line (AC-1).
- How the runner keeps the unreachable lines, which call they come from, and that the failure text is kept were unstated (AC-2).
- The scan test now covers both scan forms (AC-3).

## Decision

Two prompt sentences and one result marker, the same pattern as `BLOCKED:` and `DECISION NEEDED:`, so the runner learns from the step itself what it could not reach; no new state.

## Feature design

**Value sourcing**:
| Value | Source |
|---|---|
| later waiting boxes | the feature's boxes after the current one, `wf.OWED` on the box text |
| box text shown | `context.untagged`, `norm`, 200 characters |
| unreachable items | `UNREACHABLE:` lines in the call's result text |
| recommended option | `skip` when an UNREACHABLE line exists, else the case table |

**Security model**: box texts come from the plan, which calls can edit, so they go between data markers like issue and brief text. UNREACHABLE lines are model output shown only as the question's detail, cleaned and cut; they can only reorder the two existing options, never add one.

## Build plan

1. AC-1 and AC-2 prompt sentences in `unattended_prompt` callers, AC-2 parsing next to the `BLOCKED:` reader, the option order in `ask_case`. AC-1, AC-2.
2. AGENTS.md line and the scan test. AC-3.
3. Tests and mutation checks. AC-4.

## Consequences

**Positive**: features like 46 and 47 reach their waiting box without a question; no paid retries that cannot help.
**Negative**: a step could mark a check as "left to the box" when it could in fact run; the later box still makes you look at it.

## Rationale

The options (skip such checks in the runner, a per feature flag, or the step telling the runner) were weighed in chat on 2026-10-15; you answered the one real choice, the scan rule, and took the recommended defaults for the rest (brief).
