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

Old copies of this rule and `docs/guides/DESIGN-PIPELINE.md` are retired or stale; trust `design`.
