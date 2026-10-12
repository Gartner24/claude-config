# Verify: failure and park policy · spec 0008 · updated 2026-10-12

## Probes before accept (spec gate)

- [x] Check 1, denial shape: `rg -o '"permission_denials":\[\{.{0,400}' ~/.local/state/wf/runs`. Result: entries hold `tool_name`, `tool_use_id`, `tool_input`; no reason field. Confirmed on claude 2.1.296 run records. -> AC-5
- [x] Check 2, denial reason: `rg -l <tool_use_id> ~/.claude/projects` found the session transcript; its line for that id holds `toolUseResult: "Error: PreToolUse:Bash hook error: SHAPE: ..."`. Confirmed. -> AC-5
- [ ] Check 3, usage limit in `claude -p` JSON: UNCONFIRMED. Run this the next time a session or weekly limit is hit, then paste the output here:
  `env -C "$(mktemp -d)" claude -p "say ok" --output-format json`
  Pass: the output is a failed result (`is_error` true or a non success subtype, or a nonzero exit) and its `result`, subtype or stderr matches the AC-8 limit pattern, and the reset part matches the reset pattern. Anything else: back to `/architect`. -> AC-8, AC-11

## Manual checks after the build (real claude)

- [ ] Check 4: a scratch repo whose `/develop` box asks for `sudo pacman -S <pkg>` parks `blocked` with the package in the detail. -> AC-4
- [ ] Check 5: a scratch feature with a deliberately failing behavior: the real `/check verify` call ends with a `VERIFY FAIL:` line and `wf` runs `/debug`. -> AC-2
- [ ] Check 6: inside a call, `env | grep -c -E '_API_KEY|SECRET'` prints 0 and reading `~/.aws` fails. -> AC-7
