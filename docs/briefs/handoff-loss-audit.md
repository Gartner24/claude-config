# Handoff loss audit, 2026-10-22

11 auto handoffs plus 1 failed chain, 2026-10-21 to 2026-10-22, in claude-config and one work repo.
[M] measured from transcripts, slots or the log; [I] inference. Scripts were in the session scratchpad (temp).

## Totals [M]
- 21 of 24 owner messages were quoted verbatim in the slot.
- Of 758 facts (URLs, paths, code, bold text, ids, numbers in owner-facing messages of 500+ characters), 51% reached the slot and 20% were shown again in the new chat's first turn. Word-for-word match, so a lower bound.
- 0 of 11 new chats read the old chat's assistant text; 0 of 11 told the owner something was missing.
- 32 of 53 /tmp paths named in slots are gone now.
- 1 running helper agent was killed by a handoff and relaunched from zero.

## Loss categories, ranked
1. Reports and lists shrink to a summary and are not shown again (all 11). Example: the 62-row runner feature list became "11/11/4/36"; the slot even said "repeat only the short form if asked".
2. Open owner decisions hide behind one "last request". The ~/.config/wf, wf rules and auto skill choice was missing from the next first turn.
3. The gate (tool refusal at the handoff line) stops promised work halfway (a zip to the phone, a page save, a guide, a note to a helper) or leaves the owner's newest message unanswered (3 turns).
4. The owner cannot stop it: after "DO NOT ROLLOVER OR HANDOFF, PAUSE IT" it tried 4 more times.
5. False lessons travel down the chain: a slot said "every tool call is refused" at the line, so the next chat made no tool calls and the rollover failed twice.
6. Files live in per-session /tmp scratchpads and vanish.
7. A running agent is stopped by the rollover.
8. The facts block is wrong both ways: all 9 "[unverified]" marks were real facts; "Commits: none" after 3 amend commits; a test fixture link listed as a PR.

## Root causes
- `claude-home/mods/wf-handoff/templates/sections.md:5-24`: no section for things shown to the owner and still needed; no step to move scratchpad files.
- `sections.md:7-9`, `hooks/register.ts:238,314`: priority looks only at the latest owner message.
- `templates/instructions.md:2,8`: the new chat reads owner messages only, then goes on; nothing says to show pending items again or name what is missing.
- `register.ts:415-421` (tool deny) and `:436-439` (turn ended with an empty answer).
- `register.ts:340-341`: the off switch is read only at launch; the 2-in-a-row pause (`:182-187`) resets on every owner prompt (`:392,399`).
- Vendored jjstack rollover stops every background agent and asks for short handovers ("three to six sentences").
- `facts.ts:103` treats any line with "context" or "token" as a context figure; `facts.ts:34-38` misses `git commit -q` and takes links from any tool output.

## Fixes, ranked (owner decision pending)
1. `sections.md`: add "Shown to the owner, still needed": copy reports, lists, guides and pending questions word for word into `docs/briefs/<slug>.md` (or `~/.claude/state/auto-handoff/carry/<session>.md` with no repo) and name the file in the slot; move scratchpad files first; never "short form".
2. `instructions.md`: the first turn shows that section in full plus every open question, and says what could not be recovered; also read the old chat's assistant text for its last 10 turns.
3. Per-chat `/handoff off|on`, and honor the owner's "no handoff" (in progress with the handoff helper).
4. `register.ts:436-439`: never gate a turn that starts with a fresh owner message; hand off at turn end. At the gate allow a few more tool calls to finish a promised step; deny everything at line + 20k.
5. Before starting a handoff, wait (capped) while a background agent is running.
6. New rule `claude-home/rules/handover-carry.md`: save owner-facing deliverables to a lasting file when made; never claim tools or the handover are broken at the line.
7. `facts.ts`: mark only "N tokens"/"Nk" figures, skip quoted owner lines, read commits from `git log`.

Not checked: pairs before 2026-10-21, handoff speed (the handoff helper measures it), subagent transcripts.
