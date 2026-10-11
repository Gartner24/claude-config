# Scope contract (spec 0003 in ~/claude-config)

The runner (`wf`, `next`) reads scope files. Whenever you write a repo's `docs/scope/` or `.workflow/scope/` (`/scope`, `/architect`, any skill), keep to this.

## Header (repo scopes only, never in a hub)
- `**Source of truth:** scope|issues|mixed` and `**Autopilot:** allowed|off`, at column 0, colon inside the bold, the value as the first word. Missing means `scope` and `off`. Read from the top file only (`scope.md`, or `index.md` for an epic split), before the first `##`/`###` heading and the first box.
- `/scope` new plan: write `**Source of truth:** scope` and `**Autopilot:** off` on their own lines right after the `**Workflow:**` line (no Workflow line: after the last bold `**Key:**` header line). Never below the first `##` heading.
- `/scope` replan: add either line when missing; never change an existing value. Only the user sets `allowed`.
- Never write `**Repo:**`. A hub names its repos in a `Repos` column of its At a glance table: comma separated folder names or `~` paths (a path for an ambiguous name or a repo outside the scanned roots).

## Tags and boxes
- Status tags are `·` segments on the feature heading: `· done`, `· existing`, `· dropped`. Never write `(done)` style tags; old ones stay valid.
- `· auto` on a heading queues the feature for autopilot: `### 4. Headless step loop · in-progress · auto`. `/architect` adds it at spec capture only when the user asks to queue that feature, never on its own. It counts only on an open feature in a repo with `**Autopilot:** allowed`.
- A skipped box is ticked and ends with ` · skipped`: ``- [x] Test it: `/test x` · skipped``. Skipping a parent ticks every box under it the same way. Never skip a whole feature; mark it `· dropped`.

## Next box rule (what `next` runs)
- The first unticked box outside `## Deferred`, HTML comments and fenced blocks. `docs/` wins over `.workflow/` when both exist.
- One command per box, in its first backticked span starting with `/`. Milestones are indented under their parent box; an open milestone runs the parent's command.
