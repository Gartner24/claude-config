# 0012 verify steps

_Steps derived from spec 0012 acceptance criteria. `/check verify` runs these; `/test` covers the commands._

## UI steps (manual, real claude)
- [x] 1. Headless probe (AC-7, AC-8): in a scratch repo with a git work branch, `env -C <scratch> claude -p "/scope add a feature: pair the phone app, ending with a check on my phone that the pairing worked"`; the phone check box ends with ` · waits on you`. Then with `**Autopilot:** allowed`, the repo trusted and that box next, `wf run <scratch> -y` prints `refused: waiting: waits on you: <text>` (or `skip: <feature>: waiting` once spec 0011 is built), no run folder and no call. An unmarked box: run the probe once more; a second miss means reword the AC-7 rule line and rerun.

### Step 1 runs
- 2026-10-12, `wf run` half: scratch repo on branch `work`, `**Autopilot:** allowed`, next box `- [ ] Check on your phone that the pairing worked · waits on you` (written by hand). `python3 -B runner/wf.py run <scratch> -y` -> `refused: waiting: waits on you: Check on your phone that the pairing worked`, exit 5, no call (refused before the lock, so no run folder). PASS.
- 2026-10-12, `/scope` half: `claude -p` inside a `/develop` session's sandbox prints `Not logged in` (the sandbox hides `~/.claude/.credentials.json`), so you ran it with `!`. Result: `/scope` merged the pairing request into the hand written feature 2 (added its description and Done when, kept the hand box), and wrote a new feature 3 whose manual box reads `- [ ] Log in to the mail provider dashboard and confirm a test receipt arrived · waits on you`. A skill written box only you can close carries the marker, first try. PASS.

## Commands
- [ ] `python3 -B -m unittest discover -s runner/tests` -> all OK -> AC-1 to AC-6

## Acceptance-criteria coverage
- AC-1 to AC-6: tests named in the spec's Critical test scenarios. AC-7, AC-8: UI step 1.
