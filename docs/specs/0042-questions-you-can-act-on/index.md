# 0042 · Questions you can act on

**Date**: 2026-10-14
**Status**: Accepted
**Paths:** `runner/run.py`, `runner/context.py`, `runner/tests/test_explain.py`
**Amends**: [0033](../0033-context-in-messages/index.md) AC-4, AC-6 (steps only for a blocked call), [0021](../0021-never-stop/index.md) F10 (a waiting box's question)

## What you're agreeing to
- A step only you can do is asked in plain words: "Feature 16 needs one step only you can do: ...".
- The message explains it: what the step is and what it checks, why it matters, and numbered steps (where, the exact thing to type or tap, how you know it worked), written by one small sandboxed call from the plan and its spec.
- An old question saved without context, like the two from the night of 2026-10-13, is rebuilt this way once before it is sent again.

## Acceptance criteria
Today: a waiting box asks `the next step is waiting on you in <feature>. waits on you: <box shorthand>` with no steps (`runner/run.py` `ask_case`, `plain_question`); steps exist only for a blocked call (spec 0033 AC-6); a question queued before spec 0033 is re-sent with no context (`Run.reping`). Your words 2026-10-14: "I don't understand a single question".

- **AC-1** (plain words): a `waiting` or `manual_box` question reads `<feature> needs one step only you can do: <box text without its tags>`.
- **AC-2** (explanation): before it is asked, one call of kind `explain` runs isolated as spec 0032's draft call (hooks off, no network, writes only in its own folder), with the box, the feature's plan section, the spec and its `verify.md` between `BEGIN PLAN-DATA-<n>` and `END PLAN-DATA-<n>` as data. Only its `WHAT:`, `WHY:` and `STEP:` lines are kept (at most 6 steps); every other line is dropped. A failure asks the question as before.
- **AC-3** (shown): Telegram shows `what this is: <what> Why it matters: <why>` under the from lines and the steps numbered; ntfy shows `what:` and the steps scrubbed as today (no links or paths). Every field passes `context.safe`.
- **AC-4** (old questions): a question with no context, in the repo in use, gets AC-1 to AC-3 once before it is sent again; the result is stored.
