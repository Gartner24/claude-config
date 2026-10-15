# 0012. Waiting boxes owed to you

**Date**: 2026-10-12
**Status**: Accepted
**Paths:** `runner/wf.py`, `runner/run.py`, `live/rules/scope-contract.md`, `runner/tests/**`
**Amends**: [0002](../0002-next-repo-command/index.md) AC-6 (what makes a box waiting) and [0003](../0003-scope-contract/index.md) (a new box segment, rule file line).
**Amended by**: [0014](../0014-runner-resilience/index.md) - a waiting box that also ends ` · later boxes go on` is passed over, not refused; an untagged one stops as before.

## Summary

Some scope boxes only you can close: a check on the real claude, on your phone, a login. Today `wf` guesses them from the words `after` or `waits on` in a milestone, and the last `wf run` missed one (spec 0006 AC-9) and looped `/develop`. This spec adds an explicit marker, ` · waits on you` at the end of any box. Neither `wf run` nor `next` ever runs a marked box; both say it waits on you, and every skill that writes scope boxes learns the marker from the always loaded rule file.

## What you're agreeing to

- A box ending ` · waits on you` is yours. `wf run` refuses or parks it with `waiting` and makes no call.
- `next` never launches a marked box. It prints `waits on you: <text>` and stops.
- The old `after` and `waits on` words keep working on milestones. Top level boxes wait only on the marker. A near miss like `· waits on you.` gets a warning, not a silent run.
- Any skill writing a scope box adds the marker when only you can close it. You tick the box yourself when done.

## Requirements

**User stories**:
- As you, I want a box only I can close to stop `wf run` cold, so that a night is never spent looping on a manual check.
- As you, I want `next` to tell me a box is mine, so that I know to do it myself.
- As you, I want the skills to write the marker for me, so that I never have to remember the syntax.

**Acceptance criteria**:
- **AC-1** (marker): a box is marked when its text (`Box.text`: the text after `[ ]`, cleaned and stripped, as `parse_text` builds it) matches `·\s*waits on you\s*(?=·|$)`, case insensitive. The marker is a whole `·` segment, the same shape as `· auto` (spec 0003 AC-5), so `· waits on you, phone` and `· waits on your merge` are not the marker. The marked text is that box text with every marker segment removed and the result stripped. Ticked boxes, boxes under `## Deferred`, in comments or in fenced blocks are never picked, so their marker does nothing (spec 0002 AC-5, unchanged). Near miss: when the picked box or its note box (AC-2) contains `waits on you` (case insensitive) but is not marked, the candidate gets the warning `"waits on you" is not the marker here, end the box with " · waits on you": <text>` in `c.warnings`, so it shows wherever warnings show today. The box is not treated as marked.
- **AC-2** (which boxes count): `pick_next` passes `NextBox` the note box itself, not only its text: for an open milestone (the picked box has a parent) the note box is the picked box; for a top level box it is the first open box under it (`under`), or none. `NextBox` gains `owed`: the marked text of the picked box when it is marked; else the note box's marked text when it is marked; else `None`. `waiting` becomes true when `owed` is set, or when the note matches `\b(after|waits on)\b` as today. A top level box's own text is never checked for the `after` or `waits on` words, unchanged.
- **AC-3** (`next`): when `owed` is set, `no_start` prints `waits on you: <owed>` (instead of a launch line or `no command in this box, run it yourself: <text>`), then the warnings as today, and returns 3. So `next` never launches a marked box, with or without a command, `-y` or not. The raw note is not printed.
- **AC-4** (removed while drafting: folded into AC-3 after the cross check; the number is kept so references stay stable).
- **AC-5** (`wf run`): `start_checks` tests `owed` before `wf.no_start`, and `box_refusal` checks `owed` first, before `no_command`, `no_feature` and `manual_box`, returning `("waiting", "waits on you: <owed>")`. So at start a marked box always prints `refused: waiting: waits on you: <owed>` through the existing `refuse` (its `wf.clean`), exit 5, never the exit 3 of `no_start`. Mid feature it parks `waiting` through the existing park path (spec 0008 AC-1; spec 0011 AC-9 and AC-10: not recorded, clears when the files change). Once spec 0011 is built, its AC-3 makes the same `box_refusal` result a `skip: <feature>: waiting` line; spec 0011's build must keep the `owed` test ahead of its own box checks. For an unmarked box the checks, their order, reasons and details are unchanged.
- **AC-6** (unchanged surfaces): `--list` columns, the picker, the feature display, status tags and `· auto` handling do not change; `--list` never showed the note, so a marked box with a command looks like any other there (accepted). `confirm` and `progress_key` never see a marked box, so they need no case. The marker sits on a box, never on a heading.
- **AC-7** (rule file): `~/.claude/rules/scope-contract.md` gains exactly this line under `## Tags and boxes`, staying within spec 0003's 25 line cap:
  `- A box only you can close (a check on the real claude or your phone, a login, a purchase, someone else's action) ends with \` · waits on you\`. Any skill writing a scope box adds it; you tick the box yourself; never put it on a box \`wf run\` should run.`
  Synced into `rules/` with `./sync.sh`.
