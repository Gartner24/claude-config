# Handoff override (beats skill text)

The workflow skills (`/scope`, `/architect`, `/develop`, `/check`, `/test`) end by telling the user
"run /clear, then <next command>". That line predates this rule. Whenever a skill or your own
summary would say it, say this instead:

- Feature still open (any box of it unticked, or uncommitted work): "Commit, then `/rollover`,
  then `/clear`, then `/resume-from-clear`." `/resume-from-clear` continues with the next command.
- Feature closed (heading `· done`) or switching task: "Commit, then `/save-and-clear`, then
  `/clear`, then `<next command>`."

Never end a turn with a bare "/clear" handoff. Before either, uncommitted work is committed and
chat-only decisions are written down (`~/.claude/CLAUDE.md` `### Context`, brief before handoff).
After `/architect` the feature is still open (its Build box is unticked), so that is a `/rollover`.
