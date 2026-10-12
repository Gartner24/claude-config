# 0012 verify steps

_Steps derived from spec 0012 acceptance criteria. `/check verify` runs these; `/test` covers the commands._

## UI steps (manual, real claude)
- [x] 1. Headless probe (AC-7, AC-8): in a scratch repo with a git work branch, `env -C <scratch> claude -p "/scope add a feature: pair the phone app, ending with a check on my phone that the pairing worked"`; the phone check box ends with ` · waits on you`. Then with `**Autopilot:** allowed`, the repo trusted and that box next, `wf run <scratch> -y` prints `refused: waiting: waits on you: <text>` (or `skip: <feature>: waiting` once spec 0011 is built), no run folder and no call. An unmarked box: run the probe once more; a second miss means reword the AC-7 rule line and rerun.

### Step 1 runs
- 2026-10-12, `wf run` half: scratch repo on branch `work`, `**Autopilot:** allowed`, next box `- [ ] Check on your phone that the pairing worked · waits on you` (written by hand). `python3 -B runner/wf.py run <scratch> -y` -> `refused: waiting: waits on you: Check on your phone that the pairing worked`, exit 5, no call (refused before the lock, so no run folder). PASS.
- 2026-10-12, `/scope` half: `claude -p` inside a `/develop` session's sandbox prints `Not logged in` (the sandbox hides `~/.claude/.credentials.json`), so you ran it with `!`. Result: `/scope` merged the pairing request into the hand written feature 2 (added its description and Done when, kept the hand box), and wrote a new feature 3 whose manual box reads `- [ ] Log in to the mail provider dashboard and confirm a test receipt arrived · waits on you`. A skill written box only you can close carries the marker, first try. PASS.

### /check verify 2026-10-12: PASS
Scratch repos on branch `work`, real `runner/wf.py`:
- AC-1: near miss `/develop a` · waits on you.` -> `next` (no tty) prints the confirm line with `warning: "waits on you" is not the marker here, ...`, exit 130, not marked.
- AC-2, AC-3: `next -y` on a marked `/develop` box -> `waits on you: Build it: \`/develop a\``, exit 3; marked milestone under an unmarked parent -> `waits on you: Pair the phone`, exit 3; marked box with no command -> `waits on you: Check on your phone that the pairing worked`, exit 3. Nothing launched.
- AC-5: `wf run -y` on a marked `/architect` box -> `refused: waiting: waits on you: Design it: \`/architect a\``, exit 5 (marker beats `manual_box`); marked `/develop` box and marked milestone -> `refused: waiting: ...`, exit 5. Mid feature park: `test_next_box_inside_feature` (real `wf run`, fake claude) ok, detail `waits on you: \`/test b\``.
- AC-6: `next --list` shows marked boxes like any other (`vcmd  1. A  /develop a  work  -`).
- AC-7: live `~/.claude/rules/scope-contract.md` equals the repo copy (`diff` empty), 19 lines, under the 25 line cap.
- AC-8: step 1 above.

## Commands
- [x] `python3 -B -m unittest discover -s runner/tests` -> all OK -> AC-1 to AC-6

## Acceptance-criteria coverage
- AC-1 to AC-6: tests named in the spec's Critical test scenarios. AC-7, AC-8: UI step 1.
