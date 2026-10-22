# Verify 0076 (built 2026-10-22)

Run: `python3 -B claude-home/skills/workflow-builder/check.py --test` (27 of 27 pass), `python3 tests/fast.py`
(149 tests, 0 failed), `bin/install.sh --dry-run` (clean; lists `mkdir -p ~/.claude/workflows` and the
`skills/workflow-builder` link), `python3 scripts/check-routing.py` (routing OK), `python3 scripts/private-names.py check` (clean).
All fixtures are temp trees; nothing ran against the real `~/.claude`.

| AC | Evidence | can fail |
|---|---|---|
| AC-1 | `claude-home/skills/workflow-builder/SKILL.md` sections 1 and 2: kebab case and name clash refusal (both repo folders, both live folders, the manifest), the seven questions in order with a recommended answer each, the model rule, the one prompt "write a skill instead" rule | not run: the interview is model behavior; the proof build (row 102) is its first real test |
| AC-2 | SKILL.md section 3 names each file and its template; `templates/` holds `CONTEXT.md`, `stage-CONTEXT.md`, `workflow.js`, `starter-SKILL.md`; check.py "templates filled" case fills them and they pass | a template that loses a stage section or its Model value turns "templates filled" red (two template mutants, both red) |
| AC-3 | `templates/workflow.js`: literal meta, `missing arg: <key>` loop, one `phase()` per stage, `label`/`model`/`effort`/`schema` on each `agent()`, `pipeline()` fan out with `.filter(Boolean)` and a logged failure count, prompts naming the stage CONTEXT.md, repo, run id and run output path, earlier summary passed on, worktree branch lines, one summary per stage with `branches` | check.py fails the filled template if meta, phase titles or agent options drift from the stage folders |
| AC-4 | `templates/starter-SKILL.md` steps 1 to 6 (owner steps before, run id `date +%Y%m%d-%H%M%S`, `check-ignore -q .workflow/x` then `info/exclude`, Workflow call with `scriptPath` and `{repo, runId, limit, ...}`, output folders, human checks, `wf/` branches, run folder count, owner steps after) | not run: needs a real workflow run (row 102) |
| AC-5 | check.py `--test`: a good fixture passes, 25 fixtures each report their problem (syntax, meta not literal x3, phase order, the 4 banned calls plus one inside `${}`, missing schema/label/model/effort, Model line differs, no Model line, missing section, 0 and 2 Human check lines, missing input under `claude-home/`, under `~/.claude/`, and `~/.claude/workflows/` resolved to the repo copy, token cap, table vs folders both ways); placeholders `<`/`{` skipped (good fixture holds both). Suite hook: `tests/test_claude_config.py` `TestWorkflowBuilderCheck` | each detector disabled turns its case red: 27 of 27 mutants red (list below) |
| AC-6 | `bin/install.sh:37` mkdir list and `:65` link loop include `workflows`; `bin/claude-config.py` `drift()` calls `linked_kind("workflows", ...)` (label `workflow`, no manifest entries). Tests: `tests/test_install.py` `TestWorkflowLinks` (link made, real folder skipped and named), `tests/test_claude_config.py` `TestDrift.test_workflows` (linked: none; missing live; live only; real folder "in the repo, but live is not a link to it") | dropping `workflows` from the link loop turns `TestWorkflowLinks` red; dropping the `linked_kind` call turns `test_workflows` red |
| AC-7 | SKILL.md section 5: reread, ask only what changes, rewrite in `claude-home/workflows/<name>/`, rerun check and docs; never `~/.claude/workflows/` directly | not run: model behavior |
| AC-8 | SKILL.md section 4 step 4: offer `/<name> --limit 1` after `ok`, say a run spends usage, start only on yes; the template honors `args.limit` and logs what it left out | not run: needs a real workflow |
| AC-9 | `config/manifest.json` `icm-architect` entry (source `github:RinDig/icm-architect`, kind skill, fetch git, path `.`, install, MIT, pinned `e16cafe6a664`, base_hash, downloaded, publish, description), added in c08534f. The owner ran `claude-config.py update --apply icm-architect` (skill scan: no new findings). A fresh clone here has HEAD `e16cafe6a664`, equal to the pin | owner step; from the build agent `~/.claude/skills/icm-architect` showed as an empty folder, see the report |
| AC-10 | every file in `templates/` starts with `follows icm-architect e16cafe6a664dcf6d787a726b452adba77d913f4`; SKILL.md section 3 strips it; `follows_check()` in `bin/claude-config.py`, called by `drift()` and `update_plan()`. Test: `TestDrift.test_follows` (no entry, equal pin, moved pin in both commands, a template with no follows line). On the real manifest it prints nothing (pin equals the follows commit) | removing either call, the compare, or the no-entry line turns `test_follows` red |

## Mutants (all red, restored, green after)
- check.py and walk.mjs (run on a copy of the skill folder, `/tmp` script): syntax check off, meta literal check off
  (red on call and on interpolation), phase order off, each of the 4 banned patterns removed, `${}` code tracking off,
  `//` comment skipping off (good fixture red), each of the 4 option keys dropped, Model compare off, Model line check
  off, `Do NOT load` dropped from the sections, Human check count `> 1` and `< 1`, input exists off, workflows input
  resolved to live instead of the repo copy, placeholder skip off, token cap x10, both table/folder loops off, and two
  template mutants (fan out model, stage section): 27 of 27 red. One first ran green: nulling only the meta regex left
  the identifier scan catching `String(1)`; the mutant was widened to the whole literal check and ran red. A mutant of
  the `vm` catch behind it stays green because the literal check already refuses those cases (kept as a guard).
