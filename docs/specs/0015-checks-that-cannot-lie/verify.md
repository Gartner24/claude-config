# 0015 verify

## Before accept

- Rule files under `~/.claude/rules/` load in headless `claude -p` calls: confirmed by the spec 0012 headless `/scope` probe (2026-10-12), which followed `rules/scope-contract.md`. No new probe needed for the loading itself.

## Probes after build (AC-10, run by you with `!`)

- P1 planted verify step: record date, Claude Code version, pass or fail.
- P2 `/sync` stale spec warning: record date, version, pass or fail.
- P3 brief item dropped by a spec, named by the cross check: record date, version, pass or fail.
- 2026-10-13, Claude Code 2.1.296:
  - P1: the planted `test -f calc.py` step was dropped and named, the real step carried a `can fail:` note, the report ended `CAN FAIL CHECKED: 1`. The probe printed `FAIL a can fail note per step` because it required 2 notes, which only holds when the planted step is rewritten; the rule also allows dropping it. The probe now requires one note per counted step. PASS on that reading.
  - P2: PASS (5 of 5 lines; `src/a.py` named for spec 0001, nothing for 0002, spec 0001 unedited).
  - P3: PASS (3 of 3 lines; the dropped retry cap named with the brief, spec unedited).

# Verify: checks that cannot lie · spec 0015 · updated 2026-10-13
_Steps derived from spec 0015 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [x] `python3 -m unittest discover -s runner/tests` -> all pass, `test_checks` included -> AC-4
- [x] `python3 -B -m unittest test_checks` from `runner/tests` with the rule 11a park line in `runner/run.py` replaced by `if False:` (backup first, restore after) -> the 5 park tests go red -> AC-4
- [x] Same with the changed test file branch forced to 0 -> `test_mutation_zero_test_changed` goes red -> AC-4 (value: test file changed, from the spec 0008 snapshot)
- [x] Same with own box detection replaced by "any box state changed" -> `test_milestone` goes red -> AC-4 (value: progress, the box ticked after the call)
- [x] `grep -c "CAN FAIL CHECKED\|MUTATION CHECKED" runner/run.py` shows the two prompt sentences and two patterns; `test_run.TestHappyPath.test_argv` pins the prompt text -> AC-4
- [x] `python3 scripts/spec-paths.py --test` -> `all passed`; flipping the `--spec` skip or the `Accepted` filter makes it fail -> AC-6 (values: accepted, globs, own specs, changed files on a branch and on main, specs folder)
- [x] `python3 scripts/spec-paths.py --spec 9 --spec 0009` in any repo -> same output both ways; `--spec 12345` exits 2; run outside a git repo exits 1 with `spec-paths: ` -> AC-6
- [x] `./install.sh --dry-run` -> prints `spec-paths -> scripts/spec-paths.py` and its `ln -sfn` line -> AC-6
- [x] `python3 -B -m unittest test_spec_paths` from `runner/tests` -> every spec top file has one `**Paths:**` line right after `**Status**:`, every glob matches a real file; deleting one backfilled line makes it fail with the count -> AC-5, AC-8
- [x] `rules/check-gates.md` exists, opens with "beats skill text", holds sections 1 to 4 (AC-2, AC-3, AC-5 plus AC-7, AC-9); `NOTICE.md` lists it and `scripts/spec-paths.py`; no non ASCII character but the middle dot -> AC-1
- [x] `git diff --stat` shows no file under a vendored skill (`scope`, `architect`, `develop`, `check`, `test`, `sync` are not in this repo) -> AC-1

## Waits on you
- [x] `cp ~/claude-config/rules/check-gates.md ~/.claude/rules/check-gates.md`, then `./install.sh` -> AC-1, AC-6 (closed 2026-10-13 by wf finish)
- [x] Run with `!`: `python3 docs/specs/0015-checks-that-cannot-lie/probes/p1-verify-can-fail.py`, `p2-sync-stale.py`, `p3-brief-check.py`; each prints PASS lines; record under "Probes after build" -> AC-2, AC-3, AC-7, AC-9, AC-10

## Acceptance-criteria coverage
- AC-1 rule file and NOTICE steps · AC-2 probe P1 · AC-3 rule section 2 (probe P1 covers the verify half; the /test half is followed in chat) · AC-4 test_checks and its mutants · AC-5, AC-8 test_spec_paths · AC-6 spec-paths --test, flags, install dry run · AC-7 probe P2 · AC-9 probe P3 · AC-10 the three probe scripts
