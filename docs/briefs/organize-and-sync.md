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
- Downloaded skills: the repo holds a manifest (each skill's source, pinned version, install command) and copies only of the ones you edited, kept detached. Plugins and frameworks (gstack, jjstack, get-shit-done, vendor-jsm-skills) go in the same manifest. (answer 2026-10-15)
- Skills with no recorded source (~160 of 178 real folders; only 10 in `~/.agents/.skill-lock.json`, 4 git checkouts): the build traces each on GitHub and skills.sh; found goes in the manifest, not found is copied into the repo marked "source unknown". No skill is ever only listed. (answer 2026-10-15)
- Repo top holds only `README.md`, `AGENTS.md`, `CLAUDE.md`, `LICENSE` plus folders. Scripts (`install.sh`, `sync.sh`) move to `bin/`, config files (`mcp-config.json`, `test-preferences.json`) to `config/`, `NOTICE.md` to `docs/`. The runner's live step shape `./install.sh` and `rules/scope-contract.md` follow the new path. (answer 2026-10-15)
- `live/` is renamed `claude-home/`, still a path for path mirror of `~/.claude`. Own skills and edited copies of downloaded skills both live in `claude-home/skills/`, the manifest says which is which. (answer 2026-10-15)
- Docs: every file rewritten, one reader per file (README for you, AGENTS.md for AI), and "without losing quality": every command, fact and decision in the old docs is listed and mapped to where it lands; nothing may map to nowhere. (answer 2026-10-15)
- Guides regrouped by task into 5: setup (install, restore, MCP, plugins), daily-use (workflow chain and wf), skills (generated from the manifest, plus routing), hooks, design-pipeline. SKILLS-EVALUATION moves to `docs/research/`. (answer 2026-10-15)
- The new skill is `/claude-config`. Drift check runs only inside it, never at session start. Upstream update check runs only when you run it; a weekly reminder line appears at session start when 7 days passed since the last upstream check. Every upstream change is shown and you take it or keep yours, per change. (answers 2026-10-15)
- Measured 2026-10-15: an old `scripts/skills-audit.sh` already hashes every skill into `~/.claude/.skills-manifest.json` and guards 3 local overrides (industrial-brutalist-ui, minimalist-ui, high-end-visual-design); build on it, do not duplicate it. `install.sh`/`sync.sh` are named in `runner/finish.py`, `runner/run.py`, `runner/e2e/run.py`, about 15 runner tests, `scripts/private-names.py`, `scripts/gen-agent-index.py`, `live/settings.json`, `live/rules/scope-contract.md`, `live/skills/review-stack/SKILL.md`. dotfiles code does not call them (only its specs mention them).
- A downloaded skill containing a private name never enters the repo or the public manifest: it is copied to `~/.claude/private/skills/` instead, so it is still never only listed. (answer 2026-10-15)
- Cross check gaps on spec 0048: apply every recommended fix (per hunk take or keep asked by the skill, attended trace with a report, settings drift after the sync transform, license unknown in NOTICE, name based skill check). (answer 2026-10-15)
- After the research review (docs/research/organize-and-sync-review-2026-10-15.md), spec 0048 is kept but amended (answers 2026-10-15):
  - Edited downloaded skills are kept as the pinned original plus a patch of your edits, not a detached full copy. Update applies the patch to the new upstream and stops only on a conflict (`git merge-file`). This replaces the per change take or keep review.
  - Untraceable skills: nothing is copied into the public repo blind. You fill in the sources in [untraced-skills.md](untraced-skills.md) (169 skills, grouped by guess). What you name goes in the manifest; whatever stays unknown is decided with you, and the research says it must not be republished publicly (no license = all rights reserved).
  - A separate small feature trims skills that describe themselves in every session from 77 to about 35 (`skillOverrides`, `/skill-doctor`, shorten the 8 descriptions over 1,024 characters, check plugin skills). No skill is deleted.
  - AGENTS.md shrinks to rules that are not obvious, under 200 lines; each guide states its type (tutorial, how to, reference, explanation).
- Follow ups to keep tracking after the clear: the missed-skill report on 2026-10-18 (plan row 46), then delete `~/claude-migration-20261015/` and `~/claude-config-old` once that report is in and nothing broke.

## Measured 2026-10-15 (input for /architect, not a decision)

- `~/.claude/skills`: 265 entries; 83 are links (about 66 into jjstack and vendor-jsm-skills, 17 into this repo's `live/skills`); the rest are real folders put there by other installers (gstack, ECC, 21st, Cloudflare and others). The repo's `live/skills` holds 20.
- `~/.claude/commands`: 32 entries, repo holds 5 (27 ECC style commands are live only).
- `~/.claude/hooks`: 19 entries, repo holds 4 (jjstack links, get-shit-done `gsd-*` hooks, `workflow-start.sh`, `claude-ram-watch.sh` are live only).
- `~/.claude/settings.json` differs from `live/settings.json`.
- The repo top still has an empty `hooks/` (only `__pycache__`), left by 0035.

## Open for /architect

- Nothing open from the interview. Left to the spec writer: manifest file name and format (JSON, stdlib), where it lives outside claude-home/, how an edited skill is detected (hash vs upstream at its pinned version), migration steps and checks (same method as 0035).
