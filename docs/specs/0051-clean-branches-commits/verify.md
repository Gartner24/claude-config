# 0051 · Verify

## P1 a call cannot write the private switch (2026-10-15): pass
Read from the argv of a real `wf` build call (row 54's `/develop`, 2026-10-15, process captured in the conductor session): `--disallowedTools` holds `Edit(//home/santiago/.claude/private/**)`, and the call's sandbox settings list `/home/santiago/.claude/private` in `denyWrite`. So neither the Edit and Write tools nor a Bash command inside the sandbox can write `~/.claude/private/pr.json`; the source is `SECRETS` (`runner/run.py:347`) through `never_writable()`. The build adds a unit test that pins this (AC-1).

## /check verify 2026-10-17: PASS (AC-1 to AC-15 as first accepted)
The real runner functions and the two scripts ran on scratch git repos with a bare origin, and a fake `gh`, since this sandbox cannot reach github.com. Drivers: `python3 -B docs/specs/0051-clean-branches-commits/probes/verify0051.py` (one `==` line per check) and `bash docs/specs/0051-clean-branches-commits/probes/scripts.sh`. The D1 and E4 parts (AC-3 new patterns, AC-4 first check wait, AC-12 own first commit, AC-16) are row 71's build and are not checked here.

## Commands
- [x] `pr.auto` with and without `"auto_merge": true` in pr.json, and `run.never_writable` -> true, false, `~/.claude/private` denied. can fail: the flag is ignored or `~/.claude/private` leaves `SECRETS` -> AC-1
- [x] `merge_green` on a record with `combined: true` -> None, no `gh pr merge`, state stays draft. can fail: the combined guard is dropped -> AC-2
- [x] grep `runner/` for `def combine`, `COMBINE_PROMPT`, `combine_job`, `--combine`, `combine_conflict`; `runner/tests/test_combine.py` -> none left, file gone, `clean_suite` kept. can fail: any combine code left behind -> AC-2
- [x] `small_safe` on seven real branches -> docs only `(True, [])`; `250 lines`; `11 files`; `touches runner/x.py`; `touches src/AuthForm.ts`; `removes def run_step`; `deletes or skips a test`. can fail: a rule that never fires, or a wrong reason -> AC-3
- [x] `green` with the branch's AGENTS.md saying `suite: true` -> suite run is `python3 -c pass` (origin's), true; a FAILURE check -> false `check ci: failure`; `/test` box unticked in the main plan -> false. can fail: the branch's suite is read, or a failing check passes -> AC-4
- [x] `merge_green` after origin/work moved -> branch tip is a two parent `Merge remote-tracking branch 'origin/work'` commit pushed to origin (no rebase), one `gh pr merge 7 --repo acme/widgets --squash --delete-branch --match-head-commit <tested head>`, state merged, note `merged: 1. A: PR #7 (small and low risk)`, local branch deleted. can fail: a rebase, a stale head, or no cleanup -> AC-5, AC-6, AC-7
- [x] `merge_green` with a clash -> `merge_conflict` asked, no MERGE_HEAD left, tip unchanged, no merge. can fail: a half done merge is left or it merges anyway -> AC-6
- [x] `cleanup` of a CLOSED PR -> origin and local branch deleted; a MERGED PR whose local branch has a later commit -> `kept: feat/0002-b: commits after the PR`, branch kept. can fail: unpushed work deleted, or a closed branch left -> AC-7
- [x] risky PR -> `merge_ready` "PR #7 passed its checks but needs your review (touches runner/x.py). Merge it now? (head ...)", `asked_head` stored; "later", free text and an ntfy reply with no code merge nothing; merge now after the head moved asks again naming the new head; merge now at that head -> one squash merge, `(your merge now)`. can fail: free text or a moved head merges -> AC-8
- [x] `allowed` -> the 9 item squash merge only with green; `--admin`, `--auto` refused; `pr ready` only with green; create without `--draft` refused outside plan; rulesets GET allowed; `gh(...)` with `--admin` raises Refused. can fail: an extra flag slips through -> AC-9
- [x] `settings_check` with merge commits on and no ruleset -> one `settings: acme/widgets: ...; run bin/repo-settings.sh acme/widgets` note, self merge off. can fail: a difference is not reported -> AC-10
- [x] `bin/repo-settings.sh --check o/r` -> exit 1 `allow_merge_commit is true, wants false`; all right -> exit 0. can fail: --check always passes or always fails -> AC-10
- [x] `bin/docs-pr.sh note` -> exit 2 for code outside docs/, nothing ahead, tracked changes; docs only -> PR URL, `pr create` then `pr merge --squash --delete-branch --match-head-commit`, back on main equal to origin, no docs branch left. can fail: a non docs commit lands -> AC-11
- [x] `warnings` on a 450 line branch dated 7 days back -> `large: 450 lines changed (over 400)`, `old: branch 7 days (over 2)`; small fresh branch -> none. can fail: wrong threshold or date -> AC-12
- [x] `publish` of that 450 line branch -> `pr create --draft ... --title "feat: A (spec 0001)"`, body has the `large:` line, then `merge_ready` asked (450 lines); `report.item_line` shows both warnings on the `built:` line. can fail: the warning stays out of the PR or the report -> AC-12, AC-5
- [x] `run.plain_question` and `run.CASES` for `merge_ready` and `merge_conflict` -> plain sentences and their two options each. can fail: a missing row raises -> AC-13
- [x] `land_plan` with one scope only commit -> push to `docs/plan-<stamp>`, `pr create` (no --draft), squash merge with --delete-branch, local equal to origin; a commit with `code.py` -> nothing, note `plan not landed: code.py is outside docs/scope`. can fail: a code commit lands as plan -> AC-15
- [x] `python3 runner/tests/fast.py` -> 972 tests, 0 failed. can fail: any regression

## Checked by reading only (not counted)
- AC-14: `claude-home/rules/branch-pr.md` rules 4 to 10, architecture invariants 1, 5 and 6, and the Amended by lines in 0026, 0031 and 0043 say what AC-14 asks.

## Not reachable from the sandbox
- A direct push to `main` refused by GitHub, and the real `bin/repo-settings.sh --check Gartner24/claude-config`: github.com is denied. Your two waits on you boxes cover them.

## Spec text behind the code
- AC-11 still says `--fill` and the `git diff --quiet <old HEAD> origin/<default> -- docs` guard; PR #29 (plan E3/E4) replaced them with titles from the commits and a reset only on a clean tree with HEAD still the pushed commit.
