# Ask, never stop

## Agreed so far, do not ask again
- The problem (your words, 2026-10-13): runs are for long nights. Today a run stops about an hour in whenever a step needs to touch something the run is not allowed to touch (`~/.claude`, the runner's own `runner/`, `.git/hooks`), and in the morning nothing is built. Editing those is on purpose, it is the work. It needs your OK, not a stop.
- Not the fix: more checks, preflights or rules that predict blocks. They add depth and still leave the night idle.
- The fix:
  1. Per repo standing permission: you allow once, ahead of time, which protected places a repo's runs may write (claude-config: `~/.claude`, `runner/`, `.git/hooks`). One line in that repo's `AGENTS.md` `## Standing answers`, or one question on the `wf` confirm screen the first time. With it, the run's calls get those paths writable and simply go on. Nothing stops.
  2. Without a standing permission, a step that needs a protected path does not park: it asks on your phone ("allow claude-config to write ~/.claude/rules? yes / no / always"), keeps building every other feature meanwhile, and resumes that step the moment you answer. "always" writes the standing permission.
  3. A run guarding itself against changes to `~/.claude` accepts changes made by its own allowed calls (they are the work), and still stops on a change from anywhere else.
- Builds on the decision queue (spec 0011) for the phone question and on `wf` (spec 0020) for the confirm screen.

## Open for /architect
- The exact standing permission line and which places it can name (never secrets: credentials, ssh, gh, private/).
- How an allowed call's own `~/.claude` writes are told apart from outside changes.
