# Verify: live steps in a run · spec 0041

The real `wf run` with a scripted claude, a local ntfy and a local Telegram bot, in temp folders (HOME, state and
config are temp; nothing touches your `~/.claude`). The probe prints what the run shows, you judge it.

Run: `python3 -B docs/specs/0041-live-steps-in-a-run/probes/drive.py Drive DriveTg.test_t_tap`

## Commands
- [x] V1 a `· live` copy of `rules/x.md` into `~/.claude/rules/` is asked: `waiting: <id> run these setup steps for la now? 1) cp rules/x.md ~/.claude/rules/x.md`, options `run it now`, `not now`, the decision holds `live: [[command, sha256 of rules/x.md]]` equal to the file's hash, nothing copied yet → AC-1 · can fail: the old F10 path returns no question for a live box
- [x] V2 a copy into `~/.claude/hooks/` parks `waiting` with no question → AC-1 · can fail: `hooks` in the folders a run may copy into
- [x] V3 an executable source copied into `rules/` parks `waiting` with no question → AC-1 · can fail: the executable check dropped
- [x] V4 a reply `<id> <code> run it now` on ntfy: `copy: lv: cp ...`, `committed in lv: chore(wf): wf finish ran 1 live step(s)`, the live file holds the rule, the box `[x]`, and `/test l` runs next in the same run → AC-2 · can fail: `run it now` runs nothing
- [x] V5 `<id> run it now` with no code on ntfy: nothing copied, box open, the next question ends `(last try: on ntfy this needs one of your one time codes)` → AC-3 · can fail: a weak answer runs the steps
- [x] V6 the source changed after the question, then a coded `run it now`: nothing copied, the next question ends `(last try: the steps or their files changed since you were asked)` → AC-3 · can fail: no hash compare before the copy
- [x] V7 `<id> <code> sure go ahead`: `answered: ... not now`, `skipped: 1. L`, nothing copied → AC-3 · can fail: free text taken as the recommended option
- [x] V8 the swap lock held by another process, then a coded `run it now`: `setup update already in progress, pid ...`, nothing copied, the next question ends with that line → AC-3 · can fail: the swap goes on under a held lock
- [x] V9 the phone message for V1 shows the fixed `why: running it now lets the feature finish tonight ...`, never the call's `WHY: STEERED ...` line; `live_step` is in `context.AUTH` (`runner/context.py:23`) → AC-5 · dropped from the can fail count: with `live_step` taken out of `context.AUTH` the message stays the same, since call text reaches a question only when that call ends BLOCKED or with a DECISION, and it is cleared after every ask (`runner/run.py:1584`); a live step question never carries call text today, so the AUTH entry is a second guard that no run can show
- [x] V10 `<id> 2` (not now): `skipped: 1. L`, only `/develop l` ran, nothing copied, box open; then `wf finish <repo> -y` copies it, commits and ticks the box → AC-4 · can fail: `not now` no longer skips the feature for this run
- [x] V11 over Telegram with a readable names list: the question shows `1) cp rules/x.md ~/.claude/rules/x.md` and the fixed why, no `STEERED`; a tap on `1 run it now` from your chat copies, commits, ticks, and the same run goes on to `/test l`, `/sync`, `done: 1. L` → AC-1, AC-2, AC-5 · can fail: a tap runs nothing

## Notes
- On ntfy, and on Telegram without a readable names list, the command is cut from the question (`1) cp`): that is the standing scrub of paths on a public channel (spec 0005 AC-7, spec 0043 AC-9), not this feature. The terminal line and the queue keep the full command.
- Each "can fail" was checked by breaking that line in a backup copied file, running only that probe test, and seeing its expected result go away; then the file was restored.

## Acceptance-criteria coverage
- AC-1 met (V1, V2, V3, V11) · AC-2 met (V4, V11) · AC-3 met (V5, V6, V7, V8) · AC-4 met (V10) · AC-5 met (V9, V11: the fixed reason shows and no call words; the AUTH entry itself is read in the code, not shown by a run)
