This is an automatic handoff: the chat reached its handoff line, so write the handover now and do not ask the owner anything. Do not tell the owner to type /clear; the wf-handoff mod clears and starts the fresh chat itself.
{{#transcript}}
This chat's transcript is {{transcript}}: name it as the previous transcript, do not search for the newest log.
{{/transcript}}

Step 1, the handover memory (spec 0069). What the fresh chat needs lives in the feature's index file, not in the handover.
1. Find the index: `python3 ~/claude-config/tools/scripts/handover-memory.py path --cwd <this chat's folder> --transcript <previous transcript>` prints its path.
2. Start ONE writer agent with the Agent tool (model sonnet, effort low). Its prompt is the "Writer prompt" block below, with the transcript path, the session id (the transcript's file name without `.jsonl`) and the index path filled in. It runs in the background: write no handover yet and wait for its result. The mod waits for it too.
3. When it returns, run `python3 ~/claude-config/tools/scripts/handover-memory.py check <index> --transcript <previous transcript>`, then `... prune <index>`.
4. If the writer failed, or `check` exits 1, put the line `memory not written: <reason>` in the handover and go on with step 2. The handoff never stops for it.

Step 2, the handover. It holds only these, nothing else; the contract's other sections are left out:
- the next actions;
- the last request, as below;
- the Open questions section, as below;
- the line `Handover memory: <index path>`, and under it every `dropped:` and `unlanded:` line `check` printed, word for word;
- `memory not written: <reason>` when step 1 failed.

## Last request from the owner
> {{lastRequest}}
Status: answered or not answered (pick one: "answered" only when your replies fully did what it asks)

## Open questions and loose ends
Anything noticed but not done, promised to the owner, or waiting on someone, with who it waits on, one line each. It stays beside the memory: start a line with the memory id (`- Q2: ...`) when the same question is a `Q` item there.

Never copy the owner's messages, your reasoning, tool output, or tried and failed notes into the handover. A lasting trap found in this chat goes into `AGENTS.md` or memory the normal way.

Never stop a background agent or task that is still running: the writer adds each one as an `L` item with its id, so the fresh chat picks up its result.

Leave out token counts and context sizes; the mod adds the real numbers itself.

Once the slot is written, end the turn with one short line: the chat is cleared a second later, and the fresh chat reads the handover, not a summary.

Writer prompt:
---
You write the handover memory of a chat that is being handed off. Transcript: <transcript>. Session id: <session id>. Index: <index path>. The script is `python3 ~/claude-config/tools/scripts/handover-memory.py`.
Read the chat only through `<script> messages <transcript>`: it prints the owner's messages and the text shown to the owner, nothing else. Read the index if it exists.
Keep four kinds of item, nothing else:
- Q: a question put to the owner, or a decision the owner still owes, with no answer later in the chat.
- S: something shown to the owner that they still need: a report, a list, a guide, a set of questions. Save it word for word in a file first (Write it to your scratchpad), then add it with `--move <file>`. A file the chat made under /tmp or a scratchpad that an S item needs goes in with `--move` too; several files make a folder.
- D: a decision, answer or preference the owner agreed.
- L: a helper agent or background task still running, with its id.
Never an owner message copy, reasoning, tool output, or tried and failed notes.
Add each new item, one call each: `<script> add <index> <Q|S|D|L> --text "<one plain sentence, at most 120 characters>" --who <owner|claude> --session <session id> --quote "<exact words from one message, at most 160 characters>"`. `--who owner` when the quote is from an owner message, `--who claude` when it is text shown to the owner. Copy the quote exactly as written there, typos included; never fix its spelling. A D item quotes the owner's own words that agreed it, even a short "yes, do that"; an S item and a question Claude asked quote Claude's text. The script gives the id; a quote that is not word for word in that message is dropped by the check afterwards. Put `--text` and `--quote` in single quotes, so the shell keeps backticks and `$` as they are; write a single quote inside as `'\''`.
Old items are matched by id only, and you never edit an existing quote; a restated item is a new item.
- A question answered in this chat: `<script> done <index> Q<n>`, and the answer becomes a new D item.
- A shown item no longer needed, or a helper that finished: `<script> done <index> <id>`.
- A decision the owner changed later: add the new D, then `<script> done <index> D<old> --detail "replaced by D<new>"`.
- A decision this chat wrote into a spec, `AGENTS.md` or the scope (an Edit or Write of that file in this chat): `<script> done <index> D<n> --detail "landed: <repo relative path>"`.
Reply with one line: the ids you added and marked done, or `memory not written: <reason>`.
---
