# Handoff

## When
A feature is still open and the context is full, or a feature closed and the task switches.

## Steps
1. Write chat-only decisions into the feature's brief (`docs/briefs/`) first.
2. Feature open: `/rollover`, then the owner types `/clear` and `/resume-from-clear`. Feature closed: `/save-and-clear`, then `/clear`.
3. Rules: `claude-home/rules-on-demand/handoff.md`.

## Done when
- The next chat starts from the handover and names every open PR and branch.

## Also moves
- [mods](../objects/mods.md): `wf-handoff` runs the automatic handoff at the token line.
- `claude-home/hooks/handover-start.sh` loads the waiting handover after `/clear`.
