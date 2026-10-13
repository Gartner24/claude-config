# Scope: wf e2e fixture

**Workflow:** Beta
**Source of truth:** scope
**Autopilot:** allowed

A tiny repo `runner/e2e/run.py` copies into a temp folder to run `wf run` end to end on the real claude (spec 0014 AC-5).

## At a glance

| # | Feature | Release | Status |
|---|---|---|---|
| 1 | Add function | Release 1 | in-progress |

## Release 1

### 1. Add function · in-progress · auto
One function `add(a, b)` in `calc.py` that returns the sum, and its unittest.
**Done when:** `python3 -m unittest` passes in the repo root.
- [x] Design it (spec): `/architect add function`
- [ ] Build it: `/develop add function`
- [ ] Verify it: `/check verify add function`
- [ ] Test it: `/test add function`
- [ ] Sync docs: `/sync add function`
Spec [0001](../specs/0001-add-function.md)
Source: the wf end to end fixture (spec 0014 AC-5 in claude-config).
