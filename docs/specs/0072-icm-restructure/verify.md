# 0072 verify

## Probes before accept

### Symlink survives the file tools (2026-10-22)
Setup in a scratch folder: `CLAUDE.md` with one line, `ln -s CLAUDE.md AGENTS.md`.
- Edit tool on `AGENTS.md`: refused, "it is a symbolic link. Write to the link's target path instead: .../CLAUDE.md". Link kept.
- Write tool on `AGENTS.md`: same refusal. Link kept.
- `sed -i 's/line one/line one by sed/' AGENTS.md`: exit 0, and `ls -l` shows `AGENTS.md` as a regular 16 byte file. The link was REPLACED, the two files now differ.
Result: the link alone is not enough; AC-9 (commit refusal) and AC-8 (suite test) are required.

### Commit of a replaced link is refused (runs first in the 0072b build)
Owed: after the twin check lands, replace the link with `sed -i` in a scratch clone and try to commit. The commit must be refused. The build stops if it is not.

### Mod API sees workflow agents
Not run here: it belongs to row 100 (where runs show), not this spec.

## 0072a build (2026-10-22)

- [x] AC-1: `python3 scripts/ref-check.py --test` prints `ref-check self check: ok`; the real snapshot on main (`snapshot --link-root <main checkout>`) recorded 687 pointers (271 text, 385 spec Paths, 29 live links, 2 settings.json strings), 98 already dangling left out. A fourth spelling `/home/santiago/claude-config/` was added to the spec's three: settings.json names the repo that way and the three found 0 strings. can fail: a pointer kind not recorded, or a moved file not reported, turns a named line of the self check into `FAIL`.
- [x] AC-2: `tests/` holds the 8 live test files and `fast.py`; their root lookups read `parents[1]` (`tests/test_spec_paths.py:8`, `tests/test_layout.py:9`, `tests/test_claude_config.py:16`, `tests/test_skill_scan.py:15`, `tests/test_move_home_chat.py:14`, `tests/test_skill_keep.py:13`); `python3 tests/fast.py` ends `Ran 118 tests ... 0 failed / OK`. Standing answer at `AGENTS.md` (`suite:`) and `config/test-preferences.json` `testDir` say `tests/`. No fixtures move: none of the 8 uses `runner/tests/fixtures`. can fail: a lookup left at `parents[2]` points outside the repo; mutant `test_spec_paths.py` with `parents[2]` went red (see mutations).
- [x] AC-3: `runner/` no longer exists; `_archive/runner/` holds the code, `e2e/`, the runner only tests and `tests/fixtures`. Archived suite run once, in parallel by `tests/fast.py`'s runner pointed at `_archive/runner/tests`: `Ran 997 tests in 126.9s, 74 failed` (923 pass). The 74 failures are all the frozen code finding its repo root one folder too low (`_archive/runner/pr.py:637` looks for `scripts/private-names.py` beside its parent folder, now `_archive/`): test_clean_branches 30, test_pr 19, test_reviews 5, test_insights 4, test_parallel_repo 3, test_cheap 2, test_model_split 2, test_one_command 2, test_adopt 1, test_checks 1, test_fewer_stops 1, test_runner_bugs 1, test_runner_copy 1, test_swap 1, 1 module load error (test_pr passed 33 of 33 on main). Not fixed: `_archive/` is frozen. `**Paths:**` of live specs rewritten (36 spec files; `runner/tests/<live test>` to `tests/...`, other `runner/...` to `_archive/runner/...`). can fail: a Paths line left on `runner/` makes `ref-check.py verify` list it (run with an empty map it lists 265).
- [x] AC-4: 23 runner specs moved with their verify, rationale and probes to `_archive/runner/docs/specs/`: 0004 0005 0006 0008 0009 0010 0017 0021 0022 0024 0025 0027 0032 0033 0034 0038 0039 0040 0041 0042 0044 0058 0066 (all `**Paths:**` under `runner/`; no open scope row links any of them; hand list: none). 4 briefs moved, each named by a moved spec: `0009-review-findings`, `fast-runner`, `finish-runner-today`, `runner-review-stack-2026-10-12`. No reviews were named. Links to moved files in live specs, `docs/architecture.md` and `docs/scope/scope.md` were rewritten. Grep outside `_archive/` and the history folders (`git grep -P "(?<![\w-])(?<!_archive/)runner/"`): one hit left, `claude-home/mods/chip-dash/plan.py:3` (docstring; the build was told to leave plan.py to 0072c). `bin/docs-pr.sh` read `runner` from the origin default branch; it now reads `_archive/runner` (live once this lands). Consumed handover files outside git are not touched. can fail: a grep hit outside the history folders; a link test failure in `tests/test_layout.py::test_links`.
- [x] AC-5 (part): `ref-check.py verify /tmp/0072a-snapshot.json --map-from-git main` prints `verify: 0 broken pointers`; `bin/install.sh --dry-run` ran clean; suite OK (above); `spec-paths.py --test` passed and `--spec 0001 0043 0056 0072` printed no `matches no` line. The regression-hunter report is the coordinator's step. can fail: any pointer left to a moved path.
- [x] AC-13: `tests/test_layout.py` skips `_archive/` in `test_links` and `test_old_paths`; scope links to moved specs and briefs carry the new path (`docs/scope/scope.md`). can fail: removing the skip turns `test_links` red (mutation below).

