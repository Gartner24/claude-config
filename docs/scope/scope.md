# Scope: claude-config

Your Claude Code setup, published. The current build is the autonomous workflow runner: it starts each next step of a repo's scope for you, then later runs whole features unattended and pings your phone only for a real decision.

**Build approach:** Skateboard (each stage is usable on its own, and each next stage grows the same tool).
**Workflow:** Beta (after `/develop`: `/check verify`, then `/test`). It runs unattended on your machine, so it gets tests. `/architect` is the recommended first stop for a feature with a real decision, but skippable when you already know the build. Any feature can carry its own tag (e.g. `· GA`) to do more or less.
**Source of truth:** scope
**Autopilot:** allowed

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
| 5 | Decision parking and phone pings | Release 2 | done |
| 6 | Standing answers | Release 2 | done |
| 22 | Waiting boxes owed to you | Release 2 | done |
| 20 | Push guard outside the model | Release 2 | done |
| 8 | Failure and park policy | Release 2 | done |
| 7 | Headless verify and test | Release 2 | done |
| 9 | Design enforcement unattended | Release 2 | done |
| 10 | Build queue and decision queue | Release 3 | done |
| 26 | Review stack fixes | Release 3 | done |
| 27 | Second review stack fixes | Release 3 | done |
| 21 | Work names out of the public repo | Release 3 | done |
| 24 | Runner resilience | Release 4 | in-progress |
| 25 | Checks that cannot lie | Release 4 | in-progress |
| 28 | Guard hook false alarms | Release 4 | done |
| 29 | Several repos at once | Release 4 | in-progress |
| 30 | Live setup steps in one command | Release 5 | in-progress |
| 13 | Morning report | Release 5 | in-progress |
| 31 | Guard baseline check before each repo | Deferred | planned |
| 23 | Questions that teach | Deferred | planned |
| 15 | Cheap worker tier | Deferred | planned |
| 16 | Issues and mixed source of truth | Deferred | planned |
| 11 | Autopilot offer and batch design | Deferred | planned |
| 12 | Usage limit planning | Deferred | planned |
| 14 | Draft PR per spec | Deferred | planned |

Build order follows the table: 6, 22, 20, 8, 7, 9, 10. The goal and the rules every feature keeps are in [docs/architecture.md](../architecture.md).

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

### 5. Decision parking and phone pings · done
The unattended prompt fixes the safe panel answers and asks real decisions as `DECISION NEEDED:` plus `OPTION:` lines; you get the question on your phone with buttons and the session resumes with your reply.
**Done when:** a safe panel never reaches you, a real decision arrives on your phone, and your reply resumes the same session.
- [x] Design it (spec): `/architect decision parking and phone pings`
- [x] Build it: `/develop decision parking and phone pings`
   - [x] `hook.py` safe list and answer lookup, `--settings` argv, new prompt, auto answers recorded (AC-3, AC-4, AC-5, AC-12)
   - [x] `ntfy.py` and `wf ntfy init|codes|test`, `no_ntfy` start check, scrubbed JSON pings, reply rules and code burning (AC-1, AC-2, AC-7, AC-8, AC-13)
   - [x] Deferred classification, wait loop, `answers.json`, resume call, prose decisions (AC-6, AC-9, AC-10, AC-11, AC-12)
   - [x] Text path: `OPTION:` lines become a panel decision, new prompt and resume sentence, delete `hook.py`, `answers.json`, `auto.jsonl` and the deferred rule (spec 0005 build plan 6; AC-3 to AC-6, AC-10 to AC-12)
   - [x] Manual checks in `verify.md` (AC-14): all six on claude -p 2.1.296 and the phone; label cuts and browser replies fixed from check 5
- [x] Verify it: `/check verify decision parking and phone pings`
- [x] Test it: `/test decision parking and phone pings`
Spec [0005](../specs/0005-decision-parking-phone-pings/index.md) · code in `runner/ntfy.py`, `runner/run.py`, `runner/wf.py`, `runner/tests/`

### 6. Standing answers · done
Answers you always give the same way (`/test` runs the suite, who marks done) live once in each repo's `AGENTS.md` (`.workflow/AGENTS.md` in team repos), and `wf run` adds them to the unattended prompt instead of pinging you. Tier stays on the scope header, accepting a spec stays with you. The cross check key was dropped on 2026-10-12 (spec 0006 amended).
**Done when:** a headless `wf run` gets through `/test`'s run suite question and the done decision without a single question.
- [x] Design it (spec): `/architect standing answers`
- [x] Build it: `/develop standing answers`
   - [x] Read and check the section, refusals, defaults (AC-1 to AC-4)
   - [x] Prompt per call, last box check, fake claude `write_file` (AC-4 to AC-6, AC-8)
   - [x] Confirm line, `run.json` `answers` and `last_box` (AC-7)
   - [x] Manual checks on the real claude (AC-9): verify.md UI steps 1 and 2, both passed 2026-10-12 through a real `wf run` on scratch repos
- [x] Verify it: `/check verify standing answers`
- [x] Test it: `/test standing answers`
Spec [0006](../specs/0006-standing-answers/index.md) · code in `runner/run.py`, `runner/tests/test_run.py`

