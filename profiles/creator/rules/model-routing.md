# Model routing (profile creator only; spec 0081 AC-20)

The main session stays on Opus. Pick the helper by task; never ask the person to switch models.

- Creative and taste work: the main session, on Opus.
- Routine code, tests and docs: `careful-worker` (Sonnet).
- Batch checks, counting and file moves: `mechanical-worker` (Haiku).
- Web research legs: `researcher`.
- A helper's result is not done until the main session rechecks it against the gates (tests, checks, edge cases).
- When a cheaper helper's result fails, redo that task on Opus and note it, so the routing can be corrected.
