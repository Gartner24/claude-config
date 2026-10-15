# Verify: adopt your open PRs · spec 0031

Run 2026-10-14 by `/check verify adopt open prs` (headless, under `wf run`). Steps V1 to V8 drive real `wf run` and
`wf queue` processes in temp repos with a fake `gh`, a fake phone (ntfy) and a fake `claude`:
`python3 -B docs/specs/0031-adopt-open-prs/probes/verify-adopt.py` (prints EVIDENCE lines, exits 1 on any FAIL).
Every passing step was also run against a deliberate break in `runner/pr.py`, `runner/run.py` or `runner/auto.py`
and turned red (the `can fail:` note). Result: FAIL. 7 of 8 end to end steps pass, V4 fails; 6 of 6 unit steps pass;
15 of 15 breaks red.
Rerun 2026-10-14 after fix 73600c5, same probe plus the unit steps (`env -C runner/tests python3 -B -m unittest
test_auto.TestFingerprint test_adopt test_pr.TestReview.test_approvers_and_bot test_reviews`, 19 tests OK). Result: PASS.
8 of 8 end to end steps pass, 6 of 6 unit steps pass. V4 checked against two breaks, both red: the code form back on
`d.get('id')` in `runner/pr.py:687` (the reply as told merged nothing), and the `NEW_ID` replace in `runner/run.py:1549`
removed (the phone showed `reply {new id} <code> merge now`).
## Commands
- [x] V1 `wf run prr -y` with `"acme/*": {"adopt": true}` in pr.json, no standing answers in the repo; your open PRs #12 (ready), #13 (head main), #14 (fork), #15 (head the origin default branch), #16 (number already in a merged record) -> `gh api user --jq .login`, then `gh pr list --repo acme/widgets --state open --author me --json number,title,headRefName,baseRefName,headRefOid,isDraft,isCrossRepository,url --limit 100`; only #12 adopted with the AC-2 fields; plan line `watching: PR #12: Fix x (ready)`; origin `fix-x` is the fix commit whose parent is the PR head; one review call; c12 and c13 both seen and kept in `asks`, only c12 asked; 26 views over 8.5 s past `--max-wait` 0.36 s, ends when the PR merged -> AC-1, AC-2, AC-3, AC-4, AC-5. can fail: a fork PR adopted; asked comments not marked seen; the end wait keeps its `--max-wait` cutoff
- [x] V1b next run, reply "send that reply" -> one post to `issues/12/comments` for @bob, the c13 question asked next, still one claude call in total -> AC-4. can fail: asked comments not marked seen
- [x] V2 `adopt: "true"` (a string) -> no `gh pr list`, no record; `wf queue prr` with `adopt: true` -> exit 0, no gh call at all -> AC-1, AC-2. can fail: a truthy value adopts
- [x] V3 approved PR, `{"adopt": true, "merge": true}`, repo allows only rebase, reply `<id> code0001 merge now` -> phone shows `merge PR #12 now? (head <sha7>)`, the plain words learn line, `1 merge now`, `2 later`, `3 I merged it`; `gh pr view 12 ... --json state,isDraft,headRefOid,reviewDecision` before the merge; one `gh pr merge 12 --repo acme/widgets --rebase --match-head-commit <approved head>`; record `merged`, run.json `prs` ends with `merge`, no open question -> AC-7, AC-9, AC-9a, AC-11, AC-14. can fail: the method ignores what the repo allows
- [x] V4 approved PR, reply `<id> 1` (a tap on ntfy, no code) -> no merge; the question comes back as `merge PR #12 now? (head e6f675a) Note: on ntfy merging needs one of your one time codes: reply 6fu5 <code> merge now`, and `6fu5` is the new question's own id; replying `6fu5 code0002 merge now` as told runs one `gh pr merge 12 --repo acme/widgets --squash --match-head-commit <approved head>`, the same as the control -> AC-14. can fail: the code form names the answered (closed) question's id. (First run FAILED here: it named `w6t7` while the new question was `rrqd`; fixed in 73600c5.)
- [x] V5 reply `<id> code0001 sure go ahead` -> no merge; report line `PR #12: your reply was not an option, nothing merged` -> AC-8. can fail: free text silently ignored
- [x] V6 `{"adopt": true}` with no `merge: true`, reply `<id> code0001 merge now` -> phone shows `PR #12 is approved at head <sha7>; merge it, then tell me` with no merge now option; no merge -> AC-14. can fail: merge flag ignored in ask_merge and merge
- [x] V7 adopted PR whose head changes `CLAUDE.md`, one review comment -> question `foreign_commits` naming `CLAUDE.md` and the commit author; no claude call; no local `fix-x` branch made -> AC-12. can fail: the foreign change gate skipped before a round
- [x] V8 `pr.allowed` / `pr.gh`: a valid merge argv passes only with `merging=True`; `pr.gh` without it raises `Refused`; `--admin`, `--auto`, `--delete-branch`, a short sha, a non digit number, an unknown method all refused -> AC-9. can fail: `pr merge` allowed outside merge()
- [x] `python3 -B -m unittest test_auto.TestFingerprint` (ready and approved PR records make a fingerprint, merged does not) -> AC-6. can fail: the fingerprint skips ready PRs
- [x] `python3 -B -m unittest test_adopt.TestAdoptUnit.test_answers` (a moved head asks again naming it, no merge; approval gone sets ready; failed merge asks again) -> AC-8, AC-9, AC-9a. can fail: a moved head is merged
- [x] `python3 -B -m unittest test_adopt.TestAdoptUnit.test_diverged` (a local branch ahead of the PR head left alone with the report line; behind fast forwarded) -> AC-3. can fail: an ahead branch is moved to the PR head
- [x] `python3 -B -m unittest test_adopt.TestAdoptUnit.test_quoted_paths` (quoted, newline, non ASCII and leading space names under `.claude/` matched raw) -> AC-14 (`-z`), AC-12. can fail: diff without `-z`
- [x] `python3 -B -m unittest test_adopt.TestAdoptUnit.test_push_scanned_sha` (a branch moved after its scan is not pushed; the scanned sha is) -> AC-13. can fail: a moved branch is pushed
- [x] `python3 -B -m unittest test_pr.TestReview.test_approvers_and_bot` (the next round waits for the bot's review of the pushed head) -> AC-10. can fail: the bot wait skipped
## Failing
- none. The first run's V4 failure (the code form named the answered question's id) is fixed in 73600c5. That fix also
  changed the same hint in `runner/reviews.py:122` and `:134` (spec 0032); those are not verified here.