### Decisions of moved specs still in force (owner checks)
All 23 specs describe the retired wf runner (retired live 2026-10-22, scope row 90). A decision is listed only where a live file now carries it.
| Spec | Decision still in force | Live home |
|---|---|---|
| 0006 standing answers | per repo standing answers, asked once | `claude-home/rules/standing-answers.md`, `AGENTS.md` (`## Standing answers`) |
| 0066 waiting only by marker | only the ` · waits on you` marker makes a box wait | `claude-home/rules/scope-contract.md` |
| 0024 issues and mixed source of truth | `**Source of truth:**` header, issue read before planning | `claude-home/rules/scope-contract.md`, `claude-home/rules/when-to-switch-on.md` (issue reread) |
| 0027 several features of one repo | one worktree per feature, no overlapping `**Paths:**` | `claude-home/rules/when-to-switch-on.md` (parallel features) |
| 0032 review requests | a review of someone's PR is read only and posted only on the owner's yes | `claude-home/rules/when-to-switch-on.md` (review-isolated) |
| 0034 step brief | decisions agreed in chat go into the brief first | `claude-home/CLAUDE.md` (`### Context`) |
| 0010 design enforcement | UI work goes through the `design` pipeline and gate | `claude-home/CLAUDE.md` (`## UI / design work`) |
| 0009 headless verify | start the app, drive it in the browser, stop it | `claude-home/rules/when-to-switch-on.md` (app start and browser verify) |
| 0022 usage limit planning | new agent only under the 5 hour use limit | `claude-home/rules/when-to-switch-on.md` (start gates) |
| 0058 own status bar | bar drawn by our own code, not jjstack | `docs/specs/0059-wf-dash-band.md`, `claude-home/mods/chip-dash/` |
| 0004, 0005, 0008, 0017, 0021, 0025, 0033, 0038, 0039, 0040, 0041, 0042, 0044 | runner only (unattended loop, phone pings, queues, park policy, Telegram): nothing in force after the retirement | none needed |

### Mutations (tests added or changed)
- `scripts/ref-check.py --test`: `path:line` check off, red; "referrer names new path" rule off, red; fenced-block skip off, red (the first version stayed green here: its fenced path did not exist, fixed to an existing file); `SKIP_PREFIX` ignored, red; `<>` allowed in tokens, red; restored, green.
- `tests/test_layout.py`: `_archive/` removed from the `test_links` skip, red; `_archive/` removed from `HISTORY`, red; `tests` removed from `TOP`, red; restored, green.
- `tests/test_spec_paths.py`: `parents[1]` to `parents[2]`, red; restored, green.
- The other `parents[1]` edits (5 files) are read by the whole suite; not mutated one by one.

