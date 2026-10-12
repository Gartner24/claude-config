# Scope: claude-config

Your Claude Code setup, published. The current build is the autonomous workflow runner: it starts each next step of a repo's scope for you, then later runs whole features unattended and pings your phone only for a real decision.

**Build approach:** Skateboard (each stage is usable on its own, and each next stage grows the same tool).
**Workflow:** Beta (after `/develop`: `/check verify`, then `/test`). It runs unattended on your machine, so it gets tests. `/architect` is the recommended first stop for a feature with a real decision, but skippable when you already know the build. Any feature can carry its own tag (e.g. `· GA`) to do more or less.
**Source of truth:** scope
**Autopilot:** off

_These are recommendations to keep your build orderly, not requirements. Skip anything that does not fit: if you already know how to build a feature, use `/develop` and skip `/architect`. You decide when a feature is `done`._

Source: personal scope item 8 (`~/projects/docs/scope/scope.md`). Settled requirements: section 0 of `~/Documents/workflow-research/09-autonomous-runner-research.md`; read it before any `/architect` here.

## At a glance

| # | Feature | Phase | Status |
|---|---------|-------|--------|
| A | Sync and install | Existing | existing |
| B | Design pipeline and gate | Existing | existing |
| C | Review stack | Existing | existing |
| D | Skill routing | Existing | existing |
| 1 | Runner stack and layout | Foundation | done |
| 2 | Scope contract for the runner | Foundation | done |
| 3 | `next <repo>` | Release 1 | done |
| 17 | Worktree discovery without git | Release 1 | done |
| 18 | fzf failure is not a cancel | Release 1 | done |
| 19 | Singular change count | Release 1 | done |
| 4 | Headless step loop | Release 2 | done |
| 5 | Decision parking and phone pings | Release 2 | in-progress |
| 6 | Standing answers | Release 2 | planned |
| 7 | Headless verify and test | Release 2 | planned |
| 8 | Failure and park policy | Release 2 | planned |
| 9 | Design enforcement unattended | Release 2 | planned |
| 10 | Build queue and decision queue | Release 3 | planned |
| 15 | Cheap worker tier | Release 3 | planned |
| 16 | Issues and mixed source of truth | Release 3 | planned |
| 11 | Autopilot offer and batch design | Release 4 | planned |
| 12 | Usage limit planning | Release 4 | planned |
| 13 | Morning report | Release 4 | planned |
| 14 | Draft PR per spec | Release 4 | planned |

## Existing

### A. Sync and install · existing
`sync.sh` pulls live `~/.claude` into the repo, `install.sh` puts it back with self checks. code in `sync.sh`, `install.sh`

### B. Design pipeline and gate · existing
Run ledger, Stop hook, font and colour scripts behind `design`, `brand-system`, `design-gate`. code in `skills/design/`, `skills/design-gate/`

### C. Review stack · existing
Multi agent pre ship review with a blind lane and a pre push receipt hook. code in `skills/review-stack/`, `hooks/review-stack-pre-push`

### D. Skill routing · existing
`USAGE.md` routing table, the intent router, and its regression check. code in `skills/intent-router/`, `scripts/check-routing.py`

## Foundations

### 1. Runner stack and layout · done
Pick the language, the entry point, how it installs onto your PATH, and how it is tested. Code lives in `~/claude-config` (decided).
**Done when:** a spec records the choice, and an empty runner installs through `install.sh` and passes its own self check.
- [x] Design it (spec): `/architect runner stack and layout`
- [x] Scaffold from the decision: `/develop runner stack and layout`
Spec [0001](../specs/0001-runner-stack-and-layout.md) · code in `runner/`

### 2. Scope contract for the runner · done
The fields the runner reads: the hub `Repos` column (replaces `**Repo:**`), `**Source of truth:**`, `**Autopilot:**`, the `auto` tag, and how the next box is found (first unticked box, `docs/` or `.workflow/` base, milestone sub items). The skills that write the scope have to agree with it.
**Done when:** a spec defines the fields and the next box rule, and `/scope` and `/architect` write them.
- [x] Design it (spec): `/architect scope contract for the runner`
- [x] Build it: `/develop scope contract for the runner`
   - [x] Rule file `scope-contract.md`, synced, in `NOTICE.md` (AC-4 to AC-9)
   - [x] Header check in `wf.py` with warnings on every path, fixtures and tests (AC-1, AC-2, AC-3, AC-5, AC-7)
   - [x] Manual `/scope` replan, headless `/scope`, `/architect` queue check (AC-10); replan, headless and the `· auto` write pass; the no tag half passed at the feature 17 capture (2026-10-11)
