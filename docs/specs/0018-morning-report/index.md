# 0018. Morning report

**Date**: 2026-10-13
**Status**: Accepted
**Paths:** `runner/report.py`, `runner/ntfy.py`, `runner/run.py`, `runner/wf.py`, `runner/e2e/run.py`, `claude-home/settings.json`, `claude-home/rules/runner-handoff.md`
**Amends**: [0005](../0005-decision-parking-phone-pings/index.md) and architecture invariant 4 (one report note at the end of every run joins the question pings), [0017](../0017-several-repos-at-once/index.md) (the parent sends one note for all its children). Uses the `· live` tag of [0019](../0019-live-setup-steps/index.md).
**Amended by**: [0061](../0061-runner-improves-itself/index.md) - the session start report line gains a `wf proposals: N new` count with the inbox path.

## Summary

When a `wf run` ends, for any reason, it sends one short phone note: how it ended, what it built, what is parked or asked, what waits on you, and the next command to type. The same report, in full, is saved, and every new Claude session prints it until you run `wf finish` or `wf report --seen`, so you never wake up to a silent night. Bare `wf run` sends one combined note for all its repos. Nothing else about pings changes.

## What you're agreeing to

- Every run ends with one phone note (priority 3, normal sound), on top of the question pings you get today.
- The note holds at most 12 lines and 1000 characters; the rest is behind `wf report`.
- Every new Claude session shows the report until you run `wf finish` or `wf report --seen`, or a newer run replaces it.
- A run killed outright (power loss, `kill -9`) sends nothing; the next session says it ended without a record.
- The note goes through your public ntfy topic, scrubbed the same way as question pings.

## Requirements

**User stories**:
- As you, waking up after a night run, I want one note saying what happened and what to type next, so I do not dig through run folders.
- As you, opening Claude later, I want the same report in front of me until I deal with it.

**Acceptance criteria**:
- **AC-1** (when): every `wf run <repo>` that reached its run folder (spec 0004 `run()`, any stop reason, `interrupted` and `internal_error` included) builds the report after its final `run.json` save, writes it, and sends it, unless the environment holds `WF_REPORT=parent`. A run refused at its start checks, cancelled at the confirm, or with nothing to run sends nothing. Bare `wf run` (spec 0017 parent) starts every child with `WF_REPORT=parent` in its environment and, after its `summary:` lines, builds one report from all children and sends it once. A failure inside the report (build, write or send) prints `warning: report: <error>` and never changes the exit code. The run's record starts with `"report": null`; after the send, the run saves `run.json` once more, so the `report` field and spec 0014's spent totals (merged after the last save today) both land in the file. The parent passes `WF_REPORT=parent` through the `env=` of each child's `Popen` (its own environment plus that key).
- **AC-2** (what it holds, in this order): a head line, then one line per item, then the next command.
  - Head: `wf <status> <HH:MM>: <b> built, <p> parked, <o> open, <spent>`. `<b>`, `<p>` and `<o>` count this report's `built:`, `parked:` and `question` lines (open questions from earlier runs are not reported). `<status>` is `done` when every run of the report stopped `queue_done` and there is no `no record:`, `no end:` or `not started:` line, else `stopped <reason>[, <reason>...]` (distinct stop reasons in run order; `internal_error` reads `internal_error (crash)`). `<HH:MM>` is the local time of the latest `ended`. `<spent>` is spec 0014's `spent_line()` over all calls without its `spent: ` prefix.
  - `built: <feature>` per feature entry with outcome `feature_done`.
  - `parked: <feature>: <reason>` per entry whose outcome is in `PARKS` other than `waiting`; `stopped: <feature>: <reason>` per entry whose outcome is a repo stop or run stop.
  - `question <id>: <feature>` per entry with outcome `decision_open` (`<id>` from its detail).
  - `live: <feature>: <n> step(s)` per feature with open live boxes (spec 0019 AC-1), and `yours: <feature>: <owed text>` per other open ` · waits on you` box, both read when the report is built from each repo's scope file as the runner already finds it (`docs/` before `.workflow/`, spec 0003), through `wf.parse_text`: open boxes whose `skip` is false (so not under `## Deferred` and not in a `done` or `dropped` feature), the feature shown as the box's heading without its tags (`wf.DISPLAY_TAG`), the owed text as `wf.owed_text()` gives it with any ` · later boxes go on` tag removed too.
  - `no record: <repo>: exit <code>` per parent child that never printed a run folder, `no end: <repo>` per child whose `run.json` has no `ended`, and `not started: <repo>` per parent row with work that never started (after a signal).
  - Last: `next: <command>`, the first that applies: `wf finish` when any `live:` line exists (followed by `, then review and merge: <repo>[, <repo>...]` when anything was built); `wf queue` when any `parked:`, `stopped:`, `question`, `yours:`, `no record:`, `no end:` or `not started:` line exists; `review and merge: <repo>[, <repo>...]` (repos with a `built:` line) when anything was built; else `wf queue`.
  - In the parent, each repo's path, label and scope come from its summary row's `path`, its run from the row's `folder` (`-` means no record) and `code`.
  - With more than one repo in the report, every item line ends ` (<repo>)`.
