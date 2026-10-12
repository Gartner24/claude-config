# 0012 verify steps

_Steps derived from spec 0012 acceptance criteria. `/check verify` runs these; `/test` covers the commands._

## UI steps (manual, real claude)
- [ ] 1. Headless probe (AC-7, AC-8): in a scratch repo with a git work branch, `env -C <scratch> claude -p "/scope add a feature: pair the phone app, ending with a check on my phone that the pairing worked"`; the phone check box ends with ` · waits on you`. Then with `**Autopilot:** allowed`, the repo trusted and that box next, `wf run <scratch> -y` prints `refused: waiting: waits on you: <text>` (or `skip: <feature>: waiting` once spec 0011 is built), no run folder and no call. An unmarked box: run the probe once more; a second miss means reword the AC-7 rule line and rerun.

## Commands
- [ ] `python3 -B -m unittest discover -s runner/tests` -> all OK -> AC-1 to AC-6

## Acceptance-criteria coverage
- AC-1 to AC-6: tests named in the spec's Critical test scenarios. AC-7, AC-8: UI step 1.
