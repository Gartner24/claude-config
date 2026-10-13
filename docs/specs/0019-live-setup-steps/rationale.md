# 0019. Live setup steps in one command: rationale

## Context

Unattended `wf run` calls never write `~/.claude` or `.git/hooks` and never start a real claude check (spec 0007 guards, runner handoff rule). So every feature that changes a rule, a hook, the settings, or needs an end to end run on the real claude ends with boxes only you can close. On 2026-10-13 that was six boxes over four features, each with its own copy command, install, or check, and each check result to be typed into a verify.md by hand.

The boxes are free text, and some are written by unattended calls, so anything that runs them must not trust their wording. `install.sh` adds a second problem: it rewrites `~/.claude/settings.json` from the repo copy, which never holds `autoMode` (sync strips it for the public repo), so every install drops your live `autoMode`.

## Options considered

### Option 1: `wf finish`, a tested subcommand reading tagged boxes

**Pros**:
- Reads the scope when you run it, so it always does what is still open, from any run.
- Covered by the runner's unittest suite like everything else.
- Fixed shapes and a confirm keep a planted box from running anything else.

**Cons**:
- A new tag for `/architect` and the rules to learn.
- New code that writes git history.

### Option 2: a `finish.sh` script written into each run folder

**Pros**:
- You can read the exact script before running it.

**Cons**:
- Generated shell with no tests, and stale once you tick a box by hand.
- Steps from older runs are missing.

### Option 3: guess runnable steps from any waits-on-you box

**Pros**:
- Works on today's boxes as written.

**Cons**:
- A box mixing a copy with a human step gets ticked half done.

## Rationale

The scope files are already the runner's single truth (invariant 7), so the command that closes boxes should read them at the moment you run it, not a snapshot from the night. A tag makes the intent explicit at the time `/architect` writes the box, and the shape list makes the tag safe even when a call wrote the box. Copies run in Python and steps as argument lists, matching the runner's no shell rule.

The failure policy follows what each phase proves: a check after a failed copy or install would test the wrong setup, while checks are independent of each other, so one flaky check should not hide the others. Committing only the touched files keeps the repo clean for the next run without sweeping anything else in, and skipping `main` matches `wf run`'s branch rule.

`autoMode` is fixed in `install.sh` itself, so a hand run and a `wf finish` run behave the same.
