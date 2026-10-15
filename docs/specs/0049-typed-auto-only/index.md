# 0049 · Only a typed /auto turns on or releases

**Date**: 2026-10-15
**Status**: Proposed
**Paths:** `runner/auto.py`, `runner/wf.py`, `claude-home/settings.json`, `claude-home/skills/auto/SKILL.md`, `runner/tests/test_auto.py`, `runner/tests/test_auto_chats.py`, `AGENTS.md`
**Amends**: [0030](../0030-autonomous-mode/index.md) (AC-3), [0047](../0047-review-leftovers/index.md) (AC-1, AC-2, AC-6)

## What you're agreeing to
- Your typed `/auto on`, `/auto off` and `/auto release <names>` work exactly as today.
- The command `wf auto on` and `wf auto release` always refuse, in any spelling, so Claude can never turn a chat on or release a repo.
- `! wf auto on` typed in a chat stops working as a backup; if the hook ever misses, you type `/auto on` again.
- The hook command `wf auto hook` can be started by hand with a fake "/auto on" message; it gets the same text block as `on` and `release` had, so an odd spelling of that one command can still get through.
- A script written on purpose to call the switch code directly is out of reach of this change (Claude runs as your user).

## Summary

The review of spec 0047 ([report](../../reviews/review-2026-10-15-0047.md), Leftovers, P1) found that `wf auto on` and `wf auto release` are kept from Claude only by text patterns in settings, so an odd spelling (two spaces, quotes, `python3 runner/wf.py`) slips past. Your typed `/auto` never used the command: the prompt hook calls the switch code directly. So the command now refuses both verbs outright, and the hook stays the only way in. Your answers of 2026-10-15: case A (command refuses), reach is every command spelling. Source: plan row 53.

## Requirements

