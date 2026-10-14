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
- Claude plans and builds it in the conductor session, not the runner. When it is fast, `wf` runs the remaining features (39 to 44, then 45 to 48).

## Measured (2026-10-14 run)

- Check step 4 to 33 min, test step 16 to 42 min, closing step about 1 min; one step at a time.
- The runner suite: 709 tests, about 15 min per full run (888 s serial).
- Every test file passes when the files run at the same time: 20 files at once took 242 s wall, bound by two files: test_never_stop.py 241 s and test_run.py 149 s; every other file is under 50 s. Splitting those two by test class should bring a full run near 1 minute.
- `feat/release-4`, the branch the runner builds on, is not on GitHub (only `main` is), so a draft PR based on it cannot open until it is pushed.
