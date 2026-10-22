# Are we reinventing the wheel? Runner landscape, 2026-10-14

Scope: compare our runner (`wf`, Python, about 11,700 lines in _archive/runner/, 43 specs) with public projects that run coding agents unattended or in parallel. Stars, push dates and licenses come from `gh api repos/OWNER/REPO` on 2026-10-14. Behavior comes from READMEs I opened (copied to scratch), DeepWiki answers on each repo, and two vendor docs pages. DeepWiki answers are AI summaries of the code, so treat file names they give as pointers, not proof. I did not run any of these tools.

## 1. The candidates (verified to exist)

| Project | Stars | Last push | License | Verdict |
|---|---|---|---|---|
| OpenHands/OpenHands | 90.9k | 2026-10-14 | MIT | current, audited lightly |
| ruvnet/ruflo (was claude-flow) | 74.7k | 2026-10-14 | MIT | current, swarm framework |
| Aider-AI/aider | 49.6k | 2026-05-22 | Apache-2.0 | slowing; a chat tool, not a runner |
| conductor-oss/conductor | 32.3k | 2026-10-14 | Apache-2.0 | dropped: workflow engine, not a coding-agent tool, name clash only |
| BloopAI/vibe-kanban | 28.4k | 2026-09-19 | Apache-2.0 | README says "sunsetting" (shutdown announced) |
| eyaltoledano/claude-task-master | 28.2k | 2026-04-28 | NOASSERTION | task list for agents, not a runner |
| SWE-agent/SWE-agent | 20.6k | 2026-10-12 | MIT | research agent, one issue per run |
| OrchestratorInc/agent-orchestrator | 13.2k | 2026-10-14 | Apache-2.0 | audited in depth |
| frankbria/ralph-claude-code | 9.7k | 2026-10-10 | MIT | simple loop script |
| anthropics/claude-code-action | 9.5k | 2026-10-14 | MIT | audited in depth |
| smtg-ai/claude-squad | 8.6k | 2026-08-20 | AGPL-3.0 | audited briefly |
| MrLesk/Backlog.md | 7.0k | 2026-10-14 | MIT | audited briefly |
| generalaction/emdash | 6.0k | 2026-10-14 | Apache-2.0 | audited in depth |
| dagger/container-use | 4.1k | 2026-09-21 | Apache-2.0 | audited in depth |
| stravu/crystal | 3.1k | 2026-02-26 | MIT | stale (8 months), skipped |
| mikeyobrien/ralph-orchestrator | 3.2k | 2026-10-13 | MIT | audited in depth |
| kbwo/ccmanager | 1.3k | 2026-10-12 | MIT | session manager, skipped |
| johannesjo/parallel-code | 1.0k | 2026-10-14 | MIT | small, skipped |
| devflowinc/uzi | 0.6k | 2025-06-04 | MIT | dead, dropped |
| sweepai/sweep | 7.7k | 2025-09-18 | NOASSERTION | dormant, dropped |
| GitHub Copilot coding agent | n/a (hosted) | n/a | proprietary | docs read |
| OpenAI Codex cloud tasks | n/a (hosted; CLI openai/codex 129k stars, Apache-2.0) | n/a | proprietary | docs read |

Note: Conductor (the Mac app, closed source) has no public repo, so it could not be audited. Crystal is stale and was superseded by Nimbalyst per its own history; skipped.

## 2. In-depth audit (6 projects)

### Orchestrator.inc (OrchestratorInc/agent-orchestrator)
Sources: README (opened), DeepWiki. Doc files named by DeepWiki: `docs/architecture.md`, `frontend/src/docs/content/configuration/lifecycle-automation.mdx`, `.../guides/parallel-issues.mdx`, `backend/internal/session_manager/prompt.go`.
- Task source: you type a task, or the project "orchestrator" agent splits a goal into tasks; also GitHub and GitLab issues (`--tracker-provider`). Saved prompts ("Cues"). No plan file with checkboxes.
- Isolation: one git worktree and branch per worker. A hosted cloud service can use Docker/Coder sandboxes. No OS-level sandbox locally.
- Parallelism: many workers, live Kanban board. Board column derived from session, PR, CI, and review state ("Needs you", "In review", "Ready to merge").
- Human in the loop: session state `waiting_input`, worker calls `ao report --needs-input`. Desktop toast, in-app feed, push to a paired phone. DeepWiki says no Telegram, Slack or ntfy.
- Verification: reads PR, CI, review state and sends failures and review comments back to the owning agent. No mutation-style proof.
- Git/PR: worker owns commits and PR. Merge conflicts surfaced.
- Unattended: recurring "Automations" in a local daemon (needs the computer awake).
- Cost: only a concurrent-sandbox quota in the cloud product.
- Supports 30+ agent CLIs.

