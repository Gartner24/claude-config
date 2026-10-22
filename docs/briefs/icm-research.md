# ICM restructure of claude-config: research report
*2026-10-22 | Sources: 15 icm-architect files, the ICM paper, 2 videos, 7 Claude Code doc pages, this repo | Confidence: high on what ICM says, low on whether ICM works (no benchmark)*

Owner's ideas are in [icm-restructure.md](icm-restructure.md). Every quote below was copied from the raw source by a research agent; video quotes come from auto subtitles (weak evidence).

## Executive summary
- ICM is a way to lay out folders so ONE agent reads only what each step needs. The folders are stages and workspaces, not agents. Its own words: "One agent, reading the right files at the right moment, replaces a multi-agent framework" (icm-architect SKILL.md:8).
- For a repo that later agents edit, like claude-config, ICM's own pick is the **System map** form: the existing tree stays authoritative and a `map/` shelf is added next to `docs/` (forms.md:18, system-map.md:29, forms.md:163). ICM does not prescribe moving a code repo into numbered folders.
- ICM's restructure mode never moves a file that something still points at, unless every referrer is updated in the same change, and it requires an approved migration map first (SKILL.md:79-83). In this repo about 120 files hardcode repo paths (rough count, `rg`, 2026-10-22), and `claude-home/` must mirror `~/.claude`.
- Your orchestrator idea (main chat runs parallel agents, each with its own model and effort) is NOT part of ICM: ICM is "sequential by design" and lists concurrency and branching as where it loses (core.md:88-90). But Claude Code itself supports all of it (nested agents, per agent model and effort, saved workflows run as `/name`, an agents panel row per subagent). So it is buildable, as our own layer on top of ICM folders.
- Evidence for ICM is thin: no controlled comparison, 33 self reported users, one model family (paper lines 652-655, 642-648).

## 1. What ICM is (sources agree)
- Paper: "Numbered folders represent stages. Plain markdown files carry the prompts and context that tell a single AI agent what role to play at each step" (arXiv 2603.16021, l.7-9). "Stage sequencing is the folder numbering. Context scoping is the folder hierarchy. State management is the files on disk" (l.329-331).
- Ten invariants (SKILL.md:16-27), the ones that matter here:
  - a root entry file under about 60 lines that only routes (2);
  - a `CONTEXT.md` per working folder with Inputs, Process, Outputs, Human check (4);
  - reference apart from outputs (5);
  - a human reads each output before the next step (6);
  - 2,000 to 8,000 tokens per step (7);
  - one home per fact, generated indexes never hand edited (8, 9);
  - new unit = copy a `_templates/` folder (10).
- Six forms; pick by "what is the repeating unit of work?" (forms.md:9). Pipeline, Umbrella, Record library, Knowledge bundle, Context map, System map.
- When not to: "If the whole job fits in one saved prompt, say so and don't build a workspace at all" (SKILL.md:60); "Don't over-structure" (SKILL.md:104); "Do not scaffold objects/ processes/ effects/ for a dozen files" (system-map.md:13).

## 2. Fact check of your ideas
| # | Your idea | Verdict | Why |
|---|---|---|---|
| 1 | No file per agent; folders are workflows and those are the agents | Partly right | No agent files: right. But the folder is not the agent: "One librarian, one model, walks the building" (SKILL.md:10); video 1, 03:41: the AI "becomes the agent I need based on just simply reading and navigating that folder". The model plays a role per folder. |
| 2 | Pick which workflows run; running ones show on the status bar or the agents bar | Not in ICM; buildable | ICM has no runner or UI (videos show none; no such file in the repo). Claude Code: `subagentStatusLine` draws one row per subagent in the agent panel; mods have `$.agent.list()` for the chip band. No documented mod API lists running workflow scripts (unclear). |
| 3 | Correct name: "ICM agents" | Incorrect name | ICM says **workspace** (the whole), **pipeline** (ordered stages), **stage** (`NN_name` folder), **run** (one pass) (SKILL.md:3, core.md:11,64, forms.md:11). "Workflow" is informal only. Claude Code's own word for a scripted multi agent run is **workflow** (`.claude/workflows/`, run as `/<name>`). Suggested: "workspace" for the folder, "workflow" for the Claude Code script that runs it. |
| 4 | After all questions are answered, trigger them to build; they trigger other agents with our model and effort picks | Possible, outside ICM | Paper's own setup: Opus orchestrates and delegates to Sonnet sub-agents (l.481-483, 516-520). Claude Code: subagents nest 3 deep by default, model and effort per agent in frontmatter or per call, 20 running at once, workflows 16 at once (docs: sub-agents, workflows). ICM itself is sequential and wants a human check per stage. |
| 5 | Main chat is the orchestrator | Matches the paper | "You need one orchestrating agent that reads the right files at the right moment" (paper l.32-35). |
| 6 | A rollover section for running workflows | Needed, and a real gap | Docs: a running subagent does not survive a restart (only its transcript); we saw this today. Only `claude --bg` sessions and backgrounded workflows survive closing the terminal, none survive a reboot (agent-view docs). The handover must list each running run, its worktree and how to resume it. |
| 7 | How many | Few | ICM: "Three real stages beat seven imagined ones" (SKILL.md:60). See section 4. |

