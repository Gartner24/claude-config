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
