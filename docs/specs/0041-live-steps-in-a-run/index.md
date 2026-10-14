# 0041 · Live steps during a run

**Date**: 2026-10-14
**Status**: Accepted
**Paths:** `runner/run.py`, `runner/plain.py`, `runner/context.py`, `runner/tests/test_never_stop.py`
**Amends**: [0021](../0021-never-stop/index.md) F10 (a `· live` box was left to your next `wf` with no question)

## What you're agreeing to
- When a build reaches a step that copies a finished rule, agent, command or skill file into `~/.claude`, it asks you on your phone instead of waiting silently for your next `wf`. Hooks, scripts, settings, `./install.sh`, self-tests and probes still wait for your `wf`, since their files may come from this night's build.
- The question lists the exact steps. "run it now" (recommended) runs exactly those, and only if their files did not change since you were asked; "not now", or any other text, leaves them for your next `wf`.
- Only your own tap counts: a Telegram button from your chat, or an ntfy reply with one of your one time codes.

## Acceptance criteria
Today: `Run.ask_case` returns no question for a waiting box with `· live` (`runner/run.py`, "F10 leaves a `· live` box to wf"), so the feature parks silently until you run `wf` (night of 2026-10-13: feature 14 waited from 02:00).

- **AC-1** (asked): a waiting or manual park whose box is `· live` asks row F16 `live_step` when the feature's live boxes plan copy steps into `rules/`, `agents/`, `commands/` or `skills/` of the live dir from a non executable source (`Run.live_plan`), and the waiting box is one of them; the question names each step's command and the decision keeps `live`: each command with the sha256 of its source. Otherwise, as before, no question.
- **AC-2** (run it now): with a strong answer (`pr.strong`) the run re-plans; only when the commands and source hashes equal the decision's `live` (security review: check then act) does it stage and swap exactly those steps with `finish.Finish`, tick their boxes and commit them as `wf finish` does. The swap is taken at the next call (spec 0020 AC-6); the feature goes on from its files.
- **AC-3** (weak answer, change or failure): a non strong "run it now", a changed step or source, a held swap lock or a failed step runs nothing more; the next question says why. An answer that is no option is "not now" (security review: authorization fails closed).
- **AC-4** (not now): the feature is skipped for this run; the next `wf` screen runs its live steps as today.
- **AC-5** (authorization): `live_step` is in `context.AUTH`, so the phone shows the runner's facts and fixed reason, never a call's words as the reason.
