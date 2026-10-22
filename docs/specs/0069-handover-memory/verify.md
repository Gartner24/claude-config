# 0069 verify

## Probe before the build (build step 2): FAIL

Question: does a foreground writer agent, started inside a mod-started `/rollover` turn, finish before the slot check (decision 1, option A)?

Answer: no. In Claude Code 2.1.308 the Agent tool has no foreground mode: every call returns at once with `"status":"async_launched"` and the result text "Async agent launched successfully ... The agent is working in the background. You will be notified automatically when it completes." The rollover turn then ends while the writer still runs, the main `turn.complete` fires, and that is where `register.ts` `finishRollover()` checks the slot. The handover is written only in a later turn, after the agent's completion notice wakes the chat. With today's `finishRollover()` that is the failure "the rollover wrote no new handover; nothing was cleared".

Run 2026-10-22 (19:55 to 19:58 UTC) by a build subagent, Claude Code 2.1.308, model haiku.

Probe source: a throwaway `probe-0069` mod in `/tmp/probe-0069/mod` (never installed; `claude plugin validate` passed, one warning: no author). It registers `/probe-roll`. At the next main `turn.complete` it calls `$.command.run({ command: 'rollover', args })` the way `beginHandoff()` does. The args are: "Step 1: before anything else, start ONE writer agent with the Agent tool, in the foreground (do not set run_in_background), model haiku. Its only task: use the Write tool to write the file /tmp/probe-0069/cwd/writer.txt ... Wait for its result. Step 2: only after the agent returned, write a minimal handover." At the first main `turn.complete` after the command resolved, the mod does what `finishRollover()` does: it runs `jjstack-rollover-slot --cwd /tmp/probe-0069/cwd status --max-age-days 1`, stats the slot and `writer.txt`, and logs both mtimes. Every `tool.call` and `turn.complete` is logged with its `agentId`, through `$.fs.write`, to `/tmp/probe-0069/out/log.txt`.

Session: `tmux new-session -d -s p69b -x 200 -y 50 -c /tmp/probe-0069/cwd env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT -u CLAUDE_JOB_DIR -u CLAUDE_CODE_MESSAGING_SOCKET -u CLAUDE_CODE_MESSAGING_TOKEN -u CLAUDE_CODE_BRIDGE_SESSION_ID -u CLAUDE_CODE_EXECPATH -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_CHILD_SESSION -u CLAUDE_CODE_SESSION_ATTENDED -u CLAUDE_PID -u CLAUDE_EFFORT -u AI_AGENT -u AUTO_HANDOFF_TOKENS -u ENABLE_STOP_REVIEW AUTO_HANDOFF_DISABLE=1 claude --plugin-dir /tmp/probe-0069/mod --model haiku --permission-mode acceptEdits`, driven with `tmux send-keys`: `/probe-roll`, then "Reply with the single word ok." Every inherited `CLAUDE*` variable was unset. `AUTO_HANDOFF_DISABLE=1` kept the live wf-handoff mod out. The cwd is not a git repo.

Log of run 2 (clean env):
```
19:57:53.885Z turn.complete agent=-
19:57:53.890Z calling rollover at 1792699073888
19:57:54.043Z rollover resolved
19:57:56.492Z tool.call Agent agent=-
19:57:56.575Z tool.done Agent agent=-                  (83 ms: the launch, not the work)
19:57:59.145Z turn.complete agent=-                    (the rollover turn ended)
19:57:59.151Z SLOT CHECK ... slot=none slotMtime=none writerMtime=none
19:57:59.151Z RESULT writer before check: false; slot new: false
19:57:59.689Z tool.call Write agent=ac8ad64eb1cbc935f  (the writer starts its work after the check)
19:58:01.613Z turn.complete agent=ac8ad64eb1cbc935f
19:58:04.619Z tool.call Bash agent=-                   (a new main turn: the rollover goes on)
```
The tool_use input in the transcript was `{"description":"Write writer.txt file","model":"haiku","subagent_type":"general-purpose","prompt":"..."}`, with no background flag, and its tool_result had `"status":"async_launched"`. The screen showed "Agent(Write writer.txt file) / Backgrounded agent", then the model said: "The writer agent was launched in the foreground as you asked, but the harness started it as a background agent anyway. I'm holding off on the handover until it finishes", then "Waiting for 1 background agent to finish".

