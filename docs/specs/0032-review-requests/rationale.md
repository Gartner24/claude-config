# 0032 rationale

## Decided without asking (2026-10-13)
Each question was answered with the recommended option, as agreed in docs/briefs/finish-runner-today.md.

1. **Which repos are searched?** Options: one global search over everything asking you; one search per held repo whose `pr.json` entry says `review_requests: true`. Pick: per held repo. The read only copy needs a local clone, `wf` knows only held repos, and a bare `wf` runs one child per repo.
2. **Search outside a run?** Options: at plan time too (a request alone starts a run); only during a run. Pick: only during a run, as asked; a pending answer is still taken by the next run.
3. **Posting command?** Options: `gh pr review` as asked; the reviews API through `gh api --input`. Pick: the API. `gh pr review` cannot attach line comments (probe P2), and line comments are what the draft is.
4. **Review body?** The asked line set had only comments and a verdict, but every posted review needs a body. Options: a fixed body; a `DRAFT SUMMARY:` line. Pick: a `DRAFT SUMMARY:` line, fixed text when missing.
5. **"edit first" with no text?** Options: re-ask the same question; a reply-with-text question. Pick: a no option question (P15) whose reply replaces the summary; free text on the draft question does the same.
6. **Which reviewer skills may run?** Options: block `/review` and `/review-stack` only in bot reviewed repos; keep the call to Read, Grep and Glob. Pick: Read, Grep and Glob only (security review), which also rules out the heavy reviewers everywhere; the prompt says so too.
10. **Security review: someone else's PR as a checkout.** A worktree of their head would let their `.claude/` hooks, `CLAUDE.md` and `.mcp.json` load in the call. Pick: no checkout; the diff and file texts as data in a clean folder, user settings only, hooks off, no MCP, no network. Whether `/code-review` expands its method with only those three tools is probe P5.
11. **A scan hit on the draft?** Options: the 0026 P2 and P3 questions; the draft question again with the reason. Pick: the draft question again; P2 and P3 act on PR records, not reviews.
7. **Long drafts?** Options: a file on both channels; Telegram's existing up-to-3-messages-then-file (`telegram.send_report`) and a cut ntfy message. Pick: reuse `send_report`; ntfy has no private file channel, so it says where the full draft is.
8. **Phone text?** File paths and `@` names are dropped by the phone scrub. Options: loosen the scrub; show the file name only. Pick: file name only; spec 0033 handles links.
9. **The PR's head moved after the draft?** Options: refuse; post at the drafted head. Pick: post with `commit_id` set to the drafted head, so GitHub shows the comments against the code you saw.
