# 0060 verify: probes run before the build (AC-6)

Run 2026-10-17 with the throwaway `wf-probe` mod, Claude Code 2.1.302.

- [x] P6 a Pane opens beside the conversation: `/probe-pane` gave `{"isPlaced": true}` and drew at the terminal width. PASS.
- [x] P7 `$.agent.list()` returns subagents only (one general-purpose helper listed while it ran; "0 agent loops" in a session with none). The main session is not in the list, so the agents pane labels the main session itself. PASS.
- [ ] P8 stopping a background task from a mod: not run yet.
- [x] P9 `$.prompt.submit` runs as a turn: called from `$.clock.after(1500, ...)` after the `command.run` hook returned, the transcript showed "Prompt from the wf-probe plugin" and the reply "probe submit ok". PASS with that rule.

Build rule from P9: the "start the next step" action returns from its hook first and submits from `$.clock.after`, never awaited inside the hook.