### Live-script tests copied from the archive (owner, 2026-10-22; AC-2 amended)
A regression check found archived tests that ran live scripts. New in `tests/`, each with root `parents[1]`, discovered by `tests/fast.py` (it globs `test_*.py`):
- `test_docs_pr.py` (from test_clean_branches `TestDocsPr`): refusals, lands, resync diverged, dirty tree kept, title and body, planted checker; new cases `test_scanners_missing_from_archive` and `test_attribution_scan` cover the `_archive/runner` line this commit changed. Rebuilt on a scratch repo whose origin carries `scripts/private-names.py` and `_archive/runner`, with its own fake gh.
- `test_repo_settings.py` (`TestRepoSettings`): check, set, first run.
- `test_fb_ask.py` (test_cheap `TestSelfCheck`): `fb-ask.py --test` and the rule/AGENTS.md check.
- `test_install.py` (test_swap `TestInstallStage`, test_runner_copy dry run): WF_STAGE (still in `bin/install.sh`), settings backup, hook replace rules, `--dry-run`.
- `test_extract.py` (test_insights `Extract`): redaction, since-last-report, refusals, propose.
Dropped as runner only: everything else in those files (the runner's report, queue, merge and finish code, `finish.swap`/`recover`, `install_runner`, `wf report --hook`).
Mutants (script backed up with cp, only that file run, then restored): docs-pr archive path back to `runner`, red (7 of 8); tracked-changes check off, red; attribution scan off, red. repo-settings `allow_merge_commit=true`, red (3 of 3). fb-ask `client_repo` refusal off, red; cheap-worker rule edited, red. install.sh WF_STAGE break off, red; hook `cmp` up-to-date off, red; dry run printing `runner/*.py`, red. extract.py email redaction off, red. All restored, green.

Not done in this PR: the regression-hunter report; the live checks of `~/.claude` links (ref-check ran with `--link-root` at the main checkout, no link points at a moved path); the 74 archived-suite failures above; `plan.py` docstring.

## 0072b (map cards, CLAUDE.md entry, AGENTS.md link)
Branch `feat/0072-map-and-entry`. Suite: `python3 tests/fast.py` gives 143 tests, 0 failed. `scripts/ref-check.py verify` against the pre-change snapshot: 0 broken pointers. `bin/install.sh --dry-run`: clean.

| AC | Evidence | can fail |
|---|---|---|
| AC-6 | `CLAUDE.md` is 52 lines: never-break rules, the 4 commands, a row pointing at `map/CLAUDE.md`, standing answers, agent skills, context files. `tests/test_layout.py` `test_readers` (under 200, opens "For an AI agent") reads it through the link. | can fail: a rewrite that drops the opening line, or grows past 200 lines. The 60-line limit itself is not asserted (the tightening edit was dropped by the coordinator); checked by `wc -l`. |
| AC-7 | `map/_meta/line-homes.md` pinned to c08534f. `tests/test_map.py` `test_every_old_line_has_a_home` and `test_homes_exist`. | can fail: row for old line 13 deleted, test red (mutant below). |
| AC-8 | `AGENTS.md` is mode 120000 to `CLAUDE.md`; `test_single_load` asserts CLAUDE.md is a regular file, AGENTS.md a symlink, target `CLAUDE.md`. | can fail: AGENTS.md as a plain copy, red; link to another file, red (mutants below). |
| AC-9 | `agents_link_bad()` in `scripts/private-names.py`, called first by `cmd_check_staged` (the pre-commit hook). `--test` block "AC-9": no AGENTS.md is a no-op, link passes, replaced file refused with the repair command, link to another file refused, repaired link passes. | can fail: `agents_link_bad` forced to False, the two refuse cases red. |
| AC-10 | `map/` has the catalog, CONTEXT, schema, 2 templates, 8 object cards, 5 process cards, effects page. `test_card_set` and `test_citations_exist` (runs `ref-check.py check` over every card). | can fail: a card citing `bin/sync-gone.sh`, red. |

### Mutations
- `test_single_load`: AGENTS.md replaced by a plain copy of CLAUDE.md, red (is_symlink); AGENTS.md linked to README.md, red (readlink); restored, green.
- `test_fb_ask` (reads the `fb-ask <task>` line from `map/objects/rules.md`): `[--local]` dropped from that line, red; restored (cp backup), green.
- `test_map`: line-homes row for line 13 removed, red; a card citing a missing `bin/` path, red; restored, green.
- `private-names.py --test` AC-9 block: see the AC-9 row. The full `--test` run crashes in this sandbox at an unrelated `install.sh` section (missing `settings.json` in its temp HOME), same on main; the AC-9 block was run alone with the later sections skipped.

### Left for after merge
- The AC-9 probe commit (replace the link with `sed -i`, expect refusal) and the `cmp` of the hook copy against `scripts/private-names.py` need `bin/install.sh` run for real; until then `~/.git/hooks` keeps the old copy, which does not check the link.
- Done 2026-10-22 after PR #167 merged: `.git/hooks/pre-commit` and `commit-msg` copied from `scripts/private-names.py` by hand (`cmp` equal; `bin/install.sh` was not run because it would have put the paused chain-catch Stop hook back live). Probe: in a throwaway worktree, `AGENTS.md` replaced by a plain copy of `CLAUDE.md`, `git commit` exit 1 with "AGENTS.md must be a symlink to CLAUDE.md (spec 0072 AC-9). Repair: rm AGENTS.md && ln -s CLAUDE.md AGENTS.md && git add AGENTS.md". PASS.
- AC-9 asks the check to land in a commit before the swap; the owner asked for one commit, so both are in it.
- Not run: the regression-hunter report (AC-5).

## 0072c (scope split)
Branch `feat/0072-scope-split`. 86 of 107 feature sections (every `· done` or `· dropped` one with no unticked box, plus whole `## Release` blocks left empty) moved from `docs/scope/scope.md` to `docs/scope/done.md`; the two Deferred ones sit under `## Deferred` there so `plan.py` still marks them deferred. `scope.md` links `done.md` under the intro. The at-a-glance table is untouched (other PRs tick rows there). Suite `python3 tests/fast.py`: 145 tests, 0 failed. `claude plugin test claude-home/mods/chip-dash`: 82 pass, 0 fail. `test_plan.py`: 11 OK. `ref-check.py verify` against the pre-move snapshot (`--map-from-git origin/main`): 0 broken pointers.

| AC | Evidence | can fail |
|---|---|---|
| AC-11 | `plan.py` run on a copy of main's `docs/` and on a copy of this branch's `docs/`: 102 features each; the 11 open features identical in order; per feature `next` and `command` identical; warnings identical. Features left in `scope.md` with a done or dropped tag (85, 90, 99) each still have an unticked box. | can fail: a section moved while it still held an unticked box would change that feature's `next` (None instead of the box), and the dict comparison would differ. |
| AC-12 | Same run: open count 11 and 11, built count (done, dropped, existing states) 91 and 91, the full feature set equal as JSON. `plan.py` reads `done.md` beside `scope.md`; `test_closed_features_in_done_md_still_count_as_built` moves feature 4 into `done.md` and asserts all states equal the unsplit run. | can fail: plan.py not reading done.md, test red (mutant below). |

### Mutations
- `test_closed_features_in_done_md_still_count_as_built`: `if os.path.isfile(done_md)` changed to `if False and ...`, red (feature 4 missing); restored from backup, green.

Docstring at `plan.py:3` no longer says the parser is `runner/wf.py`'s. Not run: the regression-hunter report.

## Phase 1 whole verify (2026-10-22)
Merged main at f97b743 (PRs #165, #167, #175 in). Snapshot re-created from commit 5ee24c1 in a throwaway worktree: `ref-check.py snapshot --repo <5ee24c1 tree> --link-root /home/santiago/claude-config` gave 691 pointers (271 text, 385 spec Paths, 33 live links, 2 settings.json strings), 98 already dangling left out.

- [x] AC-5 whole phase, ref-check: `ref-check.py verify <snapshot> --map-from-git 5ee24c1` exits 1 with 36 BROKEN lines (35 text, 1 spec-paths). The rule wants the referrer to name the new path; in all 36 the referrer no longer names the old path at all (checked by token search in the current referrer, `docs/scope/done.md` included for scope.md rows): 0 of 36 still name a missing path. 35 are pointers the 0072b/0072c rewrites dropped (old `AGENTS.md` text, scope rows moved to or trimmed for `done.md`, `README.md`, `docs/architecture.md`, `docs/NOTICE.md`). The last is `0035-readable-layout` Paths, now `_archive/runner/tests/` (exists; the tool compares it without the trailing slash). Judged: no dangling pointer, strict exit is a tool limit for dropped pointers. can fail: a doc still naming `runner/` or a Paths line left on a moved folder would show in the "STILL NAMES" check as a nonzero count (it was 0).
- [x] Live links: 33 links under `~/.claude` and `~/.local/bin` point into the repo (same 33 as the snapshot), 0 dangling (`os.path.exists` on each link, read only). can fail: a link to a moved file, such as one into `runner/`, counts as DANGLING.
- [x] `bin/install.sh --dry-run`: clean, lists copy, symlink, bin links (spec-paths, fb-ask, skill-scan, start-gates, design-check, issue-reread, review-isolated) all from `scripts/` and `claude-home/`; nothing written. can fail: a path in the installer to a moved file makes the plan print an error or a source path that does not exist.
- [x] `python3 -B tests/fast.py`: `Ran 150 tests in 12.2s, 0 failed, OK` (includes test_layout, test_map, test_plan, test_docs_pr, test_install). can fail: any of the layout, link or install tests turning red on a wrong move.
- [x] `ref-check.py --test`: `ref-check self check: ok`. `spec-paths.py --spec 0001 0035 0043 0056 0072`: no output, no `matches no` line. can fail: a spec Paths glob matching no file prints a `matches no` line.
- [x] Layout: top level is `_archive bin claude-home config docs map scripts tests`, `CLAUDE.md`, `AGENTS.md -> CLAUDE.md`, `README.md`, `LICENSE`; no `runner/`; `CLAUDE.md` 52 lines (AC-6 under 60). can fail: a leftover `runner/` folder or a regular-file AGENTS.md (test_single_load red).
- Not run: regression-hunter report (AC-5); `ref-check.py check` over all markdown reports 519 MISSING (only the tail was read; those seen are in specs naming old or planned paths); it is meant for map cards, not a gate.

## Phase 1 whole test (2026-10-22)
No uncommitted source changes; each part shipped its tests (see mutations above). No test added or changed here. Suite run on merged main: 150 tests, 0 failed. MUTATION CHECKED: 0.
