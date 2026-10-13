# 0017. Several repos at once

**Date**: 2026-10-13
**Status**: In Progress
**Paths:** `runner/run.py`, `runner/e2e/run.py`
**Amends**: [0011](../0011-build-decision-queue/index.md) (AC-1 bare `wf run` runs repos side by side, AC-5 locks move to the children, AC-6 plan line, AC-19 exit codes for bare `wf run`). Builds on [0014](../0014-runner-resilience/index.md) (`runner/e2e/run.py`).

## Summary

Bare `wf run` builds one feature at a time across all trusted repos. With this spec it becomes a small parent that, after the usual plan and one confirm, starts today's single repo run (`wf run <repo> -y`) once per repo that has work, side by side, and waits for them. Each child keeps its own lock, guard, run folder, log and waits, so nothing that works today changes inside a repo. Repos whose apps share a localhost port never run together, `--jobs N` caps how many run at once, and the terminal shows every child's lines with a `[<repo>]` prefix and one summary at the end.

## What you're agreeing to

- Bare `wf run` runs every repo with work at the same time by default; `--jobs 1` gives today's one at a time.
- Parallel calls use your 5 hour usage window faster; each repo waits through a usage limit on its own.
- Two repos whose `app url` uses the same port run one after the other.
- The crash loop check (spec 0014) sees one repo at a time.
- `wf run <repo>` (one named repo) does not change.

## Requirements

**User stories**:
- As you, I want one `wf run` to build in all my repos at once, so a night covers more work.
- As you, I want each repo's run to behave exactly as it does alone.

**Acceptance criteria**:
- **AC-1** (parent): bare `wf run` runs its global checks, per repo checks and plan as spec 0011 AC-4 to AC-6 do today, plus one plan line `jobs: <n> at once` (`<n>` the `--jobs` value, else the number of repos with work), then the confirm (empty line or `-y`). After the confirm it releases every repo lock it took for the plan and starts one child per repo with work, in trust list order. A repo has work when it has a startable feature, an answered decision to resume, an unanswered decision (so its child re-pings it and collects the reply, spec 0011 AC-14, AC-15), or a `sync owed` feature: `plan()` records this as a per repo `has_work` flag, set by the same test that decides today whether the run has anything to do, and the parent reads the flag, never the printed lines. A child is `<python> -u <runner dir>/wf.py run <repo real path> -y` plus the run's `--budget`, `--call-timeout`, `--max-calls`, `--max-hours` and `--max-wait` values, where `<python>` is `sys.executable` and `<runner dir>` the real folder of `run.py`, as an argument list, stdin from `/dev/null`, in a new session (`start_new_session=True`), stdout piped to the parent and stderr merged into it (`stderr=STDOUT`). Children start one at a time: the next child starts only after the previous one has printed its `run folder:` line (spec 0014 AC-6, printed right after its confirm) or exited, so start checks (the shared MCP npm cache, the locks) never run in two children at once. A repo with no work gets no child. With nothing to start, the parent prints `nothing to run` and exits as spec 0011 AC-19 says (5 when some repo was refused).
- **AC-2** (how many): at most `--jobs N` children run at once (default: all repos with work). `--jobs` takes a whole number of 1 or more; anything else is a usage error, exit 2. With `wf run <repo>` it is accepted and ignored. When a child exits, the next waiting repo starts.
- **AC-3** (never together): for each repo with work whose standing answers name `app url` (spec 0009), the parent takes the port (the URL's port, else 80 for `http` and 443 for `https`). It also takes each repo's git common dir (resolved from its `.git` file or folder, as spec 0002 reads it, no git call) and real path. A repo is not started while a running child's repo has the same port, the same git common dir, or a real path inside its own or containing it; it starts when that child exits.
- **AC-4** (output): the parent reads each child's stdout and stderr line by line and prints each line as `[<name>] <line>` (`<name>` the repo's candidate name, or `<parent folder>/<name>` when two repos of the run share a name; every line through `clean()`), so lines of different children interleave but never break mid line. When every child has exited, it prints `summary:` and one line per repo of the plan: `  <name>: exit <code>, <last line starting with done:, parked:, stopped:, or nothing to run> | run folder: <path, or - when the child never printed one>`, `  <name>: skipped: <reason>` for a repo the plan skipped, or `  <name>: not started` (AC-5).
- **AC-5** (signals): the parent installs its SIGINT, SIGHUP and SIGTERM handlers before it starts the first child. Each signal is forwarded as SIGINT to every running child's process group (a child treats it as its own first Ctrl C, spec 0004 AC-12; a second signal is forwarded again, which the child treats as its second). After the first signal no new child starts; waiting repos show `not started` in the summary. A parent killed with SIGKILL forwards nothing: its children run on to their own end, holding their locks (accepted).
- **AC-6** (exit code): 130 when the parent got a signal or any child exited 130; else 6 when any child exited non zero (a child refused at its own start checks, for example `locked` because another process took the lock after the parent released it, counts here); else 0. A repo skipped in the plan does not change the code when at least one child started.
- **AC-7** (children unchanged): each child is the spec 0011 target form run, unchanged: its own start checks (a failure exits 5, shown in the summary), lock, guard baseline, run folder, `log.txt` (spec 0014), usage limit and outage waits, decision polling and re-ping of its own repo's open decisions, and end wait (`--max-wait`). A child waiting at its end for your reply keeps its `--jobs` slot. A change to a global guarded file (a `~/.claude` settings or hook file, spec 0007 AC-7) stops each child on its own `guard_changed` (each exits 6); that is accepted.
- **AC-8** (real check): `runner/e2e/run.py --parallel` (spec 0014 AC-5) copies the fixture into two temp repos, trusts only those two in its temp config, runs bare `wf run -y`, and prints `PASS` only when the parent exits 0, both repos end `feature_done`, and at least one call of each repo ran while a call of the other was running (from each `run.json`: call `started` plus `duration_s`). You run it with `!`; the result goes into this spec's Follow-up.

