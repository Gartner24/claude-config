# 0044 · Questions, round two

**Date**: 2026-10-14
**Status**: Proposed
**Paths:** `runner/run.py`, `runner/context.py`, `runner/telegram.py`, `runner/pr.py`, `runner/plain.py`, `runner/tests/test_questions_two.py`, `runner/tests/test_context.py`
**Amends**: [0043](../0043-fast-runner/index.md) AC-9 (Telegram layout), [0042](../0042-questions-you-can-act-on/index.md) AC-2 (steps always), [0021](../0021-never-stop/index.md) F1 (writes outside the project) and F10 (answers to a step only you can do)

## What you're agreeing to
- Telegram questions show short tappable labels (`spec: 0031 adopt open prs`, `repo: claude-config`) instead of long web addresses, and no lone `from:` line.
- The long explanation shows its first sentence; the rest opens with a tap. A step only you can do always lists numbered steps, or says none are left.
- A step only you can do also answers "do it for me" (a build step tries it, and asks again saying why if it truly needs you), and any reply you type becomes an instruction for that same try.
- An approved PR question says "your PR #N was approved" and shows each reviewer by role: your approver, the review bot, others.
- Build steps may write outside the project without asking; your secrets and live Claude setup stay blocked and never ask.

## Summary

Your verdict on the four example questions (brief: docs/briefs/fast-runner.md): the structure and explanations are good, but links are long, the steps are missing, done or skip is too narrow, the PR question hides who approved, and permission questions should not stop a run. This spec fixes each, and turns the permission question into a rule: outside the project is open, the risky places stay shut.

## Requirements

**Acceptance criteria**:
- **AC-1** (short labels): on Telegram the spec line reads `spec: <NNNN> <words of the spec folder name>` as a link to the spec, the repo line reads `repo: <repo label>` as a link to `https://github.com/<owner>/<name>` when the origin is on github.com (plain text otherwise), an issue or PR line reads `issue: #<n>` / `PR: #<n>` as a link, and the block has no `from:` line. The plain text sent when Telegram refuses the styled one keeps the full addresses. Every value still passes `context.safe`.
- **AC-2** (folded explanation): on Telegram the explanation (`what this is:`) shows its first sentence; the rest is in an expandable quote. A first sentence over 300 characters is cut at a word and the remainder folds.
- **AC-3** (steps always): the explain call for a step only you can do is told to give one to six `STEP:` lines (where, the exact thing to type or tap, how you know it worked); when the step is already done it gives one `STEP:` line saying how to check that. When the call gives none, the message shows `steps: none given; reply with a note if something is unclear`.
- **AC-4** (do it for me): a `waiting` or `manual_box` question offers `done`, `do it for me`, `skip`. `do it for me` runs one build call for that box, told: do this step yourself; when done, tick its box in the plan; when it needs the owner (a login, a phone, a purchase, someone else's action), change nothing and end with `BLOCKED: <why>`. A tick ends the question; a `BLOCKED` asks the same question again with the reason as its detail; any other outcome follows the usual park rules.
- **AC-5** (a reply is an instruction): a typed reply to such a question that matches no option runs the AC-4 call with the reply added as `The user's answer for this step: <reply>` (spec 0021 AC-3's hint).
- **AC-6** (approved PR): the `approved` question reads `your PR #<n> was approved: <feature>`, and its block shows one line per reviewer: `reviewers: your approver: approved · review bot: not yet · another reviewer: changes requested`. A role is `your approver` for a login in `pr.json` `approvers`, `review bot` for its `bot`, `another reviewer` otherwise; the state is the latest review (`approved`, `changes requested`, `commented`) or `not yet` for a requested reviewer with no review. No login is ever shown. The data is read with `gh pr view <n> --json reviews,reviewRequests` when the question is asked; a failed read shows `reviewers: could not be read`, never an empty list.
- **AC-7** (writes outside the project): every call's sandbox `allowWrite` holds the home folder too, and every call's Edit tools may write there. The never writable list (spec 0021 AC-7: secrets, the live Claude dirs' settings, hooks, rules, agents, skills, scripts, commands, private and CLAUDE.md, shell rc files, PATH folders, wf's and Claude's own folders, git config and hooks) and every deny path stay denied exactly as before; no deny entry is carved for the home folder. A write to a never writable path is denied with no question (no F1 `allow` option). Writes outside the home folder still ask as today.
- **AC-8** (probe before build): a real `claude -p` call under AC-7 shaped settings writes a folder in the home outside the repo with the Write tool and with Bash, and is refused both ways for a denied folder (a throwaway one, so a failed deny cannot touch your setup); recorded in verify.md. A failure stops the build of AC-7.

## Decision

Change the Telegram block builder and the explain prompt; add `do it for me` to the F10 row with a reply as its hint; read reviewers for the approved question; open the home folder in the guard without touching its deny lists.

## Feature design

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| spec label | `0031 adopt open prs` | the spec top file's folder name, `-` as spaces |
| repo link | `https://github.com/<owner>/<name>` | `pr.origin_repo(r)` |
| reviewer role | your approver / review bot / another reviewer | `~/.claude/private/pr.json` (`approvers`, `bot`) via `pr.private_config` |
| reviewer state | approved / changes requested / commented / not yet | `gh pr view --json reviews,reviewRequests`, latest review per login |
| do it for me prompt | the box text | the question's `box_text` |
| home folder | `~` | `os.path.expanduser("~")` |

**Security model**: AC-7 widens writes to the home folder only; the never writable list and the deny paths are unchanged and checked by a test that compares them before and after (spec 0021's `TestDenyNotNarrowed` pattern). Reviewer logins never reach the phone. A reply used as a hint passes `context.safe` like every phone field and is data in the prompt.

## Build plan

1. Probe AC-8 first, satisfies **AC-8**
2. Telegram labels, folded explanation, steps line, satisfies **AC-1**, **AC-2**, **AC-3**
3. `do it for me` and the reply hint, satisfies **AC-4**, **AC-5**
4. The approved question's wording and reviewers, satisfies **AC-6**
5. The home folder in the guard, satisfies **AC-7**

## Consequences

**Positive**: shorter messages you can act on; fewer stops; the merge decision has the reviewer context you use.
**Negative**: a step can change files in your home folder you did not expect (the branch review and your backups are the net); one more `gh` call per approved question.

## Rationale

The options were weighed in the chat panels of 2026-10-14 (brief, "Agreed so far"): permissions open outside with the risky places shut (not always allow, not keep asking); reviewers by role (not by name); the three style changes; the two extra answers as explained.
