# 0016. Guard hook false alarms: rationale

Decision record for [index.md](index.md).

## Context

The hook is a PreToolUse guard on every Bash call, in every permission mode, `wf run` calls included. It runs `grep -E` patterns over the raw command string. On 2026-10-11 it blocked a `git commit` whose message named a deletion command, and a scope edit whose text did. A blocked call in `wf run` shows up as a `denied` park (spec 0008 AC-5), and with spec 0014 two in a row stop the run. The hook is a copy in this repo (`hooks/block-destructive.sh`); the live file is `~/.claude/hooks/block-destructive.sh`, hashed by every `wf run` as a guarded file (spec 0007 AC-7). Its known limit stays: static text matching, a backstop against careless commands, not an adversary. A first draft rebuilt the command from parsed tokens; the cross check showed it lost redirects, newlines, line continuations, substitutions and `$'...'` quoting, so this design changes only data regions.

## Options considered

1. In place blanking of data regions (chosen). Pro: outside data regions the text is byte for byte the same, so every pattern keeps matching what it matches today; the raw fallback makes the worst case today's behavior. Con: commands that run a shell or interpreter keep their false alarms; a second language in the hook.
2. Rebuild the command from `shlex` tokens (first draft). Pro: fewer false alarms left. Con: the cross check found ten ways it let blocked commands through (redirects, newlines, continuations, substitutions, `$'...'`, the fork bomb in a payload, wrapper words).
3. Rewrite the hook in Python. Con: every pattern ported, a rule can slip in the move.
4. Bash only. Con: quote handling in bash is fragile exactly where it matters.

## Rationale

A security hook may trade false alarms for safety, never the reverse. Changing only characters inside data regions, and only into a neutral `_`, cannot create a match that was not there and keeps quoted paths visible to the target patterns. Any command that runs code is left raw because inside it no quoted string can be trusted as data. You picked this redesign after the cross check.
