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
| 87 | A live install box is ticked only when it is live | Release 9 | needs a decision |
| 88 | Fix: auto handoff answers the question it cut off | Release 9 | done |
| 89 | Review leftovers 2026-10-21 | Release 9 | in-progress |
| 90 | Retire the runner, its features in every chat | Release 10 | done |
| 91 | Handover memory | Release 10 | in-progress |
| 92 | Skills start themselves at the right moment | Release 10 | in-progress |
| 93 | Dashboard restructure for the setup without wf | Release 10 | needs a decision |
| 94 | Three numbers for the switch-on rules | Release 10 | done |

Build order follows the table: 6, 22, 20, 8, 7, 9, 10. The goal and the rules every feature keeps are in [docs/architecture.md](../architecture.md).

## Existing

### A. Sync and install · existing
`bin/sync.sh` pulls live `~/.claude` into the repo, `bin/install.sh` puts it back with self checks. code in `bin/sync.sh`, `bin/install.sh`

### B. Design pipeline and gate · existing
Run ledger, Stop hook, font and colour scripts behind `design`, `brand-system`, `design-gate`. code in `skills/design/`, `skills/design-gate/`

### C. Review stack · existing
Multi agent pre ship review with a blind lane and a pre push receipt hook. code in `skills/review-stack/`, `hooks/review-stack-pre-push`

### D. Skill routing · existing
`config/routing.md` routing table and its regression check (the intent router was removed 2026-10-19). code in `scripts/check-routing.py`

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

