# 0078. Assertion Guardian guard gaps

**Date**: 2026-10-22
**Status**: Proposed
**Paths:** `config/patches/assertion-guardian.patch`, `tests/test_claude_config.py`
**Amends:** [0068](0068-assertion-guardian-removed-checks.md) (approval source, shell targets, race)

## What you're agreeing to
- Only a `/allow-test-change` you type yourself, or the "allow once" button you click, approves a blocked test change. A model, an agent or another mod can no longer approve one.
- `ln`, `git apply` and `patch` near test files are refused before they run, and paths through symlinks are checked as the file they point at.
- Two shell commands on the same test file in one chat wait for each other, so one's undo can no longer erase the other's new test.
- A second approval after the first says "already allowed once", not "nothing is blocked".

## Summary
A security review of the Assertion Guardian mod (2026-10-22, build-status brief "For /architect later") found ways around it. The change stays in our patch on the upstream mod (`~/.claude/skills/assertion-guardian`, spec 0048 edited entry). Cross check 2026-10-22 corrected the first draft against the code: the state is engine plugin state (no file to guard), the BOM and link restore leftovers are already fixed (`register.tsx:123-130`, `:227-233`), and MultiEdit's existence as a mod tool event is unconfirmed.

## Context
- `hooks/register.tsx:259-268`: `command.run` for `allow-test-change` ignores `e.origin`. The mod API gives `command.run` an `origin: PromptOrigin`; `kind: 'composer'` is the user's own gesture, distinct from `model`, `plugin` and `unclassified` (types `claude-code/index.d.ts:1837-1843`, `:9216-9300`). Tests already pass `origin: {kind: 'composer'}` (`tests/assertion-guardian.test.tsx:267`).
- `register.tsx:311`: the band "allow once" button calls `allow()` from a `ui.render` click.
- `register.tsx:322`: `allow()` clears `blocked`, so a second `/allow-test-change` prints "nothing is blocked" (`:261`) while `allowed` still holds the fingerprint.
- `analyze.ts:619-682` `shellWrites()`: no `ln` branch; `git` handles rm, mv, checkout, restore; `patch` is in WRITERS (`:615`); `refuseBefore` fires for `git|mv|find` only (`:740`). `shellPlan()` is synchronous (`:734`) and resolves paths by spelling (`fold`, `:724-731`).
- `$.fs.stat(path, {resolve: true})` gives `realPath`, absent when the path leads nowhere (types `:3361-3404`). `$.fs` has no exclusive create (`:3325-3404`).
- `runAndCompare` (`register.tsx:147-181`) is the one place a Bash compare runs.

## Requirements
- **AC-1** (approval source) `/allow-test-change` allows only when `e.origin.kind === 'composer'`. Any other origin answers "Assertion Guardian: approval must be typed by you. Nothing allowed." and changes nothing. The band "allow once" button stays an approval (a click is the owner's gesture). Tests: composer allows; `model`, `plugin`, `unclassified` and a missing origin do not.
- **AC-2** (MultiEdit, probe first) Probe P1: does the host send a `tool.call` with `tool: 'MultiEdit'` to mods, and with which argument shape? If yes, MultiEdit gets the Edit check over its edits applied in order, with a test. If no, nothing is built and the probe result is recorded here.
- **AC-3** (more writes) `shellPlan()` sets `refuseBefore` when the line has `ln` with any argument that is a test path, or `git apply` or `patch` at all while the working folder is inside a repo with any test path (their targets come from the patch, not the line). `patch` joins the `refuseBefore` regex.
- **AC-4** (symlinks) In `register.tsx`, before `runAndCompare` and before the Edit/Write check, each target is resolved with `$.fs.stat(target, {resolve: true})`; with no `realPath` (file not there yet) the parent folder is resolved and the name appended; if neither resolves the call is refused before running ("cannot resolve <path>"). Matching and the `before` map use the resolved path. `shellPlan()` stays synchronous.
- **AC-5** (race) An in-memory queue per resolved path (a Map of promises in the mod module) serializes Bash calls with targets, Edit and Write on the same test file within one chat session: a call waits for the earlier ones on any of its paths (sorted order), holds them through compare and any undo, and releases in `finally`. No file and no timer: a call waits as long as the earlier call runs. Calls in two different chats are not serialized (accepted; stated in the README).
- **AC-6** (message) With `blocked` null and `allowed` non empty, `/allow-test-change` answers "Assertion Guardian: the change to <file> is already allowed once." Every reply names the file or why nothing was allowed.
- **AC-7** Spec 0068 gets `**Amended by:** 0078` (bookkeeping).
- **AC-8** Mod tests for each AC (`claude plugin test`); the patch is regenerated with `claude-config.py`; `tests/test_claude_config.py` keeps the patch applying cleanly on the pinned upstream; installed live.

## Decision
Typed by the owner only (owner, 2026-10-22, "Typed by you only"), done with the existing `origin` field; a lock per test file (owner, 2026-10-22, "Lock per test file"), done in memory per session. Rejected: a one time code (a model that reads the block can repeat it); a lock file (no exclusive create in `$.fs`, stale after a crash).

## Build plan
1. Probe P1 (MultiEdit), recorded here. (AC-2)
2. AC-1 with tests; AC-6.
3. AC-3, AC-4 with tests.
4. AC-5 with a two call test; AC-7, AC-8.

## Consequences
- **Good**: the guardian can no longer be approved by the thing it guards.
- **Bad**: two agents on one test file in one chat run one after the other; two chats are not serialized.
- **Neutral**: the patch on upstream grows; spec 0048's merge keeps it.

## Rationale
Options and owner answers above; findings in `docs/briefs/build-status-2026-10-22.md` and `docs/reviews/review-2026-10-21.md`; code facts from the 2026-10-22 cross check.
