---
name: build-features
description: Build the ready scope rows you pick in parallel, one worktree agent each, to draft PRs; then review each PR and merge the safe ones (spec 0074). Use for two or more ready rows instead of starting agents by hand.
argument-hint: ""
---
Spec 0074. Beside this file: `ready.py` (the ready list and its clashes) and `build-features.js` (the Workflow script).
Run from the repo's main checkout, never a worktree (plan.py leaves worktrees out).

## 1. Before the list
- `git fetch origin`, so the branch check sees origin's branches.
- Delete run folders older than 7 days:
  `find ~/.claude/state/build-features -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -r {} +` (a missing folder is fine).

## 2. The ready list (AC-1, AC-2)
Run `python3 ~/.claude/skills/build-features/ready.py`. Exit 1: show its line and stop. It prints JSON:
`repo`, `base` (the branch the scope is on), `rows`, `pairs`, `later`, `prError`. Each row has `row`, `heading`,
`spec`, `tier`, `label`, `offered`, `reason`, `notes`.
- `rows` empty: say `no ready rows` and stop.
- Print every row not offered with its `reason` (`no spec, not offered`, `already in progress: <branches or PRs>`).
  `later` not empty: say `not offered this run: rows <later>`.
- Print every `notes` line (a PR that may clash) and every `pairs` entry (two rows whose spec Paths meet).
- No offered row: stop.

## 3. Pick (AC-3)
Propose a model and effort per offered row by the rule: haiku for lookup, sonnet for edits and review, opus for
design and hard work; effort low, medium or high, never above high. One short reason each.
Write the DECISION block in chat first (`rules/plain-questions.md`), then one AskUserQuestion call with
`multiSelect: true`, the offered rows in order, 3 per question, up to 4 questions. Each option: label = the row's
`label`, the first option of each question with ` (Recommended)` added; description 6 to 30 words, no spec numbers or
AC codes: `<model> <effort>: <reason>`, plus a clash note when the row has one. Tell the owner to type a change in
Other as `row 92 sonnet medium`.
After the answers: apply every Other change; then for each pair of picked rows listed in `pairs`, or found by
`spec-paths --overlap <spec a> <spec b>` (exit not 0), ask that pair again alone (single select: one row or the
other). Nothing starts that the owner did not tick.

## 4. Start gates (AC-4)
For the picked rows in row order, k = 0, 1, ...: run `start-gates --running <k>` before adding row k+1.
- `go:` adds the row.
- `wait:` (exit 1): stop adding. List every row left as `not started: <the wait line>` (an unknown 5 hour use says so
  plainly, as the line says). They are not started this run.
Then run `start-gates --running <started - 1>` once and take `cores per suite <c>` from its `go:` line: every started
row gets `cores: c`. No row started: stop.

## 5. Run (AC-5 to AC-8)
Run id: `date +%Y%m%d-%H%M%S`. Call the Workflow tool with `scriptPath` `~/.claude/skills/build-features/build-features.js`
and `args` `{runId, rows: [{row, feature, spec, model, effort, cores, tier, base}]}`: `feature` is the row's
`heading`, `tier` its `tier` (the row's own tag, else the scope's `**Workflow:**` line; a row with no tier: ask the
owner before the run), `base` the JSON's `base`. Each agent writes its step to
`~/.claude/state/build-features/<runId>/row-<n>.step`; the chip band shows `build <n>` while they run.
After it ends, print one line per row: `row <n>: <status> <pr_url or branch> <step> <reason>`.

## 6. Review and merge (AC-9, AC-10)
Bot reviewed repo (origin under an org in `~/.claude/private/work.md`, by `git remote get-url origin`): no `/review`
and no merge. List the PRs for the owner and the team bot, and stop.
Otherwise, for each row with status `pr`, in row order, one PR at a time:
1. Bring the branch up to date with `<base>`: in a fresh worktree of the PR branch, `git merge origin/<base>`, push. A
   conflict: stop this PR and list it (`merge conflict with <base>`).
2. Run `/review` (jjstack) on the PR. Fix the fix now findings by `rules-on-demand/review-fix.md` in that worktree, one commit
   each, pushed (the owner's tick covers these pushes). At most 2 review rounds; a third round needed: not merged.
3. Merge only when the verdict is APPROVE and the self merge checklist (`rules-on-demand/when-to-switch-on.md`, row 38) holds:
   own or personal repo (never a work or client origin); the verify and test boxes of the row ticked in the scope
   file on the PR branch; the repo's suite green on the PR head; all checks green for that head (no check yet: wait
   10 minutes for a first one). Then `gh pr ready <n>` and
   `gh pr merge <n> --squash --match-head-commit <head sha> --delete-branch`.
4. CAUTION, REJECT, a third round, or any failed checklist item: leave the PR a draft and list it for the owner with
   the reason.
End with one line per row: merged, waiting for you (reason), failed, skipped or not started.
