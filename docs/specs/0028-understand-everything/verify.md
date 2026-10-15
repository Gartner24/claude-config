# 0028 · verify

## P1 panel shape (2026-10-13)

Command: `python3 -I docs/specs/0028-understand-everything/probes/panel-shape.py` (read only, no claude call)

```
transcripts 4973 panels 478
input keys {'questions': 477, '__unparsedToolInput': 1}
option keys {'label': 2684, 'description': 2684, 'preview': 223, 'description2': 1}
options per question {2: 301, 3: 526, 4: 126}
options starting learn or explain 1
```

Result: confirmed. `tool_input.questions[].options[].label` and `description` are the fields AC-3 and AC-4 read; one panel had unparsed input, which AC-3 lets through.

## /check verify (2026-10-14)

### Commands
- [x] `diff` of `rules/plain-questions.md` against the text block in index.md, and `cmp` with `~/.claude/rules/plain-questions.md` → identical both → AC-1, AC-2 (can fail: the rule drifts from the spec, or the install never copied it)
- [x] pipe a 2 option panel with no learn option into `python3 hooks/plain-panel.py` → exit 2, `panel: question 1: no last option "Learn this first"; ...` → AC-3 (can fail: the hook lets a panel through with no learn option)
- [x] the same panel plus "Learn this first" → exit 0, no output → AC-3 (can fail: a good panel is refused)
- [x] 4 real options plus the learn option → exit 2, `4 real options, at most 3` → AC-3 (can fail: the count check is off by one)
- [x] two questions, only the second bad → line names `question 2` → AC-3 (can fail: wrong question number)
- [x] `{not json` and `{"tool_input":{"__unparsedToolInput":"x"}}` → exit 0 → AC-3 (can fail: the hook blocks a panel it cannot read)
- [x] a question holding `verify_failed`, `spec 0028`, `Park it` → `panel: question 1: plain words: park, spec 0028, verify_failed`, through the live runner copy's `plain.py` → AC-4 (can fail: the hook cannot import the runner copy, or jargon misses a code)
- [x] a real session (2026-10-14T18:10Z, started after the install) asked a 2 option panel → the tool result was an error holding the `panel:` line, so the live settings entry fires → AC-5 (can fail: the matcher or command path is wrong and the panel shows)
- [x] `python3 hooks/plain-panel.py --test` → `plain-panel: all checks passed` → AC-6, AC-17 (can fail: a crash in the check blocks the panel)
- [x] `run.unattended_prompt`, `run.read_decision`, `run.resume_prompt` driven directly → LEARN instruction present, `('Which engine?', ['Postgres', 'SQLite'], 'A database is a filing cabinet.')`, learn answer gives `LEARN_PROMPT` → AC-8, AC-9, AC-10 (can fail: the learn line is dropped when read)
- [x] `Run.ask_case` and `Topic.ping` for verify_failed, budget, crash_loop, denied → plain words question, `learn:` line right after the question → AC-11, AC-12 (can fail: the reason code is printed raw)
- [x] `report.render` on a record with built, stuck, question, setup and waiting items → `built:`, `stuck:`, `setup steps:`, `for you:`, plain reasons, `plain.jargon` over both renderings `[]` → AC-13 (the question prefix now follows spec 0033) (can fail: `parked:` or a reason code reaches the report)
- [x] `python3 -m unittest runner/tests/test_plain.py` → 8 tests OK, including the fake `wf run` learn flow and the corpus at 0 hits → AC-7, AC-10, AC-14, AC-15 (can fail: one jargon hit anywhere in the corpus)
- [x] `panels.py` on a fake `~/.claude` → one good panel: `panels: 1, failing: 0` exit 0; plus one bad: `failing: 1`, `s.jsonl:2: question 1`, exit 1 → AC-16 (can fail: the probe passes a bad panel or prints panel text)

### Live probe run, owed a decision
- `python3 docs/specs/0028-understand-everything/probes/panels.py` on the real transcripts → `panels: 5, failing: 5`, exit 1. Four come from a session that started 2026-10-13, before the hook was installed (hooks load at session start), and one is the panel the hook refused on purpose at 18:10Z. As specced, the probe counts a refused panel as failing and dates panels by the hook file's time, not the session's start, so it goes red every time the hook does its job. Changing that is spec text: `/architect understand everything`.

## P2 learn line (real claude)
Not run yet: `wf` runs it as a live step after build step 5.

## P3 hook refuses a panel (interactive)
Not run yet: a waits on you box after the install.

## Live runs (wf finish)

- 2026-10-14, Claude Code 2.1.300: `python3 docs/specs/0028-understand-everything/probes/learn-line.py` PASS
- 2026-10-14, P3 done by Claude in a real interactive session (Claude Code 2.1.296): an AskUserQuestion panel with no "Learn this first" option was refused by the PreToolUse hook before display: `panel: question 1: no last option "Learn this first"`. PASS.
- 2026-10-14, Claude Code 2.1.299: `python3 docs/specs/0028-understand-everything/probes/learn-line.py` PASS (options: 3, learn: 285 characters, jargon: none)
