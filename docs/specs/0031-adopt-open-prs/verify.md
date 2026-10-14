# Verify

- 2026-10-14, Claude Code 2.1.299, on the private sandbox repo wf-scratch (made for these checks, safe to delete): P3 PASS: squashMergeAllowed, mergeCommitAllowed, rebaseMergeAllowed all readable (true).
- 2026-10-14, Claude Code 2.1.299, on the private sandbox repo wf-scratch (made for these checks, safe to delete): P4 PASS: `gh pr merge --squash --match-head-commit <stale sha>` refused (GraphQL: Head branch was modified); the PR stayed OPEN.
