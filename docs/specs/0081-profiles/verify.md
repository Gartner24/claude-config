# Verify: profiles · spec 0081 · updated 2026-10-27
_Steps derived from spec 0081 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Probes
- [x] AC-25 rules subfolder probe, 2026-10-27, on Claude Code (this machine): wrote `~/.claude/rules/zz-probe-0081/x.md`
  ("When asked for the probe word, answer exactly: TANGERINE-4417"), ran
  `claude -p "What is the probe word? Answer with the word only, or NONE if you have no probe word."`, got
  `TANGERINE-4417`. Result: loaded, so private rule subfolders are kept. Probe file and folder removed.

## Commands
- [x] `tools/bin/install.sh --dry-run --profile engineer` on the real machine lists no overwrite item but the
  `settings.json` order of two `permissions.deny` lines -> AC-3, AC-5 (2026-10-30: "overwrite: nothing to lose", profile engineer)
- [x] `python3 tests/fast.py` passes apart from the `review-isolated` jail failure -> AC-1 to AC-26 (2026-10-30 on main: 281 tests, 0 failed)
- [x] `claude plugin test claude-home/mods/chip-dash` passes -> AC-9 (2026-10-30: 86 pass, 0 fail, incl. "the band shows the active profile")
- [x] `python3 claude-home/hooks/profile-lock.py --test` passes -> AC-10, AC-14 (2026-10-30: "all self-checks passed", creator refused on `tools/bin/install.sh`)

## Acceptance-criteria coverage
- AC-1 to AC-9b: tests/test_profiles.py (validator, install, overwrite, sync, profile command, GNU grep), tests/test_install.py,
  chip-dash band and facts tests
- AC-10 to AC-14: profile-lock.py self check, TestCustomProfile, TestLockHook
- AC-17, AC-23: TestProfileSettings, TestPrivateLayer, TestPrivateSync
- AC-18 to AC-20, AC-26: TestCreatorFiles
- AC-15: TestCodeOwners; the GitHub rule set waits until your partner gets push access
- AC-22: TestProfileFiles (14 video skills on in creator, name-only in engineer), TestLockHook.test_creator_editable; the lemo-opuscar
  patch applies at the pin, and the two git steps it adds (fetch the pinned commit, check it out) were run by hand
