# 0016. Guard hook false alarms

**Date**: 2026-10-13
**Status**: Proposed
**Paths:** `hooks/block-destructive.sh`

## Summary

`block-destructive.sh` (the hook that blocks commands which can wipe data) scans the whole command text, so a commit message or heredoc that only mentions a deletion command is blocked, and an unattended run stalls on it. This spec adds a small step before the existing patterns: inside a quoted string or heredoc body that is plain data, spaces and shell operator characters become `_`, so a quoted sentence can no longer look like a command. Everything else is left byte for byte, and any command that runs a shell or interpreter is scanned exactly as today. Nothing blocked today gets through.

## What you're agreeing to

- Commit messages, `echo`, `printf`, `sed` scripts, `tee` and `cat` heredocs that mention a deletion command pass, including the `git commit -m "$(cat <<'EOF' ... EOF)"` form.
- A command that runs a shell or interpreter anywhere (`sh`, `bash`, `eval`, `ssh`, `xargs`, `python`, `node` and the rest of the AC-2 list) is scanned exactly as today, so its false alarms stay.
- Any parse problem, error, timeout or empty output means today's raw scan.
- `echo "rm -rf /"` is no longer blocked (it was over blocked on purpose).

## Context

The hook is a PreToolUse guard on every Bash call, in every permission mode, `wf run` calls included. It runs `grep -E` patterns over the raw command string. On 2026-10-11 it blocked a `git commit` whose message named a deletion command, and a scope edit whose text did. A blocked call in `wf run` shows up as a `denied` park (spec 0008 AC-5), and with spec 0014 two in a row stop the run. The hook is a copy in this repo (`hooks/block-destructive.sh`); the live file is `~/.claude/hooks/block-destructive.sh`, hashed by every `wf run` as a guarded file (spec 0007 AC-7). Its known limit stays: static text matching, a backstop against careless commands, not an adversary. A first draft rebuilt the command from parsed tokens; the cross check showed it lost redirects, newlines, line continuations, substitutions and `$'...'` quoting, so this design changes only data regions.

## Requirements

**User stories**:
- As you, I want a commit or file edit that only talks about a dangerous command to pass, so runs do not stall.
- As you, I want every command blocked today to stay blocked.

**Acceptance criteria**:
- **AC-1** (fast path): a command with no `'`, `"` and no `<<` is checked exactly as today, on the raw text.
- **AC-2** (raw when something runs code): the command is checked raw, as today, when any word outside quotes, or the first word after `$(` or a backtick, has a basename in `EXECUTORS`: `sh`, `bash`, `zsh`, `dash`, `ksh`, `fish`, `csh`, `tcsh`, `busybox`, `eval`, `exec`, `source`, `.`, `ssh`, `su`, `xargs`, `watch`, `tmux`, `screen`, `script`, `python`, `python3`, `node`, `perl`, `ruby`, `awk`, `gawk`, `php`, `lua`. Words are split on whitespace, newlines and `;`, `&`, `|`, `(`, `)`, `<`, `>`, `{`, `}`, `!`.
- **AC-3** (blank data regions): otherwise an embedded Python 3 stdlib step (a small hand written scanner, no `shlex`) returns the command text unchanged except inside data regions, where each whitespace character (newlines included) and each `;`, `&`, `|`, `<`, `>`, `(`, `)` becomes `_`; the quote characters themselves stay. The unchanged `check()` patterns then scan that text. Data regions:
  1. A single quoted string `'...'`.
  2. A double quoted string `"..."` holding no `$(`, `${` with a nested command, or backtick. A double quoted string holding exactly one `$(cat <<DELIM` heredoc (delimiter bare, `'DELIM'`, `"DELIM"` or `\DELIM`) and nothing else but whitespace before the closing `)` is a data region too (the usual commit message form). Any other double quoted string with a substitution is left as is.
  3. A heredoc body: for each `<<` or `<<-` operator outside quotes, the lines after the current line up to the first line equal to the delimiter (leading tabs stripped for `<<-`), bodies taken in operator order when one line has several. The rest of the operator's own line stays as is.
  Never data: `$'...'` and `$"..."` strings (left as is), unquoted text, a backslash escape outside quotes, the delimiter lines.
