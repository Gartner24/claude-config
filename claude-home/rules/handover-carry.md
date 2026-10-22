# Handover carry (beats skill text)

Source: handoff-loss-audit.md, fix 6.

- Save every owner-facing deliverable (a report, a list, a guide, a pending question) to a lasting file the moment it is made.
- In a repo: `docs/briefs/<slug>.md`. Outside a repo: `~/.claude/state/<area>/`. Never `/tmp` and never a session scratchpad: those vanish with the session.
- Name the file in the handover so the next chat finds it.
- At the handoff line, never claim that tools or the handover are broken. If a step failed, say which step and why, and what was tried.
