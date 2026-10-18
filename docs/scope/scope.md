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
| 24 | Runner resilience | Release 4 | done |
| 25 | Checks that cannot lie | Release 4 | done |
| 28 | Guard hook false alarms | Release 4 | done |
| 29 | Several repos at once | Release 4 | done |
| 30 | Live setup steps in one command | Release 5 | done |
| 13 | Morning report | Release 5 | done |
| 32 | One command: wf | Release 6 | done |
| 33 | Ask, never stop | Release 6 | done |
| 34 | Report names repos | Release 6 | done |
| 35 | Several features of one repo at once | Release 6 | done |
| 36 | Telegram instead of ntfy | Release 6 | done |
| 37 | Autonomous mode | Release 6 | done |
| 31 | Guard baseline check between repos | Release 6 | done |
| 23 | Understand everything | Release 6 | done |
| 15 | Cheap worker tier | Release 6 | done |
| 16 | Issues and mixed source of truth | Release 6 | done |
| 11 | Autopilot offer and batch design | Deferred | dropped |
| 12 | Usage limit planning | Release 6 | done |
| 14 | Branch and PR flow | Release 6 | done |
| 38 | Adopt your open PRs | Release 7 | done |
| 39 | Review requests to you | Release 7 | done |
| 40 | Context and links in every message | Release 7 | done |
| 41 | Styled Telegram messages | Release 7 | done |
| 42 | Answer questions while wf is off | Release 7 | done |
| 43 | Runs adapt to setup changes | Release 7 | done |
| 44 | A run does its own copy steps | Release 7 | done |
| 45 | Each step gets the feature's brief | Release 8 | done |
| 46 | Missed-skill detector | Release 8 | in-progress |
| 47 | Context monitor that fires | Release 8 | done |
| 48 | Readable layout for ~/.claude and claude-config | Release 8 | done |
| 49 | Fast runner | Release 8 | done |
| 50 | Fewer avoidable stops | Release 8 | done |
| 51 | Autonomous mode per chat | Release 8 | done |
| 52 | Review leftovers 2026-10-15 | Release 8 | done |
| 53 | Only a typed /auto turns on or releases | Release 8 | done |
| 54 | Organize claude-config and ~/.claude, sync what you use daily | Release 8 | done |
| 55 | Fewer skills described in every session | Release 8 | done |
| 56 | Clean branches, PRs and commits | Release 8 | done |
| 66 | Update Claude Code through /claude-config | Release 9 | done |
| 57 | Move my own skills out of jjstack | Release 9 | done |
| 58 | Own status bar and dashboards with mods | Release 9 | done |
| 59 | Memory tool: claude-mem, MemPalace, graphify or NotebookLM | Release 9 | planned |
| 60 | Sessions pass work to each other | Release 9 | in-progress |
| 61 | Cheap model gatekeeper with open models | Release 9 | done |
| 62 | Runner that improves itself | Release 9 | done |
| 63 | Evaluate Harvey, Soup, MiroFish, claude-skills-founder, Headroom | Release 9 | done |
| 64 | Recommended mods: gatekeeper, Claude to Claude, own panel | Release 9 | done |
| 65 | Scan skills with skillspector | Release 9 | done |
| 67 | Local model on the laptop | Release 9 | in-progress |
| 68 | Runner runs more than 4 features at once | Release 9 | done |
| 69 | Ideas borrowed from tools we skip | Release 9 | in-progress |
| 70 | graphify test on one repo | Release 9 | done |
| 71 | Self merge rules and review notes | Release 9 | in-progress |
| 72 | wf-dash band and alerts | Release 9 | done |
| 73 | wf-dash panes and actions | Release 9 | in-progress |
| 74 | Fix the runner's plan landing crash | Release 9 | done |
| 75 | wf-dash stray keys | Release 9 | in-progress |
| 76 | Auto handoff: our handover, fired on its own | Release 9 | planned |
| 77 | Auto handoff display: band, viewer pages, link | Release 9 | planned |
| 78 | Runner bugs found 2026-10-18 | Release 9 | planned |
| 79 | Security review leftovers 2026-10-18 | Release 9 | planned |
| 80 | Skill scan trusted list | Release 9 | done |
| 81 | wf-dash design should-fixes | Release 9 | planned |

Build order follows the table: 6, 22, 20, 8, 7, 9, 10. The goal and the rules every feature keeps are in [docs/architecture.md](../architecture.md).

## Existing

### A. Sync and install · existing
`bin/sync.sh` pulls live `~/.claude` into the repo, `bin/install.sh` puts it back with self checks. code in `bin/sync.sh`, `bin/install.sh`

### B. Design pipeline and gate · existing
Run ledger, Stop hook, font and colour scripts behind `design`, `brand-system`, `design-gate`. code in `skills/design/`, `skills/design-gate/`

### C. Review stack · existing
Multi agent pre ship review with a blind lane and a pre push receipt hook. code in `skills/review-stack/`, `hooks/review-stack-pre-push`

### D. Skill routing · existing
`config/routing.md` routing table, the intent router, and its regression check. code in `skills/intent-router/`, `scripts/check-routing.py`

## Foundations

### 1. Runner stack and layout · done
Pick the language, the entry point, how it installs onto your PATH, and how it is tested. Code lives in `~/claude-config` (decided).
**Done when:** a spec records the choice, and an empty runner installs through `bin/install.sh` and passes its own self check.
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
Work org and tool names sit in public files on main (`CLAUDE.md`, `HOOKS.md`, `SKILLS.md`, `NOTICE.md`, `README.md`, `.gitignore`). They move to one local untracked file, and the public files refer to it instead of naming anything. Root `CLAUDE.md` is the synced copy of `~/.claude/CLAUDE.md`, so `bin/sync.sh` and `bin/install.sh` have to keep the split. Then you decide whether main's history is rewritten too.
**Done when:** no tracked file on the branch or main names a work org or tool, a fresh `bin/install.sh` plus the local file gives the same behavior as today, `bin/sync.sh` cannot put a name back, and the history decision is recorded (and carried out if the answer is rewrite).
- [x] Design it (spec): `/architect work names out of the public repo`
- [x] Build the code: `/develop work names out of the public repo`
   - [x] Checker `scripts/private-names.py` with its self checks, temp files and made up names only (AC-1, AC-3, AC-6, AC-8, AC-10, AC-12)
   - [x] `bin/sync.sh` and `bin/install.sh` changes, tested on temp live trees through `CLAUDE_LIVE_DIR`, never run against the real `~/.claude` or `.git/hooks` (AC-3 to AC-7)
- [x] Create `~/.claude/private/` (`names.txt`, `work.md`, `gitignore`), move the name bearing passages of `~/.claude/CLAUDE.md` into `work.md` behind the import line, then run probe P1 from `docs/specs/0013-work-names-out/verify.md` (AC-1, AC-2) · waits on you
- [x] Reword tracked files: `/develop work names out of the public repo`
   - [x] Every file `python3 scripts/private-names.py check` reports reworded per the AC-9 rule, until it exits 0 (AC-9)
- [x] Run `bin/sync.sh` (it writes the private settings fragments under `~/.claude/private/`), confirm it exits 0 and `check` still exits 0 (AC-3, AC-4, AC-5) · waits on you
- [x] Run `bin/install.sh` (fragment merge, exclude lines, `pre-commit` and `commit-msg` hook links), then the AC-11 settings compare from verify.md (AC-6, AC-7, AC-11) · waits on you
- [x] Verify it: `/check verify work names out of the public repo`
- [x] Test it: `/test work names out of the public repo`
- [x] Swap the two hook links for copies by hand, before the build below: `cp --remove-destination scripts/private-names.py .git/hooks/pre-commit`, same for `commit-msg` (spec 0013 build plan 7a) · waits on you
- [x] Copy the hooks instead of linking them: `/develop work names out of the public repo`
   - [x] `bin/install.sh` copies and refreshes the hooks per the amended AC-7; `--test` hook fixtures copy the checker, install assertions cover the AC-7 scenario, docstring line 19 says copied, line 2 unchanged (spec 0013 build plan 7b)
- [x] Verify the hook copy: `/check verify work names out of the public repo`
- [x] Test the hook copy: `/test work names out of the public repo`
- [x] Rerun `bin/install.sh`: both hooks print `refreshed` or `up to date`, and neither is a symlink (spec 0013 build plan 7c, AC-7) · waits on you
- [x] Sync docs for feature 21: `/sync work names out of the public repo`
- [x] Merge `feat/autonomous-runner` into `main` locally, then rewrite history in a fresh clone per the spec 0013 migration plan phases 1 and 2, `check-history` exits 0 (AC-10) · waits on you
- [x] Delete and recreate `Gartner24/claude-config`, push `main`, `check-history` on a fresh clone of the new remote, swap folders (migration plan phases 3 to 5, AC-10) · waits on you
Spec: [0013](../specs/0013-work-names-out/index.md) · code in `scripts/private-names.py`, `bin/sync.sh`, `bin/install.sh`
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

### 24. Runner resilience · done · auto
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
- [x] Sync docs: `/sync runner resilience`
Spec [0014](../specs/0014-runner-resilience/index.md) · code in `runner/run.py`, `runner/wf.py`, `runner/e2e/`, tests in `runner/tests/test_resilience.py`
Source: [~/projects/docs/briefs/runner-ideas-2026-10-12.md](../../../../projects/docs/briefs/runner-ideas-2026-10-12.md) (spec A, ideas 1 to 6); personal scope row 24 (skip ahead and `/sync` box notes); personal scope row 18.

