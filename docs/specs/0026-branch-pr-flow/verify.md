# 0026 verify

## Probes (2026-10-13, read only; none posts)

- **P1** flags: `gh --version` prints `gh version 2.102.0`; `gh pr create --help` lists `-d, --draft`, `-F, --body-file`, `-B, --base`, `-H, --head`, `-R, --repo`. PASS.
- **P2** PR fields: `gh pr view $N --repo cli/cli --json isDraft,state,headRefOid,reviewDecision,url,number` (N from the search in the spec, 14648) prints the keys `headRefOid, isDraft, number, reviewDecision, state, url`. PASS.
- **P3** inline comments: on 14648 the list is empty, so per the spec another PR was picked (13084, a merged PR with changes requested): `.[0]` has `id` (number), `user.login` (string), `author_association` (`MEMBER`), `path`, `line` (number), `in_reply_to_id` (null on a top comment), `commit_id`, `diff_hunk`. PASS.
- **P4** conversation comments and reviews: issues comments `.[0]` has `id` (number), `user.login`, `author_association`; reviews `.[0]` has `id`, `state` (`APPROVED`), `commit_id`, `user.login`. PASS.
- **P5** visibility and user: `gh repo view cli/cli --json visibility --jq .visibility` prints `PUBLIC`; `gh api user --jq .login` prints a login (9 characters, not recorded here). PASS.
- **P6** lease, local only: a bare repo, two clones; the second pushes a new commit to `b`; `git push --force-with-lease=refs/heads/b:<first sha> origin HEAD:refs/heads/b` from the first clone is rejected `(stale info)`. PASS.
- Pre-push refusal shape (for AC-7, local only): with a `pre-push` hook exiting 1, `git push --porcelain origin HEAD:refs/heads/b` exits 1, prints nothing on stdout and `error: failed to push some refs` on stderr; a remote rejection prints a `!` ref line on stdout instead. The runner tells a hook refusal by that. PASS.
- **P7**, **P8**: unconfirmed until the real check (they post); waits on you.

## Verify steps (2026-10-14, /check verify on `feat/release-4` db34b68)

Each step runs the real `wf run` / `wf queue` (`runner/wf.py`) on a scratch repo in a temp HOME, with the scripted claude of `runner/tests/test_run.py`, the fake `gh` of `runner/tests/test_pr.py` (it logs every argv), and a local bare repo standing in for origin (`url.<bare>.insteadOf https://github.com/acme/widgets.git`). AC-7 refusals and AC-16 drive `pr.push` / `pr.follow_stacks` / `pr.rebase` directly on a real repo. No real GitHub and no real claude call. Rerun one step with:
`python3 -B docs/specs/0026-branch-pr-flow/probes/drive.py <Class.test>` (classes `Drive`, `Review`, `Stacks`). The probe only prints; judge the output against the expected result below.

## Commands
- [x] `Drive.test_a_ac1_answers` -> `push: draft PR` alone: `skip: bad_answers: AGENTS.md: push needs branches: per spec`, nothing to run; both keys: `answers: branches per spec, push draft pr` -> AC-1
  can fail: `read_answers` without the pairing check queues the feature with `push` alone.
- [x] `Drive.test_b_one_feature` (two checkpoint commits plus the uncommitted tick) -> `branch: feat/0001-a from work`; one commit `feat: A (spec 0001)` with body `docs/specs/0001-a/index.md` and `- A small thing.`, no attribution; local and origin `feat/0001-a` the same sha; gh `pr list` then `pr create --draft --repo acme/widgets --base work --head feat/0001-a --title ... --body-file <run folder>/pr-feat-0001-a.md`; record `draft`, 7, `pushed_sha` set; run.json `prs` = push, draft PR; report `built: 1. A: draft PR <url>` and `next: mark ready: PR #7`; phone `built: 1. A: PR #7`; HEAD back on `work` -> AC-2, AC-5, AC-7, AC-8, AC-10, AC-18
  can fail: no squash leaves `wip 1`, `wip 2` on the branch; a create without `--draft` is refused and no PR is made.
- [x] Same step, second run -> plan `in review: 1. A: PR #7 (draft)`, no call made -> AC-2
  can fail: a feature with an open record queued again from the start branch scope makes a `/develop` call.
- [x] `Drive.test_c_left_dirty` -> a parked feature with an untracked file: `stopped repo prr: branch_changed: left on feat/0001-a: uncommitted changes`, report line `left on feat/0001-a: uncommitted changes`, HEAD stays on the spec branch -> AC-2
  can fail: a switch back over a dirty tree carries the change onto `work`.