## Decision

**Chosen option**: a parent process that starts today's single repo run per repo (your pick over threads in one process).

Options and reasoning: [rationale.md](rationale.md).

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| parent | repos with work | `plan()`'s per repo `has_work` flag (startable feature, answered or unanswered decision, `sync owed`) |
| parent | child started | the child's `run folder:` line, or its exit |
| never together | git common dir, real path | the repo's `.git` file or folder resolved as spec 0002 does; `os.path.realpath` |
| parent | child argv | `sys.executable`, `run.py`'s real folder joined with `wf.py`, the repo real path, the run's cap flags |
| jobs | at once | `--jobs`, default the number of repos with work |
| port clash | port | standing answers `app url` (spec 0009), its port, else 80 or 443 by scheme |
| output | repo name | the candidate `name` (spec 0002) |
| summary | final line, run folder | the child's last `done:`, `parked:`, `stopped:` or `nothing to run` line and its `run folder:` line |
| exit | code | AC-6 over the children's exit codes |

## Build plan

1. Parent in `run.py`: plan, `jobs:` line, confirm, release locks, start children with the forwarded caps, wait, exit code; `--jobs` flag in `wf.py`, satisfies **AC-1**, **AC-2**, **AC-6**, **AC-7**
2. Port clash ordering, satisfies **AC-3**
3. Prefixed output and the summary, satisfies **AC-4**
4. Signal forwarding and `not started`, satisfies **AC-5**
5. Tests with the fake claude: two trusted repos, each a queued feature whose fake call sleeps; calls overlap in time; the second child starts only after the first printed `run folder:`; `--jobs 1` runs them one after the other; `--jobs 0` and `--jobs 1.5` exit 2; same `app url` port, a shared git common dir, and a repo nested in the other each run one after the other; a repo holding only an unanswered decision gets a child that re-pings it; two children with one open decision each and one phone reply per decision each resume their own; a child refused `locked` gives exit 6 and a summary line; a skipped repo shows `skipped:`; two repos with one name get `<parent>/<name>` prefixes; SIGINT to the parent reaches both children and gives 130; lines carry their prefix and arrive before the child exits; `wf run <repo>` output is unchanged, satisfies **AC-1** to **AC-7**
6. `runner/e2e/run.py --parallel`, satisfies **AC-8**
7. Run `python3 runner/e2e/run.py --parallel` for real (you, with `!`), satisfies **AC-8**

## Consequences

**Positive**: a night can build in every trusted repo at once; each repo's run is the one you already trust.

**Negative / tradeoffs**:
- Parallel calls use the 5 hour usage window faster; a limit hit by one repo is usually hit by all, and each waits on its own.
- Between the parent releasing a lock and the child taking it, another process can take the repo; that child is refused `locked` and the summary says so.
- The crash loop check sees one repo at a time, so a broken global hook parks two features in every repo before each child stops.
- A child waiting for your reply at its end keeps its slot when `--jobs` is lower than the number of repos.
- The plan is printed twice (the parent's, then each child's, prefixed). A separate in process path for a single repo would avoid that, at the cost of two code paths; not taken.
- Children start one after another, so the last of many repos starts a little later than the first.
- A parent killed with `kill -9` leaves its children running to their end.
- Each child takes its guard baseline at its own start, so a guarded file one repo's call changes in another repo goes unnoticed when that other repo's child starts afterwards (always so for a repo nested in another, which AC-3 starts after the outer one ends). The bare run used to stop on it while it held both repos. Accepted 2026-10-13 (your answer during the build); the calling repo's own guarded files still stop its child.
- Needs spec 0014 built first (`run folder:` after the confirm, `runner/e2e/run.py`).
- Changes architecture invariant 6: one call at a time per repo, not per run.

**Neutral**: `wf run <repo>`, `wf queue` and `wf unpark` are unchanged apart from the plan's `jobs:` line in bare `wf run`. Several features inside one repo at once still waits on feature 14.

## Follow-up

- [x] Record the `runner/e2e/run.py --parallel` result here (date, Claude Code version, `PASS` or the `FAIL` line). · waits on you
  - 2026-10-13, Claude Code 2.1.296: `PASS`. Repos `one` and `two` both ended `done: 1. Add function`, calls interleaved, parent exit 0.
