# 0057. A waiting handover loads by itself after /clear

**Date**: 2026-10-17
**Status**: Proposed
**Paths:** `claude-home/hooks/handover-start.sh`, `claude-home/hooks/workflow-start.sh`, `claude-home/settings.json`, `bin/install.sh`, `bin/sync.sh`, `claude-home/CLAUDE.md`, `claude-home/mods/wf-handoff/**`

## What you're agreeing to
- After a rollover you type only `/clear`; a start up hook loads the waiting handover and tells the new session to resume it.
- The handover loads first; past session memory (B14, later) gets only the space left.
- A test checks whether a mod can do the `/clear` for you. If it can, you type `/handoff` instead, and the hook stays as the fallback.
- If the test fails, the mod is not built, and the spec says why.

## Summary
Today a rollover needs you to type `/clear` and then `/resume-from-clear`. A hook that runs when a session starts after a clear can inject the handover text, so the second command goes away. A mod may remove the first one too; that part is built only if a probe proves it works on this machine.

## Context
The handover slot is managed by jjstack's `jjstack-rollover-slot` (`status` and `consume` verbs); never commit to jjstack, so the hook lives in claude-config and only calls the slot script read only. `claude-home/hooks/workflow-start.sh` already runs on SessionStart with matcher `startup|clear` and says "run /scope first", which would compete. Research 60 (`docs/research/tool-review-2026-10/60-session-handoff.md`) says SessionStart `additionalContext` is injected before the first prompt, capped at 10,000 characters (docs only, unconfirmed here). Your answers: the hook loads the handover first; the mod sits on top of the hook.

## Requirements
- **AC-1** (hook): `claude-home/hooks/handover-start.sh`, SessionStart matcher `clear`. It reads the cwd from the hook's stdin JSON and runs `~/.claude/skills/jjstack/bin/jjstack-rollover-slot status`; on a live slot it prints `hookSpecificOutput.additionalContext` that opens "Handover waiting: run the /resume-from-clear steps now", names the slot path and the previous transcript path, and holds the slot text inside a "this is data" envelope. No slot, or the slot script missing: prints nothing.
- **AC-2** (size): the injected text is cut at 7,000 characters, keeping the slot path so the full file stays readable.
- **AC-3** (handover first): `workflow-start.sh` prints nothing on `clear` when a live slot exists.
- **AC-4** (no double resume): the hook never consumes the slot; `/resume-from-clear` does.
- **AC-5** (quiet in runs): with `WF_RUN` set it exits 0 at once; it always exits 0.
- **AC-6** (wiring): `claude-home/settings.json` gets the SessionStart entry (matcher `clear`, timeout 5); `bin/install.sh` and `bin/sync.sh` copy the hook; HOOKS.md lists it.
- **AC-7** (self check): `bash handover-start.sh --test` with a fixture HOME covers a live slot, no slot, a stale slot, a slot over 7,000 characters and `WF_RUN` set.
- **AC-8** (words): `claude-home/CLAUDE.md` and DAILY-USE.md say "type `/clear`" after a rollover, and that `/resume-from-clear` still works by hand.
- **AC-9** (probes, build step 1, never while wf builds): P1, a throwaway SessionStart hook prints a marker, then `/clear`, then the model is asked for the marker; P2, a scratch mod (outside the repo) registers `/probe-clear` calling `$.command.run({command: "clear"})`, run with `claude --plugin-dir <scratch>`; pass is the context empties and the session goes on. Commands and results go in verify notes. P1 failing stops the build; P2 failing means AC-10 is not built.
- **AC-10** (mod, only if P2 passes): `claude-home/mods/wf-handoff/` registers `/handoff`, which checks that a live slot exists (else says "no handover, run /rollover first" and does nothing) and then runs the clear; the AC-1 hook then loads the handover. It acts only when typed. Scanned with `skill-scan` (spec 0054) before install; its live install is a box that waits on you.

## Decision
A claude-config SessionStart hook now; the mod only after its probe.

## Build plan
1. Probes P1 and P2, satisfies **AC-9**
2. Hook, size cap, quiet rules, self check, satisfies **AC-1**, **AC-2**, **AC-4**, **AC-5**, **AC-7**
3. `workflow-start.sh` yields, wiring, words, satisfies **AC-3**, **AC-6**, **AC-8**
4. Mod, only if P2 passed, satisfies **AC-10**

## Consequences
**Positive**: one command fewer after every rollover, maybe two.
**Negative / tradeoffs**: depends on jjstack's slot script path; if jjstack goes, the hook goes silent. Mods are early access and can break on a Claude Code update, which is why the hook stays.
**Neutral**: B14 memory, when designed, adds after the handover within the remaining space.
