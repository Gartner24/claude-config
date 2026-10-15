# 0051 · Verify

## P1 a call cannot write the private switch (2026-10-15): pass
Read from the argv of a real `wf` build call (row 54's `/develop`, 2026-10-15, process captured in the conductor session): `--disallowedTools` holds `Edit(//home/santiago/.claude/private/**)`, and the call's sandbox settings list `/home/santiago/.claude/private` in `denyWrite`. So neither the Edit and Write tools nor a Bash command inside the sandbox can write `~/.claude/private/pr.json`; the source is `SECRETS` (`runner/run.py:347`) through `never_writable()`. The build adds a unit test that pins this (AC-1).
