# Fresh chat after /architect (beats skill text)

Source: the JSM course check, finding 4: "prefer a clear after /architect accepts a spec" (jsm-course-check.md); retire-runner.md promised work: "After /architect accepts a spec, build in a fresh chat."

- Once /architect accepts a spec, the build does not start in the same chat.
- Write the brief first: decisions agreed in chat but not yet in a spec go under "Agreed so far, do not ask again" (`docs/briefs/<feature-slug>.md`), and point the scope row's `Source:` at it.
- Commit, invoke `/rollover` yourself, then say "Type `/clear`, then `/resume-from-clear`." The owner only types `/clear`.
- Batch first still applies: if another feature still needs a decision, run its /architect here before the handoff.
