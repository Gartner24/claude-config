# Design pipeline scripts

## Overview

Helper scripts behind the `design` and `brand-system` skills, plus the run ledger that makes
their pipelines enforceable. A Stop hook refuses to end the turn while a run has open steps,
so a bug here can trap or silently release a session.

## Key files

| File | Owns |
|---|---|
| `scripts/ledger.sh` | Run ledger (Bash wrapper over inline Python): `init`, `set`, `show`, `check`, `await`, `adopt`, `done`. State in `<target>/.design/run.json` |
| `scripts/gate.sh` | Stop hook, registered from `design/SKILL.md` and `brand-system/SKILL.md` frontmatter, not settings.json |
| `scripts/test-ledger.sh` | The assertion suite for ledger + gate. Run after any change to either |
| `scripts/build-ramp.mjs` | OKLCH colour ramp solver (culori); `--check` proves every AA contrast target |
| `scripts/fontdata.sh`, `fontsearch.py`, `enrich.py`, `pair.py` | Google Fonts corpus fetch, search, metric measuring, pairing |
| `../design-gate/scripts/token-leak.sh`, `contrast.py` | Audits the gate runs on the built UI |

## Commands

```bash
bash scripts/test-ledger.sh            # must end TOTAL ... fail=0
node scripts/build-ramp.mjs --check
bash scripts/fontdata.sh               # populate ~/.cache/gfonts before any font script
```

## Conventions

- Active run pointer is per session: `~/.claude/.design-active-<session_id>`. `gate.sh` reads `session_id` from the hook payload, then `CLAUDE_CODE_SESSION_ID`, then `global`.
- `gate.sh` must exit 0 instantly when no pointer exists; it runs on every Stop in every session.
- The gate never holds a session forever: three blocks release and mark `escaped:true`; a ledger older than 24h or unreadable releases.
- A repo's ledger is owned by one live session; another session uses `adopt`, never a second `init`.
- Skip reasons come from a closed set per step; a `RAN` row needs the required skill invocations in the transcript, not in its evidence text.
- Pass paths to Python as argv, never interpolated into source (a quote in a directory name once broke the gate).
- Font data comes from `$GFONTS_CACHE` (default `~/.cache/gfonts`); `enrich.py` cache entries carry a version (`MCACHE_V`), bump it when the record shape changes.

## Gotchas

- `scripts/node_modules/` is committed on purpose so the ramp works on a fresh clone. Do not gitignore or lint it.
- `gate.sh` calls `~/.claude/skills/design/scripts/ledger.sh` by absolute path, so it tests the installed symlink, not a copy elsewhere.

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