### Missing from your picture
- **Human gates.** ICM's core rule is a person reads each output before the next stage (invariant 6). Your batch build skips gates by design; our tier chain (verify, test, draft PR, your merge) has to stand in for them.
- **Workflows take no input mid run** (workflows docs). `/architect` questions cannot happen inside one, so "all questions answered first" is a hard precondition.
- **Cost.** A workflow run "can use meaningfully more tokens than working through the same task in conversation" (workflows docs).
- **Restarts kill subagents.** Use workflows (resumable in the same session) or `claude --bg` sessions for long builds.
- **Overlap.** Parallel builds must not touch the same files (our `**Paths:**` rule); ICM says nothing about it.

## 3. Whole restructure vs partial vs map only
- ICM's restructure mode, in order (SKILL.md:66-85):
  1. Inventory.
  2. Find the hidden form.
  3. Classify every file (catalog, contract, factory, product, dead).
  4. Reference integrity: in vault, `../`, symlinks, and outside consumers, asked to the owner.
  5. Propose a target tree plus a migration map, then approval.
  6. Copy, verify by hash, then remove.
  7. Walk test: every old reference still resolves.
- Load bearing paths here:
  - `claude-home/` mirrors `~/.claude` (install, sync, live links, spec 0035).
  - `docs/specs/` and `docs/scope/` are the folders every JSM skill expects in every repo (`/scope`, `/architect`, `/develop`, `/sync`).
  - About 70 spec `**Paths:**` lines.
  - About 120 files that name a repo path.
  - Outside consumers: `~/.claude/skills/*` links, `~/.local/bin` links, the dotfiles submodule, the hub scopes.
- What the forms say for this repo:
  - System map: "a folder later agents must edit (code, markdown, or mixed)" (forms.md:18).
  - "The subject tree remains authoritative" (forms.md:163).
  - "Prefer a `map/` shelf next to existing orientation (`docs/`)" (system-map.md:29).
  - "The map never becomes a second spec" (system-map.md:17).
- Our inference: a whole move fights both ICM's rule (held files stay) and the JSM skills' folder names. The ICM gain (short entry, per folder contracts, change impact cards) comes from the map without moving anything. The parts worth moving are local: the retired `runner/` into an `_archive/`, and loose `docs/research/` sorted.

## 4. Proposed tree (map plus small moves; draft for your review)
```
claude-config/
  CLAUDE.md            entry file, under 60 lines, routes only (AGENTS.md stays the full rules; see open question)
  claude-home/         unchanged paths (mirror of ~/.claude); + CONTEXT.md
  bin/  scripts/  config/   unchanged paths; + CONTEXT.md each
  docs/                unchanged: specs/ scope/ briefs/ guides/ reviews/ research/
  map/                 NEW, ICM System map
    CONTEXT.md         how to use the map
    _meta/schema.md    card types
    _templates/        object.md, process.md (copied from icm-architect)
    objects/           one card per part: wf-handoff, chip-dash, rules, skills, hooks, settings, specs, scope, install
    processes/         one card per action: install, sync, handoff, docs-pr, land-a-feature, run-a-workflow
    effects/CONTEXT.md "if you change X, these also move"
  _archive/runner/     the retired wf runner, moved (it is retired live; tests stay runnable)
  .claude/workflows/   NEW, saved Claude Code workflows run as /<name> (see below)
```
Workflows (our layer, not ICM): start with 2, add only when a step repeats.
- `build-features`: for each ready scope row whose questions are answered, one worktree agent runs `/develop`, `/check verify`, `/test`, then a draft PR. Per row model and effort. Rows whose `**Paths:**` overlap never run together.
- `review-fix`: on a PR with review findings, fix the "fix now" group, rerun tests, push the fix commits.
Each one gets a process card in `map/processes/` as its ICM contract (inputs, process, outputs, human check), and a row in the handover.

## 5. Open questions for /architect
1. How far: map plus small moves (above), or a whole restructure after a full ICM inventory and migration map.
2. Entry file: ICM wants `CLAUDE.md` under 60 lines with `AGENTS.md` as a generated twin (system-map.md:31). Here `AGENTS.md` is the source and `CLAUDE.md` imports it. Keep ours, or follow ICM.
3. Which workflows first, and their names.
4. Where running runs show: the agent panel (`subagentStatusLine`), the chip band, or both.

