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
Run 2026-10-18 (23:00-23:02 UTC) by a subagent, Claude Code 2.1.303, model haiku. Probe source: throwaway `probe-0063b` mod in the session scratchpad (never installed; `claude plugin validate` passed, one warning: no author). Session: `tmux new-session -d -s probe0063b -x 200 -y 50 -c <scratch>/probe-0063b-cwd "claude --plugin-dir <scratch>/probe-0063b --model haiku"`, driven with `tmux send-keys`; log through `$.fs.write` to `<scratch>/probe-0063b-out/log.txt`. Session killed after the run.

- [x] P6 the real `/rollover` through `$.command.run({ command: 'rollover', args })` writes a slot newer than the call. PASS.
  Command: `/probe-p6` arms it, then "Reply with the single word ok."; at that turn's `turn.complete` (no `agentId`) the mod calls `$.command.run({ command: 'rollover', args: 'probe P6: write a minimal handover for this scratch chat; there is no real work' })`. No `command.run` or `prompt.submit` hook intercepted it (the probe's hooks only logged and called `next`).
  Log: `P6 calling rollover at ms=1792364454381`, `command.run seen command=rollover args="probe P6: ..." origin=plugin:probe-0063b`, `prompt.submit origin=plugin:probe-0063b text="/rollover probe P6: ..."`, `P6 rollover resolved {} ms=1792364454546` (resolves at once, in 165 ms, when the turn starts, not when the rollover ends), then a new turn of 7 steps (reading the rollover references, running `jjstack-rollover-slot`), `turn.complete reason=answer answer="Handover written to ~/.claude/projects/-tmp-...-probe-0063b-cwd/rollover/session.md - type /clear, then /resume-from-clear."` at 23:01:15.6Z, 21 s after the call.
  Check: `jjstack-rollover-slot --cwd <scratch>/probe-0063b-cwd status --max-age-days 1` printed `/home/santiago/.claude/projects/-tmp-claude-1000--home-santiago--claude-7692240f-4247-4b06-ac42-86d1193f0505-scratchpad-probe-0063b-cwd/rollover/session.md`; its mtime is 1792364470.659 (23:01:10.659Z), later than the call time 1792364454.381 (16 s later).
  Behaviour: no question asked, no push or merge. The scratch cwd is not a git repo and got no file; the only write is the slot under `~/.claude/projects/<mangled cwd>/rollover/`. The slot text: header "Rollover handover - plain session", `Previous transcript:` the probe session's jsonl, `QM resume order: none`, `Reload these skills: none`, next actions "None". The skill ends its answer with "type /clear, then /resume-from-clear". It also left the text `/clear` in the composer box (not submitted; cleared with ctrl+u).
  Retired: `jjstack-rollover-slot --cwd <scratch>/probe-0063b-cwd consume` printed the slot path, and `status --max-age-days 1` then exits 1.
  Build note: the `$.command.run` promise resolves at turn start, so the mod must wait for the rollover's own `turn.complete` (the next one without `agentId`) before it sends `/clear`, and read the slot with `status` before clearing.
  can fail: no slot, or a slot older than the call (a rollover that never ran, or one stopped by a hook)

