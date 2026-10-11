# Scope: contract

The canonical scope from spec 0003.

**Build approach:** Skateboard (each stage is usable on its own).
**Workflow:** Beta (after `/develop`: `/check verify`, then `/test`).
**Source of truth:** scope
**Autopilot:** off

### 3. Skipped tail · in-progress
- [x] Build it: `/develop skipped tail`
   - [x] Only milestone · skipped
- [x] Test it: `/test skipped tail` · skipped
   - [x] Child of a skipped parent · skipped

### 4. Headless step loop · in-progress · auto
- [x] Design it (spec): `/architect headless step loop`
- [ ] Build it: `/develop headless step loop`
   - [x] Lock per repo (AC-3)
   - [ ] Budget caps (AC-4)
- [ ] Verify it: `/check verify headless step loop`
- [x] Test it: `/test headless step loop` · skipped
