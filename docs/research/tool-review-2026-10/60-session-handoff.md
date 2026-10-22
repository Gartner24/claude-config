# Row 60: can /rollover continue without the user typing /clear and /resume-from-clear?

Short answer: yes, in a plain interactive session, by one of two mechanisms. Neither was run (read-only task), so both are UNVERIFIED in practice.

## What exists today (files read)
- ~/.claude/skills/rollover/SKILL.md step 5d: plain session ends with "Handover written to <slot path> -- type /clear, then /resume-from-clear." Only internal-relay workers (5e-5g) restart without the user: they send "restart fresh" to `<name>-manager`, which relaunches claude without `--continue` and auto-types `/sync-inbox fresh`; the QM resume order carries "/resume-from-clear".
- ~/.claude/skills/resume-from-clear/SKILL.md: wakes on "exactly three carriers": the handover slot (`jjstack-rollover-slot status`), a QM resume order, a internal-relay self-message. Step 1b "twin" check and step 8 `jjstack-rollover-slot consume` guard against double resume.
- ~/claude-config/_archive/runner/run.py:2937-2938: wf runs `claude -p ... --resume <id> --output-format json` or `--session-id <id>`. wf continues the SAME session id (no context reset); it never needs /clear because each box is a new `-p` call.
- ~/claude-config/claude-home/hooks/context-monitor.js: PostToolUse hook, warns at 150k, 650k critical, tells the model to run /rollover. It only advises.

## Official mechanisms found
1. Mod API (built-in plugin-authoring skill, types file /tmp/claude-1000/bundled-skills/2.1.296/c48b3255bf6ff36a5e0ef4c3b38a27d0/plugin-authoring/types/claude-code.d.ts; the skill is embedded in the binary, not a SKILL.md on disk):
   - `$.command.run`: "Runs a slash command as if the person typed `/command args`: the event `command.run`, queued and run once the session is idle." (line 3073). Whether the built-in `clear` is allowed is UNVERIFIED ("Rejects an unknown name, and inside a hook the turn is waiting on").
   - `$.prompt.submit`: "Submits a prompt ... a turn of its own, once the session is idle." (line 2946); `asUser: true` makes it read as the person's words (line 9023).
   - `session.end` hook: "`clear` is how a hook sees a `/clear`: the conversation ends, the process goes on under a new session id, and no `session.start` fires for it." (line 11062). Mod state `$.state`/`$.store` survives; "Values in `$.state` ... and `$.store` (across sessions) are the host's and stay" (skill text). Module loaded in the same process, so a mod could hold a pending "resume prompt" across the clear.
   - `$.session.send({to:{sessionId}})` messages another RUNNING session of the same person (line 2884-2892); a session not running "is not delivered to".
   - `$.session.usage()` + `$.session.compact()` (line 2845): a mod can read context percent itself.
   - Mods are new: CHANGELOG lists `$.session.identity`, `prompt.change`, `$.ui.view` etc. (https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md). Announcement: https://claude.com/blog/claude-code-mods (HN story 49925102; not fetched, unverified content).
2. Classic hooks, no mod needed. https://code.claude.com/docs/en/hooks.md: SessionStart `source` is "`clear` after `/clear`" (line 1233), and "`additionalContext` | String added to Claude's context at the start of the conversation, before the first prompt." (line 1272). `initialUserMessage` works only with `-p`. So a SessionStart hook with matcher `clear` that runs `jjstack-rollover-slot status` and injects the slot text as additionalContext makes the post-/clear session start already holding the handover. The user still types /clear.
3. `claude --continue / --resume / --fork-session`, SDK: continue a transcript (no fresh context), what wf already uses. CHANGELOG line 7973: `--session-id` with `--fork-session`.

## Which mechanism removes the user
- A: mod with a `/rollover-go` (or `command.run` hook) that, after the skill writes the slot, calls `$.command.run({command:"clear"})` then `$.prompt.submit({text:"/resume-from-clear", asUser:true})` on the clear's `session.end`. Fully hands-free. Risks: `clear` via command.run unverified; submit-after-clear ordering unverified; mod hot-reload asks the person once per session ("Enable hot reloading for this session?").
- B: classic SessionStart(clear) hook. Safe, documented, but the user still types /clear. Removes only the /resume-from-clear typing.
- Existing internal-relay path stays for workers.

## Risks
- Lost context: resume-from-clear reads the whole transcript; a hook-injected slot must still point to it (10,000 char cap on additionalContext, hooks.md line 1017).
- Double resume: slot is consumed in step 8, but a hook that re-injects on every clear would resume twice; twin check (step 1b) handles forks only. Hook must key on slot presence and consume it.
- Permission prompts: submitted prompt runs as a normal turn under the session's permission mode; skill `Bash` calls prompt as usual. The wf sandbox deny lists do not apply to interactive sessions.
- Background tasks raise the exit dialog (QM #675 in rollover SKILL.md): keep quiet-exit before clear.
- Prompt/command injection by a mod bypasses the user's own typing; the user's injection-guard hooks (UserPromptSubmit) will see an origin `plugin`.

## Others' work
HN search (hn.algolia.com, "claude code mods"): only unrelated mods (MIDI sounds, https://github.com/delexw/miod). No session-handoff mod found. Not exhaustive; GitHub not searched.

## Recommendation: adapt (B now, A after a probe)
1. Build B (SessionStart matcher `clear` hook calling `jjstack-rollover-slot status/read`, never edit jjstack; put hook in claude-config). Effort: ~1 hour, near zero cost, low risk. Saves one typed command.
2. Probe A in a throwaway mod folder in a scratch session: does `$.command.run({command:"clear"})` work, and does a `$.prompt.submit` queued in `session.end` run in the new session? Per spec-gate.md a design depending on outside tool behaviour needs a real probe before accept. If both pass, ship A as a claude-config mod (needs skillspector scan first). Effort: half a day.
3. Reject building our own tmux/pty driver for plain sessions: mods make it unnecessary. Keep wf as is (`--resume` is the right tool there; no clear needed).
