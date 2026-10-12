# 0010. Design enforcement in `wf run`

**Date**: 2026-10-12
**Status**: In Progress
**Amends**: [0007](../0007-push-guard/index.md) AC-5 deny list gains `Skill(design)` and `Skill(brand-system)`. [0008](../0008-failure-park-policy/index.md) AC-1 park set gains `design_gate`; its classification order gains rule 14a.

## Summary

A run never picks a design. When a step would build or restyle UI and no locked design covers it, the call builds none of it and the feature parks. When the branch has changed frontend files, `wf` checks before `/sync` that each one is covered by a passing `design-gate` report written after it, and parks the feature when one is not. The check runs in `wf` (outside the model) and reads only files. The full `design` pipeline never runs unattended, so its Stop hook is not needed under `wf run`.

## What you're agreeing to

- UI work with no locked design (design.md, brand-system.html, a `.design/tokens.css` with `.design/reference-lock.md`, or a spec naming it) parks as `blocked`. You run `design` yourself, then run again.
- A run closes only when every frontend file changed on the branch (since it left `main`) has a passing `design-gate` report newer than it. Otherwise it parks `design_gate` and `/sync` does not run. A rerun cannot skip this.
- The audit is expected in the `/check verify` call (it has the browser when the repo names an app). A report made without a browser still counts if its verdict passes.
- Calls can never invoke `design` or `brand-system`. The design Stop hook stays as it is, for your own sessions.

## Requirements

**User stories**:
- As you, I want a headless run that changed UI to close only after a blind design audit passed, so that nothing reaches my morning review unaudited.
- As you, I want UI with no locked design to wait for me, so that no run picks a direction I would not have picked.

**Acceptance criteria**:
- **AC-1** (changed files): the base is found as in spec 0009 AC-9: the first of `main`, `master` for which `<git> rev-parse --verify --quiet refs/heads/<b>` succeeds, then `<git> merge-base HEAD <b>`, with the absolute `git` from spec 0007 AC-6. Changed files: the paths from `<git> diff --name-only --diff-filter=ACMR -z <base>` plus `<git> ls-files --others --exclude-standard -z`, kept when the path passes the frontend rule (AC-2) and is a regular file (`os.path.isfile`, not a symlink: `os.path.islink` false). With no base, every path from `<git> ls-files -co --exclude-standard -z` that passes the same filter counts as changed. Deleted files never count. Your own uncommitted UI edits on the branch count too.
- **AC-2** (frontend rule): a path is frontend when it is not a test file (the spec 0008 test file constant), no path segment is one of `FRONTEND_SKIP_DIRS` (`.design`, `dist`, `build`, `.next`, `node_modules`), its basename does not contain `.min.`, and either its extension (lower cased) is in `FRONTEND_EXT` (`.html .htm .css .scss .sass .less .jsx .tsx .vue .svelte .astro`), or its extension is in `FRONTEND_SCRIPT_EXT` (`.js .mjs .ts`) and it has a path segment in `FRONTEND_DIRS` (`components`, `pages`) or starts with `FRONTEND_PREFIX` (`src/ui/`). All are constants in `runner/run.py`. Script files elsewhere (`lib/ui.ts`, an `app/` folder) are not frontend, on purpose.
- **AC-3** (check before `/sync`, rule 14a): the check runs once, after rules 1 to 11 of the spec 0008 classification order, when rule 14 decides a `sync` call is next (the next box is in another feature, or no box is left), and before that call starts. A retried or resumed `sync` call never runs it again; a run that ends before reaching rule 14 never runs it. With no changed files (AC-1), the run goes on to `/sync`. For each changed file, its candidate reports are every `<dir>/.design/audit-report.md` that exists, for `<dir>` from the file's own folder up to the repo root (`c.path`), never above it. The file is covered when at least one candidate has a passing verdict (AC-4) and an `st_mtime_ns` not lower than the file's. Otherwise its problem is the first that applies: `no report` (no candidate), `older than the file` (some candidate passes, but every passing one is older), or the verdict of the nearest candidate (`verdict FAIL`, `verdict STOP`, `no verdict`). Any uncovered file parks `design_gate` and no `sync` call is made. Detail: `<n> frontend file(s) not covered by a passing design-gate report: `, where `<n>` is the number of uncovered files, then `<path> (<problem>)` for the first 5 in path order, joined with `, `, through `flat()`, first 300 characters.
- **AC-4** (verdict): the LAST line of the report matching `^\s*\**verdict:\**\s*(PASS WITH FINDINGS|PASS|FAIL|STOP)\s*(\(.*)?$` (case insensitive) that contains no `|`, the report read as UTF-8 with errors replaced. `PASS` and `PASS WITH FINDINGS` pass. No such line, or an unreadable report, reads as `no verdict`. The unfilled template line (`verdict: PASS | PASS WITH FINDINGS | FAIL | STOP`) never matches.
- **AC-5** (prompt lines): the unattended prompt gains two lines.
  1. "If this step would build or restyle a user interface and no locked design covers it (a design.md, a brand-system.html, or a .design/tokens.css next to a .design/reference-lock.md, in the folder of that UI or any parent up to the repo root, or a spec under the specs folder that names this UI's design source and composition), build none of that UI, and end with BLOCKED: no locked design for <what>. Never invoke the design or brand-system skills."
  2. "Frontend files are <the AC-2 rule in words>. In every /check verify step of a feature whose branch changed frontend files, invoke the design-gate skill when any changed frontend file has no passing .design/audit-report.md newer than it, on the lowest folder that holds all the changed frontend files; fix its Must fix items within its own pass budget, and invoke design-gate again after your last frontend edit. In any other step that changes frontend files, do the same only when this feature has no open /check verify box left. wf will not close the feature without a passing report newer than every changed frontend file."
  The model judges whether a spec names the UI's design source and composition (your answer, 2026-10-12). The `BLOCKED:` line parks `blocked` through spec 0008 AC-4; no new marker.
