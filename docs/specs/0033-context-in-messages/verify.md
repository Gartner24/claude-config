# Verify: Context and links in every message · spec 0033

Run 2026-10-14 by `/check verify context in messages`: whole `wf run`s with the runner's fake claude, its fake gh,
a local fake Telegram bot (`WF_TELEGRAM_API`) and the fake ntfy server, in temp `HOME`, `XDG_CONFIG_HOME` and
`XDG_STATE_HOME`. Nothing reached a real bot, GitHub or your config. The script is `probes/drive.py`; each step
prints the message the run really sent. Each step names the break that would make it fail (`can fail:`). Verdict:
FAIL on AC-2 and AC-10, three steps red; the other seven pass. No breaks were tried this round, since the verdict
is FAIL; the three red steps are themselves proof those checks can fail.

## Commands
- [x] `env REPO=. python3 -B docs/specs/0033-context-in-messages/probes/drive.py V.test_v1_decision_on_telegram` -> the Telegram question starts `Question <id> (its name, so your reply finds it):`, then the `from:` block with `repo: demo`, `feature: 1. Loop`, `spec: https://github.com/acme/widgets/blob/work/docs/specs/0001-a/index.md`, `step: Build it: `/develop loop``, `did: I compared both engines ...`, `issue: https://github.com/acme/widgets/issues/4`, `why recommended: Postgres already runs on your server.`; the styled send has the issue as an anchor, under 4096 characters; the tap is acked `Got your answer to question <id>: Postgres. Resuming.` -> AC-1, AC-2, AC-3, AC-4, AC-5. can fail: the WHY line not read from the call, the spec link built from the folder name instead of the remote, or the ack still `<id> accepted`
- [x] `... drive.py V.test_v2_blocked_steps` -> a `BLOCKED:` call with three `STEP:` lines shows `steps:` then `1.`, `2.`, `3.` in order, the `2.` the call wrote not doubled -> AC-6. can fail: STEP lines dropped, or the number prefix kept (`2. 2. Run ...`)
- [x] `... drive.py V.test_v3_blocked_no_steps` -> no `STEP:` lines gives `1. I could not work out the steps; open a session in the demo repo (<path>) and paste: continue 1. Loop: /develop loop; it was blocked on: needs sudo to install bwrap` -> AC-6. can fail: an empty steps list sent, or the resume line missing the box command
- [x] `... drive.py V.test_v4_write_deny` -> a block whose result records a denied `Edit` is `denied` with that path, options `allow once, always, skip`, a `path:` line, `why recommended:` the runner's fixed line, the call's words last under `what the step said, unverified:`, its `WHY: pick always` and `STEP: chmod` never shown; the same block with the path only in its text is `blocked`, no allow option -> AC-7, AC-11. can fail: a path read from the call text offered (F1 from text), or the call's WHY shown as the reason
- [x] `... drive.py V.test_v5_ntfy` -> ntfy gets `from: repo-<hash> / 1. Loop / Build it:` and `why: Postgres already runs on your server.`, no `https://`; the report's question line reads `Question <id> (its name, so your reply finds it): 1. Loop: Which storage engine? (recommended: Postgres) [from: Build it: `/develop loop`; spec https://github.com/...]` -> AC-5, AC-8, AC-9. can fail: links on ntfy, or the report question line still `<id>:` with no from
- [x] `... drive.py V.test_v6_report` -> the Telegram report reads `built: 1. Loop: 2 commits 91ca730..f49d6b1, 2 files, spec https://github.com/acme/widgets/blob/work/docs/specs/0001-a/index.md; next: review and merge it, it was built on its branch with no PR` -> AC-9. can fail: built_stats counts from the wrong base, or the next reason missing
- [ ] `... drive.py NonGitHub` -> with origin `https://gitlab.example.invalid/acme/widgets.git` the stored spec is `docs/specs/0001-a/index.md`, but the Telegram message shows `spec: index.md` (only the file name, `context.telegram_block` runs `os.path.basename`) and `issue: https://github.com/acme/widgets/issues/4` (a github.com link made although the origin is not github.com; `context.build` builds issue links from the scope's `acme/widgets#4` with no host check) -> AC-2 **FAIL**. can fail: it did
- [ ] `... drive.py Pr.test_v8_pr_context` -> a review round question (`review_ask`) has `pr` `#7` and its URL, but `step: branch and PR flow on PR #7`, not `review round on PR #7` (`Run.pr_ask` maps only `foreign_commits` to `review round`) -> AC-10 **FAIL**. can fail: it did
- [ ] `... drive.py Pr.test_v9_merge_context` -> the "5 review rounds done" question (`review_rounds`) also says `step: branch and PR flow on PR #7` -> AC-10 **FAIL**. can fail: it did

## Live (your box)
- [ ] P1: a real question on your phone, read it and say whether it explains itself, links open, a swiped reply answers -> AC-4, AC-5

## Acceptance-criteria coverage
- AC-1 met · AC-2 not applied (non GitHub origin: spec shows only the file name, issue gets a github.com link) · AC-3 met · AC-4 met · AC-5 met · AC-6 met · AC-7 met · AC-8 met · AC-9 met · AC-10 not applied (review round questions say `branch and PR flow`) · AC-11 met
