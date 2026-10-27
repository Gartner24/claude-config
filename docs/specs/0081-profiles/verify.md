# Verify: profiles · spec 0081 · updated 2026-10-27
_Steps derived from spec 0081 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Probes
- [x] AC-25 rules subfolder probe, 2026-10-27, on Claude Code (this machine): wrote `~/.claude/rules/zz-probe-0081/x.md`
  ("When asked for the probe word, answer exactly: TANGERINE-4417"), ran
  `claude -p "What is the probe word? Answer with the word only, or NONE if you have no probe word."`, got
  `TANGERINE-4417`. Result: loaded, so private rule subfolders are kept. Probe file and folder removed.

## Commands
- [ ] `tools/bin/install.sh --dry-run --profile engineer` on the real machine lists no overwrite item but the
  `settings.json` order of two `permissions.deny` lines → AC-3, AC-5
- [ ] `python3 tests/fast.py` passes apart from the `review-isolated` jail failure → AC-1 to AC-26
- [ ] `claude plugin test claude-home/mods/chip-dash` passes → AC-9
- [ ] `python3 claude-home/hooks/profile-lock.py --test` passes → AC-10, AC-14

## Acceptance-criteria coverage
- AC-1 to AC-9b: tests/test_profiles.py (validator, install, overwrite, sync, profile command, GNU grep), tests/test_install.py,
  chip-dash band and facts tests
- AC-10 to AC-14: profile-lock.py self check, TestCustomProfile, TestLockHook
- AC-17, AC-23: TestProfileSettings, TestPrivateLayer, TestPrivateSync
- AC-18 to AC-20, AC-26: TestCreatorFiles
- AC-15, AC-22: not built yet (AC-15 waits on your yes; AC-22 in its own PR, the Remotion license question first)
