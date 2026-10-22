# 0073 rationale

## Context
The runner retired on 2026-10-22 and its features became rules in every chat (`claude-home/rules/when-to-switch-on.md`, brief `retire-runner-features.md` rows 18, 20, 31, 32, 46, 59). Six of those rules need a script that was never built, so a chat either checks by hand (free memory before an agent) or skips the check (design audit before closing a UI feature). The runner had tested code for five of them; the sixth (scope marker warnings) already lives in the dashboard's `plan.py` but only shows in the plan pane.

All owner answers are in [the brief](../../briefs/switch-on-helpers.md) under "Agreed so far, do not ask again".

## Options considered
### Option 1: small standalone scripts lifted from the runner, run by rule lines (chosen)
**Pros**: tested logic, stdlib only, each helper usable alone. **Cons**: rule text can be skipped; runner code copied.

### Option 2: one `switch-on` command with subcommands
**Pros**: one link, one self check. **Cons**: unrelated helpers share a file and a failure; the repo's habit is one script per job (`spec-paths`, `fb-ask`, `skill-scan`).

### Option 3: hooks that run the helpers by themselves
**Pros**: cannot be skipped. **Cons**: more code and probes for cases rare today (no repo uses issues as its source of truth); the owner chose rule lines for issue reread.

## Rationale
The forces are: the owner wants the "Needs a script" list empty, each check must fail closed on unknown values (`rules/lessons.md`), and the runner code is about to move to `_archive/` (spec 0072a). Copying the tested functions keeps behavior that already survived review, and separate scripts match how `spec-paths` and `fb-ask` are installed and tested. Hooks were weighed per helper and only make sense once a helper proves to be skipped in practice.

The 5 hour source was first answered as "a file the mod writes", based on a wrong claim that a script could not read the value. Re-asked after the correction, the owner picked the runner's account reader, which works in every chat and needs no mod change.

Recommended without asking: the 15 minute review timeout (long enough for a large diff on Sonnet, short enough that a stuck call ends in the same sitting; runner up 30 minutes); no usage cache (the gate runs once per agent start, runner up the runner's 60 seconds); exit code 2 for "could not tell" so a caller can tell it from a real failure.
