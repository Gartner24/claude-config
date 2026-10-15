# 0044 · Questions, round two

**Date**: 2026-10-14
**Status**: Proposed
**Paths:** `runner/run.py`, `runner/context.py`, `runner/telegram.py`, `runner/pr.py`, `runner/plain.py`, `runner/tests/test_questions_two.py`, `runner/tests/test_context.py`, `runner/tests/test_telegram.py`
**Amends**: [0043](../0043-fast-runner/index.md) AC-9 (Telegram layout), [0042](../0042-questions-you-can-act-on/index.md) AC-2 (steps always), [0021](../0021-never-stop/index.md) F1 (writes outside the project) and F10 (answers to a step only you can do)

## What you're agreeing to
- Telegram questions show short tappable labels (`spec: 0031 adopt open prs`, `repo: claude-config`) instead of long web addresses, and no lone `from:` line.
- The long explanation shows its first sentence; the rest opens with a tap. A step only you can do always lists numbered steps, or says none are left.
- A step only you can do also answers "do it for me" (a build step tries it, and asks again saying why if it truly needs you), and a reply you type in your Telegram chat becomes an instruction for that same try.
- An approved PR question says "your PR #N was approved" and shows each reviewer by role: your approver, the review bot, others.
- Build steps may write in your home folder without asking; your keys and logins, live Claude setup, startup and autostart files and every repo's git hooks and settings stay blocked and never ask.

## Summary

Your verdict on the four example questions (brief: docs/briefs/fast-runner.md): the structure and explanations are good, but links are long, the steps are missing, done or skip is too narrow, the PR question hides who approved, and permission questions should not stop a run. This spec fixes each, and turns the permission question into a rule: the home folder is open, the risky places in it stay shut.

## Requirements

