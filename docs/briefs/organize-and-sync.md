# Organize claude-config and ~/.claude, and sync what you use daily

## Agreed so far, do not ask again

- Spec 0035 (readable layout) moved the repo into dotfiles and put the installed payload under `live/`, but you did not get what you meant by "organized". Organized means: change the folder structure itself, and rewrite the documentation files so they are easy to read. (your message 2026-10-15)
- Never destroy a skill. Every skill you have today keeps working through any move. (your message 2026-10-15)
- claude-config must be synced with `~/.claude`: it is out of date and misses much of what you use every day. (your message 2026-10-15)

## Measured 2026-10-15 (input for /architect, not a decision)

- `~/.claude/skills`: 265 entries; 83 are links (about 66 into jjstack and vendor-jsm-skills, 17 into this repo's `live/skills`); the rest are real folders put there by other installers (gstack, ECC, 21st, Cloudflare and others). The repo's `live/skills` holds 20.
- `~/.claude/commands`: 32 entries, repo holds 5 (27 ECC style commands are live only).
- `~/.claude/hooks`: 19 entries, repo holds 4 (jjstack links, get-shit-done `gsd-*` hooks, `workflow-start.sh`, `claude-ram-watch.sh` are live only).
- `~/.claude/settings.json` differs from `live/settings.json`.
- The repo top still has an empty `hooks/` (only `__pycache__`), left by 0035.

## Open for /architect

- What the repo holds for third party skills: copies, or a manifest naming each source and its install command.
- The target folder layout for the repo and for `~/.claude`.
- Which docs are rewritten, and for which reader.
- How sync stays current afterwards (sync.sh scope, a check that flags drift).
