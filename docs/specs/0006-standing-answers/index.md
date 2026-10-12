# 0006. Standing answers for unattended runs

**Date**: 2026-10-12
**Status**: Proposed
**Amended**: 2026-10-12, architecture pass ([architecture](../../architecture.md)): the `cross check` key is dropped before the build. Its only user would be `/architect` running unattended, which the runner never does.

## Summary

Some questions get the same answer from you every time: whether `/test` runs the suite, and whether a passing feature is marked done. Each repo can now keep those answers in a short `## Standing answers` section of its `AGENTS.md`. `wf run` reads that section once at start, shows it on the confirm line, and adds it to the unattended prompt, so those panels stop pinging your phone. Interactive sessions are untouched, `/architect` stays out of `wf run`, and accepting a spec is never a standing answer.

## What you're agreeing to

- You write up to two answers per repo by hand: run suite and done. Anything missing still pings you.
- `wf run` refuses to start if the section has a mistake, and shows the answers it will use before you press Enter.
- `done: yes` counts only when `wf` itself sees no other open box in the feature. Otherwise you still get the done question.
- Interactive sessions, `/architect`, and accepting specs stay exactly as they are today.
- The model applies the answers from the prompt. A miss shows up as a ping, never as a wrong answer.

## Requirements

**User stories**:
- As you, I want `wf run` to answer the run suite and done questions the way I always do, so that a Beta feature closes overnight without a ping.
- As you, I want a typo in the section to stop the run before it starts, so that a wrong answer can never be applied silently.
- As you, I want to see the answers a run will use before I press Enter, so that I know what it decides for me.

**Acceptance criteria**:
- **AC-1**: The section lives in the file mapped from the exact `Candidate.scope_dir` value: `docs/scope` reads `<repo>/AGENTS.md`, `.workflow/scope` reads `<repo>/.workflow/AGENTS.md`. The section starts at a line that, case folded and stripped, starts with `## standing answers`; a heading with any text after those words (for example `## Standing answers (x)`) is a refusal (AC-3), not a miss. It ends at the next line starting with `# ` or `## `. Code fences are not tracked (a known limit: a `#` line inside a fence ends the section). A missing file or a file with no such heading means no answers, which is not an error.
- **AC-2**: Inside the section, a line whose first non space character is `-` or `*` is an entry and must match `^\s*[-*]\s+([^:]+?)\s*:\s*(\S+)\s*$`. Key and value are case folded and runs of spaces in the key collapse to one. Every other line (prose, blank) is ignored, so a note in the section must not be a bullet (a bullet note such as `- Note: slow suite` is an unknown key and refuses). The map is kept in the table order below, not file order. The keys and values are exactly:
  | Key | Values |
  |---|---|
  | `run suite` | `yes`, `ask` |
  | `done` | `yes`, `ask` |