**Acceptance criteria**:
- **AC-1** (command refuses, amends 0030 AC-3 and 0047 AC-2): `cmd_auto` answers a first word of exactly `on` or `release` (any arguments after it; matching is on the parsed words, so spacing and quoting do not matter) by printing `refused: user_only: type /auto on in the chat` (for release: `refused: user_only: type /auto release <names> in the chat`) and returning 5, before any `run.state_dir()` call. It changes nothing in `auto.json` and starts nothing. This line wins under `WF_RUN` too. Any other first word keeps today's handling (unknown words give usage, exit 2). `USAGE` becomes exactly `usage: wf auto off [now] | status | start | wait | take <repos> | hook | bar`, and the `wf auto` argparse help in `runner/wf.py` drops `on [repos]` and `release <repos>` the same way. `auto.py`'s top comment says `/auto on` (typed) writes the chat, not the command.
- **AC-1b** (hook command blocked, cross check S1): `wf auto hook` read from a hand made stdin passes `interactive()`, since a Bash tool call has the same process chain as the real hook. Probe P1 (verify.md) showed the typed prompt is not yet in the chat log when the hook runs, so the log cannot tell them apart. `live/settings.json` `permissions.deny` gains `Bash(*wf auto hook*)`, `Bash(*wf.py auto hook*)` and `Bash(wf auto hook:*)`. Claude Code runs hooks outside the Bash tool, so the real hook is unaffected. This one command stays text matched only, as the security model says.
- **AC-2** (typed /auto unchanged): the hook's typed switch (`typed_switch` plus `interactive()`) still calls `on(folder, names)`, `off(now, folder)` and `release(names, folder)` directly, with the same output lines as today, including the bare `/auto release` usage line. The functions `on` and `release` keep their `WF_RUN` refusal.
- **AC-3** (the rest unchanged): `wf auto off`, `off now`, `status`, `start`, `wait`, `take`, `hook` and `bar` behave as today. The deny rules for `on` and `release` in `live/settings.json` stay as a second layer.
- **AC-4** (texts): `live/skills/auto/SKILL.md` keeps verbatim the three strings `test_auto.py` pins (the `argument-hint` line, the description's "only the user releases a repo from a chat (`/auto release" and "Claude can never run `wf auto on` or `wf auto release`"), and adds after the last one: "the command refuses them, and deny rules block them and `wf auto hook`". Its fallback line reads: if there is no such line, say the hook did not switch it and ask the user to type the same `/auto` command again in this chat. No text offers `! wf auto on` or `! wf auto release`. The `release()` docstring says "the command refuses it (spec 0049)". The DRIVE text stays unchanged. `AGENTS.md` (the `wf auto` line) and `docs/architecture.md` say `on` and `release` come only from your typed `/auto`; `/sync` may make that edit.
- **AC-5** (tests, amends 0047 AC-6): one test helper (for example `on(*words)` and `rel(*words)` on the test case) calls `auto.on(folder, words)` or `auto.release(words, folder)` under `redirect_stdout` and returns the same `(code, out)` tuple `cli` did; every setup and assertion that used `cli("on", ...)` or `cli("release", ...)` in `test_auto.py` and `test_auto_chats.py` uses it, including the two `WF_RUN` refusal tests and the bad name refusal test (so `on()` and `release()` keep their own `WF_RUN` and name checks under test). `release` leaves the usage, exit 2 loop in `test_auto.py`. New tests: `cli("on")`, `cli("on", "x")`, `cli("release", "x")`, and under `WF_RUN`, each exit 5 with the AC-1 line; a subprocess run of `python3 <runner>/wf.py auto on` with `XDG_STATE_HOME` set to a temp folder exits 5 and leaves `auto.json` byte for byte unchanged (missing stays missing); the deny rules match `wf auto hook` and `echo x | wf auto hook`; the typed `/auto on`, `/auto off`, `/auto release x` through the hook still switch. 0047's test that `wf auto release x` run directly still releases is inverted to expect the refusal. Each new or changed test is mutation checked.

## Decision

Close the door instead of guarding it: the command refuses `on` and `release` itself, so no spelling reaches the switch, and the typed `/auto` (already the only way you use) is untouched.

## Feature design

**Value sourcing**:
| Value | Source |
|---|---|
| refusal line and exit 5 | fixed text in AC-1; 5 is the existing `user_only` code |
| the verb refused | the parsed `wf auto` words, `words[0]` |
| who may switch | only the hook path: `UserPromptSubmit` prompt plus `interactive()` (unchanged, spec 0030) |

**Security model**: threat is a model slipping (running the command by mistake or a prompt injection telling it to), not a deliberate script. `wf auto on` and `release` are closed in code; `wf auto hook` with a hand made message is closed by text match only (AC-1b), so an odd spelling of it still gets through. Out of scope, named on purpose: a Python script that imports `auto` and calls `on()`, and a raw write to `auto.json` from Bash (the Edit deny rule covers only the edit tools). Both need a separate user account to close, which you declined. A `claude -p` session can never switch (unchanged, `interactive()`).

**Critical test scenarios**:
- Happy path: typed `/auto on` in an interactive session turns the chat on, verifies **AC-2**
- Refusal: `python3 runner/wf.py auto on` exits 5, `auto.json` unchanged, verifies **AC-1**
- Off stays open: `wf auto off` from the command still turns the chat off, verifies **AC-3**

## Build plan

1. `runner/auto.py` and `runner/wf.py`: refuse `on` and `release` in `cmd_auto`, trim `USAGE` and the argparse help, fix the top comment and the `release()` docstring, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**
2. `live/settings.json` deny rules for `wf auto hook`; `live/skills/auto/SKILL.md` the "can never run" reason and the retype fallback, satisfies **AC-1b**, **AC-4**
3. Tests in `runner/tests/test_auto.py` and `runner/tests/test_auto_chats.py`: move setup to direct calls, add the refusal and typed path tests, invert the 0047 release test, mutation check each, satisfies **AC-5**
4. Install live (`./install.sh`) so `~/.claude/skills/auto/SKILL.md` and the runner copy match, satisfies **AC-1**, **AC-4**

## Consequences

**Positive**: the review's P1 closes by construction; the deny pattern list no longer carries the safety.
**Negative**: no `! wf auto on` backup; a hook that misses means typing `/auto` again.
**Neutral**: deliberate scripts stay possible, as named in the security model.

## Rationale

See [rationale.md](rationale.md).
