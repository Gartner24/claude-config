# wf-dash

Source: specs 0058, 0059, 0060 (accepted 2026-10-17) and the owner's words that day. Nothing here is new; where a line is inferred it says so.

## What it is
A Claude Code mod for one person, the owner, who runs an unattended build runner (`wf`) across several repos and conducts it from chat sessions.

## Surfaces
- Band above the prompt: this session (model and effort, folder, git, context, 5 hour and weekly use) and the runner (running, parked, questions). Always visible.
- Toasts: a run finished, a feature parked, a question appeared. Once per event.
- Panes `/plan`, `/agents`, `/runner`: the whole plan, every worker, every run, with three confirmed safe actions.
- Short bottom bar once the band is live.

## Mode
Operate. Success is knowing where everything stands without asking, at a glance, and acting safely.

## Owner's words
- "full control without asking where things stand" (spec 0060 summary)
- wants the mods to look beautiful (2026-10-17)
- wants to finish fast; every question gets a recommended answer

## Constraints
- Colors are Claude Code theme keys; the owner's terminal theme decides the hues.
- ASCII only.
- Unknown is `?`, never 0. A failed fetch keeps the last good value marked stale, never an empty list.
- Never pushes, merges or deletes.

## Inferred
- Terminal width 100 to 200 columns (laptop, external monitor); the band must still read at 80.
