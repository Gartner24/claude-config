# Plugins

Installed via `claude plugin install`. Auto-update on Claude Code launch.

## Core pair: superpowers + claude-mem

These two were installed together and are designed to work as a unit.
- **superpowers** provides the skill execution framework - structured workflows for debugging, TDD, code review, planning, etc.
- **claude-mem** provides persistent memory across sessions - what Claude remembers between conversations.

Without claude-mem, superpowers forgets context between sessions. Without superpowers, claude-mem has no structured skill workflows to remember outcomes from.

## Installed plugins

### superpowers `v5.1.0`
**Source:** `claude-plugins-official/superpowers`
**Install:** `claude plugin install superpowers`
**Skills it adds:** `/brainstorming`, `/test-driven-development`, `/systematic-debugging`, `/writing-plans`, `/executing-plans`, `/subagent-driven-development`, `/dispatching-parallel-agents`, `/requesting-code-review`, `/receiving-code-review`, `/finishing-a-development-branch`, `/using-git-worktrees`, `/verification-before-completion`, `/writing-skills`

The foundation. Adds structured, opinionated workflows for every major dev activity. Always loaded. Most other skills integrate with it.

---

### claude-mem `v13.3.0`
**Source:** `thedotmack/claude-mem`
**Install:** `claude plugin install claude-mem`
**Skills it adds:** `/mem-search`, `/learn-codebase`, `/smart-explore`, `/knowledge-agent`, `/make-plan`, `/do`, `/babysit`, `/weekly-digests`, `/timeline-report`, `/pathfinder`, `/wowerpoint`, `/oh-my-issues`, `/how-it-works`, `/design-is`, `/version-bump`

Persistent cross-session memory. Claude remembers your projects, decisions, and preferences between conversations. Run `/learn-codebase` when starting on a new repo. Run `/mem-search` to recall past solutions.

---

### frontend-design
**Source:** `claude-plugins-official/frontend-design`
**Install:** `claude plugin install frontend-design`
**Skills it adds:** `/frontend-design`

Anthropic's official frontend design skill. Baseline for UI work. Impeccable and taste skills build on top of this.

---

### code-review
**Source:** `claude-plugins-official/code-review`
**Install:** `claude plugin install code-review`
**Skills it adds:** `/code-review` (effort levels: low/medium/high/max, `--comment` for inline PR comments)

Focused diff review. Use before merging. Pairs with `/review` (gstack) for pre-landing checks.

---

### feature-dev
**Source:** `claude-plugins-official/feature-dev`
**Install:** `claude plugin install feature-dev`
**Agents it adds:** `code-architect`, `code-explorer`, `code-reviewer`

Spawnable subagents for feature planning and implementation. Used internally by other skills that need deep codebase analysis.

---

### code-simplifier `v1.0.0`
**Source:** `claude-plugins-official/code-simplifier`
**Install:** `claude plugin install code-simplifier`

Refactors recently modified code for clarity. Runs as a subagent. Use after completing a feature to clean up before review.

---

### ralph-loop `v1.0.0`
**Source:** `claude-plugins-official/ralph-loop`
**Install:** `claude plugin install ralph-loop`
**Skills it adds:** `/ralph-loop`, `/cancel-ralph`

Autonomous loop runner. Keeps Claude running on a task continuously without manual re-prompting. Use for long background tasks.

---

### clangd-lsp `v1.0.0`
**Source:** `claude-plugins-official/clangd-lsp`
**Install:** `claude plugin install clangd-lsp`

C/C++ Language Server Protocol integration. Adds LSP tool for C/C++ projects.
