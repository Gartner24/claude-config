# 0030 rationale

Source: docs/briefs/autonomous-mode.md (research done, plan agreed 2026-10-13) and docs/briefs/finish-runner-today.md item 19. This spec builds that plan: state file, `/auto on|off` user only skill, SessionStart and UserPromptSubmit hooks, `systemd-run --user` for `wf`, a status bar wrapper around jjstack's `statusline.sh` with `refreshInterval`, off finishing running work.

## What the code does today
- Bare `wf` refuses inside a `wf run` call (`runner/finish.py:915`) and without a terminal unless `-y` (`:917`); its plan of repos with work is built quietly at `:944` to `:948`, which AC-5 reuses for the fingerprint.
- `wf report --hook` is the pattern for a hook that never fails (`runner/report.py:331`, `:353`); the held lock test is `locks_held()` (`:320`).
- The run picks its next feature in `pick()` (`runner/run.py:1590`) and waits for answers at the end in `end_wait()` (`:2326`). Stop reasons live in `RUN_STOPS` (`:206`) and their spec 0021 rows in `CASES` (`:212`).
- The live status line is `bash ~/.claude/skills/jjstack/bin/statusline.sh` (`settings.json` `statusLine`); the repo `settings.json` already runs `wf report --hook` at SessionStart.

## Research (from the brief, not repeated)
SessionStart fires on `clear`; a state file read by a hook survives `/clear` where built in modes do not; the status bar's only click is an OSC 8 link, and nothing in the bar or `keybindings.json` can run a command, so off is a command; a user only skill runs `` !`cmd` `` before Claude sees it; `systemd-run --user` puts `wf` outside the session.

## Decided without asking (2026-10-13)
1. **Clickable off control?** Options: an OSC 8 link to a local URL that turns it off (needs a local web server); no button, off is `/auto off`. Picked: the command. The docs allow only links, and a listening server for one toggle is more risk than value.
2. **One skill or two?** Options: `/auto-on` and `/auto-off`; one `/auto` with an argument. Picked: one `/auto` (the brief's `/auto on`, `/auto off`); P4 confirms `$ARGUMENTS` expands in the `!` line.
3. **How Claude is kept from turning it on.** Options: only the skill flag; the flag plus a deny rule plus a `WF_RUN` refusal. Picked: all three. Turning it on starts unattended runs, which invariant 5 reserves for you.
4. **Off by Claude in plain words?** Picked: allowed (the brief: "deactivate autonomous" makes Claude run the off script). Off only ever stops work.
5. **How the idle session notices changes.** Options: the user types something; a `wf auto wait` background command whose end re-invokes Claude. Picked: `wf auto wait` with `run_in_background`. The UserPromptSubmit line alone only helps when you type.
6. **When to start again.** Options: whenever `wf queue` shows work; only when the plan changed since the last start. Picked: changed plan. A feature stuck on an open question would otherwise restart `wf` in a loop.
7. **Answers that arrive with no run going.** The run's own end wait already listens up to `--max-wait` (12 h) and the next start re-pings open questions (spec 0011), so `wait` does not poll the phone itself.
8. **Off while a run is going.** Options: kill it; finish the features in progress and start no new one. Picked: finish (the brief), via a check in `pick()` and `end_wait()`, with `/auto off now` for the immediate stop (`systemctl --user stop`, which the run already treats as SIGTERM, `interrupted`).
9. **A broken `auto.json` during a run.** Options: treat as off; treat as on. Picked: on, so a corrupt file never stops a night's build; the session hook treats it as off (prints nothing), so it never starts one either.
10. **Status bar outside the driving folder.** Options: nothing; a plain `auto: <folder>`. Picked: the plain segment, so you can see from any session that some folder is driving.
11. **Where the wrapper lives.** Options: a new shell script in `~/.claude`; `wf auto bar` in the runner. Picked: `wf auto bar`, no new copy file to sync, and it reads the wf state directly.
12. **Unit environment.** User units do not inherit the session's PATH, so `wf auto start` passes PATH and the XDG folders explicitly; P2 checks `claude`, `bwrap`, `socat` and the inhibitor under the unit.
13. **Answering in chat.** Not in the agreed plan, so not built; the session tells you to answer on the phone. Listed as a follow-up.