## 6. icm-architect run on this repo (restructure steps 1 to 5, read only, 2026-10-22)
Run: clone of RinDig/icm-architect at HEAD into a new empty folder, `skillspector scan --no-llm`: 7/100, LOW, one MEDIUM (EA2 at SKILL.md:43, an interview question, false positive), no scripts. Not linked into `~/.claude/skills`: a downloaded skill belongs in `config/manifest.json` (AGENTS.md rules), so the permanent install is a build step. Its restructure mode was followed from its own SKILL.md and references. Nothing was moved.

### Step 1: inventory (tracked files, last commit, in repo files naming the area)
| Area | Files | Last touched | Referrers | What it is |
|---|---|---|---|---|
| `AGENTS.md` / `CLAUDE.md` | 1 / 1 | 10-22 / 10-14 | 113 / 99 | entry: rules and commands / one line import |
| `README.md`, `docs/architecture.md` | 1, 1 | 10-20, 10-22 | 27, many | orientation: what the repo is; runner design |
| `claude-home/skills` | 234 | 10-22 | 37 | own skills, linked live |
| `claude-home/rules` | 69 | 10-22 | 41 | rules, copied live (50 are under `ecc/`, mostly vendored) |
| `claude-home/mods` | 38 | 10-22 | 26 | wf-handoff, chip-dash, linked by hand |
| `claude-home/agents`, `hooks`, `commands`, `scripts` | 31, 8, 5, 1 | 10-15 to 10-22 | 15, 18, 4, 1 | copied or linked live |
| `bin`, `scripts`, `config` | 6, 10, 6 | 10-22 | 179, 91, 103 | install, sync, checks, manifest |
| `runner` (code) | 15 | 10-22 | 176 | the wf runner, retired live 10-22 |
| `runner/tests` | 59 | 10-22 | 87 | the WHOLE repo suite (`fast.py`), not only runner tests |
| `runner/e2e` | 7 | 10-18 | 25 | runner end to end probes |
| `docs/specs` | 231 | 10-22 | 28 | 70 or so spec folders, the decisions |
| `docs/scope/scope.md` | 1 | 10-22 | 60 | the plan: 1391 lines, about 28k tokens, 88 of 103 rows closed |
| `docs/briefs`, `research`, `reviews`, `guides` | 35, 23, 7, 5 | 10-19 to 10-22 | 55, 22, 4, 25 | chat products, research, review reports, guides |

Outside the repo, pointing in (step 4 asks these of the owner; these were found):
- 27 links in `~/.claude/skills` and `~/.claude/commands` into `claude-home/skills`, `claude-home/mods`, `claude-home/commands`.
- 3 links in `~/.local/bin` (`fb-ask`, `spec-paths`, `skill-scan`) into `scripts/`.
- `~/.claude/settings.json:18-19` names `bin/claude-config.py` and `scripts/skill-keep.py`.
- `~/projects/docs/master-list.md:4` names `docs/scope/scope.md`.
- The dotfiles submodule pointer and the `~/claude-config` link name the repo root.
- Not checked, owner to name: cron or systemd jobs, other machines, GitHub settings.

### Step 2: the hidden form
The repeating unit is a feature: scope row, then spec, then build, then verify, test, PR. That is a **record library** (specs are numbered records, `docs/scope/` the index log) wrapped around a **factory** (`claude-home/`, shipped to `~/.claude` by `bin/install.sh`). For an agent that must edit it, the form is the **System map** (forms.md:18). Name collisions a map must state once: "workflow" (our JSM chain vs Claude Code workflows), "review" (jjstack `/review` vs built in), "wf" (retired runner vs the `wf-handoff` mod), "dash" (old `wf-dash` is now `chip-dash`).

### Step 3: roles
- **Catalog:** `CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/scope/scope.md` (as index), `docs/guides/SKILLS.md` (generated).
- **Contract:** `docs/specs/*` (how each part must work), `docs/architecture.md`, `claude-home/rules/*` (how every chat must work).
- **Factory:** `claude-home/` (all), `config/`, `bin/`, `scripts/`, templates inside skills.
- **Product:** `docs/briefs/`, `docs/reviews/`, `docs/research/`, closed scope rows.
- **Leftover (not Dead):** `runner/*.py`, `runner/e2e/`. Retired live, but still referenced (see step 4).
- **Dead:** none confirmed. Every candidate has a live referrer.

