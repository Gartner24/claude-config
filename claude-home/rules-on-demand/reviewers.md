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
  `~/.gstack/projects/<slug>/` (scratch stays out of the repo); copy only the final `review-YYYY-MM-DD.md` into `docs/reviews/`.
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
- Never `/check review`. Never run `/review` and `/review-stack` over the same diff
  (you pay for the wrapped reviewer twice and reconcile two disagreeing reports).
- `/code-review` alone is enough when ALL hold: under ~200 lines and ~10 files, nothing
  touching auth/payments/migrations/deletion/permissions/crypto/config, no contract change
  (exported signature, API field, DB column, enum, env var, CLI flag), no test deleted or
  skipped, and it is your own change. Any one fails -> escalate.
- `/review-stack` (in bot-reviewed repos: only when I ask) when you distrust your own framing, not merely when the diff is large:
  someone else's PR, anything on a risk path, or a change where "it was intentional" is
  carrying too much weight. A three-line permission change is exactly what a size
  threshold waves through. Add `sealed` when the answer has to survive your own memory.
