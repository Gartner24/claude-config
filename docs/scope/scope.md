# Scope: claude-config

Your Claude Code setup, published. Rows 1 to 89 built the autonomous workflow runner (`wf`), retired live on 2026-10-22 (row 90). The current build is one workflow in every chat, with no runner.

**Build approach:** Skateboard (each stage is usable on its own, and each next stage grows the same tool).
**Workflow:** Beta (after `/develop`: `/check verify`, then `/test`). It runs unattended on your machine, so it gets tests. `/architect` is the recommended first stop for a feature with a real decision, but skippable when you already know the build. Any feature can carry its own tag (e.g. `· GA`) to do more or less.
**Source of truth:** scope
**Autopilot:** allowed

_These are recommendations to keep your build orderly, not requirements. Skip anything that does not fit: if you already know how to build a feature, use `/develop` and skip `/architect`. You decide when a feature is `done`._

Source: personal scope item 8 (`~/projects/docs/scope/scope.md`). Settled requirements: section 0 of `~/Documents/workflow-research/09-autonomous-runner-research.md`; read it before any `/architect` here.

Closed rows (done or dropped, no open box) live in [done.md](done.md).

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
| 46 | Missed-skill detector | Release 8 | done |
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
| 60 | Sessions pass work to each other | Release 9 | done |
| 61 | Cheap model gatekeeper with open models | Release 9 | done |
| 62 | Runner that improves itself | Release 9 | done |
| 63 | Evaluate Harvey, Soup, MiroFish, claude-skills-founder, Headroom | Release 9 | done |
| 64 | Recommended mods: gatekeeper, Claude to Claude, own panel | Release 9 | done |
| 65 | Scan skills with skillspector | Release 9 | done |
| 67 | Local model on the laptop | Release 9 | done |
| 68 | Runner runs more than 4 features at once | Release 9 | done |
| 69 | Ideas borrowed from tools we skip | Release 9 | done |
| 70 | graphify test on one repo | Release 9 | done |
| 71 | Self merge rules and review notes | Release 9 | done |
| 72 | wf-dash band and alerts | Release 9 | done |
| 73 | wf-dash panes and actions | Release 9 | done |
| 74 | Fix the runner's plan landing crash | Release 9 | done |
| 75 | wf-dash stray keys | Release 9 | done |
| 76 | Auto handoff: our handover, fired on its own | Release 9 | done |
| 77 | Auto handoff display: band, viewer pages, link | Release 9 | done |
| 78 | Runner bugs found 2026-10-18 | Release 9 | done |
| 79 | Security review leftovers 2026-10-18 | Release 9 | done |
| 80 | Skill scan trusted list | Release 9 | done |
| 81 | wf-dash design should-fixes | Release 9 | done |
| 82 | Finish when the owner is away | Release 9 | done |
| 83 | The word "after" stalls a feature | Release 9 | done |
| 84 | Assertion Guardian blocks only removed checks | Release 9 | done |
| 85 | Mod install also reinstalls the runner copy | Release 9 | dropped |
| 86 | Home-base chat runs from claude-config | Release 9 | done |
| 87 | A live install box is ticked only when it is live | Release 9 | done |
| 88 | Fix: auto handoff answers the question it cut off | Release 9 | done |
| 89 | Review leftovers 2026-10-21 | Release 9 | done |
| 90 | Retire the runner, its features in every chat | Release 10 | done |
| 91 | Handover memory | Release 10 | done |
| 92 | Skills start themselves at the right moment | Release 10 | done |
| 93 | Dashboard restructure for the setup without wf | Release 10 | done |
| 94 | Three numbers for the switch-on rules | Release 10 | done |
| 95 | Fix: auto handoff fires after /auto-handoff off | Release 10 | done |
| 96 | Rename the dashboard mod to chip-dash | Release 10 | done |
| 97 | Restructure claude-config to the icm-architect layout | Release 10 | in-progress |
| 98 | Helper scripts the switch-on rules still lack | Release 10 | done |
| 99 | Auto handoff off by itself in plain talk chats | Release 10 | dropped |
| 100 | build-features workflow, shown while it runs | Release 10 | done |
| 101 | Workflow templates research and a workflow builder skill | Release 10 | in-progress |
| 102 | review-fix and restructure-check workflows | Release 10 | in-progress |
| 103 | Fix: a manual handoff gets the "not live" facts list | Release 10 | in-progress |
| 104 | Fix: a resumed chat follows the folder's auto handoff setting | Release 10 | done |
| 105 | Fix: blind review findings | Release 10 | done |
| 106 | Assertion Guardian guard gaps | Release 10 | done |
| 107 | Review leftovers 2026-10-22: destructive guard spellings | Release 10 | done |
| 108 | Assertion Guardian: hidden background jobs and folder changes | Release 10 | done |
| 109 | restructure-check follow-ups from its first real run | Release 10 | done |
| 110 | Fix: install reapplies a changed patch to an edited skill | Release 10 | done |
| 111 | Review leftovers 2026-10-23: destructive guard pathspec forms | Release 10 | done |
| 113 | Review leftovers 2026-10-23 (late): guard spellings and here-strings | Release 10 | not started |
| 112 | Assertion Guardian: remaining hidden command forms | Release 10 | done |

