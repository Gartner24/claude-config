# 0036 rationale

## Why
Personal plan row 20: turn on jjstack's missed-skill detector so you see which skills should have fired and did not. The row asks for a JSON parse check after the edit, because a trailing comma once made Claude Code ignore the whole settings file.

## Decided without asking (2026-10-14)
Per `docs/briefs/finish-runner-today.md`, the recommended option was taken for every question.

| Question | Options | Pick |
|---|---|---|
| Which hooks | the detector only; detector plus `skill-fired-clear.sh` | Both. The detector alone logs every trigger match as a miss, because only `skill-fired-clear.sh` clears the pending note (`skill-fired-clear.sh:38-46`). |
| Where the edit is made | repo `settings.json` then `install.sh`; live `settings.json` then `sync.sh` | Repo then install, as the ticket asks. `sync.sh` runs first (AC-3) because `install.sh` replaces the live file with the repo copy (`install.sh:115-118`); without it an unsynced live edit would be lost. |
| Under `wf run` | on; off via a `WF_RUN` test in the settings command; off via a wrapper script | Off, inline in the settings command. Unattended prompts are box commands, not your words, so they would only add noise. An inline `[ -n "$WF_RUN" ] ||` needs no new file and leaves the vendor script untouched. |
| Parse check | the existing real install check only; add one to the dry run; a separate script | Add it to the dry run, keep the real one. The dry run is what you run before installing (`AGENTS.md` `## Commands`), and today it never parses the file. |
| Report surface | run it by hand; a SessionStart line; put it on `PATH` | By hand, by full path, documented. The ticket asks to read one report; a daily nag or a new `PATH` link is not asked for. |
| Trigger index | rebuild now; leave the 2026-09-02 one | Rebuild: an index older than the current skills matches skills that are gone and misses new ones. |
| When the feature is done | after wiring; after one report is read | After one report is read, as the row's "Done when" says, and at least 3 days in so the 24 h and 72 h windows hold real use. |