### 22. Waiting boxes owed to you · done
A box only you can close (a manual check on the real claude or your phone, like spec 0006 AC-9) gets a marker in the scope contract (spec 0003), and `next` and `wf run` treat it as waiting: refused with a reason, never built. The last `wf run` looped `/develop` on feature 6 because its open AC-9 milestone was owed to you.
**Done when:** `wf run` on a feature whose next box carries the marker refuses with a waiting reason and makes no call, `next` says the box waits on you, and `/scope` and `/architect` know how to write the marker.
- [x] Design it (spec): `/architect waiting boxes owed to you`
- [x] Build it: `/develop waiting boxes owed to you`
   - [x] Marker, `NextBox.owed` and the near miss warning (AC-1, AC-2)
   - [x] `wf run` refuses or parks a marked box, ahead of every other box check (AC-5)
   - [x] `next` never launches a marked box (AC-3, AC-6)
   - [x] Rule file line live (AC-7; architecture sentence and the repo copy are in): `cp ~/claude-config/rules/scope-contract.md ~/.claude/rules/scope-contract.md` · waits on you
   - [x] Headless `/scope` probe (AC-8; the `wf run` refusal passed, see spec 0012 `verify.md`) · waits on you
- [x] Verify it: `/check verify waiting boxes owed to you`
- [x] Test it: `/test waiting boxes owed to you`
Spec [0012](../specs/0012-waiting-boxes-owed-to-you/index.md) · code in `runner/wf.py`, `runner/run.py`, `runner/tests/`, `rules/scope-contract.md`
Source: your message of 2026-10-12, after the feature 6 `wf run` loop.

### 20. Push guard outside the model · done
A guard outside anything the model controls keeps every `wf run` call from pushing, opening or merging a PR, or starting a cloud agent: no credential in the call, the Bash sandbox blocks GitHub and the repo's remotes, and settings, hooks and git config cannot change mid run. The `--disallowedTools` deny list only matches prefixes, so `env git push`, `gh api` and other spellings still get through (review 2026-10-12). The pre-push hook and lock in the first wording were dropped at design: `--no-verify` and `gh api` skip a hook (spec 0007).
**Done when:** during a `wf run`, any push, PR or merge attempt from inside a call fails whatever its spelling or tool, and nothing changes for your pushes outside a run.
- [x] Design it (spec): `/architect push guard outside the model`
- [x] Build it: `/develop push guard outside the model`
   - [x] Probe gate with a hand built argv (AC-10)
   - [x] No credentials in a call, absolute `git`, `claude`, `python3` (AC-1, AC-6)
   - [x] Sandbox settings, hosts, MCP, tool denies, remote agent hook (AC-2 to AC-5b)
   - [x] Guarded files, `no_sandbox` start checks, `run.json` `guard` (AC-7 to AC-9, AC-11)
   - [x] Probes again through `wf run` (AC-10): run `python3 docs/specs/0007-push-guard/probes/run-wf-probe.py`, record in `verify.md`
   - [x] Worktree pointer files, `config.worktree`, include targets hashed and denied (AC-5, AC-7, amendment of 2026-10-12)
- [x] Verify it: `/check verify push guard outside the model`
- [x] Test it: `/test push guard outside the model`
Spec [0007](../specs/0007-push-guard/index.md)
Source: your message of 2026-10-12, after the `/review` of the runner branch ([report](../reviews/review-2026-10-12.md), Guardrails).

### 8. Failure and park policy · done
What parks a feature instead of looping: 2 `/debug` attempts after a FAIL, BLOCKED, sudo, logins, hook denials (logged with the reason), and paid steps that never run unattended. A usage limit error pauses the run until the limit resets, then resumes, instead of ending the night (moved here from feature 12 on 2026-10-12). Also refuses a repo whose `**Autopilot:** allowed` you did not set yourself, such as a cloned third party scope (spec 0003 follow up).
**Done when:** each of those cases parks the feature with a reason you can read, no paid step runs, and a run that hits the usage limit picks up again after the reset.
- [x] Design it (spec): `/architect failure and park policy`
- [x] Build it: `/develop failure and park policy`
   - [x] Trust list `wf allow`, call kinds, park vs stop, `spawn_failed` (AC-1, AC-9, AC-10)
   - [x] Call error retry, `BLOCKED:` marker, denials with reasons (AC-4 to AC-6)
   - [x] Verify FAIL loop and debug guard (AC-2, AC-3)
   - [x] Paid key strip on the spec 0007 lists, usage limit wait (AC-7, AC-8); needs feature 20 built
   - [x] Manual checks 4 to 6 in `verify.md` (AC-11): all passed 2026-10-12 through real `wf run`s on scratch repos
- [x] Verify it: `/check verify failure and park policy`
- [x] Test it: `/test failure and park policy`
Spec [0008](../specs/0008-failure-park-policy/index.md) · code in `runner/run.py`, `runner/tests/test_park.py`
Follow-up: the usage limit probe (spec 0008 `verify.md` Follow-up, check 3) waits on you at the next real limit; it does not hold this feature open.