**Acceptance criteria**:
- **AC-1** (short labels): on Telegram's styled message the spec line reads `spec: <NNNN> <words of the spec folder name>` (the folder above `index.md`, or a flat spec's file name without `.md`) as a link to the spec; the repo line reads `repo: <repo label>`, linked to `https://github.com/<owner>/<name>` (from `pr.origin_repo`, stored as the context's `repo_url` when the question is asked) only when the label is the repo's own name, never next to an alias or hashed label of a private repo; an issue or PR line reads `issue: #<n>` / `PR: #<n>` as a link; the block has no `from:` line. The plain text message (sent when Telegram refuses the styled one) keeps the full addresses. Every value still passes `context.safe`. Decision questions get AC-1 and AC-2; AC-3 to AC-5 are for a step only you can do.
- **AC-2** (folded explanation): on Telegram's styled message the explanation shows its first sentence (after the `(explained by a model ..., unverified)` marker when there is one: the marker and the first sentence show); the rest is in an expandable quote. A sentence ends at `.`, `!` or `?` followed by a space; a first sentence over 300 characters is cut at a word and the remainder folds. The plain text message is not folded.
- **AC-3** (steps always): the explain call for a step only you can do is told to give one to six `STEP:` lines (where, the exact thing to type or tap, how you know it worked); when the plan data it gets shows the box ticked, it gives one `STEP:` line saying how to check that it is done. When the call gives none, the message shows `steps: none given; reply with a note if something is unclear`.
- **AC-4** (do it for me): a `waiting` or `manual_box` question on an unticked box that is not a `· live` box (a live box keeps its `run it now` / `not now` question) offers `done`, `do it for me`, `skip`. `do it for me` runs one box call (counted for the feature's calls and budget like any call) whose command is `DO_IT_PROMPT` with the box text: do this step of the plan yourself; when it is done, tick its box in the plan; when it needs the owner (a login, a phone, a purchase, someone else's action), change nothing and end with `BLOCKED: <why>`. After the call the runner reads the plan again: a ticked box ends the question (in a worktree the tick reaches the one plan through spec 0043's sync); `BLOCKED` asks again with the reason as its detail, and that second question has no `do it for me` (one try per box per run); any other outcome follows the usual park rules.
- **AC-5** (a reply is an instruction): a typed reply to such a question that matches no option runs the AC-4 call with the reply added as `The user's answer for this step: <reply>` (spec 0021 AC-3's hint, flattened and cut to 300 characters), and only when the answer is strong (`pr.strong`: your Telegram chat or the keyboard); any other free text is ignored as today. The message adds the line `or reply with a note: it goes to the step as your instruction`. This runs the same try, not a later step: an intentional change from the brief's "next step".
- **AC-6** (approved PR): both merge question wordings name it: `your PR #<n> was approved: <feature>. Merge it now?` (merge on) and `your PR #<n> was approved: <feature>. Merge it, then tell me.` (merge off). Its block shows one line: `reviewers: your approver: approved · review bot: not yet · another reviewer: changes requested`. A login in `pr.json` `approvers` is `your approver` (that wins over `bot`), the `bot` login is `review bot`, any other login or a team request is `another reviewer`. A reviewer's state is their latest `APPROVED` or `CHANGES_REQUESTED` review (a later `COMMENTED` does not replace it; `DISMISSED` and `PENDING` are skipped), else `commented`, else `not yet` for a requested reviewer with no review. No login is ever shown. The data comes from the poll's existing `gh pr view` call with `reviewRequests` added and its existing reviews read; a failed read shows `reviewers: could not be read`, never an empty list.
- **AC-7** (writes in the home folder): the home folder joins every call's sandbox `allowWrite` (the `write` list), never the `allowed` list, so no deny entry is carved and `opened()` is unchanged. With it, every never writable path (spec 0021 AC-7) goes into the sandbox `denyWrite` and the Edit deny rules, not only those under an allowed path. The never writable list gains the `HOME_NEVER` paths: systemd user units, autostart and login session folders (`~/.config/systemd`, `~/.config/autostart`, `~/.config/autostart-scripts`, `~/.config/plasma-workspace`, `~/.config/environment.d`, `~/.local/share/applications`), more shell and editor startup files (`~/.zlogin`, `~/.zlogout`, `~/.bash_login`, `~/.bash_logout`, `~/.bash_aliases`, `~/.config/fish`, `~/.inputrc`, `~/.vimrc`, `~/.config/nvim`), more credential and registry folders (cargo, pip, gem, terraform, the GitHub and GitLab CLIs, keyrings, the browser profile, the git credential store), and the git `hooks`, `config` and `info` of every git repo the runner knows (the wf allow list and the repos under the scanned roots, with their worktrees). No Edit allow rule is added: AC-8 shows `--permission-mode auto` writes outside the repo without one. A write to a never writable path is denied with no question. Writes outside the home folder still ask as today. A test checks every deny entry and Edit deny rule of today is still present.
- **AC-8** (probe before build): a real `claude -p` call under AC-7 shaped settings writes a folder in the home outside the repo with the Write tool and with Bash, and is refused both ways for a denied folder (throwaway names, so a failed deny cannot touch your setup); recorded in verify.md. A failure stops the build of AC-7.
- **AC-9** (every kind seen): before this goes live, one real example of each question kind is rendered from the real code and shown to you in chat, as spec 0043 AC-10 did.

Deferred: further style ideas beyond the three you picked (your open "what else could improve?").

## Decision

Change the Telegram block builder and the explain prompt; add `do it for me` to the F10 row with a strong reply as its hint; read reviewers for the approved question; open the home folder in the guard's write list only, with every never writable path denied.

## Feature design

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| spec label | `0031 adopt open prs` | the spec link's folder above `index.md`, or a flat spec's stem, `-` as spaces |
| repo link | `https://github.com/<owner>/<name>` | `pr.origin_repo(r)`, stored as context `repo_url` |
| reviewer role | your approver / review bot / another reviewer | `~/.claude/private/pr.json` (`approvers`, `bot`) via `pr.private_config` |
| reviewer state | approved / changes requested / commented / not yet | the poll's `gh pr view` (`reviews`, `reviewRequests`) |
| do it for me prompt | the box text | the question's `box_text` |
| note | your reply | the answer text, `flat`, 300 characters, strong answers only |
| home folder | `~` | `os.path.expanduser("~")` |
| known repos | their git dirs | the wf allow list and the scanned roots (`wf.WF_ROOTS` discovery), with `git worktree list` |

**Security model**: AC-7 opens the home folder for writes only through the sandbox's write list; every never writable path and every deny path stays denied, checked by a test against today's lists. Reviewer logins never reach the phone. A note is data in the prompt, from your private chat or keyboard only.

## Build plan

1. Probe AC-8 first, satisfies **AC-8** (done 2026-10-14, verify.md)
2. Telegram labels, folded explanation, steps line, satisfies **AC-1**, **AC-2**, **AC-3**
3. `do it for me` and the strong reply note, satisfies **AC-4**, **AC-5**
4. The approved question's wording and reviewers, satisfies **AC-6**
5. The home folder in the guard, satisfies **AC-7**
6. Render every kind and show you, satisfies **AC-9**

## Consequences

**Positive**: shorter messages you can act on; fewer stops; the merge decision has the reviewer context you use.
**Negative**: a step can change files in your home folder you did not expect (the branch review and your backups are the net); a needed write to a blocked place is refused, never asked; one more field on the existing `gh` call.

## Rationale

The options were weighed in the chat panels of 2026-10-14 (brief, "Agreed so far"): permissions open in the home with the risky places shut (not always allow, not keep asking); reviewers by role (not by name); the three style changes; the two extra answers as explained; every cross check fix applied.
