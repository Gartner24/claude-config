# 0057 verify: probes run before the build (AC-9)

Run 2026-10-17 by you in scratch sessions, Claude Code 2.1.302. Probe sources: a throwaway hook and the throwaway `wf-probe` mod in the conductor session's dev-mods folder (never installed).

- [x] P1 SessionStart hook on `clear` reaches the model: `claude --settings <scratch>/settings.json` with a `matcher: "clear"` hook printing `hookSpecificOutput.additionalContext` "PROBE MARKER: the secret word is pelican-42"; after `/clear`, "What is the secret word?" answered "pelican-42", naming the SessionStart hook's added context. PASS.
  can fail: the hook output not injected after a clear, or plain stdout ignored
- [x] P2 a mod runs `/clear` and the session goes on: `claude --plugin-dir <wf-probe>`, `/probe-clear-scratch-only`. First try FAILED: `$.command.run` awaited inside a `command.run` hook is refused ("called from a command.run hook, it would wait on the turn this hook is holding"). Second try, the call made from `$.clock.after(1500, ...)` after the hook returned: the transcript showed `/clear`, the context emptied, the session kept running. PASS with that rule.
  can fail: the clear refused from a plugin, or the process exits

Build rule from P2: `/handoff` (AC-10) returns from its `command.run` hook first and runs the clear from `$.clock.after`, never awaited inside the hook.