- [x] Verify it: `/check verify scope contract for the runner`
- [x] Test it: `/test scope contract for the runner`
Spec [0003](../specs/0003-scope-contract/index.md) · code in `rules/scope-contract.md`, `runner/wf.py`, `runner/tests/`

## Release 1: next step in one command

### 3. `next <repo>` · done
From any folder, name a repo (a path, its folder name or its scope title, found by scanning your project folders); it reads the first unticked box, goes into that repo, and opens an interactive session already running that command. Removes the `/clear`, the retyping, and the wrong folder.
**Done when:** `next dotfiles` from `~/.claude` opens a session in `~/dotfiles` running its next box, and a repo with nothing left says so instead of starting a session.
- [x] Design it (spec): `/architect next repo command`
- [x] Build it: `/develop next repo command`
   - [x] `wf next` and the `next` shortcut on the row 1 scaffold, missing tool checks (AC-13, AC-14)
   - [x] Discovery, path argument and name matching (AC-1, AC-3, AC-11)
   - [x] Box parser: tags, milestones, hubs, epics (AC-5, AC-6, AC-7)
   - [x] Confirm line and exec launch, session warning (AC-8, AC-9, AC-10, AC-16)
   - [x] fzf picker, worktrees, `--list`, manual real claude check (AC-2, AC-4, AC-12, AC-15)
- [x] Verify it: `/check verify next repo command`
- [x] Test it: `/test next repo command`
Spec [0002](../specs/0002-next-repo-command/index.md) · code in `runner/wf.py`, `runner/tests/`

### 17. Worktree discovery without git · done
Discovery still runs `git worktree list --porcelain` in every scanned main checkout. Decide whether to read `.git/worktrees/*/gitdir` instead, so no git runs in a repo that is only scanned (the rule since `c26dc8a`). Changing it rewords spec 0002 AC-2 and its worktree label row.
**Done when:** spec 0002 records the decision, and if it changes, worktrees are still found and labelled with no git call in scanned repos.
- [x] Design it (spec): `/architect worktree discovery without git`
- [x] Build it: `/develop worktree discovery without git`
   - [x] File reads of `gitdir`, `commondir` and `HEAD` replace `worktrees()` and `worktree_label()`, one shared `.git` file resolver (AC-2, build step 6)
   - [x] "Worktree without git" test: zero git calls, relative, prunable, reused, empty and placeholder cases, no git on PATH (AC-2)
- [x] Verify it: `/check verify worktree discovery without git`
- [x] Test it: `/test worktree discovery without git`
Spec [0002](../specs/0002-next-repo-command/index.md) (amended AC-2) · code in `runner/wf.py`, `runner/tests/`

### 18. fzf failure is not a cancel · done
When fzf cannot open a terminal it prints `inappropriate ioctl for device` and `next` exits 0, the same as a cancelled pick (AC-4). Spec 0002 now names it: a failure exits 1 with a message. Same amendment: an empty or unknown `HEAD` shows `-` in the list branch column, not `detached ` (AC-12).
**Done when:** a picker that fails to start prints why and exits with the code the spec names, and a real cancel still exits 0.
- [x] Design it (spec): `/architect fzf failure is not a cancel`
- [x] Build it: `/develop fzf failure is not a cancel`
   - [x] `pick()` tells a cancel (130, 1) from a failure (exit 1 and message), tests for `next` and `wf run` (AC-4, build step 7)
   - [x] Shared hash pattern, `head_branch()` shows `-` for an empty or unknown `HEAD`, list tests (AC-12, build step 7)
- [x] Verify it: `/check verify fzf failure is not a cancel`
- [x] Test it: `/test fzf failure is not a cancel`
Spec [0002](../specs/0002-next-repo-command/index.md) (amended AC-4, AC-12) · code in `runner/wf.py`, `runner/tests/test_wf.py`, `runner/tests/test_run.py`

### 19. Singular change count · done
The confirm line reads `1 changes` for one change. It should read `1 change`; spec 0002 AC-8 writes `N changes`, so its wording gets the singular too.
**Done when:** one uncommitted file shows `1 change`, others still show `N changes`, with a test for each.
- [x] Design it (spec): `/architect singular change count`
- [x] Build it: `/develop singular change count`
   - [x] `changes()` returns `1 change` for one, `N changes` otherwise, test for 0, 1 and 2 (AC-8, build step 8)