### 7. Headless verify and test · done
`/check verify` drives the app through the chrome-devtools MCP (isolated Brave) instead of reporting BLOCKED, and `/test` sees the feature's changes even after checkpoint commits.
**Done when:** a Beta feature passes `/check verify` and `/test` in a headless run, and only real walls (login, captcha, 2FA, hardware) report BLOCKED.
- [x] Design it (spec): `/architect headless verify and test`
- [x] Build it: `/develop headless verify and test`
   - [x] Probe gate P2 to P7 first; any failure stops the build and goes back to `/architect` (AC-11)
   - [x] `/test` base from the merge base with `main` (AC-9, AC-10)
   - [x] App keys, `no_browser` start checks, app jail lifecycle, `app_failed` and `app_port_busy` (AC-1 to AC-3, AC-10)
   - [x] Browser calls: pinned MCP, allowed and denied tools, browser hook, prompt (AC-4 to AC-8)
   - [x] Review fixes: jail binds from the frozen deny list and the guarded file check after app stops, app env and hidden wf folders, npx from the state dir, the two hook checks and the prompt wording (AC-2 to AC-5, AC-7, AC-8)
   - [x] Rerun P2 to P7, P10 and P11 against the built code; any failure goes back to `/architect` (AC-11)
   - [x] Findings 8 and 9: binds at the real path, symlink inside a write bind parks, `absent_denied` check, `file_hash()` on a directory, then rerun P2 through the built code (AC-3, AC-11)
   - [x] Findings 10 and 13: empty folder trees pass, absent guarded symlinks and unreadable files trip, 11 and 12 residual (AC-3)
   - [x] P8 and P9 through `wf run`, with P2 rerun (AC-11)
- [x] Verify it: `/check verify headless verify and test`
- [x] Test it: `/test headless verify and test`
Spec [0009](../specs/0009-headless-verify-test/index.md) · code in `runner/run.py`, `runner/tests/test_browser.py`
Unblocked 2026-10-12: P5 failed on the WebRTC switch spelling Brave ignores; spec 0009 amended (AC-4 `--webrtc-ip-handling-policy`, `MCP_CACHE`) and P2 to P7 now pass. Steps 3 to 6 built 2026-10-12 (the held patch reapplied plus the `MCP_CACHE` checks); P8 and P9 through `wf run` remain.
Blocked 2026-10-12: a security review of the build found seven doors (app jail narrower than the call deny set, app network and token, npx local package resolution, browser loopback reach, guard URL parser differential, browser downloads, guard path symlink swap); they go to `/architect` before P8 and P9. Source: [docs/briefs/0009-review-findings.md](../briefs/0009-review-findings.md)
Blocked 2026-10-12 (step 8): the review fixes are built; P3 to P7, P10 and P11 pass through the built code, but P2 fails (bwrap cannot bind over a symlinked dotfile in the frozen deny list) and the step 7 commit review found absent deny paths left writable (`.git/hooks`). Both go to `/architect` (brief findings 8 and 9).
Unblocked 2026-10-12: `/architect` settled the seven findings (fix 1, 2, 3, 5, 7; accept 4 with the prompt reworded; accept 6, P11 saw no download saved); spec 0009 amended, P10 and P11 recorded. Last hardening round on this feature.
Unblocked 2026-10-12: `/architect` settled findings 8 and 9 (bind real paths, park a symlink inside a writable folder, catch an absent denied path that appears, plus ten cross check details); spec 0009 amended, build step 9.
Blocked 2026-10-12 (step 10): step 9 is built and P2 passes through the built code, but P8 and P9 stop `guard_changed` on the first call: Claude Code makes `<repo>/.claude/.cc-writes/` in a repo with no `.claude`, which the new absent path check counts as a change. The step 9 commit review also found three doors (renaming `.git` past its read only binds, a symlink chain through the repo, a dangling symlink at an absent guarded file). All go to `/architect` (brief findings 10 to 13).

### 9. Design enforcement unattended · done
Frontend work in a headless run is audited by `design-gate`, never skipped: UI with no locked design parks `blocked`, calls cannot invoke `design` or `brand-system`, and before `/sync` the runner parks `design_gate` when a frontend file changed on the branch has no passing report newer than it. The headless Stop hook in the first wording was dropped at design: `design` never runs unattended, and the 0007 sandbox cannot write its pointer (spec 0010).
**Done when:** a headless run whose branch changed frontend files with no fresh passing `design-gate` report parks `design_gate` before `/sync`, one with a passing report goes through, and UI with no locked design parks `blocked`.
- [x] Design it (spec): `/architect design enforcement unattended`
- [x] Build it: `/develop design enforcement unattended`
   - [x] Frontend rule, changed files from the merge base, report candidates and verdict (AC-1, AC-2, AC-4)
   - [x] Rule 14a check before `/sync`, park `design_gate`, `run.json` `design` (AC-3, AC-7, AC-8)
   - [x] Prompt lines and `Skill(design)`, `Skill(brand-system)` denies (AC-5, AC-6)
   - [x] P2 to P4 through `wf run` in `verify.md` (AC-9)