- **AC-3**: `wf run` refuses with reason `bad_answers` (exit 5, the existing `refuse()` path) when an entry does not match the AC-2 form, names an unknown key, carries a value not allowed for its key, repeats a key, when the heading appears twice in the file, when the heading has extra text (AC-1), or when the file exists but cannot be read (`OSError` or not UTF-8). The file is checked top to bottom and the first problem wins. The detail is `<path relative to repo>:<line number>: <reason>`, where a repeated key or heading reports the line of its second occurrence, and an unreadable file reports `<path relative to repo>: <reason>` with no line; then ` (expected: - run suite: yes|ask, - done: yes|ask)`. A `cross check` entry is an unknown key like any other. The check runs in `start_checks()` right after the Autopilot check, so a refusal takes no lock, makes no call and creates no run folder.
- **AC-4**: The section is read and checked once, in `start_checks()`. `Run.__init__` sets `answers` to `{}` and `record["answers"]` to `{}` so a `Run` built without `start_checks()` (as some tests do) behaves as no answers; `start_checks()` overwrites both. The answers are frozen on the `Run` for its whole life: an edit to the file during the run (yours, or a call's, such as `/sync`) changes nothing for the later calls or resumes of that run.
- **AC-5**: Every call and resume passes `--append-system-prompt` with `UNATTENDED_PROMPT` (spec 0005 AC-3 text, unchanged) followed, only when at least one sentence below applies, by ` Standing answers for this repo, use them instead of asking:` and then, in this order:
  - `run suite` `yes`: ` Run tests?, Yes, run and fix to green.`
  - `done` `yes`, only on a last box call (AC-6): ` When /test or /check verify offers to mark the feature done after its last open box passed: Yes, mark it done.`
  With no section, no entries, only `ask` values, or only `done: yes` on a call that is not a last box call, the prompt equals `UNATTENDED_PROMPT` exactly. A key that is `ask`, missing, or (for done) not applicable to this call adds nothing, so its question goes through the spec 0005 `DECISION NEEDED:` path as today.
- **AC-6**: `wf` decides the last box itself, never the model. Right before each call, `wf` rereads the scope (`load_scope`, as `reread()` does) and the call is a last box call when its box is open and the feature has no other open box outside that box and the boxes under it (`wf.under`). A resume uses the value of the call it resumes. The final `/sync` call is never a last box call. So on a Beta feature, `done: yes` applies on the `Test it` call but not on the `Verify it` call while `Test it` is still open; a done offer there pings you.
- **AC-7**: The confirm line gets one more part after the caps part: `answers: ` followed by the present keys in AC-2 table order as `<key> <value>`, joined by `, ` (for example `answers: run suite yes, done yes`), or `answers: none` when no key is present. `run.json` gets `answers`, an object of the present keys with their case folded values (`{}` when none), set before the first call. Each call record gets `last_box` (true or false, AC-6).
- **AC-8**: `wf run` still refuses `/architect` and `/scope` boxes (spec 0004 AC-2 unchanged), with or without a standing answers section. No standing answer touches a design or spec panel.
- **AC-9**: Manual checks on the real `claude`. Every scratch repo has `**Autopilot:** allowed`, a work branch, a spec with ACs for the feature, `test-preferences.json` naming a `tool` that is installed, and uncommitted source files for `/test` to cover:
  1. A Beta feature whose only open box is `Test it`, with `run suite: yes` and `done: yes`: `wf run` ends `feature_done` with an empty `decisions` list in `run.json`, and the feature heading reads `· done`.
  2. A Beta feature whose open boxes are `Verify it` then `Test it`, with `done: yes`: the `Verify it` call has `last_box` false and the feature is still `in-progress` after it (a done offer there arrives as a ping, not a yes).

## Decision

**Chosen option**: Option 1: a per repo section read by `wf run` and added to the unattended prompt.

`wf run` reads `## Standing answers` from the scope base's `AGENTS.md` once at start, refuses a section it cannot read, and turns each answer that is not `ask` into a fixed answer sentence after spec 0005's prompt. Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch**:
- `answers`: an ordered map, key in `run suite`, `done`, value from AC-2. Held on the `Run`, written to `run.json` as `answers`. No other storage.

**API surface** (CLI only):
| Surface | Inputs | Output | Errors |
|---|---|---|---|
| `wf run <repo>` start | scope base, `AGENTS.md` section | `answers: ...` part on the confirm line, `answers` in `run.json` | `refused: bad_answers: <file>:<line>: <reason> (expected: ...)`, exit 5 |
| each `claude -p` call and resume | frozen answers, last box flag | `--append-system-prompt` value from AC-5, `last_box` in the call record | none new |

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| start | which `AGENTS.md` | exact `Candidate.scope_dir` value (`docs/scope` or `.workflow/scope`), AC-1 |
| each call | last box flag | the scope reread right before the call, `wf.load_scope` plus `wf.under`, AC-6 |
| start | each answer | the `## Standing answers` bullets, AC-2 |
| prompt | `Run tests?` header and `Yes, run and fix to green` label | `skills/test/SKILL.md` step 7.5 |
| prompt | done offer description (no label exists; the offers are plain sentences, "Tests are in and passing, mark it `done`?" and "Verified and passing, mark it `done`...") | `skills/test/SKILL.md` (After writing the suite) and `skills/check/modes/verify.md` |
| prompt | base text | `UNATTENDED_PROMPT` in `runner/run.py`, spec 0005 AC-3 |
| confirm line, `run.json` | answers shown | the frozen map from AC-4 |

**Key invariants**:
- An unreadable or wrong section never starts a run; a missing one always does, with every panel pinging as before.
- The answers a run uses are the ones shown on its confirm line, for its whole life.
- Accepting a spec has no key and no prompt sentence, ever.
- With no answers, argv is byte for byte what spec 0005 passes today.
- The done answer reaches the model only on a call `wf` itself computed as the feature's last open box.

**Security model**: The section is repo content, trusted only because you set `**Autopilot:** allowed` yourself (spec 0004); refusing a cloned scope that ships it set is feature 8. Every value only picks an option the skill already offers, `done: yes` cannot push or merge (the deny list and prompt are unchanged), and in team repos the answers sit in the gitignored `.workflow/AGENTS.md`, never in a team owned file.

**Configuration required**: none (no env var, no new file beyond the optional section).

**Critical test scenarios**:
- Parse: a section with both keys, mixed case and extra spaces, prose lines and blank lines between bullets, yields the map, verifies **AC-1**, **AC-2**
- Base: a `.workflow/scope` repo reads `.workflow/AGENTS.md` and ignores a root `AGENTS.md` section; a `docs/scope` repo the reverse, verifies **AC-1**
- Refusals: one fixture each for a bad form, unknown key (`cross check` included), bad value, bullet note, repeated key, heading twice, heading with extra text, non UTF-8 file; each prints the AC-3 detail with the right line (second occurrence for repeats, none for the unreadable file), exits 5, makes no call and no run folder; with two problems the earlier line wins, verifies **AC-1**, **AC-2**, **AC-3**
- Defaults: a `Run` built without `start_checks()` passes `UNATTENDED_PROMPT` and records `answers` `{}`, verifies **AC-4**
- Freeze: the fake claude rewrites the section during call 1 (new `write_file` step key); call 2's argv carries the start prompt, verifies **AC-4**
- Prompt: argv on a last box call with both answers equals `UNATTENDED_PROMPT` plus the AC-5 sentences in order; for no section and for all `ask` it equals `UNATTENDED_PROMPT`, verifies **AC-5**
- Last box: a feature with `Verify it` and `Test it` open and `done: yes`: the `Verify it` call's prompt has no done sentence and `last_box` false, the `Test it` call's has it and `last_box` true, its resume keeps it, `/sync` never has it; an open milestone under the box does not count as another open box, verifies **AC-5**, **AC-6**
- Visibility: the confirm line shows `answers: none` and the full form; `run.json` `answers` and per call `last_box` match, verifies **AC-7**
- `/architect` box still refused `manual_box` with a full section, verifies **AC-8**
- Manual checks 1 and 2, verifies **AC-9**

## Build plan

Skateboard: each step leaves `wf run` working; step 1 already blocks a bad section, step 2 is the feature.

1. `read_answers(c)` in `runner/run.py`: file from the exact `c.scope_dir`, section bounds, entry form, keys, values, refusal reasons in file order; `Run.__init__` defaults; called from `start_checks()` after the Autopilot check, result kept on the `Run` in table order; parse, base, default and refusal tests in `runner/tests/test_run.py`, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**
2. `unattended_prompt(answers, last_box)` builds the AC-5 text; the last box check before each call (resumes reuse it, `/sync` false); `call()` passes the built prompt instead of the constant; a `write_file` step key in the fake claude; argv, last box and freeze tests, and the existing argv test keeps comparing against `UNATTENDED_PROMPT` for a repo with no section, satisfies **AC-4**, **AC-5**, **AC-6**, **AC-8**
3. Confirm line part, `run.json` `answers`, per call `last_box`; tests, satisfies **AC-7**
4. Manual checks 1 and 2 on the real `claude`, saved to this spec's `verify.md`, satisfies **AC-9**

## Consequences

**Positive**:
- A Beta feature with both answers set can run `/test` and close without a ping, which is the Release 2 goal for the done decision.
- No change to any vendored skill, no always loaded rule, and no behavior change for a repo without the section.

**Negative / tradeoffs**:
- The skills still decide the panels themselves from the prompt; nothing in `wf` checks that a standing answer was applied (same limit as spec 0005's fixed answers). A miss turns into an ordinary ping.
- The prompt labels are copied from vendored skills; a vendor pull that renames a panel or option silently weakens the match (a ping, never a wrong answer).
- `done: yes` only works on the call `wf` marks as the last box; a model that marks done on another call anyway is not stopped by `wf` (the prompt carries no done answer there, so it should ask).
- A call (for example `/sync`) can break the section partway through a run. The frozen answers protect that run, but the next `wf run` refuses until you fix it.
- Code fences inside the section are not understood (AC-1).

**Neutral**:
- Spec 0005 AC-3's prompt is now the base of a per run prompt; its text is unchanged.
- Interactive sessions keep asking every panel, by your choice.

## Follow-up

- [ ] Root `AGENTS.md`: document the `## Standing answers` section (location, keys, values); `/sync` owns this.
- [ ] Feature 8 (failure and park policy) covers a cloned scope that ships `**Autopilot:** allowed` together with standing answers.
## Rationale

Reasoning and options: see [rationale.md](rationale.md).
