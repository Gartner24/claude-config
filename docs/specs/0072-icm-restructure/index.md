# 0072. Restructure claude-config to the ICM layout, phase 1

**Date**: 2026-10-22
**Status**: Proposed
**Paths:** `CLAUDE.md`, `AGENTS.md`, `map/**`, `tests/**`, `_archive/**`, `runner/**`, `docs/scope/**`, `config/test-preferences.json`, `scripts/private-names.py`, `scripts/ref-check.py`, `claude-home/mods/chip-dash/plan.py`, `bin/install.sh`, `README.md`

## What you're agreeing to
- A new `map/` folder with short cards that tell a chat what each part of this repo is and what a change to it also moves.
- `CLAUDE.md` becomes the real entry file (under about 60 lines, never break rules stay in it); `AGENTS.md` becomes a link to it, and a commit with a broken link is refused.
- The retired runner, its tests and its old docs move to `_archive/` in git; the 8 tests for live code move to `tests/`, and the suite runs only those.
- Closed rows of the plan move out of `docs/scope/scope.md` so it stops being 28k tokens.
- Every PR proves nothing broke with a reference check script and one regression agent. Phase 2 (the whole restructure) is designed after this lands and is reviewed.

## Summary
This is phase 1 of moving claude-config to ICM (Interpretable Context Methodology, a way to lay out folders so one agent reads only what each step needs). It does only the moves the icm-architect skill checked as safe on this repo. It adds a map, shortens the entry file, archives the retired runner, and splits the huge plan file. Nothing that `~/.claude`, `~/.local/bin` or `settings.json` points at changes path.

## Structure
Phase 1 is built as three child specs, one branch and one PR each, in this order (each one stacks on the one before only if it is not merged yet):
- [0072-ref-check-and-archive.md](0072-ref-check-and-archive.md): the reference check script, `tests/` split, runner and runner docs to `_archive/`. Supports AC-1 to AC-5.
- [0072-map-and-entry.md](0072-map-and-entry.md): `map/` cards, `CLAUDE.md` as entry, `AGENTS.md` as a guarded link. Supports AC-6 to AC-10.
- [0072-scope-split.md](0072-scope-split.md): closed scope rows to `docs/scope/done.md`, chip-dash plan pane kept correct. Supports AC-11 to AC-12.

## Requirements

**User stories**:
- As the owner, I want a chat in claude-config to find what it needs in a few short files, so it stops loading 28k tokens of plan and 86 lines of rules every time.
- As the owner, I want proof that nothing broke after every move, without spending a review stack's usage.

**Acceptance criteria**:
- **AC-1**: `scripts/ref-check.py snapshot` records every path that points into the repo: tracked file text naming a repo path, spec `**Paths:**` globs, links under `~/.claude/skills`, `~/.claude/commands`, `~/.local/bin` resolving into the repo, and repo paths named in `~/.claude/settings.json`. `ref-check.py verify <snapshot>` exits 1 and lists each one that no longer resolves, unless the same change rewrote that referrer to the new path.
- **AC-2**: the 8 live code test files (`test_claude_config`, `test_skill_keep`, `test_skill_scan`, `test_spec_paths`, `test_layout`, `test_borrowed_ideas`, `test_move_home_chat`, `test_fast`), `fast.py` and `fixtures/` live in `tests/`; the suite command is `python3 tests/fast.py` in `CLAUDE.md` and `config/test-preferences.json`, and it passes.
- **AC-3**: `runner/*.py`, `runner/e2e/` and the 41 runner only tests live in `_archive/runner/`; `runner/` no longer exists; one command on the runner map card runs the archived tests by hand.
- **AC-4**: runner docs (runner specs, `docs/specs/*/probes/`, runner briefs and reviews) live in `_archive/runner/docs/`. Before a spec moves, each of its decisions still in force is named in a live spec, `CLAUDE.md` or a map card; the PR lists each such decision with its live home.
- **AC-5**: every PR of this spec shows in its body: `ref-check.py verify` clean, `bin/install.sh --dry-run` clean, the suite passing, `spec-paths` output, and one regression-hunter (Sonnet) report with no confirmed regression.
- **AC-6**: `CLAUDE.md` is under 60 lines, routes only, and holds: never break rules (public repo, private names, no attribution, ASCII, commit format), the 4 most used commands, standing answers, agent skills, context files, and a row pointing at `map/`.
- **AC-7**: every line of the old `AGENTS.md` has one new home (kept in `CLAUDE.md` or on a named map card); a test compares the old text's rule lines against the new homes and lists any line with none.
- **AC-8**: `AGENTS.md` is a symlink to `CLAUDE.md`; `tests/test_layout.py` fails when it is not.
- **AC-9**: the pre-commit hook refuses a commit where `AGENTS.md` is not a symlink to `CLAUDE.md`, and prints the repair command.
- **AC-10**: `map/` holds `CLAUDE.md` (catalog), `CONTEXT.md` (how to walk it and the name collisions: workflow, review, wf, dash), `_meta/schema.md`, `_templates/` (`object.md`, `process.md` from icm-architect), object cards (install, mods, rules, skills, specs, scope, suite, runner) and process cards (install, sync, checks, land a feature, handoff), and `effects/CONTEXT.md`; every `path` or `path:line` a card cites exists, checked by `ref-check.py`.
- **AC-11**: closed rows (`· done`, `· dropped`) live in `docs/scope/done.md`, `docs/scope/scope.md` keeps open rows plus a link to it, and `/scope`'s next box rule still finds the same next box as before the split.
- **AC-12**: the chip-dash plan pane shows the same open rows and counts as before the split (its test proves it).

