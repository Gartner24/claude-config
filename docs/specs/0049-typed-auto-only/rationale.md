# 0049 rationale

## Context

Spec 0030 kept `wf auto on` from Claude with deny patterns and a `WF_RUN` check; spec 0047 did the same for `wf auto release`. Patterns match text, so `wf  auto on`, `wf 'auto' on` or `python3 runner/wf.py auto   on` pass. The typed `/auto` never needed the command: the `UserPromptSubmit` hook calls `on()`, `off()` and `release()` in process, after `interactive()` checks it is a live interactive session with no Claude above it.

## Options considered

- **A, command refuses (chosen).** Gain: no spelling works; nothing to forge. Cost: the `! wf auto on` backup goes.
- **B, leave as is.** Gain: no build. Cost: an odd spelling still lets Claude turn a chat on or move a repo.
- **C, one use ticket written by the hook.** Gain: keeps a command path. Cost: Claude runs as the same user and can write the ticket, so more code for about B's safety.
- **D, allow only with no Claude in the process tree.** Gain: a terminal path. Cost: `systemd-run --user` or a double fork escapes the tree.

## Rationale

The only path you use is the hook, and the hook does not go through the command, so removing the command's on and release costs you only the `!` backup, which you never needed (you want only `wf`). A and C both close the spelling hole, but C's ticket is forgeable at the same user, so it adds code without adding safety. Deliberate scripts (D's escape, direct imports) are out of scope by your answer: closing them needs a separate account.
