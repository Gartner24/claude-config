# Spec gate (beats skill text)

- What you're agreeing to: every new or amended spec opens with this section, at most
  5 plain lines, before any acceptance criteria. No jargon, no AC numbers. The accept
  question quotes it, so accepting is a decision the user can actually make.
- Probe before accept: when a design depends on how an outside tool behaves (CLI flags,
  headless mode, hooks, an API), run a real probe before the spec is accepted and record
  the command and result in verify.md. Docs or research alone are "unconfirmed", never
  "confirmed".
- Small change fast path: one file, no new behaviour, no new value without a source
  (wording, a label, a typo, a constant the spec already names). Skip the cross check.
  Skip the spec amendment unless the spec quotes the exact text. Still build with a test
  and run the tier chain.
- Bookkeeping lines: `/sync` may update a spec's status, "Amended by" and "built in
  <commit>" lines itself. Anything else in a spec stays `/architect`'s.
- System view: when the repo has `docs/architecture.md`, `/architect` reads it first,
  names which of its invariants the decision touches, and updates it in the same commit
  when a decision changes one.
