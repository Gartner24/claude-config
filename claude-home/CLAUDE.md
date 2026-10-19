## Approach
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

## Workflow (JSM skills + ours)
State lives in repo files, never only in chat: `AGENTS.md`, `docs/scope/`, `docs/specs/`,
`design.md`, `docs/reviews/`. In bot-reviewed team repos the same tree lives under a
gitignored `.workflow/`. Full guide: ~/Documents/workflow-research/05-new-workflow.md.
Branches and PRs follow `rules/branch-pr.md`: one branch per spec, stacked only on `**Stacks on:**`, one commit per feature, draft PRs only.

### Route by situation
- Session start in a repo: run `/scope` with no argument and state where things stand.
- Repo has no `AGENTS.md`: `/audit` first. No `docs/scope/`: `/scope` before feature work.
- A load-bearing choice is unmade (stack, data model, provider, page design, feature
  behavior): `/architect`. Never decide it inside a build.
- Build a feature or fix scoped in the plan: `/develop`.
- After `/develop`, or any chain step the user typed (`/check verify`, `/test`), follow
  the project tier from the scope header:
  Prototype stop; Alpha `/check verify`; Beta + `/test`; GA + review + `/document`.
  Run the rest of the chain yourself without asking, then `/sync`. Stop only on a failure,
  an owed decision, or a step that pushes, merges, posts, or bills (`/review-stack`, `ultra`).
  The user only answers questions and types `/clear`; every other handoff step is yours.
  When the feature closes, invoke `/save-and-clear` yourself and tell the user to type
  `/clear`, then the next command. Mid feature (after `/architect`):
  invoke `/rollover` yourself and tell the user to type `/clear`; a start up hook loads the
  handover (`/resume-from-clear` still works by hand).
- UI changed: `/check verify` plus `design-gate`. New design or restyle: `design` pipeline.
- Review: `## Review Rules` below decide the reviewer. Never `/check review`.
- PR text: `/document pr`. Other prose: `/write`.
- Bug, failing test, wrong behavior: `/debug`.
- Feature closed: `/sync`, invoke `/save-and-clear`, then stop and say: "Feature closed.
  Type /clear, then `<next command from /scope>`."

### Decision gate (defines "clearly defined")
A task is clearly defined only if every value it produces, computes or displays has a
named source in a spec, `AGENTS.md`, or the request. Any value without one is an owed
decision: stop and route to `/architect`, or record an `Assumed` spec if told to build
anyway. Surface every `Assumed` spec before starting new work.

### Todos
- Repo work lives only in that repo's `docs/scope/`. No TODO.md, STATE.md or progress
  files in repos; skills own the status lines.
- Cross-repo work: hub scope at `~/projects/<area>/docs/scope/` (freelance, work).
- Personal, non-code: `~/projects/docs/scope/scope.md`.
- When the user lists todos in chat, put each one in the right scope with `/scope <item>`
  instead of answering with a list.
- Every scope row names its Source (GitHub issue, spec, review report, or the user's
  message). When the source is an issue, link it, read it before planning or building, and
  take the row's intent and Done when from what the issue actually asks, not a summary.

### Context
- Clear at boundaries (feature closed), not by token count.
- Size: the wf-handoff mod hands a chat off by itself at 200k tokens. Never run `/rollover` for
  size before that, only when the mod says auto handoff is paused or off.
- Brief before every handoff (any `/clear`, `/rollover`, `/save-and-clear`, or a command
  given for another session): decisions agreed in chat but not yet in a spec, scope row or
  `AGENTS.md` go first into a brief under a top section "Agreed so far, do not ask again".
  Use the file the scope row's `Source:` names, else `docs/briefs/<feature-slug>.md`
  (`.workflow/briefs/` in bot-reviewed repos), and point the row's `Source:` at it.
  `/scope` and `/architect` read that brief and list anything they drop or weaken.
