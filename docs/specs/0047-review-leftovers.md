# 0047 · Review leftovers 2026-10-15

**Date**: 2026-10-15
**Status**: Proposed
**Paths:** `runner/auto.py`, `runner/run.py`, `live/settings.json`, `live/skills/auto/SKILL.md`, `runner/tests/test_auto.py`, `runner/tests/test_auto_chats.py`, `runner/tests/test_fewer_stops.py`
**Amends**: [0046](0046-autonomous-mode-per-chat/index.md) (AC-2, AC-3, AC-4, AC-7), [0045](0045-fewer-avoidable-stops/index.md) (AC-1)

## What you're agreeing to
- Only you release a repo from a chat, by typing `/auto release <names>` in that chat. Claude can still take repos no chat holds, but it can never take one out of another chat.
- A check that hands its parts to a later "waits on you" step passes only when it also wrote "left to the box: <that step>" in its verify notes.
- The status bar's "running" count shows a run only while that run is really going.

## Summary

The review of the 2026-10-15 landing ([report](../reviews/review-2026-10-15.md), Leftovers) found two gaps that change accepted designs and one small count bug. Your answers of 2026-10-15: only you release; a written note is required. Source: plan row 52.

## Requirements

**Acceptance criteria**:
- **AC-1** (release is yours, amends 0046 AC-4): `/auto release <names>`, typed by you in an interactive session (the same `interactive()` check as `/auto on`), drops those repos from the chat of the hook's `cwd` (resolved as 0046 AC-1 says) and prints one `released: <name>` line each. `typed_switch` returns a third verb `release`; the hook calls `release(names, folder)`, which takes a folder like `on` and `off` (default `os.getcwd()`). Names follow 0046 AC-2's rules (split on spaces, each `[A-Za-z0-9._-]+`, case insensitive exact match on a repo of this chat, at most 6, else the whole command refuses). A bare `/auto release` prints `usage: /auto release <names>` on stdout so the skill sees it. `wf auto release` keeps its existing `WF_RUN` refusal.
- **AC-2** (Claude may not release, amends 0046 AC-4): `live/settings.json` removes the allow rule `Bash(wf auto release *)` and denies `Bash(*wf auto release*)`, `Bash(*wf.py auto release*)` and `Bash(wf auto release:*)`, the same three forms as `on`. Accepted cost, as with `on`: Claude is also blocked from a command that only quotes the phrase (a grep, a commit message); your own `! wf auto release <names>` is not blocked, since `!` commands skip permission rules.
- **AC-3** (texts, amends 0046 AC-3 and AC-4): every message that tells the reader to release now says to ask you: `on()` and `take()` refusals read `held by the chat in <folder>: ask the user to type /auto release <name> in that chat`, and the not live refusal reads `held by the chat in <folder>, idle: only the user moves it, by typing /auto release <name> there or /auto on <name> here`. The DRIVE text's step (5) reads: when a repo should move to another chat, first write this chat's agreed decisions about it into the feature's brief under "Agreed so far", then ask the user to type `/auto release <name>` here; step (6) reads: never run `wf auto on` or `wf auto release`. `live/skills/auto/SKILL.md` covers release in its description, its `argument-hint` (`on [repos] | off [now] | release <repos>`) and its "Claude can never run" line. 0046 AC-2's realpath wording is dropped: a name matches by folder name only, since a name may not hold `/`.
- **AC-4** (left to the box, amends 0045 AC-1): before each `/check verify` call, including a resumed one, the runner takes `self.snapshot()` (it already hashes every file under the specs folder, git ignored ones too, so `.workflow/` specs count); after the call it compares the two. A `LEFT TO BOX: <text>` line counts only when its text is one of the listed later boxes (as now) AND a file named `verify.md` whose hash changed in this call holds a line that, after `norm` and the same leading `*`, `>`, `-` and space tolerance as `LEFT_TO_BOX`, starts with `left to the box:` (case insensitive) and whose remaining text, cut to 200 characters, equals the claimed text cut to 200 (case insensitive). A resumed verify call compares against the snapshot taken before that resume, so the note must be written or rewritten in the call that claims it. The `CAN FAIL CHECKED: 0` pass needs at least one line that counts; a line that does not count is ignored, so 0 parks `unchecked` as before. The verify.md may belong to any spec of the repo; the runner does not tie it to this feature's folder.
- **AC-5** (running count, amends 0046 AC-7): a new helper `entry_running(entry)` answers one active.json entry: its tree's runner lock when it has a tree, else its repo's runner lock (`run.repo_lock` held, the check `building()` uses today). `building(repo)` reuses it over that repo's entries plus the repo lock. `counts()` counts an entry only when `entry_running` says so, and no longer gates on `report.locks_held()`. An unreadable lock (OSError) counts as running, as `building()` does today, so a lock problem never hides a real run.
- **AC-6** (tests): AC-1 the typed release from the hook (and its folder), a bare `/auto release`, refusal under `WF_RUN`; AC-2 the deny rules match `wf auto release x` and `cd /x && wf auto release x`, no allow rule does, and `wf auto release x` run directly with `WF_RUN` unset still releases; AC-3 the texts; AC-4 with a matching note (passes), without it, with a note for a longer box text that only contains the claim, and with the note left over from an earlier call (each parks `unchecked`); AC-5 a stale entry of an unlocked tree beside a running sibling tree of the same repo is not counted. Existing pins to update: `test_auto_chats.py` DRIVE regex for release, `test_auto.py` TestSettings (allow list without `auto release *`, `wf auto release x` now denied), `test_auto.py` test_bar (mock `run.repo_lock` instead of `report.locks_held`). Each mutation checked.