### Ralph Orchestrator (mikeyobrien/ralph-orchestrator)
Sources: README (opened), DeepWiki. Files named: `crates/ralph-core/src/event_loop/mod.rs`, `crates/ralph-telegram/src/service.rs`, `crates/ralph-cli/src/loops.rs`, `crates/ralph-adapters/.../pty_executor.rs`.
- Task source: a prompt or a spec folder `.ralph/specs/<name>/` (requirements, design, implementation-plan) made by `ralph plan`. Loops until the agent prints `LOOP_COMPLETE`.
- Isolation: first loop in the main tree (lock file `.ralph/loop.lock`), later loops each in `.worktrees/<loop-id>/`; optional auto-merge queue. No sandbox (PTY wrapper only).
- Human in the loop: Telegram "RObot". Agent emits `human.interact`, loop blocks until reply or timeout. You can also send guidance anytime. Replies route by reply-to or `@loop-id`. Commands `/status /tasks /restart`.
- Verification: "backpressure" gates in `ralph.yml` (tests, lint, typecheck) that reject work. Not mutation checks.
- Limits: `max_iterations`, `max_runtime_seconds`. Memories and tasks persist between iterations.
- Closest in spirit to ours on the phone side.

### claude-code-action (anthropics/claude-code-action)
Sources: README (opened), DeepWiki. Files named: `docs/security.md`, `docs/faq.md`, `docs/configuration.md`, `src/github/utils/sanitizer.ts`, `src/github/operations/restore-config.ts`, `agent-approval-check/`.
- Task source: `@claude` comments, issue assignment, or a fixed `prompt` (automation mode, can be cron). Runs on your GitHub runner.
- Isolation: the CI runner itself; write-access check on the triggering user; strips env secrets and uses bubblewrap PID namespace only in the risky `allowed_non_write_users` mode.
- Defence worth noting: restores `.claude/` and `.mcp.json` from the base branch so a PR cannot plant hooks (`restore-config.ts`); sanitizes issue text against prompt injection (`sanitizer.ts`). This is the same worry as our protected-file guard.
- Human in the loop: one progress comment with checkboxes; `agent-approval-check` sub-action requires an APPROVED review or `/approve <sha>` before agent commits count. No phone channel.
- Limits: `--max-turns` via `claude_args`.
- PRs: pushes a branch and posts a link; does not open the PR itself.

### container-use (dagger/container-use)
Sources: README (opened), DeepWiki. Files named: `repository/git.go`, `repository/flock.go`, `environment/README.md`.
- An MCP server that gives each agent a Dagger container plus a git worktree on branch `env-<id>`; state in git notes; every command auto-committed; you inspect with `git checkout` or drop into the agent's terminal.
- Strongest isolation of the set (real container, not just a directory). No task queue, no notifications, no verification, no PR flow, no unattended scheduling.
- It is a layer, not a runner. Could sit under our runner in place of bubblewrap, but it needs Docker and Dagger.

### Emdash (generalaction/emdash)
Sources: README (opened), DeepWiki. Files named: `packages/core/src/runtimes/workspace-registry/node/runtime.ts`, `packages/core/src/runtimes/automations/...`.
- Desktop app. Worktree per task. Pulls tickets from Linear, GitHub, Jira, GitLab, Asana, Monday, Forgejo, YouTrack. Cron-style automations. Remote machines over SSH.
- Installs lifecycle hooks into each agent's user config to learn status, notifications and resumable sessions (marker-tagged entries that do nothing outside Emdash). This is the same trick as our hooks and systemd bridge, done more broadly and cleanly.
- Review, PR, CI checks, merge all in one UI. Optional background push step with a "branch not pushed, retry" state.
- No sandbox beyond the worktree; no mutation-style verification; no phone chat.

### GitHub Copilot coding agent (docs.github.com, about-coding-agent page, fetched)
- Task source: issue, chat, agents panel, security alerts, plus scheduled or event automations.
- Runs in an ephemeral cloud dev environment; one branch and one PR per task; only the repo named in the task.
- Hard cap 59 minutes per session; `timeout-minutes` can shorten it.
- Runs tests and linters; Copilot code review is separate. Page did not cover firewall or notifications.

## 3. Briefly checked (not audited)

