# Handoff "brain" research, 2026-10-22

Question: the owner rejected saving everything shown in a chat (eats context, carries bad prompts and mistakes) and asked for a real "brain", maybe from a RinDig repo. [R] read, [I] inferred.

## Verdict
No RinDig repo is a memory tool to install. Adopt the cost-of-remembering folder convention plus the agentless "session" route as a design. No daemon, no vector store (MemPalace trial already showed search stores get polluted; claude-mem removed).

## RinDig repos that touch the topic (57 public) [R]
- cost-of-remembering (38 stars, MIT per README): an agent files each conversation into a folder tree; a later agent walks it. Matched long-context accuracy on LongMemEval at 97% fewer read tokens; small sample (n=39), not tested over months. Its harness bash allowlist includes rm/sed/tee: do not run it.
- icm-architect (1969 stars, MIT, markdown only): six folder forms; "Record library" and "Knowledge bundle" fit. SKILL.md and core.md not yet read.
- agentless (3 stars, MIT, markdown only): `/agentless session` turns a chat into a folder: report, the person fixes it, each correction becomes a rule; leaves out secrets, private paths and raw transcript; "walk it cold" test with a fresh agent.
- Interpretable-Context-Methodology (1364 stars, MIT): the spec behind these (CONVENTIONS.md not read).
- Content-Agent-Routing-Promptbase (162 stars, no license): layered loading: root file ~800 tokens, routing table ~300, per-folder context 200-500, leaves 500-3000 loaded only when needed.

## Proposed handoff design [I]
1. Kept, four kinds only, as small separate files: open questions and owner decisions; deliverables shown to the owner and still needed (saved word for word when made); agreed decisions (the existing "Agreed so far" brief); live state (running agents, lasting file paths). Never kept: owner prompts, reasoning, tool output, claims like "tools are refused", anything unverified.
2. Who decides: a fresh writer subagent at handoff, given the last N assistant turns and all owner messages. Each item must quote its source turn or is dropped (filters false lessons). The owner's newest message wins; "forget X" / "keep X" in chat overrides the writer.
3. Where: in a repo `docs/briefs/<feature-slug>.md` as a router (under 60 lines, one line per item with status) plus `docs/briefs/<slug>/` leaves (`.workflow/briefs/` in bot-reviewed repos); no repo: `~/.claude/state/auto-handoff/carry/<project>/`. Never /tmp; scratchpad files are moved in at handoff.
4. Deleted: open items never auto-deleted, shown with their age; a resolved item moves to `_archive/` at the next handoff and is removed after 14 days (proposal, no source) or when the feature closes.
5. New chat loads only the router (~300-800 tokens): first turn shows open questions and titles of kept deliverables, says what could not be recovered, opens a leaf only when needed.

Test before building: replay the 11 audited handoffs (handoff-loss-audit.md) and count how many facts and lists come back.