- [x] Verify it: `/check verify design enforcement unattended`
- [x] Test it: `/test design enforcement unattended`
Spec [0010](../specs/0010-design-enforcement-unattended/index.md) · code in `runner/run.py`, `runner/tests/test_design.py`
Steps 1 to 3 built 2026-10-12 inside a `wf run` call. P2 to P4 passed 2026-10-12 through real `wf run` from a normal session; P3's `design` deny was confirmed by a direct probe, since under `wf run` the AC-5 prompt line stops the call from trying (`verify.md`).

## Release 3: queues

### 10. Build queue and decision queue · done
A parked feature no longer stops the run: the runner moves to the next queued feature or repo. The queue is the scope files themselves (accepted spec, unticked build boxes, `auto` tag), one feature at a time per repo.
**Done when:** with two queued features where the first parks, the second still builds, and the parked question waits for you.
- [x] Design it (spec): `/architect build queue and decision queue`
- [x] Build it: `/develop build queue and decision queue`
   - [x] Queue inside one repo, `queue.json`, park memory, tree rule, exit codes (AC-2, AC-3, AC-7, AC-8, AC-10, AC-16 to AC-19)
   - [x] Decision queue: records, polling, resume, stale, end wait (AC-7, AC-11 to AC-13, AC-15)
   - [x] Across repos: trust list, skips, locks and guard baselines, plan, repo vs run stops, re-ping (AC-1, AC-4 to AC-6, AC-9, AC-14)
   - [x] `wf queue` and `wf unpark` (AC-20, AC-21)
   - [x] Manual checks on the real claude and phone (AC-22) · waits on you
- [x] Verify it: `/check verify build queue and decision queue`
- [x] Test it: `/test build queue and decision queue`
Spec [0011](../specs/0011-build-decision-queue/index.md) · code in `runner/run.py`, `runner/wf.py`, `runner/tests/test_queue.py`
AC-22 manual checks passed 2026-10-12 through real `wf run` and phone taps (`verify.md`).

### 26. Review stack fixes · done
Every HIGH, MEDIUM and LOW finding of the `/review-stack` of `d02d329..c95f181`, plus the 3 surviving mutants, fixed with a test and a mutation check each.
**Done when:** every finding in the brief is fixed with a red-then-green test, or listed under its `## Residual` with the decision it needs, and the suite passes.
- [x] Design it (spec): `/architect review stack fixes`
- [x] Build it: `/develop review stack fixes`
   - [x] Decision loop, plan answers and guard lines, standing answers watch, stale on unqueue, per call app logs, env strip (H1 to H4, L6, L9)
   - [x] MEDIUM fixes and the 3 mutants (M1 to M13)
   - [x] LOW fixes (L1 to L13)
   - [x] Push rule probe on the real claude: `bash docs/specs/0004-headless-step-loop/probes/push-rule.sh` (M9) · waits on you
- [x] Verify it: `/check verify review stack fixes`
- [x] Test it: `/test review stack fixes`
Specs amended: [0011](../specs/0011-build-decision-queue/index.md), [0009](../specs/0009-headless-verify-test/index.md), [0008](../specs/0008-failure-park-policy/index.md) · code in `runner/run.py`, `runner/wf.py`, `runner/ntfy.py`
Source: [docs/briefs/runner-review-stack-2026-10-12.md](../briefs/runner-review-stack-2026-10-12.md)

### 27. Second review stack fixes · done
Every HIGH and MEDIUM finding of the `/review-stack` of `c95f181..d20a328`, plus L8, fixed with a test and a mutation check each; the private secret file names rewritten out of the unpushed commits.
**Done when:** every second round finding in the brief is fixed with a test that goes red without its fix, no unpushed commit names a private secret file, and the suite passes.
- [x] Build it: `/develop second review stack fixes`
   - [x] Push rule probe rerun on the real claude, steps 9 to 11: `bash docs/specs/0004-headless-step-loop/probes/push-rule.sh` · waits on you
- [x] Verify it: `/check verify second review stack fixes`
- [x] Test it: `/test second review stack fixes`
Specs amended: [0004](../specs/0004-headless-step-loop/index.md), [0006](../specs/0006-standing-answers/index.md), [0007](../specs/0007-push-guard/index.md), [0008](../specs/0008-failure-park-policy/index.md), [0009](../specs/0009-headless-verify-test/index.md), [0010](../specs/0010-design-enforcement-unattended/index.md), [0011](../specs/0011-build-decision-queue/index.md) · code in `runner/run.py`
Source: [docs/briefs/runner-review-stack-2026-10-12.md](../briefs/runner-review-stack-2026-10-12.md) (second review section)

