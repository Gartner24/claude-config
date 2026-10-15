# Verify: Review leftovers 2026-10-15 · spec 0047 · updated 2026-10-15
_Steps derived from spec 0047 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [x] Feed `wf auto hook` a `UserPromptSubmit` JSON with `"prompt": "/auto release <repo>"` and a `cwd` inside a chat that holds `<repo>`, with `interactive()` true (scratch `XDG_STATE_HOME`) -> prints `released: <repo>`, and `auto.json` no longer lists it under the chat of that `cwd` -> AC-1
- [x] Same with `"prompt": "/auto release"` -> stdout `usage: /auto release <names>`, nothing changes -> AC-1
- [x] Same with a `cwd` in no chat -> `refused: off`; the other chat keeps its repo (the hook's folder decides, not the process folder) -> AC-1
- [x] `WF_RUN=1 wf auto release <repo>` -> `refused: user_only`, exit 5 -> AC-1
- [x] `fnmatch` the `live/settings.json` deny rules against `wf auto release x`, `cd /x && wf auto release x`, `python3 runner/wf.py auto release x` -> each matches a deny rule; no allow rule matches `wf auto release x` -> AC-2
- [x] Read the refusals: `wf auto on <repo>` from a second folder while a live chat holds it -> `left out <repo>: held by the chat in <folder>: ask the user to type /auto release <repo> in that chat`; `wf auto take <repo>` -> `refused: ... held by the chat in <folder>: ask the user to type /auto release <repo> in that chat`; with that chat idle -> `..., idle: only the user moves it, by typing /auto release <repo> there or /auto on <repo> here` -> AC-3
- [x] `auto.DRIVE` step (5) says to write the brief first, then ask the user to type `/auto release <name>` here; step (6) says never run `wf auto on` or `wf auto release`; `live/skills/auto/SKILL.md` names release in its description, `argument-hint` and the "Claude can never run" line -> AC-3
- [x] A `/check verify` call on a feature with a later waiting box that ends `LEFT TO BOX: <box>` plus `CAN FAIL CHECKED: 0` and writes `left to the box: <box>` (any case, bullets or bold) into a `verify.md` under the specs folder -> passes to the next box -> AC-4
- [x] The same call without the note, with a note whose text only contains the box text, or with the note already in verify.md before the call -> parks `unchecked` -> AC-4
- [x] `auto.counts` with two active.json entries of one repo, one tree locked and one not -> `1 feature(s) in 1 repo(s)`; with `run.repo_lock` raising OSError -> both count -> AC-5
- [x] `python3 runner/tests/fast.py` -> 0 failed -> AC-6

## Value sourcing
- [x] Release names come from the typed prompt: `/auto release OTHER` matches folder `other` (case insensitive), `/auto release a/b` refuses as not a repo name -> AC-1
- [x] Release chat comes from the hook's `cwd`, not the process folder (step 3 above) -> AC-1
- [x] Changed verify notes come from the before and after snapshots: a note in a verify.md the call did not change never counts (step 9, stale case) -> AC-4
- [x] A run is going per entry's own lock: a stale tree entry beside a locked sibling tree is not counted (step 10) -> AC-5

## Run 2026-10-15 (/check verify, PASS)
Driven against the real code: `wf auto` functions through a scratch `XDG_STATE_HOME`/`XDG_CONFIG_HOME` with three git repos (only `interactive()` forced true, since this session runs under Claude), the real `wf.py auto release` CLI, and `wf run` with the harness's fake claude for AC-4. Mutants were applied from a `cp` backup and restored; `git diff` empty after.
- Step 1: hook `/auto release OTHER`, cwd chatA, process cwd elsewhere -> `released: Other`, chatA holds only chatA. can fail: the hook passes the process folder to release (mutant: `release(switch[1])` -> `refused: off`, seen).
- Step 2: bare `/auto release` -> `usage: /auto release <names>`, state unchanged. can fail: the bare case falls through to release() and prints usage on stderr only.
- Step 3: hook cwd in no chat, process cwd chatA -> `refused: off`, chatA keeps Other. can fail: same mutant as step 1 (released Other from chatA, seen).
- Step 4: `WF_RUN=1 wf.py auto release chatA` -> `refused: user_only`, exit 5; without WF_RUN `wf.py auto release chatB` -> `released: chatB`, exit 0. can fail: the WF_RUN guard dropped from release().
- Step 5: fnmatch over `live/settings.json`: `wf auto release x` deny `*wf auto release*`, `wf auto release*`; `cd /x && ...` deny `*wf auto release*`; `python3 runner/wf.py auto release x` deny `*wf.py auto release*`; no allow rule matches; `wf auto take x` still allowed. can fail: the allow rule kept or a deny form missing. This models Claude Code's matcher the same way the 0046 pins do; the real permission engine refusing it in a live session is left to the box below.
- Step 6: on from chatB while chatA live -> `left out Other: held by the chat in chatA: ask the user to type /auto release Other in that chat`; take from chatB -> `refused: Other is held by the chat in chatA: ask the user to type /auto release Other in that chat` (rc 5); chatA idle -> `refused: Other is held by the chat in chatA, idle: only the user moves it, by typing /auto release Other there or /auto on Other here`. can fail: an old "release it there first" text left in any of the three.
- Step 7: the DRIVE text the hook printed carries step (5) brief first, then ask the user to type `/auto release <name>` here, and (6) never run `wf auto on or wf auto release`. SKILL.md read: description, `argument-hint: on [repos] | off [now] | release <repos>`, and the "Claude can never run" line name release (a read of the change's own text, not counted as can fail).
- Step 8: `wf run` verify call with the note (`> - **left to the box:** use it for a WEEK`) and `LEFT TO BOX` + `CAN FAIL CHECKED: 0` -> next call `/test a`. Also a resumed verify (question answered) that rewrites its note -> passes on to `/test a`. can fail: no snapshot before a verify call (mutant: valid case reran verify, seen).
- Step 9: no note, a note for a longer text, a note already present before the call -> each parks `unchecked` after 2 calls; a resumed verify whose note was written only by the pre resume call -> parks `unchecked`. can fail: the note check ignored (mutant: all three ran on to `/test`, seen); every verify.md counted as changed (mutant: stale and resume cases ran on to `/test a`, seen).
- Step 10: two active.json entries of chatA, trees tree1 and tree2: no lock -> `''`; tree1 locked -> `1 feature(s) in 1 repo(s)`; tree1 and repo locked -> still 1; `run.repo_lock` raising OSError -> 2. can fail: the count gated on the repo lock (mutant `building(repo)` -> 2 with tree1 locked, seen).
- Step 11: `python3 runner/tests/fast.py` -> `Ran 874 tests in 91.2s, 0 failed`.
- Value steps: `/auto release OTHER` matched folder `Other`; `/auto release a/b` -> `refused: "a/b" is not a repo name`; the hook cwd decided (steps 1, 3); stale and resume notes (step 9); per entry lock (step 10).
- Not specced, worth a look in review: the proof line recheck after a call that was itself a `retry` keeps the snapshot from before the first try, so a note from that first try would count.
- left to the box: Install it live after the merge, from main (the plan branch does not hold this feature's code)
  (the real Claude Code permission engine refusing `wf auto release` and a real typed `/auto release` in an interactive session need the installed settings and a live chat)

## Acceptance-criteria coverage
- AC-1 steps 1 to 4, value steps 1 and 2 · AC-2 step 5 · AC-3 steps 6 and 7 · AC-4 steps 8 and 9, value step 3 · AC-5 step 10, value step 4 · AC-6 step 11
