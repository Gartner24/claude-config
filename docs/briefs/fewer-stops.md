# Fewer avoidable stops

Source: your message of 2026-10-14 ("are we already fixing it? or we should add something to fix those bottlenecks?"), after the parallel run of features 39 to 48.

## Agreed so far, do not ask again

- Add one plan item for the stops the runner made tonight that cost waiting time but needed nothing from you. Design goes through `/architect` first, then the runner builds it.
- Already fixed elsewhere, not part of this item: a feature's child waiting on another feature's question, and your answers dropped as stale in a parallel run (both on `fix/questions-explained`).
- In scope, three stops seen tonight:
  1. A check step that cannot pass inside the build's sandbox: a probe needing a real `claude -p` session (feature 47, P1 and P2) or criteria needing days of real use (feature 46, AC-6 live, AC-7, AC-9) park the feature as `verify_failed`, though the plan already has a later `waits on you` box for exactly that. The check should leave those parts to that box instead of failing.
  2. "try again" recommended when a retry cannot help: when the check says it could not reach something, the recommended answer should be skip (a retry cost a few dollars for the same result).
  3. The attribution scan stopping on a test value that quotes the banned phrase on purpose (feature 39, question ppfb). The scan is a safety gate, so how quoted test values are treated is your decision in `/architect`.
- Partly covered already: each step starting cold and rereading everything (feature 45, each step gets the feature's brief).
