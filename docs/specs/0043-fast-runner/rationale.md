# 0043 · Fast runner: rationale

## Context

On 2026-10-14 the runner ran for 5.3 hours and closed 6 features with 27 steps, one at a time. Check steps took 4 to 33 minutes, test steps 16 to 42 minutes. The runner suite has 709 tests and takes 888 seconds when its files run one after another. You asked to fix the speed before any more features run (brief: docs/briefs/fast-runner.md).

Measured the same day: every test file passes when the files run at the same time. 20 files at once took 242 seconds of wall time, set by two files: test_never_stop.py (241 s) and test_run.py (149 s); every other file is under 50 seconds. Splitting by test class removes that ceiling.

Spec 0027 already runs several features of one repo at once, each in its own git worktree (a second checkout of the same repo on its own branch). It is opt in, and it needs per spec branches. Its open follow up: every branch carries its own edits to the shared scope file, so the branches clash when merged. Spec 0026 squashes a feature branch to one commit and can push it with a draft PR. `feat/release-4`, the branch this repo builds on, exists only on this machine.

The Telegram question 1zim showed that the spec 0042 fix was not enough: the question and the explanation lost every file name and command (the cleaner built for ntfy, a public server, also ran on Telegram), the explanation was cut at 300 characters, and the plan's internal tags and filler lines stayed.

## Options considered

### Option 1: turn on spec 0027 and close its gaps, plus a parallel test command

Use the existing worktree scheduler, keep the plan in one file, push draft PRs, and add a test command that runs classes in parallel.

**Pros**: reuses a built and tested scheduler; each feature is isolated in its own checkout; the test speedup also helps the serial case.
**Cons**: one more piece of bookkeeping (the plan sync); more usage per hour; more branches to merge.

### Option 2: parallel calls inside one checkout

Run several calls at once in the same working tree, on the same branch.

**Pros**: no worktrees, no extra branches.
**Cons**: two calls editing one tree corrupt each other's work and commits; this is exactly what you asked to prevent.

### Option 3: only speed up the tests

Keep one feature at a time and add only the fast suite.

**Pros**: smallest change.
**Cons**: check steps and waits stay serial; at best about 2 times faster, not the several times you asked for.

### Option 4: keep spec 0027's same file wait

Features whose Paths overlap take turns; nothing is ever combined with a clash.

**Pros**: no clash resolution at all.
**Cons**: features 39 to 44 all list `runner/run.py`, so they would run one at a time (the cross check found this); most work in this repo touches that file, so parallel would rarely help. You rejected it: "we do a feature per branch ... then we combine them ... if conflicts we check what needs to stay".

## Rationale

Option 1 is the only one that runs features at the same time without one corrupting another: each worktree has its own files and branch, and calls cannot write a sibling's tree (spec 0027). Combining at the end, as you do by hand, is what makes parallel pay off in a repo where most features touch one large file; git merges different lines of one file on its own, and only same line clashes need the resolve call. Its other unsafe edge was the plan file, and the shared plan sync closes it the way you chose: one real plan, branches with no plan diff. The test command attacks the biggest single cost (a 15 minute suite run several times per test step), measured rather than guessed. The Telegram fixes follow the 1zim message line by line.