- [x] Verify it: `/check verify singular change count`
- [x] Test it: `/test singular change count`
Spec [0002](../specs/0002-next-repo-command/index.md) (amended AC-8) · code in `runner/wf.py`, `runner/tests/test_wf.py`

## Release 2: one feature unattended

### 4. Headless step loop · done · auto
Run each box as a fresh `claude -p` call inside the repo, recompute the next box from the files after each one, and stop after `/sync`. Per call budget, wall clock and run caps, a lock per repo, `nosleep` on for the run, a clean stop on SIGINT.
**Done when:** one feature runs from `/develop` to `/sync` with no typing, a second run on the same repo is refused, and the caps stop a runaway run.
- [x] Design it (spec): `/architect headless step loop`
- [x] Build it: `/develop headless step loop`
   - [x] `wf run` loop: resolve, start checks, confirm, call, classify, `/sync`, output, exit codes (AC-1 to AC-7, AC-11, AC-14)
   - [x] Lock and run record (AC-9, AC-10)
   - [x] Caps and call timeout (AC-8)
   - [x] Signals, inhibitor, branch drift, cleanup on every path (AC-12, AC-13)
   - [x] Manual real claude checks in `verify.md` (AC-15)
- [x] Verify it: `/check verify headless step loop`
- [x] Test it: `/test headless step loop`
Spec [0004](../specs/0004-headless-step-loop/index.md) · code in `runner/run.py`, `runner/wf.py`, `runner/tests/test_run.py`

### 5. Decision parking and phone pings · in-progress
The unattended prompt fixes the safe panel answers and asks real decisions as `DECISION NEEDED:` plus `OPTION:` lines; you get the question on your phone with buttons and the session resumes with your reply.
**Done when:** a safe panel never reaches you, a real decision arrives on your phone, and your reply resumes the same session.
- [x] Design it (spec): `/architect decision parking and phone pings`
- [ ] Build it: `/develop decision parking and phone pings`
   - [x] `hook.py` safe list and answer lookup, `--settings` argv, new prompt, auto answers recorded (AC-3, AC-4, AC-5, AC-12)
   - [x] `ntfy.py` and `wf ntfy init|codes|test`, `no_ntfy` start check, scrubbed JSON pings, reply rules and code burning (AC-1, AC-2, AC-7, AC-8, AC-13)
   - [x] Deferred classification, wait loop, `answers.json`, resume call, prose decisions (AC-6, AC-9, AC-10, AC-11, AC-12)
   - [x] Text path: `OPTION:` lines become a panel decision, new prompt and resume sentence, delete `hook.py`, `answers.json`, `auto.jsonl` and the deferred rule (spec 0005 build plan 6; AC-3 to AC-6, AC-10 to AC-12)
   - [ ] Manual real claude and phone checks in `verify.md` (AC-14)
- [ ] Verify it: `/check verify decision parking and phone pings`
- [ ] Test it: `/test decision parking and phone pings`
Spec [0005](../specs/0005-decision-parking-phone-pings/index.md) · code in `runner/ntfy.py`, `runner/run.py`, `runner/wf.py`, `runner/tests/`

### 6. Standing answers · needs a decision
Answers you always give the same way (tier, cross check, `/test` runs the suite, who marks done, accept the spec) live once in each repo's `AGENTS.md`, and the skills read them instead of asking.
**Done when:** a headless run gets through `/architect` accept, `/test` setup, and the done decision without a single question.
- [ ] Design it (spec): `/architect standing answers`

### 7. Headless verify and test · needs a decision
`/check verify` drives the app through the chrome-devtools MCP (isolated Brave) instead of reporting BLOCKED, and `/test` sees the feature's changes even after checkpoint commits.
**Done when:** a Beta feature passes `/check verify` and `/test` in a headless run, and only real walls (login, captcha, 2FA, hardware) report BLOCKED.
- [ ] Design it (spec): `/architect headless verify and test`

### 8. Failure and park policy · needs a decision
What parks a feature instead of looping: 2 `/debug` attempts after a FAIL, BLOCKED, sudo, logins, hook denials (logged with the reason), and paid steps that never run unattended. Also refuses a repo whose `**Autopilot:** allowed` you did not set yourself, such as a cloned third party scope (spec 0003 follow up).
**Done when:** each of those cases parks the feature with a reason you can read, and no paid step runs.
- [ ] Design it (spec): `/architect failure and park policy`

