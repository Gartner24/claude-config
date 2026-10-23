This chat was started by an automatic handoff; the owner typed nothing. Resume the work from the handover. Trust its "Handoff facts" and "Handoff numbers" blocks: code wrote them. A figure marked [unverified: not in Handoff numbers] is a guess from the previous chat.
Before anything else, Read the whole slot file named on the "Slot:" line: the copy in your context can be cut short. Then read the index named on its `Handover memory:` line and nothing else: run `python3 ~/claude-config/tools/scripts/handover-memory.py ages <index>` and Read the index. Do not read the previous transcript. Open a detail file only when the next step needs it.
The handover's Open questions section and the memory's `Q` items are two lists of the same thing: an open question in either one is open. The "Open questions" block below holds both, each once.
Your first reply to the owner opens with what is still pending: every question in that block, every open Q item with its age, the title of every open S item, and every L item you will check (still running? then collect its result). Say plainly what could not be recovered: each `dropped:` or `unlanded:` line under `Handover memory:`, and a `memory not written: <reason>` line if the handover has one.
{{#priority}}
The owner's last request was not answered yet. Do it first, before anything else in the handover:
> {{lastRequest}}
{{/priority}}
{{^priority}}
The owner's last request was answered; go on with the handover's next actions.
{{/priority}}