### 21. Work names out of the public repo · done
The merge of the runner branch to main waits on this. Built by `wf run`; no `wf` step writes `.git/hooks` or `~/.claude` (those steps are yours, marked below).
Work org and tool names sit in public files on main (`CLAUDE.md`, `HOOKS.md`, `SKILLS.md`, `NOTICE.md`, `README.md`, `.gitignore`). They move to one local untracked file, and the public files refer to it instead of naming anything. Root `CLAUDE.md` is the synced copy of `~/.claude/CLAUDE.md`, so `sync.sh` and `install.sh` have to keep the split. Then you decide whether main's history is rewritten too.
**Done when:** no tracked file on the branch or main names a work org or tool, a fresh `install.sh` plus the local file gives the same behavior as today, `sync.sh` cannot put a name back, and the history decision is recorded (and carried out if the answer is rewrite).
- [x] Design it (spec): `/architect work names out of the public repo`
- [x] Build the code: `/develop work names out of the public repo`
   - [x] Checker `scripts/private-names.py` with its self checks, temp files and made up names only (AC-1, AC-3, AC-6, AC-8, AC-10, AC-12)
   - [x] `sync.sh` and `install.sh` changes, tested on temp live trees through `CLAUDE_LIVE_DIR`, never run against the real `~/.claude` or `.git/hooks` (AC-3 to AC-7)
- [x] Create `~/.claude/private/` (`names.txt`, `work.md`, `gitignore`), move the name bearing passages of `~/.claude/CLAUDE.md` into `work.md` behind the import line, then run probe P1 from `docs/specs/0013-work-names-out/verify.md` (AC-1, AC-2) · waits on you
- [x] Reword tracked files: `/develop work names out of the public repo`
   - [x] Every file `python3 scripts/private-names.py check` reports reworded per the AC-9 rule, until it exits 0 (AC-9)
- [x] Run `./sync.sh` (it writes the private settings fragments under `~/.claude/private/`), confirm it exits 0 and `check` still exits 0 (AC-3, AC-4, AC-5) · waits on you
- [x] Run `./install.sh` (fragment merge, exclude lines, `pre-commit` and `commit-msg` hook links), then the AC-11 settings compare from verify.md (AC-6, AC-7, AC-11) · waits on you
- [x] Verify it: `/check verify work names out of the public repo`
- [x] Test it: `/test work names out of the public repo`
- [x] Swap the two hook links for copies by hand, before the build below: `cp --remove-destination scripts/private-names.py .git/hooks/pre-commit`, same for `commit-msg` (spec 0013 build plan 7a) · waits on you
- [x] Copy the hooks instead of linking them: `/develop work names out of the public repo`
   - [x] `install.sh` copies and refreshes the hooks per the amended AC-7; `--test` hook fixtures copy the checker, install assertions cover the AC-7 scenario, docstring line 19 says copied, line 2 unchanged (spec 0013 build plan 7b)
- [x] Verify the hook copy: `/check verify work names out of the public repo`
- [x] Test the hook copy: `/test work names out of the public repo`
- [x] Rerun `./install.sh`: both hooks print `refreshed` or `up to date`, and neither is a symlink (spec 0013 build plan 7c, AC-7) · waits on you
- [x] Sync docs for feature 21: `/sync work names out of the public repo`
- [x] Merge `feat/autonomous-runner` into `main` locally, then rewrite history in a fresh clone per the spec 0013 migration plan phases 1 and 2, `check-history` exits 0 (AC-10) · waits on you
- [x] Delete and recreate `Gartner24/claude-config`, push `main`, `check-history` on a fresh clone of the new remote, swap folders (migration plan phases 3 to 5, AC-10) · waits on you
Spec: [0013](../specs/0013-work-names-out/index.md) · code in `scripts/private-names.py`, `sync.sh`, `install.sh`
Source: [docs/briefs/work-names-out.md](../briefs/work-names-out.md) (decisions); your message of 2026-10-12 (`/scope` request after the runner branch review); your `/architect` amendment of AC-7, 2026-10-12 (hooks copied, not linked, after a `wf run` stopped `guard_changed` on `.git/hooks/commit-msg`).

## Release 4: resilience and checks

Queued in the batch planning session of 2026-10-12 (personal scope row 24). One bare `wf run` builds them in file order. A box that waits on you sets aside only its feature. Until feature 24 is built, a `/sync` box parks `manual_box`, so a feature that reaches its `/sync` box before then waits for the next run.

### 28. Guard hook false alarms · done
`block-destructive.sh` blocked a `git commit` on 2026-10-11 because its message named a deletion command, and again on a scope edit. Inside a quoted string or heredoc that is plain data, spaces and operator characters become `_` before the patterns run; anything that runs a shell or interpreter, and any parse problem, is scanned as today.
**Done when:** a commit message or heredoc mentioning a deletion command passes, every command blocked today is still blocked, and `bash hooks/block-destructive.sh --test` covers both.
- [x] Design it (spec): `/architect guard hook false alarms`
- [x] Build it: `/develop guard hook false alarms`
   - [x] Data region scanner, executor check and raw fallbacks in the repo copy of the hook (AC-1 to AC-4)
   - [x] New self checks with the forced blanking switch and a mutation check per allow case (AC-5)
- [x] Verify it: `/check verify guard hook false alarms`
- [x] Test it: `/test guard hook false alarms`
- [x] Between runs, copy the hook live: `cp ~/claude-config/hooks/block-destructive.sh ~/.claude/hooks/block-destructive.sh`, then make one real commit whose message names a deletion command (AC-6) · waits on you
- [x] Sync docs: `/sync guard hook false alarms`
Spec [0016](../specs/0016-guard-hook-false-alarms/index.md) · code in `hooks/block-destructive.sh`
Source: personal scope row 10 (`~/projects/docs/scope/scope.md`; hook errors on 2026-10-11); redesign agreed 2026-10-13 after the cross check.

