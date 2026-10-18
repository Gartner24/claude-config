# 0063. Auto handoff: our handover, fired on its own

**Date**: 2026-10-18
**Status**: Proposed
**Paths:** `claude-home/mods/wf-handoff/**`
**Amends:** [0057](0057-handover-on-clear.md) AC-10 (the mod no longer acts only when typed)

## What you're agreeing to
- When a chat reaches 200k tokens, it hands itself off: it runs our full `/rollover`, clears, and the fresh chat resumes with nothing typed.
- Past the line, new tool calls are refused so one burst of reads cannot overflow; the handoff starts at the end of that turn.
- Code, not the model, adds the facts to the handover: files changed, commits, issues, real token numbers, and your last request with whether it was answered.
- Loop guards: a fresh chat must grow 40k before it can hand off again, and after 2 handoffs with no message from you it pauses until you type.
- It runs in every interactive chat, never inside wf runs or background workers; auto compact and compact-keeper stay as the backstop.

## Summary

Today a long chat only hands off when Claude runs `/rollover` and you type `/handoff`. This spec makes the handoff mod watch the context size and do the whole thing itself at 200k: it asks the working model for the full handover, adds the facts code can know for sure, clears, and starts the fresh chat on `/resume-from-clear`. It copies the parts of alexknowshtml/claude-auto-handoff (MIT) that beat ours, and keeps ours where ours is better: the note is written by the working model, never a cheaper one. The display side (progress in the band, viewer pages, the handoff link) is spec 0064.

## Context

The owner wants chats to stay sharp without having to remember to hand off. Today the hand off waits on two things: the model noticing it is past about 150k and running `/rollover`, and the owner typing `/handoff`. On a long build either one slips, and the chat drifts toward the 700k auto compact, which squashes it into a summary nobody controls.

alexknowshtml/claude-auto-handoff 0.8.6 (MIT) fires on its own at a token line and adds facts by code, but its note is written by Haiku from the transcript, which loses decisions. Our `/rollover` (a vendored jjstack skill, overwritten on every pull) writes a richer note and saves agreed decisions into repo files, and `/resume-from-clear` reads the whole previous transcript. The brief `docs/briefs/auto-handoff.md` records the owner's verdict: every part of theirs that is better, ours gets.

Constraints: the mod engine (function hooks, `$.*` calls) is what both mods use; `/rollover` cannot be edited (vendored), so anything added to the note is added by the mod around it; the start hook `handover-start.sh` (spec 0057 AC-2) cuts the slot text at 7,000 bytes, so whatever the mod adds must survive that cut; wf runs and background worker chats manage their own context and must not be touched.

## Requirements

**User stories**:
- As the owner, I want a long chat to hand itself off at 200k with nothing typed, so it never fills up or gets auto compacted.
- As the owner, I want the fresh chat to know exactly what changed and what I last asked, so it never guesses.

