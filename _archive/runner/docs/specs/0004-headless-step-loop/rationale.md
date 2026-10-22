# 0004. Headless step loop: decision record

## Context

Release 1 (`next <repo>`, spec 0002) removed the mechanics of starting a step: the `/clear`, the retyping, the wrong folder. You still sit at the keyboard for every step. The research counted 33 human touches to start one build, and most of what remains after `next` is pressing Enter between steps and answering panels. Release 2 is one feature built with nobody there.

The forces are set by how the skills work. State lives in repo files, resolved from the working folder, and every box is a command, so the next step can be computed from the scope rather than from chat output. A fresh session per step is the clean equivalent of the `/clear` you type today. The loop runs on your laptop, on your subscription, often overnight: it must not let the machine sleep, must not run twice on one repo, must not spend a whole usage window on one runaway call, and must stop cleanly when you press Ctrl C.

Scope boundaries are tight on purpose. Answering panels and phone pings (feature 5), standing answers (6), headless verify (7), retry and park policy (8), design enforcement (9), queues (10), usage planning (12) and commits and PRs (14) are separate features. This feature has to behave safely before any of them exist, which mostly means stopping with a clear reason where they would later take over.

Settled before this spec (research section 0, not asked again): each call is a fresh `claude -p`; a lock per repo; budget, wall clock and run caps; `nosleep` for the run; SIGINT for a clean stop; paid steps never run unattended; web content is data only.

## Options considered

### Option 1: Own driver around `claude -p`, inside `wf` (chosen)

`wf run` loops: run the box as `claude -p <command> --output-format json`, read the JSON result, reread the scope, decide, repeat. Caps, lock and signals live in the driver.

**Pros**:
- Stdlib only, the same program and parser as `wf next`; no new dependency (spec 0001).
- Each call is a separate process, so a crash, timeout or Ctrl C affects one step and the files show exactly how far it got.
- `--max-budget-usd`, `--permission-prompts none` and `--disallowedTools` give per call limits without touching your settings.

**Cons**:
- A question inside a step cannot be answered mid call; until feature 5 adds the defer hook and resume, it can only stop the run.
- Reads Claude Code's JSON output shape, which can change between versions.

### Option 2: Agent SDK driver

A long lived Python process using the Agent SDK, whose `canUseTool` callback sees AskUserQuestion and can wait for your reply.

**Pros**:
- Native question handling, so feature 5 would fit without a defer and resume dance.

**Cons**:
- Needs the SDK package installed, breaking the stdlib only rule of spec 0001 and the clone and run property of this repo.
- The process must stay alive through every wait; a laptop sleep or crash loses the session state the driver holds.

### Option 3: An existing Ralph style runner

continuous-claude, ralph-claude-code or snarktank/ralph: loops and limits already built.

**Pros**:
- Loop, caps and logging exist today.

**Cons**:
- They drive their own task files, not your scope boxes, and have no real human escalation.
- continuous-claude merges and pushes per run, the opposite of the never push rule; adapting them means maintaining a fork.

### Option 4: One long session with `/loop` or `/goal`

A single interactive or headless session told to work through the feature box by box.

**Pros**:
- No driver code at all.

**Cons**:
- No fresh context per step, so context fills up and degrades across a whole feature, the thing `/clear` exists to prevent.
- Caps, lock and a clean stop would rely on the model following instructions rather than on a process boundary.

## Rationale

The deciding force is that the scope files, not the session, are the state. Option 1 is the only one that treats each step as disposable: a call can crash, time out or be interrupted and the next decision is still made from what the files say. That is also what makes `no_progress` a reliable stop: the driver never trusts what a call claims, only whether the next box changed. Option 4 keeps everything in one context and so loses both the fresh context and the process boundary the caps depend on.

Option 2 would make feature 5 easier, but it trades away the stdlib rule that keeps `wf` installable from a clone, and it holds the state in a live process, which is the wrong place for an overnight run on a laptop. The defer hook plus `--resume` that feature 5 will use keeps state on disk, consistent with Option 1. Option 3 solves the easy half (looping) and gets the hard half (your scope format, human escalation, never pushing) wrong.

Choices made in the interview, and why: one feature per run with an explicit `/sync` call, because the queue is feature 10 and an explicit final call proves `/sync` ran. Autopilot `allowed` is required because spec 0003 made `off` the default precisely so no repo runs before you switch it on. Questions are denied rather than left hanging, because a `-p` call has nobody to answer, and an explicit `DECISION NEEDED:` line turns a stall into a readable stop. The child call runs in its own session so Ctrl C reaches `wf` alone, which is what lets the first Ctrl C be graceful and still record the run. The inhibitor is `wf`'s own child rather than your `nosleep`, so the run can end it without ending one you started.

Changes after the cross check (a read only review on another model, all applied on your call): an allow list of commands instead of blocking only `/architect`, so a box that posts, bills or needs you never runs unattended; refusing a detached checkout and a box outside any feature; SIGHUP and SIGTERM handled like Ctrl C plus an inhibitor held by `tail --pid`, so a closed terminal or `kill -9` never leaves a call running unlocked or the machine pinned awake; a non truncating lock open, atomic `run.json` writes and an `internal_error` record; Autopilot reread before every call; a wider push deny list. You also asked for `handle-lid-switch` in the inhibitor, so a run survives the lid closing.

Decided by the architect (not asked), with the runner up: refusing `no git` and an unreadable branch alongside `main` and `master`, because an unattended run with no version control has no undo (runner up: allow it with a warning). A 30 second grace between SIGINT and SIGKILL on timeout, long enough for claude to finish writing its session (runner up: 10 seconds). Box identity for the progress check is feature, box text and note, because a ticked milestone changes the note even when the parent box is still the first open one (runner up: file and line, which shift whenever a skill edits lines above).
