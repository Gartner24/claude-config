# 0072c. Scope split

## Summary
Third PR of phase 1. Closed rows of `docs/scope/scope.md` move to `docs/scope/done.md`, so the plan a chat loads holds only open work. Branch `feat/0072-scope-split`, stacked on 0072a while 0072a is unmerged (0072a changes scope links to moved files).

## Scope
Acceptance criteria AC-11 and AC-12 of [index.md](index.md); build plan tasks 8 and 9.

## Notes for the build
- Run the next box rule and the chip-dash plan pane test on the old file first, save their output, and compare after the split.
- `scope.md` stays the top file (scope contract), so `~/projects/docs/master-list.md:4` keeps working.
- Rationale: the 28k token plan is the largest single break of ICM's 2k to 8k per step rule (icm-research.md section 6).