**Acceptance criteria**:
- **AC-1** (line): the mod reads the context size after every turn (`turn.complete`) and before every model request (`turn.step`), adding tool output not yet measured at 4 characters per token. The line is the `threshold` setting (default 200000), or `AUTO_HANDOFF_TOKENS` when set; in a chat that started from a handoff it is never lower than that chat's starting size plus `minHeadroom` (default 40000). The starting size is the `$.session.usage().context.tokens` read right after `next(e)` returns in the first `turn.step` of the seeded turn (before `next(e)` it is unset in a just cleared session, probe P4; measuring at turn end let reads inflate it upstream). Only main loop events count: any event carrying an `agentId` (a subagent) is ignored. When `turn.step` finds the size past the line, it ends the turn there and arms the handoff, so a long stretch without tool calls cannot run past it; how a `turn.step` hook ends the turn is settled by probe P7 (AC-13).
- **AC-2** (tool gate): once the size is past the line and no handoff is running, every `tool.call` is refused with the text "context is at the handoff line; finish this turn in words, the handoff starts at the end of it". A refused call always ends in a handoff at the end of that turn, even if the measured size later reads under the line; if that turn is interrupted (Esc) and no `turn.complete` arrives, the next `turn.step` or the next owner prompt starts the handoff instead. The gate never refuses calls in a turn whose prompt starts with `/rollover`, `/save-and-clear` or `/handoff`, or whose `prompt.submit` carries `command.name` `rollover`, `save-and-clear` or `handoff`, or while the module `rolling` flag is set (AC-3), so a hand started rollover still works past the line.
- **AC-3** (rollover): at the end of a turn past the line, the mod captures the last prompt the owner typed (a `prompt.submit` with origin `composer` or `bridge` whose text does not start with `/`; only these reset the guard count and set the last request) and runs `$.command.run({ command: 'rollover', args: <sections template text> })` straight from `turn.complete` (a mod may not send slash text through `$.prompt.submit`, probe P1), It sets a module `rolling` flag before the call; the first main loop `turn.complete` (no `agentId`) after the call resolves is the rollover's end (probe P1 saw the call resolve and then the command's turn start). The sections template (AC-9) asks for a `## Last request from the owner` section quoting that prompt and a `Status: answered` or `Status: not answered` line. Tool calls are not gated while this rollover turn runs.
- **AC-4** (facts by code): when the rollover turn ends and `${HOME}/.claude/skills/jjstack/bin/jjstack-rollover-slot --cwd <cwd> status --max-age-days 1` (the same path and flags as the existing `/handoff`) names a slot whose file modification time is later than `triggeredAt`, the mod inserts a `## Handoff facts` block right after the slot's first heading line, so the 7,000 byte cut keeps it: files edited or written this session (from `Edit`, `Write`, `NotebookEdit` tool calls in `$.session.messages()`, minus paths matching the `ignoreFiles` setting), commit hashes and subjects from `git commit` tool output, and GitHub issue and PR links from tool output. When the `viewer` setting is not blank, the block also holds one `viewer: <link>` line (spec 0064 AC-6). Facts, the viewer line and numbers together stay under 2,000 bytes; longer lists end in `+N more`, so the 7,000 byte cut still keeps the rollover's next actions. Code reused from their `brief.ts` `extractFacts`. A rollover turn that ends with no new slot (including one that ends on a question to the owner) is a failure under AC-8.
- **AC-5** (numbers by code): the same block carries `## Handoff numbers`: tokens at handoff, the line and where it came from (`threshold` setting, `AUTO_HANDOFF_TOKENS`, or start plus headroom), the starting size of this chat when it came from a handoff (else `unknown`), and the handoffs since the owner last typed. In the slot's lines that mention context or tokens (never file names, code spans or the numbers block itself), any figure that is not in Handoff numbers (a number followed by `k` or `tokens`, a bare number of 4 or more digits with or without commas, or a percentage) is suffixed `[unverified: not in Handoff numbers]` and logged.
- **AC-6** (clear and seed): after AC-4 and AC-5, the mod starts one `$.clock.after` callback (spec 0057 probe P2) that awaits `$.command.run({ command: 'clear' })` and, once it resolves, runs the seed as `$.command.run({ command: 'resume-from-clear', args: <instructions template text> })` (AC-9) in the same callback. No `session.start` fires after a `/clear` (probe P3); the start hook of spec 0057 has already run when the clear call resolves, so its text is in context before the seed. The mod marks the session as seeded (module variable and chain state) at the moment it runs the seed, never by watching its own submit; an owner's own `/clear` gets no seed. The 15 second timeout covers only the awaited clear call: if it rejects or has not resolved by then, the phase goes to failed (AC-8) and a late resolve is ignored (no seed); the failure text says the chat may still have cleared. The seed call is run without awaiting the resume turn; a seed failure means only that the call rejects at once. The phase never sticks in clearing or seeding. The start hook of spec 0057 still loads the handover text; the seed is the only carrier of the priority part, and the resume runs once, from the seed. The priority switch reads the `Status:` line directly under `## Last request from the owner`; when it reads `not answered` the fresh chat answers that request first. Chain identity: the mod keeps the root session id in a module variable that survives `/clear` and in the chain state file, keyed by root. An owner prompt typed while the phase is rolling, clearing or seeding is held: the mod's `prompt.submit` hook refuses it and keeps its text, and at that moment it resets the guard count (AC-7) and sets the last request. Right after the seed call the mod sends it again, slash text through `$.command.run` and plain text through `$.prompt.submit`; the owner types nothing else. The host puts a dropped text back in the composer box (probe P8), so the drop reason reads "held for the handoff; it is sent for you, clear the box".
- **AC-7** (loop guards): a handoff is counted when its seed command is run, and a failed handoff counts too; after `maxConsecutiveHandoffs` (default 2) counted handoffs with no owner prompt in between, the mod stops handing off and gating, shows "auto handoff paused: type anything to resume" (a toast here; the band in spec 0064), and resumes counting at the next owner prompt.
- **AC-8** (failure): if the rollover turn ends with no new slot, nothing is cleared; if the clear call fails or times out, the mod does nothing further; if the seed fails after the clear, the handover stays in the slot for a typed `/resume-from-clear`. Either way the gate opens, the failure stays visible until the owner types, and it is logged. Auto compact (700k) and compact-keeper are left as they are, as the backstop.
- **AC-9** (templates): `sections.md` and `instructions.md` ship in the mod's `templates/` and are copied to `~/.claude/auto-handoff/` on first start when missing; the owner's copies win. `instructions.md` supports `{{#priority}}...{{/priority}}` and `{{^priority}}...{{/priority}}`, switched by the `Status:` line.
- **AC-10** (settings): `threshold`, `minHeadroom`, `maxConsecutiveHandoffs`, `sectionsTemplate`, `instructionsTemplate`, `ignoreFiles`, and `viewer` (format `[host:]port`, host `tailscale` or an IP, default `tailscale:3846`, blank for no server; used by spec 0064) are rows in `/config` under the mod (stored in `pluginConfigs`); `AUTO_HANDOFF_TOKENS` overrides the line for one shell, `AUTO_HANDOFF_DISABLE=1` turns the mod off for one session.
- **AC-11** (where): the mod acts only in interactive main sessions; it does nothing in headless (`claude -p`) sessions, for subagent events (`agentId` set), or when `WF_RUN` or `TM_WORKER_NAME` is set. Its folders (`~/.claude/state/auto-handoff/`, `~/.claude/auto-handoff/`) are created through `$.fs.write`, which makes parent folders (upstream 0.8.6 relies on this; probe P5 checks it). `/handoff` (spec 0057 AC-10) keeps working by hand.
- **AC-12** (log): every trigger, refusal, slot found or missing, clear, seed, pause and failure goes to `~/.claude/state/auto-handoff/auto-handoff.log`, one line each with the session id.
- **AC-13** (probes, build step 1): P1 `$.command.run({ command, args })` from `turn.complete` runs a slash command as if typed; P2 a refusing `tool.call` hook returns the refusal text to the model and the turn ends in words; P3 a `$.command.run` seed made in a `$.clock.after` callback right after an awaited `$.command.run({ command: 'clear' })` reaches the new session with plugin origin, and the spec 0057 start hook text is already in its context; P4 `$.session.usage().context.tokens` is set inside `turn.step`; P5 `$.fs.write` to a path whose folders do not exist creates them; P6 the real `/rollover` run through `$.command.run({ command: 'rollover', args })` with the sections text writes a slot newer than the call (no hook stops it); P7 a `turn.step` hook can end the current turn before the next model request, and the way it does so; P8 a `prompt.submit` hook can refuse a composer prompt, and the mod can send its text again afterwards. Run with `claude --plugin-dir <scratch>` in a scratch folder, results in verify notes. Any FAIL stops the build and sends this spec back to `/architect`. Run 2026-10-18: P1 to P5 pass in the forms above (P1 and P3 failed as first worded, with `$.prompt.submit`). P6 to P8 pass (run 2026-10-18): the rollover writes a slot, a `turn.step` hook ends the turn by answering with `stopReason: 'end_turn'` and no tool uses without calling `next(e)`, and a `prompt.submit` hook refuses with `{ drop }`.
- **AC-14** (scan and credit): the reused code from claude-auto-handoff is named in `docs/NOTICE.md` with its MIT license; the mod passes `skill-scan` before its live install, a box that waits on you.

