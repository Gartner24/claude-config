# Verify: fewer avoidable stops · spec 0045

Run on 2026-10-15 against commit e43dc92 (feature commit ab9c3a9, then the suite gate fix). The runner code
(`runner/run.py`, `runner/plain.py`, `runner/pr.py`, `runner/wf.py`) is unchanged since ab9c3a9. Every scenario drives
the real `wf run` (runner/wf.py) on a temp repo, with the test stub standing in for `claude -p`. The plans copy the box
shapes of features 46 and 47.
Script: `python3 -B docs/specs/0045-fewer-avoidable-stops/probes/verify_scenarios.py` (V6 scans `9ef7f1b..HEAD`,
every commit this feature added on top of its planning commit).

## Commands

- [x] V1, feature 46 shape: the verify call says `LEFT TO BOX: After 3 days, run the report...` and `CAN FAIL CHECKED: 4` -> the verify prompt lists only that open waiting box between `BEGIN BOXES-DATA-0` / `END BOXES-DATA-0` (the ticked `Install it live` box is left out), calls go `/check verify m`, `/test m`, and the only question is the waiting box's own (`waiting`), no verify park -> AC-1
  can fail: `later_owed` returns nothing, so no box list reaches the prompt (seen red on ab9c3a9).
- [x] V2, feature 47 shape: every check left to the box, `- **LEFT TO BOX:** Install it live after the merge...` and `CAN FAIL CHECKED: 0` -> the verify passes on to `/test c`, the only question is the waiting box's own -> AC-1
  can fail: the `left` gate is dropped, so `CAN FAIL CHECKED: 0` parks `unchecked` (seen red on ab9c3a9).
- [x] V3: `LEFT TO BOX: some box I invented` with `CAN FAIL CHECKED: 0` -> parks `unchecked` after the verify call and its one retry; `/test` never runs -> AC-1
  can fail: the runner takes any box name, so the verify passes and `/test c` runs (seen red on ab9c3a9).
- [x] V4: a verify that fails with `UNREACHABLE: probe P1 needs a real claude -p` -> question `verify_failed` offers `1 skip`, `2 try again`; detail starts `could not reach: probe P1 needs a real claude -p; ` and keeps the failure text; why line `a retry runs in the same sandbox, so it cannot reach this either` -> AC-2
  can fail: the option swap is dropped, so `try again` comes first (seen red on ab9c3a9).
- [x] V5: an ordinary failing verify (no UNREACHABLE line, through the debug loop) -> question offers `try again` first, detail without `could not reach` -> AC-2
  can fail: skip is always put first (seen red on ab9c3a9).
- [x] V6: the real push scan (`pr.attribution_hits`) over all 3 feature commits' messages and their 637 line diff, which now also holds the `test_pr.py` fix -> no hits; the same diff with one whole trailer line planted at a line start -> exactly one hit, at `runner/tests/test_fewer_stops.py:17` -> AC-3
  can fail: the scan stops reading added lines at the start of a line (`LINE_START = ()`), so the planted trailer passes (seen red again on e43dc92 after the planting was anchored to a line start).
- [x] `python3 -B -m unittest discover -s runner/tests -p test_fewer_stops.py` -> 13 tests OK -> AC-4
- [x] `python3 runner/tests/fast.py` (whole suite) -> 840 tests, 0 failed. The earlier failure (spec 0046's Paths line naming an unbuilt test while Accepted) is fixed by e43dc92.

## Acceptance-criteria coverage

- AC-1: V1, V2, V3 met
- AC-2: V4, V5 met
- AC-3: V6 met; the AGENTS.md line is in place
- AC-4: 13 feature tests pass
- Suite gate: passes

## Notes for review

- The V6 planting used to pick the first `+TRAILER = ` in the diff. Once the probe file itself was committed, that first match sat mid line inside the probe, so the planted phrase was not at a line start and the scan rightly ignored it. The planting now anchors on a line start. A probe fix, not a runner fault.
- e43dc92 widens `runner/tests/test_spec_paths.py`: an Accepted spec whose plan feature is still open may name files its build will create. That relaxes a corpus test outside this spec's own criteria; worth a look in review.
