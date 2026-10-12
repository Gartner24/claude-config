# 0012. Waiting boxes owed to you: decision record

## Context

`wf` marks a box waiting only from prose: a milestone note containing `after` or `waits on` as a word (spec 0002 AC-6). `next` shows it as `waiting:`, and `wf run` refuses or parks it (spec 0004 AC-2, spec 0008 AC-1). A top level box's own text is never checked.

On 2026-10-12 the open milestone for spec 0006 AC-9 read "Manual checks on the real claude (AC-9)". Neither word was in it, so `wf run` ran the parent `/develop` again and again until a cap stopped it. The box was owed to you, not to a model, and nothing in the scope said so in a form `wf` could read.

The skills that write scopes (`/scope`, `/architect`, `/develop`) are vendored and overwritten on pull, so any convention has to reach them through the always loaded rule file (spec 0003 AC-9), not a patch.

## Options considered

### Option 1: ` · waits on you` segment on any box (chosen)

A whole `·` segment, like `· skipped` and `· auto`. Checked on the picked box and on the note box. It wins over every other box check.

**Pros**: explicit and machine matched; same shape as the existing tags; on milestones it already matches the old `waits on` words, so old and new agree.
**Cons**: strict, so a loosely worded marker on a top level box is missed.

### Option 2: ` · you` segment

**Pros**: short.
**Cons**: its own pattern, reads less clearly, and it does not overlap the existing waiting words.

### Option 3: plain words `waits on you`, anywhere

**Pros**: no new syntax.
**Cons**: the same prose guess that missed feature 6, and on top level boxes the loose words would park real work ("after `/develop`").

### Also decided

- Placement: any box, top level or milestone. A milestone only rule would still run a top level manual box that carries a command.
- `next`: never launches a marked box. First picked "show and still launch"; the cross check showed a marked milestone would launch its parent `/develop`, the same loop with a label, so it was changed to print and exit 3.
- Near miss (`· waits on you.`): a warning, not a silent run (cross check).
- `wf run` tests the marker before `no_start`, so a marked box always reads `refused: waiting`, never the exit 3 of a box with no command (cross check).
- Keep `after`: spec 0002 and the dotfiles fixture rely on it.
- Top level boxes wait on the marker only, not the loose words.
- Marker wins over `no_command`, `no_feature` and `manual_box`, so the message says why.
- Writers: any skill that writes a scope box, through one rule line.
- Proof that skills obey: one headless `claude -p` probe, as spec 0003 AC-10 did.

## Rationale

The failure was a guess, so the fix is a declaration. A `·` segment is the one syntax the scope contract already uses for machine read facts about a line, and making it read ` · waits on you` keeps the milestone path working with no parser change there. Checking it first in `box_refusal` turns every marked box into the one reason that is true for it, instead of whichever check happened to run first. `next` stops too, because the marker means "a person must do this", not a skill; launching the parent command would only restart the build the box is waiting on.
