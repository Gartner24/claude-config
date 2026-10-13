# 0015 rationale

## Context

Two ideas from the runner comparison (brief `~/projects/docs/briefs/runner-ideas-2026-10-12.md`, spec B) and one open item from personal scope row 12 part 2. A verify step or test can pass while the code is broken: `rules/lessons.md` records a suite that stayed green while 600 violations shipped, and tests that reimplemented the logic they claimed to test. Specs drift silently when later work changes the files they govern, because nothing links a spec to its files. Decisions agreed in chat were dropped by `/scope` after a `/clear` (2026-10-11), and `~/.claude/CLAUDE.md` holds only an interim line asking skills to read the brief.

The workflow skills (`/check`, `/test`, `/sync`, `/architect`, `/scope`) are vendored and overwritten on every pull, so an edit to them does not last. Always loaded rule files under `~/.claude/rules/` do last, and reach headless calls (spec 0012 probe).

## Options considered

### Option 1: one new rule file plus deterministic helpers (chosen)
- Pro: survives skill updates; one file to read; the parts that can be code (`spec-paths`, the `wf` line check) are code and tested.
- Con: the chat side still depends on the model following text.

### Option 2: spread over existing rule files
- Pro: no new file.
- Con: each rule hides inside a longer file about something else; harder to see what overrides which skill.

### Option 3: wrapper skills
- Pro: also survives updates.
- Con: skills load only when they trigger, so a headless call can miss the wrapper.

## Rationale

Option 1, which you picked. Forces: the vendored skills cannot be edited durably, and the user rule "a test that passes against broken code is not coverage" (`rules/lessons.md`) needs teeth where nobody watches, which is `wf run`. So the unattended path gets a real check (rule 11a, your pick over rule only), the chat path gets the rule text, and the stale spec warning is a script rather than model judgment (your pick), so it gives the same answer every time and has its own tests. Paths are backfilled on every existing spec (your pick) because the runner specs are the most likely to drift. The brief check lists and asks rather than fixing (your pick), matching how the cross check already treats gaps. The probes run by you (your pick) because a `wf` call cannot start a nested claude.

Decided here without a question: the line is required only when the call ticks its box (your pick on the marker question); `spec-paths` compares the merge base on a branch and the last commit on main; it is linked onto PATH by `install.sh` like `wf`, so the rule can call `spec-paths` in any repo; `**Paths:** none` for a spec that governs no file.
