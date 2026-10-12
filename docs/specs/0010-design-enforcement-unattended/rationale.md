# 0010 rationale: design enforcement in `wf run`

## Context

The research settled that unattended frontend work must go through `design` and `design-gate`, never skipped (section 0 of the autonomous runner research). Architecture invariant 2 says a run never decides design, and lists an open gap: a `/develop` step can still change UI without a locked design.

Three facts from the code shape the problem:
- The `design` pipeline needs you in at least two places: `direction` proposes two options and waits when nothing is locked, and `preview` needs a message you typed after seeing screenshots at 1440 and 390. A phone ping is text only.
- Its Stop hook arms through a pointer file in `~/.claude`. Spec 0007's sandbox lets a call write only inside the repo, the git dir and caches, so under `wf run` the hook never arms.
- `design-gate` prefers the chrome-devtools browser, which only `/check verify` and debug calls get (spec 0009), and has shell fallbacks without it.

Without a decision, a `/develop` call can ship UI that was neither designed by you nor audited, and the morning review is the first place anyone sees it.

## Options considered

### Option 1: file check in `wf` before `/sync`, `design` kept out of calls

Calls park UI that has no locked design (`BLOCKED:`), `design` and `brand-system` are denied, `design-gate` runs in `/check verify`, and `wf` checks once before `/sync` that every changed frontend file has a passing report newer than it.

**Pros**: outside the model; one audit per feature, with the browser; no new call kind or storage; reuses spec 0008's `BLOCKED:` park.
**Cons**: a forgotten audit is found only at the end; "build or restyle" is the model's judgement.

### Option 2: check after every call

The scope row's first wording: any call that changed frontend files needs a newer report before the next call.

**Pros**: fails at the step that caused it.
**Cons**: `/develop` must audit without a browser; every `/debug` edit means another full audit; more calls hit the timeout.

### Option 3: `wf` runs its own gate call before `/sync`

A new call kind that invokes `design-gate` whenever the report is missing or stale.

**Pros**: the audit is never forgotten.
**Cons**: a new call kind, browser wiring for it, and an amendment to spec 0009, to fix a case the park already reports.

### Option 4: make the design Stop hook work headless

Move the ledger pointer into the repo so the hook arms inside the sandbox.

**Pros**: the full ledger (critique bar, skills invoked) applies to unattended work.
**Cons**: only matters if `design` runs in a call, which the direction and preview steps make impossible without you; edits `ledger.sh`, `gate.sh` and their tests for no unattended gain.

## Rationale

Option 1 because the design pipeline cannot finish without you, so the honest unattended path is: park what needs a direction, audit what was built within a locked one. Checking once before `/sync` puts the audit where the browser is and avoids paying for a full blind audit after every edit. The check believes only files, like the box check, which keeps invariant 7. Parking `design_gate` on a forgotten audit costs a morning look, which is cheaper than Option 3's new call kind. You chose each part (park, before `/sync`, drop the hook, fixed extension list, prompt line with `BLOCKED:`, all four lock sources, PASS or PASS WITH FINDINGS, nearest report, prompt driven audit, park on FAIL, reports without a browser count) on 2026-10-12, then applied the cross check fixes the same day (merge base instead of a start snapshot, last verdict line, any passing candidate up the tree, audit again after the last edit, rule 14a, skip dirs, `app` dropped, lock per folder, deny limited to the two pipeline skills).

Decided here without a question:
- Test files and anything under `.design/` are not frontend: tests are not UI, and the report folder must not trip its own check. Runner up: count tests too, which would demand an audit for a test only change.
- Changed files from the merge base with `main`, not a snapshot at run start: a start snapshot reset on every rerun, so a parked `design_gate` cleared itself on the next run (cross check). The merge base keeps no state and is already the `/test` base in spec 0009. Runner up: a per feature snapshot saved in the state folder, which is new storage with its own cleanup rules.
- `st_mtime_ns` for freshness: the same rule as the design gate (no file newer than the report). Its failure is a false park, never a false pass. Runner up: hash the files into the report, which needs `design-gate` to change.
- Deny `Skill(design)` and `Skill(brand-system)` instead of only a prompt line: makes "no direction unattended" mechanical. Runner up: prompt only.
