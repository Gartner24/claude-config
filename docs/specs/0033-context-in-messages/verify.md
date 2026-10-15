# Verify: Context and links in every message · spec 0033

Run 2026-10-14 by `/check verify context in messages`: whole `wf run`s with the runner's fake claude, its fake gh,
a local fake Telegram bot (`WF_TELEGRAM_API`) and the fake ntfy server, in temp `HOME`, `XDG_CONFIG_HOME` and
`XDG_STATE_HOME`. Nothing reached a real bot, GitHub or your config. The script is `probes/drive.py`; each step
prints the message the run really sent. Each step names the break that would make it fail (`can fail:`).

Round 1 (at 1a5c3e1): FAIL on AC-2 and AC-10, steps V7 to V9 red. Round 2 (at ed8ff79, the fix): PASS, all 9 steps
green (`drive.py -v`, 25 tests OK). Then 11 breaks, each made in the source, run against its own step only, and
restored from a copy: every one turned its step red. V6 used to check only `next: `, which the report's own
`next: review and merge: <repo>` line also matches, so it is now pinned to the feature's full next reason.

## Commands
- [x] `env REPO=. python3 -B docs/specs/0033-context-in-messages/probes/drive.py V.test_v1_decision_on_telegram` -> the Telegram question starts `Question <id> (its name, so your reply finds it):`, then the `from:` block with `repo: demo`, `feature: 1. Loop`, `spec: https://github.com/acme/widgets/blob/work/docs/specs/0001-a/index.md`, `step: Build it: `/develop loop``, `did: I compared both engines ...`, `issue: https://github.com/acme/widgets/issues/4`, `why recommended: Postgres already runs on your server.`; the styled send has the issue as an anchor, under 4096 characters; the tap is acked `Got your answer to question <id>: Postgres. Resuming.` -> AC-1, AC-2, AC-3, AC-4, AC-5. can fail: the ack back to `<id> accepted` (break tried, red), or the why line dropped from the block (break tried, red)
- [x] `... drive.py V.test_v2_blocked_steps` -> a `BLOCKED:` call with three `STEP:` lines shows `steps:` then `1.`, `2.`, `3.` in order, the `2.` the call wrote not doubled -> AC-6. can fail: the steps left unnumbered (break tried, red)
- [x] `... drive.py V.test_v3_blocked_no_steps` -> no `STEP:` lines gives `1. I could not work out the steps; open a session in the demo repo (<path>) and paste: continue 1. Loop: /develop loop; it was blocked on: needs sudo to install bwrap` -> AC-6. can fail: an empty steps list sent (break tried, red)
- [x] `... drive.py V.test_v4_write_deny` -> a block whose result records a denied `Edit` is `denied` with that path, options `allow once, always, skip`, a `path:` line, `why recommended:` the runner's fixed line, the call's words last under `what the step said, unverified:`, its `WHY: pick always` and `STEP: chmod` never shown; the same block with the path only in its text is `blocked`, no allow option -> AC-7, AC-11. can fail: a recorded Edit denial no longer turned into F1 (break tried, red)
- [x] `... drive.py V.test_v5_ntfy` -> ntfy gets `from: repo-<hash> / 1. Loop / Build it:` and `why: Postgres already runs on your server.`, no `https://`; the report's question line reads `Question <id> (its name, so your reply finds it): 1. Loop: Which storage engine? (recommended: Postgres) [from: Build it: `/develop loop`; spec https://github.com/...]` -> AC-5, AC-8, AC-9. can fail: the ntfy why line dropped (break tried, red)
- [x] `... drive.py V.test_v6_report` -> the Telegram report reads `built: 1. Loop: 2 commits <a>..<b>, 2 files, spec https://github.com/acme/widgets/blob/work/docs/specs/0001-a/index.md; next: review and merge it, it was built on its branch with no PR` -> AC-9. can fail: the feature's next reason missing from the built line (break tried, red)
- [x] `... drive.py NonGitHub` -> with origin `https://gitlab.example.invalid/acme/widgets.git` the stored and shown spec is `docs/specs/0001-a/index.md`, the issue shows `acme/widgets#4`, and the message holds no `https://` -> AC-2. can fail: the spec back to only its file name `index.md` (break tried, red), or a github.com issue link made for a non GitHub origin (break tried, red)
- [x] `... drive.py Pr.test_v8_pr_context` -> a review round question (`review_ask`) has `pr` `#7` and its URL, and `step: review round on PR #7` -> AC-10. can fail: `review_ask` falls back to `branch and PR flow` (break tried, red)
- [x] `... drive.py Pr.test_v9_merge_context` -> the "5 review rounds done" question (`review_rounds`) says `step: review round on PR #7` -> AC-10. can fail: `review_rounds` falls back to `branch and PR flow` (break tried, red)

## Live (your box)
- [ ] P1: a real question on your phone, read it and say whether it explains itself, links open, a swiped reply answers -> AC-4, AC-5

## Acceptance-criteria coverage
- AC-1 met · AC-2 met · AC-3 met · AC-4 met · AC-5 met · AC-6 met · AC-7 met · AC-8 met · AC-9 met · AC-10 met · AC-11 met
- AC-4 and AC-5 on a real phone stay with P1, your box.
