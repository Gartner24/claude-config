## Workflow (JSM skills + ours)
State lives in repo files, never only in chat: `AGENTS.md`, `docs/scope/`, `docs/specs/`,
`design.md`, `docs/reviews/`. In bot-reviewed team repos the same tree lives under a
gitignored `.workflow/`. Full guide: ~/Documents/workflow-research/05-new-workflow.md.
Branches and PRs follow `rules/branch-pr.md`: one branch per spec, stacked only on `**Stacks on:**`, one commit per feature, PRs open as drafts.

### Route by situation
- Session start in a repo: run `/scope` with no argument and state where things stand.
- Repo has no `AGENTS.md`: `/audit` first. No `docs/scope/`: `/scope` before feature work.
- A load-bearing choice is unmade (stack, data model, provider, page design, feature
  behavior): `/architect`. Never decide it inside a build.
- Build a feature or fix scoped in the plan: `/develop`.
- After `/develop`, or any chain step the user typed (`/check verify`, `/test`), follow
  the project tier from the scope header:
  Prototype stop; Alpha `/check verify`; Beta + `/test`; GA + review + `/document`.
  Run the rest of the chain yourself without asking, then `/sync`. Stop only on a failure,
  an owed decision, or a step that pushes, merges, posts, or bills (`/review-stack`, `ultra`).
  Handoffs (`/rollover`, `/save-and-clear`, `/clear`): `rules/handoff.md`. Feature closed: `/sync` first.
- UI changed: `/check verify` plus `design-gate`. New design or restyle: `design` pipeline.
- Review: `## Review Rules` below decide the reviewer.
- PR text: `/document pr`. Other prose: `/write`.
- Bug, failing test, wrong behavior: `/debug`.
- Which skill, cost and who starts it: `rules/skill-map.md`.
- A chat opening in a repo starts `/audit` or `/scope` by itself (wf-handoff mod), and a Stop hook
  (`hooks/chain-catch.py`) refuses to end a turn while a planned step or a `/debug` for a red test is owed.

### Decision gate (defines "clearly defined")
A task is clearly defined only if every value it produces, computes or displays has a
named source in a spec, `AGENTS.md`, or the request. Any value without one is an owed
decision: stop and route to `/architect`, or record an `Assumed` spec if told to build
anyway. Surface every `Assumed` spec before starting new work.

### Todos
- Repo work lives only in that repo's `docs/scope/`. No TODO.md, STATE.md or progress
  files in repos; skills own the status lines.
- Cross-repo work: hub scope at `~/projects/<area>/docs/scope/` (freelance, work).
- Personal, non-code: `~/projects/docs/scope/scope.md`.
- When the user lists todos in chat, put each one in the right scope with `/scope <item>`
  instead of answering with a list.
- Every scope row names its Source (GitHub issue, spec, review report, or the user's
  message). When the source is an issue, link it, read it before planning or building, and
  take the row's intent and Done when from what the issue actually asks, not a summary.

### Context
- Clear at boundaries (feature closed), not by token count.
- Size: the handoff mod hands a chat off by itself at 250k tokens. Never run `/rollover` for
  size before that, only when the mod says auto handoff is paused or off.
- Brief before every handoff (any `/clear`, `/rollover`, `/save-and-clear`, or a command
  given for another session): decisions agreed in chat but not yet in a spec, scope row or
  `AGENTS.md` go first into a brief under a top section "Agreed so far, do not ask again".
  Use the file the scope row's `Source:` names, else `docs/briefs/<feature-slug>.md`
  (`.workflow/briefs/` in bot-reviewed repos), and point the row's `Source:` at it.
  `/scope` and `/architect` read that brief and list anything they drop or weaken.
- One brief per feature, and it is the feature's handover index (spec 0069): its four sections hold
  open questions, things shown and still needed, agreed decisions and live state, one quoted item
  each, written with `~/claude-config/tools/scripts/handover-memory.py` (`rules/handover-carry.md`).
  `/sync` deletes it when the feature closes (`rules/check-gates.md` gate 5).
- Which handoff (feature open vs closed): `rules/handoff.md`.
- Long single feature: suggest `/compact` mid build. Autocompact (700k) is a last resort.

### Never in a repo
`.gstack/`, `jjstack/`, `.superpowers/`, `.claude/settings.local.json`, `.design/run*.json`,
review worktrees. If a tool creates one, it is globally ignored; do not commit it.

## Language Rules
ECC rules live in ~/.claude/rules/ecc/ but are excluded from loading (claudeMdExcludes in
settings.json) - most restate default practice. Read one on demand if a task needs it.
The kept, project-specific lessons are in ~/.claude/rules/lessons.md (always loaded).
