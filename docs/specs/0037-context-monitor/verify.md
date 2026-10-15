# 0037 verify

## Probes

- **P3** license, 2026-10-14: `npm view get-shit-done-cc license repository.url` printed
  `license = 'MIT'` and `repository.url = 'git+https://github.com/gsd-build/get-shit-done.git'`.
  Confirmed. `NOTICE.md` names it.
- **P1** transcript usage, 2026-10-14, partial: inside a `wf run` call (`claude -p`), its own
  transcript under `~/.claude/projects/<cwd slug>/<session>.jsonl` read with
  `jq -c 'select(.type=="assistant") | {sc: .isSidechain, u: .message.usage}'` shows
  `isSidechain: false` and all three of `input_tokens`, `cache_creation_input_tokens`,
  `cache_read_input_tokens` on every assistant line (for example 2 + 212 + 93373). The hook
  input half (`transcript_path` in the PostToolUse input) needs a real `claude -p` with a
  temp settings file, which a sandboxed `wf` call cannot start: unconfirmed, owed to you.
- **P2** `additionalContext` reaches the model: needs a real `claude -p`; unconfirmed, owed to
  you. Commands are in the spec's Probes section.
