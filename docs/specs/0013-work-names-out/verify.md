# 0013 verify steps

_Steps derived from spec 0013 acceptance criteria. `/check verify` runs these; `/test` covers the commands._

## Probes

- [x] P0. Import reach (spec-gate probe, 2026-10-12, claude 2.1.296). Scratch project whose `CLAUDE.md` is `@<abs path outside the project>/work.md`, where that file says "The codeword is PELICAN-7". `env -C <proj> claude -p "What is the codeword from your instructions? Reply with only the codeword, or NONE." --max-turns 1` -> `NONE`. The same with `@inner.md` inside the project -> `PELICAN-7`. So a project `CLAUDE.md` cannot import the private file; the import goes in the user level `~/.claude/CLAUDE.md` (AC-2).
- [x] P2. filter-repo matching (spec-gate probe, 2026-10-12, git-filter-repo a40bce548d2c). Temp repo with `Zorblex and zorblex and ZORBLEX` in a text file, `x\0Zorblex` in a binary file, message `msg Zorblex`. Literal line `Zorblex==>work-org` (with a `#` comment line and a blank line in the file) -> text `work-org and zorblex and ZORBLEX`, binary unchanged, message `msg work-org`: literal lines are case sensitive and binary blobs are skipped; comment and blank lines did no harm. Then `regex:(?i)zorblex==>work-org` on text and message `msg ZORBLEX zorblex` -> `work-org and work-org and work-org`, `msg work-org work-org`. So the rewrite uses `filter-expr`'s case insensitive expressions and `check-history` scans binary blobs (AC-10).
- [ ] P1. User level import (AC-2, run before any other build step; a failure stops the build). After `~/.claude/private/work.md` exists and the live `~/.claude/CLAUDE.md` carries `@~/.claude/private/work.md`: `env -C <empty scratch dir> claude -p "Which GitHub orgs count as bot reviewed in your instructions? Reply with the org names only, or NONE." --max-turns 1` names the orgs from `work.md`. In a sandboxed session `claude -p` says `Not logged in`; you run it with `!`. · waits on you

## Manual steps

- [ ] 1. History (AC-10): the migration plan phases 1 to 5; `check-history` exits 0 in the rewritten copy and in a fresh clone of the new remote. · waits on you
- [ ] 2. Same behavior (AC-11): `jq -S` of the live `settings.json` before and after a fresh `install.sh`, arrays sorted, compare equal.

## Commands

- [ ] `python3 scripts/private-names.py --test` -> AC-1, AC-3, AC-6, AC-8, AC-12
- [ ] `python3 scripts/private-names.py check` on the branch and on merged `main` -> exit 0 -> AC-9
- [ ] `./sync.sh` with a planted name in a temp live rule file -> exit 1, tree unchanged -> AC-4

## Value sourcing (added by /develop, 2026-10-12)

- [ ] `filter-expr` on a temp names list with `name==>x` and a plain name -> the `==>` part is the replacement, the plain one gets `***REMOVED***`, longest first -> AC-10
- [ ] any hit line names the matching `names.txt` line number, never the name, including a name inside a path (masked as `***`) -> AC-4, AC-8
- [ ] `strip-settings` on the committed `settings.json` with a names list that matches nothing -> output byte for byte equal to the committed file (the old `jq` format) -> AC-3
- [ ] install in a scratch clone with temp `HOME` and `CLAUDE_LIVE_DIR`: a fragment path under `/home/santiago` lands under the temp `$HOME`; the private `gitignore` line lands in the clone's `.git/info/exclude` once on a rerun; an existing hand written `commit-msg` hook is left alone -> AC-6, AC-7
