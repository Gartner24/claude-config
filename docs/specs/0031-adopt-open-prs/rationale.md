# 0031 rationale

## Decided without asking (2026-10-13)
Each question was answered with the recommended option, as agreed in docs/briefs/finish-runner-today.md.

1. **Where does the adopt switch live?** Options: a standing answer in AGENTS.md; `~/.claude/private/pr.json` per repo; a `wf` flag. Pick: `pr.json` (`"adopt": true`). Team repos must not need a file change, and the file already holds the per repo approver and bot entries (0026 AC-15).
2. **Does adoption need `push: draft PR` too?** Options: yes; no, `adopt: true` alone opts the repo in to the review loop. Pick: no. A team repo cannot carry the standing answer, and adopting its PRs is the point.
3. **When are open PRs read?** Options: every plan, including `wf queue` and the autonomous fingerprint; plan of a real run plus each review poll; review poll only. Pick: plan of a real run plus each review poll. A first run must see a new PR to know there is work, while `wf queue` stays read only and `wf auto wait` (every 30 s) never calls GitHub.
4. **Which PRs?** Options: every open PR you authored; only ready ones. Pick: every open one you authored, as asked; drafts are only marked, as 0026 AC-11 does. Forks are left out because `wf` pushes fixes to origin.
5. **A local branch that is not at the PR head?** Options: reset it; fast forward only and otherwise wait; skip the sync. Pick: fast forward only. Your own unpushed commits are never thrown away.
6. **The same comment judged again every poll?** 0026 leaves asked comments unseen, so with a long watch each poll would start another call for them. Options: keep; mark asks seen and ask them one by one from the record. Pick: the latter, so calls happen only for new comments.
7. **Which repos count for the endless watch?** Options: every held repo; held repos that have not ended. Pick: not ended, because only those are polled; an ended repo would hold the run with nothing checking it.
8. **Free text on the merge question?** Options: fall back to the recommended option as other PR questions do; never merge. Pick: never merge, counted as later with a report line.
9. **Merge method?** Options: always squash; the first the repo allows of squash, merge, rebase. Pick: the first allowed, read with `gh repo view`.
10. **Guard against code pushed after the approval?** Options: none; `--match-head-commit` with the approved head. Pick: `--match-head-commit`, and a fresh check of the head before the call; a moved head goes back to ready.
11. **A failed merge?** Options: a new case with retry; ask the merge question again with the reason. Pick: the same question again, so retrying is again your explicit tap and no new case row is needed.
13. **Security review: code from someone else on an adopted PR.** Options: check each commit's author; one aggregate diff since the last cleared head. Pick: the aggregate diff. An author name is whatever the committer typed, the commits API stops at 250, and a merge commit's changes are not in a per commit file list.
14. **Which answer is recommended there?** Options: "I reviewed them, go on"; "skip this PR". Pick: "skip this PR", the safe one; going on needs your look at the commits first.
15. **Security review: the merge after a later push.** Options: trust the head stored at approval; read the PR again on your tap. Pick: read it again and ask again on any change, with `--match-head-commit` as GitHub's own check.
16. **Security review: who may answer a merge?** Options: any reply on the phone channel; your own chat on Telegram, a coded reply on ntfy. Pick: the latter. An ntfy topic accepts posts from anyone who knows its name, and its buttons carry no code.
17. **Which flag turns merging on?** Options: reuse `adopt`; a separate `"merge": true`. Pick: a separate flag, so watching PRs never implies merging them.
12. **The approved question after you merged on GitHub?** Options: leave it open; withdraw it when a poll sees the PR merged or closed. Pick: withdraw, or the run would wait on a question that no longer matters.
