# 0042 · Questions you can act on

**Date**: 2026-10-14
**Status**: Accepted
**Paths:** `runner/run.py`, `runner/context.py`, `runner/tests/test_explain.py`
**Amends**: [0033](../0033-context-in-messages/index.md) AC-4, AC-6 (steps only for a blocked call), [0021](../0021-never-stop/index.md) F10 (a waiting box's question)

## What you're agreeing to
- A step only you can do is asked in plain words: "Feature 16 needs one step only you can do: ...".
- The message explains it: what the step is and what it checks, why it matters, and numbered steps (where, the exact thing to type or tap, how you know it worked), written by one small sandboxed call from the plan and its spec.
- Every other question that grants nothing (a check that did not report, a fix that touched a test or plan, a step that ran out of time) also says in plain words what happened, what each answer does, and why the first is recommended. Questions that grant something (merge, post, allow writes) keep the runner's own fixed reason.
- An old question saved without context, like the two from the night of 2026-10-13, is rebuilt this way once before it is sent again.

## Acceptance criteria
Today: a waiting box asks `the next step is waiting on you in <feature>. waits on you: <box shorthand>` with no steps (`runner/run.py` `ask_case`, `plain_question`); steps exist only for a blocked call (spec 0033 AC-6); a question queued before spec 0033 is re-sent with no context (`Run.reping`). Your words 2026-10-14: "I don't understand a single question".

- **AC-1** (plain words): a `waiting` or `manual_box` question reads `<feature> needs one step only you can do: <box text without its tags>`.
- **AC-2** (explanation): before it is asked, one call of kind `explain` runs isolated as spec 0032's draft call (hooks off, no network, writes only in its own folder), with the box, the feature's plan section, the spec and its `verify.md` between `BEGIN PLAN-DATA-<n>` and `END PLAN-DATA-<n>` as data. Only its `WHAT:`, `WHY:` and `STEP:` lines are kept (at most 6 steps); every other line is dropped. A failure asks the question as before.
- **AC-3** (shown): Telegram shows `what this is: <what> Why it matters: <why>` under the from lines and the steps numbered; ntfy shows `what:` and the steps scrubbed as today (no links or paths). Every field passes `context.safe`.
- **AC-4** (old questions): a question with no context, in the repo in use, gets AC-1 to AC-3 once before it is sent again; the result is stored.
- **AC-5** (every question that grants nothing): a case question whose case is not in `context.AUTH` (and not `waiting`, `manual_box`, `live_step`) gets one isolated explain call over the question, its options, the runner's detail, what the step said it did and the last change of each file the detail names (inside the repo only); its `WHAT:` is the context's what, its `WHY:` the reason the first option is recommended. The step's own why and steps, when it gave them, win. A question in `context.AUTH` gets no such call. Asked 2026-10-14: "the format... longer better explained messages".
