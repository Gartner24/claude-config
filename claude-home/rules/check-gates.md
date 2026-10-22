# Check gates (beats skill text)

Spec 0015 in ~/claude-config, gate 5 spec 0069. Gates that stop the workflow from fooling itself. The
vendored skills (`/check`, `/test`, `/sync`, `/architect`, `/scope`) are overwritten on every
pull, so the gates live here, and this file wins where a skill says otherwise.

## 1. A verify step must be able to fail

Applies to every `/check verify`.

- For every step you report, write one note in the report: `can fail: <the break that would
  make this step fail>`. Name a real break in the code under test, for example "the parser
  keeps the old header" or "the endpoint returns 200 for a bad token".
- A step whose expected result would still hold on broken code is not a pass. That covers a
  step that only checks a file exists, a command that exits 0 with no check on its output, a
  read back of a value the step itself just wrote, and a grep for text the change itself
  added. Rewrite such a step so it observes the behavior, or drop it and name it as dropped.
  Never count it as a pass.
- When the verify passes, end your final message with one line:
  `CAN FAIL CHECKED: <n>`, where `<n>` is the number of steps that passed this check.

## 2. A test must be able to fail

Applies to every `/test`.

- Mutation check every test you add or change, as `rules/lessons.md` describes: back up the
  file with `cp`, break the behavior the test claims to cover, run only that test file, see
  that test go red, restore from the backup, confirm it is green again.
- Older tests the feature relies on are not rechecked. They were checked when written, and a
  whole suite run per mutant is too slow (agreed 2026-10-13).
- A test that stays green on its mutant is fixed or removed before the report.
- The report lists each checked test with its mutant, one line each.
- When the suite passes, end your final message with one line: `MUTATION CHECKED: <n>`,
  where `<n>` is the number of tests checked (0 when no test was added or changed).

## 3. Every spec names its files, and `/sync` warns on stale ones

- Every spec top file (a flat `NNNN-*.md`, or `NNNN-*/index.md`; never `rationale.md`,
  `verify.md` or a child spec) carries one line right after `**Status**:` and before any
  `**Amends**` or `**Amended by**` line:
  `**Paths:**` then repo relative globs in backticks, comma separated (`fnmatch` syntax,
  `**` allowed), naming the code and config the spec governs, never `docs/`.
  A spec that governs no file writes `**Paths:** none`.
- Document repos (spec 0070 AC-20): when the repo's `AGENTS.md` has the line
  `**Deliverable:** documents`, `**Paths:**` may name folders under `docs/`, except `docs/scope/`,
  `docs/specs/`, `docs/briefs/` and `docs/reviews/`. In such a repo `/architect` writes the feature's
  test box ticked with ` · skipped` (no code, no suite): ``- [x] Test it: `/test x` · skipped``.
- `/architect` writes the line on every new spec and updates it on every amendment.
- `/sync`, before it reports: for every 4 digit spec number linked as `specs/NNNN-` on the
  synced feature's heading block (its pointer line and its `Spec` line), run
  `spec-paths --spec NNNN` once, all of them on one command line
  (`spec-paths --spec 0007 --spec 0011`). Copy every `warning:` line, or the
  `spec-paths:` error line when it exits 1, into the report under a heading
  `Specs possibly stale`. Never edit those specs and never stop on a warning or an error.
  Deciding what to do about a stale spec is yours, through `/architect`.

## 4. Cross checks compare against the brief

- `/architect`: when the feature's scope row names a brief on its `Source:` line, give the
  cross check that brief's `## Agreed so far, do not ask again` section along with the spec.
  List every agreed item the spec drops or weakens as a gap in the cross check gaps panel,
  each with a recommended fix.
- `/scope`: before writing a row whose `Source:` names a brief, compare the row with that
  brief's `## Agreed so far, do not ask again` section, and ask about every dropped or
  weakened item, with a recommended answer, before writing.
- Neither changes anything you did not answer.

## 5. A feature's brief closes with the feature

Spec 0069. The script is `python3 ~/claude-config/scripts/handover-memory.py`.

- On every `/sync`: run `<script> lint <repo>` once. Copy every `warning:` line into the report
  under a heading `Briefs to tidy`. Never stop on them.
- When `/sync` closes a feature (its heading gets `· done`) and the row's `Source:` names a brief:
  run `<script> prune <brief>`, then `<script> close <brief>`.
  - Exit 1: do not close the feature. Copy the lines it printed (each open item, each decision not
    landed) into the report and ask the owner about them.
  - Exit 0: `git rm` the brief, its detail folder and its `archive.md`, and change the row's
    `Source:` link to `<path> @ <short sha>`, the sha being the last commit that had the brief.
- `docs/briefs/general.md` is never closed; its items leave only by the 14 day archive rule.
- A brief a spec links to is kept: after `close` exits 0, skip the `git rm` and keep the row's `Source:` link (owner, 2026-10-22: the spec cites it as the record of the owner's answers).