## Options considered

### Option 1: Install their mod as is
Load claude-auto-handoff beside ours.
**Pros**: nothing to build; maintained upstream.
**Cons**: Haiku writes the note, losing decisions; replaces auto compact; skips our twin check, transcript read and scope briefs; two handoff systems fight.

### Option 2: Extend our wf-handoff mod, reusing their code where it is better
Our `/rollover` and resume stay; the mod gains their trigger, gate, guards, facts, numbers and templates, with their MIT code reused.
**Pros**: keeps the stronger note; one system; their tested logic for the parts we lacked.
**Cons**: we own the merged code; upstream fixes need copying by hand.

### Option 3: Rules only (no mod), the model runs `/rollover` at 200k
**Pros**: no code.
**Cons**: it is what fails today; no gate, no auto clear.

## Decision

**Chosen option**: Option 2: extend `wf-handoff`, reusing their code.

## Rationale

The owner's verdict was to take every part of theirs that is better. Option 2 is the only one that does that without giving up the parts where ours is better (the working model writes the note, the resume reads the full transcript). Reuse is allowed by their MIT license and cuts the build to adapting proven logic.

## Feature design

**Data model sketch**: no database. One state file per chain, `~/.claude/state/auto-handoff/<root session id>.json`: `root` (string), `session` (the current session id), `previous` (the session id before the last clear, or null), `startTokens` (number or null), `unattended` (number), `triggeredAt` (ISO time or null), `phase` (`idle`, `gated`, `rolling`, `clearing`, `seeding`, `paused`, `failed`), `lastRequest` (string or null).