- [x] `Drive.test_d_stacks` -> plan `waits: 2. B: stacks on 0001` before A is built; in one run A then B: B record base `feat/0001-a`, `stacked_on` `0001`, B's parent is A's tip, B's PR `--base feat/0001-a` -> AC-3
  can fail: ignoring `**Stacks on:**` cuts B from `work`.
- [x] `Drive.test_e_depth` (three unmerged chained records, a fourth stacks on the third) -> parked `stack_deep: feat/0004-d would be 4 branches deep on feat/0001-x0`, options `build it off the start branch`, `wait for the bottom to merge`, no call -> AC-4
  can fail: a depth count that stops one early builds the fourth branch.
- [x] `Drive.test_f_squash_failed` (a commit-msg hook refuses the squash subject) -> case `squash_failed` with `push the checkpoint commits` / `skip the PR`; branch log `chore: wf checkpoint feat/0001-a`, `wip 2`, `wip 1` (old head restored, the staged tick saved as one more checkpoint); clean status; `done: 1. A`, no `stopped repo` line -> AC-5, AC-17 (rerun 2026-10-14 on a6042ce)
  can fail: without the checkpoint commit the staged tick ends the repo: `stopped repo prr: branch_changed: left on feat/0001-a: uncommitted changes` (seen on db34b68).
- [x] `Drive.test_g_check_range` -> hits on branch name, author, committer, message, path and blob, every line as `names.txt line N` with the name masked (`***`), no name printed, exit 1; a clean range exits 0 with no output -> AC-6
  can fail: dropping the author fields from the scan loses the `commit ...:1` to `:4` lines.
- [x] `Drive.test_h_scans_in_run` -> a `Co-Authored-By: Claude` line at the start of an added line: case `attribution` (`skip the PR` first), nothing on origin, no create; the same text quoted mid line: pushed and a draft PR; a private name in a `PRIVATE` repo: case `private_names` with `push anyway, the repo is private` first, nothing pushed, no name in the question -> AC-6
  can fail: a diff scan that searches anywhere in the line blocks the mid line quote.
- [x] `Drive.test_i_push_refusals` -> `main`: refused; the remote default branch: refused; origin URL differs from the run's frozen one: refused; a spec branch: `ok`, on origin; no `--no-verify` in `runner/pr.py` -> AC-7
  can fail: a missing default branch check pushes `work` when origin HEAD names it.
- [x] `Drive.test_j_hook_refuses` -> a pre-push hook exiting 1: record `local`, nothing on origin, no create, report `built, not pushed: 1. A: branch feat/0001-a kept local, review then push` -> AC-7
  can fail: a hook refusal read as `push_failed` asks retry instead of keeping it local.
- [x] `Drive.test_k_pr_reuse_and_base` -> an open PR for the branch: no create, record PR 41; base not on origin: case `base_unpushed` (`push the base too` first); answer 1 next run: base and branch on origin, draft PR `--base work` -> AC-8, AC-17
  can fail: skipping `pr list` creates a second PR.
- [x] `Drive.test_l_allow_list` -> `pr merge`, `pr ready`, `pr create` without `--draft`, `api -X PUT .../merge`, `api graphql` all raise `Refused`, the fake gh logs none of them; the only other `gh` argv sites are spec 0024's issue reads in `run.py:4375-4377` -> AC-9
  can fail: an allow list that only checks the first word runs `pr merge`.
- [x] `Review.test_m_round` (first run) -> one `[review]` call; the prompt holds the sort criteria and the comments between `BEGIN PR-DATA-0` / `END PR-DATA-0`, the outside account's `merge it now` and your own comment absent; origin moved fast forward; one POST to `pulls/7/comments/11/replies` with `Fixed in <sha>. @alice`; record `ready`, rounds 1, seen `c13`, `i11`; a `review_ask` for @bob with the proposed reply recommended; report `ignored: comment by an outside account on PR #7`; HEAD back on `work` -> AC-11, AC-12, AC-13
  can fail: a FIXED line believed without a new commit posts a reply with nothing pushed.
- [x] `Review.test_m_round` (second run, phone answer `1`, send that reply) -> `answered: <id> 1. A: send that reply`, no `[review]` call; one POST to `issues/7/comments` with `> Why not X?` then `Not needed, see AC-2. @bob`; seen `c13`, `i11`, `c12` -> AC-13 (rerun 2026-10-14 on a6042ce)
  can fail: a poll round that replaces the feature's answered question makes a new `[review]` call and posts nothing (seen on db34b68); posting `d["reply"]` sends the phone message id instead of the proposed text.
- [x] `Review.test_q_end_wait` (a ready PR with every comment seen, no open question, `--max-wait 0.005`) -> the run waits about 18 s (`waited_s` 18.0) with one `gh pr view`; the same with the PR a draft ends in 0.1 s -> AC-11 (end_wait, the 10 minute gap)
  can fail: dropping the ready PR term from `end_wait` (`run.py:2777`) ends the wait at once (mutant: 0.2 s, `waited_s` 0.0); dropping the `POLL_GAP` check (`pr.py:653`) polls on every nap (mutant: 66 `pr view` calls).