- Suite tests (in place, `cp` backup and restore): `linked_kind("workflows")` removed, `follows_check` removed from
  drift, removed from the plan, its compare emptied, its no-entry line removed, its no-follows-line name changed,
  `workflows` dropped from the install link loop, check.py token cap off (suite hook): 8 of 8 red; the touched test
  modules green after restore.

## Review fixes (PR 176, /review CAUTION)
- P1: `walk.mjs` no longer evaluates the meta: `literalAt()` parses strings, numbers, true, false, null, arrays and
  objects, and refuses anything else (regex literals, calls, identifiers as values, template strings). check.py
  `--test` case "meta payload" holds the reviewer's payload with a marker path in a temp folder: refused, no marker.
  Can fail: putting a `vm.runInNewContext` eval back turns it red with "marker written True".
- P2: `templates/workflow.js`: the stage feeding the fan out uses `LIST` (items required), and a missing items list
  marks the fan out stage failed. check.py `--test` runs the filled template under node with stub agents: without items
  the fan out is `failed: true` and the first agent's schema requires `items`; with two items it reads "2 of 2 item(s)
  done", `failed: false`. Can fail: dropping `items` from `LIST`, the missing list guard, or the count summary turns its
  case red.
- check.py `--test`: 30 of 30 pass. Mutants: 30 of 30 red, including the 4 new ones above.

## Not covered
- The interview, update mode and dry run (AC-1, AC-4, AC-7, AC-8) are skill prose; the first real run is the proof
  build of review-fix (row 102), left to the main chat.
- The `mkdir -p ~/.claude/workflows` line has no test of its own (the link test's live folder already exists).

## Re-verify 2026-10-22 (after merging origin/main)

Ran: `check.py --test` 30 of 30; `tests/fast.py` 154 tests, 0 failed; `bin/install.sh --dry-run` lists mkdir workflows and the workflow-builder link; templates all carry follows e16cafe6a664 and `drift` prints no review line (pin equals follows). Re-mutated: workflows dropped from the install link loop (TestWorkflowLinks red), linked_kind workflows call removed (test_workflows red); restored, suite green.

Verdict: AC-2, AC-3, AC-5, AC-6, AC-9, AC-10 met. AC-1, AC-4, AC-7, AC-8 are skill prose and not verifiable until the proof build (row 102); Verify and Test boxes stay unticked.

## Proof build: review-fix (2026-10-22)

Built `review-fix` (row 102 first box) with the builder, from the owner's seven answers (last bullet of
`docs/briefs/workflow-builder.md`). Files: `claude-home/workflows/review-fix/{CONTEXT.md,review-fix.js,stages/01_sort,02_fix,03_check/CONTEXT.md}`
and `claude-home/skills/review-fix/SKILL.md`. No workflow run was started (the dry run is the owner's call).

Ran: `check.py review-fix` prints `ok` (check.py resolves its repo from its own file location, so running the
worktree copy checks the worktree; `CLAUDE_HOME_DIR` and `CLAUDE_LIVE_DIR` also override); `check.py --test` 30 of 30;
`bin/claude-config.py docs` wrote the worktree's `docs/guides/SKILLS.md`; `claude-config.py install --dry-run` lists
`skills/review-fix` and `workflows/review-fix` links; `tests/fast.py` 154 tests, 0 failed.

| Step | AC | Result | can fail |
|---|---|---|---|
| Answers brief holds all seven interview answers (job, walk-through, stages, per-stage contracts, fan out, owner steps, args) and the files use them: 3 stages `01_sort`/`02_fix`/`03_check`, models sonnet low/medium/medium, args repo, runId, pr, branch, round, suite | AC-1 | pass (interview itself ran in the main chat; the files match its answers) | a stage name, Model line or arg that differs from the answers means the files do not match the brief |
| `check.py review-fix` prints `ok`: literal meta, phases equal to the 3 stage folders in order, every `agent()` has label/model/effort/schema, Model lines equal the script, one Human check line each, input paths exist, root table equals the folders | AC-2, AC-3, AC-5 | pass | changing one Model line or a phase title makes it print a problem line (its `--test` cases) |
| Starter `claude-home/skills/review-fix/SKILL.md`: owner steps before (pr, findings, round, branch, suite), repo, run id, `.workflow/` ignore check, Workflow call with `scriptPath` and `{repo, runId, limit, pr, branch, round, suite}`, per stage listing with human check, run folder count, owner steps after (push only when ready and no ask finding) | AC-4 | pass (run id is the spec's `YYYYMMDD-HHMMSS` with the PR number prefixed: `<pr>-YYYYMMDD-HHMMSS`) | dropping the ignore check, the `limit` arg or the folder count line leaves a starter step missing against AC-4 |
| Update mode (section 5) | AC-7 | not proven: this build used no `--update`; only prose and SKILL.md section 5 exist | not run: needs a later `--update` on review-fix |
| Dry run offer (section 4 step 4) | AC-8 | not proven: no run started by instruction; script honors `args.limit` as the template does | not run: needs the owner's yes to `/review-fix <pr> --limit 1` on a real PR |

Verdict: AC-1, AC-2, AC-3, AC-5 proven by this build; AC-4 met; AC-7 and AC-8 still
unproven. Verify and Test boxes of row 101 stay unticked.

Ambiguity: the answers do not say how `round` is derived. The starter counts earlier run folders `<pr>-*` in
`.workflow/runs/review-fix/` plus 1 and refuses a third. Also not said: who writes the leftovers brief and scope row;
the starter does it after the run in round 2. And 03_check merges in a worktree of the PR branch (the answers say only
"merges the groups onto the PR branch").