## Decision

Release moves behind your typing, like turning a chat on, so a session can never pull a repo out of another chat; taking stays open because it only reaches repos no chat holds. The left to the box claim needs a written note, found by comparing the specs folder before and after the call with the snapshot the runner already takes, so no git state or verify file path has to be guessed.

## Feature design

**Value sourcing**:
| Value | Source |
|---|---|
| release names | the typed prompt after `/auto release` (hook `prompt`) |
| release chat | the hook's `cwd`, resolved as 0046 AC-1 says |
| changed verify notes | `self.snapshot()` before and after the verify call, files named `verify.md` whose hash changed |
| a run is going | `entry_running(entry)`: the entry's tree lock, else its repo lock |

**Security model**: release joins `on` as user only (deny rule plus the interactive check). Take can still add a free repo to another chat if a session changes folder first; it can never remove one, and every repo it reaches is on your `wf allow` list.

**Cross check** (another model, 2026-10-15; all 8 gaps took the recommended fix): the note is found with the existing snapshot, not git (AC-4); a resumed verify needs its own note (AC-4); the note must match the box text exactly, not contain it (AC-4); the running count checks each entry's own lock (AC-5); release takes the hook's folder and answers a bare command on stdout (AC-1); refusal texts no longer tell Claude to release (AC-3); the DRIVE text, skill text and test pins are listed (AC-3, AC-6); the deny rule's cost is stated (AC-2).

## Build plan

1. AC-1, AC-2, AC-3: `typed_switch` and the hook, `release(words, folder)`, settings rules, refusal texts, DRIVE text, skill text.
2. AC-4: snapshot before each verify call and the note check beside the `LEFT TO BOX` reader in `runner/run.py`.
3. AC-5: `entry_running`, `building`, `counts`.
4. AC-6: new tests, the three updated pins, mutation checks.

## Consequences

**Positive**: no chat loses a repo without you; a silent "checked nothing" pass is caught.
**Negative**: moving a repo between chats needs one typed command from you; Claude cannot run a command that merely quotes `wf auto release`; a model could still write the note without trying the check, but the note is on record for you to read.

## Rationale

Your two answers of 2026-10-15 settle the shape; the rest are recommended defaults and the cross check fixes listed above.