### 24. Runner resilience · in-progress · auto
Eight runner changes: wait through an API outage, stop on a crash loop, count tokens and cost, name the boxes a timed out call ticked, a real end to end fixture, a live log, a `/sync` box that runs, and a waits on you box that lets later boxes go on.
**Done when:** the spec is built, each behavior has its test, and `python3 runner/e2e/run.py` passes on the real claude.
- [x] Design it (spec): `/architect runner resilience`
- [x] Build it: `/develop runner resilience`
   - [x] Tokens and cost, live log with `--session-id` (AC-3, AC-6)
   - [x] Timeout unconfirmed boxes, outage waits, crash loop (AC-1, AC-2, AC-4)
   - [x] Sync box and skip ahead in `wf.py` and `run.py`, repo copy of `rules/scope-contract.md`, architecture table (AC-7, AC-8)
   - [x] Fixture repo and `runner/e2e/run.py` with its fake `wf` test (AC-5)
- [x] Verify it: `/check verify runner resilience`
- [x] Test it: `/test runner resilience`
- [x] Copy the rule file live: `cp ~/claude-config/rules/scope-contract.md ~/.claude/rules/scope-contract.md` (AC-8) · waits on you
- [x] Run the real end to end with `!`: `python3 runner/e2e/run.py`, record it in `docs/specs/0014-runner-resilience/verify.md` (AC-5, AC-9) · waits on you
- [ ] Sync docs: `/sync runner resilience`
Spec [0014](../specs/0014-runner-resilience/index.md) · code in `runner/run.py`, `runner/wf.py`, `runner/e2e/`, tests in `runner/tests/test_resilience.py`
Source: [~/projects/docs/briefs/runner-ideas-2026-10-12.md](../../../projects/docs/briefs/runner-ideas-2026-10-12.md) (spec A, ideas 1 to 6); personal scope row 24 (skip ahead and `/sync` box notes); personal scope row 18.

### 25. Checks that cannot lie · in-progress · auto
One always loaded rule file the vendored skills cannot overwrite: verify steps and tests must be able to fail, every spec lists its files and `/sync` warns on stale ones, and cross checks compare against the brief. Under `wf run` a pass without its check line parks `unchecked`.
**Done when:** the spec is built, a planted check that cannot fail is rejected, a commit touching an accepted spec's files is flagged by `/sync`, a dropped brief item is named by the cross check, and an update of the vendored skills keeps all three.
- [x] Design it (spec): `/architect checks that cannot lie`
- [x] Build it: `/develop checks that cannot lie`
   - [x] `scripts/spec-paths.py` with `--test` and its `install.sh` link (AC-6)
   - [x] Rule 11a, the `unchecked` park and prompt lines (AC-4)
   - [x] `rules/check-gates.md` repo copy, `NOTICE.md`, `**Paths:**` backfill on specs 0001 to 0015 (AC-1 to AC-3, AC-5, AC-7 to AC-9)
   - [x] Probe scripts P1 to P3 written (AC-10)
- [x] Verify it: `/check verify checks that cannot lie`
- [x] Test it: `/test checks that cannot lie`
- [x] Copy the rule live and link the script: `cp ~/claude-config/rules/check-gates.md ~/.claude/rules/check-gates.md`, then `./install.sh` (AC-1, AC-6) · waits on you
- [x] Run probes P1 to P3 with `!` and record them in `docs/specs/0015-checks-that-cannot-lie/verify.md` (AC-10) · waits on you
- [ ] Sync docs: `/sync checks that cannot lie`
Spec [0015](../specs/0015-checks-that-cannot-lie/index.md) · code in `runner/run.py`, `scripts/spec-paths.py`, `rules/check-gates.md`, `install.sh`, tests in `runner/tests/test_checks.py`, `runner/tests/test_spec_paths.py`
Source: [~/projects/docs/briefs/runner-ideas-2026-10-12.md](../../../projects/docs/briefs/runner-ideas-2026-10-12.md) (spec B, ideas 7 and 8; item 7 narrowed to changed tests, agreed 2026-10-13); personal scope rows 19 and 12 part 2.

### 29. Several repos at once · in-progress · auto
Bare `wf run` becomes a parent that starts today's single repo run once per repo with work, side by side: `--jobs N` caps it, repos sharing an app port, git dir or folder never run together, lines are prefixed `[<repo>]` with one summary at the end. Several features inside one repo at once still waits on feature 14.
**Done when:** the spec is built, and one `wf run` builds features in two repos at the same time (`runner/e2e/run.py --parallel` passes on the real claude).
- [x] Design it (spec): `/architect several repos at once`
- [x] Build it: `/develop several repos at once`
   - [x] Parent: has work flag, staggered child start, `--jobs`, exit codes (AC-1, AC-2, AC-6, AC-7)
   - [x] Never together rule, prefixed output and summary, signal forwarding (AC-3, AC-4, AC-5)
   - [x] `runner/e2e/run.py --parallel` (AC-8)
