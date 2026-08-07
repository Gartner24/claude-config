---
description: Write engineering prose - commit messages, PR bodies, issues, release notes, README and docs, or a PDF. Gathers the real context (diff, code, logs) before drafting, then runs the /polish de-slop gate. Does not create the PR; /pr does that.
---

# Write

Produce the engineering prose described in `$ARGUMENTS`.

If `$ARGUMENTS` is empty, ask which artifact and for what change.

## Step 1 - Identify the artifact

| Artifact | Format authority |
|---|---|
| commit message | `~/.claude/rules/ecc/common/git-workflow.md` - conventional commits, `<type>: <description>`, attribution off |
| PR body | repo's `.github/PULL_REQUEST_TEMPLATE*` if present, else the git-workflow PR section |
| issue / bug report | repo's `.github/ISSUE_TEMPLATE/` if present |
| release notes | `document-release` skill |
| README / docs page | `document-generate` + `writing-skills` |
| PDF | draft as markdown first, then `make-pdf` |

If the repo has a template, it wins over anything here. Read it before drafting.

## Step 2 - Gather the real context first

**Never draft from the conversation alone.** The conversation is what you *think* changed; the
diff is what actually changed. They differ more often than feels possible.

- Commit: `git diff --staged` (or `git diff` if nothing staged - and say which you used).
- PR: `git diff <base>...HEAD` plus `git log <base>..HEAD --oneline`. The full commit history,
  not just the last commit.
- Issue: the failing command and its actual output. Paste real output, never a paraphrase.
- Docs/README: read the code being documented. Grep for the symbols before naming them.

If you cannot get the real context, say so and stop. Do not write a plausible-sounding
description of a change you have not read.

## Step 3 - Draft

Rules that apply to all of them:

- **No invented specifics.** File paths, function names, flags, version numbers, endpoints, and
  metrics all come from something you read. Unknown stays UNKNOWN.
- **Lead with what changed and why**, not with what you did. "Auth tokens now refresh on 401"
  beats "I refactored the auth module."
- **Scope honestly.** If part of the work is incomplete or untested, the PR body says so. A test
  plan with an unchecked box is worth more than a confident summary that is wrong.
- Length matches the change. A one-line fix gets a one-line commit.

## Step 4 - Polish gate (required, not optional)

Run `/polish` on the draft. Every time, including one-line commit messages.

This is non-negotiable for the same reason `/design` step 7 is: the failure mode is invisible to
the author. Do not skip it because the text "already looks clean."

## Step 5 - Hand off, do not overreach

- Commit message: print it. Commit only if the user asked you to.
- PR body: print it, then offer `/pr` to actually push and open it. `/write` does not touch the
  remote.
- Issue: print it, then offer to file it with `gh issue create`.
- PDF: run `make-pdf` and give the path.

## Read back anything outward-facing

Before telling the user a PR comment, issue, or release note is posted, fetch it back and read
it. An unexpanded `$VAR` or a template placeholder is public the moment it posts.

## Not this command

- Creating the PR (branch, push, `gh pr create`) -> `/pr`
- Marketing copy, landing pages, social, articles -> `content-ops` / `article-writing`
- Thesis, papers, literature review -> `/academic`
