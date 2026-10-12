# 0006. Standing answers: rationale

## Context

A headless `wf run` asks you everything the skills ask, through phone pings (spec 0005). Most of those questions get the same answer every time: in the sessions behind the research note, 25 of 30 design answers were the recommended pick. Three panels on the build path are pure repeats per repo: the `/architect` cross check, `/test`'s "Run tests?" (asked every run, never saved), and the done offer after the last box (`/check verify` at Alpha, `/test` at Beta). Until they stop pinging, a Beta feature cannot close without you.

Forces:
- The workflow skills are vendored and overwritten on pull, so they cannot be taught a new file format; whatever reads the answers has to live in `wf` or in the prompt.
- `claude -p` has no AskUserQuestion (spec 0005), so answers reach the skill only as prompt text, and nothing can check the model applied them.
- In bot reviewed team repos `AGENTS.md` is team owned and committed; your personal answers must not land there.
- The tier already lives on the scope header and the `/test` framework in `test-preferences.json`; a second copy could disagree with either.
- You keep design decisions and spec acceptance at the keyboard; `/architect` stays out of `wf run`.

## Options considered

### Option 1: Per repo section read by `wf run`, added to the unattended prompt

`wf` parses `## Standing answers` from the scope base's `AGENTS.md` at start, validates it, and appends one fixed answer sentence per answer.

**Pros**:
- Only headless runs change; interactive skills keep their "always ask" design.
- `wf` validates the section and shows it before the run, so a typo is caught up front.
- No vendored file touched, no context cost in other sessions.

**Cons**:
- The model still applies the answers; `wf` cannot verify it.
- Interactive sessions keep asking the same questions.

### Option 2: Always loaded rule file telling skills to read the section

A rule under `~/.claude/rules/` (the spec 0003 pattern) tells every session to take these answers from `AGENTS.md` instead of asking.

**Pros**:
- Also removes the repeats at the keyboard.
- One mechanism for headless and interactive.

**Cons**:
- Overrides the cross check skill's deliberate "never skip on the engineer's behalf" rule in every session.
- Loads in every session; no validation step before it takes effect, so a typo is applied or ignored silently.

### Option 3: More global fixed answers in the prompt

Extend spec 0005's fixed answers (Doc type and the others) with run suite yes and done yes for every repo.

**Pros**:
- Smallest change: one string.

**Cons**:
- No per repo say: a repo with a slow or service bound suite, or one where you want to close features yourself, cannot opt out.
- Cross check has no single right answer across repos.

## Rationale

Option 1 fits the forces: the vendored skills cannot read a new format, so the prompt is the only channel either way, and `wf` is the one place that can validate the answers and show them before a run. Keeping it headless respects the skills' interactive design, which you chose to keep. Option 3 is simpler but takes away the per repo choice that the research settled on ("live once in each repo's AGENTS.md"). Option 2's reach into interactive sessions is exactly what you declined.

Choices settled with you: missing answers ping (noisy, safe); a bad section refuses the run; read once and frozen; the scope base picks the file so team repos stay clean; tier and test framework stay where they already live; accept is never a standing answer; the three fixed answers from spec 0005 stay global; `done: yes` reaches the model only on a call that `wf` itself computed as the feature's last open box, so it cannot skip `/test` at a Beta `/check verify` on the model's word (your call after the cross check). Decided here: the refusal reuses exit 5 and `refuse()` like every other start refusal; prose lines in the section are ignored so the section can carry a note (as long as it is not a bullet); the manual probe prints the prompt through `python3 -c` instead of a new `wf` flag.

Amended 2026-10-12 (architecture pass, your call): the `cross check` key is dropped. `/architect` never runs under `wf run`, so the key had no user; the cross check stays an interactive panel.
