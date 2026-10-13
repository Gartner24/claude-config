# 0013 verify steps

_Steps derived from spec 0013 acceptance criteria. `/check verify` runs these; `/test` covers the commands._

## Probes

- [x] P0. Import reach (spec-gate probe, 2026-10-12, claude 2.1.296). Scratch project whose `CLAUDE.md` is `@<abs path outside the project>/work.md`, where that file says "The codeword is PELICAN-7". `env -C <proj> claude -p "What is the codeword from your instructions? Reply with only the codeword, or NONE." --max-turns 1` -> `NONE`. The same with `@inner.md` inside the project -> `PELICAN-7`. So a project `CLAUDE.md` cannot import the private file; the import goes in the user level `~/.claude/CLAUDE.md` (AC-2).
- [x] P2. filter-repo matching (spec-gate probe, 2026-10-12, git-filter-repo a40bce548d2c). Temp repo with `Zorblex and zorblex and ZORBLEX` in a text file, `x\0Zorblex` in a binary file, message `msg Zorblex`. Literal line `Zorblex==>work-org` (with a `#` comment line and a blank line in the file) -> text `work-org and zorblex and ZORBLEX`, binary unchanged, message `msg work-org`: literal lines are case sensitive and binary blobs are skipped; comment and blank lines did no harm. Then `regex:(?i)zorblex==>work-org` on text and message `msg ZORBLEX zorblex` -> `work-org and work-org and work-org`, `msg work-org work-org`. So the rewrite uses `filter-expr`'s case insensitive expressions and `check-history` scans binary blobs (AC-10).
- [x] P1. User level import (AC-2, run before any other build step; a failure stops the build). After `~/.claude/private/work.md` exists and the live `~/.claude/CLAUDE.md` carries `@~/.claude/private/work.md`: `env -C <empty scratch dir> claude -p "Which GitHub orgs count as bot reviewed in your instructions? Reply with the org names only, or NONE." --max-turns 1` names the orgs from `work.md`. In a sandboxed session `claude -p` says `Not logged in`; you run it with `!`. · waits on you
  - Run 1, 2026-10-12, by you with `!`: it named both orgs from `work.md`. PASS

## Manual steps

- [ ] 1. History (AC-10): the migration plan phases 1 to 5; `check-history` exits 0 in the rewritten copy and in a fresh clone of the new remote. · waits on you
- [x] 2. Same behavior (AC-11): `jq -S` of the live `settings.json` before and after a fresh `install.sh`, arrays sorted, compare equal.
  - Run 1, 2026-10-12: live settings.json before and after a real install.sh (autoMode deleted from both, arrays sorted) compare equal; the private fragments merged and install verify passed. install.sh still drops the live autoMode section, as before; it was put back by hand from the backup.

## Commands

- [x] `python3 scripts/private-names.py --test` -> AC-1, AC-3, AC-6, AC-8, AC-12
  - Run 1, 2026-10-12, `/check verify`: `private-names: all self checks passed`, exit 0.
- [ ] `python3 scripts/private-names.py check` on the branch and on merged `main` -> exit 0 -> AC-9
  - Run 1, 2026-10-12, `/check verify`, branch half only: `git ls-files -z | xargs -0 python3 scripts/private-names.py check` exit 0 (real names list read). A bare `check` lists the sandbox's untracked `/dev/null` dotfiles and exits 1 on `unreadable`; those are not repo files. Merged `main` waits on the merge box.
- [x] `./sync.sh` with a planted name in a temp live rule file -> exit 1, tree unchanged -> AC-4
  - Run 1, 2026-10-12, `/check verify`, scratch clone plus temp live tree, made up names: clean tree exit 0 with empty `git status --porcelain` and 0600 fragments; a name in `rules/planted.md` prints `.../rules/planted.md:2: names.txt line 2`, exit 1, repo tree hash unchanged; a name in a settings `env` value prints `settings.json (stripped):515: names.txt line 3`, exit 1; no names list prints the AC-1 line three times, exit 1.

## Value sourcing (added by /develop, 2026-10-12)

- [x] `filter-expr` on a temp names list with `name==>x` and a plain name -> the `==>` part is the replacement, the plain one gets `***REMOVED***`, longest first -> AC-10
  - Run 1, 2026-10-12, `/check verify`: `regex:(?i)zorblexcorp==>***REMOVED***` then `regex:(?i)quux==>tool`; a `regex:` line is refused, exit 1. In a temp repo `check-history` exit 1 before, `filter-repo` with that file, exit 0 after (three cases and `superquuxer` rewritten, message `msg tool`); a planted binary blob makes it exit 1 again.
- [x] any hit line names the matching `names.txt` line number, never the name, including a name inside a path (masked as `***`) -> AC-4, AC-8
  - Run 1, 2026-10-12, `/check verify`: `***-site/a.md: path name: names.txt line 4`; temp repo with hooks linked: clean commit exit 0, staged file `leak.txt:1: names.txt line 4` exit 1 (mixed case name), message `commit message:1: names.txt line 3` exit 1, no names list exit 1. The real repo's `.git/hooks/pre-commit` runs inside the `wf run` sandbox with nothing staged and exits 0, so the names list is readable there (spec Neutral note).
- [x] `strip-settings` on the committed `settings.json` with a names list that matches nothing -> output byte for byte equal to the committed file (the old `jq` format) -> AC-3
  - Run 1, 2026-10-12, `/check verify`: the clean sync in the AC-4 scratch clone left `git status --porcelain` empty, so both settings files came out byte for byte equal.
- [x] install in a scratch clone with temp `HOME` and `CLAUDE_LIVE_DIR`: a fragment path under `/home/santiago` lands under the temp `$HOME`; the private `gitignore` line lands in the clone's `.git/info/exclude` once on a rerun; an existing hand written `commit-msg` hook is left alone -> AC-6, AC-7
  - Run 1, 2026-10-12, `/check verify`: `--dry-run` wrote nothing; install merged the fragment (path swapped to the temp `$HOME`, `skillOverrides` key in, shared deny item not doubled, every public deny item kept), 1 exclude line, `pre-commit` linked, `hook exists, not replaced: commit-msg`; rerun added 0 exclude lines and 0 deny items; no fragment and no names list print both skip lines. install exits 1 at its own design ledger self check under a temp `HOME` (3 brand board cases need the private brand kit under `~/projects`); with the real `HOME` that check passes 107 of 107. Not a spec 0013 change.
