# 0055. Search helpers on Haiku, and a record of what each model costs

**Date**: 2026-10-17
**Status**: Accepted
**Paths:** `claude-home/agents/*.md`, `claude-home/rules/lessons.md`, `claude-home/rules/cheap-worker.md`, `_archive/runner/run.py`, `_archive/runner/report.py`, `_archive/runner/tests/test_model_split.py`
**Amends**: [0014](0014-runner-resilience/index.md) (each call record gains a `models` field)

## What you're agreeing to
- The code explorer and docs lookup helpers move to Haiku, the cheapest model; reviewers stay on Sonnet.
- The rule on which model a helper uses gets a Haiku line.
- Each runner call records how much each model cost, and the morning report shows a weekly split.
- No routing mod is built now. When models other than the main one cost over 15% of a week's runner spend (an upper bound, since reviewers count too), the report says so and the improvement inbox gets a "consider a routing mod" proposal for you to promote.

## Summary
Cheap, read only work should run on cheap models so your limit lasts. Today only two helpers use Haiku. This moves the two pure search helpers too, writes the rule down, and starts measuring per model cost so a later routing mod is decided by data.

## Context
Agent pins live in `claude-home/agents/*.md` (31 files, each with a `model:` line); scout and researcher are on haiku; code-explorer (`:4`) and docs-lookup (`:5`) are on sonnet. `claude-home/rules/lessons.md:6-9` never mentions haiku. Runner calls record cost and tokens (`runner/run.py:2866-2868`) but not the per model split, which each `call-NN.json` holds in `modelUsage` (seen in run feat-0047). Plan B6 (brief): a spawn routing mod only after measuring the savings. Your answer (2026-10-17): search helpers only.

## Requirements
- **AC-1** (pins): `claude-home/agents/code-explorer.md` and `docs-lookup.md` say `model: haiku`; every other agent's `model:` is unchanged. A test over all `claude-home/agents/*.md` counts files without a `model:` line (must be 0) and checks the haiku set is exactly scout, researcher, doc-updater, code-explorer, docs-lookup, printing offenders.
- **AC-2** (rule): `lessons.md` "Subagent models" reads: haiku for read only search and lookup helpers, sonnet for review and simple edits, opus only for architecture and hard debugging.
- **AC-3** (record): each call record (`runner/run.py:2827-2868`) gains `models`: `{<raw model id>: {cost_usd: modelUsage[id].costUSD, output_tokens: modelUsage[id].outputTokens}}`, keys exactly as the call's `modelUsage` returns them; absent `modelUsage` gives `null`, never `{}` or 0. The main model of a call is the key with the largest `cost_usd`.
- **AC-4** (run line): the morning report (`runner/report.py`) adds one line per run: cost by model id and the share spent on models other than each call's main model; when no call of the run has `models`, it says `model split: unknown`.
- **AC-5** (week and gate): a `week_split()` function walks `~/.local/state/wf/runs/*/run.json`, takes calls whose `started` is in the last 7 days and that have `models`, and sums cost per model id over them; the denominator is the summed `cost_usd` of those same calls. The report prints `week: non main models <p>% of $<total> (upper bound for helper cost; <k> calls without a split skipped)`, and with zero usable calls `week: unknown`, never 0%. When `p` is over 15, the report also prints `consider a routing mod (spec 0055)`. The plan nudge is a proposal in the improvement inbox, built by spec 0061 AC-4 (your answer 2026-10-17: `/sync` is a downloaded skill, so no code can live there). This spec builds no `agent.spawn` mod. The figure covers runner calls only, not your interactive sessions, and counts reviewers and other helpers too, so it overstates what moving search helpers would save.
- **AC-6** (probe, build step 1; passed 2026-10-17: a `claude -p` call that spawned scout listed `claude-haiku-5-5` as its own `modelUsage` key next to `claude-opus-5-5[1m]`): `claude -p "use the scout agent to list the files here" --output-format json` in a scratch folder; record whether `modelUsage` lists the haiku model as its own key. If it does not, AC-4 and AC-5 are not built (they would always read 0) and the spec says why.
- **AC-7** (tests): a fixture call with two models gives the exact `models` dict; no `modelUsage` gives `None`; a 7 day fixture over 15% prints the gate line and one under does not; a week with only unsplit calls prints `week: unknown`; mutation checked.

## Decision
Two pin changes, one rule line, a per model field in call records, one report line, and a written threshold for the mod.

## Rationale
Moving only pure search keeps review quality, which the lessons rule protects. The threshold turns "after measuring" into a check that can be read off the report.

## Build plan
1. Probe the `modelUsage` shape, satisfies **AC-6**
2. Agent pins and their corpus test, satisfies **AC-1**
3. Rule line, satisfies **AC-2**
4. `models` field, run line, week split and gate, satisfies **AC-3** to **AC-5**
5. Tests, satisfies **AC-7**

## Consequences
**Positive**: search helpers cost a fraction of before; the next decision has numbers.
**Negative / tradeoffs**: Haiku traces code less well than Sonnet.
**Neutral**: the live copy in `~/.claude/agents` updates through `bin/install.sh`.
