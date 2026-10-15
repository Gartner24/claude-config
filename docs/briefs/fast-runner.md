# Fast runner

Source: your message of 2026-10-14, about 18:45, after a 5.3 hour run closed 6 features with 27 one-at-a-time steps.

## Agreed so far, do not ask again

- The runner is too slow and gets fixed now, before any more features run. `wf` is stopped for this (your words: "you can stop wf if needed").
- Several agents at once: while one feature is in its check step, other features start; check steps and test steps of different features run at the same time, and no feature's work can corrupt another's.
- 1. The test step runs only the tests the feature touches, then the full suite once at the end.
- 2. Parallel features inside one repo are turned on (spec 0027's design, feature 35).
- 3. Fewer questions, and the ones left understandable on the first read (the Telegram format fix: paths kept on Telegram, the explanation not cut, the plan's internal tags gone, no generic learn line or circular reason when a real explanation exists; every question kind rendered and shown to you before it changes).
- Turn every runner switch on in claude-config: `parallel` (4), `branches: per spec`, and `push: draft PR` (your words: "Turn everything on, I don't care about the pushes ... that's why they are draft"). The private names scan and the attribution scan still run before every push.
- Plan file: one shared plan. After every step the runner copies that feature's section into the one real plan file in the main checkout; feature branches carry no plan changes (answered 2026-10-14).
- At once: 4 (answered 2026-10-14).
- Full suite: once per feature, at the end of its test step, with the fast command (answered 2026-10-14).
- Cross check gaps 2 to 10 of spec 0043: apply every recommended fix (answered 2026-10-14).
- Push `feat/release-4` to GitHub after the private names and attribution scans pass (answered 2026-10-14).
- No same-file waiting (your words 2026-10-14: "we do a feature per branch ... then we combine them via a rebase or a third branch which will be the pr or 2 PRs pointing to main, if conflicts we check what needs to stay if one of the 2 or both and fix that"). Every feature runs at once on its own branch whatever files it touches; the branches are combined at the end into a third branch with its own PR, and a clash is resolved by keeping what each feature needs (one side, the other, or both).
- Question format verdict (2026-10-14, the four rendered examples):
  - Kind 1 (step only you can do): "really good". Improve: short link text instead of the long spec URL (like an md file name), the repo as a link too, the empty looking `from:` label, real numbered steps (what to do, where, how you know it worked), and more answer options than done or skip when the step needs a different reply. Open: "what else could improve, meaby more style?"
  - Kind 2 (decision): "yes, as is", with the same improvements as kind 1.
  - Kind 3 (permission): you asked whether it should ask at all ("it should allow always ... or no?"); asked back with a recommendation.
  - Kind 4 (approved PR): fix the wording ("your PR #N was approved"), and show who was asked to review, who approved and who has not (you merge on your approver's yes; the bot alone is not enough).
- Permissions (answered 2026-10-14): writes outside the project are allowed without asking, except your secrets and the live Claude setup (settings, hooks, rules, skills), which stay blocked and never ask. This also covers a work repo's step needing to change a related repo.
- Reviewers on an approved PR question (answered 2026-10-14): by role from your private PR settings ("your approver: approved, review bot: not yet"), never by name.
- Telegram style (answered 2026-10-14): short tappable link labels (spec and repo), no lone `from:` line; the long explanation folded after its first sentence; numbered steps on every step only you can do, or a line saying none apply.
- Order (answered 2026-10-14): start the runner now with the fast runner; build the message improvements in parallel, live at the next run.
- Answers for a step only you can do (2026-10-14): add "do it for me" (a build call tries it; if it truly needs you it asks again saying why) and "reply with a note" (your text goes to the next step as an instruction). You also asked to learn the ideas first; explained in chat, then confirmed: "Those two extra answers as you explained them sound great, build them like that".
- Spec 0044 cross check gaps (answered 2026-10-14): apply every recommended fix, including keeping keys and logins, autostart and login programs, shell and editor startup files and every other repo's git hooks and git settings blocked when the home folder opens, and taking a typed note only from your private Telegram chat.
- Missing risky places in the home folder (answered 2026-10-14): watch and stop. Nothing is created in your home; anything a step puts in such a place stops that repo right after the step and you are told. Not: creating empty folders to lock them.
- Spec 0044 goes live (answered 2026-10-14): merge into `feat/release-4` locally and install once the runner is idle; no push.
- The night of 2026-10-15 (answered about 00:50): finish all claude-config and runner work tonight; the conductor runs and watches the runner, answers mechanical questions itself, fixes what it finds, and leaves as few morning questions as possible. Dotfiles, freelance and work are out of scope tonight (the CMS session does the work items).
- Merge to main and push tonight: yes, once the review findings are fixed, every test passes, and the private names and attribution scans are clean.
- Readable layout live migration tonight: yes, one step at a time with its check, after a full backup of `~/.claude`; a failed check restores the backup and stops.
- Claude plans and builds it in the conductor session, not the runner. When it is fast, `wf` runs the remaining features (39 to 44, then 45 to 48).

## Measured (2026-10-14 run)

- Check step 4 to 33 min, test step 16 to 42 min, closing step about 1 min; one step at a time.
- The runner suite: 709 tests, about 15 min per full run (888 s serial).
- Every test file passes when the files run at the same time: 20 files at once took 242 s wall, bound by two files: test_never_stop.py 241 s and test_run.py 149 s; every other file is under 50 s. Splitting those two by test class should bring a full run near 1 minute.
- `feat/release-4`, the branch the runner builds on, is not on GitHub (only `main` is), so a draft PR based on it cannot open until it is pushed.