- **AC-8** (headless probe, `verify.md`): in a scratch repo, `claude -p` runs `/scope` asked to enroll a feature whose plan includes a check on your phone; the written box ends with ` · waits on you`. Then `wf run` on that repo (Autopilot allowed, trusted, work branch), with that box as the next box, prints `refused: waiting: waits on you: <text>` (or the spec 0011 `skip:` line) and makes no call. If the box comes out unmarked, run the probe once more; a second miss means the AC-7 line is reworded (never the skill) and the probe rerun. Command and result recorded in `verify.md`.

## Decision

**Chosen option**: Option 1: a ` · waits on you` box segment, checked on the picked box and its note box, winning over every other box check.

Explicit marker beside the old words, read in `wf.py`, refused first in `run.py`, taught through the rule file.

## Feature design

**Data model sketch** (in memory only):
- `NextBox.owed`: string or `None` (AC-2). `NextBox.waiting` keeps its meaning and is true whenever `owed` is set.
- One new pattern in `runner/wf.py`, `OWED = re.compile(r"·\s*waits on you\s*(?=·|$)", re.I)`, beside `AUTO_TAG`.
- `pick_next` passes the note box (AC-2) so `NextBox` can test it. No file format change beyond the segment, no stored state.
- The near miss warning (AC-1) is appended to `Candidate.warnings` where the candidate's next box is computed.

**Value sourcing**:
| Action | Value produced / displayed | Source |
|---|---|---|
| parse | marked or not | `OWED` on `Box.text` (AC-1) |
| parse | `owed` text | `Box.text` with `OWED` segments removed and stripped, picked box first, then the note box (AC-1, AC-2) |
| parse | `waiting` | `owed is not None` or the note matching `WAITING` (AC-2) |
| parse | near miss warning | `waits on you` in the picked or note box text without an `OWED` match; fixed string in AC-1 |
| `next` | `waits on you: <owed>`, exit 3 | `NextBox.owed` via `no_start`; exit code 3 from spec 0002 AC-6 (AC-3) |
| `wf run` at start | `refused: waiting: waits on you: <owed>`, exit 5 | `owed` tested in `start_checks` before `no_start`; printed by `refuse` (AC-5) |
| `wf run` mid feature | park `waiting`, detail `waits on you: <owed>` | `box_refusal` (AC-5); scope of the reason from spec 0008 AC-1 / spec 0011 AC-9 |
| skill writes a box | ` · waits on you` | rule file line (AC-7) |

**Key invariants**:
- A marked box is never sent to `claude` by `wf run`, whatever its command.
- An unmarked box behaves exactly as before this spec, in `next` and `wf run`.
- Only you tick a marked box; no skill and no `wf` code ticks it.

