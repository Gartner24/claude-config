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

## P2 learn line (real claude)
Not run yet: `wf` runs it as a live step after build step 5.

## P3 hook refuses a panel (interactive)
Not run yet: a waits on you box after the install.

- 2026-10-14, P3 done by Claude in a real interactive session (Claude Code 2.1.296): an AskUserQuestion panel with no "Learn this first" option was refused by the PreToolUse hook before display: `panel: question 1: no last option "Learn this first"`. PASS.
