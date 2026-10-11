# 0003. Scope contract for the runner: rationale

Build spec: [index.md](index.md).

## Context

Release 2 onward runs features unattended, so the runner must read per repo switches from the scope files themselves (research section 0: the queue is the scope files, no new queue file). Today nothing defines those switches: no scope in any of the 25 repos carries `**Repo:**`, `**Source of truth:**` or `**Autopilot:**`, and the scope template mentions "skipped" boxes without a syntax, so `next` reads them as open.

The skills that write scopes, `/scope` and `/architect`, are vendored from an upstream repo into `~/.claude/vendor-jsm-skills`. An edit inside them is lost on the next vendor pull. Whatever teaches them the contract must survive that, and must also load in headless `claude -p` runs.

The next box rule already exists as code and tests (spec 0002, AC-5, AC-6, AC-11). Status tags exist in two styles (`· done` and `(done)`), and the parser reads both. Hubs (personal, freelance, work) track cross repo work; the freelance hub already names repos in a `Repos` column.

## Options considered

### Option 1: Always loaded rule file plus a header check in `wf` (chosen)
A short rule file in `~/.claude/rules/` teaches the skills; `wf` parses and warns.

**Pros**:
- Survives vendor updates and loads in every session, headless included.
- One tested check reads what the skills write before Release 2 depends on it.

**Cons**:
- The rule sits outside the skill text, so a skill can still miss it; only the warning and the manual check catch that.
- Costs some context in every session, in every repo.

### Option 2: Patch the vendored skills in place
Edit the scope template and the architect capture step directly.

**Pros**:
- The rule is exactly where the skill reads it.

**Cons**:
- The next vendor pull silently removes it, the same failure as the jjstack `location: home` edit in personal scope row 2.

### Option 3: Fork the vendored skills
Keep a fork with the patches, rebased on upstream.

**Pros**:
- Durable, and the rule lives in the skill.

**Cons**:
- A fork to maintain and rebase for a handful of lines.

### Option 4: Contract only, no reader
The spec and rule file only; Release 2 writes the parser.

**Pros**:
- Smallest change now.

**Cons**:
- Nothing checks the skills' output until the runner depends on it unattended.

## Rationale

The force that decides it is the vendoring. A rule inside the skill is the strongest placement, but a vendor pull removes it with no signal; a fork fixes that at the cost of a permanent rebase chore. The rules folder is already the always loaded channel (`lessons.md`), already synced by `sync.sh`, and loads in `claude -p` runs, which is where the contract matters most.

Defaults of `scope` and `off` make the contract opt in: 25 existing scopes stay valid with zero edits, and nothing runs unattended until you write `allowed`. The header check is small, and it turns a typo like `Autopilot: on` into a visible warning instead of a silent `off` (or worse, a silent `allowed` in a later release).

`**Repo:**` is dropped from repo scopes because a file naming its own folder goes stale when the repo moves and is wrong in every worktree. The research goal behind it, finding a repo from a hub, is met by the hub `Repos` column the freelance hub already uses. The `· auto` and `· skipped` forms reuse the `·` segment the parser and the display stripping already handle, so neither needs new parser code.
