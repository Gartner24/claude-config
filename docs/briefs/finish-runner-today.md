# Finish the runner today

## Agreed so far, do not ask again
- 2026-10-13, your message: the runner is finished today, from the `~/.claude` conductor session, in one go. Specs and `/architect` are still used and written down, but the conductor answers every design question itself with the recommended option and records it; you are not asked. Then `/develop`, verify and test, non stop, until done. Stop only before merge or push.
- Start when the claude-config window finishes its current fix, so two sessions never edit the runner at once.

## The complete list, in build order
Must have (the goal: queue features, sleep, wake up built, answer the question queue, it finishes):
1. Runner runs from its own installed copy (one folder per version), so runs can edit `runner/` (spec 0020 amendment).
2. Never stop: a case for every stop reason (spec 0021).
3. One command `wf` (spec 0020): one confirm screen, report, setup swap, checks beside the builds, retakes, builds side by side; no `finish`/`unpark`/lock waits; the lock names its real holder.
4. Choose tonight's features on the `wf` confirm screen ("do 1, 2, 4, 12"): every queued feature listed, untick the ones to leave for later.
5. The report names repos (feature 34).
Small safety and cleanup, same day:
6. Guard hook: `bash -c "rm -rf ~"` passes because a quote is not a left boundary (spec 0016 follow-up).
7. Push guard: also hash the targets of `~/.gitconfig` and `~/.config/git/config`, a `core.hooksPath` outside the git hooks folder, and `info/attributes` (spec 0007 follow-up).
8. Prune old run folders (keep the newest 50) (spec 0014 follow-up).
9. Tick the stale follow-up boxes that later features already closed (specs 0003, 0004, 0005, 0006, 0008, 0011, 0014, 0015, 0018).
Land it:
10. Review (`/review-stack`, a sandbox and permission path), fix, merge to main and push, with your yes. Includes everything since the last push (releases 4 to 6).
Agreed features, all in (your message 2026-10-13: these were agreed earlier, none of them is optional):
11. Usage limit planning (feature 12): estimate each step's usage, fit the run to the 5 hour window and the weekly limit, start after a reset, never start a run the week cannot finish.
12. Cheaper model for simple work (feature 15): summaries, logs, triage and drafts go to the free claude-fb models; never code edits, decisions, security or client code.
13. Understand everything (feature 23, wider than first written): not only question panels, everything Claude says to you is in plain words you can follow, with a way to learn any idea first. Research first, then design.
14. Guard baseline check between repos (feature 31).
15. GitHub issues as the source of truth (feature 16): per repo `scope`, `issues` or `mixed`; the runner rereads the linked issue before every step.
16. Branch and PR standard, draft PR per feature with push at the end of a run, and the PR review loop until the approver approves (one design, three features).
17. Several features of the same repo at once (needs 16).
Last:
18. Telegram instead of ntfy: questions with buttons and typed replies, longer reports. Needs one thing from you: a bot token from Telegram's BotFather (2 minutes), kept outside the repo.
19. Autonomous mode, the very last: the session drives `wf` itself, stays on through `/clear`, shown in the status bar, off with `/auto off`. Plan and research in [autonomous-mode.md](autonomous-mode.md).
Maintenance, not features: rerun the probes after a Claude Code upgrade (specs 0005, 0007); the usage limit and outage probes wait for a real limit or outage.
