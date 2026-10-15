---
name: claude-config
description: Sync ~/.claude and the claude-config repo both ways, show drift between them, and update downloaded skills from upstream after a yes per skill (spec 0048).
argument-hint: sync | install | drift | update
---
Drive `~/claude-config/bin/claude-config.py`. It never asks anything itself; you ask the user. No command changes a skill without the user's yes on that skill.

- `drift` (also when no argument is given): run `python3 ~/claude-config/bin/claude-config.py drift`. Show its output grouped as printed, then say in one plain sentence what each group means (live only, missing live, differs). Exit 1 means drift was found, not that the tool failed. Change nothing.
- `sync`: run `python3 ~/claude-config/bin/claude-config.py sync`, then `git -C ~/claude-config status --short`, and show what changed. Do not commit unless the user asks.
- `install`: run it with `--dry-run` first, show the output, and run it for real only after the user says yes.
- `update`: run `python3 ~/claude-config/bin/claude-config.py update --plan`. For each entry it lists, ask the user yes or no, one question per entry, showing its changed files and line counts. For each yes, run `update --apply <entry>`:
  - exit 0: installed; say so.
  - exit 2: a conflict. Nothing was installed. Show the files under `~/.claude/state/claude-config-conflicts/<entry>/` with their `<<<<<<<` markers, help the user fix them, then run `update --apply <entry> --resolved`.
  - exit 1: show the message and stop for that entry.
  Entries listed as "update by hand, not checked" are never applied by the tool; show their `install` command instead.

The drift check runs only here, never at session start. The session start line about upstream checks comes from a hook and only counts days.