- [x] P7 a `turn.step` hook ends the turn before the next model request; record how. PASS.
  Command: `/probe-p7 nonext` arms it, then "Use Bash to run echo a, then echo b, then echo c, one call each". The hook (an `async function*`, main loop only) passes steps with `yield* next(e)` until `e.index >= 1`, then answers without calling `next`: `return { turnId: e.turnId, index: e.index, answer: 'P7-STOPPED', toolUses: [], stopReason: 'end_turn', usage: null }`. The API types say "An answer without `next` sends no request".
  Log: `turn.step ... index=0`, `turn.step done index=0 stop=tool_use tools=1`, `turn.step ... index=1`, `P7 ending turn at index=1 by mode=nonext`, `turn.complete reason=answer agent=- answer=""`. No further `turn.step` line and no new `prompt.submit`. Screen: "Ran 1 shell command", "Churned for 2s", no error line; only `echo a` ran (b and c never did).
  Mechanism: return a `TurnStepResult` with empty `toolUses` and `stopReason: 'end_turn'` without calling `next(e)`. The turn ends as `turn.complete reason=answer` with an empty answer (the hook's `answer` text did not show on screen or in `turn.complete`). The `throw` and plain-`return` variants were left unrun, since this one works. The tool call of the step before it had already run, so end the turn on the first step after the tool results, as here.
  can fail: a further model request after the hook, or an error shown for the turn

- [x] P8 a `prompt.submit` hook refuses a composer prompt and the mod sends its text again afterwards. PASS.
  Command: `/probe-p8` arms it, then the composer prompt "What is 17 plus 25? Reply with just the number." The hook, for `origin.kind === 'composer'` and text not starting with `/`: keeps `e.text`, starts `$.clock.after(2000, ...)`, and returns `{ drop: 'probe-0063b: held, will be sent again in 2 s' }` (the documented refusal; the reason is shown to the person). The timer calls `$.prompt.submit({ text })`.
  Log: `prompt.submit origin=composer text="What is 17 plus 25? ..."`, `P8 refusing composer prompt, holding text=...`, no `turn.step` for 2 s, `P8 timer fired, resending via $.prompt.submit`, `P8 resend resolved {"text":"What is 17 plus 25? Reply with just the number.","origin":{"kind":"plugin","name":"probe-0063b"}}`, then `turn.step index=0`, `turn.complete reason=answer answer="42"`.
  Screen: "Prompt dropped by a hook: probe-0063b: held, will be sent again in 2 s", then a block "Prompt from the probe-0063b plugin ... This is how Claude Code surfaces a prompt a plugin submits between turns", then the answer `42`.
  Origin of the resent prompt: `{ kind: 'plugin', name: 'probe-0063b' }`, not composer. It did not pass through the mod's own `prompt.submit` hook (no log line), as seen in 0057 and P3. Side effect: after the drop the host puts the typed text back in the composer box and it stays there after the resend (a second Enter would send it again), so the mod should not rely on the box being empty.
  can fail: the typed prompt reaching the model before the resend, or the resend never arriving

## /check verify of the build (2026-10-18, under wf run): FAIL

How it ran: a real Claude chat cannot start here (the sandbox has no login: `claude auth status` says `"loggedIn": false`), so the mod ran inside Claude Code's own mod engine with the host faked in memory: `claude plugin test` on a scratch copy of `claude-home/mods/wf-handoff/`, with the shipped tests plus the checks in [verify-checks.test.ts.txt](verify-checks.test.ts.txt) (rename to `.ts` and drop into the mod's `tests/` to rerun). `claude plugin validate claude-home/mods/wf-handoff` passed (one warning: no author). Each passing check was run once more against a broken copy of the code and went red (mutant named per line); the scratch copy was then diffed back to the repo, identical.

