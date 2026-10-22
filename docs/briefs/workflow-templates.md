# Workflow templates research (scope row 101)
*2026-10-22 | 13 web sources plus a read of our own skills and the ICM sources | Confidence: medium (few public scripts exist yet; several read only in part)*

## Agreed so far, do not ask again
- 2026-10-22: the owner chose to run this research now, in the same chat, focused on the two questions of [icm-restructure.md](icm-restructure.md) "Workflows".

## Executive summary
Claude Code's Workflow tool is new; public scripts are few and mostly single author. The patterns that recur are stable: fan out finders, deduplicate in plain script code, verify each finding with a skeptic that defaults to "not real", compute the verdict from counts, and give every agent a schema. Edits run in per agent worktrees; read only agents skip them. A workflow cannot ask the owner anything mid run, so every human gate sits outside the script (a skill before or after it). ICM itself is sequential and has no script concept: its contribution is the stage contract (Inputs, Process, Outputs, one Human check, Do NOT load), which maps to a process card plus a script whose phases match the card's stages.

## 1. Existing templates worth borrowing (ranked)
| # | Name | What it does | Pattern | Source (read) |
|---|---|---|---|---|
| 1 | audit-fanout | 8 finder agents by dimension, dedup in code, one refuter per dimension, synth; a failed finder blocks CLEAN | parallel find, dedup, parallel refute, synth; verdict from counts | [S6](https://github.com/Canhada-Labs/ceo-orchestration/tree/main/.claude/workflows) (full) |
| 2 | Official prompt shapes | audit many files, fix until a check passes, migrate each file in an isolated copy, review every changed file, research, find until the list stops growing | prompts plus one minimal `pipeline()` example | [S1](https://code.claude.com/docs/en/workflows.md) (full) |
| 3 | deep-review-flow | 6 competency reviewers, dedup, one skeptic per finding (default real=false), triage FIX/DEFER/ACCEPT | review, verify, triage | [S8](https://github.com/AnastasiyaW/codex-claude-code-config/tree/main/workflows) (full) |
| 4 | oversee-dispatch | per issue: plan, critic, revise (3 critiques, 2 revises max), human gate; second run: execute in worktrees, verify | review and fix loop, build fan out, per stage model | [S7](https://github.com/optave/ops-codegraph-tool/blob/main/.claude/workflows/oversee-dispatch.js) (part) |
| 5 | /deep-research (bundled) | searches by angle, cross checks, votes per claim | parallel search, verify, vote, synth | S1 (doc only) |
| 6 | Bun port chain | map, write each file with two reviewers, fix until build and tests are clean | migration fan out plus fix loop | [S4](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code) (full; scripts not found) |
| 7 | workflow-worker / gate | parallel workers on a plan step, one serial gate running tests picked by git diff; claims about 80% fewer tokens | parallel build, serial gate | [S13](https://news.ycombinator.com/item?id=49587379) (single author, unverified) |
| 8 | council-audit, sota-scan, retrospection, nightly-hygiene, codd-greenfield | judge panel across vendors; research sweep; candidate tournament; scheduled read only sweep; sequential phases | various | S6, [S9](https://github.com/MerlijnW70/sota-scan), [S11](https://github.com/wbopan/retro-harness), [S10](https://github.com/yohey-w/codd-dev/tree/main/examples/claude_workflows) (headers only; S10 uses an older API shape) |

Recurring rules (S1, S4, S6, S7, S8): schema on every agent; filter nulls and never report a failed lane as clean; bounded fix rounds with a no progress stop; worktree only for agents that edit; per stage model to cut cost; run a small slice first; no `Date.now()`, `Math.random()`, bare `new Date()` or `import()`; at most 16 agents at once, 1000 per run. Cost warning (S12, anecdotal): 62 Opus agents hit a 5 hour cap in 18 minutes.

## 2. Workflows we can make from our own skills (ranked by value for effort)
| # | Name | Skills, in order | Fans out over | Stays with the owner | Guess: how often |
|---|---|---|---|---|---|
| 1 | build-features | develop, check verify, test, document pr | ready scope rows | pick, review, merge (spec 0074) | weekly |
| 2 | review-fix (row 102) | sort findings by `rules/review-fix.md`; fix per file group (worktree, test, mutation check); suite; check verify, test; sync | file groups that share no file | ask group, push, merge; HIGH left after round 2 blocks | after most PRs |
| 3 | restructure-check (row 102) | capture outputs on base and HEAD (install dry run, drift, docs regen, every `--test`, file and link inventory), diff, suite, spec-paths | surfaces, base and HEAD | a real difference: debug or accept | during restructure phases |
| 4 | monthly-ops cycle | Care base plus each paid add-on (seo-ops cycle, content, GBP, reviews, backlinks), then the report | one agent per add-on per client | retainer scope, approving the queue, sending the report | monthly per client |
| 5 | design-audit sweep | design-gate (and cro on marketing pages) per surface, merged fix list | surfaces and viewports | which fixes to take | per site delivery |
| 6 | site-launch gate | production audit, accessibility, security review, Lighthouse, SEO guide check, one report | the five checks | deploy, sitemap, offer | per launch |

Not worth wrapping: review-stack (already fans out inside), asset batches (generation bills), and the interactive skills whole: design, brand-system, architect, scope ask the owner mid run. Skills that ask mid run (AskUserQuestion): design, assets, brand-system, scope, architect, develop (on an owed decision), test (no preferences file), document (doc type), review. Inside a workflow they need the standing answers given up front, or the agent returns `skipped: needs a decision` (spec 0074 AC-7). check needs the mode word and an `app start` line.

## 3. What an ICM style workflow builder should produce
ICM: "numbered folders carry sequencing, hierarchy carries context scoping, plain markdown files carry state" (icm-architect SKILL.md:8); a stage contract has Inputs (exact paths), Process, Outputs, exactly one Human check, and a Do NOT load line (references/core.md); a stage's context is about 2,000 to 8,000 tokens; "Nothing moves to the next stage until a person has read the output of the last one" (templates/CLAUDE.md); "If the whole job fits in one saved prompt, say so and don't build a workspace at all" (SKILL.md, Build step 3). ICM is sequential; parallel fan out is our layer on top (core.md lists automated mid pipeline branching and high concurrency as where ICM loses).

Proposal for one workflow `<name>` (inference, not an ICM statement):
- `map/processes/<name>.md`: the contract card (stages, inputs, outputs, one human check each, Do NOT load, Hits / Does not hit), under about 500 tokens. Single home of the instructions.
- a Workflow script whose `phase()` titles equal the card's stages; each agent prompt says "read map/processes/<name>.md stage N, then do it".
- one script per human gate (the docs: no mid run input; for sign off between stages, run each stage as its own workflow), the gate itself in a skill or the chat.
- per run outputs written by agents (scripts have no file access), so the filesystem shows the state.
- checks on its own output: walk test (a cold agent finds the card and names the next stage in 2 reads), every input path exists, card and script stage names match, static script checks (meta literal, no banned calls, schema where the result is read, nulls filtered), Paths overlap before any parallel edit, a one item dry run.
- if the job is one prompt, it writes a skill instead.

## 4. Open questions for the builder's /architect
1. Gate granularity: one workflow per human gate, or one per job ending at a draft PR.
2. Contract home: a process card in `map/processes/` (needs row 97 phase 1's `map/`) or a stage folder tree per workflow.
3. Where scripts live: a skill folder passed by `scriptPath` (spec 0074's choice) or `.claude/workflows/` (the docs say the save dialog refuses a symlinked `.claude/workflows`; our `~/.claude` is partly links).
4. Non repo work later (marketing, publicity): per run outputs under `~/.claude/state/<area>/`.
5. Model and effort per stage: a shared table, or chosen per run.

## Sources
1. S1 Claude Code docs, Workflows: https://code.claude.com/docs/en/workflows.md (full)
2. S2 Claude Code docs, Agents: https://code.claude.com/docs/en/agents.md (full)
3. S3 Claude Code docs, Worktrees: https://code.claude.com/docs/en/worktrees.md (isolation sections)
4. S4 Introducing dynamic workflows: https://claude.com/blog/introducing-dynamic-workflows-in-claude-code (full)
5. S5 Anthropic, multi agent research system: https://www.anthropic.com/engineering/multi-agent-research-system (passages)
6. S6 ceo-orchestration workflows (audit-fanout, council-audit, nightly-hygiene)
7. S7 ops-codegraph-tool oversee-dispatch.js
8. S8 codex-claude-code-config workflows (deep-review-flow.js)
9. S9 sota-scan; S10 codd-dev examples; S11 retro-harness retrospection.js
10. S12 Hacker News discussion of S4: https://news.ycombinator.com/item?id=48311705
11. S13 Hacker News, cutting token spend on dynamic workflows: https://news.ycombinator.com/item?id=49587379
12. RinDig/icm-architect: SKILL.md, references/core.md, forms.md, system-map.md, templates (raw files, full)
13. Own skills: `~/.claude/skills/*/SKILL.md` front matter and outlines, `rules/review-fix.md`, spec 0074

## Methodology
Three parallel read only agents (Sonnet): web templates (curl, gh, Hacker News Algolia API), own skill inventory (local files), ICM builder (raw GitHub files, Claude Code docs). `gh search code` for `export const meta` found nothing; searching `.claude/workflows` found the scripts. No Bun workflow scripts were found; that chain is described second hand. ICM paper quotes were not reread (second hand from icm-research.md). Every frequency in section 2 is a guess.
