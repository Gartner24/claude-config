# 0011. Build queue and decision queue: `wf run` moves on after a park

**Date**: 2026-10-12
**Status**: Accepted
**Paths:** `runner/run.py`, `runner/wf.py`, `runner/tests/test_queue.py`, `rules/scope-contract.md`
**Amended**: 2026-10-12, review stack findings H2 and H3 (`docs/briefs/runner-review-stack-2026-10-12.md`): AC-6 per repo `answers:` and `guard:` lines, standing answers read once per run; AC-6 and AC-9 standing answers watched during the run (`guard_changed` repo stop); finding H1: AC-7 pick skips an answered Decision whose feature has a Park that applies; finding L9: AC-13 an answered Decision whose feature is no longer queued is stale; finding L2: AC-12 and the data model, a Decision's `reply`; finding M12: the spec 0010 `design` record moves to the FeatureEntry
**Amended**: 2026-10-12, second review stack (`c95f181..d20a328`, same brief): AC-9 a file at or under a repo's submodule `.git` path (frozen text) is that repo's own; AC-13 wording, a stale record's feature runs again only if still queued; AC-6 the reread of the standing answers refuses a file that is not regular or is past 16 MiB (spec 0006 AC-3), which stops the repo `guard_changed`
**Amended by**: [0014](../0014-runner-resilience/index.md) - AC-3 the next box passes over sync boxes and skippable waiting boxes, a `/sync` box runs as the final call; AC-9 run stops gain `api_outage` and `crash_loop`; AC-10 a `call_timeout` whose call ticked boxes parks with `cap` null.
**Amended by**: [0015](../0015-checks-that-cannot-lie/index.md) - AC-9 park set gains `unchecked`.
**Amended by**: [0017](../0017-several-repos-at-once/index.md) - AC-1 bare `wf run` runs repos side by side as `wf run <repo> -y` children, AC-5 locks move to the children, AC-6 plan line, AC-19 exit codes for bare `wf run`.

## Summary

Today one `wf run` builds one feature, and a question or a failure ends the night. With this spec a run works through a queue: every feature tagged `· auto` with its spec box ticked, in every repo on your `wf allow` list. A feature that parks (a failure only you can fix) or asks a question is set aside and the run goes on to the next one. Your phone answer resumes the waiting feature later in the same run, or in the next run, because parks and open questions are kept in one state file outside the repos.

## What you're agreeing to

- `wf run` with no name builds the queued features of every repo you trusted with `wf allow`; `wf run <repo>` builds one repo's queue. A feature without `· auto` never runs unattended any more.
- A question pings your phone and the run moves on; your answer resumes that feature when the run gets back to it, or in the next run.
- A park is remembered until you edit that feature in the scope or run `wf unpark`; a cap park (`budget`, `max_calls`, `call_timeout`) also clears when you rerun with a higher value for that cap. Only a `call_error` park is retried by the next run on its own.
- While a repo has uncommitted changes and a parked feature or open question, no other feature starts there.
- `--max-calls` and the 2 debug attempts count per feature; `--max-hours` and the one usage limit wait stay per run. Exit 0 means nothing is left waiting for you.
- New commands: `wf queue` shows the plan without changing anything, `wf unpark` clears parks and open questions.
- (Amended) The plan shows each repo's standing answers, the app command included, and its guard size. If a step changes the standing answers mid run, that repo stops. An answered question for a feature you untagged or finished is dropped, and a parked feature's answer waits until the park clears.

## Requirements

**User stories**:
- As you, I want a parked feature to stop only itself, so that one stuck feature does not waste the night.
- As you, I want my phone answer to resume the feature that asked, even after the run has moved on or ended, so that a question costs a reply, not a rerun.
- As you, I want to see and clear what is parked without reading `run.json` files.