- claude-squad: tmux plus worktrees TUI; `--autoyes` flag auto-accepts prompts; `s` pushes the branch, `c` checkout (README). Interactive tool, no queue, no phone, AGPL.
- Backlog.md: markdown task files with acceptance criteria and a Kanban; three human review points (spec, plan, code). A task manager, it does not run agents (README).
- Task Master: task list with dependencies, `next` picks by dependency then priority then id; optional orchestrator/executor/checker subagents in Claude Code (DeepWiki).
- Ruflo: swarm/MCP framework with 300+ tools, memory, policy gates, signed audit chain. Large surface, mostly aimed at agent coordination, not unattended repo-by-repo delivery (DeepWiki). Hype level high; I did not verify its claims.
- Codex cloud (learn.chatgpt.com/docs/cloud, fetched): tasks keep running while your computer sleeps, per-environment network allowlist, many parallel tasks, you review and open a PR. Notifications and limits not covered on the page.
- OpenHands: event or cron "automations" in an isolated sandbox, PR creation prompts, a verification harness that forbids agents editing human test notes in PRs, Slack or email digest fields (DeepWiki; it said the resolver itself was not clearly covered, so weak evidence).
- Vibe Kanban: README header says it is sunsetting. Do not build on it.
- SWE-agent, Aider: single-task agents, not schedulers.

## 4. Comparison table

Legend: Y yes, P partial, N no, ? not found in what I read.

| Project | Stars | Last push | License | Task source | Isolation | Parallel | Ask human / phone | Verify | Git/PR | Unattended | Cost caps |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ours (wf) | private | n/a | n/a | markdown plan with checkboxes, slash command per box; issues mode (spec 0024) | bubblewrap, net limits, write-deny, protected-file guard | repos (process each) and features (worktrees) | park, keep going, Telegram buttons or ntfy, resume on answer | steps must prove they can fail; mutation checks | branch per spec, 1 commit, optional draft PR after name and attribution scan | morning report, usage-limit waits, systemd, autonomous mode | per-call budgets and caps |
| Orchestrator.inc | 13.2k | 2026-10-14 | Apache-2.0 | typed tasks, orchestrator agent, GitHub/GitLab issues | worktree (Docker only in cloud) | Y, Kanban | desktop and paired-phone push; waiting_input | CI/review state fed back | worker opens PR | local daemon automations | cloud sandbox quota only |
| Ralph Orchestrator | 3.2k | 2026-10-13 | MIT | prompt or spec folder | worktree per extra loop | Y | Telegram, blocking question, free guidance | backpressure gates | auto-merge queue | loop until done | iterations, runtime |
| claude-code-action | 9.5k | 2026-10-14 | MIT | @claude, issue, prompt, cron | CI runner; bwrap in risky mode | per workflow run | PR comments, approval check | agent-approval-check | branch plus link | Y (CI) | max-turns |
| container-use | 4.1k | 2026-09-21 | Apache-2.0 | whatever the agent is given | container plus worktree | Y | N | N | env branch, manual merge | N | N |
| Emdash | 6.0k | 2026-10-14 | Apache-2.0 | 10+ trackers | worktree, SSH remotes | Y | in-app via hooks | CI view | push, PR, merge UI | cron automations | ? |
| Copilot coding agent | hosted | n/a | proprietary | issue, chat, alerts, schedule | cloud env | Y | PR review | tests, linters | 1 PR per task | Y | 59 min cap |
| Codex cloud | hosted | n/a | proprietary | web, mobile, CLI, Slack | per-task cloud workspace, net allowlist | Y | follow-ups | you review | PR on request | runs while asleep | ? |
| claude-squad | 8.6k | 2026-08-20 | AGPL-3.0 | you type | tmux plus worktree | Y | N | N | push key | autoyes only | N |
| Backlog.md | 7.0k | 2026-10-14 | MIT | task files | none | N | 3 review points | acceptance criteria | n/a | N | N |
| Task Master | 28.2k | 2026-04-28 | NOASSERTION | tasks.json | none | via subagents | N | task-checker agent | commits in autopilot | partial | N |
| OpenHands | 90.9k | 2026-10-14 | MIT | cron, events | sandbox runtime | Y | Slack/email digest | verify harness | PR | Y | ? |
| Ruflo | 74.7k | 2026-10-14 | MIT | CLI, MCP | policy gates | swarms | CLI, MCP | signed audit | ? | ? | gates |

## 5. What they do better than ours (worth borrowing)

