# chip-dash

Renamed to chip-dash 2026-10-22 (was wf-dash; command /chip, /wf-dash kept as alias).

Source: specs 0058, 0059, 0060 (accepted 2026-10-17) and the owner's words that day; spec 0071 (2026-10-22) for today's surfaces. Nothing here is new; where a line is inferred it says so.

## What it is
A Claude Code mod for one person, the owner, who runs an unattended build runner (`wf`) across several repos and conducts it from chat sessions.

## Surfaces
Today (2026-10-22, the runner retired; spec 0071):
- Band above the prompt: this session (model and effort, folder, git, context, 5 hour and weekly use), `owed N` when this chat owes a step, and the auto handoff. Always visible.
- Dashboard `/chip` (alias `/wf-dash`), three views: Plan (`p`, every plan from `plan.py`, a confirmed start), Now (`n`, what this chat owes, your open PRs with their checks, the handoff, an agents count), Agents (`a`, this chat's agents and shells, a confirmed stop).

History (specs 0058 to 0060, the runner):
- Band above the prompt: this session and the runner (running, parked, questions). Always visible.
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
