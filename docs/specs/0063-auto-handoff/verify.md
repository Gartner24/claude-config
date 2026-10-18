# 0063 verify: probes run before the build (AC-13)

Run 2026-10-18 by a subagent of the conductor session, Claude Code 2.1.302, model haiku. Probe source: the throwaway `probe-0063` mod in a session scratchpad folder (never installed; `claude plugin validate` passed, one warning: no author). Session: `tmux new-session -d -s probe0063 -x 200 -y 50 -c <scratch>/probe-0063-cwd "claude --plugin-dir <scratch>/probe-0063 --model haiku"`, driven with `tmux send-keys` to the claude pane, every observation logged by the mod through `$.fs.write` to `<scratch>/probe-0063-out/log.txt`. Session killed after the run; the throwaway slot written for the scratch folder (P3) was retired with `jjstack-rollover-slot --cwd <scratch>/probe-0063-cwd consume`, and `status` then exits 1.

Verdict: P2, P4, P5 PASS. P1 and P3 FAIL as the spec words them; both pass with a different call, so AC-3 and AC-6 go back to `/architect`.

- [x] P1 a slash command from `turn.complete` runs as if typed. FAIL with `$.prompt.submit`, PASS with `$.command.run` (the spec now uses that).
  Command: `/probe-p1` arms it, then "Reply with the single word ok."; at that turn's `turn.complete` (no `agentId`) the mod calls `$.prompt.submit({ text: '/probe-0063:probe-skill hello-p1' })`.
  Result: the call is refused before any hook runs:
  `P1 submit rejected HooksError: probe-0063: prompt.submit: submits a prompt to the model; a text beginning with / would run a command as the user; run one with $.command.run({ command }) (host check)`.
  Same refusal with `asUser: true` (`/probe-p1 asuser`). Nothing reached the screen.
  Working alternative, same hook: `$.command.run({ command: 'probe-0063:probe-skill', args: 'hello-p1' })` called directly from `turn.complete` (no timer needed, unlike a call from inside a `command.run` hook in 0057 P2). Log: `command.run seen command=probe-0063:probe-skill args="hello-p1" origin=plugin:probe-0063`, then `prompt.submit origin=plugin:probe-0063 command={"name":"probe-0063:probe-skill","args":"hello-p1"}`, `P1 submit resolved {}`, a new turn, `turn.complete ... answer="PROBE-SKILL-RAN args=hello-p1"`. Screen showed `> /probe-0063:probe-skill hello-p1` then `PROBE-SKILL-RAN args=hello-p1`, as if typed.
  `/rollover` the same way (`/probe-p1r cmd`): `command.run seen command=rollover args="probe-0063 P1 check, do not act" origin=plugin:probe-0063`; the probe's own `command.run` hook answered it (`{"text":"probe-0063 stopped /rollover on purpose"}`) so the real skill never ran and no handover was written (`status` for the scratch folder exits 1). So `/rollover` resolves as a slash command from a plugin; the full skill run was not exercised, by design.
  can fail: the host refusing a plugin-run slash command, or the command resolving to nothing

- [x] P2 a refusing `tool.call` hook returns the refusal text to the model and the turn ends in words. PASS.
  Command: `/probe-gate` (gate on: every `tool.call` returns `{ deny: "context is at the handoff line; finish this turn in words, the handoff starts at the end of it" }`), then "Use the Bash tool to run: echo probe. If the tool call is refused, quote the exact refusal text you received in your reply and do not retry."
  Result: `tool.call DENIED tool=Bash`, one more model request (`turn.step index=1`), then `turn.complete reason=answer` with answer "The Bash call was refused, so I did not retry. The exact refusal text was: `<tool_use_error>context is at the handoff line; finish this turn in words, the handoff starts at the end of it</tool_use_error>`". The model gets the text wrapped in `<tool_use_error>`; it did not retry.
  can fail: the deny text not reaching the model, or the turn ending in an error instead of an answer

