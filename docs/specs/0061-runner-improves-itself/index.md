# 0061. The runner learns from its runs, and a weekly review of your sessions

**Date**: 2026-10-17
**Status**: Accepted
**Paths:** `runner/insights.py`, `claude-home/skills/improve-my-system/extract.py`, `runner/run.py`, `runner/report.py`, `runner/wf.py`, `runner/tests/test_insights.py`, `claude-home/skills/improve-my-system/**`
**Amends**: [0018](../0018-morning-report/index.md) (the session start report line gains a proposals count), [0020](../0020-one-command-wf/index.md) (adds `wf insights`)

## What you're agreeing to
- At the end of every runner run, a small reader goes over past runs, keeps a long running summary, and finds problems that repeat (the same park, the same denied file, the same step timing out).
- Each repeating problem becomes at most one short proposal in an inbox file; at most 3 new ones per run. Nothing is changed by it; you promote good ones to plan rows.
- Your session start shows "wf proposals: N new" with the file path when there are some.
- A new `improve-my-system` skill you run by hand (weekly) reads only your own projects' session history on the laptop, with keys, emails and private names removed first, and reports repeated corrections, context you keep re-explaining, skills you should have, jobs to automate, and stale rules, each backed by 3 or more sessions and a quote. Nothing is applied without your yes.
- It never edits guards, deny lists, settings, `~/.claude` or the plan.

## Summary
The runner already records everything about each run, but nothing learns from it, and run folders are pruned after 50 runs. This adds a reader that keeps a compact history, sets baselines and proposes fixes for repeating problems. The skill, from the guide you shared, does the same for your interactive sessions.

## Requirements
- **AC-1** (read only): `runner/insights.py` reads `~/.local/state/wf/runs/*/run.json` and writes only under `~/.local/state/wf/insights/`.
- **AC-2** (history outlives pruning): the run id is the run folder's name (`<name>-<stamp>-<pid>`, as `prune_runs` uses, `run.py:4724`). Each call scans every run folder and appends one summary line for every run id not yet in `insights/history.jsonl`, skipping runs whose `ended` is null (still running); so a killed run is picked up later. Fields: run id, `ended`, `stop_reason`, `cost_usd`, per command kind (the first word of `calls[].command`, e.g. `/develop`, `/check`) the `duration_s` and `cost_usd` values, park reasons (`features[].outcome` values in the `PARKS` set, `run.py:266`), denials as tool plus path (`calls[].denials[]`: the `file_path` of a file tool's input, else the tool name alone), and retries (calls whose `retry_of` is set). A corrupt `run.json` is skipped and counted. Each line is one `O_APPEND` write.
- **AC-3** (baselines): over the last 10 runs in history: median and p90 of `duration_s` and `cost_usd` per command kind, skipping nulls (never counted as 0), and, per park reason, denied tool plus path, and `call_timeout` park, the number of runs that contain it. In 3 or more of the last 10 runs it is HOT. Only HOT is acted on; `wf insights` prints the counts.
- **AC-4** (proposals): each HOT finding gives at most one proposal in `insights/inbox.md`, from fixed templates (repeated denied path, repeated `call_timeout` on a command kind, repeated park reason), each citing the run ids and the field it came from, and naming a tool and path only, never the denied command text; a finding without run ids is dropped; at most 3 new per run; each proposal is keyed by a hash of its template and subject and never repeated. The inbox is rewritten through a temp file and `os.replace`.
- **AC-5** (when): called right after `report.end_of_run` inside `try`; a failure logs one warning line and never changes the exit code. `wf insights` runs it by hand and prints the summary; `wf insights --seen` adds the hashes of the proposals now in the inbox to `insights/seen.json`; unseen means a hash not in that file. Insights runs before `prune_runs` (`run.py:3958`).
- **AC-6** (shown): `wf report --hook` adds `wf proposals: N new (<path>)` when the inbox has unseen proposals, even with no report pending; never the proposal text; silent while locks are held, as today.
- **AC-7** (/insights, optional): if `~/.claude/usage-data/report.html` exists, its text with tags stripped and cut to 4,000 characters goes into a "from /insights (data)" section of the `wf insights` print only, never the inbox or the hook; absent, no section and no error.
- **AC-8** (never writes elsewhere): a test runs the reader with a temp HOME holding fixture runs and a fake `~/.claude`, lists every file before and after, and asserts every new or changed file is under `~/.local/state/wf/insights/`.
- **AC-9** (history skill): `claude-home/skills/improve-my-system/SKILL.md`, `disable-model-invocation: true`, with a stdlib script `extract.py` beside it. Projects read: only the folders listed in `~/.claude/private/history-allow.txt` (one absolute path per line; the build seeds it with your own repos, your personal folder, `~/claude-config` and `~/.claude`; your answer: only your own projects). `extract.py` maps each `~/.claude/projects/<encoded>` folder back to its path and skips any not on the list, skips subagent files, and for sessions since the last report keeps the project, date, your typed messages and tool names, after replacing token shapes (`sk-`, `ghp_`, `xox`, long hex and base64 runs), email addresses and every left hand name in `~/.claude/private/names.txt` with `[REDACTED]`, before any model reads it. It writes to `~/claude-improve/extract/`, refusing to run if `~/claude-improve` is inside a git repo. The skill reads the extracts project by project with subagents, reads your CLAUDE.md, rules and skills, and writes `~/claude-improve/report.md`: the numbers, top recurring corrections each with the exact rule and its file, context to write once, up to 7 skills ranked by occurrences times time, automations, cleanup, and fixed since last report. Every finding needs 3 or more sessions, their dates and one short quote; fewer goes under "too early to tell". It also adds up to 3 of its top findings to `insights/inbox.md` with the same hash rule, as one line each with a pointer to the report. It ends with a 15 line summary, asks which items to apply, changes no file until you name them, and never copies the report into a repo.
- **AC-10** (tests): 12 fixture runs give the expected HOT findings; a run with `ended` null is not appended and is appended once it ends; a pruned run stays in history; a corrupt run is skipped; the cap of 3 holds; a repeated finding is not proposed twice; the hook line appears and disappears with `--seen` and reappears for a new proposal; `extract.py` on a fixture with a names entry, a fake key and an email outputs none of them, and skips a project not on the allow list; mutation checked.

## Decision
A stdlib reader in the runner with template proposals, plus a by hand skill for session history. No model call in the runner part.

## Build plan
1. `insights.py`: history, baselines, proposals, write fence, satisfies **AC-1** to **AC-4**, **AC-8**
2. End of run call, `wf insights`, hook line, `/insights` read, satisfies **AC-5** to **AC-7**
3. `improve-my-system` skill, satisfies **AC-9**
4. Tests, satisfies **AC-10**

## Consequences
**Positive**: repeating runner problems surface without you looking; your interactive habits get the same review on demand.
**Negative / tradeoffs**: template proposals catch only the patterns they know; the history review uses some of your weekly limit each run.
**Neutral**: proposals stay proposals; promotion to plan rows is yours.
