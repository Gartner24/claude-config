# Autonomous mode: the session drives the runner

## Agreed so far, do not ask again
- Your idea (2026-10-13): a mode, shown in the status bar, that ties the session to the runner. While it is on, the session runs `wf` itself; you never open a terminal for it. It stays on through `/clear`. You turn it off with a command (and a status bar control if one is possible). It is the last runner item, after Telegram.

## Research (2026-10-13, Claude Code docs at code.claude.com/docs/en/{hooks,statusline,skills,keybindings,permission-modes,goal,scheduled-tasks}, the local jjstack status line, the official ralph-loop plugin)
- Survives `/clear`: the SessionStart hook fires with `source` `startup`, `resume`, `clear`, `compact` or `fork`; its stdout (or `hookSpecificOutput.additionalContext`) is added to the new context. UserPromptSubmit can add a one line reminder on every turn. Built in modes (`/goal`, auto permission mode, `/loop`) do not survive `/clear`; a state file read by a hook does (ralph-loop keeps its state in a file).
- Status bar: `statusLine` runs a command on events (new message, mode change) and on `refreshInterval` (seconds, minimum 1); ANSI colors and several rows work. The only click it supports is an OSC 8 link that opens a URL (Ctrl+click on Linux); nothing in the status bar or in `keybindings.json` can run a command. So the off switch is a command; the bar only shows the state.
- jjstack's bar is `~/.claude/skills/jjstack/bin/statusline.sh` (model, folder, git, context, usage). A jjstack update overwrites edits there, so the mode segment goes in a small wrapper that runs jjstack's script and appends the segment.
- Toggle command: a user only skill can run a shell line before Claude sees it (`` !`cmd` ``), so `/auto on` and `/auto off` write the state file directly.
- Background work: a Bash `run_in_background` command outlives the turn but its fate on `/clear` or session exit is not documented; `systemd-run --user` puts `wf` outside the session entirely.

## Plan
1. State file `~/.local/state/wf/auto.json`: `on`, the folder it was turned on in, `since`. One file; turning it on in a second folder moves it (only one driving session).
2. `/auto on` and `/auto off`: user only skills that write the file (`disable-model-invocation: true`). Natural words work too ("deactivate autonomous" makes Claude run `/auto off`'s script).
3. SessionStart hook (all sources) in that folder: when on, add the driving instructions: start `wf -y` when there is work and no run, never wait in chat, relay open questions and the report, start again when new features get queued or answers arrive.
4. UserPromptSubmit hook: one line each turn, "autonomous: on, wf <state>, <n> questions open".
5. `wf` is started with `systemd-run --user --unit wf-auto` so it survives `/clear`, closing the window and the session ending; `wf` already refuses a second run on a held repo, and the unit name stops a double start.
6. Status bar wrapper: jjstack's line plus an `AUTO` segment (green on, with "running 2 repos, 1 question" from `wf` state), `refreshInterval: 5`.
7. Off: `/auto off` stops new starts; a run already going finishes its current features unless you say "stop now".

## Probes on the real claude before building
- P1: SessionStart output after `/clear` reaches the model (a marker word it repeats).
- P2: a `systemd-run --user` `wf` keeps running after `/clear` and after the window closes.
- P3: `refreshInterval` updates the bar while idle.
