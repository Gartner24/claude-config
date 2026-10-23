# 0077. Restructure claude-config, phase 2: lighter chats and one tools folder

**Date**: 2026-10-22
**Status**: Proposed
**Paths:** `claude-home/CLAUDE.md`, `claude-home/rules/**`, `claude-home/rules-on-demand/**`, `claude-home/hooks/skill-rules.py`, `claude-home/hooks/chain-catch.py`, `claude-home/settings.json`, `claude-home/MAP.md`, `claude-home/mods/**`, `tools/**`, `tools/bin/**`, `tools/scripts/**`, `tools/config/**`, `map/**`, `tests/**`, `.gitignore`, `README.md`, `CLAUDE.md`
**Amended**: 2026-10-22: rule map widened by the PR #205 review
**Amends:** [0072](../0072-icm-restructure/index.md) Follow-up "Phase 2"; [0070](../0070-skills-start-themselves.md) AC-12, AC-16, AC-21 (per-message reminder removed); [0073](../0073-switch-on-helpers/index.md) AC-14 (helper link sources move to `tools/scripts/`)

## What you're agreeing to
- Every chat starts with about 5k tokens of rules instead of about 13k. A rule tied to a skill loads when that skill starts, through a hook, so a skill update never wipes it. A rule tied to a situation (a merge, a commit, a "done" claim) keeps one always loaded pointer line that says which file to read.
- The per-message "/scope" reminder goes away. The chat-start scope readout and the Stop hook stay.
- `bin/`, `scripts/` and `config/` move into one `tools/` folder, with every live path updated in the same PR and no links left at the old paths.
- `docs/specs/`, `docs/scope/` and `claude-home/` stay where they are; the downloaded workflow skills hardcode them.
- Each of the two PRs passes restructure-check before it merges.

## Summary
Phase 1 built the whole tree icm-architect proposed. Phase 2 finishes the restructure in two PRs. PR A (0077a) cuts the always loaded text, adds a pointer file to `~/.claude`, drops the per-message reminder and brings the stale docs up to date. PR B (0077b) moves the three factory folders into `tools/`. Apart from the load timing of the moved rules and the dropped reminder (both owner decisions), nothing changes how anything works.

## Requirements

### PR A (0077a): lighter chats
- **AC-1** Always loaded text = `CLAUDE.md` plus every `*.md` directly in `rules/` (not `rules/ecc/`, excluded by `claudeMdExcludes`; not the `@~/.claude/private/work.md` import, which is private). At most 20,000 characters, measured by a test on `claude-home/` AND by a verify step on live `~/.claude/` after install, each printing the total on failure.
- **AC-2** `claude-home/CLAUDE.md` keeps: Approach, Output, Code Rules, The ticket is the spec, ASCII Only, Agent Behavior, Hallucination Prevention, Shell Discipline, Debugging Rules, the two review questions ("Every review answers these two first") and the three Review Rules lines ("State the bug. Show the fix. Stop.", "No suggestions beyond the scope of the review.", "No compliments on the code before or after the review."; owner decision 2026-10-22), the work.md import, and one Routing block. `rules/` keeps `lessons.md`, `no-attribution.md`, `plain-questions.md`, `new-number-replaces-old.md`, `stop-and-reset.md`. The Routing block holds the current "Route by situation" bullets cut to one line each, plus one pointer line per situation trigger (table below), each naming the file to read, for example `- Before merging a PR: read ~/.claude/rules-on-demand/when-to-switch-on.md (self-merge checklist).`
- **AC-3** Every other `CLAUDE.md` section and rule file moves, text unchanged, to `claude-home/rules-on-demand/` (section table below). `claude-home/rules-on-demand/map.json` maps skill names to files (rule map below). `tests/test_rules_on_demand.py` fails on: a file no skill or pointer line names, a mapped file that does not exist, a map key that is not in the fixed list in the test, kept equal to the map, and a line of today's `claude-home/CLAUDE.md` or `rules/*.md` that exists in neither the kept text nor `rules-on-demand/` (line homes check over both, saved from the base commit).
- **AC-4** `claude-home/hooks/skill-rules.py` reads files from `~/.claude/rules-on-demand/` (`$CLAUDE_LIVE_DIR` override for tests). On PreToolUse with matcher `Skill` it takes `tool_input.skill`; on UserPromptSubmit it takes the first token of `prompt` when the prompt starts with `/` directly followed by a name (`/architect foo bar` gives `architect`; `/ architect` gives nothing), lower cased. Matching: the exact name first; for `plugin:skill`, only an exact `plugin:skill` key matches (no fallback to the part after the colon, so `code-review:code-review` does not load the `code-review` rules unless mapped). It prints `hookSpecificOutput.additionalContext` with each mapped file under a `# rules for /<skill>: <file>` line. A typed skill that the model then also starts gets the rules twice (accepted, no dedupe). An unknown skill or any error prints nothing and exits 0. Self check `--test`, run by install verify.
- **AC-5** Remove the reminder: the UserPromptSubmit `chain-catch.py --prompt` entry in `claude-home/settings.json`, `prompt()` and its five AC-16 self checks in `chain-catch.py`, and the text citing it in `claude-home/CLAUDE.md`, `rules/skill-map.md` and `rules/scope-contract.md`. Chat-start `/audit` and `/scope` (wf-handoff mod) and the Stop hook stay.
- **AC-6** `claude-home/MAP.md` (under 10 lines: this tree comes from `~/claude-config`; edit `claude-home/` there and run install; the map is `~/claude-config/map/CLAUDE.md`) is copied by install to `~/.claude/MAP.md`, is in `COPIED_FILES` for drift and sync, and is never auto loaded.
- **AC-7** Install: `rules-on-demand/` joins the mkdir and copy lists (`bin/install.sh:37`, `:43-46`); a file in live `~/.claude/rules/` or `rules-on-demand/` with no repo source is moved to `~/.claude/backups/rules/<date>/` and named in the install output (so moved rules stop auto loading live); drift and sync know the folder. `skill-rules.py` joins the copied hooks list.
- **AC-8** `docs/architecture.md` describes today's system (chat driven workflow, hooks, mods, workflows, install and sync); the runner design text moves to `_archive/runner/docs/architecture.md`. `README.md` has no present tense runner text. `map/` cards name `rules-on-demand/` and the skill rules hook.
- **AC-9** `/restructure-check` runs on the PR. Pass = its report's verdict line lists no "needs a look" item other than differences this spec names (the moved rules, the removed reminder and its checks, the new hook and folder, the rewritten docs). Any other "needs a look" item blocks the merge until fixed or the owner accepts it.

