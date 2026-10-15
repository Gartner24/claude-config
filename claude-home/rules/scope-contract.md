# Scope contract (spec 0003 in ~/claude-config)

The runner (`wf`, `next`) reads scope files. Whenever you write a repo's `docs/scope/` or `.workflow/scope/` (`/scope`, `/architect`, any skill), keep to this.

## Header (repo scopes only, never in a hub)
- `**Source of truth:** scope|issues|mixed` and `**Autopilot:** allowed|off`, at column 0, colon inside the bold, the value as the first word. Missing means `scope` and `off`. Read from the top file only (`scope.md`, or `index.md` for an epic split), before the first `##`/`###` heading and the first box.
- `/scope` new plan: write `**Source of truth:** scope` and `**Autopilot:** off` on their own lines right after the `**Workflow:**` line (no Workflow line: after the last bold `**Key:**` header line). Never below the first `##` heading.
- `/scope` replan: add either line when missing; never change an existing value. Only the user sets `allowed`.
- Never write `**Repo:**`. A hub names its repos in a `Repos` column of its At a glance table: comma separated folder names or `~` paths (a path for an ambiguous name or a repo outside the scanned roots).

## Tags and boxes
- Status tags are `·` segments on the feature heading: `· done`, `· existing`, `· dropped`. Never write `(done)` style tags; old ones stay valid.
- `· auto` on a heading queues the feature for autopilot: `### 4. Headless step loop · in-progress · auto`. `/architect` adds it when the spec is accepted in a repo with `**Autopilot:** allowed` (rules/runner-handoff.md), unless the user says to keep that feature manual. It counts only on an open feature in a repo with `**Autopilot:** allowed`.
- A skipped box is ticked and ends with ` · skipped`: ``- [x] Test it: `/test x` · skipped``. Skipping a parent ticks every box under it the same way. Never skip a whole feature; mark it `· dropped`.
- A box only you can close (a check on the real claude or your phone, a login, a purchase, someone else's action) ends with ` · waits on you`. Any skill writing a scope box adds it; you tick the box yourself; never put it on a box `wf run` should run.
- A waiting box that later boxes do not need also ends with ` · later boxes go on`: ``- [ ] Copy the rule file live · waits on you · later boxes go on``. `wf run` and `next` pass over it to the feature's next open box; the feature's final `/sync` waits until you tick it. `/architect` adds it only when no later box of the feature needs that step done first. The tag counts only on the box's own text, never on a note or parent box.
- A waiting box that `wf` (spec 0019, spec 0020) may run for you also ends with ` · live`: ``- [ ] Copy the rule live: `cp claude-home/rules/x.md ~/.claude/rules/x.md` · waits on you · live``. It needs both tags, exactly one command in backticks, and no other backticked text (no `` `!` ``, no path) or human step in the box. The command is one of four shapes: `cp <repo file> ~/.claude/<same path>` (a leading `claude-home/` on the repo file is dropped, so `claude-home/rules/x.md` goes to `~/.claude/rules/x.md`; never `settings*.json` or `private/`), `bin/install.sh`, `python3 runner/e2e/run.py` (optionally `--parallel`), or `python3`/`bash` of `docs/specs/<dir>/probes/<name>.py|.sh` with no arguments. `/architect` writes them, one step per box; a human step goes in its own box without ` · live`.
- A feature's `/sync` box, when it has one, is its last box. `wf run` runs it as the feature's final call, once every other box is ticked.

## Next box rule (what `next` runs)
- The first unticked box outside `## Deferred`, HTML comments and fenced blocks. `docs/` wins over `.workflow/` when both exist.
- One command per box, in its first backticked span starting with `/`. Milestones are indented under their parent box; an open milestone runs the parent's command.
