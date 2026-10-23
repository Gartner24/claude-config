# 0078 verify notes

## P1 does the host send MultiEdit to mods (run 2026-10-22, Claude Code 2.1.309)
- Probe mod: a `tool.call` hook that appends `tool=<e.tool> keys=<sorted keys> json=<event>` for every call to a log file, then returns `next(e)`. Throwaway folder with one file `a.txt` (`one`, `two`); no settings changed.
- Command: `cd /tmp/ag0078/p1work; claude -p --plugin-dir /tmp/ag0078/p1mod --permission-mode acceptEdits "First list ... every tool you have. Then: if you have a tool named MultiEdit, use MultiEdit (not Edit) on a.txt ... If you have no MultiEdit tool, say NO-MULTIEDIT and then use Edit once on a.txt ..."`.
- Result: Claude listed its tools (loaded and deferred, checked through ToolSearch), none named MultiEdit, and answered `NO-MULTIEDIT`. The hook logged only `tool=Read` and `tool=Edit` (keys `file_path,new_string,old_string,replace_all,tool,tool_use_id`). The engine's generated mod types (`claude-code/index.d.ts`, 2026-10-22) name no `MultiEdit` either.
- Verdict: no. The host has no MultiEdit tool, so no `tool.call` with `tool: 'MultiEdit'` reaches a mod. Per AC-2 nothing is built for it.

## P5 how `$.fs.stat` answers (run 2026-10-22, Claude Code 2.1.309)
- Probe mod: a `tool.call` hook that calls `$.fs.stat(path, {resolve})` with `resolve` true and false on each case below and writes each answer, or the rejection message, to a log file, then returns `next(e)`. Throwaway folder `/tmp/ag0078/p5work`: `real/file.txt` (a file), `dangling -> nowhere.txt` (missing target), `tofile -> real/file.txt`, `todir -> real`; no settings changed.
- Command: `cd /tmp/ag0078/p5work; claude -p --plugin-dir /tmp/ag0078/p5mod --permission-mode acceptEdits "Run the Bash command: echo probe"`.
- Result (`resolve: true`; `false` is the same without `realPath`):
  - regular file `real/file.txt`: `{"kind":"file","isLink":false,"realPath":"/tmp/ag0078/p5work/real/file.txt"}`
  - dangling link `dangling`: resolves (no rejection) as `{"kind":"other","isLink":true}`, no `realPath`
  - link to a file `tofile`: `{"kind":"file","isLink":true,"realPath":"/tmp/ag0078/p5work/real/file.txt"}`
  - missing path `missing.txt`: rejects, `$.fs.stat(/tmp/ag0078/p5work/missing.txt) failed: ENOENT`
  - also: link to a folder `todir` gives `kind dir`, `realPath .../real`; a file under it `todir/file.txt` gives `realPath .../real/file.txt`; a missing file under it `todir/nope.txt` rejects ENOENT.
- Verdict: matches what `resolve()` relies on (a missing path rejects, so the walk up runs; a dangling link answers with no `realPath`, so the call is refused; a file or a link to one has `realPath`). The one difference from the test mock, `kind` of a dangling link (`other`, the mock said `file`), is not read by `resolve()`; the mock now answers `other`.

## Build checks (2026-10-22)
- Built in a scratch copy: upstream `ccdwyer/assertion-guardian` at pinned `ae1de89f` plus the old patch, which first equalled the live copy (`diff -r`, no difference).
- `claude plugin test`: 53 pass, 0 fail (46 before, 7 new). `claude plugin validate`: passed.
- Patch regenerated with `CLAUDE_LIVE_DIR=<throwaway live dir holding the built mod> python3 bin/claude-config.py patches`; upstream at pinned plus the new patch equals the built mod (`diff -r`, no difference). `TestShippedPatch` checks the same on every suite run.
- Review fixes (PR 206, 2026-10-22): `claude plugin test` 56 pass, 0 fail (3 new); `claude plugin validate` passed; patch regenerated the same way, upstream plus patch equals the built mod.
