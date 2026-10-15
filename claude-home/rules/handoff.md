# Handoff override (beats skill text)

The workflow skills (`/scope`, `/architect`, `/develop`, `/check`, `/test`) end by telling the user
"run /clear, then <next command>". That line predates this rule. The user only answers questions
and types `/clear`; you run every other step yourself. Instead of that line:

- Next step is in the same feature's chain (`/check verify`, `/test`, `/sync`): run it now, no handoff.
- Any build or fix work tied to a scope row counts as `/develop` for the chain, even from a free form
  prompt: when it lands, run the rest of the tier chain yourself. A "stop before merge or push" in the
  prompt stops only at merge or push, never after the suite. Never end a turn by printing the next chain
  command.
- Feature still open and a handoff is due (after `/architect`, or past ~150k tokens): commit,
  invoke `/rollover` yourself, then say "Type `/clear`, then `/resume-from-clear`."
- Feature closed (heading `· done`) or switching task: commit, invoke `/save-and-clear` yourself,
  then say "Type `/clear`, then `<next command>`."

Never end a turn with a bare "/clear" handoff, and never ask the user to type `/rollover` or
`/save-and-clear`. Before either, chat-only decisions are written down (`~/.claude/CLAUDE.md`
`### Context`, brief before handoff).