**State transitions**: idle -> gated (past the line mid turn) -> rolling (rollover command run) -> clearing (slot found, facts added) -> seeding -> idle in the new session. rolling -> failed (no slot); any -> paused (guard). failed and paused -> idle on the next owner prompt.

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| line check | context size | `$.session.usage().context.tokens` plus unmeasured tool output / 4 |
| line check | the line | `threshold` setting, `AUTO_HANDOFF_TOKENS`, or `startTokens` + `minHeadroom` |
| rollover prompt | last request | last `prompt.submit` with origin `composer` or `bridge` |
| facts block | files, commits, issues | `$.session.messages()` tool calls and results |
| numbers block | start size | `startTokens` in the chain state, set when a seeded session is first measured |
| seed | priority switch | the slot's `Status:` line |
| seed | seeded mark | set by the mod where it runs the seed command |
| guard | handoffs in a row | `unattended` in the chain state, reset by an owner prompt |

**Key invariants**: never clears without a slot written after the trigger; never gates during the rollover turn; never acts in `WF_RUN` or `TM_WORKER_NAME` sessions; never edits the vendored `/rollover` skill.

**Security model**: local only; the mod reads the session and writes the slot and its own state and log under `~/.claude`. No network.

**Configuration required**: `AUTO_HANDOFF_TOKENS`, `AUTO_HANDOFF_DISABLE` (both optional).

**Critical test scenarios**:
- Happy path: a scratch chat with `AUTO_HANDOFF_TOKENS` low crosses the line, the gate refuses a read, the rollover runs, facts and numbers are in the slot, the chat clears and resumes with nothing typed, verifies **AC-1** to **AC-6**.
- Loop: a seeded chat that starts near the line does not hand off before start + 40k; a third unattended handoff pauses, verifies **AC-1**, **AC-7**.
- Failure: the rollover writes no slot, nothing clears and the failure stays, verifies **AC-8**.
- Where: with `WF_RUN` set nothing happens, verifies **AC-11**.

## Build plan

1. Probes P1 to P8, results in verify notes, satisfies **AC-13** (all done 2026-10-18, see `0063-auto-handoff/verify.md`)
2. Line check, gate, chain state and log, satisfies **AC-1**, **AC-2**, **AC-12**
3. Rollover prompt with last request and sections template, satisfies **AC-3**, **AC-9**
4. Facts and numbers block from their `extractFacts` and `markUnverifiedFigures`, satisfies **AC-4**, **AC-5**
5. Clear, seed, priority switch, failure path, satisfies **AC-6**, **AC-8**
6. Loop guards, settings, env vars, where rule, satisfies **AC-7**, **AC-10**, **AC-11**
7. Tests (`claude plugin test`), NOTICE credit, scan, satisfies **AC-14**

## Consequences

**Positive**: chats hand off on time with nothing typed; the fresh chat gets facts it can trust.
**Negative / tradeoffs**: a turn past the line loses its remaining tool calls; we maintain adapted copies of their code; a handoff mid task costs one rollover turn of tokens.
**Neutral**: `/handoff` stays for manual use; spec 0057's start hook is unchanged.

## Follow-up

- [ ] Spec 0064: progress in the wf-dash band, viewer pages over Tailscale, handoff link.