**Acceptance criteria**:
- **AC-1** (targets): bare `wf run` takes every path in `allowed.json` (spec 0008 AC-9), in file order, once per real path; a missing, unreadable or malformed file refuses `untrusted` (exit 5) as there. Each path becomes a candidate through `wf.make_candidate`: a path that no longer exists or has no scope is skipped `missing`, a scope that cannot be read (`OSError`, `StopIteration`) is skipped `scope_unreadable: <error>`, a hub is skipped `hub`. `wf run <target>` resolves one repo with `wf.resolve` (spec 0004 AC-1) and runs only its queue. Bare `wf run` never walks the current folder and never opens the picker.
- **AC-2** (queued feature): a feature of a candidate is queued when its heading is level 3, outside `## Deferred`, not `done`, `existing` or `dropped` (`Box.skip` false), carries the `· auto` segment (spec 0003 AC-5), and has a decision box that counts as ticked. A decision box is a box whose label (the text before its first backtick) ends with `(spec)` (scope legend, `rules/scope-contract.md`); it counts as ticked when it is `[x]` and does not end with `· skipped`; with several decision boxes, all must count. The feature must also have an open box, or have every box ticked (then `/sync` is owed, AC-8). Two queued features with the same display heading in one repo are both skipped `ambiguous_feature: <heading>`. Queue order is file order (`load_scope` order for an epic split). A feature with no decision box is never queued.
- **AC-3** (startable): a queued feature is startable when it has no Park record that still applies (below), no Decision record (answered or not), its next box (`wf.pick_next` over that feature's own boxes) passes `box_refusal` (`no_command`, `manual_box`, `waiting` make it `skip: <feature>: <reason>` in the plan and are not recorded), and the tree rule (AC-7) lets it start. A feature with every box ticked has `/sync` as its next call and no box check. A Park record stops applying, and `wf run` or `wf unpark` deletes it (never `wf queue`), when its `section_sha` differs from the feature's current section hash, when its feature is no longer queued, or, for `budget`, `max_calls` and `call_timeout`, when this run's `--budget`, `--max-calls` or `--call-timeout` is greater than the record's `cap`. The section comes from a new `wf.sections(text)` beside `parse_text`, sharing `HEADING`, the fence rule and `uncomment`: per level 3 heading, the raw lines (comments included, so editing a comment counts) from the heading up to the next heading of level 1 to 3 or the end of that file. The hash is sha256 of those lines joined with `\n`.
- **AC-4** (start checks): global checks first, each ends the command: state folder (`state_unwritable`, exit 5), `queue.json` (`queue_unreadable`, exit 5, AC-17), `claude` on PATH (exit 1), ntfy config (`no_ntfy`, exit 5), and the trust file for bare `wf run`. Then per repo, in this order: `hub`, `missing`, `scope_unreadable`, Autopilot (`autopilot_off`), trust (`untrusted`, target form only), standing answers (`bad_answers`), branch (`branch`), lock (`locked`, AC-5). With a target, the first failing repo check refuses exit 5 as spec 0004 AC-2 does. In bare `wf run`, a failing repo is listed `skip: <reason>: <detail>` and the others go on. No run folder is created and no call is made before the confirm. The spec 0004 AC-2 box checks (`no_feature`, `no_command`, `manual_box`, `waiting`) no longer refuse; they are per feature skips (AC-3), and exit 3 is gone. A repo with no open box at all shows `nothing to run`.
- **AC-5** (locks): every repo that passes its other checks is locked (spec 0004 AC-9, same file and holder line) before the confirm, and every lock is held until `wf` exits, including repos that end early (AC-9). A lock already held makes that repo `skip: locked: <pid> <start>`.
- **AC-6** (plan and confirm): before the confirm `wf` prints the plan, one block per candidate in run order:
  `<name> (<label>) on <branch>, <N changes>`, then for a repo that passed its checks two indented lines: `answers: ...` in the spec 0006 AC-7 form (so `app start` and `app url` show in full, spec 0009 AC-10), and `guard: <n> hosts, <k> files` (spec 0007 AC-9: `<n>` is the length of `run.json` `guard.hosts`, `<k>` of `guard.guarded_files`; `wf queue` builds no guard and leaves this line out). Both go through `flat()`. A repo that failed a check shows only its `skip:` line. Then one indented line per item: `queued: <feature>`, `sync owed: <feature>`, `resume: <id> <feature>: <question>` (answered), `open: <id> <feature>: <question>` (unanswered), `parked: <feature>: <reason>: <detail> (wf unpark to retry)`, `skip: <feature>: <reason>`, `stale: <id> <feature>` (AC-13); or the single line `skip: <reason>: <detail>` for a skipped repo. Then `caps: <budget> USD/call, <timeout>m/call, <max calls> calls/feature, <max hours>h, wait <max wait>h`, then warnings (header, open sessions, codes left). Every text goes through `flat()`. The confirm itself is spec 0004 AC-3 (empty line or `-y`). Standing answers are read once per repo at its start check (AC-4) and never reread during the run, so the app command that runs is the one the plan showed; a call that edits `AGENTS.md` changes the next run's plan, not this run. So that a change cannot reach an unread `-y` plan, `wf` rereads each held repo's standing answers (`read_answers`) wherever it runs the spec 0007 AC-7 guarded file check (each pick, so also after a run's last feature, before each call, after each app stop); when the result differs from the one read at start (a key added, removed or changed, or the section no longer parses), the repo stops `guard_changed`, detail `<file> standing answers changed during the run; check them before the next wf run` (`<file>` as in spec 0006 AC-3). It wins over a park or decision outcome the feature had, as other `guard_changed` stops do. Only parsed values are compared, so editing the rest of `AGENTS.md` (as `/sync` does) does not trip. When no repo has a startable feature or a resumable decision, it prints the plan and `nothing to run`, makes no call, and exits per AC-19, or 5 when at least one repo was skipped by a refusal reason (not `missing`, `hub` or nothing queued).
- **AC-7** (pick order and tree rule): before each new piece of work, `wf` rereads the scopes of the held repos that have not ended and rereads `queue.json` under its lock, then picks the first of: (1) an answered Decision in a held, not ended repo whose feature has no Park record that applies (AC-3), oldest `asked` first (a resume that parks before its call, such as `app_failed` on the app restart, keeps its record and waits for the park to clear, instead of being picked again in the same run); (2) the first startable feature of the first held, not ended repo in run order. A picked feature runs until it finishes, parks, opens a decision, or its repo or the run stops. Tree rule: a repo is dirty when `git status --porcelain` lists anything or fails (a failed status reads as dirty, never as clean). In a dirty repo that has any Park or Decision record, no feature starts (`skip: <feature>: dirty with parks`); an answered Decision there may still resume. A dirty repo with no record lets a feature start, as today.
- **AC-8** (one feature): a feature's calls follow spec 0004 and spec 0008, restricted to that feature: the next box after each call is `wf.pick_next` over the feature's own boxes; the feature is finished when it has no open box (this replaces spec 0004 AC-6 rule 10's "or the next box's feature differs"), and then one `/sync` call runs (spec 0004 AC-7). A feature picked with every box already ticked starts with that `/sync` call. A passing `/sync` gives the feature outcome `feature_done`. Before the run picks again, any app spec 0009 started for the feature is stopped.
- **AC-9** (park, repo stop, run stop): every reason ends one of three scopes. Repo stop (no more calls in that repo this run, lock kept): `branch_changed`, `autopilot_off`, `scope_unreadable`, `guard_changed` on that repo's standing answers (AC-6), and `guard_changed` when the changed file is that repo's own `.claude/settings.json` or `.claude/settings.local.json`, or a file under its git common dir (`config`, `hooks/`) that no other held repo shares, or a file at or under one of its submodule `.git` paths (spec 0007 AC-9 `submodules`: an in place `.git` folder, a `.git` pointer), matched against both forms frozen at start (as written and resolved) and never resolved again, unless another held repo is checked out in that submodule folder or above it (a trusted child repo such as dotfiles holding nvim), or has its git common dir there, in either form (second review and its commit reviews: resolving it later let a call swap the folder for a link to `/`; one form missed a layout under a symlinked parent). Run stop: `interrupted`, `run_limit`, `usage_limit`, `spawn_failed`, `ping_failed`, `internal_error`, `app_port_busy` (spec 0009), and `guard_changed` on any other guarded file (a `~/.claude` settings file, a plugin `hooks.json`, a hook token wherever it lives), since those run in every repo's calls. Park (this feature only): every other reason, including `verify_failed`, `blocked`, `denied`, `debug_touched`, `no_progress`, `call_error`, `call_timeout`, `budget`, `max_calls`, `app_failed` (spec 0009), `design_gate` (spec 0010), and `manual_box`, `waiting`, `no_command`, `no_feature` met mid feature. This replaces spec 0008 AC-1's two sets; `decision_timeout` leaves the list (AC-15). Every guarded file of spec 0007 AC-7, for every held repo and the global ones, is hashed once at the confirm and compared before each call in any repo.
- **AC-10** (park records): a park writes or replaces the feature's Park record in `queue.json`, except `call_error` (the next run retries it) and `manual_box`, `waiting`, `no_command`, `no_feature` (they clear when the files change). The record: `repo`, `feature`, `section_sha` (its section after the last call), `reason`, `detail`, `cap` (for `budget`, `max_calls`, `call_timeout`: the `--budget`, `--max-calls` or `--call-timeout` value in force; else null), `run` (run folder), `parked_at`. The terminal prints `parked: <feature>: <reason>: <detail>` and the run picks again (AC-7).
- **AC-11** (decision queue): a call classified as a decision (spec 0008 rule 10) no longer waits in place. When the feature has no counted calls left for the resume, it parks `max_calls` with no ping. An asking call with no `session_id` parks `call_error` (`no session_id to resume`) with no ping. Otherwise `wf` draws an id (spec 0005 AC-7 alphabet) and writes the Decision record in one locked transaction, so the id is unique across `queue.json` and this run; appends the decision to `run.json` `decisions` with its asking `call`; pings it (spec 0005 AC-7), recording each publish response id in the record's `pings`; prints the spec 0005 AC-12 `waiting:` lines; gives the feature outcome `decision_open`; and picks again. A first ping that fails three times stops the run `ping_failed`; the record stays with `sent` null.
- **AC-12** (replies): `wf` polls the topic (spec 0005 AC-8 request, burn and reply rules) once after the confirm, after every call, and every 15 seconds during the end wait (AC-15). The cursor starts at `since=<asked time of the oldest unanswered Decision, unix seconds>`, or, when there was none at the first poll, at the first ping id of this run; after that it is the last message id seen. Messages whose id is in any record's `pings` or `acks`, or is its `reply`, are skipped. A reply counts for any unanswered Decision record in `queue.json`, whichever run or repo it belongs to: the first accepted answer is stored on the record (`answer`, `source` `phone`, `answered`, and the message id as `reply`, so a later poll that reads the same message again does not count it as ignored) in one locked transaction, and any later reply to that id is ignored (`ignored` + 1). The ack text becomes `<id> accepted`, and its publish id goes into the record's `acks`. The terminal prints `answered: <id> <answer> (phone)`. A failed poll prints `warning: ntfy poll failed: <error>` once per run and never stops it.
- **AC-13** (resume): picking an answered Decision (AC-7) first checks it: when the repo's branch differs from the record's `branch`, the record's feature is no longer a heading in the scope, or that feature is no longer queued (AC-2: its `· auto` tag removed, or marked `done`, `existing` or `dropped`), the record is dropped, the terminal shows `stale: <id> <feature>`, and the feature is picked again fresh only if it is still queued (a moved branch; a gone or unqueued feature runs nothing). Otherwise a resume call runs (spec 0005 AC-10 argv and prompt, `--resume <session_id>`) with the record's `call_kind`, `command` and `box_text`, counted on the feature; a `debug` kind resume takes a fresh spec 0008 AC-3 snapshot at its start. The record leaves `queue.json` only after the resume (with its spec 0008 AC-6 retry) has been classified. A resume that still fails as a call error after its retry is treated as stale: the record is dropped, `stale: <id> <feature>` is printed, and the feature parks `call_error` (not recorded, so the next run starts it fresh). A run stop during the resume leaves the record in place. The `run.json` decision entry gets `resumed_in` (the call n). The resume is then classified like any call of that feature, its progress compared with the record's `box_text`.
- **AC-14** (re-ping): right after the confirm, every unanswered Decision in a held repo is pinged once more with its same id, body and buttons (spec 0005 AC-7), its publish id added to `pings`. A failed re-ping prints `warning: re-ping <id> failed: <error>` and the run goes on; the record keeps its old `sent`, or gets the body when it was null.
- **AC-15** (end wait): when AC-7 finds nothing to pick and a held, not ended repo has an unanswered Decision, `wf` waits, polling every 15 seconds in `POLL` slices, while the end wait time of this run (all such waits added, on `CLOCK_BOOTTIME`) is under `--max-wait` hours (default 12). An answer goes back to AC-7. Answered Decisions that cannot resume do not start or extend a wait. The wait keeps every lock and the inhibitor, adds to `waited_s` (not counted toward `--max-hours`), and Ctrl C, SIGHUP or SIGTERM stop it `interrupted`. When the wait budget is used up or no such Decision is left, the run ends `queue_done`; unanswered Decisions stay in `queue.json`.
- **AC-16** (caps): `--max-calls` (default 20) counts per feature per run: calls not `limited` (spec 0008 AC-8), resumes, retries and `/sync` included. Before a feature's call, when its count has reached the cap, the feature parks `max_calls`. The 2 debug attempts of spec 0008 AC-2 count per feature per run. A feature resumed in a later run starts both counts at 0. `--budget`, `--call-timeout`, `--max-hours`, `--max-wait` and the one usage limit wait per run keep their spec 0004, 0005 and 0008 meaning.
- **AC-17** (state file): `<state>/queue.json` (spec 0004 AC-9 state folder) holds `{"version": 1, "parks": [...], "decisions": [...]}`. Missing reads as empty. Every read, and every read, change and write done as one transaction, holds `fcntl.flock(LOCK_EX)` on `<state>/queue.lock`; the lock is never held across a call, a ping, a poll or a sleep. A write goes to `queue.json.tmp` (mode `0o600`) then `os.replace`. At the start of `wf run`, `wf queue` or `wf unpark`, a file that does not parse, has another `version`, or breaks a Data model rule refuses `queue_unreadable` (exit 5), names the problem, and is never overwritten. The same failure, or a failed write, during a run stops it `internal_error` (exit 6), leaving the file as last written. At most one Park and one Decision per (`repo`, `feature`); Decision `id` unique in the file.
- **AC-18** (record): `run.json` drops the top level `repo`, `name`, `feature` and `branch` and gains `repos` (RepoEntry list, in run order) and `features` (FeatureEntry list, in the order features were picked; a resumed feature reuses its entry from this run when it has one). Each Call gains `feature` (FeatureEntry `n`). `decisions` holds every decision opened or resumed in this run (AC-11, AC-13). `stop_reason` gains `queue_done`; `parked` (spec 0008 AC-1) moves to FeatureEntry `outcome`. The terminal per call line (spec 0004 AC-11) shows `[<feature count>/<max calls>] <name>: <command> -> ...`, a feature's end prints `done: <feature>`, `parked: ...` or `open: <id> <feature>`, a repo stop prints `stopped repo <name>: <reason>: <detail>`, and the last lines are `queue done: <D> done, <P> parked, <O> open` or `stopped: <reason>: <detail>`, then `run folder: <path>`.
- **AC-19** (exit codes): 0 when, at exit, no Park or Decision record exists for any held repo and every feature entry of this run is `feature_done` (or there is none); 6 otherwise for `queue_done` and `nothing to run`, and for any run stop except `interrupted`; 130 for `interrupted`; 5, 1 and 2 as spec 0004 AC-14 plus AC-4 and AC-17. Exit 3 is no longer used.
- **AC-20** (`wf queue [target]`): prints the AC-6 plan for the same targets `wf run` would take, with each open or answered Decision's options on `  <n> <label>` lines under it, then exits 0. It is read only: no call, no write, Park records that no longer apply are shown as `would clear: <feature>`, and each lock is tested with `LOCK_NB` and released at once (a held lock shows `skip: locked: <pid> <start>`). It runs only the state folder, `queue_unreadable` and trust file global checks; it needs neither `claude` nor the ntfy config.
- **AC-21** (`wf unpark <target> [feature]`): resolves the repo with `wf.resolve` (its exit codes), refuses `locked` (exit 5) while a run holds that repo, and deletes that repo's Park and Decision records: all of them with no feature, else the feature whose display heading equals the argument (case folded), else the one feature whose heading contains it; several matches print them and exit 1. It prints `unparked: <feature>` per Park and `dropped: <id> <feature>` per Decision, or `nothing parked in <name>`, and exits 0. A dropped Decision is never resumed; its feature starts fresh in the next run.
- **AC-22** (manual checks, `verify.md`): against the real `claude` and your phone, in a scratch repo with `**Autopilot:** allowed`, on a work branch, trusted: (1) the done when: two `· auto` features, the first told to end `BLOCKED: test park` with a clean tree; the run parks it `blocked` and builds the second to `feature_done`; (2) a feature that asks a `DECISION NEEDED:` question pings, the run moves to another feature, your phone answer resumes the first after that one ends, same `session_id`; (3) a question left unanswered at Ctrl C is re-pinged by the next `wf run`, answered, and resumed; (4) a second trusted repo on `main` shows `skip: branch` while the first runs.

## Decision

**Chosen option**: Option 1: Queue state in `wf`, decisions kept in one state file

`wf run` plans from the scope files of every trusted repo, runs one feature at a time, sets aside a parked or asking feature, and keeps parks and open decisions in `<state>/queue.json` so a reply resumes the asking session in this run or a later one.

## Feature design

**Data model sketch** (confirmed with you; `dirty` dropped and `cap`, `pings`, `acks`, `resumed_in` added after the cross check):

`<state>/queue.json` (new, mode `0o600`, written atomically under `flock`):

| Entity | Field | Type | Notes |
|---|---|---|---|
| Park | `repo` | string, required | repo real path; key with `feature` |
| | `feature` | string, required | display heading (tags stripped) |
| | `section_sha` | hex string, required | AC-3 section hash after the last call |
| | `reason`, `detail` | string, required; string nullable | AC-10 recorded reasons only |
| | `cap` | number, nullable | cap value for `budget`, `max_calls`, `call_timeout` |
| | `run` | string, required | run folder that parked it |
| | `parked_at` | ISO time, required | |
| Decision | `id` | 4 chars `a-z0-9`, required, unique in file | spec 0005 AC-7 |
| | `repo`, `feature` | string, required | key, at most one Decision per feature |
| | `branch` | string, required | `head_branch` when asked |
| | `session_id` | string, required | asking call's JSON |
| | `call_kind` | `box`, `debug` or `sync` | spec 0008 AC-2 kinds |
| | `command` | string, required | the asking call's command |
| | `box_text` | string, nullable | null for `debug` and `sync` |
| | `question`, `options`, `kind`, `multi` | string, list, `panel`/`prose`, bool | spec 0005 AC-4 |
| | `sent` | string, nullable | scrubbed body, null until a ping succeeds |
| | `pings`, `acks` | lists of ntfy message ids | skipped by the poll |
| | `asked` | ISO time, required | also the AC-12 `since` |
| | `answer`, `source`, `answered` | string, `phone`, ISO time; all nullable | set by the first accepted reply |
| | `ignored` | int | rejected replies |
| | `reply` | ntfy message id, nullable, may be absent | the reply that answered it; skipped by the poll (an absent field reads as null, so older files stay valid) |
| | `run` | string, required | asking run folder |

`run.json` (changed, AC-18):

| Entity | Field | Type | Notes |
|---|---|---|---|
| Run | `repos`, `features` | lists | replace top level `repo`, `name`, `feature`, `branch`; `stop_reason` adds `queue_done` |
| RepoEntry | `repo`, `name`, `branch` | string | |
| | `skip` | string, nullable | AC-4 reason and detail |
| | `ended` | string, nullable | AC-9 repo stop reason |
| FeatureEntry | `n` | int from 1 | |
| | `repo`, `feature` | string | |
| | `outcome` | string, nullable | `feature_done`, a park reason, `decision_open`, a repo or run stop reason; null while running |
| | `detail` | string, nullable | |
| | `calls` | list of int | call numbers |
| | `counted`, `debug_attempts` | int | AC-16, per run |
| | `design` | object, nullable | spec 0010 AC-7 record of this feature's design check, null until it runs; replaces the top level `run.json` `design`, which several features used to overwrite |
| Call | `feature` | int | FeatureEntry `n`; other fields as specs 0004, 0005, 0008 |
| Decision (in `decisions`) | spec 0005 fields plus `resumed_in` | int, nullable | `call` is null for a decision opened in an earlier run |

Relations: Run 1:N RepoEntry, Run 1:N FeatureEntry, FeatureEntry 1:N Call, Call 0..1 Decision. Park and Decision N:1 feature identity (`repo`, `feature`).

**State transitions**:
- Feature, across runs: `queued -> running -> feature_done`; `running -> parked -> (section edited | wf unpark | higher cap) -> queued`; `running -> call_error -> queued next run`; `running -> decision_open -> answered -> running (resume)`; `decision_open | answered -> stale -> queued`; `running -> repo stopped | run stopped` (queued again next run, the Decision kept if one was open).
- Run: `planning -> refused | cancelled | confirmed -> (pick -> feature calls)* -> end wait <-> pick -> queue_done`; any run stop ends it from any state after the confirm.

**API surface** (command line):

| Command | Key inputs | Key outputs | Exit codes |
|---|---|---|---|
| `wf run [target] [-y] [--budget] [--call-timeout] [--max-calls] [--max-hours] [--max-wait]` | no target: trust list; target: one repo; flags as specs 0004 and 0005, `--max-calls` per feature | plan, confirm, per call lines, feature end lines, final lines (AC-6, AC-18) | 0, 1, 2, 5, 6, 130 (AC-19) |
| `wf queue [target]` | as `wf run` | plan with options (AC-20) | 0, 1, 5 |
| `wf unpark <target> [feature]` | repo, optional heading or unique substring | `unparked:` and `dropped:` lines (AC-21) | 0, 1, 5 |

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| targets | repo list and order | `allowed.json` (spec 0008 AC-9), file order, unique by real path; or `wf.resolve(target)` |
| queue | queued features | scope boxes from `wf.parse_text`: `Box.feature`, `Box.skip`, the `· auto` pattern (spec 0003 AC-5), the decision box label ending `(spec)` (scope legend, `rules/scope-contract.md`), `· skipped` suffix |
| queue | feature next box | `wf.pick_next` over the boxes whose `feature` equals that heading; `/sync` when all are ticked |
| queue | feature identity | candidate real path plus the display heading (`DISPLAY_TAG` stripping) |
| queue | section hash | `wf.sections(text)` raw lines per level 3 heading, sha256 |
| queue | cap park cleared | this run's flag value vs the record's `cap` |
| tree rule | dirty | `git status --porcelain` through `wf.git`; nonzero exit or no git reads dirty |
| tree rule | records in repo | Park and Decision records with that `repo` |
| plan | branch, changes, sessions, warnings | `head_branch`, `changes`, `open_sessions`, header warnings (spec 0002, 0003) |
| pick | order | answered Decisions by `asked`, then repos in run order, features in file order |
| park | reason scopes, recorded set | AC-9 and AC-10 constants in `run.py` |
| repo vs run `guard_changed` | scope | the changed file vs the repo's own `.claude/settings*.json` and unshared git common dir |
| guard | baseline | spec 0007 AC-7 hashes of every held repo's and the global guarded files, taken at the confirm |
| decision | id | spec 0005 AC-7 draw inside the `queue.json` transaction, unique against the file and this run |
| poll | cursor | oldest unanswered Decision `asked` as unix seconds, else this run's first ping id, then the last id seen |
| poll | own messages | `pings` and `acks` of every record, plus this run's publish ids |
| resume | session, command, kind, box | the Decision record |
| resume | stale | `head_branch` vs record `branch`; heading present in the reread scope; a resume still failing after its retry |
| end wait | budget | `--max-wait` hours, summed over this run's end waits, `CLOCK_BOOTTIME` |
| caps | feature count | FeatureEntry `counted`, calls not `limited` |
| exit code | 0 vs 6 | records left for held repos and FeatureEntry outcomes |
| state file | path, lock | `<state>/queue.json`, `<state>/queue.lock` |

**Key invariants**:
- One call at a time per run; one feature at a time per repo.
- Every repo a run touches stays locked by it from the confirm to exit, so no other run resumes or starts work there meanwhile.
- `wf` still writes nothing in a repo; queue state lives only in the state folder.
- A feature runs unattended only with `· auto` and a ticked decision box, in a repo with `**Autopilot:** allowed` on your trust list.
- While a repo is dirty and holds any Park or Decision record, no feature starts there.
- A Decision is resumed at most once: its record leaves `queue.json` only after its resume is classified, and a feature with a Decision record never starts fresh.
- A reply only ever answers an id `wf` issued and still holds in `queue.json`.
- An unknown tree state (failed `git status`) is never read as clean.
- `queue.lock` is never held across a call, a ping, a poll or a sleep.

**Security model**: unchanged from specs 0005, 0007 and 0008. `queue.json` holds full questions and answers, local only, `0o600` in a `0o700` folder. A reply can answer an unanswered Decision from an earlier run, the same power as answering it during that run, under the same id, option and code rules. A repo left out of the trust list keeps its records but never resumes them.

**Configuration required**: none new. `<state>/queue.json` and `queue.lock` are created on first use.

**Critical test scenarios** (unittest, fake `claude` and fake ntfy as in specs 0004 and 0005, temp state and config folders):
- Done when: one repo, two `· auto` features; the first's call ends `BLOCKED: x` with a clean tree; it parks `blocked`, the second runs to `/sync` and `feature_done`, a Park record exists, exit 6, verifies **AC-8**, **AC-9**, **AC-10**, **AC-19**
- Queue rules: no tag, tag with unticked `(spec)` box, `(spec)` box ticked `· skipped`, no decision box, `· done · auto`, under `## Deferred`, `· auto-merge`, two features with one display heading (`ambiguous_feature`); only the valid one is queued; file order kept; a feature whose next box is `/architect` or waiting shows `skip:` and is not recorded, verifies **AC-2**, **AC-3**
- Sync owed: a run interrupted after the last box is ticked and before `/sync`; the next run shows `sync owed:` and runs only `/sync`, verifies **AC-2**, **AC-8**
- Sections: a `###` inside a fence or a comment is not a section; an epic split hashes per file; a comment edit changes the hash, verifies **AC-3**
- Trust list: three paths (one missing, one hub, one with an unreadable scope, one valid) and the valid one listed twice through a symlink; bare `wf run` runs it once; a target runs only it; a missing trust file refuses `untrusted`, verifies **AC-1**, **AC-4**
- Repo checks: in bare form a repo on `main`, one with Autopilot off and one locked by another process show `skip:` lines and the fourth runs; the same repo as a target refuses exit 5; every repo skipped by a refusal exits 5 with `nothing to run`, verifies **AC-4**, **AC-5**, **AC-6**
- Plan text: queued, sync owed, resume, open, parked, skip and stale lines with the caps line, verifies **AC-6**
- Parked resume: an answered Decision whose resume parks `app_failed` on the app restart is not picked again; the run goes on to the next feature and ends, the record stays, `wf unpark` clears both, verifies **AC-7**
- Plan answers and guard: a held repo's block shows `answers: none`, then the full form with `app start` and `app url`, and `guard: <n> hosts, <k> files` matching `run.json` `guard`; `wf queue` shows the answers line and no guard line; a call (fake claude `write_file` step) that rewrites `app start` in `AGENTS.md` stops its repo `guard_changed` with the standing answers detail before the next call, and a later browser call never starts the new command; a call that edits `AGENTS.md` outside the section does not stop, verifies **AC-6**, **AC-9**
- Stale on unqueue: an answered Decision whose feature lost `· auto`, or is now `· done`, prints `stale:` and is dropped instead of resumed, verifies **AC-13**
- Tree rule: the first feature parks with a dirty tree; the second shows `skip: dirty with parks`; with a clean tree it runs; an answered Decision in the dirty repo still resumes; a fake `git` that fails status reads dirty; a dirty tree at start with no records lets the first feature start, verifies **AC-7**
- Feature boundary: a feature's last box ticked while an earlier non queued feature still has open boxes; the run calls `/sync`, not that box, verifies **AC-8**
- Repo stop: the fake flips Autopilot off in repo A; A ends `autopilot_off`, repo B still runs; a change to `~/.claude/settings.json` (temp home) stops the whole run `guard_changed`; a change to repo A's `.claude/settings.json` ends only A; a change to a git config shared by two held worktrees stops the run, verifies **AC-9**
- Park memory: a `blocked` park is skipped by the next run; editing one character of its section makes it run again; `wf unpark` makes it run again; a `budget` park clears with a higher `--budget` and stays with the same one; a `call_error` park writes no record and the next run retries, verifies **AC-3**, **AC-10**, **AC-21**
- Decision move on: feature 1 asks; ping sent, its id in `run.json` `decisions`, feature 2 starts; the fake ntfy serves `<id> 1` during feature 2; after feature 2 ends, feature 1 resumes with `--resume`, the AC-10 prompt and its own session id; the record leaves `queue.json` only after the resume is classified, verifies **AC-7**, **AC-11**, **AC-12**, **AC-13**
- No calls left: a question on the feature's last counted call parks `max_calls`, no POST, verifies **AC-11**, **AC-16**
- Across runs: a run interrupted with an open Decision leaves the record; the next run re-pings it with the same id, the reply resumes it; earlier pings and acks are skipped by the poll; a record whose branch changed is dropped `stale` and the feature starts fresh; a resume failing twice is dropped `stale`; two replies to one id keep the first; an interrupt during a resume keeps the record, verifies **AC-12**, **AC-13**, **AC-14**
- End wait: only an open Decision left; the reply arrives after 3 polls and resumes; with `--max-wait` tiny the run ends `queue_done` with the record kept; Ctrl C in the wait is `interrupted`; the wait does not count toward `--max-hours`, verifies **AC-15**
- Caps: `--max-calls 2` parks feature 1 `max_calls` and feature 2 still gets 2 calls; a third `VERIFY FAIL: debug` in feature 2 parks it while feature 1 had used its own 2 attempts, verifies **AC-16**
- State file: broken JSON, `version` 2, two Parks for one feature, a duplicate id each refuse `queue_unreadable` and leave the file unchanged; a write failure mid run stops `internal_error`; mode `0o600` after writes; a concurrent `wf unpark` waits on `queue.lock`, verifies **AC-17**
- Record and exit: `run.json` `repos`, `features`, Call `feature`; exit 0 only when every feature finished and no record is left; a run with nothing to run but an old park exits 6, verifies **AC-18**, **AC-19**
- `wf queue`: prints the plan with options and `would clear:`, makes no call and no write, leaves locks free, runs with no `claude` on PATH and no ntfy config, verifies **AC-20**
- `wf unpark`: exact, substring, ambiguous (exit 1), none, locked repo (exit 5), verifies **AC-21**
- Manual: the four checks in `verify.md`, verifies **AC-22**

## Build plan

Skateboard: each step leaves `wf run` usable. Step 1 is already the queue inside one repo; later steps make it remember, move across repos, and keep questions. Build after features 6, 20, 8, 7 and 9 (it amends their classification and record).

1. Queue inside one repo: `wf.sections`, queue and startable rules (decision box, `· skipped`, sync owed, ambiguous headings), per feature `pick_next`, feature boundary, the pick loop over one repo, park continues to the next feature, `features` and Call `feature` in `run.json`, per feature `--max-calls` and debug count, tests, satisfies **AC-2**, **AC-3**, **AC-8**, **AC-16**, **AC-18**
2. State file and park memory: `queue.json` read, validate, locked transactions and atomic write, mid run failure; Park records with section hash and `cap`, the recorded set, clearing rules; tree rule; exit codes; tests, satisfies **AC-3**, **AC-7**, **AC-10**, **AC-17**, **AC-19**
3. Decision queue: Decision records instead of the in place wait, id draw in the transaction, `pings` and `acks`, polling after calls and the cursor, replies for any record, `<id> accepted`, answered first pick order, resume from the record with removal after classification, stale rules, fresh debug snapshot, end wait, `decision_timeout` removed, tests, satisfies **AC-7**, **AC-11**, **AC-12**, **AC-13**, **AC-15**
4. Across repos: bare `wf run` from the trust list, per repo checks as skips, all locks and guard baselines at the confirm, the plan print and confirm, repo stop vs run stop including the `guard_changed` split, app stop between features, re-ping at start, `repos` in `run.json`, tests, satisfies **AC-1**, **AC-4**, **AC-5**, **AC-6**, **AC-8**, **AC-9**, **AC-14**, **AC-18**
5. `wf queue` and `wf unpark`, tests, satisfies **AC-20**, **AC-21**
6. Manual checks in `verify.md` on the real claude and phone, satisfies **AC-22**

## Consequences

**Positive**:
- One night builds every queued feature it can, and the morning starts with a list of parks and open questions instead of one stopped run.
- A phone answer is never wasted: it resumes the asking session even after the run that asked has ended.
- The queue stays the scope files plus one state file; nothing new to keep in a repo.

**Negative / tradeoffs**:
- A dirty repo with any park or open question blocks every other feature there until you commit, stash or unpark; your own uncommitted changes count as dirty too. Skills that leave work uncommitted make this common.
- All features in a repo share its one branch until feature 14; work from several features lands on it together. Spec 0010's design gate reads the whole branch, so one feature's uncovered frontend files make every later feature in that repo park `design_gate` at `/sync`.
- Answers first, then repos in trust list order: a long queue in an early repo can use up `--max-hours` before later repos get a turn.
- One usage limit wait per run now covers a whole queue, so a second limit in a long night stops every remaining feature.
- ntfy.sh keeps messages about 12 hours, so a reply sent while no run polls for longer than that is lost; the next run's re-ping asks again.
- Section hash unparks on any edit inside the section, including a `/sync` of another feature that rewrites a status line there; that costs one retry.
- A resume can come hours later in a session whose files changed meanwhile (by that feature, by an answered resume after another feature's park, or by you).
- Holding every planned repo's lock for the whole run blocks a second `wf run` on any of them, even a repo the first run is only waiting in.
- Calls count per feature, so a night with many queued features can make many more calls than before; `--max-hours` is the only run wide bound on calls.
- Untagged features no longer run with `wf run <repo>`; you tag them `· auto` first.

**Neutral**:
- Amends spec 0004 (AC-1 feature choice, AC-2 box checks and exit 3, AC-3 plan, AC-6 rule 10, AC-9 several locks, AC-10 record, AC-14 exits), spec 0005 (AC-8 replies across runs, the cursor and the ack, AC-9 end wait, AC-10 resume source, `decision_timeout`), spec 0007 (AC-7 baseline at the confirm for every held repo, `guard_changed` scope), spec 0008 (AC-1 three scopes, AC-2 per feature debug count, AC-10 `parked` moves to features) and the reason sets of specs 0009 and 0010. `/develop` notes each when it builds the step.
- `docs/architecture.md` changes in the same commit as this spec: components (`queue.json`, `wf queue`, `wf unpark`), data flow (park and move on), invariants 4, 6 and 8.

## Follow-up

- [x] Spec 0004 follow up "skip waiting boxes instead of refusing" closes with AC-3. (closed by spec 0011 AC-3)
- [x] Spec 0005 follow up "turn the in place wait into park and move on" closes with AC-11. (closed by spec 0011 AC-11)
- [x] Spec 0008 follow up "feature 10 moves on after a park" closes with AC-9. (closed by spec 0011 AC-9)
- [ ] Feature 13 (morning report) reads `run.json` `features` and `queue.json`.
- [ ] Feature 14 (branch per spec) may lift the dirty repo block and the branch wide design gate cascade; revisit AC-7 then.
- [x] Root `AGENTS.md` Commands: `wf queue`, `wf unpark`, bare `wf run`; `/sync` owns this. (closed: AGENTS.md Commands)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