**Security model**:
- The marker only ever removes work from `wf run`, never adds any. A cloned scope that writes it can only make a run do less. Same trust rules as spec 0008.

**Critical test scenarios** (`runner/tests/`, calling `wf.pick_next`, `wf.NextBox`, `run.box_refusal` and the real commands, never a copy of their logic):
- Marker shapes (calling `OWED` directly): `· waits on you`, `· WAITS ON YOU`, `· waits on you · skipped` mark; `· waits on you, phone`, `· waits on your merge`, `waits on you` without the dot do not; `owed` has the segment removed, verifies **AC-1**
- Near miss: a picked box ending `· waits on you.` is not marked and adds the AC-1 warning; `next` shows it, verifies **AC-1**
- Placement: marked top level box with a command; marked top level box with no command; marked open milestone under a ticked parent; unmarked parent whose first open milestone is marked; top level box whose text says `after the build` is not waiting, verifies **AC-2**
- `next -y` on a marked box with a command, a marked milestone under a ticked `/develop` parent, and a marked box with no command each print `waits on you: <text>`, exit 3, no exec, verifies **AC-3**
- `wf run` refuses `waiting: waits on you: <text>`, exit 5, for a marked `/develop` box, a marked `/architect` box (marker wins over `manual_box`) and a marked box with no command (wins over `no_start` and `no_command`); no call; a marked box reached as the next box after a call parks `waiting`, verifies **AC-5**
- Existing `next`, `--list` and refusal tests stay green unchanged, verifies **AC-6**
- Mutation check: drop the `owed` check from `box_refusal`, the mid feature park test goes red; drop it from `start_checks`, the marked no command test goes red (exit 3); make `pick_next` pass no note box, the marked milestone under an unmarked parent goes red, verifies **AC-2**, **AC-5**
- Manual: the AC-8 probe, verifies **AC-7**, **AC-8**

## Build plan

Skateboard: the parser change alone already makes `wf run` refuse marked milestones; each step widens it.

1. `OWED`, `NextBox.owed`, `pick_next` passing the note box, near miss warning, tests, satisfies **AC-1**, **AC-2**
2. `start_checks` and `box_refusal` test `owed` first, tests including the mid feature park, satisfies **AC-5**
3. `no_start` prints `waits on you:` and returns 3 for any marked box, tests, `--list` unchanged, satisfies **AC-3**, **AC-6**
4. Rule file line in `~/.claude/rules/scope-contract.md`, `./sync.sh`; `docs/architecture.md` command section gains one sentence that a ` · waits on you` box is refused `waiting` before the command check, satisfies **AC-7**
5. Headless probe in a scratch repo, recorded in `verify.md`, satisfies **AC-8**

## Consequences

**Positive**:
- A manual check can no longer loop a run; it parks with a reason that says it is yours.
- Skills write one fixed segment instead of hoping their wording contains `waits on`.

**Negative / tradeoffs**:
- The marker is strict: a box written `· waits on you (phone)` is not marked. On a milestone the old words still catch it; on a top level box it runs, with the near miss warning on the confirm line. Accepted for the same reason `· auto` is strict.
- The rule file costs one more line of context in every session.
- `next` will not launch a marked box even when you want the command's help with the manual step; you start `claude` yourself then.
- `next` shows only `waits on you: <owed>`; a milestone note under a marked top level box is not shown.

**Neutral**:
- `after` and `waits on` stay as milestone signals (spec 0002 AC-6), so old scopes need no edit.
- Spec 0011 removes `no_start` from `wf run`'s box checks and turns the start refusal into a per feature skip; its build keeps the `owed` test first (AC-5).

## Follow-up

- [x] When building, add ` · waits on you` to any open box in this repo's `docs/scope/scope.md` that only you can close.
- [x] `/develop` notes the AC-6 amendment in spec 0002 and the new segment in spec 0003 (`**Amended by**` lines).

## Rationale

Decision record (context, options, rationale): [rationale.md](rationale.md). Verify steps: [verify.md](verify.md).