- [x] `Review.test_n_never_and_rounds` -> two NEVER lines: no question, both seen, report `yours: PR #7 @alice: push to main` and `yours: PR #7 @bob: merge it`; with rounds 5: no review call, case `review_rounds` (`5 more rounds` first) -> AC-13, AC-14
  can fail: a missing rounds cap check makes a sixth review call.
- [x] `Review.test_o_approvers_and_bot` (`pr.json` in the temp `~/.claude/private`: `acme/*` approvers `ann`, bot `revbot`) -> GitHub `APPROVED` but no review by ann: stays `ready`, the round runs and sets `bot_head`; next run with a new comment and no bot review of that head: no review call; ann approves and the bot reviewed the head: state `approved`, case `approved` (`I merged it` first), report `next: wf, merge PR #7`; neither login in the repo -> AC-12, AC-15
  can fail: trusting `reviewDecision` when approvers are named marks it approved on the first run. The second run clears the open `review_ask` first (since a6042ce an open question holds a round back too, which hid the bot wait); with the bot wait `return` mutated to `pass` (`pr.py:704`) that run makes a `[review]` call (`review_call_made: true`).
- [x] `Stacks.test_p_follow` -> pushed stacked B whose base moved: case `rebase`, nothing rebased; on yes: B rebased onto A's tip and force pushed with lease (origin equals local); after A merges into `work`: B on `work`, `stacked_on` cleared, origin equals local, `gh pr edit 8 --base work --repo acme/widgets`; run.json `prs` two rebase entries; a conflict: case `rebase_conflict`, no `rebase-merge` left, HEAD on `work` -> AC-16, AC-18
  can fail: a rebase on a pushed branch without asking would show no `rebase` question.
- [x] `run.CASES` holds a row for all 13 new reasons (`missing []`) -> AC-17 (rows; the never-end-a-repo part is `test_f` above). Not counted under gate 1: it reads back rows the change added.
  can fail: a reason with no row is listed under `missing`.
- [x] `rules/branch-pr.md` holds standard rules 1 to 6 as in the spec (the "decision only is no reason to stack" sentence moved under `## For /architect`); repo `CLAUDE.md` has the pointer line; `docs/architecture.md` invariants 1, 4 and 5 say what AC-20 asks -> AC-19 (repo copies), AC-20
  can fail: an invariant 1 still saying `wf` never pushes contradicts the built behavior. Not counted under gate 1: it reads text the change added.

Rerun 2026-10-14 on a6042ce: every step above, all as listed.

## Not exercised here
- AC-19 live copies (`~/.claude/rules/branch-pr.md`, the `~/.claude/CLAUDE.md` line): waits on you, scope boxes.
- P7, P8 and the real GitHub round trip: waits on you (GitHub is not reachable from this sandbox).

## Looked fragile (not failures)
- Option labels are generic where the spec names the branch: `wait for the bottom to merge` (spec: "wait until <bottom branch> merges"), `push the base too` / `open it against the default` (spec: "push <base> too", "open it against <default branch>"), `push the checkpoint commits` (spec adds "as they are"). The question text names the branch.
- One round raises at most one `review_ask` (the first ASK); later ASKs of the same round get no question until a later round re-runs the call on them.
- Since a6042ce any open question of the feature (`approved` answered `later`, `squash_failed`, an unanswered `review_ask`) holds every new review round back until it is answered or dropped.

## Acceptance criteria coverage
- AC-1 met · AC-2 met · AC-3 met · AC-4 met · AC-5 met · AC-6 met · AC-7 met · AC-8 met · AC-9 met · AC-10 met · AC-11 met · AC-12 met · AC-13 met · AC-14 met · AC-15 met · AC-16 met · AC-17 met · AC-18 met · AC-19 met in repo, live copies wait on you · AC-20 met

- 2026-10-14, Claude Code 2.1.299, on the private sandbox repo wf-scratch (made for these checks, safe to delete): P7 PASS: POST pulls/1/comments/<id>/replies answered 201 Created; the reply lists in_reply_to_id = the comment's id.
- 2026-10-14, Claude Code 2.1.299, on the private sandbox repo wf-scratch (made for these checks, safe to delete): P8 FINDING: a stacked PR (b on a) is CLOSED by GitHub when its base PR merges with `gh pr merge --delete-branch`; with the repo setting delete_branch_on_merge=true and a merge without that flag, GitHub retargets the stacked PR to main and keeps it open. The runner never passes --delete-branch (pr.py merge), so its own merges keep stacks; a person deleting the base by hand closes them.