### PR B (0077b): one tools folder
- **AC-10** `bin/`, `scripts/` and `config/` move with `git mv` to `tools/bin/`, `tools/scripts/`, `tools/config/`. The repo root holds no `bin`, `scripts` or `config`, and no link at those paths.
- **AC-11** Every live referrer moves in the same PR, including: `claude-home/settings.json` hook commands; the `~/.local/bin` link sources in install (`install.sh:106-129`, spec 0073 AC-14); install's own paths (`:14` root, `:55`, `:82`, self checks `:279-307`); the installed git hooks under `.git/hooks/` (refreshed by install); `claude-home/` rules, rules-on-demand, skills, hooks and mods (`mods/wf-handoff/templates/*.md`, `mods/chip-dash/*.test.ts`); `map/` cards; `tests/`; both `CLAUDE.md` files; `README.md`; `docs/guides/`; `.gitignore`; `tools/config/test-preferences.json` contents; spec `**Paths:**` lines (bookkeeping). Old briefs, reviews, research, `docs/scope/done.md` and `_archive/` keep the old paths as history.
- **AC-12** Every script that finds the repo root from its own location goes one level further (`Path(__file__).resolve().parent.parent` becomes `.parents[2]`, `install.sh`'s "one folder up" becomes two); a test greps the moved files for `parent.parent` and `dirname "$0"/..` and checks each resolves to the repo root.
- **AC-13** A final test greps `claude-home/`, `map/`, `tests/`, `tools/`, both `CLAUDE.md` files, `README.md` and `docs/guides/` for `bin/`, `scripts/` and `config/` path uses not under `tools/`, and prints each hit; the count is 0.
- **AC-14** Commands, in order: `python3 scripts/ref-check.py snapshot --out <tmp>/before.json` on the base; the move; `python3 tools/scripts/ref-check.py verify --snapshot <tmp>/before.json --map-from-git origin/main` (check the real flag names at build and write them here); `tools/bin/install.sh --dry-run`; the real install; `claude-config.py drift` prints `drift: none`; `hook-files` clean; the suite.
- **AC-15** `/restructure-check` on the PR, pass rule as AC-9 with the moved paths as the named differences.

## Section and rule homes (AC-2, AC-3)
| Today | Goes to |
|---|---|
| `CLAUDE.md` Approach, Output, Code Rules, Ticket is the spec, ASCII, Agent Behavior, Hallucination, Shell, Debugging, two review questions | stays |
| `CLAUDE.md` Workflow intro, Route by situation | Routing block (one line each) |
| `CLAUDE.md` Decision gate, Todos, Context, Never in a repo | `rules-on-demand/workflow.md`; Routing keeps "a value with no named source: /architect", "todos in chat: /scope each", "repo holds no .gstack/, jjstack/, .superpowers/, settings.local.json" |
| `CLAUDE.md` Review Rules "Which reviewer" and "Which one, never two" | `rules-on-demand/reviewers.md`; Routing keeps "before landing your own repo: /review; small own diff: /code-review; never both /review and /review-stack" |
| `CLAUDE.md` UI / design pipeline | `rules-on-demand/design-pipeline.md`; Routing keeps "any UI build or restyle: run the design skill" |
| `CLAUDE.md` Language Rules | `rules-on-demand/workflow.md` |
| `rules/` all files not kept by AC-2 | `rules-on-demand/<same name>` |

## Situation pointer lines (AC-2)
| Situation | Pointer to |
|---|---|
| Before merging a PR | `when-to-switch-on.md` (self-merge checklist) |
| A PR you opened has review comments | `when-to-switch-on.md` (review comment loop), `review-fix.md` |
| The branch has commits by someone else; reviewing someone's PR | `when-to-switch-on.md` |
| "I am leaving", "finish it", "do these features", two ready features | `when-to-switch-on.md` |
| Any commit, branch, push or PR | `branch-pr.md` |
| Before saying fixed or done; a tool refusal | `handoff.md` ("Not live is not fixed") |
| Free form build or fix tied to a scope row | `handoff.md` (counts as /develop) |
| Showing the owner a report, list or pending question | `handover-carry.md` |
| A risky change under review | `second-review.md` |
| Input over about 20,000 characters, or many items to sort | `cheap-worker.md` |
| Picking a skill | `skill-map.md` |
| Writing a scope box from any skill | `scope-contract.md` |

## Rule map (AC-3, skill start loading)
| Skill | Files |
|---|---|
| scope | `scope-contract.md`, `skill-map.md`, `workflow.md`, `check-gates.md`, `when-to-switch-on.md`, `handoff.md` |
| architect | `spec-gate.md`, `standing-answers.md`, `fresh-chat-after-architect.md`, `runner-handoff.md`, `check-gates.md`, `branch-pr.md`, `scope-contract.md`, `workflow.md`, `handoff.md` |
| develop | `branch-pr.md`, `handoff.md`, `check-gates.md`, `when-to-switch-on.md`, `scope-contract.md`, `workflow.md` |
| check, test | `check-gates.md`, `when-to-switch-on.md`, `standing-answers.md`, `scope-contract.md`, `handoff.md` |
| sync | `check-gates.md`, `handover-carry.md`, `when-to-switch-on.md`, `scope-contract.md`, `spec-gate.md`, `standing-answers.md`, `handoff.md` |
| audit | `standing-answers.md` |
| debug | `handoff.md` |
| review, review-stack, review-fix, jj-security-review, security-review, code-review | `reviewers.md`, `review-fix.md`, `second-review.md`, `cheap-worker.md` |
| rollover, save-and-clear, resume-from-clear | `handoff.md`, `handover-carry.md`, `runner-handoff.md`, `workflow.md` |
| workflow-builder, build-features, review-fix, restructure-check | `branch-pr.md`, `when-to-switch-on.md` |
| design, design-gate, assets | `design-pipeline.md` |
| write, pr | `branch-pr.md` |
| document | `branch-pr.md`, `standing-answers.md` |

Map keys are checked against a fixed list inside `tests/test_rules_on_demand.py`, kept equal to `map.json` (AC-3): a key added to the map without adding it to the list fails, and so does a list entry missing from the map. The test does not read `claude-home/skills/` or `config/manifest.json`.

## Decision
Keep `docs/specs/`, `docs/scope/` and `claude-home/`; move `bin/`, `scripts/`, `config/` into `tools/`; load skill rules through a hook and situation rules through pointer lines. Options and reasons: [rationale.md](rationale.md).

## Build plan
1. 0077a, branch `feat/0077-lighter-chats`. First probe P3 (verify.md): does a command the wf-handoff mod sends at chat start (`$.command.run`) reach UserPromptSubmit? A FAIL makes the mod itself print `scope-contract.md` and `skill-map.md` into its start text instead (no other change), recorded in verify.md. Then: measure today's load (save the number); `skill-rules.py` with `--test`; move sections and files per the tables; Routing block and pointer lines; AC-3 test; AC-5 removals; `MAP.md`; install, drift and sync changes; docs. Suite, dry run, install on a yes, the live AC-1 measure, `/restructure-check`, PR. (AC-1 to AC-9)
2. After 0077a is live: a fresh chat; type `/architect x`, then in another fresh chat ask a plain question; the rules arrive only in the first. · waits on you
3. 0077b, branch `feat/0077-tools-folder`, cut after 0077a merges (both edit rule paths): AC-14 commands in order, with AC-11 to AC-13. `/restructure-check`, PR. (AC-10 to AC-15)

## Consequences
- **Good**: about 8k fewer tokens in every chat; the code rules and the two review questions stand out; a root that reads like the map's roles.
- **Bad**: a situation rule now depends on Claude following its pointer line (owner accepted, 2026-10-22, "pointer lines stay loaded"). Old notes naming `bin/` or `scripts/` fail once with "no such file".
- **Neutral**: one more hook (`skill-rules.py`) to maintain; its self check runs in install verify.

## Follow-up
- Spec status lines of 0072 (phase 1 done), 0074 and 0076 are bookkeeping for `/sync`.

## Rationale
See [rationale.md](rationale.md). Probes: [verify.md](verify.md).
