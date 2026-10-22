# Handoff override (beats skill text)

The workflow skills (`/scope`, `/architect`, `/develop`, `/check`, `/test`) end by telling the user
"run /clear, then <next command>". That line predates this rule. The user only answers questions
and types `/clear`; you run every other step yourself. Instead of that line:

- Next step is in the same feature's chain (`/check verify`, `/test`, `/sync`): run it now, no handoff.
- Any build or fix work tied to a scope row counts as `/develop` for the chain, even from a free form
  prompt: when it lands, run the rest of the tier chain yourself. A "stop before merge or push" in the
  prompt stops only at merge or push, never after the suite. Never end a turn by printing the next chain
  command.
- Feature still open and a handoff is due (after `/architect`; a size handoff is the handoff mod's, see `### Context`): commit,
  invoke `/rollover` yourself, then say "Type `/clear`, then `/resume-from-clear`."
- Feature closed (heading `· done`) or switching task: commit, invoke `/save-and-clear` yourself,
  then say "Type `/clear`, then `<next command>`."

## Owed steps are caught (spec 0070)

- A turn that ends while a step is owed is refused by `hooks/chain-catch.py`, with `owed: <step>`
  lines: run the step, or tick its box ` · skipped` in the scope with the reason. After 3 refusals in
  one turn it lets the turn end and shows the owner what is still owed.
- `/debug` started by the catch, or by any failing test, applies its minimal fix without asking, then
  reruns the test. It still stops under `rules/stop-and-reset.md` after 2 failed fixes on the same cause.

Never end a turn with a bare "/clear" handoff, and never ask the user to type `/rollover` or
`/save-and-clear`. Before either, chat-only decisions are written down (`~/.claude/CLAUDE.md`
`### Context`, brief before handoff).

## Not live is not fixed (2026-10-22)

- A fix is "fixed" only when it is merged and live (for a mod or skill: merged into the checkout
  `~/.claude` links to). Until then say "in PR #N, not live yet", never "fixed" or "done".
- A fresh chat opens its first reply with every unmerged PR and branch the handover or the wf-handoff
  mod's "Open PRs" list names, then merges the ones the self-merge checklist allows
  (`rules/when-to-switch-on.md`), before other work.
- A tool refusal is not the owner's rule. Never write "do not merge" (or "do not X yourself") into a
  handover or memory because a classifier refused once; write the refusal as a fact with the exact
  command, and ask the owner.