- **AC-4** (failure means raw): an unclosed quote, a heredoc with no end line, a substitution whose closing `)` cannot be matched, any exception, a nonzero exit, empty output for a non empty command, more than 2 seconds, or a missing `python3` all mean the raw command is checked, as today.
- **AC-5** (self checks): `bash hooks/block-destructive.sh --test` keeps every current case (the `echo "rm -rf /"` note becomes an `allow`) and adds:
  - allow (each blocked today, checked 2026-10-13 against the current hook): `git commit -m "docs: rm -rf / was the bug"`; `git commit -m "$(cat <<'EOF'` with a body line `rm -rf ~` then `EOF` and `)"`; `cat <<EOF > notes.md` with a body naming `mkfs.ext4 /dev/sda`; `sed -i 's/a/mkfs.ext4 x/' f`; `echo "wipe it with mkfs.ext4 /dev/sdb1"`; `printf '%s\n' 'dd if=/dev/zero of=/dev/sda'`.
  - still blocked (each blocked today, and each must stay blocked): `cat x >/dev/sda`; `: > /home/santiago/f`; `echo hi` newline `find / -delete`; `rm -rf \` newline `/`; `rm -rf $(echo /)`; `` rm -rf `echo ~` ``; `rm -rf $'/'`; `rm -rf "$HOME"`; `rm -rf "/home/x y"`; `bash -c ':(){ :|:& };:'`; `nohup sh -c 'mkfs.ext4 /dev/sdb1'`; `timeout 5 bash -c 'dd if=/dev/zero of=/dev/sda'`; `cat <<EOF | sh` with body `mkfs.ext4 /dev/sdb1`; `python3 -c "import os; os.system('mkfs.ext4 /dev/sdb1')"`; `echo "a; mkfs.ext4 /dev/sdb1" | sh`; `git commit -m "x; mkfs.ext4 /dev/sdb1` (unclosed quote). All sixteen were confirmed blocked by the current hook on 2026-10-13.
  - Each new allow case is mutation checked (`rules/lessons.md`): removing the blanking step turns it red. Each still blocked case is run with the blanking step forced on (AC-2 and AC-4 bypassed in a test switch) where it applies, so a hole in the blanking shows even when the raw fallback would hide it.
- **AC-6** (live copy): the live hook is updated by copying the repo file to `~/.claude/hooks/block-destructive.sh`, a step you do yourself outside any `wf run` (the live file is a guarded file, so a copy during a run stops it `guard_changed`). After the copy, a real session commit whose message names a deletion command passes.

## Decision

**Chosen option**: blank data regions in place with a small Python scanner inside the bash hook, raw scan for anything that runs code and on any failure; patterns and `--test` unchanged.

**Options considered**:
1. In place blanking of data regions (chosen). Pro: outside data regions the text is byte for byte the same, so every pattern keeps matching what it matches today; the raw fallback makes the worst case today's behavior. Con: commands that run a shell or interpreter keep their false alarms; a second language in the hook.
2. Rebuild the command from `shlex` tokens (first draft). Pro: fewer false alarms left. Con: the cross check found ten ways it let blocked commands through (redirects, newlines, continuations, substitutions, `$'...'`, the fork bomb in a payload, wrapper words).
3. Rewrite the hook in Python. Con: every pattern ported, a rule can slip in the move.
4. Bash only. Con: quote handling in bash is fragile exactly where it matters.

**Rationale**: a security hook may trade false alarms for safety, never the reverse. Changing only characters inside data regions, and only into a neutral `_`, cannot create a match that was not there and keeps quoted paths visible to the target patterns. Any command that runs code is left raw because inside it no quoted string can be trusted as data. You picked this redesign after the cross check.

## Build plan

1. The scanner with the fast path, the executor check and every raw fallback, wired before `check()`, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**
2. New `--test` cases, the forced blanking switch, a mutation check per allow case, satisfies **AC-5**
3. Live copy and a real commit check (you), satisfies **AC-6**

## Consequences

**Positive**: the common false alarms (commit messages, echo, sed, heredoc file writes) stop; every command blocked today stays blocked.

**Negative / tradeoffs**:
- A commit or edit made through `bash -c`, a Python heredoc or any other executor keeps today's false alarm.
- The hook needs `python3` for the blanking; without it, false alarms come back (never a missed block).
- More code in a security hook; the self checks, including the forced blanking cases, are the guard.
- `echo "rm -rf /"` passes now.

**Neutral**: `jq` stays the input parser; exit codes and messages are unchanged. `bash -c "rm -rf ~"` is not blocked today (the rm check does not accept a quote before `rm`) and stays that way; fixing that is a separate change.

## Follow-up

- [ ] `bash -c "rm -rf ~"` passes today because `rm_is_destructive` does not treat a quote as a left boundary; enroll a fix if wanted.
- [ ] The Bash shape hook may have the same quoted text problem; enroll it only if it bites.
