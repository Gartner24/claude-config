# Verify: autonomous mode · spec 0030

Run 2026-10-14 by `/check verify autonomous mode` (headless, under `wf run`). Each step drives the real `wf auto`
CLI as a separate process in a temp state folder, with a fake `systemctl` and `systemd-run` first on PATH:
`python3 -B docs/specs/0030-autonomous-mode/probes/verify-cli.py` (prints PASS or FAIL per step, exits 1 on any FAIL).
Each step was also run against a deliberate break in `runner/auto.py` or `runner/run.py` and turned red (the
`can fail:` note). Result: 25 of 25 CLI steps passed, 18 of 18 breaks red; the runner stop path and plan fingerprint
steps passed and 4 of 4 breaks red; the whole runner suite passed.

## Commands
- [x] `wf auto on` in folder `work` -> prints `autonomous: on in work`; `auto.json` mode 0600 with `on` true, the real folder path, `since`, `relayed` [] -> AC-1, AC-2. can fail: `on` kept the folder of an earlier `on`
- [x] `wf auto on` in a second folder -> `folder` is replaced -> AC-1. can fail: same break as above
- [x] `wf auto status` in the folder with one open and one answered question -> `autonomous: on, wf idle, 1 questions open`; from another folder `autonomous: on in work` -> AC-6. can fail: answered questions counted as open
- [x] `wf auto hook` with SessionStart in the folder -> the driving instructions, the status line, then the open question quoted -> AC-4. can fail: same count break
- [x] `wf auto hook` with SessionStart from another folder, and with input that is not JSON -> no output, exit 0 -> AC-4. can fail: hook prints in every folder while on
- [x] `wf auto hook` with UserPromptSubmit -> the status line only -> AC-7. can fail: UserPromptSubmit also printed the driving instructions
- [x] `wf auto hook` with UserPromptSubmit prompt `/auto off` from this headless Claude -> state stays on (security review 2026-10-14). can fail: the hook switched for any caller
- [x] `WF_RUN=1 wf auto on` -> `refused: user_only`, exit 5, `auto.json` unchanged; `WF_RUN=1 wf auto start` the same -> AC-3. can fail: `on` ignored WF_RUN
- [x] after `wf auto off`: `wf auto status` -> `autonomous: off`, SessionStart hook prints nothing -> AC-6, AC-4. can fail: `off` did not set `on` false
- [x] `wf auto start` while off -> `refused: off`, exit 5, no systemd-run -> AC-5. can fail: same break
- [x] `wf auto start` with the unit active -> `wf already running`, exit 0, no systemd-run -> AC-5. can fail: `start` ignored an active unit
- [x] `wf auto start` with the unit idle -> `wf started`; systemd-run argv is exactly `--user --unit wf-auto --collect --working-directory <folder> --setenv PATH=... --setenv WF_AUTO=1 --setenv XDG_STATE_HOME=... --setenv XDG_CONFIG_HOME=... -- <runner/wf.py> -y`; `started` recorded -> AC-5. can fail: WF_AUTO dropped from the unit
- [x] `wf auto start` when systemd-run fails -> `failed: Failed to start transient service unit: ...`, exit 1 -> AC-5. can fail: the failure was hidden
- [x] `wf auto off` -> `autonomous: off, a running build finishes its current features`, no `systemctl stop` -> AC-2. can fail: `off` did not set `on` false
- [x] `wf auto off now` -> `autonomous: off, build stopped`, `systemctl --user stop wf-auto` called -> AC-2. can fail: the unit was never stopped
- [x] `wf auto bogus` -> usage on stderr, exit 2 -> AC-2. can fail: an unknown word exited 0 with no usage
- [x] `wf auto wait` while off -> `off` -> AC-8. can fail: `off` did not set `on` false
- [x] `wf auto wait` twice with two new questions -> `question ab12`, then `question cd34`; both in `relayed` -> AC-8. can fail: a relayed question was never recorded
- [x] `wf auto wait` with the unit active, then inactive -> `run ended` -> AC-8. can fail: a run that ended was ignored (wait hung)
- [x] `wf auto wait` idle, empty plan, `started` null -> still waiting after 5 s -> AC-8. can fail: wait exited with an empty plan
- [x] `wf auto bar` in the folder with a fake jjstack script -> its two lines unchanged, ` \e[32mAUTO idle\e[0m` on the last -> AC-10. can fail: the green dropped; jjstack output replaced
- [x] `wf auto bar` from another folder -> ` auto: work`, no color -> AC-10. can fail: jjstack output replaced
- [x] `wf auto bar` with no jjstack script -> only the segment, exit 0 -> AC-10. can fail: the green dropped
- [x] `wf auto bar` while off -> nothing -> AC-10. can fail: the bar showed a segment while off
- [x] `python3 -B -m unittest test_auto.TestAutoOff` (a real `wf demo -y` with WF_AUTO=1 and `auto.json` off ends `stopped: auto_off`, exit 6, no call; `end_wait` stops `auto_off`; a broken file counts as on) -> AC-9. can fail: pick or end_wait ignored auto off; a broken file counted as off
- [x] `python3 -B -m unittest test_auto.TestFingerprint test_auto.TestWait.test_work` (the plan bare `wf` would build gives a fingerprint; `wait` prints `work` only for a new plan) -> AC-5, AC-8. can fail: the fingerprint was always empty
- [x] `python3 -B -m unittest discover -s runner/tests` -> Ran 718 tests, OK (includes spec 0021 AC-1 with row U11 `auto_off`) -> AC-9

## Wiring (read, not counted as runtime proof)
- [x] repo `settings.json`: deny `Bash(*wf auto on*)`, `Bash(wf auto on:*)`; SessionStart and UserPromptSubmit run `/home/santiago/.local/bin/wf auto hook`; statusLine `wf auto bar`, refreshInterval 5 -> AC-3, AC-10, AC-11
- [x] `~/.claude/skills/auto` links to the repo skill; `~/.local/bin/wf` runner copy has the same `auto.py` as the repo; the installed `wf auto status` runs -> AC-11
- [ ] the live `~/.claude/settings.json` was not readable from the verify call (read denied); the install box covers it

## Not met as written
- AC-2 says the skill body runs `` !`wf auto $ARGUMENTS` ``. Probe P4 (2026-10-14) found the deny rule blocks that
  command inside the skill too, so commit 150690f moved the switch into the UserPromptSubmit hook and the skill only
  reports its line. The outputs AC-2 names are all met (steps above); the spec text and P4 still describe the old
  skill line and owe an `/architect` amendment.

## Waits on you (probes P1 to P4, real interactive session)
- [ ] P1 SessionStart notes reach the model after `/clear` and after reopening the window
- [ ] P2 the `wf-auto` unit outlives the session, and the real `wf -y` finds claude, bwrap and socat in it
- [ ] P3 the bar updates within 10 s while idle
- [ ] P4 `/auto on` typed by you writes `auto.json`; asking Claude to turn it on ends in a deny

## Acceptance criteria coverage
- AC-1 met · AC-2 met in behavior, spec text stale · AC-3 met · AC-4 met · AC-5 met · AC-6 met · AC-7 met · AC-8 met · AC-9 met · AC-10 met · AC-11 met in the repo, live file by the install box