- **AC-3** (the saved report): the full report, with real repo names, full owed box texts, each park's detail after its reason, and one `run folder: <path>` line per run at the end, is written atomically to `<state>/report.txt` (mode 0600, `<state>` as spec 0011), and `<state>/report.seen` is removed. `run.json` gets `"report"`: `"sent"`, `"failed: <error>"`, or `"parent"` for a child.
- **AC-4** (the phone note): one ntfy POST through `Topic.publish` (spec 0005 AC-7: three tries 10 seconds apart), which gains optional `title` and `tags` arguments (defaults unchanged for question pings); the report passes title `wf report`, priority 3, `tags` `[]`, no actions, and `stopped=lambda: False`, so a Ctrl C run still sends. Only a returned message id records `sent`. Its body is the AC-2 lines where repo names are spec 0005 repo labels, and every feature name, owed text, reason and label goes through a new `ntfy.scrub_field(cfg, text, limit, fallback)`: spec 0005 AC-7 scrubbing cut to `limit`, then `fallback` when the result is empty or holds a block list entry (feature 40 with fallback `feature`, owed text 80 with `step`, reason 40 with `reason`). No park detail, path or run folder is sent. At most 12 lines and 1000 characters: when over, `built:` lines are dropped first, then other item lines from the end, replaced by one `+<n> more, run wf report` line; the head and `next:` lines always stay.
- **AC-5** (`wf report`): `wf report` prints `<state>/report.txt` (or `no report yet`), exit 0. `wf report --seen` writes `<state>/report.seen` holding the name of the newest run folder at that moment (empty when there is none), exit 0. Both also print the AC-6 killed run line when it applies.
- **AC-6** (session start): `wf report --hook` prints, when `report.txt` exists and `report.seen` does not, one line `wf morning report (shows in every session until you run wf finish or wf report --seen):` then the report. It also prints `wf run <run folder name> ended without a record (killed or power loss), see its log.txt` for the newest folder under `<state>/runs` (by the `YYYYmmdd-HHMMSS` part of its name, parsed from the right as `<name>-<date>-<time>-<pid>`) when: its `run.json` is missing or has `ended` null, the pid is not running (`os.kill(pid, 0)`), its time is later than `report.txt`'s modification time (or there is no `report.txt`), and `report.seen` does not name it. It prints nothing when `WF_RUN` is set or any lock file under `<state>/locks` is held, tested by a non blocking `flock` that is released at once (the same lock helper as `repo_lock`). It never writes, always exits 0, and swallows its own errors.
- **AC-7** (wiring): the repo `settings.json` gains a `SessionStart` hook entry running `/home/santiago/.local/bin/wf report --hook` (install.sh swaps the home path). `rules/runner-handoff.md` gains under *At session start in a repo*: when the session opens with a wf morning report, say it first in one short list with its next command, then follow *After a wf run ends*. Both reach `~/.claude` through spec 0019 live steps, never from a `wf run` call.
- **AC-8** (real check): `runner/e2e/run.py` prints `PASS` only when also the temp state folder holds `report.txt` and the run's `run.json` says `"report": "sent"`; with `--parallel`, only when each child `run.json` says `"parent"` and the parent wrote one `report.txt` naming both repos. You run it (spec 0019 live step); it sends a real note to your phone.

## Decision

**Chosen option**: Option 1: a report built from `run.json` plus the scope files, written to the state folder, sent once by whoever ran last (the run, or the parent), and shown by a session start hook until you act.

## Feature design

**Data model sketch** (files, no database):
- `<state>/report.txt`: the full report text (AC-3). One file; a newer run overwrites it.
- `<state>/report.seen`: empty marker. Present means do not show at session start. Removed by every new report; created by `wf report --seen` and by a completed `wf finish` (spec 0019).
- `run.json`: new field `report` (`"sent"`, `"failed: <error>"`, `"parent"`, null while running).