- [x] Verify it: `/check verify several repos at once`
- [x] Test it: `/test several repos at once`
- [x] Run `python3 runner/e2e/run.py --parallel` with `!` and record it in the spec's Follow-up (AC-8) · waits on you
- [ ] Sync docs: `/sync several repos at once`
Spec [0017](../specs/0017-several-repos-at-once/index.md) · code in `runner/run.py` (`parallel()`), `runner/wf.py` (`--jobs`), `runner/e2e/run.py` (`--parallel`), tests in `runner/tests/test_parallel.py`
Source: personal scope row 23 (`~/projects/docs/scope/scope.md`; your message of 2026-10-12, multi tasking question).

## Release 5: nothing left for you in the morning

The 2026-10-13 night run ended at 03:20 with no message and six manual steps over four features. Designed together on 2026-10-13 (specs 0018, 0019); the next `wf run` builds 30 first, then 13.

### 30. Live setup steps in one command · in-progress · auto
The runner keeps building and gathers every waits-on-you step of the run that copies into `~/.claude`, runs `install.sh` or runs a real claude check, then gives you one command that does them all and ticks their boxes. The unattended calls still never write `~/.claude` themselves. Built before feature 13, which reads its ` · live` tag.
**Done when:** a run whose features end in live setup steps leaves you one command, and running it does every step, keeps `autoMode`, and ticks the boxes so the next run can `/sync`.
- [x] Design it (spec): `/architect live setup steps in one command`
- [ ] Build it: `/develop live setup steps in one command`
   - [ ] ` · live` tag, shapes, plan and confirm in `runner/finish.py` and `wf finish` (AC-1 to AC-3)
   - [ ] Phases, backups, logs, failure policy, Ctrl C (AC-4)
   - [ ] Record in verify.md, tick, commit, end lines, report.seen, exit codes (AC-5 to AC-8)
   - [ ] `install.sh` keeps `autoMode`, its self checks; repo copies of `rules/scope-contract.md` and `rules/runner-handoff.md` (AC-9, AC-10)
- [ ] Verify it: `/check verify live setup steps in one command`
- [ ] Test it: `/test live setup steps in one command`
- [ ] Copy the scope contract live: `cp ~/claude-config/rules/scope-contract.md ~/.claude/rules/scope-contract.md` (AC-10) · waits on you · live
- [ ] Copy the handoff rule live: `cp ~/claude-config/rules/runner-handoff.md ~/.claude/rules/runner-handoff.md` (AC-10) · waits on you · live
- [ ] Install, keeping your autoMode: `./install.sh` (AC-9) · waits on you · live
- [ ] Sync docs: `/sync live setup steps in one command`
Spec [0019](../specs/0019-live-setup-steps/index.md) · code in `runner/finish.py`, `runner/wf.py`, `install.sh`, tests in `runner/tests/test_finish.py`, `scripts/private-names.py --test`
Source: [docs/briefs/morning-report-and-live-steps.md](../briefs/morning-report-and-live-steps.md) (fix A).

### 13. Morning report · in-progress · auto
When a run ends, for any reason, one phone message: what got built, what waits on you, and the next command. The next `~/.claude` session opens with the same report.
**Done when:** after a run you get the phone note, and your next `~/.claude` session opens with the report.
- [x] Design it (spec): `/architect morning report`
- [ ] Build it: `/develop morning report`
   - [ ] `runner/report.py`, `ntfy` title, tags and `scrub_field`, called at the end of a single repo run (AC-1 to AC-4)
   - [ ] One report for a bare `wf run` parent (AC-1, AC-2)
   - [ ] `wf report`, `--seen`, `--hook`, killed run line; settings SessionStart entry and the handoff rule line (AC-5 to AC-7)
   - [ ] `runner/e2e/run.py` report checks (AC-8)
- [ ] Verify it: `/check verify morning report`
- [ ] Test it: `/test morning report`
- [ ] Install the session hook: `./install.sh` (AC-7) · waits on you · live
- [ ] Copy the handoff rule live: `cp ~/claude-config/rules/runner-handoff.md ~/.claude/rules/runner-handoff.md` (AC-7) · waits on you · live
- [ ] Real end to end with the report: `python3 runner/e2e/run.py` (AC-8) · waits on you · live
- [ ] Real parallel end to end with one report: `python3 runner/e2e/run.py --parallel` (AC-8) · waits on you · live
- [ ] Sync docs: `/sync morning report`
Spec [0018](../specs/0018-morning-report/index.md) · code in `runner/report.py`, `runner/ntfy.py`, `runner/run.py`, `runner/wf.py`, `runner/e2e/run.py`, tests in `runner/tests/test_report.py`
Source: [docs/briefs/morning-report-and-live-steps.md](../briefs/morning-report-and-live-steps.md) (fix B); first deferred 2026-10-12, brought back 2026-10-13.

## Deferred
Out of scope for the current build pass, kept so the plan stays honest.