Commands
- [x] `claude plugin test claude-home/mods/wf-handoff`: 14 pass, 0 fail (the shipped tests) -> AC-1 to AC-12
- [x] V1 subagent events (`agentId`) never gate, end a turn or hand off -> AC-1, AC-11. can fail: the `agentId` skip dropped from `tool.call` (went red)
- [x] V3, V3b facts block under 2,000 bytes -> AC-4. Fixed in 1c47781, PASS on the rerun below. Was **FAIL**: 2,065 bytes with 200 edited files, 2,075 with long files, commits and links lists. `factsBlock` in `facts.ts` budgets only the heading, viewer and numbers plus 120 bytes of slack (`fixed`, facts.ts line 53), but the block also holds the provenance line (about 110 bytes), three list titles, `- none` and `- +N more` lines and blank lines. Fix: count every fixed line of the block in `fixed` (or measure the joined block and drop list lines until it fits), in bytes, not UTF-16 length.
- [x] V2 `ignoreFiles` globs leave matching paths out; `NotebookEdit` paths kept -> AC-4. can fail: the ignore filter removed (went red)
- [x] V15 a chain `link` adds exactly one `viewer:` line -> AC-4 (the link itself is spec 0064 AC-6). can fail: the viewer line dropped (went red)
- [x] V4 unverified marks only on context or token lines: `12%` and `1,234,567 tokens` marked and logged; a code span, a file name `run-200k.txt`, a line with no context word, and a known figure (60k = tokens at handoff) left alone -> AC-5. can fail: the file name guard removed (went red)
- [x] V17 the last request is quoted as typed -> AC-3, AC-6. Fixed in 1c47781, PASS on the rerun below. Was **FAIL**: typed `use $& and $' in the regex` reached `/rollover` as `use {{lastRequest}} and  GO-ON in the regex GO-ON`. `fillTemplate` (facts.ts line 123) passes the owner's text as a `String.replace` replacement string, so `$&`, `$'`, `` $` `` and `$$` are expanded. Same for the held prompt in the seed. Fix: `.replace(/\{\{lastRequest\}\}/g, () => vars.lastRequest)`.
- [x] V5 an owner's own `/clear` starts a new chain: no seed, guard count back to 0 -> AC-6, AC-7. can fail: the chain reset in `session.end` removed (went red)
- [x] V6 a clear that rejects: phase failed, no seed, text says the chat may still have cleared -> AC-6, AC-8. can fail: only a timeout treated as failure (went red)
- [x] V7 a seed that rejects: phase failed, text says type /resume-from-clear, counted once, gate open -> AC-7, AC-8. can fail: the seed failure swallowed (went red)
- [x] V8 held slash text resent through `$.command.run` (`scope`, `add a thing`), plain text through `$.prompt.submit` -> AC-6. can fail: slash text not routed to command.run (went red)
- [x] V9 `Status: answered` under the last request section seeds the not priority branch, even with a later `Status: not answered` in another section -> AC-6, AC-9. can fail: priority always on (went red)
- [x] V10 the `sectionsTemplate` setting (`~/my/sections.md`) is the text handed to `/rollover` -> AC-9, AC-10. can fail: the setting ignored (went red)
- [x] V11a a gated turn with no `turn.complete` (Esc) hands off at the next `turn.step`, which ends at once -> AC-2. can fail: the fallback removed (went red)
- [x] V11b the same, the next owner prompt starts the handoff, is held, and becomes the last request -> AC-2, AC-3. can fail: the prompt fallback removed (went red)
- [x] V12 with no settings the line is 200,000 (199k runs, 201k refused) -> AC-1, AC-10. can fail: the `plugin.json` default changed to 300000 (went red; the code fallback in register.ts is never used, the engine fills defaults from `userConfig`)
- [x] V13 with no settings the third unattended crossing pauses, logged with the session id -> AC-7, AC-12. can fail: the `plugin.json` default changed to 3 (went red)
- [x] V14 a refused call hands off even when the size later reads under the line -> AC-2. can fail: both gated checks removed (went red; either one alone keeps it working)
- [x] V16 trigger, refusal, rollover start, slot found and failure each log one line with the session id -> AC-12. can fail: the session id left out of the log line (went red)

Not exercisable here
- The live run (a real chat crosses the line, rolls over, clears and resumes with nothing typed; the `/config` rows show) needs a real logged in interactive Claude: left to the box: Install the mod live after its scan.
- AC-13: probes P1 to P8, recorded above. AC-14: `docs/NOTICE.md` names claude-auto-handoff 0.8.6 with its MIT license; the scan is the same later box. Note for review: NOTICE says the code was written fresh from their design (the upstream source was not fetched), while AC-4 says "code reused from their `brief.ts`"; behavior is what AC-4 asks, provenance differs.

## /check verify rerun after the fix (2026-10-18, under wf run): PASS

Same method as above, on commit 1c47781 (the fix changed only `facts.ts`; `hooks/register.ts` is the code the earlier mutants ran on). Scratch copy of the mod plus the checks file, which now also holds V3c. `claude plugin test`: 34 pass, 0 fail. `claude plugin validate`: passed, one warning (no author). Scratch copy diffed back to the repo after the mutants: identical. Full suite `python3 runner/tests/fast.py`: 1042 tests, 0 failed.

- [x] V3 facts block 1,991 bytes, V3b 1,964 bytes, both under 2,000, `+N more` present, next actions kept -> AC-4. can fail: the old guessed 120 bytes of slack in place of the measured frame (went red: 2,065 and 2,075, the numbers of the first run)
- [x] V3c 200 paths with accented and Japanese letters, plus a viewer line: 1,996 UTF-8 bytes -> AC-4. can fail: measuring with string length instead of UTF-8 bytes (went red: 2,794 bytes)
- [x] V17 `use $& and $' in the regex` reaches `/rollover` exactly as typed -> AC-3, AC-6. can fail: the string replacement brought back in `fillTemplate` (went red: `use {{lastRequest}} and  GO-ON in the regex GO-ON`)
- [x] V1, V2, V4 to V16 and the 14 shipped tests still pass on the fixed code.

Left to the box: Install the mod live after its scan (the live run in a real logged in chat, the `/config` rows, and the scan of AC-14).
