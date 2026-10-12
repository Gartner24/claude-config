# Verify: decision parking and phone pings · spec 0005 · updated 2026-10-11
_Steps derived from spec 0005 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Manual (AC-14, real claude and ntfy.sh)
- [x] Check 1: a real step asked to choose a storage engine with AskUserQuestion -> FAILED, see Findings -> AC-14.1, AC-6
- [ ] Check 2: a real step ends with `DECISION NEEDED:` and `OPTION:` lines; the phone reply resumes the same session -> AC-14.2, AC-4, AC-10
- [x] Check 3: a real `Doc type` panel decided by the model with the (recommended) option, no ping -> AC-14.3, AC-5
- [x] Check 4: dropped 2026-10-11, no `--settings` is passed any more -> AC-14.4 · skipped
- [ ] Check 5: on the phone, buttons, a coded free text reply, a reused code and `<id> maybe` -> AC-14.5, AC-7, AC-8
- [x] Check 6: a subagent's decision reaches the main agent's final message -> AC-14.6

## Commands
- [ ] `python3 -m unittest discover -s runner/tests` -> all pass (fake claude, fake ntfy) -> AC-1 to AC-13
- [ ] `wf ntfy init`, subscribe the phone, `wf ntfy test`, tap `1 yes` -> `accepted: yes` -> AC-1

## Value sourcing (one step per row that milestone 6 changed)
- [ ] Question: a result with two `DECISION NEEDED:` lines and a bare one after them -> the last non empty one is the question (`TestReadDecision`) -> AC-4
- [ ] Options: bold, bullet and indented `OPTION:` lines, a blank line before the first, 11 options -> labels without `*`, cut to 9 (`TestReadDecision`) -> AC-4
- [ ] Safe panel answer: `run.UNATTENDED_PROMPT` names `Doc type`, `Save to verify.md`, `Not now, later` exactly as the skills spell them (`test_argv`, plus manual check 3) -> AC-3, AC-5
- [ ] Resume prompt: a tapped `2` resumes with `The user answered your DECISION NEEDED question: SQLite`; a coded reply resumes with its text (`test_happy_path`, `test_panel_free_text`) -> AC-10, AC-11
- [ ] Session id: an asking call with no `session_id` stops `call_error` with no POST (`test_no_session`) -> AC-10
- [ ] Label scrub: an option `/tmp/x` pings as `option 1`, never a blank button (`test_empty_label`) -> AC-7
- [ ] Deny list: `AskUserQuestion` is first in `--disallowedTools`, no `--settings`, no `WF_RUN_DIR` (`test_argv`) -> AC-3

## Findings

### Check 1, 2026-10-11, Claude Code 2.1.296
`claude -p` in a scratch folder, with the spec 0005 `--settings` hook and `WF_RUN_DIR` set, prompted to ask Postgres or SQLite with AskUserQuestion:

| Flags | Result |
|---|---|
| `--permission-mode auto` | exit 0, `subtype` `success`, `stop_reason` `end_turn`, no `deferred_tool_use`; result: "AskUserQuestion isn't in this session's tools, either loaded or deferred, and the session is non-interactive" |
| `--tools AskUserQuestion` | exit 0, `success`, `end_turn`; result `NO_TOOL` |
| `--tools default,AskUserQuestion --allowedTools AskUserQuestion` | `error_max_budget_usd` at 1 USD before the first turn (180k token context) |

AskUserQuestion is not offered to the model in `-p` mode, so the hook never runs and no call ends `tool_deferred`. AC-3, AC-4, AC-5, AC-6 and AC-10 hold against the fakes but have no effect against this CLI. The prose path (AC-11: a `DECISION NEEDED:` line, ping, wait, `--resume` with the answer sentence) does not depend on the tool. Spec 0005 needs `/architect` to decide the panel path before checks 2, 3 and 6 can run.

Decided 2026-10-11 by `/architect`: the text path with `OPTION:` lines (spec 0005 Option 5, build plan milestone 6). Checks 2, 3 and 6 above are rewritten for it.

### Checks 3 and 6, 2026-10-12, Claude Code 2.1.296
Both ran with wf's exact argv (`run.DENIED`, `run.UNATTENDED_PROMPT`, `--max-budget-usd 3`) in a scratch git repo, `main` plus a feature branch one commit ahead.

| Check | Prompt | Result |
|---|---|---|
| 3 | `/document` | exit 0, `success`, 0.46 USD; it picked `PR description` (the inferred, recommended type) itself and wrote the PR body; no `DECISION NEEDED:` line, so no ping |
| 6 | spawn one subagent to choose Postgres or SQLite, told the owner decides | exit 0, `success`, 0.51 USD; the main agent's final message ended `DECISION NEEDED: Which storage engine should the history feature in calc.py use?` plus two `OPTION:` lines; `read_decision` returned a two option panel |

Check 6 also shows the first half of check 2: a real step ends its message in the AC-4 shape. The phone half of check 2 (reply, resume, same `session_id`) and check 5 still wait for the phone. No prompt change was needed for subagents.
