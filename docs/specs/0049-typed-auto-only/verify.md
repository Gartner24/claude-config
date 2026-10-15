# 0049 verify

## Probe P1 (2026-10-15): is the typed prompt in the chat log when UserPromptSubmit runs?

Hook: `probes/prompt_in_log_hook.py`, given as a `--settings` UserPromptSubmit hook; it records whether the prompt is in `transcript_path` at hook time.

- `claude -p --model haiku --settings <probe settings> "probe0049 first message, reply ok"`: transcript file did not exist yet.
- Same with `--resume <session>`: 38 entries, `prompt_in_log: false` (only a `queue-operation` enqueue line held the text, -p mode).
- Interactive `claude --model haiku --settings <probe settings>` in tmux, third typed message after a reply: 37 entries, last three `atis-latch`, `system`, `system`, `prompt_in_log: false`.

Result: FAIL for the "check the chat log" design. The typed prompt is written after the hook. A hand made payload also names its own `transcript_path`, so it could point at any idle chat. Fallback taken as agreed: deny rules for `wf auto hook` (AC-1b).

## /check verify (2026-10-15): PASS, 30 of 30

Run: `python3 -B docs/specs/0049-typed-auto-only/probes/verify_check.py` (real `python3 runner/wf.py auto ...` subprocesses with `XDG_STATE_HOME` in a temp folder; the hook steps call `cmd_auto(["hook"])` in process with `interactive()` patched true). Then `python3 runner/tests/fast.py`: 880 tests, 0 failed.

## Commands
- [x] `wf auto on`, `on x`, `on a b`, `release x`, bare `release` -> exit 5, the AC-1 line, no state folder created -> AC-1. can fail: `cmd_auto` routes `on` to `on()` again (mutant 1 and 2: exit 0 or a name refusal, state written)
- [x] same under `WF_RUN=1` -> exit 5, the AC-1 line, not the bare `refused: user_only` -> AC-1. can fail: the refusal sits below the WF_RUN check (mutant: `refused: user_only`)
- [x] odd spellings through `bash -c`: `auto  on`, `auto 'on' x`, `"auto" "release" x` -> exit 5, AC-1 line -> AC-1. can fail: same mutant (went red)
- [x] an existing `auto.json`: `wf auto on` from a new folder and `wf auto release <repo>` leave it byte for byte the same -> AC-1. can fail: `on` reaches the switch (mutant 2: bytes changed)
- [x] `cmd_auto(["on"])`, `cmd_auto(["release","x"])` with `run.state_dir` raising -> both 5 -> AC-1. can fail: the refusal comes after a state read (mutant: raised)
- [x] `wf auto bogus` -> exit 2, `usage: wf auto off [now] | status | start | wait | take <repos> | hook | bar` -> AC-1. can fail: USAGE still lists on or release
- [x] `wf --help`, `wf auto --help` hold neither `on [repos]` nor `release <repos>` -> AC-1. can fail: the argparse help left untrimmed
- [x] typed `/auto on`, bare `/auto release`, `/auto release nosuchrepo`, `/auto off` through the hook -> chat on, `usage: /auto release <names>`, `release()` name refusal, chat gone -> AC-2. can fail: the hook routed through `cmd_auto` (would now refuse)
- [x] `on()` and `release()` under `WF_RUN` -> 5 and 5, `refused: user_only` -> AC-2. can fail: the WF_RUN guard dropped from the functions
- [x] `wf auto status` then `wf auto off` from the chat folder -> status shows on, off exits 0 and empties `chats` -> AC-3. can fail: the refusal catching `off` too
- [x] deny rules in `live/settings.json` match `wf auto hook`, `echo x | wf auto hook`, `python3 runner/wf.py auto hook`, `wf auto on`, `wf auto release x`, and not `wf auto off`, `status`, `take x` -> AC-1b, AC-3. can fail: a hook rule missing, or a pattern so broad it denies `off`
- [x] `grep -rnE "! wf auto (on|release)" live runner AGENTS.md docs/architecture.md` -> no hits -> AC-4. can fail: the old SKILL.md fallback line kept
- [x] `runner/tests/test_auto.py`, `test_auto_chats.py` -> 40 OK; `on`/`rel` helpers, refusal and subprocess tests present -> AC-5 (mutation checks per test are the Test box)

Read, not run: the SKILL.md strings, `release()` docstring and `auto.py` top comment match AC-4 (seen in the diff); not counted as checks.

Left to the box: Install it live after the merge, from main (the plan branch does not hold this feature's code). That is where a real typed `/auto on` in an interactive Claude session goes through the real `interactive()` process walk; this sandbox cannot run one.