### 25. Checks that cannot lie · done · auto
One always loaded rule file the vendored skills cannot overwrite: verify steps and tests must be able to fail, every spec lists its files and `/sync` warns on stale ones, and cross checks compare against the brief. Under `wf run` a pass without its check line parks `unchecked`.
**Done when:** the spec is built, a planted check that cannot fail is rejected, a commit touching an accepted spec's files is flagged by `/sync`, a dropped brief item is named by the cross check, and an update of the vendored skills keeps all three.
- [x] Design it (spec): `/architect checks that cannot lie`
- [x] Build it: `/develop checks that cannot lie`
   - [x] `scripts/spec-paths.py` with `--test` and its `bin/install.sh` link (AC-6)
   - [x] Rule 11a, the `unchecked` park and prompt lines (AC-4)
   - [x] `rules/check-gates.md` repo copy, `NOTICE.md`, `**Paths:**` backfill on specs 0001 to 0015 (AC-1 to AC-3, AC-5, AC-7 to AC-9)
   - [x] Probe scripts P1 to P3 written (AC-10)
- [x] Verify it: `/check verify checks that cannot lie`
- [x] Test it: `/test checks that cannot lie`
- [x] Copy the rule live and link the script: `cp ~/claude-config/rules/check-gates.md ~/.claude/rules/check-gates.md`, then `bin/install.sh` (AC-1, AC-6) · waits on you
- [x] Run probes P1 to P3 with `!` and record them in `docs/specs/0015-checks-that-cannot-lie/verify.md` (AC-10) · waits on you
- [x] Sync docs: `/sync checks that cannot lie`
Spec [0015](../specs/0015-checks-that-cannot-lie/index.md) · code in `runner/run.py`, `scripts/spec-paths.py`, `rules/check-gates.md`, `bin/install.sh`, tests in `runner/tests/test_checks.py`, `runner/tests/test_spec_paths.py`
Source: [~/projects/docs/briefs/runner-ideas-2026-10-12.md](../../../../projects/docs/briefs/runner-ideas-2026-10-12.md) (spec B, ideas 7 and 8; item 7 narrowed to changed tests, agreed 2026-10-13); personal scope rows 19 and 12 part 2.

### 29. Several repos at once · done · auto
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
- [x] Sync docs: `/sync several repos at once`
Spec [0017](../specs/0017-several-repos-at-once/index.md) · code in `runner/run.py` (`parallel()`), `runner/wf.py` (`--jobs`), `runner/e2e/run.py` (`--parallel`), tests in `runner/tests/test_parallel.py`
Source: personal scope row 23 (`~/projects/docs/scope/scope.md`; your message of 2026-10-12, multi tasking question).

## Release 5: nothing left for you in the morning

The 2026-10-13 night run ended at 03:20 with no message and six manual steps over four features. Designed together on 2026-10-13 (specs 0018, 0019); the next `wf run` builds 30 first, then 13.

### 30. Live setup steps in one command · done · auto
The runner keeps building and gathers every waits-on-you step of the run that copies into `~/.claude`, runs `bin/install.sh` or runs a real claude check, then gives you one command that does them all and ticks their boxes. The unattended calls still never write `~/.claude` themselves. Built before feature 13, which reads its ` · live` tag.
**Done when:** a run whose features end in live setup steps leaves you one command, and running it does every step, keeps `autoMode`, and ticks the boxes so the next run can `/sync`.
- [x] Design it (spec): `/architect live setup steps in one command`
- [x] Build it: `/develop live setup steps in one command`
   - [x] ` · live` tag, shapes, plan and confirm in `runner/finish.py` and `wf finish` (AC-1 to AC-3)
   - [x] Phases, backups, logs, failure policy, Ctrl C (AC-4)
   - [x] Record in verify.md, tick, commit, end lines, report.seen, exit codes (AC-5 to AC-8)
   - [x] `bin/install.sh` keeps `autoMode`, its self checks; repo copies of `rules/scope-contract.md` and `rules/runner-handoff.md` (AC-9, AC-10)
- [x] Verify it: `/check verify live setup steps in one command`
- [x] Test it: `/test live setup steps in one command`
- [x] Copy the scope contract live: `cp ~/claude-config/rules/scope-contract.md ~/.claude/rules/scope-contract.md` (AC-10) · waits on you · live
- [x] Copy the handoff rule live: `cp ~/claude-config/rules/runner-handoff.md ~/.claude/rules/runner-handoff.md` (AC-10) · waits on you · live
- [x] Install, keeping your autoMode: `bin/install.sh` (AC-9) · waits on you · live
- [x] Sync docs: `/sync live setup steps in one command`
Spec [0019](../specs/0019-live-setup-steps/index.md) · code in `runner/finish.py`, `runner/wf.py`, `bin/install.sh`, tests in `runner/tests/test_finish.py`, `scripts/private-names.py --test`
Source: [docs/briefs/morning-report-and-live-steps.md](../briefs/morning-report-and-live-steps.md) (fix A).

### 13. Morning report · done · auto
When a run ends, for any reason, one phone message: what got built, what waits on you, and the next command. The next `~/.claude` session opens with the same report.
**Done when:** after a run you get the phone note, and your next `~/.claude` session opens with the report.
- [x] Design it (spec): `/architect morning report`
- [x] Build it: `/develop morning report`
   - [x] `runner/report.py`, `ntfy` title, tags and `scrub_field`, called at the end of a single repo run (AC-1 to AC-4)
   - [x] One report for a bare `wf run` parent (AC-1, AC-2)
   - [x] `wf report`, `--seen`, `--hook`, killed run line; settings SessionStart entry and the handoff rule line (AC-5 to AC-7)
   - [x] `runner/e2e/run.py` report checks (AC-8)
- [x] Verify it: `/check verify morning report`
- [x] Test it: `/test morning report`
- [x] Install the session hook: `bin/install.sh` (AC-7) · waits on you · live
- [x] Copy the handoff rule live: `cp ~/claude-config/rules/runner-handoff.md ~/.claude/rules/runner-handoff.md` (AC-7) · waits on you · live
- [x] Real end to end with the report: `python3 runner/e2e/run.py` (AC-8) · waits on you · live
- [x] Real parallel end to end with one report: `python3 runner/e2e/run.py --parallel` (AC-8) · waits on you · live
- [x] Sync docs: `/sync morning report`
Spec [0018](../specs/0018-morning-report/index.md) · code in `runner/report.py`, `runner/ntfy.py`, `runner/run.py`, `runner/wf.py`, `runner/e2e/run.py`, tests in `runner/tests/test_report.py`
Source: [docs/briefs/morning-report-and-live-steps.md](../briefs/morning-report-and-live-steps.md) (fix B); first deferred 2026-10-12, brought back 2026-10-13.

## Release 6: work non stop

### 32. One command: wf · done · auto
You type only `wf`. After one confirm screen it shows the report, applies pending live setup steps as one atomic swap, runs pending real claude checks, takes back features whose cause is fixed, and starts every repo with work side by side, never waiting on or stopping a run already going. `wf finish`, `wf unpark` and the rest stop being steps you are told to type.
**Done when:** with a run going in another repo, one `wf` does all five steps, that run keeps going and its next call uses the new setup, a change to `~/.claude` not made by `wf` still stops the run, and no skill, rule or report tells you to type any `wf` subcommand.
- [x] Design it (spec): `/architect one command wf`
- [x] Build it: `/develop one command wf`
   - [x] Runner copy: `install_runner` in `runner/finish.py`, `bin/install.sh` calls it, deny `~/.local/share/wf` (AC-12)
   - [x] Locks: holder line by every taker, `wf finish` without repo locks, held repos skipped (AC-9, AC-7)
   - [x] Runs take a `wf` swap: `live_dir()`, ledger acceptance, live dir guard rebuild, state folder deny (AC-5)
   - [x] Staged setup and swap: `WF_STAGE` in `bin/install.sh`, stage, journal, ledger, ordered renames, crash finish (AC-3, AC-4)
   - [x] Retakes by reason, then bare `wf`: screen, order, builds, checks beside them, commit retries (AC-6, AC-1, AC-2, AC-7, AC-8)
   - [x] One command texts and rule copies, corpus test, `runner/e2e/run.py --beside` (AC-10, AC-11)
- [x] Verify it: `/check verify one command wf`
- [x] Test it: `/test one command wf`
- [x] Copy the handoff rule live: `cp ~/claude-config/rules/runner-handoff.md ~/.claude/rules/runner-handoff.md` (AC-10) · waits on you · live
- [x] Copy the scope contract live: `cp ~/claude-config/rules/scope-contract.md ~/.claude/rules/scope-contract.md` (AC-10) · waits on you · live
- [x] Install the runner copy: `bin/install.sh` (AC-12) · waits on you · live
- [x] Real check beside a run: `python3 runner/e2e/run.py --beside` (AC-11) · waits on you · live
- [x] Sync docs: `/sync one command wf`
Spec [0020](../specs/0020-one-command-wf/index.md)
Source: [docs/briefs/never-wait-on-each-other.md](../briefs/never-wait-on-each-other.md).

