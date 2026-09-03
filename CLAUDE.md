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

## Review Rules
- State the bug. Show the fix. Stop.
- No suggestions beyond the scope of the review.
- No compliments on the code before or after the review.

### Which reviewer to use
Three different tools share the word "review". Pick by target, never by habit:
- `/code-review` - Claude Code's own reviewer. Local diff, or pass a target:
  `/code-review 123` (PR), `/code-review main...HEAD`, `/code-review high`,
  `/code-review ultra` (deep cloud pass), `--comment` to post inline PR comments,
  `--fix` to apply. First stop for "are there bugs in this diff".
- `/review-stack` - the multi-agent gate. Adds what /code-review does not run:
  regression-hunter, pr-intent-verifier, security, DB concurrency. Takes a PR number
  too, and **invokes /code-review itself** as a seventh reviewer, so never run both by
  hand. Use before shipping and on every PR from someone else. It never launches
  `ultra` - that is billed and yours to type.
- `/review` - jjstack's local pre-landing pass. NOT the built-in. It shadows Claude's
  `/review` alias, so type `/code-review` when you mean the built-in.

### Which one: /code-review or /review-stack
`/code-review` alone is enough when ALL hold: under ~200 lines and ~10 files, nothing
touching auth/payments/migrations/deletion/permissions/crypto/config, no contract change
(exported signature, API field, DB column, enum, env var, CLI flag), no test deleted or
skipped, and it is your own change. Any one fails -> `/review-stack`. Two override size
outright: someone else's PR, and anything on a risk path. A three-line permission change
is exactly what a size threshold waves through.

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
For any UI build or redesign in a React + Tailwind project (full setup: ~/claude-config/DESIGN-PIPELINE.md):
1. Lock direction first. A reference the user points at (screenshot/image/URL) -> design-dna to extract it. Otherwise ui-ux-pro-max: style + palette + font pairing + stack. Reuse the saved project/client direction if one exists; otherwise propose 2 and wait.
2. Source components from the magic MCP (21st.dev) before hand-rolling - use /ui or /design.
3. Assemble with frontend-design + impeccable.
4. Add motion only where it earns its place - Kowalski restraint, no motion slop. Pick by kind: animate (general), transitions-dev (plain CSS transitions), gsap-scrolltrigger/gsap-timeline (scroll + choreography), apple-design (gesture/spring/physical), threejs-* (3D).
5. Before showing anything: run /impeccable critique (UX) AND /impeccable audit (a11y/perf/responsive) AND a motion audit (review-animations on the diff, improve-animations on a whole app, transitions-polish for timing). Report what failed, fix it, then present.
Never skip step 5. If the stack is not React/Tailwind, skip step 2 (Magic is React-only).
# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
