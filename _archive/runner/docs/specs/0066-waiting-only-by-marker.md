# 0066. Waiting only by the marker

**Date**: 2026-10-19
**Status**: Accepted
**Paths:** `runner/wf.py`, `runner/tests/**`
**Amends**: [0012](0012-waiting-boxes-owed-to-you/index.md) AC-2 (which boxes count as waiting) and [0002](0002-next-repo-command/index.md) AC-6.

## What you're agreeing to

- A box or milestone waits on you only when it ends with ` · waits on you`.
- The words "after" and "waits on" in a milestone no longer hold a feature back.
- A milestone that still says "waits on" without the marker gets a warning in `wf queue`, never a silent hold.
- Nothing open today changes: no current plan relies on the old words (checked 2026-10-19).

## Summary

The runner read any open milestone containing "after" or "waits on" as waiting for you (`WAITING` in `runner/wf.py`). A milestone that only mentioned "after" made `wf queue` say `skip: waiting` forever (found 2026-10-19 on a work repo feature). The explicit marker from spec 0012 already says it on purpose, so the word guess goes.

## Requirements

- **AC-1** (waiting): `NextBox.waiting` is true exactly when `NextBox.owed` is set (spec 0012 AC-2's `owed`, unchanged). The note box text is no longer matched against `\b(after|waits on)\b`; the `WAITING` pattern is removed.
- **AC-2** (near miss): when the picked box or its note box contains `waits on` (case insensitive) and is not marked, the candidate gets the existing near miss warning (spec 0012 AC-1 text), so `waits on the merge` warns instead of holding. The warning names the words it found: `"waits on" is not the marker here, end the box with " · waits on you"` (it said `"waits on you"` before). A box containing only `after` gets no warning.
- **AC-3** (display): `next` prints the note as `note: <text>` for an unmarked note box (it printed `waiting: ` before when the words matched); a marked one keeps `waits on you: <owed>`.
- **AC-4** (test): a test with a milestone `build it after the schema lands` under an open parent shows the feature not waiting (red on the old code), and one with `waits on the merge` shows not waiting plus the near miss warning.

## Decision

Only the marker counts (your pick 2026-10-19, over keeping "waits on" as a word signal). Wording never decides.

## Build plan

1. `runner/wf.py`: drop `WAITING`, set `waiting = self.owed is not None`, widen `NEAR_OWED` to `waits on` (AC-1, AC-2, AC-3).
2. Tests in `runner/tests/` for AC-4; mutation check each. Update the existing tests that assert the old word behavior: `test_wf.py` (`test_open_parent_takes_first_open_milestone_as_waiting_note`, `test_tab_indented_milestone`, the `next` output line `waiting: claude-config as a submodule`), `test_run.py` (the `waits on the merge` skip case and the rule 11 case), `test_queue.py` (the `skip: 10. Later: waiting` cases); check `test_resilience.py` and `test_review_fixes.py` waiting fixtures. A test that needs a waiting milestone gets the marker in its fixture.
3. Spec 0012: add an `**Amended by**` line naming this spec.

## Consequences

A milestone that truly must wait has to carry the marker. Skills already write it (rule file `scope-contract.md`).
