# Organize claude-config and ~/.claude, and sync what you use daily

## Agreed so far, do not ask again

- Spec 0035 (readable layout) moved the repo into dotfiles and put the installed payload under `live/`, but you did not get what you meant by "organized". Organized means: change the folder structure itself, and rewrite the documentation files so they are easy to read. (your message 2026-10-15)
- Never destroy a skill. Every skill you have today keeps working through any move. (your message 2026-10-15)
- claude-config must be synced with `~/.claude`: it is out of date and misses much of what you use every day. (your message 2026-10-15)
- claude-config stays its own repo, nested in dotfiles as a submodule the same way nvim is (already true since 2026-10-15; keep it).
- The layout is optimized for reading by you and by AI, since it is read many times: a clear folder structure, no files floating loose at the top. This goes for the repo and for the parts of `~/.claude` you own. Ask whether `live/` is the right shape; it is not settled.
- claude-config holds your whole Claude setup, never leaking anything private: your own skills, and the skills you downloaded.
- Every downloaded skill records where it came from, so it can be updated later.
- A downloaded skill you edit is detached from its source, so an update never overwrites your changes. On update, you see what changed upstream for that skill and choose per change: take it into your version, or keep yours.
- A new skill (working name: update claude-config) syncs and updates your whole Claude setup. It never breaks or changes a working skill on its own; the reorganization only moves and organizes.
- Follow ups to keep tracking after the clear: the missed-skill report on 2026-10-18 (plan row 46), then delete `~/claude-migration-20261015/` and `~/claude-config-old` once that report is in and nothing broke.

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