### 9. Design enforcement unattended · needs a decision
Frontend work in a headless run goes through `design` and `design-gate`, never skipped: the Stop hook runs headless, and the runner fails a step that changed frontend files without a newer gate report.
**Done when:** a headless UI step with no fresh `design-gate` report fails, and one with a passing report goes through.
- [ ] Design it (spec): `/architect design enforcement unattended`

## Release 3: queues

### 10. Build queue and decision queue · needs a decision
A parked feature no longer stops the run: the runner moves to the next queued feature or repo. The queue is the scope files themselves (accepted spec, unticked build boxes, `auto` tag), one feature at a time per repo.
**Done when:** with two queued features where the first parks, the second still builds, and the parked question waits for you.
- [ ] Design it (spec): `/architect build queue and decision queue`

### 15. Cheap worker tier · needs a decision
Low value work (summaries of long pages, transcripts and logs, first pass triage of search results, field extraction, classification, commit message drafts) goes to claude-fb's free models through an `fb-ask` helper, and the answer comes back to the Claude session as data. Never code edits, decisions, security review, or client code on fb-any.
**Done when:** a runner step sends a summary job through `fb-ask`, Claude uses the answer, and a code or decision task can never be routed there.
- [ ] Design it (spec): `/architect cheap worker tier`

### 16. Issues and mixed source of truth · needs a decision
Per repo `**Source of truth:** scope | issues | mixed`. With issues or mixed, the runner rereads the linked GitHub issue before every step; if it changed after the spec was written, the feature parks and you are asked. In mixed, the issue holds the requirement and the scope tracks the build, and the issue wins on conflict. Never tied to an org or repo name.
**Done when:** an issue edited after its spec parks the feature with the diff shown, and a repo set to scope never calls GitHub.
- [ ] Design it (spec): `/architect issues and mixed source of truth`

## Release 4: overnight autopilot

### 11. Autopilot offer and batch design · needs a decision
When a conversation ends with buildable features, one question: "Queue these for autopilot?". Then `/architect` runs for each one back to back, one question round per spec, until every spec is accepted and tagged `auto`.
**Done when:** answering yes leaves every queued feature with an accepted spec and the `auto` tag, with all questions asked before the unattended run starts.
- [ ] Design it (spec): `/architect autopilot offer and batch design`

### 12. Usage limit planning · needs a decision
Estimate each step's usage from past sessions, compare it with the 5 hour window and the weekly limit, start right after a reset, sleep through a reset, and refuse a run the week cannot finish.
**Done when:** a run that does not fit is refused before it starts, and one that hits the 5 hour limit pauses and resumes after the reset.
- [ ] Design it (spec): `/architect usage limit planning`

### 13. Morning report · needs a decision
What ran, what parked and why, what it cost: a short note on your phone, and the full report shown when your main session starts.
**Done when:** after a run you get the phone note, and your next `~/.claude` session opens with the report.
- [ ] Design it (spec): `/architect morning report`

### 14. Draft PR per spec · needs a decision
Checkpoint commits on a work branch squash into one clean commit per feature, and the runner opens one draft PR per spec, never marked ready or merged. Waits on the branch and PR standard (personal scope item 11).
**Done when:** a finished feature ends as one commit on its branch with a draft PR, and the runner has no path to merge or mark ready.
- [ ] Design it (spec): `/architect draft PR per spec`

## Deferred
Out of scope for the current build pass, kept so the plan stays honest.
- none for now

## Legend

**The decision box.** Every feature carries exactly one, the sub task whose label ends with `(spec)`. Skills locate it by that `(spec)` suffix, never by an exact label. Every other box is an execution box and `/architect` never ticks one.

- **Next step** = the first unticked box (always a command or a tracked milestone).
- **needs a decision** = run `/architect` first; otherwise straight to `/develop`. The tag drops once the spec is captured.
- **Atomic build tasks live in the spec's `## Build plan`, not here**: the scope carries only the milestone rollup.
- **Status** `planned` -> `in-progress` -> `done`, plus `existing` (pre workflow) and `dropped` (de scoped, kept for history).
- **Workflow tier tag** beside a heading (e.g. `· GA`) sets that one feature's rigor; no tag inherits the Beta default.
- **Workflow** Beta = `/check verify`, then `/test` after `/develop`. A feature built on an unratified decision (an `Assumed` spec) stays flagged, but that never blocks `done`.
- **Pointer line** (`spec <n> · code in <path>`): the spec link added by `/architect`, the code path by `/develop`.
