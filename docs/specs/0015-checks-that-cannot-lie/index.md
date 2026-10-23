# 0015. Checks that cannot lie

**Date**: 2026-10-13
**Status**: Accepted
**Paths:** `claude-home/rules-on-demand/check-gates.md`, `tools/scripts/spec-paths.py`, `tools/bin/install.sh`, `_archive/runner/run.py`
**Amends**: [0008](../../../_archive/runner/docs/specs/0008-failure-park-policy/index.md) (classification order gains rule 11a, the `unchecked` park), [0011](../0011-build-decision-queue/index.md) (AC-9 park set gains `unchecked`).

## Summary

Three rules that stop the workflow from fooling itself, kept in one new rule file so a pull of the vendored skills cannot erase them. A verify step or a test must be able to fail on broken code, and the report says how; under `wf run`, a passing `/check verify` or `/test` without that proof parks. Every spec lists the files it covers, and `/sync` warns when a change touched the files of another accepted spec. Cross checks compare the plan with the brief and list anything agreed that it dropped.

## What you're agreeing to

- `/check verify` names, for every step, the break that would make it fail; a step that would pass on broken code is rewritten, never reported as a pass.
- `/test` mutation checks every new or changed test (break the code, watch it go red, restore), and the report says it did.
- Under `wf run`, a `/check verify` or `/test` call that ticks its box without its `CAN FAIL CHECKED:` or `MUTATION CHECKED:` line parks `unchecked`.
- Every spec gets a `**Paths:**` line (specs 0001 to 0015 backfilled), and `/sync` runs a new `spec-paths` command and passes on its warnings.
- `/architect` cross checks and `/scope` writes list anything the row's brief agreed that the plan drops; you decide each one.

## Requirements

**User stories**:
- As you, I want a green verify or test to mean the code works, not that the check could not fail.
- As you, I want to hear when a change quietly makes an accepted spec stale.
- As you, I want decisions agreed in chat to survive into the spec and the scope.
- As you, I want all three to survive an update of the vendored skills.

