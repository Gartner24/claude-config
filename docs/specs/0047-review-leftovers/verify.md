# Verify: Review leftovers 2026-10-15 · spec 0047 · updated 2026-10-15
_Steps derived from spec 0047 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [ ] Feed `wf auto hook` a `UserPromptSubmit` JSON with `"prompt": "/auto release <repo>"` and a `cwd` inside a chat that holds `<repo>`, with `interactive()` true (scratch `XDG_STATE_HOME`) -> prints `released: <repo>`, and `auto.json` no longer lists it under the chat of that `cwd` -> AC-1
- [ ] Same with `"prompt": "/auto release"` -> stdout `usage: /auto release <names>`, nothing changes -> AC-1
- [ ] Same with a `cwd` in no chat -> `refused: off`; the other chat keeps its repo (the hook's folder decides, not the process folder) -> AC-1
- [ ] `WF_RUN=1 wf auto release <repo>` -> `refused: user_only`, exit 5 -> AC-1
- [ ] `fnmatch` the `live/settings.json` deny rules against `wf auto release x`, `cd /x && wf auto release x`, `python3 runner/wf.py auto release x` -> each matches a deny rule; no allow rule matches `wf auto release x` -> AC-2
- [ ] Read the refusals: `wf auto on <repo>` from a second folder while a live chat holds it -> `left out <repo>: held by the chat in <folder>: ask the user to type /auto release <repo> in that chat`; `wf auto take <repo>` -> `refused: ... held by the chat in <folder>: ask the user to type /auto release <repo> in that chat`; with that chat idle -> `..., idle: only the user moves it, by typing /auto release <repo> there or /auto on <repo> here` -> AC-3
- [ ] `auto.DRIVE` step (5) says to write the brief first, then ask the user to type `/auto release <name>` here; step (6) says never run `wf auto on` or `wf auto release`; `live/skills/auto/SKILL.md` names release in its description, `argument-hint` and the "Claude can never run" line -> AC-3
- [ ] A `/check verify` call on a feature with a later waiting box that ends `LEFT TO BOX: <box>` plus `CAN FAIL CHECKED: 0` and writes `left to the box: <box>` (any case, bullets or bold) into a `verify.md` under the specs folder -> passes to the next box -> AC-4
- [ ] The same call without the note, with a note whose text only contains the box text, or with the note already in verify.md before the call -> parks `unchecked` -> AC-4
- [ ] `auto.counts` with two active.json entries of one repo, one tree locked and one not -> `1 feature(s) in 1 repo(s)`; with `run.repo_lock` raising OSError -> both count -> AC-5
- [ ] `python3 runner/tests/fast.py` -> 0 failed -> AC-6

## Value sourcing
- [ ] Release names come from the typed prompt: `/auto release OTHER` matches folder `other` (case insensitive), `/auto release a/b` refuses as not a repo name -> AC-1
- [ ] Release chat comes from the hook's `cwd`, not the process folder (step 3 above) -> AC-1
- [ ] Changed verify notes come from the before and after snapshots: a note in a verify.md the call did not change never counts (step 9, stale case) -> AC-4
- [ ] A run is going per entry's own lock: a stale tree entry beside a locked sibling tree is not counted (step 10) -> AC-5

## Acceptance-criteria coverage
- AC-1 steps 1 to 4, value steps 1 and 2 · AC-2 step 5 · AC-3 steps 6 and 7 · AC-4 steps 8 and 9, value step 3 · AC-5 step 10, value step 4 · AC-6 step 11
