# Ask, never stop

## Agreed so far, do not ask again
- The problem (your words, 2026-10-13): runs are for long nights. Today a run stops about an hour in whenever a step needs to touch something the run is not allowed to touch (`~/.claude`, the runner's own `runner/`, `.git/hooks`), and in the morning nothing is built. Editing those is on purpose, it is the work. It needs your OK, not a stop.
- Not the fix: more checks, preflights or rules that predict blocks. They add depth and still leave the night idle.
- The fix:
  1. Per repo standing permission: you allow once, ahead of time, which protected places a repo's runs may write (claude-config: `~/.claude`, `runner/`, `.git/hooks`). One line in that repo's `AGENTS.md` `## Standing answers`, or one question on the `wf` confirm screen the first time. With it, the run's calls get those paths writable and simply go on. Nothing stops.
  2. Without a standing permission, a step that needs a protected path does not park: it asks on your phone ("allow claude-config to write ~/.claude/rules? yes / no / always"), keeps building every other feature meanwhile, and resumes that step the moment you answer. "always" writes the standing permission.
  3. A run guarding itself against changes to `~/.claude` accepts changes made by its own allowed calls (they are the work), and still stops on a change from anywhere else.
- Widened the same day (your message: "I say do spec 1, 2, 4, 5, 12, 14 ... n and wake up with it done"): the same rule for every reason a feature is set aside today, not only protected paths. Nothing is set aside silently. Each one becomes a phone question with a recommended action, the run keeps building everything else, and your answer resumes it (in the same night, or on the next `wf`):
  - `denied` (protected path): allow / always / skip, as above.
  - `blocked` (login, sudo, hardware, missing locked design): what is needed, with "done, go on" / skip.
  - `verify_failed` after its debug attempts, `no_progress`, `debug_touched`, `unchecked`, `design_gate`: what failed, with "try again with this hint" (free text) / skip.
  - caps (`budget`, `max_calls`, `call_timeout`): "give it more" / skip.
  - on `main`: the run makes the feature branch itself, no question.
  - `guard_changed` from outside the run, `crash_loop`, `app_failed`: ask, with retry / skip; only these may also pause the repo, never the whole run.
- Builds on the decision queue (spec 0011) for the phone question and on `wf` (spec 0020) for the confirm screen.

## Open for /architect
- The exact standing permission line and which places it can name (never secrets: credentials, ssh, gh, private/).
- How an allowed call's own `~/.claude` writes are told apart from outside changes.