**Acceptance criteria**:
- **AC-1** (where it lives): one new rule file `rules/check-gates.md` in this repo, live at `~/.claude/rules/check-gates.md` (always loaded, headless calls included, like `rules/handoff.md`), opening with a line that it beats skill text. It holds AC-2, AC-3, AC-5, AC-7 and AC-9. `NOTICE.md` lists it as authored. The repo copy is written by the build; the live copy is a step you do yourself (`~/.claude` is outside a call's reach). No vendored skill file is edited.
- **AC-2** (verify steps can fail): `/check verify` writes, for every step it reports, a `can fail: <the break that would make this step fail>` note in its report. A step whose expected result would still hold on broken code (it checks only that a file exists, that a command exits 0 with no assertion on its output, reads back a value the step itself just wrote, or greps for text the change itself added) is rewritten into one that observes the behavior, or dropped and named as dropped; it is never counted as a pass. When the verify passes, its final message ends with one line `CAN FAIL CHECKED: <n>`, `<n>` the number of steps that passed this check.
- **AC-3** (tests can fail): `/test` mutation checks every test it adds or changes (older tests the feature relies on are not rechecked; they were checked when written, and a whole suite pass per call is too slow, agreed 2026-10-13 as a narrowing of brief item 7), per `rules/lessons.md` (back up the file, break the behavior the test claims to cover, run only that test file, see that test go red, restore, confirm green). A test that stays green on its mutant is fixed or removed before the report. The report lists each test with its mutant in one line. When the suite passes, the final message ends with one line `MUTATION CHECKED: <n>`, `<n>` the number of tests checked (0 when no test was added or changed).
- **AC-4** (wf checks the line): a new classification rule 11a in `runner/run.py`, right after spec 0008 rule 11 (`VERIFY FAIL:`) and inside the kind `box` path, before the kind `sync` return and the missing heading return: a kind `box` call whose command is `/check verify` (first two words) or `/test` (first word), whose own box is ticked in the reread scope after the call (matched by position and text, as spec 0014 AC-4 matches boxes; a milestone tick or a tag edit alone is not progress), is checked against the last result of the call after its retries and resumes. Two constants in the `BLOCKED` line shape (leading `[ \t>*-]*`, optional bold): `CAN_FAIL = ...CAN FAIL CHECKED:\**[ \t]*(\d+)` and `MUTATION = ...MUTATION CHECKED:\**[ \t]*(\d+)`, the last matching line counts. The call parks `unchecked` when the line is missing, when a verify line says 0, or when a test line says 0 while a test file changed during the call (test files and their hashes from the spec 0008 AC-3 snapshot, taken before each `/test` box call). Detail: `<box text> ticked without a valid <MARKER> line; untick it to rerun, or wf unpark to accept`. A call that asks a decision, ends `BLOCKED:` or `VERIFY FAIL:`, or ticks nothing is decided by the earlier rules and needs no line; a debug call never needs one, and the verify rerun after it needs its own. `unchecked` is a recorded park (spec 0011 AC-10). The unattended prompt gains the two end line instructions. A pass sets the call record's `marker` to `can_fail_checked` or `mutation_checked` (never overwriting `blocked` or a `verify_fail_*` value, which the earlier rules set first) and a new `checked_n` int, else null.
- **AC-5** (`**Paths:**` line): every spec's top file (a flat `NNNN-*.md`, or `NNNN-*/index.md`; never `rationale.md`, `verify.md` or a child spec) carries one line right after `**Status**:` and before any `**Amends**` or `**Amended by**` line: `**Paths:**` then repo relative globs in backticks, comma separated (`fnmatch` syntax, `**` allowed), naming the code and config the spec governs, never `docs/`. `/architect` writes it on every new spec and updates it on every amendment. A spec that governs no file writes `**Paths:** none`.
- **AC-6** (`spec-paths`): `scripts/spec-paths.py` (Python stdlib, argument lists only), linked by `install.sh` to `~/.local/bin/spec-paths` as `wf` is. Run inside a repo, it finds the specs folder (`docs/specs/`, else `.workflow/specs/`), reads every spec top file (AC-5 shapes only) whose `**Status**:` starts with `Accepted` and whose `**Paths:**` is not `none`, and compares its globs with the changed files. `--spec NNNN` (repeatable, 4 digits, leading zeros optional) names the specs of the feature being synced: they are left out of the warnings. Changed files: on a branch other than `main` or `master`, the files changed since the merge base with `main` (else `master`); on `main` or `master`, the files changed since the parent of the oldest commit that added any named spec's top file (`git log --diff-filter=A`), or, with no `--spec`, `HEAD`'s commit; in both cases plus uncommitted and untracked files (`git ls-files -mo --exclude-standard`). It prints one line per hit, `warning: <file> touches accepted spec <NNNN> <title> (<glob>)`, sorted, or nothing, and exits 0 either way; a git failure prints `spec-paths: <error>` and exits 1; a bad flag exits 2. `--test` runs its self checks on temp repos and exits 0 only when all pass.
- **AC-7** (`/sync` passes it on): the rule tells `/sync` to run `spec-paths --spec NNNN` once per 4 digit spec number linked (`specs/NNNN-`) on the synced feature's heading block (its pointer line and `Spec` line) before it reports, and to copy every warning line, or the error line on exit 1, into its report under `Specs possibly stale`. `/sync` never edits those specs and never stops on a warning or an error; deciding is yours (`/architect`).
- **AC-8** (backfill): specs 0001 to 0015 each get their `**Paths:**` line, built from the files their own build plans name, kept as narrow as those files (no folder wide glob when files are named). Many runner specs share `runner/run.py`, so a runner change warns about several specs; that noise is accepted.
- **AC-9** (brief check): the rule tells `/architect` to give its cross check the `## Agreed so far, do not ask again` section of the brief that the feature's scope row names on its `Source:` line (when there is one), and to list every agreed item the spec drops or weakens as a gap in the cross check gaps panel, with a recommended fix. It tells `/scope`, before it writes a row whose `Source:` names a brief, to compare the row with that section and ask about every dropped or weakened item, with a recommended answer, before writing. Neither changes anything you did not answer. `~/.claude/CLAUDE.md` `### Context` keeps its interim line.
- **AC-10** (probes): three probe scripts under `docs/specs/0015-checks-that-cannot-lie/probes/`, each building a scratch repo and running one headless `claude -p` step, run by you with `!` after the live copy (a probe starts claude, which a `wf` call cannot): P1 a verify step planted to pass on broken code is rewritten or dropped, and the result ends with `CAN FAIL CHECKED:`; P2 a commit touching an accepted spec's paths makes `/sync`'s report list it under `Specs possibly stale`; P3 a brief agreeing an item and a spec that drops it make the `/architect` cross check name it. Results go into `verify.md`; a failed probe sends the rule wording back to `/architect`.

## Decision

**Chosen option**: one always loaded override rule file plus two deterministic pieces (`spec-paths`, the `wf` marker check), the vendored skills untouched.

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model**: files only. Spec top file gains `**Paths:**`. `run.json` call `marker` gains two values; `stop_reason` and the park set gain `unchecked`.

**Classification order** (spec 0008): ... 11 `VERIFY FAIL:`; **11a missing check line (AC-4)**; 12 kind `sync`; ...

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| verify report | can fail note | the step's own expected result and the break that changes it (AC-2) |
| verify end line | `<n>` | steps that passed the can fail check |
| test end line | `<n>` | tests mutation checked (AC-3) |
| wf 11a | progress | the box ticked after the call (spec 0004 progress key) |
| wf 11a | marker present | last line matching the AC-4 pattern in `result` |
| spec-paths | specs folder | `docs/specs/` else `.workflow/specs/` |
| spec-paths | accepted | `**Status**:` value starts with `Accepted` |
| spec-paths | globs | `**Paths:**` line, backticked items |
| spec-paths | changed files | merge base with `main` (else `master`) on a branch; on main the parent of the oldest commit adding a `--spec` top file, else `HEAD`'s commit; plus `git ls-files -mo --exclude-standard` |
| spec-paths | own specs | `--spec`, the `specs/NNNN-` links on the synced feature's heading block |
| wf 11a | test file changed | spec 0008 AC-3 snapshot of test files before the `/test` box call vs after |
| brief check | agreed items | the `## Agreed so far, do not ask again` section of the brief named on the row's `Source:` line |
| backfill | paths | scope pointer lines (`code in ...`) and each build plan's named files |

**Key invariants**:
- No vendored skill file is edited; a pull of the skills keeps all three rules.
- `spec-paths` and `/sync` only warn; nothing blocks a sync.
- A brief check never changes a spec or scope row on its own.
- `wf` still writes nothing in a repo.

**Security model**: no new trust boundary. `spec-paths` reads git and spec files in the current repo only.

**Configuration required**: `~/.local/bin` on PATH (already true for `wf`).

**Critical test scenarios**:
- 11a: fake claude ticks a `/test` box with `MUTATION CHECKED: 3`: goes on; same with no line: parks `unchecked`, detail names the box, Park recorded; a `/check verify` pass with `CAN FAIL CHECKED: 2`: goes on; without: parks; a verify ending `VERIFY FAIL: debug` with no line: the debug loop as before; a `/test` that ticks nothing: `no_progress` as before; a `/develop` box with no line: goes on, verifies **AC-4**
- `spec-paths --test`: a temp repo with an accepted spec covering `src/*.py` and a proposed one covering `lib/**`: a change to `src/a.py` on a branch warns once; on main via the last commit warns; an untracked `src/b.py` warns; a change to `lib/x.py` does not (not accepted); `--spec` of the spec silences it; `**Paths:** none` never warns; `.workflow/specs/` found when `docs/specs/` is absent; a failing git exits 1; a bad flag exits 2, verifies **AC-6**
- Backfill: every spec top file under `docs/specs/` has exactly one `**Paths:**` line right after `**Status**:`, and every glob on it matches at least one tracked file (a corpus wide count, printing offenders), verifies **AC-5**, **AC-8**
- 11a edges: a bold `**MUTATION CHECKED:** 2` passes; `CAN FAIL CHECKED: 0` parks; `MUTATION CHECKED: 0` with a test file changed parks, with none passes; a resumed `/test` whose last result has the line passes; a milestone tick alone is not progress; a verify rerun after a debug call without its line parks, verifies **AC-4**
- `spec-paths` on main with `--spec 0007`: a change two commits after spec 0007 was added warns for other specs and never for 0007; `--spec 7` equals `--spec 0007`, verifies **AC-6**
- Rule file: present in `rules/`, listed in `NOTICE.md`, holds the AC-2, AC-3, AC-5, AC-7 and AC-9 sections, `asciify.py --check` passes, verifies **AC-1**
- Probes P1 to P3 on the real claude, verifies **AC-2**, **AC-3**, **AC-7**, **AC-9**, **AC-10**

## Build plan

Skateboard: the deterministic pieces first, so the rule text can point at them.

1. `scripts/spec-paths.py` with `--test`, the `install.sh` link and its self check, satisfies **AC-6**
2. Rule 11a, the `unchecked` park, the prompt lines, `marker` values, tests, satisfies **AC-4**
3. `rules/check-gates.md` (repo copy) and `NOTICE.md`, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-5**, **AC-7**, **AC-9**
4. Backfill `**Paths:**` on specs 0001 to 0015 with the corpus check, satisfies **AC-5**, **AC-8**
5. Live copy and install (you): `cp ~/claude-config/rules/check-gates.md ~/.claude/rules/check-gates.md`, then `./install.sh` for the `spec-paths` link, satisfies **AC-1**, **AC-6**
6. Probes P1 to P3 written, then run by you with `!`, results in `verify.md`, satisfies **AC-10**

## Consequences

**Positive**:
- A green verify or test carries its own proof, and unattended runs park instead of shipping a check that could not fail.
- Stale specs surface at `/sync` time instead of months later.
- Agreed decisions get a mechanical second look before a spec or scope row is written.

**Negative / tradeoffs**:
- The rule depends on the model following it in chat; only the `wf` line check is enforced, and a model can still write the line without doing the work.
- A good passing call that forgets its line parks `unchecked`, and you then unpark it by hand.
- Mutation checks make `/test` slower (one extra run per test).
- `**Paths:**` lines can drift too; `spec-paths` is only as good as them.
- On `main`, `spec-paths` compares everything since the feature's spec was added, so other work committed in that window also counts and can warn.
- Runner specs share `runner/run.py`, so a runner change warns about several specs at once.

**Neutral**:
- Amends specs 0008 and 0011 (rule 11a, the park set). `/develop` notes both when it builds step 2.
- Spec 0014 is built first in the queue; this feature's build edits `runner/run.py` after it.

## Follow-up

- [ ] If `unchecked` parks are common on good calls, revisit AC-4 (`/architect checks that cannot lie`).

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
