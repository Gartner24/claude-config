# 0057 verify: probes run before the build (AC-9)

Run 2026-10-17 by you in scratch sessions, Claude Code 2.1.302. Probe sources: a throwaway hook and the throwaway `wf-probe` mod in the conductor session's dev-mods folder (never installed).

- [x] P1 SessionStart hook on `clear` reaches the model: `claude --settings <scratch>/settings.json` with a `matcher: "clear"` hook printing `hookSpecificOutput.additionalContext` "PROBE MARKER: the secret word is pelican-42"; after `/clear`, "What is the secret word?" answered "pelican-42", naming the SessionStart hook's added context. PASS.
  can fail: the hook output not injected after a clear, or plain stdout ignored
- [x] P2 a mod runs `/clear` and the session goes on: `claude --plugin-dir <wf-probe>`, `/probe-clear-scratch-only`. First try FAILED: `$.command.run` awaited inside a `command.run` hook is refused ("called from a command.run hook, it would wait on the turn this hook is holding"). Second try, the call made from `$.clock.after(1500, ...)` after the hook returned: the transcript showed `/clear`, the context emptied, the session kept running. PASS with that rule.
  can fail: the clear refused from a plugin, or the process exits

Build notes (2026-10-17, /develop): `bash claude-home/hooks/handover-start.sh --test` 18 checks pass (hook and the workflow-start yield, slots written by the real slot script). `claude plugin test claude-home/mods/wf-handoff` 2 pass; `claude plugin validate` passes (one warning, no author). Spec 0054's `skill-scan` is not built yet, so the scan was `skillspector scan claude-home/mods/wf-handoff --no-llm`: score 0/100, 0 issues (static pass only; the model pass is yours to run before install).

Build rule from P2: `/handoff` (AC-10) returns from its `command.run` hook first and runs the clear from `$.clock.after`, never awaited inside the hook.

## /check verify, 2026-10-17 (wf run, sandbox)

- [x] `bash claude-home/hooks/handover-start.sh --test`: 18 ok, "all self-checks passed" (real `jjstack-rollover-slot write` fixtures) -> AC-1, AC-2, AC-3, AC-4, AC-5, AC-7
  can fail: confirmed on scratch mutants, each turned a check red: hook ignores `WF_RUN` (M1), cap raised to 9000 bytes (M2, 8999), 5 day max age (M3), workflow-start keeps `/scope` with a live slot (M4)
- [x] Independent drive on a scratch HOME, the command taken from `claude-home/settings.json` (SessionStart `matcher: clear`, `bash ~/.claude/hooks/handover-start.sh`, timeout 5) -> AC-1, AC-3, AC-4, AC-6:
  slot written by the real slot script; hook on `clear` printed one JSON object opening "Handover waiting: run the /resume-from-clear steps now", then `Slot: <path>`, `Previous transcript: /x/prev.jsonl`, the slot text between `<<<HANDOVER DATA>>>` and `<<<END HANDOVER DATA>>>`, exit 0; workflow-start printed only the weekly line (no `/scope`); slot still on disk after the hook; after `consume` a second clear printed 0 bytes and workflow-start went back to "run /scope"; bad stdin exits 0 silently
  can fail: confirmed, the M5 mutant (hook drops the transcript line) printed no `Previous transcript:` header line
- [x] `claude plugin test claude-home/mods/wf-handoff`: 2 pass (clears only with a live slot, only after the timer, same status argv as the hook); `claude plugin validate`: passed, one warning (no author) -> AC-10
  can fail: confirmed, M6 (clear called at once instead of from `$.clock.after`) failed both tests
- [x] `python3 -m unittest runner.tests.test_swap`: 10 OK; `bin/install.sh --dry-run` lists `hooks/handover-start.sh` copy and chmod; install's self check exits 1 on failure (`bin/install.sh:263`); `bin/sync.sh` scans and copies it (`OPTIONAL`, like workflow-start.sh, since it is not live before the first install) -> AC-6
  can fail: the dry run would not list the hook if the install loop missed it
- [x] Words read: `claude-home/CLAUDE.md` Route and Context sections and `docs/guides/DAILY-USE.md` step 7 say type `/clear` after a rollover and that `/resume-from-clear` still works by hand -> AC-8
- [x] AC-9 probes P1, P2: passed earlier in your scratch sessions (above)
- Left to the box: "Copy the hook and settings live (`bin/install.sh` copies both and runs the hook self check), and install the mod" (a real `/clear` and `/handoff` in a live session with the installed hook and mod)

Full suite (`python3 runner/tests/fast.py`): 972 tests, 1 failed, `test_layout.TestShape.test_links`: `docs/scope/scope.md` links to `../specs/0061-runner-improves-itself/index.md` and `../specs/0054-skill-scan-script/verify.md`, both added by a323d64 (PR #40 on main) and missing on both main and this branch. Not from this feature; you said pass it and go on (2026-10-17), so the Verify box is ticked.

Weak test found for `/test`: the self check "names slot path and transcript" passes on M5, because the transcript path also appears inside the handover data; it should look at the header before `<<<HANDOVER DATA>>>`.