## Wiring (read, not counted as runtime proof)
- [x] `rules/branch-pr.md` rule 6 says only a person merges, or `wf` on that person's explicit "merge now" answer -> AC-11
- [x] `docs/architecture.md` invariants 1 and 5 say `wf` merges only on your explicit "merge now" -> AC-11
- [x] spec 0026 "What you're agreeing to" (line 12), rule 6 (line 23), AC-9, AC-15 and AC-20 say `wf` merges only on your explicit "merge now" -> AC-11
## Waits on you
- [ ] Write `~/.claude/private/pr.json` for the repos to adopt (scope box)
- [ ] Probes P3 and P4 on a scratch GitHub repo (they post)
## Acceptance criteria coverage
- AC-1 met · AC-2 met · AC-3 met · AC-4 met · AC-5 met · AC-6 met · AC-7 met · AC-8 met · AC-9 met · AC-9a met · AC-10 met · AC-11 met · AC-12 met · AC-13 met · AC-14 met (V4 green after 73600c5)
# Verify
- 2026-10-14, Claude Code 2.1.299, on the private sandbox repo wf-scratch (made for these checks, safe to delete): P3 PASS: squashMergeAllowed, mergeCommitAllowed, rebaseMergeAllowed all readable (true).
- 2026-10-14, Claude Code 2.1.299, on the private sandbox repo wf-scratch (made for these checks, safe to delete): P4 PASS: `gh pr merge --squash --match-head-commit <stale sha>` refused (GraphQL: Head branch was modified); the PR stayed OPEN.