- [x] P3 a seed reaches the cleared session after a timer `/clear`. FAIL at `session.start` (it never fires), PASS after the awaited clear (the spec now uses that).
  Command: `/probe-p3` arms a module flag and runs `/clear` from `$.clock.after(1500, ...)`; the mod's `session.start` hook would submit the seed.
  Result: the clear ran (screen shows `> /clear`, context emptied) but no `session.start` fired: the log has `P3 timer fired, running /clear` and nothing more. The API types say so too: `session.start` fires "once per process ... then once per fresh load of one (never `/clear`)", and `session.end` with `reason: clear` notes "no `session.start` fires for it". A seed starting with `/resume-from-clear` would also be refused by `$.prompt.submit` (P1).
  Working alternative: await the clear in the same timer callback, then submit. `/probe-p3 after`: `session.end reason=clear sessionId=0e3c959f-...`, then `P3 clear resolved {"text":""} sessionId=8406ba3a-...` (a new id), then `$.prompt.submit` of a plain text seed resolved with `"origin":{"kind":"plugin","name":"probe-0063"}`. The seeded turn answered: "SessionStart first line: `SessionStart:clear hook success: wf morning report ...` Line with the secret word: `PROBE P3 MARKER: the secret word is heron-63.`", the marker that exists only in the slot loaded by the spec 0057 start hook (`handover-start.sh`, SessionStart `clear`). So the start hook text was in context before the seed. The same path with `$.command.run({ command: 'probe-0063:probe-skill', args: 'seeded-after-clear' })` (`/probe-p3 aftercmd`) ran the skill in the cleared session with `origin=plugin:probe-0063` and answered `PROBE-SKILL-RAN args=seeded-after-clear`: the carrier for a `/resume-from-clear` seed.
  can fail: the seed landing before the start hook text, or arriving with a composer origin

- [x] P4 `$.session.usage().context.tokens` is set inside `turn.step`. PASS, with a gap.
  Command: a `turn.step` hook (`async function*`) reads `$.session.usage()` before and after `yield* next(e)`.
  Result: set on every step except the first request of a fresh or just cleared session, where it is `undefined` before `next(e)`: `turn.step ... index=0 agent=- tokensBefore=undefined window=1000000` then `tokensAfter=87289`; later steps `tokensBefore=87289`, `88191`, and so on. After each `/clear`: `P3 clear resolved ... tokens=undefined`, seeded turn `index=0 tokensBefore=undefined`, `tokensAfter=58156`. `tokens` is the input of the last response, so AC-1's "starting size read at the first `turn.step` of the seeded turn" must be read after `next(e)` (or on step 1), never before. Subagent steps (`agentId`) were not exercised.
  can fail: `tokens` absent inside `turn.step` on every step

- [x] P5 `$.fs.write` to a path whose folders do not exist creates them. PASS.
  Command: `/probe-p5` writes `<scratch>/probe-0063-out/p5/deep/a/b/c/p5.txt`; `probe-0063-out` did not exist before the session (`ls` of the scratchpad showed no such folder).
  Result: `P5 wrote .../p5/deep/a/b/c/p5.txt, read back: "p5 ok\n"`; on disk `ls` shows `p5.txt`, 6 bytes, 15:49:24. The log file itself was first written into the missing `probe-0063-out` folder at session start.
  can fail: the write rejecting with no such directory

## Build rules from these probes
- A mod never submits slash text through `$.prompt.submit` (host check); slash commands go through `$.command.run({ command, args })`, which works straight from `turn.complete` and from a timer after a clear. AC-3 (`/rollover` + sections text) and AC-6 (`/resume-from-clear` + instructions text) need the args form; the args carry the template text.
- There is no `session.start` after `/clear`. The seed goes in the `$.clock.after` callback after `await $.command.run({ command: 'clear' })` resolves (or from `session.end` with `reason: clear`), and the 15 second "no session.start" failure path in AC-6 needs another trigger.
- The start size of a seeded chat is read after the first model response, not before it.
- Seen but not explained: the plain `$.prompt.submit` made from the timer after the clear never passed through the probe's own `prompt.submit` hook (no log line), though its result named `origin: plugin`; the `$.command.run` path did pass through it. A mod that marks a seeded session from its own `prompt.submit` hook should set the mark where it submits, not rely on seeing its own submit.

## Still to run (added by the amendment of 2026-10-18)
- [ ] P6 the real `/rollover` through `$.command.run({ command: 'rollover', args })` writes a slot newer than the call.
- [ ] P7 a `turn.step` hook ends the turn before the next model request; record how.
- [ ] P8 a `prompt.submit` hook refuses a composer prompt and the mod sends its text again afterwards.
