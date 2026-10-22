# 0033 · Context and links in every message

**Date**: 2026-10-14
**Status**: Accepted (built b424cd5)
**Paths:** `runner/context.py`, `runner/run.py`, `runner/telegram.py`, `runner/ntfy.py`, `runner/report.py`, `runner/pr.py`, `runner/reviews.py`, `runner/tests/test_context.py`
**Amends**: [0005](../0005-decision-parking-phone-pings/index.md) (the ping body and the ack), [0018](../0018-morning-report/index.md) AC-2 (built lines and question lines), [0021](../0021-never-stop/index.md) F1 and F2 (a block from the run's own write deny is F1; a block carries steps), [0028](../0028-understand-everything/index.md) (a WHY line beside the LEARN line), [0029](../0029-telegram/index.md) AC-4 (the first line of a question message).

## What you're agreeing to
- Every question on your phone says where it comes from: the repo, the feature, its spec as a link, the step it was running, what that step had done or found, the linked issue and PR, and why the recommended answer is recommended.
- Technical words stay, each with a few plain words; Telegram gets the full text and links, ntfy (a public server) a short form without links.
- The question's 4 letter name is shown as "Question w8d0 (its name, so your reply finds it)"; typed replies like `w8d0 2` and swiped replies work as before, and the answer is confirmed with "Got your answer to question w8d0: <option>. Resuming."
- When a step is blocked on something only you can do, the question gives numbered steps: what, where, the exact command, and how you know it worked. A block that is only the build's own write protection asks to allow the path instead.
- The morning report shows, per feature, what was built (commits, files, links) and the next step with its reason, and for each open question where it comes from.

## Acceptance criteria
Today: a ping is `<id>: <question>`, a `learn:` line, the numbered options and a reply hint (`runner/telegram.py:254-275`, `runner/ntfy.py:249-270`); every line is scrubbed, which drops any token with `/`, `\`, `~` or `@` (`runner/ntfy.py:23`, `:142-147`), so no link survives; the ack is `<id> accepted` (`runner/run.py`, `self.topic(d).publish(f"{d['id']} accepted", ...)`); a `BLOCKED:` line becomes F2 with "done, go on" and "skip" and no steps (`runner/run.py` `BLOCKED`, `CASES["blocked"]`).

- **AC-1** (context record): every Decision gains `context`, built by the runner process when it asks (`Run.ask`), never from call output except where named: `repo` (display name), `feature`, `spec` (the feature's spec top file, repo relative, from its spec link, `pr.spec_file`), `branch` (the branch the question is on), `step` (box text and command, e.g. `` `/check verify ask never stop` ``), `did` (the call's result text above its `DECISION NEEDED:` or `BLOCKED:` line, last 600 characters; call output), `issues` (the feature's linked issues as `owner/repo#n`, spec 0024 AC-2's reader, in any mode), `pr` (the PR number and URL the runner read from `gh`, for PR and review questions), `why` (call output, the `WHY:` line, AC-3), `steps` (call output, AC-6). Missing parts are left out, never guessed.
- **AC-2** (links only from what the runner read): a link is built only from `git remote get-url origin` when its host is `github.com` (`run.github_origin`): spec `https://github.com/<owner>/<repo>/blob/<branch>/<spec path>`, issue `https://github.com/<owner>/<repo>/issues/<n>`; a PR link is only the URL `gh` returned. A non GitHub origin shows the repo relative path. No link is ever taken from call text.
- **AC-3** (WHY): the unattended prompt asks, after a `DECISION NEEDED:` question and its `OPTION:` lines, for one `WHY: <why the first option is recommended>` line beside the `LEARN:` lines; `read_decision` returns it. Case questions take their why from `plain.WHY[case]` (one line per row, the reason the first option is first).
- **AC-4** (Telegram message): after the question and its `learn:` line, a `from:` block: `repo: <repo>`, `feature: <feature>`, `spec: <link or path>`, `step: <step>`, `path: <path>` (F1), `did: <did>`, `issue: <link>` per issue, `PR: #<n> <url>`, `why: <why>`; then the numbered options and the reply hint. Text from calls, repos and GitHub (`did`, `why`, `steps`, the feature, the step) goes through the existing scrub, cut and block list (`ntfy.scrub_field`, AC-7 of spec 0005; private names checked as today), line by line; links are added after scrubbing and dropped when they contain a block list entry. The message stays within 4096 characters: `did` is cut first, then `steps`.
- **AC-5** (question name): Telegram question messages and the report write the id as `Question <id> (its name, so your reply finds it)` on its first use in a message, never a bare `<id>:` prefix. The swipe reply matcher (`telegram.ASKED`) accepts that first line and the old `<id>:` one; typed replies (`ntfy.REPLY`) are unchanged. The ack is `Got your answer to question <id>: <option label>. Resuming.` on both channels.
- **AC-6** (BLOCKED steps): the prompt asks a blocked call to end, after its `BLOCKED:` line, with numbered `STEPS:` lines: what to do, where (which terminal or session, which folder), the exact command or line to paste, and how you know it worked. The F2 question shows them as `1.`, `2.`, ...; with none, the runner writes `I could not work out the steps; open a session in <repo path> and paste: <one line resume prompt>` (`continue <feature>: <box command>; it was blocked on: <blocked text>`).
- **AC-7** (a block that is the run's own write deny, as amended by the security review): a `BLOCKED:` call whose own permission denials (the result's `permission_denials`) record a denied file edit ends as `denied` (F1) with the path from that record: "allow once" (recommended), "always", "skip", or "try again", "skip" for a never writable path (spec 0021 AC-7). A path only named in the call's text is never offered: that block stays F2 with no allow option.
- **AC-11** (security review, authorization questions): in a question that grants something (F1, merge, post your review, clear a foreign change, accept a changed setup, push anyway, force push), the options and the recommended one come only from the runner's case table, the `why` shown is the runner's fixed line (`plain.WHY`), the call's steps never show, and the call's own words come last under `what the step said, unverified:`, after the runner's facts (path, PR, head). Every field of every phone message and phone report line passes one gate, `context.safe`: scrub (path tokens kept only for runner built links and paths and a blocked step's commands on Telegram), cut, block list and private names list.
- **AC-8** (ntfy): ntfy keeps its scrubbed message and gains a short `from:` line `<repo label> / <feature> / <step>` and the `why:` line, scrubbed; no links (the topic server is public).
- **AC-9** (report): each built feature line gains `<k> commits <first7>..<last7>, <f> files`, its spec link and its branch or PR link, and a `next:` part with its reason (`mark ready: PR #<n>, because only you mark a PR ready`); each open question line gains its short `from:` (feature, step, spec link). The Telegram report keeps links; the ntfy report scrubs as today.
- **AC-10** (PR and review questions): PR questions (spec 0026, 0031) and review questions (spec 0032) fill `pr` and `step` (`review round on PR #<n>`, `merge`, `review request`).

## Build plan
1. `runner/context.py`: building `context`, links, Telegram and ntfy rendering; `Run.ask` fills it; `WHY:` in the prompt and `read_decision`; `plain.WHY` (AC-1 to AC-4, AC-8, AC-10).
2. Question name and ack (AC-5), with matcher tests.
3. BLOCKED steps and the write deny route (AC-6, AC-7).
4. Report lines (AC-9).
5. Live: one real question on Telegram, read on the phone · waits on you · live.

## Probes
- **P1** (live, posts to your bot) a 3500 character question message with links arrives whole and the links open; a swiped reply to it answers the question.

## Follow-up
- ntfy links behind a private self hosted server, if you ever run one.