- **AC-6** (skill denies): every call and resume gets `Skill(design)` and `Skill(brand-system)` in `--disallowedTools`, added to the spec 0007 AC-5 list. Only these two pipeline skills are denied: the other style skills (`impeccable`, `frontend-design`, the register lenses) build inside a locked design, and line 1 of AC-5 covers the case with none.
- **AC-7** (record): `run.json` gets `design`: null until the AC-3 check runs, then `{"base": sha or null, "changed": [paths], "reports": {report path: verdict}, "problems": [{"path": p, "problem": text}]}`, where a verdict is `PASS`, `PASS WITH FINDINGS`, `FAIL`, `STOP` or `no verdict`, all paths relative to the repo, lists in path order. The check is not a call: no call record, nothing counted toward `--max-calls`. Each run has its own `run.json`, so a rerun records its own check.
- **AC-8** (park): `design_gate` is a park in the spec 0008 AC-1 sets (`parked: true`, `parked: design_gate: <detail>`, exit 6). Nothing pings you (architecture invariant 4).
- **AC-9** (probes): `verify.md` records P1 (a `context: fork` skill runs in `claude -p` and writes `.design/audit-report.md`, run 2026-10-12). P2 to P4 run through `wf run` after this feature is built on top of specs 0007 and 0008: (P2) a scratch repo feature whose `/develop` box writes a `.tsx` file and whose `/check verify` box runs `design-gate` reaches `/sync`, which shows the forked skill can create `.design/` and write the report inside the sandbox; (P3) a call asked to invoke `design` is denied, and the same call can still invoke `design-gate` (the deny is not a prefix match); (P4) a `/develop` box asking for a new page in a repo with no locked design parks `blocked` with `no locked design`. If P2 or the `design-gate` half of P3 fails, this spec goes back to `/architect`.

## Decision

**Chosen option**: Option 1: a file check in `wf` before `/sync`, with the design pipeline kept out of unattended calls.

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch**: no new storage. In `run.json`: `design` (AC-7).

**Where it sits in the spec 0008 classification order**: rule 14a, between rule 14's decision that a `sync` call is next and that call (AC-3).

**API surface** (CLI only):
| Surface | Inputs | Output | Errors |
|---|---|---|---|
| before the `sync` call | `git merge-base`, `git diff`, `git ls-files`, `.design/audit-report.md` files | `design` in `run.json`, then the `sync` call | park `design_gate: <detail>` |
| each call and resume | | prompt with the AC-5 lines, `--disallowedTools` with AC-6 | park `blocked: no locked design for <what>` (spec 0008) |

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| check | base | spec 0009 AC-9 rule, absolute `git` (spec 0007 AC-6) |
| check | changed files | `git diff --name-only --diff-filter=ACMR -z <base>` plus untracked files; with no base, `git ls-files -co --exclude-standard -z` |
| check | frontend or not | AC-2 constants in `runner/run.py`, spec 0008 test file constant |
| check | candidate reports | every `.design/audit-report.md` from the file's folder up to `c.path` |
| check | fresh or stale | `os.stat().st_mtime_ns` of the file vs each passing candidate |
| check | verdict | AC-4 pattern, last matching line |
| check | park detail | AC-3 format, `flat()`, 300 characters |
| call | locked design meaning | AC-5 line 1 (your answer, 2026-10-12) |
| call | audit folder | lowest folder holding the changed frontend files, worked out by the call (AC-5 line 2) |
| call | skill denies | AC-6 constants |

**Key invariants**:
- `wf` writes nothing in the repo; the check only reads files.
- No `sync` call starts while a frontend file changed on the branch lacks a passing report newer than it, whichever run changed it.
- No unattended call runs `design` or `brand-system`, so no run picks a direction (architecture invariant 2).

**Security model**: the check is outside the model and believes only the files, like the box check (architecture invariant 7). A call can still write a fake report; that is the same threat model as spec 0007 (an accidental or injected shortcut, not a model working to cheat), and `design-gate` runs forked and blind, so the call that built the UI does not grade it. Accepted, no further hardening.

**Configuration required**: none.