Build order follows the table: 6, 22, 20, 8, 7, 9, 10. The goal and the rules every feature keeps are in [docs/architecture.md](../architecture.md).

## Existing

### A. Sync and install · existing
`tools/bin/sync.sh` pulls live `~/.claude` into the repo, `tools/bin/install.sh` puts it back with self checks. code in `tools/bin/sync.sh`, `tools/bin/install.sh`

### B. Design pipeline and gate · existing
Run ledger, Stop hook, font and colour scripts behind `design`, `brand-system`, `design-gate`. code in `skills/design/`, `skills/design-gate/`

### C. Review stack · existing
Multi agent pre ship review with a blind lane and a pre push receipt hook. code in `skills/review-stack/`, `hooks/review-stack-pre-push`

### D. Skill routing · existing
`tools/config/routing.md` routing table and its regression check (the intent router was removed 2026-10-19). code in `tools/scripts/check-routing.py`

## Release 7: clean branches and the tool review
The clean branches feature and the October 2026 tool review plan ([brief](../briefs/tool-review-2026-10.md)).

### 59. Memory tool: claude-mem, MemPalace, graphify or NotebookLM
Pick the memory tool (MemPalace or NotebookLM as a second brain; graphify was removed and claude-mem's data deleted 2026-10-19), weighing usage, token cost, memory quality and code memory.
**Done when:** one memory setup is chosen with its reasons and installed, or each option is rejected with a reason.
- [x] Research and compare: `/deep-research memory for Claude Code: claude-mem, MemPalace, graphify, NotebookLM` · report in [docs/research/tool-review-2026-10/](../research/tool-review-2026-10/)
- [ ] Design it (spec): `/architect memory tool` (after the MemPalace trial review, about 2026-10-30; your answer 2026-10-17) · waits on you
Source: [brief](../briefs/tool-review-2026-10.md). Every item needs its own deep research and a comparison with the existing setup first; row 66 goes first.

### 85. Mod install also reinstalls the runner copy · dropped
Dropped 2026-10-22: the runner is retired live (row 90), so no mod calls an installed `wf` any more.
When a mod calls a new `wf` subcommand, the install box copies the mod but not the runner, so the mod calls a command the installed `wf` does not have yet.
**Done when:** a mod install box that needs a new `wf` subcommand also reinstalls the runner copy (`finish.install_runner`), with a test.
- [ ] Design it (spec): `/architect mod install also reinstalls the runner copy`
- [ ] Build it: `/develop mod install also reinstalls the runner copy`
- [ ] Verify it: `/check verify mod install also reinstalls the runner copy`
- [ ] Test it: `/test mod install also reinstalls the runner copy`
- [ ] Sync docs: `/sync mod install also reinstalls the runner copy`
Source: chat 2026-10-19 (carried in the handover of that day).

## Release 10: one workflow in every chat, no runner

### 90. Retire the runner, its features in every chat · done
The `wf` runner is retired live. What it did for some chats is now a rule in every chat, the loaded text is trimmed, and risky reviews get a second claude-fb pass.
**Done when:** no `wf` link, rule or allow entry is live; the kept features switch on by condition (`rules/when-to-switch-on.md`); the changes are merged and copied live.
- [x] Build it: PRs #126 to #135, #137, #138 (retire live, `/auto-handoff` switch, 250k handoff line, allow rules, three small rules, question format, wf leftovers, handoff fixes, briefs, all chats rules, trim, fb second review); dotfiles PR #1 (global commit-msg hook)
- [x] Copy live: rules, `CLAUDE.md`, hooks, settings (17 wf rules removed by your script), `~/.config/wf` trashed
- [ ] Push the local dotfiles main (one merge commit, plus the AGENTS.md trim) · waits on you · later boxes go on
- [x] Try `fb-ask review` on the next risky review (ran on PRs #206, #214, #218 on 2026-10-22/23: 29 findings, 0 confirmed, all dropped against the code)
Source: [brief](../briefs/retire-runner.md) ("Decisions 2026-10-22 (third chat)") and [brief](../briefs/context-trim-and-all-chats.md).

### 97. Restructure claude-config to the icm-architect folder layout · in-progress
You asked to restructure claude-config into the folder layout of RinDig's icm-architect repo. Phase 1: [0072](../specs/0072-icm-restructure/index.md); phase 2 is designed after phase 1 lands.
**Done when:** the repo follows the agreed layout, `tools/bin/install.sh --dry-run` and the suite pass, and every live link still resolves.
- [x] Run icm-architect read only: skillspector scan of RinDig/icm-architect, install it, run its restructure mode steps 1 to 5 only (inventory, form, roles, reference report, proposed tree and migration map, nothing moved); save its output in [brief](../briefs/icm-research.md) and show the owner its tree next to ours
- [x] Design it (spec): `/architect restructure claude-config to the icm-architect layout` (spec 0072, phase 1; answers in [brief](../briefs/icm-restructure.md))
- [x] Build it: `/develop restructure claude-config to the icm-architect layout`
  - [x] Reference check, tests split, runner archive (0072a; AC-1 to AC-5, AC-13) · PR #165: ref-check clean, suite 139 ok (5 live-script tests copied from the archive, your call after the regression check), /review APPROVE with 2 P3s fixed, see [verify](../specs/0072-icm-restructure/verify.md)
  - [x] Map cards, CLAUDE.md entry, AGENTS.md link (0072b; AC-6 to AC-10) · built on feat/0072-map-and-entry: suite 143 ok, ref-check clean, AC-9 probe commit and hook refresh left for after merge, see [verify](../specs/0072-icm-restructure/verify.md)
  - [x] Scope split (0072c; AC-11, AC-12)
- [x] Verify it: `/check verify restructure claude-config to the icm-architect layout` (whole phase on merged main: 33 live links resolve, dry run clean, suite 150 ok, ref-check strict exit 1 on 36 dropped pointers judged not dangling, see [verify](../specs/0072-icm-restructure/verify.md))
- [x] Test it: `/test restructure claude-config to the icm-architect layout` (no new test; suite 150 ok; mutation check 0)
- [x] Design phase 2 (spec): `/architect restructure claude-config phase 2` (spec [0077](../specs/0077-restructure-phase-2/index.md) accepted 2026-10-22 after a Sonnet cross check, 12 gaps fixed; probes P1 and P2 passed, P3 owed at build step 1)
- [x] Build phase 2 PR A: `/develop restructure claude-config phase 2` (0077a lighter chats, AC-1 to AC-9)
  - [x] Built on feat/0077-lighter-chats · PR #205 merged: probe P3 passed (no mod change), always loaded text 52,699 to 16,325 characters, 14 rule files and 3 CLAUDE.md sections moved word for word to `rules-on-demand/`, `skill-rules.py` hook, reminder removed, `MAP.md`, install, drift and sync, docs; suite 167 ok, 21 mutants caught, see [verify](../specs/0077-restructure-phase-2/verify.md)
  - [x] Real install and the live AC-1 measure (installed 2026-10-23, drift none)
  - [x] `/restructure-check` on the PR (AC-9): run 20261022-230208 on #205, cited in [verify](../specs/0077-restructure-phase-2/verify.md)
- [ ] Live check: a fresh chat with `/architect x` gets the rules, a plain question chat does not · waits on you · later boxes go on
- [x] Build phase 2 PR B: `/develop restructure claude-config phase 2` (0077b tools folder, AC-10 to AC-15, after PR A merges)
  - [x] Built on feat/0077-tools-folder · PR #210 merged: the bin, scripts and config folders moved with `git mv` under `tools/`, every live referrer moved (settings, install links and self checks, sync, hooks, mods, workflow stage, rules, skills, map, tests, docs, spec Paths lines), root finders two folders up, `tests/test_tools_folder.py` (AC-10, AC-12, AC-13); ref-check verify left only history, live-only and non-repo pointers; 25 mutants caught, see [verify](../specs/0077-restructure-phase-2/verify.md)
  - [x] Real install from the new path, then `drift: none` and `hook-files` clean (installed 2026-10-23, drift none)
  - [x] `/restructure-check` on the PR (AC-15): hand recapture on head with `tools/` paths, run 20261023-014032, verdict pass, needs a look 0; see [verify](../specs/0077-restructure-phase-2/verify.md) PR B
- [x] Verify it: `/check verify restructure claude-config phase 2`
  - [x] PR B (AC-10 to AC-15): 8 steps with can-fail notes (install dry run, live links, docs, self checks, 55 spec-paths, ref-check verify, drift, suite 184 ok); see [verify](../specs/0077-restructure-phase-2/verify.md)
  - [x] PR A (AC-1 to AC-9): throwaway install shows 16,834 always loaded characters, the skill rules hook loads 9 architect files for a Skill start and a typed `/architect x` and nothing for a plain prompt, moved live rules backed up not deleted, restructure-check run 20261022-230208 cited; see [verify](../specs/0077-restructure-phase-2/verify.md)
- [x] Test it: `/test restructure claude-config phase 2`
  - [x] PR B: suite 184 ok after merging main dc66fdb, no test added or changed in this pass (builder's 25 mutants stand), mutation check 0
  - [x] PR A: suite 180 ok, wf-handoff mod 158 pass, dry run clean, no test added or changed in this pass (builder's 21 mutants stand), mutation check 0
- Earlier note on this box (after phase 1 is merged and reviewed). Also checks the live side (your answers 2026-10-22): first find out whether Claude ever edits `~/.claude` without the repo's map. If not, drop the `~/.claude` map with one line of reasoning in the spec; if yes, add only the smallest pointer file, shipped from `claude-home/` by `tools/bin/install.sh` and never loaded in normal chats. `~/.claude/private/` stays live only. Right before this box, run the restructure-check interview (row 102, `/workflow-builder restructure-check`; owner 2026-10-22). The design also cuts the always loaded text (about 18k to 25k tokens before the first message, [blind review](../reviews/blind-setup-review-2026-10-22.md) fix 1; owner 2026-10-22: fold it into phase 2)
Source: [brief](../briefs/icm-restructure.md); [brief](../briefs/retire-runner.md) line 13; your messages 2026-10-22.

### 99. Auto handoff off by itself in plain talk chats · dropped
You asked that auto handoff be off in chats that are only talk (no build), besides the on/off switch.
Dropped 2026-10-22 (your answer, tenth chat): your third chat decision stands, "Handoff in talk chats: manual only, the owner types /auto-handoff off. Nothing to build" ([brief](../briefs/retire-runner.md) line 81); row 95 makes that off hold per folder.
**Done when:** a chat with no repo work does not hand off by itself, by the condition you pick, with a mod test.
- [ ] Design it (spec): `/architect auto handoff off in plain talk chats`
Source: [brief](../briefs/retire-runner.md) second chat decisions ("still to build"); your first message 2026-10-22.

### 101. Workflow templates research and a workflow builder skill · in-progress
Research recommended workflow templates and the workflows we can make from our own skills and repos (site design, SEO, reviews), then a skill that builds new workflows the ICM way (marketing and publicity workflows come later). from spec 0072
**Done when:** a research brief lists the candidates with sources, and the builder skill makes one workflow that passes its own check.
- [x] Research it: `/deep-research workflow templates for claude-config` ([brief](../briefs/workflow-templates.md), 2026-10-22)
- [x] Design it (spec): `/architect workflow builder skill` (spec [0076](../specs/0076-workflow-builder.md) accepted 2026-10-22 after a Sonnet cross check, 15 fixes applied). Build after rows 92, 87, 98 and 97 phase 1 merge.
- [x] Build it: `/develop workflow builder skill`
  - [x] Templates and `check.py` (AC-2, AC-3, AC-5)
  - [x] The skill: interview, writing, update mode, dry run offer (AC-1, AC-4, AC-7, AC-8)
  - [x] Install link and drift kind (AC-6)
  - [x] icm-architect scan, manifest entry, build, follows line check (AC-9, AC-10) (scan and install run by you 2026-10-22)
  - [x] Proof: build review-fix (row 102) with it
- [x] Verify it: `/check verify workflow builder skill` (AC-1 to AC-6, AC-9, AC-10 with can fail lines in the spec verify.md; AC-7 and AC-8 on first real use, your answer 2026-10-22)
- [x] Test it: `/test workflow builder skill` (check.py 30 of 30, suite 154 ok; mutants in verify.md)
- [ ] Prove AC-7 and AC-8 on first real use: your first `/review-fix <pr> --limit 1` on a real review (AC-8), and your first change to review-fix through `/workflow-builder review-fix --update` (AC-7) · waits on you · later boxes go on
Source: [brief](../briefs/workflow-builder.md); [brief](../briefs/icm-restructure.md) "Workflows"; your messages 2026-10-22.

### 102. review-fix and restructure-check workflows
The two workflows you asked to be reminded of: `review-fix` (fix a PR's review findings) and `restructure-check` (the nothing broke check as one command). Built with the row 101 builder. from spec 0072. No separate spec (your answer 2026-10-22): the builder's interview is their design, seeded by the stage outlines in the [research brief](../briefs/workflow-templates.md) section 2. Starts after row 101 is built.
**Done when:** both run as `/review-fix` and `/restructure-check` on a real PR.
- [x] Design and build review-fix: `/workflow-builder review-fix` (row 101's proof step)
- [x] Design and build restructure-check: `/workflow-builder restructure-check` (interview 2026-10-22: capture, diff, judge; own PRs only; draft PR #200, check.py ok)
- [x] Run restructure-check on a real PR (PRs #205 and #210, 2026-10-22 and 2026-10-23)
- [ ] Run review-fix on a real PR (still owed: your first `/review-fix <pr>` on a real review) · waits on you
Source: [brief](../briefs/icm-restructure.md) "Workflows"; your messages 2026-10-22.

### 103. Fix: a manual handoff gets the "not live" facts list
A manual `/rollover` then `/clear` gets no "not live" list in the handover: the wf-handoff mod adds it only on its auto path (`claude-home/mods/wf-handoff/hooks/register.ts:371`, `notLiveNow`). The PR #152 fix has never had a real test.
**Done when:** a handover written by a manual `/rollover` names every changed file that is not live yet, the same as the auto path, with a mod test red on the old code.
- [x] Fix it: `/debug a manual handoff gets the not live facts list` (root cause: `finishRollover` was the only caller of `notLiveNow`, so `/handoff` after a manual `/rollover` only cleared; now `gatherFacts` is shared and `/handoff` stamps the slot once)
- [x] Verify it: `/check verify a manual handoff gets the not live facts list` (can fail: `/handoff` leaves the slot without a `## Handoff facts` block; mod test red with the stamp off)
- [x] Test it: `/test a manual handoff gets the not live facts list` (mutants: stamp disabled -> red on `## Handoff facts`; once-guard removed -> red on the second `/handoff` adding a second block)
- [ ] Live check: type `/rollover`, then `/clear`; the new chat's handover has a `## Handoff facts` block with the not live list · waits on you · later boxes go on
Source: gap found in the ninth chat of 2026-10-22 (handover of that chat, next action 2).

### 113. Review leftovers 2026-10-23 (late): guard spellings and here-strings
Found by the automated security reviews of PRs #217 and #218 and the #218 review, after rows 111 and 112 closed. `block-destructive.sh` (a text pattern guard with stated limits): a pathspec with `sub/..` that climbs to the root, a `git checkout`/`restore` split by a backslash line continuation, and `--staged` written after `--`. Assertion Guardian (spec 0079 lists only pipes): text fed to a shell by `bash <<< "..."`, `sh <<<`, `source <(...)`, `bash <(...)`, `| ksh`, `| busybox sh`. MEDIUM. The guardian part widens spec 0079 AC-7, so it needs a short `/architect` answer first.
**Done when:** each form is refused (the destructive guard) or refused before running (the guardian), with a self or mod test each, and it is live; or a form is dropped with the owner's reason.
- [ ] Design it (spec): `/architect guard leftovers here-strings` · waits on you
- [ ] Fix it: `/debug guard leftovers here-strings`
  - [x] Destructive guard part (PR pending): `..` segment, absolute, `$` and `~` pathspecs refused; backslash newline joined in check(); `--staged`/`-S`/`--worktree`/`-W` honoured only before a bare `--`. Self tests and mutants in `claude-home/hooks/block-destructive.sh`. Owner (2026-10-23): no more hardening of this text guard.
- [ ] Verify it: `/check verify guard leftovers here-strings`
- [ ] Test it: `/test guard leftovers here-strings`
Source: automated security reviews of PRs #217 and #218, and the PR #218 review (2026-10-23, this chat).

## Deferred
Out of scope for the current build pass, kept so the plan stays honest.

## Legend

**The decision box.** Every feature carries exactly one, the sub task whose label ends with `(spec)`. Skills locate it by that `(spec)` suffix, never by an exact label. Every other box is an execution box and `/architect` never ticks one.

- **Next step** = the first unticked box (always a command or a tracked milestone).
- **needs a decision** = run `/architect` first; otherwise straight to `/develop`. The tag drops once the spec is captured.
- **Atomic build tasks live in the spec's `## Build plan`, not here**: the scope carries only the milestone rollup.
- **Status** `planned` -> `in-progress` -> `done`, plus `existing` (pre workflow) and `dropped` (de scoped, kept for history).
- **Workflow tier tag** beside a heading (e.g. `· GA`) sets that one feature's rigor; no tag inherits the Beta default.
- **Workflow** Beta = `/check verify`, then `/test` after `/develop`. A feature built on an unratified decision (an `Assumed` spec) stays flagged, but that never blocks `done`.
- **Pointer line** (`spec <n> · code in <path>`): the spec link added by `/architect`, the code path by `/develop`.