### 31. Guard baseline check before each repo · planned
Bare `wf run` would check each repo's protected files just before starting it and skip the repo if anything changed since the plan. Left out of feature 29 on 2026-10-13 (answer `w8d0 2`); the gap is recorded in spec 0017.
**Done when:** a protected file changed by another repo's call makes the next repo skip with the file named.
- [ ] Design it (spec): `/architect guard baseline check before each repo`
Source: spec [0017](../specs/0017-several-repos-at-once/index.md) accepted gap; decision `w8d0` of 2026-10-13.

### 23. Questions that teach · needs a decision
Deferred 2026-10-12: do it after the runner features are built.
Every question panel, in every session, explains the ideas it asks about in plain words and offers a way to learn the idea before you answer. It grows `rules/plain-questions.md`, which already asks for plain wording and a from zero explanation when you say you do not follow. Research comes first, so the design rests on how good teaching inside a question is actually done.
**Done when:** a question panel in a fresh session explains each idea it asks about in plain words and offers a "learn this first" path, the rule reaches skills that are vendored and overwritten on pull, and the research behind it is recorded in the spec's `rationale.md`.
- [ ] Research it: `/deep-research how to teach a concept inside a decision question: plain explanations, an option to learn more, without slowing down people who already know it`
- [ ] Design it (spec): `/architect questions that teach`
Source: your message of 2026-10-12 (`/scope` request).

### 15. Cheap worker tier · needs a decision
Deferred 2026-10-12 (architecture pass): a cost saving, the goal does not need it.
Low value work (summaries of long pages, transcripts and logs, first pass triage of search results, field extraction, classification, commit message drafts) goes to claude-fb's free models through an `fb-ask` helper, and the answer comes back to the Claude session as data. Never code edits, decisions, security review, or client code on fb-any.
**Done when:** a runner step sends a summary job through `fb-ask`, Claude uses the answer, and a code or decision task can never be routed there.
- [ ] Design it (spec): `/architect cheap worker tier`

### 16. Issues and mixed source of truth · needs a decision
Deferred 2026-10-12 (architecture pass): your scopes are the source of truth; issues are not needed for the goal.
Per repo `**Source of truth:** scope | issues | mixed`. With issues or mixed, the runner rereads the linked GitHub issue before every step; if it changed after the spec was written, the feature parks and you are asked. In mixed, the issue holds the requirement and the scope tracks the build, and the issue wins on conflict. Never tied to an org or repo name.
**Done when:** an issue edited after its spec parks the feature with the diff shown, and a repo set to scope never calls GitHub.
- [ ] Design it (spec): `/architect issues and mixed source of truth`

### 11. Autopilot offer and batch design · needs a decision
Deferred 2026-10-12 (architecture pass): you run `/architect` yourself in one sitting; batching it is a convenience.
When a conversation ends with buildable features, one question: "Queue these for autopilot?". Then `/architect` runs for each one back to back, one question round per spec, until every spec is accepted and tagged `auto`.
**Done when:** answering yes leaves every queued feature with an accepted spec and the `auto` tag, with all questions asked before the unattended run starts.
- [ ] Design it (spec): `/architect autopilot offer and batch design`

### 12. Usage limit planning · needs a decision
Deferred 2026-10-12 (architecture pass): estimates and refusals are not needed; the pause through a reset moved into feature 8.
Estimate each step's usage from past sessions, compare it with the 5 hour window and the weekly limit, start right after a reset, sleep through a reset, and refuse a run the week cannot finish.
**Done when:** a run that does not fit is refused before it starts, and one that hits the 5 hour limit pauses and resumes after the reset.
- [ ] Design it (spec): `/architect usage limit planning`

### 14. Draft PR per spec · needs a decision
Deferred 2026-10-12 (architecture pass): opening a PR needs a push, which the runner never does.
Checkpoint commits on a work branch squash into one clean commit per feature, and the runner opens one draft PR per spec, never marked ready or merged. Waits on the branch and PR standard (personal scope item 11).
**Done when:** a finished feature ends as one commit on its branch with a draft PR, and the runner has no path to merge or mark ready.
- [ ] Design it (spec): `/architect draft PR per spec`

## Legend

**The decision box.** Every feature carries exactly one, the sub task whose label ends with `(spec)`. Skills locate it by that `(spec)` suffix, never by an exact label. Every other box is an execution box and `/architect` never ticks one.

- **Next step** = the first unticked box (always a command or a tracked milestone).
- **needs a decision** = run `/architect` first; otherwise straight to `/develop`. The tag drops once the spec is captured.
- **Atomic build tasks live in the spec's `## Build plan`, not here**: the scope carries only the milestone rollup.
- **Status** `planned` -> `in-progress` -> `done`, plus `existing` (pre workflow) and `dropped` (de scoped, kept for history).
- **Workflow tier tag** beside a heading (e.g. `· GA`) sets that one feature's rigor; no tag inherits the Beta default.
- **Workflow** Beta = `/check verify`, then `/test` after `/develop`. A feature built on an unratified decision (an `Assumed` spec) stays flagged, but that never blocks `done`.
- **Pointer line** (`spec <n> · code in <path>`): the spec link added by `/architect`, the code path by `/develop`.
