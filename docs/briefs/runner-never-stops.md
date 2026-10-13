# The runner never stops on a known block

## Agreed so far, do not ask again
- Your rule (2026-10-13): the runner does not stop. A block that could have been seen before the run is a runner bug, not your job to find in the morning, and it must not depend on any chat session remembering to check.
- Trigger, 2026-10-13: feature 32 parked `blocked` 7 minutes into its build because `wf run` calls may not write `runner/` (the `~/.local/bin` deny follows the `wf` link into it). Earlier the same day the codebase carousel parked on a missing locked design. Both were knowable before the run started.
- Two layers:
  1. Preflight in `wf` itself: before the confirm screen, for every queued feature, check its spec's `**Paths:**` against the guard's deny list (resolved through links) and, for a UI feature, that a locked design exists. A feature that would block is shown on the confirm screen with the reason and the fix, and is not started; every other feature runs.
  2. Planning: `rules/runner-handoff.md` step 2 now has the same check, so `/architect` fixes the gap (a box split, a design route) before the handoff instead of listing it.
- When a call still hits a block nobody could predict, the runner sets aside only that feature and goes on with every other one (as today), and the morning report names the fix.

## Open for /architect
- Which other block reasons can be predicted from the spec and the repo (app start line, trust, branch, missing tools).
- Whether a predicted block becomes a waits-on-you box automatically or only shows on the screen.
