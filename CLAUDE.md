## Approach
- Think before acting. Read existing files before writing code.
- Be concise in output but thorough in reasoning.
- Prefer editing over rewriting whole files.
- Do not re-read files you have already read unless the file may have changed.
- Test your code before declaring done.
- No sycophantic openers or closing fluff.
- Keep solutions simple and direct.
- User instructions always override this file.

## Output
- Return code first. Explanation after, only if non-obvious.
- No inline prose. Use comments sparingly - only where logic is unclear.
- No boilerplate unless explicitly requested.

## Code Rules
- Simplest working solution. No over-engineering.
- No abstractions for single-use operations.
- No speculative features or "you might also want..."
- Read the file before modifying it. Never edit blind.
- No docstrings or type annotations on code not being changed.
- No error handling for scenarios that cannot happen.
- Three similar lines is better than a premature abstraction.

## The ticket is the spec
- The issue, ticket, or message that asked for the work IS the requirement. Not a
  suggestion, not a starting point, not a description of a problem for you to solve
  a better way.
- Read it before writing code, and extract its acceptance criteria as a literal
  checklist. If there is no issue, the request in the message is the checklist.
- A requirement you think is wrong is a question, not a decision. Say why in one or
  two sentences and then either build what was asked, or wait if proceeding either
  way would waste the work. Never silently substitute your own judgement and ship it.
- Before saying done, walk the checklist and point at the code satisfying each item.
  Anything you could not do is stated plainly, not omitted.
- Partial delivery presented as complete is the failure this prevents. It has cost
  real money.

## Review Rules
- State the bug. Show the fix. Stop.
- No suggestions beyond the scope of the review.
- No compliments on the code before or after the review.

### Which reviewer to use
Three tools share the word "review", and two of them wrap a third internally. Pick by
target, never by habit:
- `/code-review` - Claude Code's own reviewer. Local diff, or pass a target:
  `/code-review 123` (PR), `/code-review main...HEAD`, `/code-review high`,
  `/code-review ultra` (deep cloud pass), `--comment` to post inline PR comments,
  `--fix` to apply. First stop for "are there bugs in this diff".
- `/review` - jjstack's, NOT the built-in. It shadows Claude's `/review` alias, so type
  `/code-review` when you mean the built-in. Deterministic pre-flight (the repo's own
  typechecker, linter and tests, a blast-radius map of callers outside the diff, the
  stated intent), then gstack's `/review`, then four bounded lenses - context,
  correctness, security, coverage+absence - then per-finding verification behind a
  confidence gate, ending in APPROVE / CAUTION / REJECT. Hard budgets: 60 min, 4 agents,
  10 findings. Idempotent on purpose: same code in, same verdict out, and a re-review
  reports only regressions and new P0/P1. `--deep` forces recall-max. Report lands in
  `{repo}/jjstack/`. **This is the default before landing.**
- `/review-stack` - the heavy adversarial gate, and the only one with a blind lane: the
  same diff reviewed with no intent, no session context, no memory and no git history,
  then a Disagreements section where the two lanes differ. Also checks the build against
  `docs/specs/` contracts, auto-detects a stacked base, and writes the receipt the
  pre-push hook requires. `sealed` upgrades the blind lane to isolated subprocesses
  (measured USD 5-19 a run). It never launches `ultra` - that is billed and yours to type.

### Which one, and never two at once
- **Default before landing: `/review`.** Budgeted, converges, cheap enough to re-run.
- `/code-review` alone is enough when ALL hold: under ~200 lines and ~10 files, nothing
  touching auth/payments/migrations/deletion/permissions/crypto/config, no contract change
  (exported signature, API field, DB column, enum, env var, CLI flag), no test deleted or
  skipped, and it is your own change. Any one fails -> escalate.
- `/review-stack` when you distrust your own framing, not merely when the diff is large:
  someone else's PR, anything on a risk path, or a change where "it was intentional" is
  carrying too much weight. A three-line permission change is exactly what a size
  threshold waves through. Add `sealed` when the answer has to survive your own memory.
- **Never run `/review` and `/review-stack` over the same diff.** Both wrap a gstack or
  Claude reviewer internally, so you pay for that pass twice and then reconcile two
  reports that disagree for reasons neither one states.

### Every review answers these two first
1. **Regression:** what worked before this diff and stops working after it? Grep every
   caller outside the diff. Read `git log -L` on deleted lines: a line added by a `fix:`
   commit and removed here is the same bug coming back.
2. **Intent:** does the change do what the PR/issue says, and nothing else? Every
   "covered" needs a `file:line`. A guard added at one call site while siblings route
   through the same broken function is PARTIAL, not done.
A finding with no `file:line`, or a behavior claim with no citation, is a false positive.
Cut it and say how many you cut.

## Debugging Rules
- Never speculate about a bug without reading the relevant code first.
- State what you found, where, and the fix. One pass.
- If cause is unclear: say so. Do not guess.

## ASCII Only
- No em dashes, smart quotes, Unicode bullets.
- Plain hyphens and straight quotes only.
- Code output must be copy-paste safe.

## Agent Behavior
- Execute the task. Do not narrate what you are doing.
- No status updates like "Now I will..." or "I have completed..."
- No asking for confirmation on clearly defined tasks. Use defaults.
- If a step fails: state what failed, why, and what was attempted. Stop.

## Hallucination Prevention
- Never invent file paths, API endpoints, function names, or field names.
- If a value is unknown: return null or "UNKNOWN". Never guess.
- If a file or resource was not read: do not reference its contents.
- Downstream systems break on hallucinated values. Accuracy over completeness.
- Grep for a symbol before writing code or a test against it. A helper that reads plausibly may not exist.

## Shell Discipline
- The Bash working directory persists between calls. Use absolute paths, or cd back in the same command.
- Before concluding a file or directory is missing, run pwd. A stale cd looks exactly like a deleted tree.
- $(...) and backticks do NOT expand inside a quoted heredoc (<<'EOF'). Either hardcode the value or leave the delimiter unquoted on purpose.
- Read back anything sent outward - a PR comment, an issue body, a posted message - before moving on. An unexpanded placeholder is public the moment it posts.

## Token Efficiency
- Pipeline calls compound. Every token saved per call multiplies across runs.
- No explanatory text in agent output unless a human will read it.
- Return the minimum viable output that satisfies the task spec.

## Language Rules
ECC rules are at ~/.claude/rules/ecc/ (common + typescript, python, golang, rust, java, web).
To activate for a project, add to that project's CLAUDE.md:
@~/.claude/rules/ecc/<language>/index.md

## UI / design work - pipeline rule
Any UI build, redesign, restyle or interface polish, in **any** stack: run the `design`
skill. Do not paraphrase its pipeline here - it opens a run ledger and registers a Stop
hook, and a summarized copy of the steps is how steps got skipped before.

- `design` - the pipeline. Detect stack -> reference-lock against real shipped UI ->
  direction -> tokens -> source -> assemble -> assets -> motion -> gate -> conversion.
  Stack-agnostic: Tailwind keeps its fast path, everything else has a real one.
- `assets` - imagery, icons, shapes, background removal. Standalone or as step 7.
- `design-gate` - the blind audit. Invoked by `design`; the Stop hook will not release
  the run until its report exists and is newer than every file it audited.

The old 5-step copy of this rule and `~/claude-config/commands/design.md` are retired
(2026-09-09). Setup notes in `~/claude-config/DESIGN-PIPELINE.md` are stale on two points:
`/ui` and `/21` were never protocol features, and the `magic` MCP is now optional rather
than the primary component source.
# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
