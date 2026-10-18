# 0059 verify: probes run before the build (AC-6)

Run 2026-10-17 with the throwaway `wf-probe` mod (`claude --plugin-dir`, and hot reloaded in the conductor session), Claude Code 2.1.302.

- [x] P1 AbovePrompt band draws on the terminal surface: green line "wf-probe band: five_hour 10%, seven_day 42%" above the prompt. PASS.
- [x] P2 toast on load: "wf-probe loaded: ..." shown top right. PASS.
- [x] P3 `$.session.usage()` rate limits: `rateLimits` is a list of `{kind: "five_hour" | "seven_day", percentUsed, resetsAt}` (field names to use), matching the status line within 1 point (band 10%/42%, bar 10%/43%). `context.percent` is null until the session's first model reply (band showed `?`, then 6%). PASS.
- [x] P4 `$.process.run(["wf", "queue"])` from a mod: exit 0, first line "claude-config on main, 0 changes". PASS.
- [ ] P4b session id shared between the status line stdin and the mod: not run; the build checks it first and, if absent, keys the short bar marker by cwd.
- [x] P5 the mod loads in a new session: `session.start` logged on each start, also after a hot reload. PASS. `$.state` persistence not exercised; the build keeps toast ids in a file next to its marker.