### 33. Ask, never stop · done · auto
A step that needs a protected place (`~/.claude`, the runner's own `runner/`, `.git/hooks`) never parks. With a standing permission for that repo (allowed once, ahead of time) the run just writes it and goes on. Without one, it asks on your phone (yes, no, always), keeps building everything else meanwhile, and resumes that step when you answer.
The same holds for every other reason a feature is set aside today (blocked, failed checks, caps, on main): it becomes a phone question with a recommended action, the rest keeps building, and your answer resumes it (see the brief).
**Done when:** a claude-config night run whose features edit `~/.claude` and `runner/` builds them to the end with no stop, given the standing permission; without it you get one phone question and the step resumes on your yes; no park reason ends a feature without a question; a change to `~/.claude` from outside the run still stops that repo.
- [x] Design it (spec): `/architect ask never stop`
- [x] Build it: `/develop ask never stop`
   - [x] Case table in code with the AC-1 completeness test
   - [x] Feature level questions and resumes F1 to F12, standing permission (AC-2, AC-3, AC-7)
   - [x] Repo and run level cases R1 to R3, U2 to U10 (AC-4, AC-5)
   - [x] Report: open questions, repo names (AC-6, AC-8)
   - [x] Push guard coverage and run folder pruning (AC-9, AC-10)
- [x] Verify it: `/check verify ask never stop`
- [x] Test it: `/test ask never stop`
- [x] Sync docs: `/sync ask never stop`
Spec [0021](../specs/0021-never-stop/index.md) · code in `runner/run.py`, `runner/report.py`
Source: [docs/briefs/runner-never-stops.md](../briefs/runner-never-stops.md).

### 34. Report names repos · done · auto
The morning report says `repo-e679` where it means `claude-config`, because it scrubs every repo name. Show the folder name of repos that are not private (the private names list decides), so the next step is readable.
**Done when:** the phone report for a claude-config run names `claude-config`, and a repo whose name is on the private list is still hidden.
- [x] Design it (spec): built inside feature 33, spec 0021 AC-8
- [x] Build it: `/develop ask never stop` (milestone "Report: open questions, repo names")
- [x] Sync docs: `/sync report names repos`
Source: the 14:51 report of 2026-10-13 ("next: wf finish, then review and merge: repo-e679").

### 31. Guard baseline check between repos · done · auto
A repo that starts later in a bare `wf` checks its protected files are unchanged since you confirmed the plan; a change asks you (accept or stop this repo) while the rest builds.
**Done when:** a protected file changed after the plan makes that repo ask with the file named, and the other repos keep building.
- [x] Design it (spec): `/architect guard baseline check between repos`
- [x] Build it: `/develop guard baseline check between repos`
- [x] Verify it: `/check verify guard baseline check between repos`
- [x] Test it: `/test guard baseline check between repos`
- [x] Sync docs: `/sync guard baseline check between repos`
Spec [0025](../specs/0025-guard-baseline-between-repos/index.md) · Source: spec 0017 accepted gap; decision `w8d0` of 2026-10-13.

### 16. Issues and mixed source of truth · done · auto
In repos set to `issues` or `mixed`, `wf` rereads the linked issue before every step and hands its text to the step as quoted data; a change after the spec was accepted asks you with the diff, and the rest builds.
**Done when:** an issue edited after its spec asks with the diff shown, and a repo set to scope never calls GitHub.
- [x] Design it (spec): `/architect issues and mixed source of truth`
- [x] Build it: `/develop issues and mixed source of truth`
- [x] Verify it: `/check verify issues and mixed source of truth`
- [x] Test it: `/test issues and mixed source of truth`
- [x] Probe P2 on a throwaway issue (it edits the issue): see the spec's verify.md · waits on you
- [x] Sync docs: `/sync issues and mixed source of truth`
Spec [0024](../specs/0024-issues-source-of-truth/index.md) · Source: your message 2026-10-13 (agreed, not optional).

### 12. Usage limit planning · done · auto
The `wf` screen says whether tonight's picks fit your 5 hour window and your week; a run that does not fit waits for the reset (or you pick fewer, or type `now`), never refused. 10 points of the week stay free for your daytime use.
**Done when:** the screen shows fits or starts at <time>, a run that does not fit starts after the reset, and the login token is never printed or saved.
- [x] Design it (spec): `/architect usage limit planning`
- [x] Build it: `/develop usage limit planning`
- [x] Verify it: `/check verify usage limit planning`
- [x] Test it: `/test usage limit planning`
- [x] Compare the first real `wf` screen with the status line bars (P4) · waits on you
- [x] Sync docs: `/sync usage limit planning`
Spec [0022](../specs/0022-usage-limit-planning/index.md) · Source: your message 2026-10-13 (agreed, not optional).

### 14. Branch and PR flow · done · auto
One branch per spec (stacked only when the spec says so, at most 3 deep), one squashed commit per feature. In repos that opt in with `- push: draft PR`, `wf` (never a call) pushes the branch and opens a draft PR after the private names and attribution scans; a pre-push hook refusal keeps the branch local. After you mark it ready, review comments are fixed, pushed and answered with an @mention; declines are asked first. It never marks ready or merges.
**Done when:** a finished feature ends as one commit with a draft PR (or a local branch when the hook refuses), and the review loop answers every comment until the required approver approves.
- [x] Design it (spec): `/architect branch and PR flow`
- [x] Build it: `/develop branch and PR flow`
- [x] Verify it: `/check verify branch and PR flow`
- [x] Test it: `/test branch and PR flow`
- [x] Copy the rule live: `cp ~/claude-config/rules/branch-pr.md ~/.claude/rules/branch-pr.md` · waits on you · live
- [x] Add the branch-pr pointer line to `~/.claude/CLAUDE.md` · waits on you
- [x] Probes P7 and P8 on a scratch GitHub repo (they post) · waits on you
- [x] Sync docs: `/sync branch and PR flow`
Spec [0026](../specs/0026-branch-pr-flow/index.md) · Source: personal scope rows 11 and 27; your message 2026-10-13.

### 35. Several features of one repo at once · done · auto
A repo that opts in with `- parallel: <n>` builds up to n features at once, each in its own worktree on its own branch; features whose spec paths overlap never run together.
**Done when:** `runner/e2e/run.py --same-repo` passes on the real claude.
- [x] Design it (spec): `/architect several features of one repo at once`
- [x] Build it: `/develop several features of one repo at once`
- [x] Verify it: `/check verify several features of one repo at once`
- [x] Test it: `/test several features of one repo at once`
- [x] Real check: `python3 runner/e2e/run.py --same-repo` · waits on you · live
- [x] Sync docs: `/sync several features of one repo at once`
Spec [0027](../specs/0027-same-repo-parallel/index.md) · Source: personal scope row 23.

### 15. Cheap worker tier · done · auto
Boring reading jobs go to the free claude-fb models through `fb-ask` (text only, six job kinds); never client or work repos; falls back to normal Claude at once when the free models are down. Used today for the summary a failed check hands to `/debug`.
**Done when:** a failed check's debug step gets an `fb-ask` summary in an allowed repo, and a repo not on your list never reaches it.
- [x] Design it (spec): `/architect cheap worker tier`
- [x] Build it: `/develop cheap worker tier`
- [x] Verify it: `/check verify cheap worker tier`
- [x] Test it: `/test cheap worker tier`
- [x] Create `~/.claude/private/fb-ok.txt` (your own repo origins) and `~/.claude/private/fb-ask.conf` · waits on you
- [x] Copy the rule live: `cp ~/claude-config/rules/cheap-worker.md ~/.claude/rules/cheap-worker.md` · waits on you · live
- [x] Probes P1 to P3 (the claude-fb proxy) · waits on you
- [x] Sync docs: `/sync cheap worker tier`
Spec [0023](../specs/0023-cheap-worker-tier/index.md) · Source: your message 2026-10-13 (agreed, not optional).

### 23. Understand everything · done · auto
Everything Claude tells you uses words you can follow; every question panel ends with "Learn this first"; phone questions carry a short explanation and a learn option; the runner speaks plain words, with a jargon test.
**Done when:** a panel in a fresh session offers "Learn this first", a runner report holds no word from the jargon list, and the rule survives a pull of the vendored skills.
- [x] Research it: done inside spec 0028 (rationale.md)
- [x] Design it (spec): `/architect understand everything`
- [x] Build it: `/develop understand everything`
- [x] Verify it: `/check verify understand everything`
- [x] Test it: `/test understand everything`
- [x] Copy the rule live: `cp ~/claude-config/rules/plain-questions.md ~/.claude/rules/plain-questions.md` · waits on you · live
- [x] Real check of the LEARN line: `python3 docs/specs/0028-understand-everything/probes/learn-line.py` · waits on you · live
- [x] A panel is refused without "Learn this first" in a real session (P3) · waits on you
- [x] Sync docs: `/sync understand everything`
Spec [0028](../specs/0028-understand-everything/index.md) · Source: your messages 2026-10-12 and 2026-10-13.

### 36. Telegram instead of ntfy · done · auto
Questions come to your own Telegram bot with buttons, and you can reply in your own words; longer reports, very long ones as a file; the bot key is in one file only you can read; without it, ntfy works as today.
**Done when:** a run's question and report arrive in Telegram and a tap or a typed reply answers the question.
- [x] Design it (spec): `/architect telegram`
- [x] Build it: `/develop telegram`
- [x] Verify it: `/check verify telegram`
- [x] Test it: `/test telegram`
- [x] Make the bot with @BotFather, then `wf telegram init` and `wf telegram test` · waits on you
- [x] Sync docs: `/sync telegram`
Spec [0029](../specs/0029-telegram/index.md) · Source: personal scope row 26.

### 37. Autonomous mode · done · auto
`/auto on` ties a session to the runner: it starts `wf` when there is work, relays questions and the report, stays on through `/clear`, shows AUTO in the status bar; `/auto off` finishes running work, `/auto off now` stops it. Claude can never turn it on.
**Done when:** after `/auto on` and `/clear`, the new session still drives `wf`, the bar shows AUTO, and `/auto off` stops new starts.
- [x] Design it (spec): `/architect autonomous mode`
- [x] Build it: `/develop autonomous mode`
- [x] Verify it: `/check verify autonomous mode`
- [x] Test it: `/test autonomous mode`
- [x] Install the hooks, skill and status bar: `bin/install.sh` · waits on you · live
- [x] Probes P1 to P4 in a real session (`/clear`, closing the window, idle bar refresh, the skill argument) · waits on you
- [x] Sync docs: `/sync autonomous mode`
Spec [0030](../specs/0030-autonomous-mode/index.md) · Source: your message 2026-10-13; [docs/briefs/autonomous-mode.md](../briefs/autonomous-mode.md).

### 38. Adopt your open PRs · done · auto
wf adopts the open PRs you list in pr.json, runs the review loop on them, watches each until it merges, and merges only on your explicit merge now tap.
**Done when:** an adopted PR gets its review round, is watched until merged, and merges only on your tap.
- [x] Design it (spec): `/architect adopt open prs`
- [x] Build it: `/develop adopt open prs`
- [x] Verify it: `/check verify adopt open prs`
- [x] Test it: `/test adopt open prs`
- [x] Write `~/.claude/private/pr.json` for the repos to adopt · waits on you · later boxes go on
- [x] Probes P3 and P4 on a scratch GitHub repo (they post) · waits on you · later boxes go on
- [x] Sync docs: `/sync adopt open prs`
Spec [0031](../specs/0031-adopt-open-prs/index.md) · Source: your message 2026-10-13 (the gap after the draft PR until approved and merged).

### 39. Review requests to you · done · auto
A PR review requested of you becomes a question: wf drafts the review in an isolated call and posts it only on your tap.
**Done when:** a review request arrives as a question, the draft shows, and only post as my review posts it.
- [x] Design it (spec): `/architect review requests`
- [x] Build it: `/develop review requests`
- [x] Verify it: `/check verify review requests`
- [x] Test it: `/test review requests`
- [x] Probes P3 to P5 on a scratch GitHub repo (they post) · waits on you · later boxes go on
- [x] Sync docs: `/sync review requests`
Spec [0032](../specs/0032-review-requests/index.md) · Source: your message 2026-10-13 (watch for review requests to me).

### 40. Context and links in every message · done · auto
Every question and report on your phone says where it comes from: repo, feature, spec link, step, what it did, issue and PR links, and why the recommended answer is recommended.
**Done when:** a question on the phone shows its from block with working links and the why line.
- [x] Design it (spec): `/architect context in messages`
- [x] Build it: `/develop context in messages`
- [x] Verify it: `/check verify context in messages`
- [x] Test it: `/test context in messages`
- [x] Probe P1: read a real question on your phone and say whether it explains itself · waits on you · later boxes go on
- [x] Sync docs: `/sync context in messages`
Spec [0033](../specs/0033-context-in-messages/index.md) · Source: your message 2026-10-13 (context, links and the why in every message).

### 41. Styled Telegram messages · done · auto
Telegram questions in bold and italics with tappable links and the step's own words in an expandable quote; every inserted value escaped.
**Done when:** a real question arrives styled, its links open, and injected markup shows as plain text.
- [x] Design it (spec): `/architect styled telegram`
- [x] Build it: `/develop styled telegram`
- [x] Verify it: `/check verify styled telegram`
- [x] Test it: `/test styled telegram`
- [x] Sync docs: `/sync styled telegram`
Spec [0038](../specs/0038-styled-telegram/index.md) · Source: your message 2026-10-14 01:30.

### 42. Answer questions while wf is off · done · auto
Open questions show on the wf screen to answer at the keyboard; `wf questions` lists them with links; a user timer keeps Telegram taps while wf is off.
**Done when:** a question answered at the keyboard resumes its call on the next run, and a tap made while wf was off is kept.
- [x] Design it (spec): `/architect questions while off`
- [x] Build it: `/develop questions while off`
- [x] Verify it: `/check verify questions while off`
- [x] Test it: `/test questions while off`
- [x] Turn the timer on: `wf telegram timer on` · waits on you · later boxes go on
- [x] Sync docs: `/sync questions while off`
Spec [0039](../specs/0039-questions-while-off/index.md) · Source: your message 2026-10-14 02:20.

### 43. Runs adapt to setup changes · done · auto
A run switches to Telegram set up mid run, retakes a step the old setup refused once the new one allows it, and the design gate finds the right base in a shallow clone.
**Done when:** each of the three happens in a real run without a new wf.
- [x] Design it (spec): `/architect runs adapt to setup changes`
- [x] Build it: `/develop runs adapt to setup changes`
- [x] Verify it: `/check verify runs adapt to setup changes`
- [x] Test it: `/test runs adapt to setup changes`
- [x] Sync docs: `/sync runs adapt to setup changes`
Spec [0040](../specs/0040-runs-adapt-to-setup-changes/index.md) · Source: the night of 2026-10-13, morning list 2026-10-14.

### 44. A run does its own copy steps · done · auto
When a build reaches a copy of a rule, agent, command or skill into ~/.claude, it asks you on the phone and runs exactly the approved copy itself.
**Done when:** a live copy box is asked, run on your tap and ticked, and the build goes on in the same run.
- [x] Design it (spec): `/architect live steps in a run`
- [x] Build it: `/develop live steps in a run`
- [x] Verify it: `/check verify live steps in a run`
- [x] Test it: `/test live steps in a run`
- [x] Sync docs: `/sync live steps in a run`
Spec [0041](../specs/0041-live-steps-in-a-run/index.md) · Source: your message 2026-10-14 (fix the reason it stopped).

### 45. Each step gets the feature's brief · done · auto
Every unattended step gets the feature's brief (the agreed decisions) so nothing agreed in chat is lost between steps.
**Done when:** a step's prompt carries the brief and a test shows a decision from the brief reaching the call.
- [x] Design it (spec): `/architect step brief`
- [x] Build it: `/develop step brief`
- [x] Verify it: `/check verify step brief`
- [x] Test it: `/test step brief`
- [x] Sync docs: `/sync step brief`
Spec [0034](../specs/0034-step-brief/index.md) · Source: personal scope row 12 (session handoff fidelity, last part). Code in `runner/run.py` (`brief_parts`, `brief_fit`, `Run.brief_check`).

### 46. Missed-skill detector · in-progress · auto
A hook notes when a session could have used a skill it did not, and a weekly report lists the top misses.
**Done when:** the hook runs in real sessions and the report names the top missed skills.
- [x] Design it (spec): `/architect missed skill detector`
- [x] Build it: `/develop missed skill detector`
- [x] Verify it: `/check verify missed skill detector`
- [x] Test it: `/test missed skill detector`
- [x] Install it live after the merge, from main (the plan branch does not hold this feature's code) · waits on you · later boxes go on
- [x] After 3 days, run the report and write its verdict into verify.md · waits on you · later boxes go on (2026-10-17: WARM, read as trigger noise, no router)
- [ ] Sync docs: `/sync missed skill detector`
Spec [0036](../specs/0036-missed-skill-detector/index.md) · Source: personal scope row 20.

### 47. Context monitor that fires · done · auto
A context monitor that actually warns at the thresholds, wired to the status line in use.
**Done when:** a long session gets the warning at the threshold.
- [x] Design it (spec): `/architect context monitor`
- [x] Build it: `/develop context monitor`
- [x] Verify it: `/check verify context monitor`
- [x] Test it: `/test context monitor`
- [x] Install it live after the merge, from main (the first install ran without this branch) · waits on you · later boxes go on
- [x] Sync docs: `/sync context monitor`
Spec [0037](../specs/0037-context-monitor/index.md) · Source: personal scope row 6.

### 48. Readable layout for ~/.claude and claude-config · done · auto
One README map of what lives where, everything installed under claude-home/, guides under docs/guides/, ~/.claude tidied with nothing lost.
**Done when:** the README map is true, the repo has its new shape, and every migration step passed its check.
- [x] Design it (spec): `/architect readable layout`
- [x] Build it: `/develop readable layout`
- [x] Verify it: `/check verify readable layout`
- [x] Test it: `/test readable layout`
- [x] Run the live migration steps in the spec's migrate.md, one at a time with their checks · waits on you (2026-10-15, all steps passed; step 4 left until the open freelance design run closes)
- [x] Sync docs: `/sync readable layout`
Spec [0035](../specs/0035-readable-layout/index.md) · code in `claude-home/`, `bin/sync.sh`, `bin/install.sh`, `scripts/`, `runner/finish.py`, `README.md` · Source: personal scope row 9.

### 50. Fewer avoidable stops · done · auto
The runner stops less for things that need nothing from you: a check that cannot pass in the sandbox leaves those parts to the plan's later box, a retry that cannot help is not recommended, and quoted test values in the attribution scan are handled as you decide.
**Done when:** a run with features like 46 and 47 (checks needing a real session or days of use) finishes them up to their waiting box without a question, a stop where a retry cannot help recommends skip, and the attribution scan follows your rule for quoted test values.
- [x] Design it (spec): `/architect fewer avoidable stops`
- [x] Build it: `/develop fewer avoidable stops`
- [x] Verify it: `/check verify fewer avoidable stops`
- [x] Test it: `/test fewer avoidable stops`
- [x] Sync docs: `/sync fewer avoidable stops`
Spec [0045](../specs/0045-fewer-avoidable-stops/index.md) · code in `runner/run.py`, `runner/tests/test_fewer_stops.py`, `AGENTS.md` · Source: [brief](../briefs/fewer-stops.md).

### 51. Autonomous mode per chat · done · auto
Several Claude chats each drive the runner for their own repos at once; a repo belongs to one chat at a time and moves with its context written down first.
**Done when:** two chats in two folders each run autonomous mode for their own repos, their bars and questions show only their repos, and a take of a repo the other live chat holds is refused.
- [x] Design it (spec): `/architect autonomous mode per chat`
- [x] Build it: `/develop autonomous mode per chat`
- [x] Verify it: `/check verify autonomous mode per chat`
- [x] Test it: `/test autonomous mode per chat`
- [x] Install it live after the merge, from main (the plan branch does not hold this feature's code) · waits on you · later boxes go on
- [x] Two real chats in two folders: each turns on its own repos, the bars show only their own, a take of the other's repo is refused (AC-11) · waits on you · later boxes go on (passed 2026-10-17: the personal chat's take of claude-config was refused, its bar showed only its own)
- [x] Sync docs: `/sync autonomous mode per chat`
Spec [0046](../specs/0046-autonomous-mode-per-chat/index.md) · Source: [brief](../briefs/autonomous-per-chat.md) · code in `runner/auto.py`.

### 52. Review leftovers 2026-10-15 · done · auto
Only you release a repo from a chat; a check handing parts to a later step needs a written note; the bar's running count checks each run's own lock.
**Done when:** `/auto release` works only when you type it, Claude's `wf auto release` is denied, a left to the box pass needs its verify.md note, and a stale run never shows as running.
- [x] Design it (spec): `/architect review leftovers 2026-10-15`
- [x] Build it: `/develop review leftovers 2026-10-15`
- [x] Verify it: `/check verify review leftovers 2026-10-15`
- [x] Test it: `/test review leftovers 2026-10-15`
- [x] Install it live after the merge, from main (the plan branch does not hold this feature's code) · waits on you · later boxes go on
- [x] Sync docs: `/sync review leftovers 2026-10-15`
Spec [0047](../specs/0047-review-leftovers/index.md) · code in `runner/auto.py`, `runner/run.py`, `claude-home/settings.json`, `claude-home/skills/auto/SKILL.md` · Source: [review](../reviews/review-2026-10-15.md) (Leftovers).

### 53. Only a typed /auto turns on or releases · done · auto
`wf auto on` and `wf auto release` always refuse; only your typed `/auto` turns a chat on or releases a repo, and `wf auto hook` is denied to Claude.
**Done when:** Claude cannot turn a chat on or release a repo through any spelling of `wf auto on` or `wf auto release`, and your typed `/auto on` and `/auto release` still work.
- [x] Design it (spec): `/architect only a typed auto turns on or releases`
- [x] Build it: `/develop only a typed auto turns on or releases`
  - [x] Command refuses on and release, help texts and comments (AC-1, AC-2, AC-3, AC-4)
  - [x] Deny `wf auto hook`, the /auto skill text (AC-1b, AC-4)
  - [x] Tests moved to direct calls, refusal and typed path tests (AC-5)
- [x] Verify it: `/check verify only a typed auto turns on or releases`
- [x] Test it: `/test only a typed auto turns on or releases`
- [x] Install it live after the merge, from main (the plan branch does not hold this feature's code) · waits on you · later boxes go on
- [x] Sync docs: `/sync only a typed auto turns on or releases`
Spec [0049](../specs/0049-typed-auto-only/index.md) · code in `runner/auto.py`, `runner/wf.py`, `claude-home/settings.json`, `claude-home/skills/auto/SKILL.md` · Source: [review](../reviews/review-2026-10-15-0047.md) (Leftovers).

### 54. Organize claude-config and ~/.claude, sync what you use daily · done · auto
A folder structure and docs that are easy to read, and a repo that holds (or names) everything you use every day, without losing any skill.
**Done when:** the new layout is live, the rewritten docs read plainly, every skill still works, and a check shows no drift between the repo and `~/.claude`.
- [x] Design it (spec): `/architect organize and sync claude-config with ~/.claude`
- [x] Fill in the skill sources in [untraced-skills.md](../briefs/untraced-skills.md) · waits on you
- [x] Amend the spec (original plus patch, untraced skills, short AGENTS.md): `/architect amend 0048 organize and sync`
- [x] Build it: `/develop organize and sync claude-config with ~/.claude`
  - [x] Probes P1 and P2, then the repo shape: `claude-home/`, `bin/`, `config/`, every path reference and the live step shapes (AC-1 to AC-4, AC-16)
  - [x] `bin/claude-config.py` sync, install, drift and the `/claude-config` skill, folding in `skills-audit.sh` (AC-7, AC-9)
  - [x] Manifest from the lock file, framework checkouts and the traced brief, pins by history walk, patches, private store, NOTICE (AC-5 to AC-8)
  - [x] Update with the patch carried forward, conflicts and `--resolved`, the state file and the weekly reminder hook (AC-10, AC-11)
  - [x] Docs map first, then the rewrite, a short AGENTS.md and the 5 typed guides (AC-12, AC-13)
- [x] Verify it: `/check verify organize and sync claude-config with ~/.claude`
- [x] Test it: `/test organize and sync claude-config with ~/.claude`
- [x] Back up `~/.claude` and the repo, as `migrate.md` step 0 says (AC-14) · waits on you
- [x] Install the new layout by running `bin/install.sh` yourself (the old runner copy does not know this path yet) · waits on you
- [x] Check every skill name still opens, then remove the temporary `live` link (AC-15) · waits on you
- [x] Sync docs: `/sync organize and sync claude-config with ~/.claude`
Spec [0048](../specs/0048-organize-and-sync/index.md) · Source: [brief](../briefs/organize-and-sync.md).

### 55. Fewer skills described in every session · done
A fixed keep list of 37 skills keeps its description in every session; a script sets every other own skill and command to name only and reports every installed plugin. No skill is deleted, and the six long descriptions you rely on stay unchanged.
**Done when:** after the script and `bin/sync.sh`, a new session describes only keep list skills among your own, the report lists every installed plugin (sentry-skills and turned off ones included), and every skill still runs by name.
- [x] Design it (spec): `/architect fewer skills described in every session`
- [x] Build it: `/develop fewer skills described in every session`
  - [x] Keep list and script: write, backup, dry run, plugin report (AC-1 to AC-7, AC-9)
  - [x] Tests against a temp live dir (AC-8)
- [x] Verify it: `/check verify fewer skills described in every session`
- [x] Test it: `/test fewer skills described in every session`
- [x] Run `python3 scripts/skill-keep.py --dry-run`, then without it, then `bin/sync.sh` right away (AC-7) · waits on you · later boxes go on
- [x] Sync docs: `/sync fewer skills described in every session`
Spec [0050](../specs/0050-fixed-skill-keep-list/index.md) · code in `scripts/skill-keep.py`, `scripts/skill-keep.txt`, `runner/tests/test_skill_keep.py` · Source: [research](../research/organize-and-sync-review-2026-10-15.md), section 5, and the [brief](../briefs/organize-and-sync.md).

## Release 7: clean branches and the tool review
The clean branches feature and the October 2026 tool review plan ([brief](../briefs/tool-review-2026-10.md)).

### 56. Clean branches, PRs and commits · done · auto
Code reaches main only through its own squash merged PR, branches and worktrees are deleted after a merge, no combined branches, small low risk PRs merge themselves in an opted in repo, plan commits land by a docs PR, and big or old features get a warning.
**Done when:** a runner built feature ends as one squash commit on main through its PR with its branch and worktree gone, a direct push to main is refused by GitHub, and the runner's plan commits reach main by a docs PR.
- [x] Design it (spec): `/architect clean branches, PRs and commits`
- [x] Build it: `/develop clean branches, PRs and commits`
  - [x] Probe P1, combine step removed (AC-1, AC-2)
  - [x] Small and low risk, green from main, size and age lines (AC-3, AC-4, AC-12)
  - [x] Merge lock, update by merge, self merge, merge now question, allow list (AC-5, AC-6, AC-8, AC-9, AC-13)
  - [x] Cleanup after merge, plan commits by docs PR (AC-7, AC-15)
  - [x] Settings check, `bin/repo-settings.sh`, `bin/docs-pr.sh` (AC-10, AC-11)
  - [x] Rules, architecture, Amended by lines (AC-14)
- [x] Verify it: `/check verify clean branches, PRs and commits`
- [x] Test it: `/test clean branches, PRs and commits` (967 tests pass; 41 build and 15 review mutation checks)
- [x] Set the GitHub settings: `bin/repo-settings.sh Gartner24/claude-config`, then `--check` exits 0 · waits on you
- [x] Turn self merge on: `"auto_merge": true` in the claude-config entry of `~/.claude/private/pr.json` · waits on you
- [x] Sync docs: `/sync clean branches, PRs and commits`
Spec [0051](../specs/0051-clean-branches-commits/index.md) · Source: [brief](../briefs/clean-branches-and-commits.md).

### 68. Runner runs more than 4 features at once · done · auto
Remove the fixed 4: any number up to a ceiling, a live memory and usage brake, and the same files rule back from each spec's Paths line.
**Done when:** a `wf` run starts more than 4 features when memory and usage allow, never two whose Paths overlap, and holds back when free memory or the 5 hour use crosses its line.
- [x] Research and compare: `/deep-research runner with n features at once` · report in [docs/research/tool-review-2026-10/](../research/tool-review-2026-10/)
- [x] Design it (spec): `/architect runner runs more than 4 features at once`
- [x] Build it: `/develop runner runs more than 4 features at once`
  - [x] Stress test at 8 and git lock retry, stress test again (AC-7, AC-8)
  - [x] Parallel 1 to 8, read loop timeout, memory and usage brake (AC-1, AC-2, AC-3, AC-4)
  - [x] Same repo Paths wait and `Paths: none` (AC-5)
  - [x] Cores split through `WF_CORES` (AC-6)
- [x] Verify it: `/check verify runner runs more than 4 features at once` (10 of 10 steps can fail checked; `- parallel: 6` waits for the merge)
- [x] Test it: `/test runner runs more than 4 features at once` (15 mutants red, 980 tests pass)
- [x] Sync docs: `/sync runner runs more than 4 features at once`
After the merge and `bin/install.sh`: set `- parallel: 6` in AGENTS.md (your answer 2026-10-18, in the brief).
Spec [0052](../specs/0052-more-features-at-once.md) · Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan item B2.

### 66. Update Claude Code through /claude-config · done
Update Claude Code and check drift between the repo and `~/.claude` before the tool review.
**Done when:** Claude Code is current and `bin/claude-config.py drift` prints `drift: none`.
- [x] Update and drift check: `/claude-config` · waits on you (done in plan A1, PR #21, drift none)
Source: [brief](../briefs/tool-review-2026-10.md). Every item needs its own deep research and a comparison with the existing setup first; row 66 goes first.

### 57. Move my own skills out of jjstack · done
Find the skills in jjstack that are yours from its git history, and copy your own skills and the jjstack parts you use into claude-config; never commit to jjstack.
**Done when:** every skill you wrote that lived in jjstack runs from claude-config, the status line no longer needs jjstack, and jjstack has no new commit from this.
- [x] Research and compare: `/deep-research which jjstack skills are mine and what I use from jjstack` · report in [docs/research/tool-review-2026-10/](../research/tool-review-2026-10/)
- [x] Design it (spec): `/architect move my own skills out of jjstack` · skipped: decided in the research answers 2026-10-15, no spec needed
Closed 2026-10-17: the research answer for this row says keep jjstack; only its status line goes, replaced by row 58 (spec 0058); spawn-review was copied in plan A5 (PR #26).
Source: [brief](../briefs/tool-review-2026-10.md). Every item needs its own deep research and a comparison with the existing setup first; row 66 goes first.

### 58. Own status bar and dashboards with mods · done · auto
Our own status bar without jjstack: the segments ported into the runner.
**Done when:** the bottom bar draws every segment it drew before with no jjstack folder, and unknown values show `?`.
- [x] Design it (spec): `/architect own status bar and dashboards with mods`
- [x] Build it: `/develop own status bar and dashboards with mods`
  - [x] Ported segments, usage modes, unknown rules (AC-1, AC-3, AC-5)
  - [x] `bar()` switch, liveness kept, tests (AC-2, AC-4, AC-6)
- [x] Verify it: `/check verify own status bar and dashboards with mods`
- [x] Test it: `/test own status bar and dashboards with mods` (990 tests pass; 19 tests mutation checked, one fixed to see its own seen write)
- [x] Sync docs: `/sync own status bar and dashboards with mods`
Spec [0058](../specs/0058-own-status-bar.md) · Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan item B3, part 1 of 3; the band is row 72, the panes row 73.

### 59. Memory tool: claude-mem, MemPalace, graphify or NotebookLM
Pick the memory tool (keep claude-mem, MemPalace, graphify, both, or NotebookLM as a second brain), weighing usage, token cost, memory quality and code memory.
**Done when:** one memory setup is chosen with its reasons and installed, or each option is rejected with a reason.
- [x] Research and compare: `/deep-research memory for Claude Code: claude-mem, MemPalace, graphify, NotebookLM` · report in [docs/research/tool-review-2026-10/](../research/tool-review-2026-10/)
- [ ] Design it (spec): `/architect memory tool` · waits on you (after the MemPalace trial review, about 2026-10-30; your answer 2026-10-17)
Source: [brief](../briefs/tool-review-2026-10.md). Every item needs its own deep research and a comparison with the existing setup first; row 66 goes first.

### 60. Sessions pass work to each other · in-progress · auto
After a rollover you type only `/clear`: a start up hook loads the waiting handover; a `/handoff` mod on top if its probe passes.
**Done when:** a rolled over session continues after only `/clear`, and the mod is built or rejected with its probe result.
- [x] Design it (spec): `/architect sessions pass work to each other`
- [x] Run probes P1 and P2 in a scratch session (spec 0057 AC-9), write results in its verify notes · waits on you (both passed 2026-10-17, P2 with the clear run from a timer)
- [x] Build it: `/develop sessions pass work to each other`
  - [x] Hook, size cap, quiet rules, self check (AC-1, AC-2, AC-4, AC-5, AC-7)
  - [x] workflow-start yields, wiring, words (AC-3, AC-6, AC-8)
  - [x] Mod, only if P2 passed (AC-10) · built in `claude-home/mods/wf-handoff/`, static skillspector scan clean
- [x] Verify it: `/check verify sessions pass work to each other`
- [x] Test it: `/test sessions pass work to each other` (19 hook checks and 2 mod tests pass; 2 checks mutation checked; suite red only on the two plan links from main, you said go on)
- [ ] Copy the hook and settings live (`bin/install.sh` copies both and runs the hook self check), and install the mod: `ln -s ~/claude-config/claude-home/mods/wf-handoff ~/.claude/skills/wf-handoff` after a `skillspector scan` with the model pass · waits on you · later boxes go on
- [x] Sync docs: `/sync sessions pass work to each other`
Spec [0057](../specs/0057-handover-on-clear.md) · code in `claude-home/hooks/handover-start.sh`, `claude-home/mods/wf-handoff/` · Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan item B4; the handover first half of B14.

### 61. Cheap model gatekeeper with open models · done · auto
Search helpers run on Haiku, the model rule says so, and each runner call records cost per model so a routing mod is decided by data.
**Done when:** code-explorer and docs-lookup are on Haiku, call records carry `models`, and the morning report shows the run and week split with the 15% gate.
- [x] Design it (spec): `/architect cheap model gatekeeper with open models`
- [x] Build it: `/develop cheap model gatekeeper with open models`
  - [x] Probe the `modelUsage` shape (AC-6) · `claude -p` says Not logged in inside the sandbox; a real run record (feat-0048, 2026-10-15, call-01) lists its Sonnet helper as its own `modelUsage` key, so AC-4 and AC-5 were built
  - [x] Agent pins and rule (AC-1, AC-2)
  - [x] `models` field, run line, week split and gate (AC-3 to AC-5, AC-7)
- [x] Confirm Haiku gets its own cost key: in an empty folder run `claude -p "use the scout agent to list the files here" --output-format json` and check `modelUsage` lists a haiku model (AC-6) · waits on you · later boxes go on
- [x] Copy the new agent pins and rule live: `bin/install.sh` · waits on you · live · later boxes go on
- [x] Verify it: `/check verify cheap model gatekeeper with open models`
- [x] Test it: `/test cheap model gatekeeper with open models`
- [x] Sync docs: `/sync cheap model gatekeeper with open models`
Spec [0055](../specs/0055-cheap-work-cheap-models.md) · Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan item B6; row 64's gatekeeper rides on it.

### 62. Runner that improves itself · done · auto
Treat the runner as a system with a feedback loop: each run's results improve the next run, and it improves itself while idle.
**Done when:** the runner records what slowed or broke each run and turns it into a change or a proposal without you asking.
- [x] Research and compare: `/deep-research self improving agent runners and feedback loops` · report in [docs/research/tool-review-2026-10/](../research/tool-review-2026-10/)
- [x] Design it (spec): `/architect runner that improves itself`
- [x] Build it: `/develop runner that improves itself`
  - [x] History, baselines, proposals, write fence (AC-1 to AC-4, AC-8)
  - [x] End of run call, `wf insights`, hook line, /insights read (AC-5 to AC-7)
  - [x] improve-my-system skill and its extract script (AC-9)
- [x] Verify it: `/check verify runner that improves itself`
- [x] Test it: `/test runner that improves itself` (984 tests pass; 3 new tests mutation checked)
- [x] Write `~/.claude/private/history-allow.txt` with your own project folders (AC-9) · waits on you · later boxes go on
- [x] Sync docs: `/sync runner that improves itself`
Spec [0061](../specs/0061-runner-improves-itself/index.md) · code in `runner/insights.py`, `claude-home/skills/improve-my-system/` · Source: [brief](../briefs/tool-review-2026-10.md). Plan item B5.

### 63. Evaluate Harvey, Soup, MiroFish, claude-skills-founder, Headroom · done
Research each tool and compare it with the setup: Harvey (repo, site and `~/Downloads/guia-harvey.pdf`), Soup, MiroFish, claude-skills-founder, Headroom.
**Done when:** each tool is adopted, adapted or rejected with a reason, and each adopted one passed `skillspector`.
- [x] Research and compare: `/deep-research Harvey, Soup, MiroFish, claude-skills-founder, Headroom against our setup` · report in [docs/research/tool-review-2026-10/](../research/tool-review-2026-10/)
Closed 2026-10-17: research done, verdicts in brief section C; the ideas kept are row 69.
Source: [brief](../briefs/tool-review-2026-10.md). Every item needs its own deep research and a comparison with the existing setup first; row 66 goes first.

### 64. Recommended mods: gatekeeper, Claude to Claude, own panel · done
Check the three recommended mods against what we already have: a gatekeeper to a cheaper model, Claude talking to Claude (one plans, one builds), and an own panel of what each agent does.
**Done when:** each of the three is kept, built or dropped with a reason.
- [x] Research and compare: `/deep-research recommended Claude Code mods against our setup` · report in [docs/research/tool-review-2026-10/](../research/tool-review-2026-10/)
Closed 2026-10-17: the gatekeeper rides on row 61 (spec 0055), Claude to Claude is dropped (/architect then /develop and wf already do it, brief section C), the own panel is rows 58, 72 and 73.
Source: [brief](../briefs/tool-review-2026-10.md). Every item needs its own deep research and a comparison with the existing setup first; row 66 goes first.

### 65. Scan skills with skillspector · done · auto
Scan every installed skill and every new candidate with NVIDIA's `skillspector`; one `skill-scan` command and a scan before every skill update.
**Done when:** `skill-scan` runs both passes over every skill and plugin, shows only new serious findings, and `claude-config update --apply` prints a scan of what it installs.
- [x] Design it (spec): `/architect scan skills with skillspector`
- [x] Build it: `/develop scan skills with skillspector`
  - [x] Format probe (AC-11) · notes in spec [0054](../specs/0054-skill-scan-script.md) (its verify.md lands with the build)
  - [x] `skill-scan` targets, passes, resume, verdict, baseline, delta (AC-1 to AC-6, AC-9)
  - [x] Update hook, install link, skill text (AC-7, AC-8, AC-10, AC-12) · code in `scripts/skill-scan.py`, `bin/claude-config.py` `scan()`
- [x] Scan the installed skills: `skillspector` · waits on you (done in plan A4, 2026-10-16)
- [x] Bulk baseline (AC-5, build step 5): after this merges, run bin/install.sh, then `! skill-scan static --accept` in a terminal (about 20 minutes; it ends with "static: baseline holds N findings"). The build sandbox cannot write ~/.claude/state · waits on you · later boxes go on
- [x] Verify it: `/check verify scan skills with skillspector`
- [x] Test it: `/test scan skills with skillspector`
- [x] Sync docs: `/sync scan skills with skillspector`
Spec [0054](../specs/0054-skill-scan-script.md) · Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan items A3, A4, B7.

### 67. Local model on the laptop · in-progress · auto
fb-ask can send private text to the model on the laptop (`fb-local`) with `--local`; client and work text only that way.
**Done when:** `fb-ask --local` answers through `fb-local` only, client text passes only with it, and a long or cut input falls back.
- [x] Design it (spec): `/architect local model on the laptop`
- [x] Build it: `/develop local model on the laptop`
  - [x] `--local` flag, limits, truncation and build checks, gates (AC-1 to AC-6)
  - [x] Self checks, rule and docs (AC-7, AC-8)
- [x] Copy the rule live: `cp claude-home/rules/cheap-worker.md ~/.claude/rules/cheap-worker.md` · waits on you · live · later boxes go on
- [x] Install `ollama-vulkan` and join the render and video groups · waits on you (done in plan A7)
- [x] Trial: speed test, one opencode task against claude-fb's cloud model · waits on you (done in plan A7, agent task skipped by your choice)
- [x] Verify it: `/check verify local model on the laptop` (AC-1 to AC-8 met, 13 can fail steps; AC-9 left to its box)
- [x] Test it: `/test local model on the laptop` (21 self check mutants and 4 docs mutants all red, suite 973 green)
- [ ] Live probes P1 and P2, never while wf builds (AC-9) · waits on you · later boxes go on
- [ ] Sync docs: `/sync local model on the laptop`
Spec [0053](../specs/0053-fb-ask-local-model.md) · code in `scripts/fb-ask.py` · Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan items A7, B8, D4.

### 69. Ideas borrowed from tools we skip · in-progress · auto
Build the four ideas taken from Harvey, MiroFish and claude-skills-founder: a lead finder that never sends, a reaction tester, an idea scorecard, and the new number replaces old rule.
**Done when:** each of the four is in a skill and used once on a real case.
- [x] Design it (spec): `/architect ideas borrowed from tools we skip`
- [x] Build it: `/develop ideas borrowed from tools we skip`
  - [x] lead-finder skill (AC-1 to AC-3, AC-9)
  - [x] reaction-tester skill (AC-4, AC-9)
  - [x] Scorecard and rule file, manifest test (AC-5, AC-6, AC-8)
- [x] Verify it: `/check verify ideas borrowed from tools we skip`
- [x] Test it: `/test ideas borrowed from tools we skip` (983 tests pass; 11 tests mutation checked, 6 new)
- [x] Link the two skills and copy the rule live after the merge: `bin/install.sh` · waits on you · live · later boxes go on
- [ ] Use each of the four once on a real case, write it in verify notes (AC-7) · waits on you · later boxes go on
- [ ] Sync docs: `/sync ideas borrowed from tools we skip`
Spec [0056](../specs/0056-borrowed-ideas.md) · code in `claude-home/skills/lead-finder/`, `claude-home/skills/reaction-tester/`, `claude-home/rules/new-number-replaces-old.md` · Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan items B10 to B13.

### 70. graphify test on one repo · done
Map one large own repo with graphify, code only and AI keys hidden, and ask 8 to 10 questions with and without the map.
**Done when:** the test's numbers are written down and graphify is kept in that repo or uninstalled with its skill removed.
- [x] Research and compare: `/deep-research graphify against our setup` · report in [docs/research/tool-review-2026-10/](../research/tool-review-2026-10/)
- [x] Run the test on the repo you pick · waits on you (done in plan A8: it failed the rule; kept installed by your choice; B9 dropped)
Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan items A8, B9, D2.

### 71. Self merge rules and review notes · auto
The PR #18 review's open items and two script bugs found while landing it.
**Done when:** each item is fixed with a test or dropped with a reason.
- [x] Decide the three spec items (risk list, old branch date, wait for a check) · waits on you (answered 2026-10-17, written into spec 0051 AC-3, AC-4, AC-12, AC-16)
- [ ] Build it: `/develop self merge rules and review notes` (spec 0051 build step 9; tag this feature `· auto` only after row 56 is done, both change `runner/pr.py`)
- [ ] Verify it: `/check verify self merge rules and review notes`
- [ ] Test it: `/test self merge rules and review notes`
- [ ] Sync docs: `/sync self merge rules and review notes`
Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan items D1, E3, E4.

### 72. wf-dash band and alerts · done · auto
Our own mod draws a band above the prompt with the session, its effort and the runner, and alerts on finished runs, parks and questions as top right toasts that stay 15 s, each kept for the dashboard's Alerts view.
**Done when:** the band shows every segment, the effort and the runner counts, unknown shows `?`, and alerts fire once per event as 15 s toasts and land in the alert list.
- [x] Design it (spec): `/architect own status bar and dashboards with mods`
- [x] Run probes P1 to P5 in a scratch session (spec 0059 AC-6), write results in its verify notes · waits on you (passed 2026-10-17; P4b checked in the build)
- [x] Lock the look first: run the `design` pipeline on wf-dash (band, toasts, panes, short bar) in a session and land its locked `design.md` · waits on you (owner accepted the look as is on 2026-10-17 at critique 29/40; stray keys are row 75)
- [x] Build it: `/develop wf-dash band and alerts`
  - [x] `wf status --json` (AC-1)
  - [x] Band with effort, alerts, short bar (AC-2 to AC-5, amended 2026-10-18)
  - [x] Tests and scan (AC-7); the `skill-scan` runs in the install box below
- [x] Verify it: `/check verify wf-dash band and alerts`
- [x] Test it: `/test wf-dash band and alerts`
- [x] Install the mod live after its scan · waits on you · later boxes go on
- [x] Sync docs: `/sync wf-dash band and alerts`
Spec [0059](../specs/0059-wf-dash-band.md) · Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan item B3, part 2 of 3; stacks on spec 0058.

### 73. wf-dash panes and actions · in-progress · auto
One `/wf-dash` dashboard with Plan, Builds, Agents and Alerts views for the whole plan, every agent, the runner and the alerts, with three confirmed safe actions (replaces the separate `/plan`, `/agents` and `/runner` panes, amended 2026-10-18).
**Done when:** `/wf-dash` shows every scope, feature state, agent, run and alert in its four views, and the safe actions work with a confirm.
- [x] Design it (spec): `/architect own status bar and dashboards with mods`
- [ ] Run probes P6 to P9 in a scratch session (spec 0060 AC-6), write results in its verify notes · waits on you
- [x] Lock the look first: run the `design` pipeline on wf-dash (band, toasts, panes, short bar) in a session and land its locked `design.md` · waits on you (owner accepted the look as is on 2026-10-17 at critique 29/40; stray keys are row 75)
- [ ] Build it: `/develop wf-dash panes and actions`
  - [ ] `wf plan --json` and `wf answer` (AC-1, AC-5)
  - [ ] The `/wf-dash` dashboard: Plan, Builds, Agents and Alerts views (AC-2 to AC-4a)
  - [ ] Actions with confirm, tests (AC-5, AC-7)
- [ ] Verify it: `/check verify wf-dash panes and actions`
- [ ] Test it: `/test wf-dash panes and actions`
- [ ] Install the mod update live after its scan · waits on you · later boxes go on
- [ ] Sync docs: `/sync wf-dash panes and actions`
Spec [0060](../specs/0060-wf-dash-panes.md) · Source: [brief](../briefs/tool-review-2026-10.md), section The plan, enforced until done. Plan item B3, part 3 of 3, with your plan pane ask; stacks on spec 0059.

### 74. Fix the runner's plan landing crash · done · auto
At the end of the 2026-10-17 run, landing the runner's own plan commits failed with "the build tool itself hit a bug: expected str, bytes or os.PathLike object, not NoneType", so the plan commits stayed local until landed by hand (PR #36).
**Done when:** a run that ends with plan commits lands them through its docs PR with no crash, with a test that fails on the old code.
- [x] Design it (spec): `/architect fix the runner's plan landing crash` (no new decision: a bug against spec 0051 AC-15)
- [x] Fix it: `/debug fix the runner's plan landing crash`
- [x] Verify it: `/check verify fix the runner's plan landing crash`
- [x] Test it: `/test fix the runner's plan landing crash` (1026 tests pass; 2 tests mutation checked against 3 mutants)
- [x] Sync docs: `/sync fix the runner's plan landing crash`
Spec [0051](../specs/0051-clean-branches-commits/index.md) AC-15 · Source: the run report of 2026-10-17 17:57 (`plan landing:` line, run folders under `~/.local/state/wf/runs/*-20261017-17*`).

### 75. wf-dash stray keys · in-progress · auto
In the wf-dash dashboard, a key it does not draw (a filter digit outside Plan, any other letter) types into the chat prompt and takes the keyboard; the "ctrl+x tab returns here" hint did not give the keys back in a tmux test. Critique held at 29/40 mostly on this.
**Done when:** no key typed while the dashboard has the keyboard reaches the prompt, or the way back is shown and proven in a real terminal.
- [x] Design it (spec): `/architect wf-dash stray keys` (choice: catch every key with a surface module `Client` and its `onKey`; your answer 2026-10-18)
- [ ] Run probe P10 in a scratch tmux session with `claude --plugin-dir` (spec 0062 AC-1), write the result in its verify notes; a FAIL stops this feature and sends it back to `/architect` · waits on you
- [ ] Build it: `/develop wf-dash stray keys`
- [ ] Verify it: `/check verify wf-dash stray keys`
- [ ] Test it: `/test wf-dash stray keys`
- [ ] Real terminal check: type stray keys on every view in tmux, the prompt stays empty (spec 0062 AC-6) · waits on you · later boxes go on
- [ ] Sync docs: `/sync wf-dash stray keys`
Spec [0062](../specs/0062-wf-dash-stray-keys.md) · Source: the owner's message of 2026-10-17 ("accept as is") after critique round 10 scored the look 29/40.

### 76. Auto handoff: our handover, fired on its own · in-progress · auto
At 200k tokens a chat hands itself off with nothing typed: the mod gates new tool calls, runs our full `/rollover`, adds facts, numbers and your last request by code, clears, and seeds `/resume-from-clear`; loop guards 40k and 2 in a row.
**Done when:** a scratch chat crosses the line and resumes in a fresh chat with nothing typed, and every AC of spec 0063 is built.
- [x] Design it (spec): `/architect auto handoff` (your answers 2026-10-18: 200k, compact stays as backstop, every interactive chat, guards 40k and 2; all cross check fixes applied)
- [x] Run probes P1 to P5 in a scratch session with `claude --plugin-dir` (spec 0063 AC-13), write results in its verify notes; a FAIL sends this back to `/architect` · waits on you (ran 2026-10-18: P2, P4, P5 pass; P1 and P3 FAIL, both with a working alternative, see [verify notes](../specs/0063-auto-handoff/verify.md))
- [x] Amend the spec after the probe FAILs: `/architect auto handoff` (rollover and seed through `$.command.run`, seed after the awaited clear, AC-1 size read after `next(e)`; done 2026-10-18, cross check fixes applied, three new probes added)
- [x] Run probes P6 to P8 in a scratch session with `claude --plugin-dir` (spec 0063 AC-13), write results in its verify notes; a FAIL sends this back to `/architect` · waits on you (ran 2026-10-18: all pass, see [verify notes](../specs/0063-auto-handoff/verify.md))
- [x] Build it: `/develop auto handoff` (code in `claude-home/mods/wf-handoff/`; the `viewer:` line waits on spec 0064's link)
- [x] Verify it: `/check verify auto handoff` (PASS 2026-10-18 after the fix in 1c47781; the live run is left to the install box)
- [ ] Test it: `/test auto handoff`
- [ ] Install the mod live after its scan · waits on you · later boxes go on
- [ ] Sync docs: `/sync auto handoff`
Spec [0063](../specs/0063-auto-handoff.md) · Source: [brief](../briefs/auto-handoff.md) (the owner's messages of 2026-10-18).

### 77. Auto handoff display: band, viewer pages, link · auto
The handoff shows its steps and result in the wf-dash band (toasts where there is no band), each handover gets a readable page served on your Tailscale address, and a chat that came from a handoff links back to it.
**Done when:** a handoff shows in the band, its page opens from your phone over Tailscale, and every AC of spec 0064 is built.
- [x] Design it (spec): `/architect auto handoff` (your answers 2026-10-18: progress in the wf-dash band, install Tailscale)
- [ ] Install Tailscale on this laptop and your phone and log in to both (spec 0064 AC-7) · waits on you · later boxes go on
- [ ] Build it: `/develop auto handoff display`
- [ ] Verify it: `/check verify auto handoff display`
- [ ] Test it: `/test auto handoff display`
- [ ] Install both mods live after their scan · waits on you · later boxes go on
- [ ] Sync docs: `/sync auto handoff display`
Spec [0064](../specs/0064-auto-handoff-display.md) · Source: [brief](../briefs/auto-handoff.md) (the owner's messages of 2026-10-18).

### 78. Runner bugs found 2026-10-18 · auto
Six runner bugs found while conducting the 2026-10-18 runs: an accepted design park that comes back, a PR that reverts main, a worktree planning from a stale scope, a scope copy that blocks the main merge, a doubled "learn this first", and row 71 never queued.
**Done when:** each of the six is fixed with a test that fails on the old code, or dropped with a reason.
- [ ] Fix them: `/debug runner bugs found 2026-10-18`
- [ ] Verify it: `/check verify runner bugs found 2026-10-18`
- [ ] Test it: `/test runner bugs found 2026-10-18`
- [ ] Sync docs: `/sync runner bugs found 2026-10-18`
Source: [brief](../briefs/leftovers-2026-10-18.md), section Runner bugs.

### 79. Security review leftovers 2026-10-18 · auto
The 2026-10-18 security review's open items in the status bar and the skill scan script.
**Done when:** each item is fixed with a test that fails on the old code, or dropped with a reason.
- [ ] Fix them: `/debug security review leftovers 2026-10-18`
- [ ] Verify it: `/check verify security review leftovers 2026-10-18`
- [ ] Test it: `/test security review leftovers 2026-10-18`
- [ ] Sync docs: `/sync security review leftovers 2026-10-18`
Source: [brief](../briefs/leftovers-2026-10-18.md), section Security review leftovers.

### 80. Skill scan trusted list · done · auto
The skill scan skips gstack, jjstack and ui-ux-pro-max and names them in its report, so scans finish inside the time limit.
**Done when:** a scan skips the three, lists them as skipped, and still scans everything else.
- [x] Design it (spec): `/architect skill scan trusted list` (amends spec 0054; already written as its AC-13 on 2026-10-18)
- [x] Build it: `/develop skill scan trusted list`
- [x] Verify it: `/check verify skill scan trusted list`
- [x] Test it: `/test skill scan trusted list`
- [x] Sync docs: `/sync skill scan trusted list`
Spec [0054](../specs/0054-skill-scan-script.md) AC-13 · Source: [brief](../briefs/leftovers-2026-10-18.md), section Spec 0054 AC-13 trusted list.

### 81. wf-dash design should-fixes · in-progress · auto
The design gate's seven should-fixes for the wf-dash band; you pick which to build.
**Done when:** each should-fix is built or dropped by your pick.
- [x] Pick which should-fixes to build · waits on you (your pick 2026-10-18: all seven)
- [x] Design it (spec): `/architect wf-dash design should-fixes`
- [x] Build it: `/develop wf-dash design should-fixes`
- [x] Verify it: `/check verify wf-dash design should-fixes`
- [x] Test it: `/test wf-dash design should-fixes`
- [ ] Sync docs: `/sync wf-dash design should-fixes`
Spec [0065](../specs/0065-wf-dash-should-fixes.md) · Source: [brief](../briefs/leftovers-2026-10-18.md), section Row 72 design gate should-fixes.

## Deferred
Out of scope for the current build pass, kept so the plan stays honest.

### 49. Fast runner · done
Features build, check and test 4 at a time on their own branches, one plan file stays the truth, the suite runs in about a minute, and Telegram questions read clearly.
**Done when:** a `wf` run of features 39 to 48 runs 4 at once, combines its branches into one draft PR, and every question kind reads clearly on your phone.
- [x] Design it (spec): `/architect fast runner`
- [x] Build it: `/develop fast runner`
  - [x] Fast suite command and the suite prompt sentence (AC-7, AC-8)
  - [x] No same file wait, the shared plan, plan free commits (AC-2, AC-4, AC-5, AC-6)
  - [x] Combine step with its draft PR (AC-3)
  - [x] Telegram question text, every kind shown to you (AC-9, AC-10)
- [x] Verify it: `/check verify fast runner` · skipped
- [x] Test it: `/test fast runner`
- [x] Merge into feat/release-4, set the switches, scan and push feat/release-4 (AC-1, AC-11)
- [x] Run `wf` on 39 to 48 and compare the elapsed time (AC-12) · waits on you · skipped
- [x] Sync docs: `/sync fast runner`
Spec [0043](../specs/0043-fast-runner/index.md) · Source: [brief](../briefs/fast-runner.md).

### 11. Autopilot offer and batch design · dropped
Covered by `rules/runner-handoff.md` (batch first: every feature that needs a decision gets its `/architect` before the hand-off to the runner) and by choosing tonight's features on the `wf` screen (spec 0020 AC-13).

## Legend

**The decision box.** Every feature carries exactly one, the sub task whose label ends with `(spec)`. Skills locate it by that `(spec)` suffix, never by an exact label. Every other box is an execution box and `/architect` never ticks one.

- **Next step** = the first unticked box (always a command or a tracked milestone).
- **needs a decision** = run `/architect` first; otherwise straight to `/develop`. The tag drops once the spec is captured.
- **Atomic build tasks live in the spec's `## Build plan`, not here**: the scope carries only the milestone rollup.
- **Status** `planned` -> `in-progress` -> `done`, plus `existing` (pre workflow) and `dropped` (de scoped, kept for history).
- **Workflow tier tag** beside a heading (e.g. `· GA`) sets that one feature's rigor; no tag inherits the Beta default.
- **Workflow** Beta = `/check verify`, then `/test` after `/develop`. A feature built on an unratified decision (an `Assumed` spec) stays flagged, but that never blocks `done`.
- **Pointer line** (`spec <n> · code in <path>`): the spec link added by `/architect`, the code path by `/develop`.