**Critical test scenarios**:
- Rule: `a.tsx`, `styles/x.scss`, `src/components/b.ts`, `src/ui/c.ts`, `app/page.tsx` are frontend; `app/models.ts`, `src/lib/d.ts`, `x.test.tsx`, `.design/e.html`, `dist/app.css`, `vendor.min.css`, `README.md` are not, verifies **AC-2**
- No UI: a branch whose changes are only `.py` files reaches `/sync`, `design.changed` is `[]`, verifies **AC-3**, **AC-7**
- Missing: the fake claude writes `src/components/Nav.tsx` in `/develop`, no report anywhere; the run parks `design_gate` with `(no report)`, no sync call is made, `parked: true`, verifies **AC-3**, **AC-8**
- Passing: the same plus a later call writes `.design/audit-report.md` ending `verdict: PASS WITH FINDINGS`; the run reaches `/sync`, verifies **AC-3**, **AC-4**
- Stale: a passing report written, then a later call edits the `.tsx` again; parks `(older than the file)`, verifies **AC-3**
- Rerun: a run parks `design_gate`; a second run on the same branch whose next box leads straight to `/sync` parks again, verifies **AC-1**, **AC-3**
- Verdicts: last line `verdict: FAIL`, `**verdict:** stop`, a report with no verdict line, and a report holding only the unfilled template line each park with the matching problem; `verdict: pass (2 should fix)` passes; a report with `verdict: FAIL` then a later `verdict: PASS` passes, verifies **AC-4**
- Candidates: `apps/web/.design/audit-report.md` passing covers `apps/web/src/a.tsx`; a FAIL report in `apps/web/src/.design/` plus a passing root report newer than the file still covers it; a changed `apps/admin/b.tsx` with only the `apps/web` report parks `(no report)`; a report above the repo root is never read, verifies **AC-3**
- Base: committed and uncommitted `.tsx` changes on a branch off `main` both count; a file changed on `main` before the branch point does not; with no `main` or `master`, every frontend file counts and `design.base` is null, verifies **AC-1**
- Argv: every call and resume carries the AC-5 lines and both AC-6 denies, verifies **AC-5**, **AC-6**
- Blocked: a result ending `BLOCKED: no locked design for the pricing page` parks `blocked` with that text, verifies **AC-5**
- Order: a `VERIFY FAIL: debug` on the last verify box runs the debug call first; the check runs only when rule 14 picks `/sync`; a retried `sync` call does not rerun it, verifies **AC-3**
- Real claude: P1 to P4 in `verify.md`, verifies **AC-9**

## Build plan

Skateboard: each step leaves `wf run` usable. Specs 0007, 0008 and the 0009 AC-9 base helper are built first (this spec extends the 0007 deny list, the 0008 park set, order and `BLOCKED:` reader, and reuses the 0009 base).

1. Frontend rule constants, `frontend_changed()` (base, diff, untracked, filter), `design_problems()` (candidates, mtime, verdict) with unit tests, satisfies **AC-1**, **AC-2**, **AC-4**
2. Rule 14a before the `sync` call, park `design_gate` in the 0008 park set, `design` in `run.json`; fake claude tests for missing, passing, stale, rerun, candidates, base and order, satisfies **AC-3**, **AC-7**, **AC-8**
3. The two prompt lines and the two skill denies on calls and resumes; argv and `BLOCKED:` tests, satisfies **AC-5**, **AC-6**
4. P2 to P4 through `wf run` on a scratch repo, recorded in `verify.md`, satisfies **AC-9**

## Consequences

**Positive**:
- Architecture invariant 2's open gap closes: UI without a locked design waits for you, and UI with one is audited before the feature closes.
- One file check outside the model, no new storage, no new call kind; a rerun cannot reset it.

**Negative / tradeoffs**:
- A UI feature with no `/check verify` box relies on its last UI changing call running `design-gate`; if it does not, the feature parks at the end, after all the build work.
- `design-gate` can take up to 3 passes of 20 minutes inside a `/check verify` call; with the default 60 minute `--call-timeout` that call can park `call_timeout`. Raise `--call-timeout` for UI heavy runs.
- A report made without a browser (no `app start` and `app url`) has no perf numbers or reference screenshots and still counts.
- Freshness is by timestamp: a formatter or hook that rewrites a frontend file after the audit, even with the same content, parks `design_gate` (a false park, never a false pass).
- The base is the local `main` or `master`: a stale local `main`, a branch cut from another feature branch, or your own uncommitted UI edits widen the set that needs an audit. With neither branch, every frontend file needs one.
- A small UI fix where no locked design covers it depends on the model judging "build or restyle"; a call may park something you would have let through.
- A call could write a passing report without auditing; accepted under the spec 0007 threat model.

**Neutral**:
- The design Stop hook is unchanged and stays for your own sessions; its pointer in `~/.claude` cannot be written inside the 0007 sandbox, which no longer matters because `design` is denied there.
- Scope row 9 drops "the Stop hook runs headless" and its Done when is reworded to the AC-3 check.

## Follow-up

- [ ] Spec 0007 and 0008 headers get `Amended by: 0010` when this is accepted; `/sync` owns those lines.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
