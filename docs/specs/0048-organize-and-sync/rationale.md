# 0048. Rationale

## Context
Spec 0035 moved claude-config into dotfiles and put the installed files under `live/`, but the result still did not read as organized to you: ten loose files at the top, guides that grew to about 22,000 words, and a `live/` name that says nothing about what it holds.

The bigger gap is coverage. Measured 2026-10-15: `~/.claude/skills` has 265 entries and the repo holds 20. About 180 real folders came from other installers (gstack, ECC, 21st, Cloudflare and others), and only 10 of them have a recorded source in `~/.agents/.skill-lock.json`. Commands (27 of 32), hooks (15 of 19) and the live `settings.json` are also live only. A new machine restored from the repo today would lose most of the setup, and "has this skill changed upstream?" cannot be answered for most skills.

You also patch downloaded skills (three overrides are guarded by `scripts/skills-audit.sh`). Any reinstall silently reverts those patches. The constraint from you is absolute: no working skill may break, and nothing may change a skill without your yes.

## Options considered

### Option 1: Fix in place
Keep `live/` and the top level as they are, extend `skills-audit.sh` to record sources, and edit the docs where they are wrong.

**Pros**: smallest change, no path migration, no runner change.
**Cons**: leaves the shape you said is not organized; `skills-audit.sh` is a bash plus inline Python tool that only hashes `SKILL.md`, so per change updates would be bolted onto the wrong base; the docs stay long.

### Option 2: Restructure in place, manifest plus copies, one tool (chosen)
Rename and regroup in one pass, record every downloaded thing in a manifest, copy in only edited and untraceable skills, and build one stdlib Python tool that absorbs `skills-audit.sh`.

**Pros**: one source of truth for provenance; the repo stays small (no full vendoring); edits are protected by hash; the reminder and drift check reuse the same code.
**Cons**: a path migration across the runner and about 15 tests; tracing 160 skills is slow and imperfect.

### Option 3: Vendor everything
Copy all 265 skills into the repo and treat the repo as the only source.

**Pros**: restore needs no network; drift is a plain directory compare.
**Cons**: thousands of third party files in a public repo, each with its own license; upstream updates become manual merges of whole trees; the repo becomes unreadable, the opposite of the goal.

### Option 4: Fresh repo, strangler move
Start a new repo with the new shape and move pieces over while the old one keeps running.

**Pros**: the old setup keeps working untouched during the move.
**Cons**: two repos to keep in sync in the meantime, the dotfiles submodule and `wf` trust list move twice, and history splits.

## Rationale
Option 2 is the only one that meets both of your answers: a manifest plus copies of edited ones (not Option 3), and a changed folder structure (not Option 1). The repo is small and owned by one person, so a strangler move (Option 4) buys safety the step by step migration already gives, at the cost of a second repo. The temporary `live -> claude-home` link gives the same "old keeps working" property for the one risky moment, the rename.

The manifest is JSON read with the standard library because every other tool here is stdlib Python and the runner already parses JSON state; YAML or TOML would add a dependency or a parser for no gain. It sits in `config/` because it describes the repo, it is not installed into `~/.claude`, so it must not live under `claude-home/`.

Edited detection compares a hash of the whole installed folder to the hash of the upstream folder at the pinned version. That needs no network at drift time and catches edits to any file, where the old `skills-audit.sh` hashed only `SKILL.md` and needed a marker string per override.

## References
Not requested (references level: none).
