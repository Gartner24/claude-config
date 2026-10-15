# 0049 verify

## Probe P1 (2026-10-15): is the typed prompt in the chat log when UserPromptSubmit runs?

Hook: `probes/prompt_in_log_hook.py`, given as a `--settings` UserPromptSubmit hook; it records whether the prompt is in `transcript_path` at hook time.

- `claude -p --model haiku --settings <probe settings> "probe0049 first message, reply ok"`: transcript file did not exist yet.
- Same with `--resume <session>`: 38 entries, `prompt_in_log: false` (only a `queue-operation` enqueue line held the text, -p mode).
- Interactive `claude --model haiku --settings <probe settings>` in tmux, third typed message after a reply: 37 entries, last three `atis-latch`, `system`, `system`, `prompt_in_log: false`.

Result: FAIL for the "check the chat log" design. The typed prompt is written after the hook. A hand made payload also names its own `transcript_path`, so it could point at any idle chat. Fallback taken as agreed: deny rules for `wf auto hook` (AC-1b).
