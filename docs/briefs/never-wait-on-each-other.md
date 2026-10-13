# Never wait on each other

## Agreed so far, do not ask again
- Goal (your message 2026-10-13): you work non stop and the agents never stop because something else is running. A run, `wf finish`, `wf unpark` and your own sessions all go on at the same time.
- Trigger, all on 2026-10-13:
  - `wf finish` held every repo's lock for 30 minutes (its install self checks hung), so `wf unpark` in another repo was refused.
  - `wf finish` refused because a run in another repo was going; you had to start a wait loop by hand.
  - The refusal named an old run's pid instead of the real holder (the lock file keeps the previous holder line).
- The real conflict is only the shared live setup in `~/.claude` (rules, hooks, settings, agents): every Claude on the machine reads it, and a run's guard stops when it changes. Nothing else `wf finish` does conflicts with a run.
- Direction agreed in chat:
  1. `wf finish` never refuses because of a run, and never holds repo locks while it works.
  2. The real claude checks (`runner/e2e/run.py`, probes) run in their own temp folders and start at once, side by side with any run.
  3. The live setup change is applied as one atomic swap (new files written aside, then renamed into place), so no Claude ever reads half old, half new files.
  4. A run treats a swap made by `wf finish` as expected, not as tampering: it takes the new baseline at its next call boundary instead of stopping `guard_changed`. Each call is a fresh claude session, so every call runs wholly under one setup. Any change not made by `wf finish` still stops the run as today.
  5. The lock refusal names the process that really holds the lock.

## Open for /architect
- How a run tells a `wf finish` swap from any other change (a ledger entry with the new file hashes written by `wf finish`, checked by the guard) and how that stays safe against a call forging it.
- What an in flight call sees during a swap (hooks run per tool call and read the new file after the rename; rules and settings are read at session start) - needs a probe on the real claude.
- Whether `install.sh` itself must become swap based, or `wf finish` stages its output and swaps.
- Ctrl C or a crash in the middle of a swap: how it rolls back.
