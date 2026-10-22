# Row 62: making the wf runner improve itself

## 1. What the runner already records (sensors)
- run.json, 50 runs sampled in ~/.local/state/wf/runs (read with a script): keys repos, features, calls, decisions, caps, waited_s, limit_wait, outage_waits, notes, cost_usd, tokens. Stop reasons: queue_done 47, interrupted 3.
- Per call (runs/*/run.json "calls"): command, duration_s (40.6 s for /check verify, 506.6 s for /test in one run), exit_code, subtype, num_turns, cost_usd, tokens, denials[], marker (can_fail_checked), retry_of, resumes, decision.
- Per feature: outcome ("blocked"), detail, debug_attempts, counted calls, cost.
- Park/stop classes, ~/claude-config/_archive/runner/run.py:273-282. PARKS: verify_failed, blocked, denied, debug_touched, no_progress, call_error, call_timeout, budget, max_calls, manual_box, waiting, no_command, no_feature, app_failed, design_gate, unchecked, issue_changed, stack_deep, paths_overlap. REPO_STOPS: branch_changed, autopilot_off, scope_unreadable. RUN_STOPS: interrupted, run_limit, usage_limit, spawn_failed, guard_changed, ping_failed, internal_error, app_port_busy, api_outage, crash_loop, auto_off.
- queue.json keeps parks and decisions between runs; log.txt, call-NN.json, report.txt (~/claude-config/docs/architecture.md line 23).
- Existing comparator, in-run: "crash_loop when two features in a row park with the same call error" (architecture.md invariant 8). Retake logic (run.py ~826-860) clears a park when its cause changed (new commit, new setup).
- Existing cross-session loop, row 46: jjstack hooks log skill misses to ~/.jjstack/skill-misses.jsonl; ~/.claude/skills/jjstack/bin/jjstack-skill-miss-report states "HOT - >=10 misses concentrated in <=5 skills in the last 24h ... COLD - ... description sharpening is working". That is a full sensor + comparator + threshold, but no actuator: a human reads it.

## 2. Systems view
- Balancing loops that exist: caps, timeouts, crash_loop, park-and-retake, guard checks. They stabilize one run. None carries information from run N to run N+1 about the runner itself (single-loop only: errors fixed, rules never questioned).
- Missing sensor aggregation: nothing counts park reasons across the 50 runs, nothing ranks denials (denials[] is recorded per call but never summed), nothing tracks cost or duration per box type, nothing compares retry rate per command.
- Missing comparator: no baseline ("verify median 40 s, cost 1.5 USD"); no alarm on drift.
- Missing actuator: no path from a finding to a scope row. Double-loop (change the rule, not the action) is entirely human.
- Ashby's requisite variety (general law, unverified for this repo): a regulator needs at least as many responses as the disturbances it must absorb. Disturbance types here: about 40 reason codes. Responses: park and ask. A proposer that maps a repeated reason code to a specific proposal type raises variety without touching the guards.
- Reinforcing-loop risk: a runner that edits its own guards or tests removes the balancing loop that protects it (Goodhart: it can make its own metric pass).

## 3. Prior art (fetched via arxiv API, export.arxiv.org)
- Reflexion, https://arxiv.org/abs/2303.11366: "reinforce language agents not by updating weights, but instead through linguistic feedback ... maintain their own reflective text in an episodic memory buffer". Maps to: per-failure note stored, fed to the next attempt. Not weight changes.
- Self-Refine, https://arxiv.org/abs/2303.17651: same model "as the generator, refiner, and feedback provider". Maps to a within-call loop; our /check and /test already do it.
- Voyager, https://arxiv.org/abs/2305.16291: "an ever-growing skill library of executable code" plus "environment feedback, execution errors, and self-verification". Maps to promoting a repeated fix into a skill or rule.
- Agent Workflow Memory, https://arxiv.org/abs/2409.07429: "inducing commonly reused routines, i.e., workflows, and selectively providing workflows to the agent". Maps to per-repo recipes for common parks (e.g. app_failed).
- ADAS, https://arxiv.org/abs/2408.08435: agents "defined in code" and searched by a meta-agent. Needs a benchmark we lack; reject.
- Darwin Godel Machine, https://arxiv.org/abs/2505.22954: "iteratively modifies its own code ... and empirically validates each change using coding benchmarks"; SWE-bench 20.0% to 50.0%; "All experiments were done with safety precautions (e.g., sandboxing, human oversight)". Gain came from an archive plus a benchmark. We have no held-out benchmark for the runner, so self-modification would be unvalidated.
- Not verified: SWE-agent/OpenHands trajectory analysis, Claude Code /insights (firecrawl rate limited; HN search found nothing relevant). HN threads on self-improving coding agents exist (e.g. https://news.ycombinator.com/item?id=46896117) but I did not read them.

## 4. Missing loops to build (proposal, never auto-applied)
1. Aggregator (read only): `wf insights` style script over runs/*/run.json: park reasons by count, denials by path/tool, cost and duration by box type, retries, unchecked/no_progress rates, per repo. Pure stdlib, no model.
2. Comparator: rule table like the miss report: reason X in >=3 of last 10 runs = HOT. Same HOT/WARM/COLD shape already used in jjstack-skill-miss-report.
3. Proposer: for each HOT finding, write one scope row (Source: the insight file) or a brief under docs/briefs/. Examples: repeated `denied` on one path = row "decide whether this write path joins the allow list" (a decision, goes to /architect); repeated `call_timeout` on /test = row "raise or split"; "brief not read: not in a briefs folder" note seen in two recent runs (runs/feat-0049, feat-0050 notes) = row to fix brief lookup.
4. Memory of fixes (Reflexion/AWM style): a per-repo recipes file of park -> fix that worked, read as context by /debug. Text only.
5. Closing the loop: next aggregation checks whether the HOT reason dropped after the row shipped; if not, the row reopens (double-loop signal).

## 5. Idle time
When the queue is empty (queue_done) and usage budget remains: run the aggregator (zero cost), then optionally one cheap fb-ask summarize/triage pass on log.txt files (cheap-worker.md; only repos on fb-ok.txt, never client repos). Never start builds from proposals; proposals wait as scope rows for the human's /scope.

## 6. Safety limits
- Proposals are text files and scope rows only. No edits to guard hooks, deny lists, permission-floor, settings.json, ~/.claude, push guard, or the aggregator itself (invariants 1-3 and 8 in architecture.md).
- Proposer writes only to docs/scope rows or docs/briefs/ in a worktree; a human ticks and runs them. Row cap per run (suggest 3) to avoid flooding.
- Anything touching guards goes through /architect and the human, same as today ("Never decides design", invariant 2).
- Proposer must cite run ids and file:line; a finding without a citation is dropped.

## 7. Recommendation: build our own, small, adapt ideas
- Adapt: Reflexion/AWM idea (stored text lessons fed to later attempts) and the HOT/WARM/COLD thresholds from row 46.
- Reject: DGM and ADAS self-modification. Reason: they rely on a held-out benchmark for validation; we have none, and the threat model forbids self-edited guards.
- Adopt nothing off the shelf; no verified tool found.
- Effort: aggregator + comparator about 150-250 lines stdlib Python plus tests, about 1 feature (one /architect spec, then runner build). Cost: zero tokens for sensors; proposer can be a template (no model) at first. Risk: low, read only plus scope row writes.
- First step: spec "run insights" with the aggregator only; measure for one week before adding the proposer.
