# Handover carry (beats skill text)

Source: handoff-loss-audit.md, fix 6; spec 0069 (handover memory). The script is
`python3 ~/claude-config/scripts/handover-memory.py`; `<script> path` prints this chat's index (the
feature's brief, `docs/briefs/general.md` with no feature, `~/.claude/state/handover/<project>/index.md`
outside a repo).

- Save every owner-facing deliverable (a report, a list, a guide, a pending question) the moment it
  is shown, as an `S` item of the index: write it word for word to a file, then
  `<script> add <index> S --text ... --who claude --session <id> --quote ... --move <file>`. Never leave
  it in `/tmp` or a session scratchpad: those vanish with the session.
- Whatever writes a `D` item's decision into a spec, `AGENTS.md` or the scope (`/architect`, `/scope`,
  `/sync`, or a plain chat) marks that item in the same step:
  `<script> done <index> D<n> --detail "landed: <repo relative path>"`. The owner never marks one.
- A typed `/rollover` runs the same memory step as the auto handoff, before it writes the handover:
  start one writer agent (sonnet, effort low) with the "Writer prompt" block of
  `~/.claude/auto-handoff/sections.md`, wait for its result (it runs in the background), then
  `<script> check <index> --transcript <this chat's transcript>` and `<script> prune <index>`. The
  handover names the index on a `Handover memory: <path>` line; when the writer failed or `check`
  exits 1 it says `memory not written: <reason>` instead, and the handoff goes on.
- At the handoff line, never claim that tools or the handover are broken. If a step failed, say which
  step and why, and what was tried.
