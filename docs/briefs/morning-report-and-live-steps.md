# Morning report and live setup steps in one command

## Agreed so far, do not ask again
- Trigger: the 2026-10-13 night run built features 24, 25, 28 and 29, ended at 03:20 and sent no message. You woke up with six manual steps spread over four features and no summary.
- The safety rule stays: an unattended `wf run` call never writes `~/.claude` or `.git/hooks` and never starts a real claude test run by itself.
- Fix A, live setup steps in one command: the runner keeps building, collects every waits-on-you step of the run that copies into `~/.claude`, runs `install.sh` or runs a real claude check, and at the end gives you one command that does them all (back up, copy, install, put `autoMode` back, run the checks, record results, tick the boxes). You paste one line instead of a list.
- Fix B, morning report: when a run ends, for any reason, one phone message: what got built, what waits on you, and the next command. The next `~/.claude` session opens with the same report.
- Both are designed now, in one `/architect` sitting, and queued `· auto` for the next run.

## Open for /architect
- Fix A: where the one command lives (`wf finish`, or a script the run writes into its run folder) and whether real claude checks (`runner/e2e/run.py`, probes) run inside it or stay separate.
- Fix A: `install.sh` drops the live `autoMode` section on every run (it rewrites `settings.json` from the repo copy). Keep live only keys instead of restoring them afterwards?
- Fix B: the message length limit on the phone, and what a run that ended on a crash or a limit says.