## Decision
**Chosen option**: Option 2, map plus safe moves, then phase 2 after review.

Move only what nothing outside points at, add the ICM map and entry file, and leave the held paths (`claude-home/`, `bin/`, `scripts/`, `config/`, `docs/specs/`, `docs/scope/`) where they are until phase 2 has its own migration map.

**Implementation skills**: icm-architect (RinDig/icm-architect, read from its clone; its install as a downloaded skill in `config/manifest.json` is task 1).

## Feature design

**Data model sketch**: none (files only).

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| ref-check snapshot | paths pointing in | `git ls-files` text, spec `**Paths:**` lines, `find -lname` in the 3 outside folders, `~/.claude/settings.json` |
| ref-check verify | "rewritten in this change" | the referrer's text in the working tree names the new path from the migration map |
| AC-7 line homes | old `AGENTS.md` text | `git show <base>:AGENTS.md` |
| AC-11 same next box | next box before | the next box rule run on `<base>:docs/scope/scope.md` |
| card citations | cited paths | backticked paths in `map/**/*.md` |

**Key invariants**: no held path changes; no tracked file is deleted outright (moves only, `git mv`); the suite passes after every PR; nothing private enters the repo.

**Security model**: no change. The pre-commit hook stays a copy, not a link (spec 0013 AC-7); the twin check is added inside `scripts/private-names.py` pre-commit mode, so the existing hook carries it.

**Critical test scenarios**:
- `sed -i` on `AGENTS.md` replaces the link: the commit is refused (AC-9), the suite fails (AC-8).
- A moved test file still named by a spec `**Paths:**` line not updated: `ref-check.py verify` lists it (AC-1).
- A map card cites a path that was renamed: `ref-check.py` lists it (AC-10).
- Splitting the scope changes nothing the next box rule picks (AC-11) or the plan pane shows (AC-12).

## Build plan
1. Install icm-architect as a downloaded skill (manifest entry, pin, license, scan), satisfies **AC-10**.
2. `scripts/ref-check.py` with `snapshot`, `verify`, citation check and `--test`, satisfies **AC-1**, **AC-10**.
3. Snapshot on main, then `git mv` the 8 live tests, `fast.py`, `fixtures/` to `tests/`; update the suite command, test preferences and `**Paths:**` lines, satisfies **AC-2**.
4. `git mv` runner code, e2e and runner tests to `_archive/runner/`; runner docs to `_archive/runner/docs/` after the decision check, satisfies **AC-3**, **AC-4**.
5. Write the map catalog, schema, templates and cards from the old `AGENTS.md` and section 6 of the research brief, satisfies **AC-10**.
6. Rewrite `CLAUDE.md` as the entry; add the line homes test, satisfies **AC-6**, **AC-7**.
7. Replace `AGENTS.md` with the link; add the layout test and the pre-commit twin check with its `--test`, then rerun `bin/install.sh` to refresh the hook copy, satisfies **AC-8**, **AC-9**.
8. Split closed rows to `done.md`; update `chip-dash/plan.py` if its test shows a change, satisfies **AC-11**, **AC-12**.
9. Per PR: ref-check verify, install dry run, suite, spec-paths, one regression-hunter on Sonnet, satisfies **AC-5**.

## Migration plan
**Strategy**: strangler (moves land one PR at a time; held paths untouched until phase 2).
**Phases**:
1. 0072a: ref check, `tests/`, runner and runner docs archive.
2. 0072b: map, `CLAUDE.md` entry, `AGENTS.md` link and commit check.
3. 0072c: scope split.
**Rollback**: revert the one squash merge commit of the failed PR; `git mv` moves revert cleanly, and rerun `bin/install.sh` after reverting 0072b so the hook copy matches.
**Risks**: a referrer the snapshot cannot see (cron, another machine) points at a moved runner path; the owner is asked for outside consumers at the 0072a PR.

## Consequences
**Positive**: a chat loads a short entry file and only the cards it needs; the suite drops dead tests; old runner decisions stop mixing with live ones.

**Negative / tradeoffs**: a rule on a card loads only when the card is opened; the archived runner tests no longer run by default; about 3 PRs and links into old specs to update; `sed -i` style edits to `AGENTS.md` now fail at commit instead of silently drifting.

**Neutral**: phase 2 needs its own `/architect` with a migration map for the held paths.

## Follow-up
- [ ] Phase 2: `/architect` the whole restructure after phase 1 is merged and reviewed (its migration map moves held paths only with every outside referrer updated in the same change).
- [ ] Rows 100 to 102 (workflows) are separate scope rows.

## Rationale
See [rationale.md](rationale.md).