### Step 4: reference integrity, the blockers
- `runner/` cannot move as a whole: `runner/tests/` is the suite for `bin/claude-config.py`, `scripts/*`, the layout and the borrowed ideas (`test_claude_config.py`, `test_skill_keep.py`, `test_skill_scan.py`, `test_spec_paths.py`, `test_layout.py`, `test_borrowed_ideas.py`, `test_move_home_chat.py`, `test_fast.py`), and `AGENTS.md` names `python3 runner/tests/fast.py` as the suite; `config/test-preferences.json:6` points there too. About 41 of the 59 test files import runner modules and would go with it. No live code imports the runner (`chip-dash/plan.py` copied its parser).
- `claude-home/` cannot move: 27 outside links, `bin/install.sh`, spec 0035 same path rule.
- `bin/` and `scripts/` cannot move: settings.json and `~/.local/bin` links.
- `docs/scope/` and `docs/specs/` cannot move: every JSM skill and `spec-paths` expect them; the master list links the scope.
- `docs/scope/scope.md` itself can split: the scope contract allows an `index.md` top file, but the chip-dash plan pane parses it, so a split needs that parser checked in the same change.

### Step 5: the skill's proposed tree and migration map (nothing moved)
```
claude-config/
  CLAUDE.md            stays a one line pointer (ICM allows it, core.md naming rule)
  AGENTS.md            cut to routing only, under 60 lines; rules and gotchas move to map/ cards
  claude-home/ bin/ scripts/ config/ docs/   unchanged paths (held, step 4)
  docs/scope/          index.md (open rows) + done.md (closed rows), if the plan pane parser follows
  map/                 NEW System map: CLAUDE.md, CONTEXT.md, _meta/schema.md, _templates/,
                       objects/ (install, mods, rules, skills, specs, scope, suite),
                       processes/ (install, sync, land a feature, handoff), effects/CONTEXT.md
  tests/               NEW home of the non runner tests (moved out of runner/tests/, suite path updated)
  _archive/runner/     runner code, e2e and its own tests, after tests/ is split out
```
| Old path | New path | Role | Referrers to update in the same change |
|---|---|---|---|
| `runner/tests/test_{claude_config,skill_keep,skill_scan,spec_paths,layout,borrowed_ideas,move_home_chat,fast}.py`, `fast.py`, `fixtures/` | `tests/` | Factory (suite) | `AGENTS.md` commands and standing answer, `config/test-preferences.json:6`, each spec `**Paths:**` naming them |
| `runner/*.py`, `runner/e2e/`, the other runner tests | `_archive/runner/` | Leftover | `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/NOTICE.md`, `bin/install.sh:91` comment, `scripts/asciify.py:24` and `scripts/fb-ask.py:174` comments, spec `**Paths:**` lines |
| `AGENTS.md` rules and gotchas | `map/objects/*.md` | Contract | none outside (the 113 referrers name the file, which stays) |
| closed rows of `docs/scope/scope.md` | `docs/scope/done.md` | Product | `chip-dash/plan.py` parser, `~/projects/docs/master-list.md:4` (keeps working if `scope.md` stays the top file) |

Next to section 4: the skill agrees on `map/` and on keeping `claude-home/`, `docs/specs/`, `docs/scope/` in place. It differs in three places: it finds `runner/tests/` is the whole suite, so the runner can only be archived after the tests are split; it adds the entry file cut (AGENTS.md to under 60 lines); and it flags the 28k token scope file as the largest single break of ICM's 2k to 8k per step rule. It proposes no `.claude/workflows/` (ICM has no workflows; those stay our layer).

## Sources
1. https://github.com/RinDig/icm-architect - README.md, SKILL.md, references/core.md, forms.md, system-map.md, reference-integrity.md, assets/templates/ (all 15 files read)
2. Van Clief, McDermott, "Interpretable Context Methodology: Folder Structure as Agentic Architecture", arXiv 2603.16021 v2, 18 Mar 2026 - read in full
3. https://www.youtube.com/watch?v=dZ8P7zevuGw - "ICM Explained (Folders Over Agents) in Five Minutes", Jake Van Clief, 2026-09-21 (auto subtitles)
4. https://www.youtube.com/watch?v=UDJmO7xyCSo - community pitch, 2026-06-14, no technical content on ICM
5. https://code.claude.com/docs/en/sub-agents.md - nesting depth 3, model and effort per agent, 20 concurrent, restart behavior
6. https://code.claude.com/docs/en/workflows.md - saved workflows, limits, cost, no mid run input
7. https://code.claude.com/docs/en/agent-view.md - background sessions survive terminal close, not reboot
8. https://code.claude.com/docs/en/plugins/mods/reference.md, api.md, interface.md, statusline.md - `$.agent.list()`, `subagentStatusLine`, render sites

## Methodology
Four parallel read only agents: icm-architect repo (curl of raw files), the paper (pdftotext of the arXiv PDF), the videos (yt-dlp auto subtitles), Claude Code docs (claude-code-guide). Repo path count by `rg` in this repo. Not read: the main ICM repo `Interpretable-Context-Methodology`, RinDig's `agentless` (says "build an agent or a team as a folder of markdown", may define agents differently), video frames, the mods TypeScript types.