- Which handoff: feature still open (boxes unticked, uncommitted work, a step half done)
  -> `/rollover`, then `/clear` (the handover loads itself; `/resume-from-clear` by hand
  also works). Feature closed or switching
  task -> `/save-and-clear`, then `/clear`.
- Long single feature: suggest `/compact` mid build. Autocompact (700k) is a last resort.

### Never in a repo
`.gstack/`, `jjstack/`, `.superpowers/`, `.claude/settings.local.json`, `.design/run*.json`,
review worktrees. If a tool creates one, it is globally ignored; do not commit it.

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
  `~/.gstack/projects/<slug>/` (scratch stays out of the repo); copy only the final `review-YYYY-MM-DD.md` into `docs/reviews/`. **The default before landing - except in bot-reviewed repos (below).**
- `/jj-security-review` - jjstack's security pass. **Renamed from `/security-review` in
  jjstack 0.40.2 (pulled 2026-09-09)** specifically so Claude Code's own built-in
  `/security-review` stays reachable - the built-in has no other name. So: `/security-review`
  is now Anthropic's, `/jj-security-review` is jjstack's (Anthropic's methodology + Sentry's
  investigation-first approach + OWASP Top 10:2025 + MCP-specific CWE). Neither is `/review`.
- `/review-stack` - the heavy adversarial gate, and the only one with a blind lane: the
  same diff reviewed with no intent, no session context, no memory and no git history,
  then a Disagreements section where the two lanes differ. Also checks the build against
  `docs/specs/` contracts, auto-detects a stacked base, and writes the receipt the
  pre-push hook requires. `sealed` upgrades the blind lane to isolated subprocesses
  (measured USD 5-19 a run). It never launches `ultra` - that is billed and yours to type.

### Which one, and never two at once
Bot-reviewed repos (which orgs, which bot, what to run there) are defined in the private file:

@~/.claude/private/work.md

- **Everything else - my own and freelance repos - default before landing: `/review`.**
  Budgeted, converges, cheap enough to re-run. When it finishes, copy its final
  `review-YYYY-MM-DD.md` into `docs/reviews/`; no
  other jjstack file enters a repo.
- `/code-review` alone is enough when ALL hold: under ~200 lines and ~10 files, nothing
  touching auth/payments/migrations/deletion/permissions/crypto/config, no contract change
  (exported signature, API field, DB column, enum, env var, CLI flag), no test deleted or
  skipped, and it is your own change. Any one fails -> escalate.
- `/review-stack` (in bot-reviewed repos: only when I ask) when you distrust your own framing, not merely when the diff is large:
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
- Grep for a symbol before writing code or a test against it. A helper that reads plausibly may not exist.

## Shell Discipline
- The Bash working directory persists between calls. Use absolute paths, or cd back in the same command.
- Before concluding a file or directory is missing, run pwd. A stale cd looks exactly like a deleted tree.
- $(...) and backticks do NOT expand inside a quoted heredoc (<<'EOF'). Either hardcode the value or leave the delimiter unquoted on purpose.
- Read back anything sent outward - a PR comment, an issue body, a posted message - before moving on. An unexpanded placeholder is public the moment it posts.

## Language Rules
ECC rules live in ~/.claude/rules/ecc/ but are excluded from loading (claudeMdExcludes in
settings.json) - most restate default practice. Read one on demand if a task needs it.
The kept, project-specific lessons are in ~/.claude/rules/lessons.md (always loaded).

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
(2026-09-09). Setup notes in `~/claude-config/docs/guides/DESIGN-PIPELINE.md` are stale on two points:
`/ui` and `/21` were never protocol features, and the `magic` MCP is now optional rather
than the primary component source.
# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

## Superpowers
- Ignore the "1% chance -> must invoke" rule. Invoke a skill only when it clearly matches the task.
- Use superpowers only for subagent-driven-development and dispatching-parallel-agents. Planning, building, verifying and debugging follow `## Workflow` above.
