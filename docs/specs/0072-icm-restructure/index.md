# 0072. Restructure claude-config to the ICM layout, phase 1

**Date**: 2026-10-22
**Status**: Proposed
**Paths:** `CLAUDE.md`, `AGENTS.md`, `map/**`, `tests/**`, `_archive/**`, `config/test-preferences.json`, `scripts/private-names.py`, `scripts/ref-check.py`, `claude-home/mods/chip-dash/plan.py`, `bin/install.sh`, `README.md`

## What you're agreeing to
- A new `map/` folder with short cards that tell a chat what each part of this repo is and what a change to it also moves.
- `CLAUDE.md` becomes the real entry file (under about 60 lines, never break rules stay in it); `AGENTS.md` becomes a link to it, and a commit with a broken link is refused.
- The retired runner, its tests and its old docs move to `_archive/` in git; the 8 tests for live code move to `tests/`, and the suite runs only those. Nothing outside git is deleted.
- Closed rows of the plan move out of `docs/scope/scope.md` so it stops being 28k tokens.
- Every PR proves nothing broke with a reference check script and one regression agent. Phase 2 (the whole restructure) is designed after this lands and is reviewed.

## Summary
This is phase 1 of moving claude-config to ICM (Interpretable Context Methodology, a way to lay out folders so one agent reads only what each step needs). It does only the moves the icm-architect skill checked as safe on this repo. It adds a map, shortens the entry file, archives the retired runner, and splits the huge plan file. Nothing that `~/.claude`, `~/.local/bin` or `settings.json` points at changes path.

## Structure
Phase 1 is three child specs, one branch and one PR each, in this order:
- [0072-ref-check-and-archive.md](0072-ref-check-and-archive.md): the reference check script, `tests/` split, runner and runner docs to `_archive/`. AC-1 to AC-5, AC-13.
- [0072-map-and-entry.md](0072-map-and-entry.md): `map/` cards, `CLAUDE.md` as entry, `AGENTS.md` as a guarded link. AC-6 to AC-10. Stacks on 0072a while 0072a is unmerged.
- [0072-scope-split.md](0072-scope-split.md): closed scope rows to `docs/scope/done.md`, chip-dash plan pane updated. AC-11, AC-12. Stacks on 0072a while 0072a is unmerged (scope links to moved files change there).

## Requirements

**User stories**:
- As the owner, I want a chat in claude-config to find what it needs in a few short files, so it stops loading 28k tokens of plan and 86 lines of rules every time.
- As the owner, I want proof that nothing broke after every move, without spending a review stack's usage.

**Acceptance criteria**:
- **AC-1**: `scripts/ref-check.py snapshot --out <file>` records every path that points into the repo:
  - in tracked text: backticked or markdown link tokens that contain `/` and start with a top repo folder (`bin`, `config`, `claude-home`, `runner`, `scripts`, `docs`, `tests`, `map`, `_archive`) or with `~/claude-config/`, `$HOME/claude-config/` or the realpath `/home/santiago/dotfiles/claude-config/`; `path:line` also checks the line exists; globs expand with fnmatch; fenced blocks, `docs/specs`, `docs/reviews`, `docs/briefs` history, `_archive/` and vendored trees (`claude-home/agents/`, `claude-home/rules/ecc/`, `claude-home/skills/anti-ai-writing/`) are skipped;
  - spec `**Paths:**` globs of specs outside `_archive/`;
  - links under `~/.claude/skills`, `~/.claude/commands`, `~/.local/bin` whose `readlink -f` is under the repo;
  - strings in `~/.claude/settings.json` starting with any of the three repo path spellings.
  `ref-check.py verify <snapshot> --map <file>` (map = `old -> new` lines from `git diff -M --name-status <base>`) exits 1 and lists each pointer that no longer resolves, unless its referrer now names the mapped new path. It runs on the owner's machine. `--test` covers each pointer kind.
