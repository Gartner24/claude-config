# Verify: search helpers on Haiku and per model cost · spec 0055

The spec is the flat file `../0055-cheap-work-cheap-models.md`; this folder only holds its verify steps.
First run: 2026-10-17, `/check verify` under `wf run`, result FAIL (one AC-5 piece not built).
Second run: 2026-10-17, after the spec moved the plan nudge to spec 0061 AC-4, result PASS. Every command step rerun: 31 agents pinned, haiku set exact; 40 real call files through `model_costs`, `{}` and absent give `None`; the run line, the scratch week line (7% of $35.17, 1 skipped) and the full `report.render` (8/2 shows the gate line, 9/1 does not) match the lines below; the 12 tests OK; full suite 980 tests OK. The live week on your real state prints `week: unknown`, correct, since every run record predates the `models` field. AC-6 is not rerun here: `claude -p` in the sandbox still says Not logged in (its own empty `modelUsage` gave `None`, as AC-3 says); the conductor's result above stands for its scope box.

## Commands
- [x] `grep -rH "^model:" claude-home/agents/` lists 31 files, all pinned; haiku is exactly code-explorer, doc-updater, docs-lookup, researcher, scout → AC-1
  can fail: a pin left on sonnet, an extra agent moved to haiku, or an agent with no `model:` line
- [x] `claude-home/rules/lessons.md` "Subagent models" reads "haiku for read only search and lookup helpers, sonnet for review and simple edits, opus only for architecture and hard debugging" → AC-2
  can fail: the rule still says sonnet for search
- [x] Real call files from run feat-0048 (`~/.local/state/wf/runs/feat-0048-*/call-*.json`) through `run.model_costs`: call-01 gives `{claude-opus-5-5[1m]: {cost_usd 8.06, output_tokens 68258}, claude-sonnet-5-5: {cost_usd 2.62, output_tokens 105508}}`; `{}` and absent give `None` → AC-3
  can fail: `model_costs` returns `{}` for an empty modelUsage (mutant seen: printed `{}`)
- [x] `report.model_line` over those 15 real split calls prints `models: claude-opus-5-5[1m] $32.22, claude-sonnet-5-5 $2.62, claude-opus-5-5 $0.33; non main 7%`; a run with no split prints `model split: unknown` → AC-4
  can fail: the main model picked wrong, so the share reads far above 7%
- [x] `report.week_line` on a scratch state with the real calls dated yesterday, one unsplit call today, and a 999 USD haiku call 10 days old prints `week: non main models 7% of $35.17 (upper bound for helper cost; 1 calls without a split skipped)` → AC-5
  can fail: the 7 day window not applied (mutant seen: `0% of $1034.17`)
- [x] `report.render` full report with an 8/2 USD week prints the `consider a routing mod (spec 0055)` line; a 9/1 week does not → AC-5
  can fail: the threshold is wrong or the line is missing (mutant `> 25` seen: line gone)
- [x] `python3 -B -m unittest test_model_split test_resilience.TestTokens test_cheap.TestReportLine` from `runner/tests`: 12 OK; TestTokens drives a real `wf demo -y` with a fake claude and reads `models` back from run.json → AC-3, AC-7
- [x] (moved) the plan nudge is now spec 0061 AC-4's inbox proposal, by your answer 2026-10-17; AC-5 here is the report line only → AC-5 · skipped
  Not built: no rule or code anywhere tells `/sync` to do this (grep for "routing mod" in `~/.claude/skills/sync`, `~/.claude/rules`, `claude-home/`, `runner/` finds only the report line).
- [x] `claude -p "use the scout agent to list the files here" --output-format json` in an empty folder lists a haiku model as its own `modelUsage` key → AC-6 (run by the conductor 2026-10-17: keys `claude-opus-5-5[1m]` 0.4629 USD and `claude-haiku-5-5` 0.0043 USD)
  Waits on you (scope box): `claude -p` says Not logged in inside the sandbox. Real evidence so far: feat-0048 call-01 lists its Sonnet helper as its own key.

## Acceptance criteria coverage
- AC-1 met · AC-2 met · AC-3 met · AC-4 met · AC-5 met (the plan nudge is spec 0061 AC-4 now) · AC-6 passed by the conductor 2026-10-17, its own scope box · AC-7 met (tests green; mutation check belongs to `/test`)
