# Scope contract (spec 0003 in ~/claude-config)

Whenever you write a repo's `docs/scope/` or `.workflow/scope/` (`/scope`, `/architect`, any skill), keep to this.

## Header (repo scopes only, never in a hub)
- `**Source of truth:** scope|issues|mixed`, at column 0, colon inside the bold, the value as the first word. Missing means `scope`. Read from the top file only (`scope.md`, or `index.md` for an epic split), before the first `##`/`###` heading and the first box.
- `/scope` new plan: write `**Source of truth:** scope` on its own line right after the `**Workflow:**` line (no Workflow line: after the last bold `**Key:**` header line). Never below the first `##` heading.
- `/scope` replan: add the line when missing; never change an existing value.
- Never write `**Repo:**`. A hub names its repos in a `Repos` column of its At a glance table: comma separated folder names or `~` paths (a path for an ambiguous name or a repo outside the scanned roots).

## Tags and boxes
- Status tags are `·` segments on the feature heading: `· done`, `· existing`, `· dropped`. Never write `(done)` style tags; old ones stay valid.
- A skipped box is ticked and ends with ` · skipped`: ``- [x] Test it: `/test x` · skipped``. Skipping a parent ticks every box under it the same way. Never skip a whole feature; mark it `· dropped`.
- A box only you can close (a check on the real claude or your phone, a login, a purchase, someone else's action) ends with ` · waits on you`. Any skill writing a scope box adds it; you tick the box yourself.
- A waiting box that later boxes do not need also ends with ` · later boxes go on`: ``- [ ] Copy the rule file live · waits on you · later boxes go on``. Work passes over it to the feature's next open box; the feature's final `/sync` waits until you tick it. `/architect` adds it only when no later box of the feature needs that step done first. The tag counts only on the box's own text, never on a note or parent box.
- A feature's `/sync` box, when it has one, is its last box. It runs once every other box is ticked.

## Next box rule
- The first unticked box outside `## Deferred`, HTML comments and fenced blocks. `docs/` wins over `.workflow/` when both exist.
- One command per box, in its first backticked span starting with `/`. Milestones are indented under their parent box; an open milestone runs the parent's command.