- **AC-2**: the 8 live code test files (`test_claude_config`, `test_skill_keep`, `test_skill_scan`, `test_spec_paths`, `test_layout`, `test_borrowed_ideas`, `test_move_home_chat`, `test_fast`), `fast.py` and the fixtures the live tests use live in `tests/`; their repo root lookups change from `parents[2]` (or `.parent.parent.parent`) to `parents[1]`; `test_layout.py`'s top folder list adds `tests`, `map`, `_archive` and drops `runner`. The suite command `python3 tests/fast.py` replaces `python3 runner/tests/fast.py` in the standing answers and in `config/test-preferences.json` (`testDir` and run command), and the suite passes.
- **AC-3**: `runner/*.py`, `runner/e2e/`, the 41 runner only tests and the fixtures they need live in `_archive/runner/`; `runner/` no longer exists. The runner map card holds `cd _archive/runner && python3 -m unittest discover -s tests`; the build runs it once and records the pass count in the PR, with any failure listed. `**Paths:**` lines of live specs naming `runner/` are rewritten to `_archive/runner/...` (a Paths only amendment), and `spec-paths` is clean.
- **AC-4**: runner docs move to `_archive/runner/docs/`. A runner spec is one whose `**Paths:**` are all under `runner/`, plus a hand list named in the PR; a spec mixing live and runner paths stays live; a spec an open scope row links to stays live. Runner briefs and reviews are only those a moved runner spec names (by `Source:` or link) plus `docs/specs/*/probes/` of moved specs; each is listed in the PR. Before a spec moves, each of its decisions still in force is named with its live home (a live spec, `CLAUDE.md` or a map card) in a PR table that the owner checks. No file outside `_archive/` and the history folders still names `runner/` (grep in the PR). Consumed handover files outside git are not touched.
- **AC-5**: every PR of this spec shows in its body: `ref-check.py verify` clean, `bin/install.sh --dry-run` clean, the suite passing, `spec-paths` output, and one regression-hunter (Sonnet) report. A regression the builder confirms with a `file:line` blocks the PR; unconfirmed findings are listed in the body.
- **AC-6**: `CLAUDE.md` is under 60 lines, routes only, and holds: never break rules (public repo, private names, no attribution, ASCII, commit format), these 4 commands (`python3 tests/fast.py`, `bin/install.sh --dry-run`, `bin/sync.sh`, `python3 bin/claude-config.py drift`), standing answers, agent skills, context files, and a row pointing at `map/`.
- **AC-7**: `map/_meta/line-homes.md` maps every non blank, non heading line of the old `AGENTS.md` (read with `git show <pinned commit hash>:AGENTS.md`) to its new file; a test fails on any old line with no entry, or an entry naming a file that does not exist.
- **AC-8**: `AGENTS.md` is a symlink to `CLAUDE.md`; `tests/test_layout.py`'s single load test asserts `CLAUDE.md` is a regular file and `AGENTS.md` a symlink to it (replacing the `@AGENTS.md` and "For an AI agent" checks).
- **AC-9**: the pre-commit hook refuses a commit where `git ls-files -s AGENTS.md` is not mode `120000` pointing at `CLAUDE.md`, and prints the repair command; it does nothing in a repo with no tracked or staged `AGENTS.md`. `--test` covers refuse, pass, and no-op. The check and its test land in a commit before the `AGENTS.md` swap; after the swap, `bin/install.sh` is rerun and the hook copy is `cmp`'d against the script; a probe commit of a replaced link is refused and recorded in verify.md.
- **AC-10**: `map/` holds `CLAUDE.md` (catalog), `CONTEXT.md` (how to walk it and the name collisions: workflow, review, wf, dash), `_meta/schema.md`, `_templates/` (`object.md`, `process.md`, written in this repo after the skill's templates, credited in `docs/NOTICE.md`), object cards (install, mods, rules, skills, specs, scope, suite, runner) and process cards (install, sync, checks, land a feature, handoff), and `effects/CONTEXT.md`; every `path` or `path:line` a card cites exists, checked by `ref-check.py`.
- **AC-11**: features whose heading carries `· done` or `· dropped` and that have no unticked box live in `docs/scope/done.md`; `docs/scope/scope.md` keeps every other feature plus a link to `done.md`; the first unticked box and its command for every feature, computed with the chip-dash parser on `<base>:docs/scope/scope.md` and on the new files, are identical.
- **AC-12**: the chip-dash plan pane shows the same open rows and open count as before the split, and reads its done count from `done.md`; `plan.py` is changed for this and its test proves both.
- **AC-13**: `test_layout.py`'s link test skips `_archive/` (frozen); scope rows linking a moved file get the new path in the same PR.

## Decision
**Chosen option**: Option 2, map plus safe moves, then phase 2 after review.

Move only what nothing outside points at, add the ICM map and entry file, and leave the held paths (`claude-home/`, `bin/`, `scripts/`, `config/`, `docs/specs/`, `docs/scope/`) where they are until phase 2 has its own migration map.

**Implementation skills**: icm-architect (RinDig/icm-architect), registered as a downloaded skill in `config/manifest.json` (task 1); none of its files are copied into the repo.

## Feature design

**Data model sketch**: none (files only).

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| ref-check snapshot | paths pointing in | AC-1 token rule over `git ls-files`, spec `**Paths:**`, `readlink -f` of the 3 outside folders, `~/.claude/settings.json` |
| ref-check verify | "rewritten in this change" | the `--map` file from `git diff -M --name-status <base>` |
| AC-4 runner spec set | which specs move | `**Paths:**` all under `runner/`, plus the PR's hand list |
| AC-7 line homes | old `AGENTS.md` text | `git show <pinned hash>:AGENTS.md`; `map/_meta/line-homes.md` |
| AC-11 same next box | next box per feature | chip-dash parser on base and new scope files |
| AC-12 done count | closed rows | `docs/scope/done.md` |
| card citations | cited paths | backticked paths in `map/**/*.md` |

**Key invariants**: no held path changes; moves are `git mv` only; the suite passes after every PR; nothing private enters the repo; nothing outside git is deleted.

**Security model**: no change. The pre-commit hook stays a copy, not a link (spec 0013 AC-7); the twin check lives in `scripts/private-names.py` pre-commit mode, so the existing hook carries it.

**Critical test scenarios**:
- `sed -i` on `AGENTS.md` replaces the link: the commit is refused (AC-9), the suite fails (AC-8).
- A moved test still named by a live spec `**Paths:**` line not rewritten: `ref-check.py verify` and `spec-paths` list it (AC-1, AC-3).
- A map card cites a renamed path: `ref-check.py` lists it (AC-10).
- The scope split changes nothing the next box rule picks (AC-11) or the pane shows as open (AC-12).

## Build plan
1. Register icm-architect in `config/manifest.json` (pin, license, scan), satisfies **AC-10**.
2. `scripts/ref-check.py` with `snapshot`, `verify --map`, citation check and `--test`, satisfies **AC-1**, **AC-10**.
3. Snapshot on main; `git mv` the 8 live tests, `fast.py` and their fixtures to `tests/`; fix root lookups, `test_layout` top list, suite command, test preferences, standing answer, satisfies **AC-2**.
4. `git mv` runner code, e2e, runner tests and fixtures to `_archive/runner/`; runner docs to `_archive/runner/docs/` after the decision table; rewrite live specs' runner `**Paths:**`; link test skips `_archive/`; scope links updated; run the archived tests once, satisfies **AC-3**, **AC-4**, **AC-13**.
5. Map catalog, schema, templates, cards and `effects/` from the old `AGENTS.md` and icm-research.md section 6; NOTICE entry, satisfies **AC-10**.
6. Rewrite `CLAUDE.md` as the entry; write `line-homes.md` and its test, satisfies **AC-6**, **AC-7**.
7. Twin check in `private-names.py` with `--test` (own commit), then the `AGENTS.md` link and new single load test, rerun `bin/install.sh`, `cmp` the hook, probe commit, satisfies **AC-8**, **AC-9**.
8. Split closed rows to `done.md`; change `plan.py` to read the done count from it, with its test, satisfies **AC-11**, **AC-12**.
9. Per PR: ref-check verify, install dry run, suite, spec-paths, one regression-hunter on Sonnet, satisfies **AC-5**.

## Migration plan
**Strategy**: strangler (moves land one PR at a time; held paths untouched until phase 2).
**Phases**:
1. 0072a: ref check, `tests/`, runner and runner docs archive.
2. 0072b: map, `CLAUDE.md` entry, `AGENTS.md` link and commit check.
3. 0072c: scope split.
**Rollback**: revert the one squash merge commit of the failed PR; rerun `bin/install.sh` after reverting 0072b so the hook copy matches.
**Risks**: a referrer the snapshot cannot see (cron, another machine) points at a moved runner path; the owner is asked for outside consumers at the 0072a PR.

## Consequences
**Positive**: a chat loads a short entry file and only the cards it needs; the suite drops dead tests; old runner decisions stop mixing with live ones.

**Negative / tradeoffs**: a rule on a card loads only when the card is opened; the archived runner tests no longer run by default; about 3 PRs and links into old specs to update; a skill that edits `AGENTS.md` with the Edit or Write tool is refused with `CLAUDE.md` named as the target, and a `sed -i` edit is stopped at commit.

**Neutral**: phase 2 needs its own `/architect` with a migration map for the held paths.

## Follow-up
- [ ] Phase 2: `/architect` the whole restructure after phase 1 is merged and reviewed. Its migration map moves held paths only with every outside referrer updated in the same change; its review is the same script plus one agent, switched to `/review` if phase 2 rewrites code rather than moving files.
- [ ] Rows 100 to 102 (workflows) are separate scope rows.

## Rationale
See [rationale.md](rationale.md).
