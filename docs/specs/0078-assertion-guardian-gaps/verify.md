# 0078 verify notes

## P1 does the host send MultiEdit to mods (run 2026-10-22, Claude Code 2.1.309)
- Probe mod: a `tool.call` hook that appends `tool=<e.tool> keys=<sorted keys> json=<event>` for every call to a log file, then returns `next(e)`. Throwaway folder with one file `a.txt` (`one`, `two`); no settings changed.
- Command: `cd /tmp/ag0078/p1work; claude -p --plugin-dir /tmp/ag0078/p1mod --permission-mode acceptEdits "First list ... every tool you have. Then: if you have a tool named MultiEdit, use MultiEdit (not Edit) on a.txt ... If you have no MultiEdit tool, say NO-MULTIEDIT and then use Edit once on a.txt ..."`.
- Result: Claude listed its tools (loaded and deferred, checked through ToolSearch), none named MultiEdit, and answered `NO-MULTIEDIT`. The hook logged only `tool=Read` and `tool=Edit` (keys `file_path,new_string,old_string,replace_all,tool,tool_use_id`). The engine's generated mod types (`claude-code/index.d.ts`, 2026-10-22) name no `MultiEdit` either.
- Verdict: no. The host has no MultiEdit tool, so no `tool.call` with `tool: 'MultiEdit'` reaches a mod. Per AC-2 nothing is built for it.

## Build checks (2026-10-22)
- Built in a scratch copy: upstream `ccdwyer/assertion-guardian` at pinned `ae1de89f` plus the old patch, which first equalled the live copy (`diff -r`, no difference).
- `claude plugin test`: 53 pass, 0 fail (46 before, 7 new). `claude plugin validate`: passed.
- Patch regenerated with `CLAUDE_LIVE_DIR=<throwaway live dir holding the built mod> python3 bin/claude-config.py patches`; upstream at pinned plus the new patch equals the built mod (`diff -r`, no difference). `TestShippedPatch` checks the same on every suite run.
