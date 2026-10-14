# 0026 rationale

## Context

Three agreed features in one design (brief `docs/briefs/finish-runner-today.md` item 16): the branch and PR standard (personal scope row 11), the draft PR per spec (claude-config scope feature 14, deferred 2026-10-12 because "opening a PR needs a push, which the runner never does"), and the PR review loop until approval (personal scope row 27).

What the code does today:
- `branch_off` (`runner/run.py:1697-1712`) leaves `main`/`master` for `feat/<slug>` (spec 0021 R1) and otherwise builds every feature on the branch the repo is on. Release branches like `feat/release-4` collect many features, which is the stack problem row 11 describes.
- Calls get `call_env()` (`runner/run.py:2976-2983`): no `GH_TOKEN`, no ssh agent, no credential files (spec 0007). The `wf` process itself keeps your environment. That is the door this spec uses: the push and every `gh` call happen in `wf`, after the call ended, never inside one.
- `wf` runs git with hooks off (`runner/wf.py:47`, `:265`) because scanned repos are untrusted; `wf finish` commits with plain git so your hooks run (`runner/finish.py:778`). The squash and push here follow `wf finish`: they act on your own trusted repos, after the guard check, so the hooks are the baseline ones spec 0007 hashed.
- The phone scrub drops every token holding `/`, `@` or `://` (`runner/ntfy.py:23`, `:142-147`), so a PR URL can only reach the phone as `PR #<n>`.
- `scripts/private-names.py` scans a working tree, staged files, one message, or the whole history (`:123-197`); none fits "the commits about to leave". The runner copy (`~/.local/share/wf/<fp>/`, spec 0020 AC-12) holds only `runner/*.py`, so the checker has to travel with it.
- `CASES` (`runner/run.py:212-243`) and its completeness test (spec 0021 AC-1) are where every new failure gets its question.

## Options considered

Where the push happens:
1. In the runner process after the feature ends (chosen). Calls keep spec 0007 untouched; one small code path holds credentials; the scans run on exactly what leaves.
2. In a call with credentials. Rejected: undoes spec 0007 for every step of every repo.
3. By you in the morning. Rejected: the request is that the PR is waiting when you wake up.

Where a feature's branch is checked out:
1. Switch the repo's checkout per feature, restore the start branch at the end (chosen). One feature at a time per repo is already the rule (architecture invariant 6), and spec 0021 R1 already switches branches.
2. A worktree per feature. Left to spec 0027, which needs it for features side by side; one at a time does not.

Scope ticks across branches: each feature's ticks live on its own branch, so the start branch's scope still shows a built feature as open. Options: read the queue from the records (chosen: `prs` in `queue.json` says what is built and in review); merge each branch back into the start branch (rejected: that is the release branch pattern this replaces); a separate untracked scope (rejected: changes the scope contract for every repo).

Who sorts a reviewer's comment: a call (it reads code and judges), with the criteria of `rules/review-fix.md` in its prompt and a fixed output line per comment, while `wf` believes only the commits it can see (same rule as spec 0011: the files are the truth).

## Decided without asking (2026-10-13)

Per `docs/briefs/finish-runner-today.md` ("the conductor answers every design question itself with the recommended option and records it"). Each: question, options, pick.

1. How does a repo opt in? Options: one key `push: draft PR`; two keys `branches: per spec` and `push: draft PR`; a trust list flag. Pick: two standing answer keys, push needing branches. Spec 0027 needs branches without pushing, and AGENTS.md standing answers are already where per repo choices live (spec 0006).
2. Base of a spec branch? Options: always `origin/main`; the start branch. Pick: the start branch, because specs and scope are committed there; a branch cut from `main` would miss an unmerged spec. A start branch missing on origin is case `base_unpushed`, recommended "push it too".
3. When to stack? Options: whenever a spec names another spec; only on an explicit `**Stacks on:**` line. Pick: explicit line, written by `/architect` only for a code dependency on an unmerged spec. Stacks are the pain row 11 names; the default must be off the base.
4. Max stack depth? Options: 2, 3, 5, unlimited. Pick: 3 (the branch plus two below). Deeper chains are where rebases turned unmaintainable.
5. Rebase a pushed stack on its own? Options: always; never; ask. Pick: ask (`rebase`, recommended yes), since rewriting pushed history is "never automatic" in `rules/review-fix.md`. Unpushed branches rebase silently.
6. Squash when? Options: before the first push; at merge only. Pick: before the first push (scope feature 14 "one clean commit per feature"); review fixes stay separate commits afterwards, so nothing pushed is rewritten.
7. Commit message of the squash? Options: a `/document pr` call; built by `wf` from the feature heading and the spec. Pick: built by `wf`: no model, no extra call, no attribution possible, Conventional Commit form.
8. Run the repo's hooks on the runner's commit and push? Options: hooks off as `wf.git`; hooks on as `wf finish`. Pick: on. A pre-push gate you installed (the review receipt hook) is yours; when it refuses a draft push, case `push_failed` recommends "push without the pre-push hook this once", because a draft is not a landing and merging still waits on you. Flagged for your review: if you want drafts to wait for a review receipt, answer "skip the PR" there.
9. Private names hit? Options: always block; block in public repos, ask in private ones. Pick: by visibility. Work names are expected inside a private work repo; the scan exists for public ones (spec 0013, the 2026-10-12 leak). Unknown visibility counts as public.
10. Attribution scan scope? Options: messages only; messages plus every added line; messages plus added lines starting with a trailer form. Pick: the last, so a spec quoting the pattern (this one) passes while a real trailer line in a file is caught.
11. Marking ready and merging? Options: merge on your phone yes; never. Pick: never, no code path (scope feature 14 "the runner has no path to merge or mark ready"); the `gh` allow list makes that testable. Approval opens a question that tells you to merge.
12. How are new comments noticed? Options: a daemon; GitHub webhooks; polling in runs. Pick: polling inside `wf` runs (start, between features every 10 minutes, and the end wait), no new process or service.
13. Whose comments count? Options: everyone; repo collaborators and the named bot. Pick: collaborators (`OWNER`, `MEMBER`, `COLLABORATOR`) and the bot; others are listed, never acted on. A comment is untrusted input to a call that edits code; limiting authors keeps a stranger on a public repo from steering a fix round.
14. A decline? Options: reply on its own; ask first. Pick: ask first (as requested), with the call's proposed reply as the recommended option.
15. Round cap? Options: none; 5 then ask. Pick: 5 then ask; the loop still runs until approval when you say "5 more".
16. Required approver? Options: GitHub's `reviewDecision` only; a named list. Pick: a named list per repo in `~/.claude/private/pr.json`, falling back to `reviewDecision`; names never in a repo.
17. Bot reviewed repos? Options: separate mode; the same loop with a wait for the bot's review on each pushed head. Pick: the same loop plus the wait, and no local review ever, matching the private description of those repos.
18. Report link on the phone? Options: the URL; the PR number. Pick: the number, since the scrub drops URLs; the full report and `run.json` keep the URL.

## Rationale

Calls stay exactly as guarded as today; the only new outward action is in a short, allow listed path of `wf` that runs after its own guard check and two scans. Every new failure is a spec 0021 case, so none stops the night. The standard is written once, in a rule file people and `/architect` read, and the runner follows the same text.

Accepted gaps: a fix round's call reads comment text written by other people (prompt injection reaches a call that can edit code, not one that can push; the commits it makes are pushed to a draft or ready PR you review, never merged); the review loop only runs while a `wf` run is going.
