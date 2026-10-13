# One command: wf

## Agreed so far, do not ask again
- Your rule (2026-10-13, said many times): one command, `wf`. No `wf finish`, `wf unpark`, `wf report`, `wf queue` for you to remember. Every extra command steps on your work and adds complexity. Those may stay as internals, never as steps you are told to type.
- You work non stop and the agents never stop because something else is running.
- Typing `wf` (in any folder, any time, even while other runs go on) does everything that is due, in this order, after one confirm screen listing it all (Enter, or `-y`):
  1. Shows the morning report of runs that ended since you last looked.
  2. Applies pending live setup steps (copies into `~/.claude`, `install.sh`) as one atomic swap: new files written aside, then renamed into place, so no Claude reads half old, half new files.
  3. Runs pending real claude checks (`runner/e2e/run.py`, probes) in their temp folders, records them and ticks their boxes.
  4. Takes back every feature that was set aside for something now fixed (today's `wf unpark`); one whose cause is still there stays set aside and the screen says why in one line.
  5. Starts the build of every repo with work, side by side, skipping repos a run already holds (they are not an error).
- A run already going is never stopped by `wf`: it treats a swap made by `wf` as expected and takes the new setup at its next call (each call is a fresh claude session). Any change to `~/.claude` not made by `wf` still stops it, as today.
- No lock is held longer than the step that needs it; a refusal names the real holder.
- Decided in /architect, 2026-10-13 (spec 0020): the swap is per file, renamed in a loop of a few milliseconds with `settings.json` last, so a Claude starting inside that window may see some new and some old files, every file whole (accepted over a whole set swap). A call already running sees the new settings and hooks mid call (probe P1, accepted). The real claude checks run beside the builds, not before them, so nothing waits on them. A second `wf` during a swap skips only the swap and does the rest.
- Trigger, 2026-10-13: `wf finish` held every repo lock for 30 minutes, `wf unpark` was refused, `wf finish` refused because a run was going, and a hand made wait loop was needed.

## Open for /architect
- How a run tells a swap made by `wf` from any other change, and how that stays safe against a call forging it.
- What an in flight call sees during a swap (hooks read per tool call, rules and settings at session start); needs a probe on the real claude.
- Whether `install.sh` becomes swap based, or `wf` stages its output and swaps.
- Ctrl C or a crash mid swap: how it rolls back.
- What "the cause is now fixed" means for each park reason, so step 4 never retakes a feature blindly.
