# After a review: fix, ask, or stop (beats skill text)

Applies after `/review`, `/review-stack`, `/code-review`, or a bot review on a PR. Sort every
confirmed finding (it has a `file:line`) into one group:

- **Fix now, no question:** the fix is local and changes no accepted spec text, no behavior the
  user would notice, and adds no value without a named source. Fix it with a test and a
  mutation check (`rules/lessons.md`).
- **Ask:** the fix changes accepted spec text, picks between behaviors, trades safety against
  convenience, or would leave a known risk. One question panel for all of them, a recommended
  option on each (`rules/plain-questions.md`). Spec text changes go through `/architect`.
- **Never automatic:** push, merge, rewriting pushed history, anything billed.

Group the "fix now" findings by file. Groups that share no file may be fixed in parallel, one
subagent per group in its own git worktree, then merged back; findings in the same file stay in one
sequence. Run the full suite once after the merge.

Then run the tier chain yourself (`rules/handoff.md`): `/check verify`, `/test`, `/sync`.

## Stopping point
- A re-review covers only the fix commits, never the whole range again.
- At most 2 review rounds per landing. After round 2, any finding left at MEDIUM or below is not
  fixed in this round: write it into the review brief's `## Leftovers` with its `file:line`, and add
  one scope row "Review leftovers <date>" whose `Source:` is that brief. Then tell the user it is
  ready to merge, and list the leftovers in one line each.
- A HIGH or CRITICAL left after round 2 blocks the merge: say so and ask.
- Leftovers are bugs, not specs. They are fixed later with `/debug` or `/develop` from the scope
  row; only one whose fix needs a decision goes to `/architect`.