**API surface**:
| Command | Inputs | Output | Exit |
|---|---|---|---|
| end of `wf run <repo>` | its `run.json`, scope files, ntfy config | report.txt, one note, `run.json` `report` | unchanged |
| end of bare `wf run` | children run folders from the summary rows | report.txt, one note | unchanged |
| `wf report` | report.txt, newest run folder | the report, or `no report yet` | 0 |
| `wf report --seen` | none | creates report.seen | 0 |
| `wf report --hook` | env `WF_RUN`, locks, report.txt, report.seen, newest run folder | the report or nothing | 0 always |

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| head | status, reasons | `run.json` `stop_reason` of each run |
| head | time | latest `run.json` `ended`, local time |
| head | counts | `run.json` `features[].outcome` |
| head | spent | `spent_line()` over `run.json` `calls` (spec 0014) |
| built, parked, stopped, question | feature, reason, id | `run.json` `features[]` `feature`, `outcome`, `detail` |
| live, yours | boxes | scope files of each run's repos, reread at build time (`wf.parse_text`, `OWED`, spec 0019 `LIVE`) |
| no record, no end | repo, exit code | parent summary rows (spec 0017 AC-4) |
| next | command | AC-2 rule over the lines above |
| repo on phone | label | `ntfy.repo_label()` (aliases, else `repo-<sha1>`) |
| killed run line | folder, pid | newest `<state>/runs/<name>-<time>-<pid>` folder and its `run.json` |
| send | server, topic | `~/.config/wf/ntfy.json` already loaded by the run |

**Key invariants**:
- The note never holds a path, a park detail, a question text, a run folder or an unscrubbed name.
- A report problem never changes how a run ends or its exit code.
- A `wf run` call never sees the report: `--hook` is silent under `WF_RUN` and while any run holds a lock.
- One note per `wf run` command: a child under a parent never sends.

**Security model**: the ntfy topic is public to anyone who knows its name (spec 0005). The note carries only scrubbed feature names, repo labels, reason words, counts and the next command. Full detail stays in `report.txt` (0600).

**Configuration required**: none new.

**Critical test scenarios**:
- A run ending `queue_done` with one built, one parked, one live box and one other waiting box writes the head, five lines in AC-2 order and `next: wf finish`; the note body matches, labels and scrubbing applied: AC-1, AC-2, AC-4.
- A run ending `internal_error` still writes and sends with `stopped internal_error (crash)`: AC-1, AC-2.
- A failing POST (three times) prints the warning, records `failed: ...` and keeps the exit code: AC-1, AC-3.
- 30 item lines: note has 12 lines, `built:` lines go first, ends with `+<n> more, run wf report` then `next:`, under 1000 characters; a block list hit in one field replaces only that field: AC-4.
- A run stopped by Ctrl C still sends (`stopped` ignored) and records `sent`; a publish returning no id never records `sent`: AC-1, AC-4.
- A parent with two children: children record `parent`, one note, both repos named, `no record:` for a child that died before its folder: AC-1, AC-2.
- `--hook` prints under neither `WF_RUN` nor a held lock, prints nothing after `--seen`, prints again after a newer report, prints the killed run line for a dead pid folder: AC-5, AC-6.
- `next:` picks `wf finish`, `wf queue`, `review and merge` in that order: AC-2.

## Build plan

Skateboard: the single repo report first (usable on its own), then the parent, then the session hook, then the real check.

Built after feature 30 (spec 0019), whose step 1 adds `wf.LIVE`.

1. `runner/report.py`: build the lines from run records and scope files, the full and the phone renderings, the cap, write report.txt and remove report.seen, send through `ntfy.Topic.publish`. Tests in `runner/tests/test_report.py`, satisfies **AC-2**, **AC-3**, **AC-4**
2. Call it at the end of `Run.run()` (after the final save, before the return) unless `WF_REPORT=parent`; record `report`; warning path, satisfies **AC-1**, **AC-3**
3. Parent: set `WF_REPORT=parent` on children, build one report from the summary rows and their run folders, send once, satisfies **AC-1**, **AC-2**
4. `wf report` with `--seen` and `--hook` in `runner/wf.py`, killed run line, satisfies **AC-5**, **AC-6**
5. Repo `settings.json` SessionStart entry (install.sh already swaps `/home/santiago` for `$HOME`) and the `rules/runner-handoff.md` line. Both are copy files (AGENTS.md): edit the repo copies and never run `./sync.sh` before the live steps below, or it overwrites them. Architecture invariant 4 is already updated by this spec's commit, satisfies **AC-7**
6. `runner/e2e/run.py` report assertions (single and `--parallel`), its fake `wf` test updated, satisfies **AC-8**
7. Live steps (spec 0019), one per box, each ` · waits on you · live`: `./install.sh` (the hook), `cp ~/claude-config/rules/runner-handoff.md ~/.claude/rules/runner-handoff.md`, `python3 runner/e2e/run.py`, `python3 runner/e2e/run.py --parallel`, satisfies **AC-7**, **AC-8**

## Consequences

**Positive**:
- A night run always ends with a message, including crashes and limits.
- The morning starts from one list and one command.

**Negative / tradeoffs**:
- One more buzz per run, also for `runner/e2e/run.py` runs and for a run you stopped with Ctrl C at the keyboard.
- Every session shows the report until you act, which is noise on a day you choose to leave it.
- A session started by a probe's own `claude -p` (not under `wf run`) also sees an unseen report in its context.
- A run killed outright pings nothing; you learn it at the next session only.

**Neutral**:
- Architecture invariant 4 now lists the report note.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