### 87. A live install box is ticked only when it is live · in-progress
Rows 67, 69 and 71 each had a "copy live" box ticked while `claude-config drift` showed the file missing or different live (found and fixed 2026-10-20). Spec [0075](../specs/0075-live-tick-guard.md). Build only after row 92 merges (both edit `settings.json` and `bin/claude-config.py`).
**Done when:** ticking a ` · live` box first runs the drift check for the files it names and refuses the tick if they differ, with a test.
- [x] Design it (spec): `/architect a live install box is ticked only when it is live` (spec 0075 accepted 2026-10-22 after a Sonnet cross check, 9 fixes applied)
- [x] Build it: `/develop a live install box is ticked only when it is live` (PR #169, /review APPROVE, review and security fixes in)
  - [x] `live-tick.py` with `--test` (AC-1 to AC-6, AC-8)
  - [ ] `COPIED_FILES`, live settings entry, `bin/sync.sh` (AC-7) (repo side built; the live copy and live settings entry come after the merge) · later boxes go on
- [x] Verify it: `/check verify a live install box is ticked only when it is live` (AC-1 to AC-8 with can fail lines in the spec verify.md)
- [x] Test it: `/test a live install box is ticked only when it is live` (24 self checks, suite 144 ok, every guard mutation checked)
- [ ] Sync docs: `/sync a live install box is ticked only when it is live`
Source: [brief](../briefs/live-tick.md); drift check 2026-10-20 in the conductor chat. Plan item E7 in the [brief](../briefs/tool-review-2026-10.md).

### 89. Review leftovers 2026-10-21
Small bugs the Assertion Guardian review left (low severity, none blocks use).
**Done when:** each leftover in the report is fixed with a test, or dropped with a reason.
- [ ] Fix them: `/debug review leftovers 2026-10-21`
  - [x] build() clones an unreachable source twice (PR #139)
  - [x] Byte order mark refusal text, and restore skips a symlink: edit the live assertion-guardian mod, `claude plugin test`, then `bin/sync.sh` regenerates `config/patches/assertion-guardian.patch`
  - [x] `/allow-test-change <file>` for a shell refusal: find the code first
  - [ ] Concurrent Bash calls undo each other's additions: the fixing chat picked "leave it, the README says it" · waits on you
  - [ ] Spec 0068 Amended line for the refusal shape: `/architect assertion guardian blocks only removed checks`
  - [x] chain-catch owes `/develop` for a row whose text says it builds only after other rows (row 100 on 2026-10-22, after an edit of the live `settings.json` its spec names): skip a row that still waits on unmerged rows
  - [ ] `bin/install.sh` copies the commit hooks to `<repo>/<hooksPath>` when a global `core.hooksPath` is set (dry run 2026-10-22: `mkdir -p .../claude-config//home/santiago/.config/git/hooks`); it should use `git rev-parse --git-common-dir`/hooks, where the global dispatcher looks
Source: [review report](../reviews/review-2026-10-21.md) (P3 rows and Guardrails): a file with a byte order mark refused with generic text; restore writes through a symlink; build() clones an unreachable source twice; `/allow-test-change <file>` does nothing for a shell refusal; concurrent Bash calls can undo each other's additions; spec 0068 has no Amended line for the refusal shape.

## Release 10: one workflow in every chat, no runner

### 90. Retire the runner, its features in every chat · done
The `wf` runner is retired live. What it did for some chats is now a rule in every chat, the loaded text is trimmed, and risky reviews get a second claude-fb pass.
**Done when:** no `wf` link, rule or allow entry is live; the kept features switch on by condition (`rules/when-to-switch-on.md`); the changes are merged and copied live.
- [x] Build it: PRs #126 to #135, #137, #138 (retire live, `/auto-handoff` switch, 250k handoff line, allow rules, three small rules, question format, wf leftovers, handoff fixes, briefs, all chats rules, trim, fb second review); dotfiles PR #1 (global commit-msg hook)
- [x] Copy live: rules, `CLAUDE.md`, hooks, settings (17 wf rules removed by your script), `~/.config/wf` trashed
- [ ] Push the local dotfiles main (one merge commit, plus the AGENTS.md trim) · waits on you · later boxes go on
- [ ] Try `fb-ask review` on the next risky review (never run against the real claude-fb models yet)
Source: [brief](../briefs/retire-runner.md) ("Decisions 2026-10-22 (third chat)") and [brief](../briefs/context-trim-and-all-chats.md).

### 91. Handover memory · in-progress
A fresh chat after a handoff keeps every open question, shown list and agreed decision, written by a small helper into the feature's brief and checked against the old transcript.
**Done when:** spec 0069's acceptance criteria hold, and the replay of the 11 audited handoffs keeps at least as much as today's slots.
- [x] Design it (spec): `/architect handover memory` (spec [0069](../specs/0069-handover-memory.md) accepted 2026-10-22)
- [x] Build it: `/develop handover memory` (PR open, see below)
  - [x] Probe: a foreground writer agent inside a mod-started rollover finishes before the slot check; a FAIL goes back to `/architect` (FAIL 2026-10-22, the Agent tool runs the writer in the background; you picked a mod wait for running agents, spec amended; run 3 with the wait PASS; see the spec's [verify.md](../specs/0069-handover-memory/verify.md))
  - [x] `scripts/handover-memory.py` check, prune, ages, close, lint, with `--test` (also path, messages, add, done; 32 mutants red)
  - [x] Replay the 11 audited handoffs; stop on a loss (run 2 FAIL, 2 of 11 kept fewer open owner questions; you decided the slot keeps its Open questions section beside the memory, spec amended; run 3 PASS counting memory plus slot; see verify.md)
  - [x] Templates `sections.md` and `instructions.md`, writer failure line, mod tests (mod tests 148 pass, 52 mutants red)
  - [ ] Live rules: `handover-carry.md`, `check-gates.md` gate 5, `CLAUDE.md` Context, live templates, then `bin/sync.sh` (repo copies under `claude-home/` edited; copying them live is left, after the merge) · later boxes go on
- [x] Verify it: `/check verify handover memory` (AC-1 to AC-22 with can fail lines in the spec verify.md; replay run 3 PASS)
- [x] Test it: `/test handover memory` (mod tests 148, suite 149, handover-memory self checks pass; 52 mutants red)
Source: [brief](../briefs/handover-memory.md), [brief](../briefs/handoff-loss-audit.md) and [brief](../briefs/retire-runner.md).

### 92. Skills start themselves at the right moment · in-progress
Today the 9 workflow skills start only because rule text says so, and on 2026-10-22 `/scope` never ran at chat start and free form builds skipped the `/develop` chain. You want real triggers, like the JSM agentic engineering course describes.
**Done when:** each of the 9 skills has a trigger you chose (hook or rule), and a chat that skips one is caught, with a test per hook.
- [x] Design it (spec): `/architect skills start themselves at the right moment` (spec [0070](../specs/0070-skills-start-themselves.md) accepted 2026-10-22)
- [x] Build it: `/develop skills start themselves at the right moment` (PR #166, merged 2026-10-22, 1229a0b)
  - [x] Probes: Stop hook block, headless tell, mod start at chat open and after `/clear`; a FAIL goes back to `/architect` (2026-10-22: (a) to (e) PASS; finding F1 in [verify.md](../specs/0070-skills-start-themselves/verify.md): the shell start hook runs before the mod, so it applies the mod's rule itself, spec amended)
  - [x] `spec-paths --files`, then `chain-catch.py` with `--test` and its Stop hook (also `--prompt` and the AC-17 to AC-20 rules; 65 checks, each mutation checked)
  - [x] wf-handoff mod start of `/audit` and `/scope`, `workflow-start.sh` skip, mod tests (F1: the hook applies the mod's rule itself, owner 2026-10-22; one shared case list; the origin is parsed, not substring matched)
  - [x] Live rules: `handoff.md`, `skill-map.md`, `CLAUDE.md`, settings Stop hook, then `bin/sync.sh` (repo copies under `claude-home/` edited, plus `check-gates.md`, `scope-contract.md` and the UserPromptSubmit hook; copied live 2026-10-22 after PR #166; drift clean, live self checks pass) · later boxes go on
- [x] Verify it: `/check verify skills start themselves at the right moment` (AC-1 to AC-21 with can fail lines in the spec's verify.md; /review APPROVE on PR #166, its P2 and 3 security notes fixed)
- [x] Test it: `/test skills start themselves at the right moment` (mod tests 137, chain-catch, workflow-start and spec-paths self checks pass, suite 139 ok; 117 mutants red)
Source: [brief](../briefs/skills-start-themselves.md), your messages 2026-10-22 ("the 9 skills should have rules when to trigger automatically like develop or others") and [brief](../briefs/retire-runner.md).

### 93. Dashboard restructure for the setup without wf · in-progress
The wf-dash band and panes still read the retired runner's ideas. You like the dashboard and want it restructured and connected to today's setup.
**Done when:** every number and pane reads a live source of today's setup, and the design gate passes.
- [x] Design it (spec): `/architect dashboard restructure for the setup without wf` (spec [0071](../specs/0071-dashboard-now-view.md) accepted 2026-10-22)
- [x] Build it: `/develop dashboard restructure for the setup without wf` (after rows 95 and 96 merge) (PR #164, /review APPROVE, review fixes 6f49598)
  - [x] Probe `gh api graphql` PR search from the mod (a FAIL goes back to `/architect`) (PASS 2026-10-22, spec verify.md)
  - [x] Readers, Now view, band `owed N`, mod tests (26 new tests, 27 of 28 mutants red; mod tests 82 of 82 pass after the review fix)
  - [x] Let the old view key assertion change: type `/allow-test-change`, then `dashboard.test.ts:60` expects `p n a` · waits on you (allowed 2026-10-22; mod tests 81 pass)
  - [x] Confirm Plan's next group key `t` (`n` went to Now; a guessed letter) · waits on you · later boxes go on (your answer 2026-10-22: keep `t`)
  - [x] design.md and PRODUCT.md, then `design-gate` (gate pass 3 2026-10-22: PASS WITH FINDINGS, 1 should-fix for `/architect`: `checks failing` cut at 40 columns)
- [x] Verify it: `/check verify dashboard restructure for the setup without wf` (AC-1 to AC-10 with can fail lines in the spec's verify.md; open: `checks failing` and `checks pending` cut at 40 columns, a label AC-3 spells, for `/architect`)
- [x] Test it: `/test dashboard restructure for the setup without wf` (mod tests 82 of 82, suite 1136 ok, mutants in verify.md)
Source: [brief](../briefs/dashboard-restructure.md); your message 2026-10-22 ("I think the dashboard is great still just need a restructuring and connect with our updates").

### 95. Fix: auto handoff fires after /auto-handoff off, and off holds per folder · in-progress
You turned auto handoff off and a chat handed off by itself again. You also want an off to hold for every later chat started in the same folder, until you turn it on there.
**Done when:** after `/auto-handoff off`, no chat in that folder (new, cleared, resumed or forked) hands off by itself until `/auto-handoff on`; a mod test reproduces the bug red first.
- [x] Trace and fix: `/debug auto handoff fires after off` (PR #147: off was keyed by session id and dropped on an owner `/clear`; now one file per folder; 97 mod tests pass, 4 mutants red)
- [x] Merge PR #147 (merged 2026-10-22, eb42408)
- [ ] Verify it: `/check verify fix auto handoff off`
- [ ] Test it: `/test fix auto handoff off`
Source: your message 2026-10-22 ("I turned auto handoff [off] and it got done again automatically... if I start a /auto-handoff off all the next chats started after it in the same folder will be off").

### 96. Rename the dashboard mod to chip-dash · in-progress
Your tools are the "chip" family. The wf-dash mod becomes `chip-dash` everywhere (folder, plugin id, state keys, tests, chip text), command `/chip`, `/wf-dash` kept as an alias.
**Done when:** no `wf-dash` name is left in the mod except the alias, its tests pass, and you relink it after the security scan.
- [x] Rename it: `/develop rename the dashboard mod to chip-dash` (PR #148 merged 2026-10-22, e3cd82c; suite 1136 pass, mod tests 57 and 97 pass)
- [x] Relink `~/.claude/skills/chip-dash` after `skillspector scan` · waits on you (2026-10-22: scan `--no-llm`, no model key; 2 HIGH and 10 MEDIUM, all false positives: audit report prose, PRODUCT.md prose, list form subprocess calls)
Source: [brief](../briefs/dashboard-restructure.md) (name answer).

### 97. Restructure claude-config to the icm-architect folder layout · in-progress
You asked to restructure claude-config into the folder layout of RinDig's icm-architect repo. Phase 1: [0072](../specs/0072-icm-restructure/index.md); phase 2 is designed after phase 1 lands.
**Done when:** the repo follows the agreed layout, `bin/install.sh --dry-run` and the suite pass, and every live link still resolves.
- [x] Run icm-architect read only: skillspector scan of RinDig/icm-architect, install it, run its restructure mode steps 1 to 5 only (inventory, form, roles, reference report, proposed tree and migration map, nothing moved); save its output in [brief](../briefs/icm-research.md) and show the owner its tree next to ours
- [x] Design it (spec): `/architect restructure claude-config to the icm-architect layout` (spec 0072, phase 1; answers in [brief](../briefs/icm-restructure.md))
- [ ] Build it: `/develop restructure claude-config to the icm-architect layout`
  - [x] Reference check, tests split, runner archive (0072a; AC-1 to AC-5, AC-13) · PR #165: ref-check clean, suite 139 ok (5 live-script tests copied from the archive, your call after the regression check), /review APPROVE with 2 P3s fixed, see [verify](../specs/0072-icm-restructure/verify.md)
  - [x] Map cards, CLAUDE.md entry, AGENTS.md link (0072b; AC-6 to AC-10) · built on feat/0072-map-and-entry: suite 143 ok, ref-check clean, AC-9 probe commit and hook refresh left for after merge, see [verify](../specs/0072-icm-restructure/verify.md)
  - [x] Scope split (0072c; AC-11, AC-12)
- [ ] Verify it: `/check verify restructure claude-config to the icm-architect layout`
- [ ] Test it: `/test restructure claude-config to the icm-architect layout`
- [ ] Design phase 2 (spec): `/architect restructure claude-config phase 2` (after phase 1 is merged and reviewed)
Source: [brief](../briefs/icm-restructure.md); [brief](../briefs/retire-runner.md) line 13; your messages 2026-10-22.

### 98. Helper scripts the switch-on rules still lack · in-progress
`rules/when-to-switch-on.md` lists scripts not built yet: start gates (free memory, 5 hour use, cores per suite), design-check, issue reread, review-isolated, `spec-paths --overlap`, scope marker warnings. Spec [0073](../specs/0073-switch-on-helpers/index.md). Build only after rows 92, 93 and 97 phase 1 (0072a) merge: their Paths overlap.
**Done when:** each script exists with its self check, and the rule file's "Needs a script" list is empty.
- [x] Design it (spec): `/architect helper scripts for the switch-on rules` (spec 0073 accepted 2026-10-22 after a Sonnet cross check, 14 fixes applied)
- [x] Build it: `/develop helper scripts for the switch-on rules` (PR #172, /review CAUTION, all 5 findings fixed in d2d2c19)
  - [x] Part A: start-gates, `spec-paths --overlap`, two rule lines (AC-1 to AC-4)
  - [x] Part B: design-check, `plan.py --warnings`, two rule lines (AC-5 to AC-7)
  - [x] Part C: probes P2b and P2c, issue-reread, review-isolated, last rule lines (AC-8 to AC-12) · probes passed, see [verify](../specs/0073-switch-on-helpers/verify.md)
  - [ ] Install links, self checks, live rule copy, `bin/sync.sh` (AC-13, AC-14); links and self checks are in `bin/install.sh`, the live copy and the install wait · later boxes go on
- [x] Verify it: `/check verify helper scripts for the switch-on rules` (AC-1 to AC-14 with can fail lines in the spec verify.md; isolated review probed against the real claude)
- [x] Test it: `/test helper scripts for the switch-on rules` (five self checks and suite 145 ok; 42 mutants red)
Source: [brief](../briefs/switch-on-helpers.md); `claude-home/rules/when-to-switch-on.md` "Needs a script, not built yet"; your messages 2026-10-22.

### 99. Auto handoff off by itself in plain talk chats · dropped
You asked that auto handoff be off in chats that are only talk (no build), besides the on/off switch.
Dropped 2026-10-22 (your answer, tenth chat): your third chat decision stands, "Handoff in talk chats: manual only, the owner types /auto-handoff off. Nothing to build" ([brief](../briefs/retire-runner.md) line 81); row 95 makes that off hold per folder.
**Done when:** a chat with no repo work does not hand off by itself, by the condition you pick, with a mod test.
- [ ] Design it (spec): `/architect auto handoff off in plain talk chats`
Source: [brief](../briefs/retire-runner.md) second chat decisions ("still to build"); your first message 2026-10-22.

### 100. build-features workflow, shown while it runs · in-progress
A saved Claude Code workflow (`/build-features`) that builds every ready scope row whose questions are answered, one worktree agent each, with per row model and effort; running agents show as rows in the agent panel and as a count on the chip band. from spec 0072. Spec [0074](../specs/0074-build-features/index.md). Build only after rows 93 and 98 merge (it uses row 98's helpers and edits chip-dash).
**Done when:** `/build-features` builds two non overlapping ready rows to draft PRs, and both places show them while they run.
- [x] Design it (spec): `/architect build-features workflow` (spec 0074 accepted 2026-10-22 after a Sonnet cross check, 17 fixes applied; probe P1 passed: a mod sees workflow agents)
- [ ] Build it: `/develop build-features workflow`
  - [ ] Probes P2 (agent panel rows) and P3 (worktree agent builds and pushes); a P3 FAIL goes back to `/architect`
  - [ ] Skill: ready list, clashes, pick panel, start gates, workflow script (AC-1 to AC-8)
  - [ ] Review and merge loop (AC-9, AC-10)
  - [ ] Panel script, band count, rule line, live copy and `bin/sync.sh` (AC-11 to AC-13)
- [ ] Verify it: `/check verify build-features workflow`
- [ ] Test it: `/test build-features workflow`
Source: [brief](../briefs/build-features.md) (probe passed); [brief](../briefs/icm-restructure.md) "Workflows" and "Running workflows show"; your messages 2026-10-22.

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
- [ ] Verify it: `/check verify workflow builder skill`
- [ ] Test it: `/test workflow builder skill`
Source: [brief](../briefs/workflow-builder.md); [brief](../briefs/icm-restructure.md) "Workflows"; your messages 2026-10-22.

### 102. review-fix and restructure-check workflows
The two workflows you asked to be reminded of: `review-fix` (fix a PR's review findings) and `restructure-check` (the nothing broke check as one command). Built with the row 101 builder. from spec 0072. No separate spec (your answer 2026-10-22): the builder's interview is their design, seeded by the stage outlines in the [research brief](../briefs/workflow-templates.md) section 2. Starts after row 101 is built.
**Done when:** both run as `/review-fix` and `/restructure-check` on a real PR.
- [x] Design and build review-fix: `/workflow-builder review-fix` (row 101's proof step)
- [ ] Design and build restructure-check: `/workflow-builder restructure-check`
- [ ] Run both on a real PR · waits on you
Source: [brief](../briefs/icm-restructure.md) "Workflows"; your messages 2026-10-22.

### 103. Fix: a manual handoff gets the "not live" facts list
A manual `/rollover` then `/clear` gets no "not live" list in the handover: the wf-handoff mod adds it only on its auto path (`claude-home/mods/wf-handoff/hooks/register.ts:371`, `notLiveNow`). The PR #152 fix has never had a real test.
**Done when:** a handover written by a manual `/rollover` names every changed file that is not live yet, the same as the auto path, with a mod test red on the old code.
- [ ] Fix it: `/debug a manual handoff gets the not live facts list`
- [ ] Verify it: `/check verify a manual handoff gets the not live facts list`
- [ ] Test it: `/test a manual handoff gets the not live facts list`
Source: gap found in the ninth chat of 2026-10-22 (handover of that chat, next action 2).

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