Run 1 (19:55 to 19:57, only `CLAUDECODE` and `CLAUDE_CODE_ENTRYPOINT` unset) gave the same result: `tool.done Agent` 57 ms after the call, `Backgrounded agent`. There the writer wrote at 19:56:32.5, and the main `turn.complete` plus the slot check followed at 19:56:33.7, which found `slot=none`. The handover was written later, in the turn after the completion notice: "Handover written to /home/santiago/.claude/projects/-tmp-probe-0069-cwd/rollover/session.md".

Cleanup: run 1's slot was retired with `jjstack-rollover-slot --cwd /tmp/probe-0069/cwd consume`. Run 2 was killed before it wrote its slot. `status --max-age-days 1` then exits 1. Both tmux sessions were killed.

Effect on the build: build step 2 says a FAIL goes back to `/architect`, so the build stopped there. The owner then picked option A with a wait (spec amended, run 3 below). The facts given to `/architect` at that point:
- In both runs the chat's next turn woke after the agent's completion notice and finished the rollover. A mod that waits for this chat's agents (`agentsRunning()`, already used by `startHandoff()`) and then for the next main `turn.complete` before it checks the slot would see the slot. That changes `register.ts`, which the spec's option A said it would not touch.
- Option B (the mod runs the writer itself with `claude -p` through `$.process.run` after the slot is written) does not depend on the Agent tool. It was not probed.
- A typed `/rollover` (AC-3's rule path) has the same async agent. The vendored rollover then ends its turn before the writer is done, so its own handover may be written before the writer's index is.

## Probe run 3, with the wait (after the owner's decision): PASS

The owner picked option A with a wait (spec amended 2026-10-22: the mod waits for running agents, then checks the slot). Run 2026-10-22 20:03 to 20:08 UTC, same session command (tmux session `p69c`, every `CLAUDE*` variable unset, haiku, `acceptEdits`). The probe mod now does what `register.ts` does after the change:
- a main `Agent` tool call during the rollover sets `writerLaunched`;
- a main turn that begins while no agent runs, after a writer was launched, sets `afterAgents`;
- at a main `turn.complete` it waits when `agentsRunning()` is above 0, or when the slot is not new and a writer was launched but no turn has begun since every agent finished; otherwise it checks the slot.

The args no longer say "foreground". The log:
```
20:04:09.433Z calling rollover at 1792699449431
20:04:09.613Z main turn begins 0c3339c1-... afterAgents=false
20:04:11.778Z tool.call Agent agent=-
20:04:11.854Z tool.done Agent agent=-
20:04:13.422Z turn.complete agent=-
20:04:13.429Z WAIT busy=1 slotNew=false writerLaunched=true afterAgents=false
20:04:14.405Z tool.call Write agent=a07c653a437af6c96
20:04:15.983Z turn.complete agent=a07c653a437af6c96
20:04:16.096Z main turn begins 41d0e0b4-... afterAgents=true
20:07:27.365Z tool.call Bash agent=-      (the gap is the probe's permission prompts, answered by hand)
20:07:56.758Z tool.call Write agent=-     (the handover body)
20:08:14.087Z turn.complete agent=-
20:08:14.106Z SLOT CHECK now=1792699694099 call=1792699449431 slot=/home/santiago/.claude/projects/-tmp-probe-0069-cwd/rollover/session.md slotMtime=1792699679422.9634 writerMtime=1792699454425.659
20:08:14.107Z RESULT writer before check: true; slot new: true; writer before slot: true
```
The slot was found at the first `turn.complete` after the wait, it was newer than the call, and the writer's file was older than the slot. Three read-only Bash commands of the rollover skill (`cat .../rollover-handover.md`, `jjstack-background-tasks`, `printenv TM_WORKER_NAME`) asked for approval in this scratch session and were answered "Yes" by hand. A live chat runs in auto mode, which handles these. Cleanup: `jjstack-rollover-slot --cwd /tmp/probe-0069/cwd consume` printed the slot path, and the tmux session was killed.

## Replay of the 11 audited handoffs (AC-12): FAIL, the build stops here

Run 2026-10-22, 20:30 to 21:00 UTC. The 11 pairs are the ones in the audit agent's own report (in the transcript of the chat that wrote handoff-loss-audit.md): six claude-config chats (9d4a5ed9, 6c177ef1, ec0227ec, f8ae08e1, ac6d92e1, 36d35b86) and five work repo chats (49de1c16, d3f2d148, 2c3937a6, 66ba8d70, 84e6eace). "Today's slot" is the consumed slot that names each old transcript, under `~/.claude/projects/<folder>/rollover/session.consumed-*.md`.

How it ran:
- one writer agent per old transcript (sonnet, effort low, the spec's writer). Each got the "Writer prompt" block of `templates/sections.md` word for word, the old transcript, its session id, and an index in `/tmp/replay-0069/run2/<s8>/index.md`. Each started from an empty index;
- then `handover-memory.py check <index> --transcript <old transcript>` and `prune <index>` on each index.
- The indexes and detail files stay in `/tmp`. They hold client text and are never committed. This file names counts and kinds only.

Run 1 used the first writer prompt. Its check dropped 4 items, among them 36d35b86 Q2: the ~/.config/wf, wf rules and auto skill choice, the very decision the audit found missing. The causes were writer slips, not made-up items:
- a quote passed to the shell unquoted, whose backticks zsh ran;
- a quote with the owner's typo "fixed";
- a D item that quoted Claude's text as the owner's.

The prompt then got three lines: single quotes for `--text` and `--quote`, quotes copied typos included, and a D item quotes the owner's own words. Run 2 used that prompt; its check dropped nothing.

Run 2, open items per index after check and prune, against the slot:

| Handoff | Q | S | D | L | index chars | slot "Open questions" bullets | slot "Agreed" bullets |
|---|---|---|---|---|---|---|---|
| 9d4a5ed9 | 2 | 1 | 0 | 0 | 939 | 6 | 6 |
| 6c177ef1 | 2 | 1 | 1 | 0 | 892 | 4 | 5 |
| ec0227ec | 1 | 1 | 1 | 0 | 779 | 4 | 7 |
| f8ae08e1 | 1 | 1 | 0 | 0 | 617 | 3 | 8 |
| ac6d92e1 | 3 | 1 | 0 | 0 | 951 | 3 | 6 |
| 36d35b86 | 3 | 1 | 4 | 0 | 1949 | 6 | 8 |
| 49de1c16 | 2 | 3 | 3 | 0 | 1609 | 8 | 10 |
| d3f2d148 | 3 | 1 | 2 | 0 | 1606 | 9 | 11 |
| 2c3937a6 | 3 | 2 | 1 | 0 | 1325 | 5 | 4 |
| 66ba8d70 | 2 | 1 | 0 | 0 | 775 | 5 | 6 |
| 84e6eace | 4 | 1 | 0 | 0 | 1180 | 5 | 7 |

The slot counts are much higher, but most of those bullets were carried from chats before the replayed window, or are tasks and notes, not owner decisions. Each slot bullet is one line that often bundles several items. So each open owner decision in a slot's "Open questions" section was traced by hand to the chat's own text (`handover-memory.py messages`). Each one raised in that chat was checked against the open Q items and S detail files of the indexes of the same chain up to that chat (the cc chain, and the work repo chain).

What the replay kept that the slots did not:
- S, shown and still needed (AC-19): 14 detail files. The slots kept none of them word for word. These include the 62 row runner feature list (36d35b86 S1, the audit's lead example) and two work repo deliverables the audit names as lost (2c3937a6 S2, 49de1c16 S2). One shown work repo deliverable was not kept; the owner had already finished with it in the chat.
- 36d35b86 Q2, the three small choices the audit found missing from the next first turn, is kept.

Open owner decisions per handoff:
- Nine handoffs: the chain's indexes hold every open owner decision the chat raised that the slot kept. The cross-repo wf questions sit in the work repo chain (66ba8d70 Q1 and S1).
- 49de1c16 (LOSS): the slot kept two open owner questions the replay index lacks. One is the runner questions waiting on the owner, which come back in the next chat's index (d3f2d148 Q1). The other, a work repo confirmation, does not come back. The replay kept the other two open owner questions the slot kept. It also missed one owner choice that the slot missed too (run 1 had it as Q2).
- d3f2d148 (LOSS): the slot kept one open owner question, a work repo status question, that the replay index has no item for. Its writer left out questions it judged answered later, but this one was not answered.

AC-12: "A replay that keeps fewer open decisions than today's slots stops the build and goes back to `/architect`." In two of eleven handoffs it kept fewer, so the build stops here. The misses are the writer's recall, not the check. The check dropped nothing in run 2, and every miss is a question the chat asked in its own text. A third replay run on the same prompt was not tried (two runs; rules/stop-and-reset.md).

## Replay run 3, slot plus memory (after the owner's decision): PASS

The owner decided on the replay loss, and decision 5 was amended 2026-10-22: the slot keeps its Open questions section beside the memory. The fresh chat gets both lists, and AC-12 counts open questions from the two together.

Run 2026-10-22 (about 21:20 UTC): 11 writer agents again (sonnet, effort low, the same writer prompt). The run 2 indexes were deleted with the `/tmp` scratch, so the transcripts were read again from their original paths. The new indexes were written under the job folder `~/.claude/jobs/fd2083a4/tmp/replay-0069/run3/`, outside the repo; it goes away with the job. Then `check` and `prune` ran on each index. The slot side is today's "Open questions" section: the template keeps writing it as before, so the old consumed slots stand for it.

| Handoff | dropped | Q | S | D | L | slot open bullets | memory + slot | kept at least the slot |
|---|---|---|---|---|---|---|---|---|
| 9d4a5ed9 | 0 | 1 | 1 | 0 | 0 | 6 | 7 | yes |
| 6c177ef1 | 0 | 2 | 1 | 2 | 0 | 4 | 6 | yes |
| ec0227ec | 0 | 1 | 0 | 0 | 0 | 4 | 5 | yes |
| f8ae08e1 | 0 | 1 | 1 | 0 | 0 | 3 | 4 | yes |
| ac6d92e1 | 0 | 4 | 1 | 0 | 0 | 3 | 7 | yes |
| 36d35b86 | 0 | 3 | 1 | 4 | 0 | 6 | 9 | yes |
| 49de1c16 | 0 | 2 | 2 | 3 | 0 | 8 | 10 | yes |
| d3f2d148 | 0 | 2 | 1 | 2 | 0 | 9 | 11 | yes |
| 2c3937a6 | 0 | 2 | 2 | 1 | 0 | 5 | 7 | yes |
| 66ba8d70 | 0 | 3 | 0 | 1 | 0 | 5 | 8 | yes |
| 84e6eace | 0 | 4 | 1 | 0 | 0 | 5 | 9 | yes |

What the table shows:
- Counted together, every handoff keeps at least what its slot kept, by construction: the slot's list is part of the count.
- The two run 2 losses are in their slots' sections, so the fresh chat gets them: two open questions in 49de1c16 and one in d3f2d148.
- The memory side adds questions the slot section lacked. For example, 36d35b86 keeps the ~/.config/wf choices as their own Q item. It also adds the S detail files: 12 in run 3, against none word for word in the slots.

Two notes on the counts:
- The memory+slot column can count one question twice, because the old slots name no memory ids. A live slot names them (`- Q2: ...`, template), and the mod then lists such a question once (the "listed once" test).
- Writer recall varies run to run (the S count was 14 in run 2 and 12 in run 3). The slot section is what makes the count hold.

AC-12 (amended rule): PASS.

## Acceptance criteria

Everything below is on the branch and tested. The replay passes under the amended decision 5.

- [x] AC-1 four kinds only. `templates/sections.md` has no "What the owner said" or "Tried and failed" section. The slot holds next actions, the last request, the `Handover memory:` line and the failure line, and the writer prompt keeps Q, S, D, L only. Test `tests/test_handover_memory.py` `test_sections_keep_four_kinds_and_no_owner_copy`. can fail: the owner message section put back into sections.md (mutant "owner message copy back": red).
- [x] AC-2 quote or drop. `scripts/handover-memory.py` `cmd_check` (line 277) drops an item of this session whose quote is not in the right speaker's messages, after `norm` (line 58). Checks "AC-2 a made up quote is dropped", "a real quote is kept, whitespace and a pipe collapsed", and exit 1 naming the line. can fail: the quote match turned off (mutant "quote ignored": red).
- [x] AC-3 writer at handoff. `templates/sections.md` step 1 and the writer prompt; `rules/handover-carry.md` for a typed `/rollover`; `register.ts` `rollTurnDone` (line 366) waits for running agents, and for a main turn begun after they finished (line 661), capped at `AGENT_WAIT_MS` (15 min), then checks once and fails with the existing line. Probe run 3 PASS. Mod tests "spec 0069 AC-3" (5 tests). can fail: the slot checked while the writer runs (mutants "no agent wait", "no wait for a later turn", "afterAgents never set", "writer not seen", "no cap", "cap fails without a slot check": all red). The writer's recall gaps are covered by the slot's Open questions section (decision 5 amended; replay run 3).
- [x] AC-4 no /tmp. `cmd_add --move` (line 223) moves the file into the detail folder; `rules/handover-carry.md` says to save a deliverable as an S item when it is shown. Check "AC-4 AC-19 one file moves in as S1 with its extension". can fail: the file left in /tmp (mutant "extension dropped": red; the check also asserts the source is gone).
- [x] AC-5 the new chat reads only the index. `templates/instructions.md`: the jq read is gone; it reads the index and runs `ages`; the first reply lists Q with ages, S titles, L, and the `dropped:`, `unlanded:` and `memory not written:` lines. Test `test_instructions_read_only_the_index`. can fail: the jq read back (mutant "jq read back": red), Q ages left out (mutant "no Q ages": red).
  Amended 2026-10-22, decision 5: the slot keeps its Open questions section. `templates/sections.md` writes it, and its lines start with the memory id when the same question is a Q item. `register.ts` `openQuestions` joins the slot section and the index's open Q items, each once, and `seed()` reads the index named on the slot's `Handover memory:` line and adds the joined list to the fresh chat's start text. `instructions.md` says an open question in either list is open. Mod tests "spec 0069 amended" (3) and `test_slot_keeps_open_questions`. can fail:
  - a slot-only question not listed (mutants "slot list ignored", "block not sent": red);
  - a memory-only question not listed (mutants "memory ignored", "index not read": red);
  - a question in both listed twice (mutant "no dedupe": red);
  - a done Q listed (mutant: red);
  - the section dropped from the template (mutant: red).
- [x] AC-6 status, age, archive. `cmd_prune` (line 308). Checks "a 15 day old done line is deleted", "a 13 day old done line is kept", "an open item of any age stays", "a done item moves to the archive with its done date". can fail: 15 days kept (mutant "archive keeps 15 days": red), 13 days deleted (red), open items moved (red).
- [x] AC-7 ages. `cmd_ages` (line 333), check "AC-7 ages" (`Q1 open 294d very old question`). can fail: an age off by one (mutant: red).
- [x] AC-8 close. `cmd_close` (line 347) exits 1 naming each open item and each D without an existing `landed:` path. A D `replaced by D<n>` whose D<n> exists passes; the spec does not say this, so it is flagged for `/architect`. `rules/check-gates.md` gate 5. Checks "AC-8 ...": four of them. can fail: open items ignored (mutant: red), a missing landed path accepted (mutant: red).
- [x] AC-9 brief links. `cmd_lint` (line 370), gate 5 copies the warnings under "Briefs to tidy". Check "AC-9 AC-21 both warnings, general.md and a closed brief exempt". can fail: a broken link not printed (mutant "broken link silent": red), general.md warned (red), a `@ sha` link warned (red).
- [x] AC-10 one brief per feature. `claude-home/CLAUDE.md` `### Context`, the line after the brief rule. No test: rule text. can fail: not checked by code.
- [x] AC-11 tests. `handover-memory.py --test` covers AC-2, AC-6, AC-8 and AC-9; `tests/test_handover_memory.py` runs it in the suite. The mod tests have the AC-3 and AC-22 cases, and the template tests cover the owner message removal. Mutants: 33 of 33 script, 18 of 18 mod, 5 of 5 template, all red. The PR #174 review fixes are included: a `.workflow/` landed path (mutant: the old `lstrip("./")`, red); an index path in backticks, and numbered or indented slot questions (3 mutants, red). can fail: see each line.
- [x] AC-12 replay: run 2 FAIL under the first rule; run 3 PASS under the amended rule (memory plus slot), see above. can fail: a handoff whose memory plus slot count is below its slot count (the count script prints `kept >= slot` False).
- [x] AC-13 landed mark automatic. `rules/handover-carry.md`; the writer prompt's `landed:` rule; `messages` lists the files the chat edited (line 193). Checks "AC-13 AC-18 a landed mark on an edited file stays" and "AC-13 messages lists the files this chat edited". can fail: edits not listed (mutant: red).
- [x] AC-14 which feature. `cmd_path` (line 408): branch row first, else the row of the spec edited last, else general.md, and no repo means `~/.claude/state/handover/<project>/index.md`. Checks "AC-14 ..." (4). can fail: branch ignored, edited spec ignored, no repo path wrong (mutants: red).
- [x] AC-15 which session. `cmd_check` checks only `s8 == sid[:8]`; the mod passes `transcriptOf` into the template (unchanged), and handover-carry.md covers a typed `/rollover`. Check "AC-15 an older session's item is left alone". can fail: other sessions checked (mutant: red).
- [x] AC-16 what a message is. `owner_text` (line 142): no isMeta, no tool_result, no system-reminder, no text starting with a tag; claude text is assistant text blocks only. `messages` prints the same filter for the writer. Checks "AC-16 ..." (6). can fail: each of isMeta, reminder, tool_result, tag, claude-as-owner (mutants: red).
- [x] AC-17 ids. `next_id` (line 216): the highest number over index plus archive, plus one; the writer prompt matches old items by id only. Check "AC-17 the next D id counts the archive". can fail: the archive ignored (mutant: red).
- [x] AC-18 landed path real. `cmd_check` removes a `landed:` mark whose path is not an Edit or Write target and prints `unlanded:`. Check "AC-18 a landed mark on a file never edited is removed". can fail: the mark kept (mutant "unlanded kept": red).
- [x] AC-19 detail files. `cmd_add --move`: one file `S1.<ext>`, several make `S2/`. Replay: 14 S items, none of the audit's lost deliverables missed. Checks "AC-4 AC-19 ..." and "AC-19 several files go in a folder S2/". can fail: no folder (mutant: red).
- [x] AC-20 pipe and size. `norm` turns `|` into `/` and `"` into `'`; `size_warning` (line 296) over 2000 characters names the longest lines and the oldest open items, and archives nothing. Checks "AC-20 a pipe and a double quote are replaced" and "AC-20 over 2000 characters it warns with the oldest". can fail: a pipe kept (mutant: red), the warning gone (mutant: red).
- [x] AC-21 /sync order. Gate 5 says prune then close, then `git rm` and `Source:` set to `<path> @ <short sha>`; lint skips a `@ sha` link and general.md. Check: the AC-9 one. can fail: a closed brief warned (mutant: red).
- [x] AC-22 writer failure. `register.ts` line 413: a handover that names no index gets the `memory not written:` line and the handoff goes on. The template has the rollover write the line itself, and instructions.md makes the fresh chat say it. Mod tests "spec 0069 AC-22" (3). can fail: the line not added (mutant "no memory line": red), always added (mutant: red).

Results: `claude plugin test claude-home/mods/wf-handoff` 150 pass, 0 fail. `claude plugin validate` passed with warnings (no author, no icon; both were there before). `python3 tests/fast.py` ran 149 tests, 0 failed (on origin/main ec4718c). `handover-memory.py --test`: all passed.
CAN FAIL CHECKED: 21
MUTATION CHECKED: 56
