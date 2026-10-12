# Standing answers for interactive sessions (beats skill text)

When a skill would ask one of these, do not ask. Take the answer, and say it in one line
("cross check: another model (standing)").

- `/architect` "Cross check this spec?": another model.
- `/architect` "Does this data model match?": matches. The spec summary still shows it.
- `/architect` "References / sources?": none. A design that depends on an outside tool
  still gets its probe (`spec-gate.md`).
- `/architect` accept the spec: accept it yourself when all hold, then print its
  "What you're agreeing to" section and the commit:
  - the user answered the cross check gaps panel (that panel is still asked);
  - every probe the spec requires before accept has passed, or the spec says plainly
    that the build runs them first and stops on a failure;
  - nothing in it contradicts `docs/architecture.md` or another accepted spec.
  If any fails, say which and ask. The user can still say "change it" afterwards.
- `/check verify` "Save verify steps?": save to verify.md.
- `/document` "Doc type?": the recommended option.
- Agent skills or tool discovery offer: not now, later.
- `/test` "Run the suite?": yes.
- "Mark the feature done?" after verify and test passed: yes.

Still ask: design choices in the `/architect` interview, the cross check gaps panel,
anything that pushes, merges, posts, bills or deletes, and any question not listed here.
`wf run` keeps its own rules: an unattended call never accepts a spec.
