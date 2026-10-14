# 0041 · Live steps during a run

**Date**: 2026-10-14
**Status**: Accepted
**Paths:** `runner/run.py`, `runner/plain.py`, `runner/context.py`, `runner/tests/test_never_stop.py`
**Amends**: [0021](../0021-never-stop/index.md) F10 (a `· live` box was left to your next `wf` with no question)

## What you're agreeing to
- When a build reaches a setup step `wf` can run (copy a file into `~/.claude`, `./install.sh`, a self-test or probe), it asks you on your phone instead of waiting silently for your next `wf`.
- The question lists every such step it would run. "run it now" (recommended) runs them right away and the build goes on; "not now" leaves them for your next `wf`.
- Only your own tap counts: a Telegram button from your chat, or an ntfy reply with one of your one time codes.

## Acceptance criteria
Today: `Run.ask_case` returns no question for a waiting box with `· live` (`runner/run.py`, "F10 leaves a `· live` box to wf"), so the feature parks silently until you run `wf` (night of 2026-10-13: feature 14 waited from 02:00).

- **AC-1** (asked): a waiting or manual park whose box is `· live` asks row F16 `live_step` when `finish.boxes` plans at least one step for the repo; the question names each planned step's command. No planned step: as before, no question.
- **AC-2** (run it now): with a strong answer (`pr.strong`), the run runs `wf finish <repo> -y` from its own runner copy, outside every call's sandbox, without `WF_RUN`, `WF_STAGE` or `CLAUDE_LIVE_DIR`, its output in `live-NNN.log` in the run folder, at most 30 minutes. The swap it makes is taken at the next call (spec 0020 AC-6); the feature goes on from its files.
- **AC-3** (weak answer or failure): a non strong "run it now" runs nothing; the next question says why, as does a failed `wf finish` (its exit and log).
- **AC-4** (not now): the feature is skipped for this run; the next `wf` screen runs its live steps as today.
- **AC-5** (authorization): `live_step` is in `context.AUTH`, so the phone shows the runner's facts and fixed reason, never a call's words as the reason.