1. A live board or status view. Orchestrator.inc and Emdash derive "needs you / in review / ready to merge" from PR, CI and review state. We have a morning report and queue text but no always-on view. Cheap borrow: a `wf status` table with the same four buckets read from existing run files.
2. CI and review feedback goes back into the same agent. Orchestrator.inc sends failed CI and review comments to the worker that owns the PR. Our fix loop for bot review comments is manual (`rules/review-fix.md`). Borrow: after the draft PR exists, poll CI and reviews, and queue a fix step.
3. Free-form guidance mid-run. Ralph lets you message a running loop and routes by reply-to or `@loop-id`. Ours only answers parked questions. Borrow: a Telegram message that appends a note to a feature's next step brief.
4. Prompt-injection and planted-config defence. claude-code-action restores `.claude/` and `.mcp.json` from the base branch and sanitizes issue text. We guard protected files, but I saw no input sanitizer for issue-sourced tasks (spec 0024 mode). Borrow: strip HTML comments and invisible characters from issue bodies before they enter a prompt.
5. Required human approval as a status check. `agent-approval-check` makes agent commits need an APPROVED review or `/approve <sha>`. Ours stops at draft PR, which is similar, but a branch-protection check would make it enforceable by the server.
6. Many ticket sources. Emdash reads Linear, Jira, and more. Ours reads markdown and GitHub issues. Only worth it if you use another tracker.
7. Container-grade isolation as an option. container-use gives a real container per agent. Bubblewrap is lighter; keep ours, but note container-use as the upgrade if bubblewrap proves too weak.
8. Hard wall-clock cap. Copilot's 59-minute cap and Ralph's `max_runtime_seconds` are simple. Confirm ours has a per-call wall clock as well as budgets (I did not re-verify in code).

## 6. What ours does that none of them do

Checked against the READMEs and DeepWiki answers above. "None" means none of the projects I read; I cannot rule out private tools.

- Plan file of checkboxes where each box names a slash command, run in order headlessly. Closest: Ralph spec folders, Backlog.md task files (but those do not run).
- Verify and test steps must prove they can fail (`CAN FAIL CHECKED`, `MUTATION CHECKED` lines, runs park `unchecked` without them). Others use gates (tests, lint) or review; none check that the check can fail.
- Park-and-continue: a feature that needs a decision is parked, other features keep building, resume when answered, with context and links in the question. Ralph blocks the whole loop instead. Orchestrator.inc marks "needs input" but has no resume-on-answer chain.
- Telegram buttons plus ntfy as phone channels with questions carrying context. Ralph has Telegram text; Orchestrator.inc has push only.
- Real OS sandbox per unattended call (bubblewrap, network limits, write-deny) together with a protected-file change stop. claude-code-action has a narrow version; container-use has containers but nothing else.
- Outgoing scans before a draft PR push: private names and attribution scan.
- Usage-limit waits tied to the Claude subscription, and a morning report.
- Autonomous mode bound to an interactive Claude Code session through hooks and a systemd user unit.
- Slash-command skills as the unit of work (`/develop`, `/check verify`, `/test`, `/sync`). This is tied to your own skill set and is the main reason a drop-in swap is hard.

## 7. Verdict

Partly reinventing, mostly not. The commodity layer is already solved by others: worktree per task, a board, a PR button, a cron trigger, even a Telegram question (Ralph). If you only needed "run several agents in worktrees and watch them", adopting Orchestrator.inc, Emdash or Ralph would beat maintaining 11,700 lines.

But none of them reads your markdown plan, runs your slash-command chain, enforces mutation-checked verification, parks and resumes decisions per feature, or jails each unattended call. Those are the parts you actually rely on, and replacing the runner would mean rebuilding them on top of someone else's loop. Two of the closest candidates are risky bets: Vibe Kanban is shutting down; Orchestrator.inc and Emdash are desktop apps built around a UI and interactive sessions (Orchestrator.inc's automations need the computer awake).

Recommendation:
- Do not replace. Keep `wf`.
- Do not adopt a whole project. Borrow ideas (section 5), in this order: status board, CI/review feedback loop into the PR, issue-text sanitizer, mid-run guidance messages, wall-clock cap check.
- Look again at Ralph Orchestrator if you want a lower-maintenance backend for the "loop until done" part. It is Rust, MIT, active, has worktrees, Telegram and backpressure. Study `crates/ralph-telegram/src/service.rs` and `loops.rs` before deciding. I would only borrow ideas, not switch.
- Consider container-use only if bubblewrap is ever bypassed in practice.
- Size concern: `run.py` is 5,439 lines. The landscape says a runner of this scope is normally a product team's job; the cost of keeping your own is maintenance, not feasibility.

## 8. Caveats

- DeepWiki answers are model summaries; claims such as "no Telegram in Orchestrator.inc" come from one answer and should be confirmed in its docs before you rely on them.
- Conductor (closed source), Crystal (stale), ccmanager, parallel-code, uzi and Sweep were not audited.
- I skimmed our runner file sizes and spec list, not every spec; the "ours" row relies on the description you gave plus those.
- Star counts reflect 2026-10-14 and include some hype-driven projects (Ruflo). Stars are not quality.
