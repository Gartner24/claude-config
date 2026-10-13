# 0020. One command: wf

**Date**: 2026-10-13
**Status**: Proposed
**Paths:** `runner/wf.py`, `runner/run.py`, `runner/finish.py`, `runner/report.py`, `runner/e2e/run.py`, `install.sh`, `rules/runner-handoff.md`, `rules/scope-contract.md`
**Amends**: [0004](../0004-headless-step-loop/index.md) AC-9 (every lock holder writes its line), [0007](../0007-push-guard/index.md) AC-7 (a swap made by `wf` is taken, not a stop), [0011](../0011-build-decision-queue/index.md) AC-3 (parks are taken back by what changed), [0017](../0017-several-repos-at-once/index.md) AC-1 (a repo a run holds is skipped, not refused), [0018](../0018-morning-report/index.md) AC-2, AC-6 (texts say `wf`), [0019](../0019-live-setup-steps/index.md) AC-3, AC-4 (no repo locks, no refusal for a run, staged swap, live dir).

## Summary

You type `wf` and nothing else. After one confirm screen it shows the morning report, swaps any pending live setup steps into `~/.claude` in one fast swap, takes back features whose cause of failure has changed, starts every repo with work side by side, and runs the real claude checks beside those builds. A run that is already going is never stopped or waited on: it accepts a swap made by `wf` (a ledger of fingerprints tells it apart from any other change) and uses the new setup from its next call. `wf finish`, `wf unpark`, `wf report`, `wf queue` and `wf run` stay inside as internals, and nothing tells you to type them.

## What you're agreeing to

- `wf` alone does the whole morning: report, setup swap, retakes, builds, checks, after one Enter (or `-y`).
- A run already going keeps going; it takes the new setup at its next call, and any other change to `~/.claude` still stops it.
- The setup is built in a temp copy first (install.sh and its self checks run there); only if every step passes are the changed files renamed into place, settings.json last. `wf` itself runs from its own copy outside the repo, one folder per version, so a run can edit the repo's runner code and never mixes old and new runner code.
- A parked feature comes back only when what its failure depends on changed (a commit, a setup swap, a new Claude Code version, a higher cap); otherwise the screen says what would bring it back.
- No lock is held longer than the step that needs it, and every refusal names the real holder.

## Requirements

**User stories**:
- As you, any time of day, I want to type `wf` and have everything due done, so I never remember a subcommand or wait on a run.
- As you, I want a run going overnight to survive my morning `wf` and pick up the new setup.

**Acceptance criteria**:
- **AC-1** (the command): bare `wf [-y] [--jobs N] [--budget ...] [--call-timeout ...] [--max-calls ...] [--max-hours ...] [--max-wait ...]` (the `wf run` caps, same defaults) works from any folder and covers every repo on the trust list. It refuses `unattended`, exit 5, when `WF_RUN` is set, and `no_tty`, exit 5, when stdin is not a terminal and `-y` is not given. Before the screen it finishes any interrupted swap (AC-4). It takes no repo lock to plan: each repo is read, and a repo whose lock is held is listed `running: <name>: <holder>` (AC-9) and given no build, without changing the exit code. `next`, `wf allow` and `wf ntfy` stay as they are; the other subcommands stay as internals.
- **AC-2** (the screen): one screen, in this order, each section left out when empty: `report:` the unseen morning report (`<state>/report.txt` when `report.seen` is absent, plus the spec 0018 AC-6 killed run line); `setup:` each copy and install step as `<phase>: <repo>: <feature>: <command>`, or one line `setup update already in progress, pid <pid> since <time>` when the swap lock is held (AC-3); `checks:` each check step the same way; `retake:` each park taken back as `<repo>: <feature>: <reason> (<what changed>)`; `parked:` each park kept as `<repo>: <feature>: <reason>: retaken on <what would retake it>` (AC-6); `build:` each repo with work and its queued features (spec 0017 plan lines); `running:` repos a run holds; `yours:` boxes listed as yours (spec 0019 AC-2 reasons). When the swap lock is held, `setup:` and `checks:` hold only that one line. `<what changed>` is one of a fixed set: `a new commit`, `setup <stamp>`, `claude <old> -> <new>`. The `build:` lines are the ones `Run.plan()` prints for bare `wf run` today (spec 0011 AC-6, spec 0017 AC-1), with no repo lock kept. Then `Enter to go, anything else cancels: ` unless `-y`: only an empty line goes on; any text (`y` included), EOF or Ctrl C cancels, exit 130, nothing changed. With nothing in setup, checks, retake or build, it prints the report (if any), then `nothing to do`, writes `report.seen`, exit 0.
- **AC-3** (staged setup): after the confirm, `wf` writes `report.seen` (spec 0018 AC-5 content), then, when there are setup steps, takes the swap lock `<state>/swap.lock` (non blocking; held: skip setup and checks with the AC-2 line, go on to AC-6). It builds `<state>/finish/<stamp>/stage/` (mode 0700) as a copy of the live dir's `agents`, `rules`, `hooks`, `scripts`, `commands`, `skills`, `settings.json`, `settings.local.json`, `CLAUDE.md` and `private` (links kept as links, absent ones skipped). Copy steps write into the stage at `<rel>`. Each install step runs `./install.sh` as today (spec 0019 AC-4: argument list, repo as working directory, own process group, log file) with `CLAUDE_LIVE_DIR=<stage>` and `WF_STAGE=1` added to your environment. With `WF_STAGE=1`, `install.sh` skips its writes outside `$LIVE` (the runner copy of AC-12, the `~/.local/bin` links and the repo's `.git/hooks` copies) and prints `staged: bin links and git hooks left to wf`; its other self checks run as today (some read the repo, not the stage, which is fine: they test repo code). Without `WF_STAGE`, `install.sh` behaves exactly as today, so the spec 0013 self checks through `CLAUDE_LIVE_DIR` keep passing. A failed copy or install: no swap, checks skipped, the screen's last lines name the failed step and its log, and `wf` goes on to AC-6 and AC-7 on the setup that is live now. The failed stage is kept for you to read; on success the stage is deleted after AC-4; at most the 3 newest stage folders are kept. The live dir is `live_dir()`: `$CLAUDE_CONFIG_DIR`, else `~/.claude`, one helper in `runner/run.py` used by every place in `runner/` that names `~/.claude` today (`freeze_guard`, `deny_paths`, `user_exclusions`, `user_read_denies`, the hook token and plugin globs, `finish.live_dir`), replacing spec 0019's `CLAUDE_LIVE_DIR` for `wf` itself, so the swap, the guard and claude read the same folder.
- **AC-4** (the swap): the changed set is every path under the stage that is absent from the live dir or differs from it (bytes and mode for a file, target for a link); nothing is ever deleted from the live dir. Added to the changed set: for each install step of a repo, the `install.sh` parts `WF_STAGE` skipped, computed by `wf` with the same code `install.sh` uses (the AC-12 runner copy: when its `<fp>` folder is absent, the whole folder is written as `<fp>.wf-swap-<stamp>` beside it and renamed into place in one step, first of all renames; the `wf` and `next` links under `~/.local/bin` to that copy, renamed right after the folder; and the `spec-paths` link to the repo's file; and the `pre-commit` and `commit-msg` copies of `scripts/private-names.py` under the repo's git hooks folder, with the same replace rules as install.sh:165-193; a hook it would leave alone is left alone). Order: first `wf` writes `<state>/finish/<stamp>/swap.json` `{"renames": [[aside, live], ...], "done": false}`; then, for each, the new file or link in the same folder as `<name>.wf-swap-<stamp>` (folders made as needed); then one ledger line appended to `<state>/swaps.jsonl` (mode 0600): `{"stamp", "pid", "at", "files": {<path>: <sha256 of the new content>}}`, which names the git hooks copies too, and every file of the AC-12 copy folder whether or not the folder already existed. For a link, the ledger value is the sha256 of the content it resolves to (what the guard's `file_hash` reads), not `link:<target>`; `swap.json` keeps the target for the rename. After the renames `wf` sets the picked copy folder's mtime and prunes as AC-12 does. With SIGINT, SIGHUP and SIGTERM blocked (`signal.pthread_sigmask`), it renames every aside file onto its live path with `os.replace`: the AC-12 copy folder first, then the `~/.local/bin` links, then every other path except the settings files, then `settings.local.json`, then `settings.json` last (a running call rereads settings mid call, verify.md P1, so a hook settings names must already be in place). Then `"done": true`, signals unblocked, the swap lock released, and each copy and install box counts as passed. A `swap.json` with `"done": false` found at the next `wf` start (under the swap lock; held: left to its holder) is finished forward (each rename whose aside file still exists; when its ledger line is missing, the aside files are deleted instead and nothing is renamed, since no run could accept them), printed as `finished an interrupted swap from <stamp>` or `dropped an interrupted swap from <stamp>`, then marked done. Any `*.wf-swap-*` file in a `swap.json` path list that is `done: true`, or named by no `swap.json`, is deleted at that start.
- **AC-5** (runs take the swap): wherever a run checks its guarded files (spec 0007 AC-7, spec 0011 AC-9: before each call, after an app stop, before the design check), a moved guarded file is accepted when some `swaps.jsonl` line's `files` maps that path to its current hash (no time test: a run that started mid swap must still accept the last renames; the byte exact fingerprint carries the safety). When every moved file is accepted, the run rebuilds, for each held repo, only the parts of its guard derived from the live dir: the settings files read, their hook scripts (`hook_tokens`), the plugin `hooks.json` list, the deny paths under the live dir and the sandbox settings built from them. Every guarded path of the repo itself (git config, git hooks, include targets, submodules, the repo's `.claude`) keeps its old baseline hash, except a path the ledger accepted. A path that is new in the rebuilt list (a hook script the new settings name) must be accepted by the ledger the same way, else `guard_changed` as today. On success the new guard replaces the old, the next call gets the new `--settings` and deny list, and the run logs `setup <stamp> taken` in `log.txt` and appends `{"stamp", "at"}` to a new `run.json` field `setups`. Any moved file not accepted stops the run `guard_changed` exactly as today. Every call's Edit deny list gains the state folder (`path_rules("Edit", state_dir())`), and its Bash sandbox already cannot write there.
- **AC-6** (retakes): a Park record gains `head` (`git rev-parse HEAD`, else null), `setup` (the newest `swaps.jsonl` stamp at park time, else null) and `claude` (first word of `claude --version`, else null). Under `queue.lock` only (no repo lock), `wf` deletes each Park record of a trusted repo whose cause changed: `verify_failed`, `blocked`, `no_progress`, `debug_touched`, `design_gate`, `unchecked`, `app_failed` when a commit since `head` changed a file outside the scope folder and `verify.md` files (`git diff --quiet <head> HEAD -- . ':!docs/scope' ':!.workflow' ':!**/verify.md'` exits 1), since `wf`'s own tick commits and every `/sync` move HEAD without fixing anything (a record with no `head`: the committer time of the newest commit touching such a file, `git log -1 --format=%cI -- <same paths>`, is later than `parked_at`); `denied` and `call_timeout` when `swaps.jsonl` has a stamp newer than `setup`, or `claude --version` now differs from `claude`. A null `setup` or `claude`, or a failing `claude --version` now, means unknown: that signal never retakes. Cap parks (`budget`, `max_calls`, and `call_timeout` by its cap) are left to `applies()` exactly as today (spec 0011 AC-3, its unconfirmed `cap` null rule included); `wf` only reads it to print the line. A section text change still clears any park, as today. Every other park stays, with its `retaken on` line: `a new commit`, `a setup change or a new Claude Code version`, `a higher --<cap>`. Decisions are not touched.
- **AC-7** (builds): after AC-3 to AC-6, `wf` starts the builds as bare `wf run` does (spec 0017: one child per repo with work, `--jobs`, ports and git dirs never shared, `[<name>]` prefixed output, one morning report from all children), except that a repo whose lock is held is a `running:` skip, not a refusal, and a child refused `locked` at its own start (a run took the lock after the plan) counts as skipped, not as exit 6.
- **AC-8** (checks beside builds): right after the builds start (or after AC-6 when there are none), the check steps run in the parent, one at a time, beside the children, as spec 0019 AC-4 runs them (each distinct command once per repo, log file, output prefixed `[check]`), and only when the swap passed. A check step never writes the live dir: the end to end check and every probe use temp folders (`CLAUDE_CONFIG_DIR` and `XDG_*` of their own); a test runs the checks against a fake live dir and asserts its tree is byte equal before and after. When the last check ends: spec 0019 AC-5 records each result in verify.md, AC-6 ticks every box whose steps passed (copy and install boxes included), and AC-7 commits per repo. A commit that fails because git's index lock is held is retried 3 times, 2 seconds apart, then prints `edits left uncommitted in <repo>: <git error>`. Ctrl C forwards SIGINT to every child (spec 0017 AC-5) and to the running check's group; no further check starts; results that ended are still recorded.
- **AC-9** (locks): every lock taker (`wf run` at its lock, `wf unpark`, the swap lock) writes its holder line `<pid> <ISO time> <what>` (`<what>` is `wf run <repo name>`, `wf unpark`, or `wf setup swap`) right after winning the lock: one `os.pwrite` of the new line at offset 0, then `os.ftruncate` to its length, so a loser never reads an empty file (today's truncate then write left that window, run.py:2101), and every refusal or `running:` line prints that line. `wf finish` takes no repo lock and never refuses because a run holds one. No lock is held past the step it guards: plan reads take none, a retake holds only `queue.lock`, the swap lock covers stage, install and renames only.
- **AC-10** (one command everywhere): no runner output, report, hook line or rule tells you to type `wf finish`, `wf unpark`, `wf report`, `wf queue` or `wf run`: those texts say `wf` (park lines `(wf unpark to retry)` become `(retaken on <what would retake it>)`, the report's next line and the session start line say `wf`, `next: wf run` and `next: fix the FAIL lines, then wf finish` become `next: wf`). `rules/runner-handoff.md` step 4 says "Ready for the runner: type `wf` in a terminal." and its morning steps run `wf queue` themselves without telling you to. `rules/scope-contract.md` says `wf` where it says `wf finish`. A test walks every string constant in `runner/*.py` (docstrings and `build_parser` help texts left out) and every line of the repo copies of `rules/runner-handoff.md` and `rules/scope-contract.md`, and asserts zero matches, ignoring case, of ``\b(type|run|then|next:)\s+`?wf (finish|unpark|report|queue|run)\b`` and of `\bwf (finish|unpark|report|queue|run) to (retry|accept)\b`, printing every offender. Naming an internal as a thing (`a wf run holds this repo`, `` `wf run` refuses ``) is fine; telling you to type it is not. The rule's session start line is worded "read the queue (`wf queue`, read only) yourself".
- **AC-12** (runner copy, amendment 2026-10-13): one function, `install_runner(repo, home, dry)` in `runner/finish.py`, does the whole copy, and `install.sh` calls it (`python3` with the repo's `runner/` on the path), so the copy has exactly one implementation. It copies `runner/*.py` (not `tests/`, `e2e/` or `__pycache__`, which is left alone and never hashed) into `<home>/.local/share/wf/<fp>/`, where `<fp>` is the first 12 hex digits of the sha256 over, for each file in name order, its name, a NUL byte, its bytes and a NUL byte. The folder is written as `<fp>.tmp-<pid>` and renamed into place in one step, and left alone when `<fp>` already exists. It then points `<home>/.local/bin/wf` and `next` at `<fp>/wf.py` (link replace, with today's `SKIP` for a real file in the way), sets the chosen folder's mtime to now (it is the folder's "last picked" time), and deletes every other folder under `<home>/.local/share/wf` whose mtime is older than 7 days and that no `<home>/.local/bin` link points into. With `dry` it changes nothing and prints one `would:` line per step, as `install.sh --dry-run` does today. It returns `<fp>`. `spec-paths` stays linked to the repo. Why: spec 0007's `hook_tokens` turns the SessionStart hook's `~/.local/bin/wf` into its real path and `deny_paths` denies that file's folder, so with the link into the repo every `wf run` call is denied Edit on `runner/` (verify.md P2). With the copy, the denied and hashed folder is the copy, never the repo. `deny_paths` also denies `~/.local/share/wf` as a whole, so no call edits any copy. A running `wf` keeps importing from its own folder (Python puts the resolved script folder first on its path) and bare `wf run` starts its children from `realpath(__file__)`, so a run never mixes versions, and a folder picked in the last 7 days is never pruned under it. Tests call `install_runner` directly with a temp `home` and a temp repo (never `install.sh` itself, whose self checks run the unit suite) and assert: both links resolve under `.local/share/wf/<fp>/`, the copy holds every `runner/*.py` and no `tests`, a second call with the same files makes no new folder, a call after a runner change makes a new folder and keeps the old one, a folder older than 7 days and unlinked is pruned while a linked old one is kept, `dry` changes nothing, and `deny_paths` from a settings hook naming the link holds no path under the repo and holds `~/.local/share/wf`. One `install.sh --dry-run` check asserts the `would:` copy line.
- **AC-11** (real check): `runner/e2e/run.py --beside` makes two temp repos A and B from the fixture, a temp `XDG_STATE_HOME`, `XDG_CONFIG_HOME` and `CLAUDE_CONFIG_DIR` (your login copied in, removed at the end however it ends), starts `wf run A -y` in the background, waits until A's first call has started, then gives B a live copy box whose file changes the temp `settings.json` hook script and runs `wf -y`. It prints `PASS` only when `wf` exits 0, the swap ledger names the file, A's `run.json` ends `feature_done` with one `setups` entry and a call started after it, B's box is ticked, and then a second hand made change to the temp `settings.json` during a fresh run of A stops it `guard_changed`. Otherwise `FAIL: <check>`. You run it as a live step.

## Decision

**Chosen option**: Option 1: bare `wf` as one orchestrator over the existing internals, with a staged per file swap, a fingerprint ledger the runs trust, and per reason retakes.

## Feature design

**Data model sketch** (files, all under `<state>` = `$XDG_STATE_HOME/wf` else `~/.local/state/wf`):
- `swaps.jsonl` (new, 0600, append only): one line per swap, `stamp` (`YYYYmmdd-HHMMSS`), `pid`, `at` (ISO), `files` {live path: `sha256` hex of the content, for a link the content it resolves to}.
- `finish/<stamp>/stage/` (new): the staged live tree. `finish/<stamp>/swap.json` (new): `renames` [[aside, live]], `done` bool.
- `swap.lock` (new): holder line `<pid> <time> wf setup swap`.
- `locks/<sha1>.lock`: holder line gains `<what>`; written by every taker.
- `queue.json` Park record: gains `head` (str or null), `setup` (str or null), `claude` (str or null). `PARK_FIELDS` grows; an old record without them still loads.
- `run.json`: gains `setups` [{`stamp`, `at`}].
- `~/.local/share/wf/<fp>/` (new, AC-12): one copy of `runner/*.py` per fingerprint; `wf` and `next` link into the newest install's folder.
- Live dir aside files: `<name>.wf-swap-<stamp>`, present only between AC-4's write and rename.

**State per swap**: none, staged, failed (no rename, stage kept for you to read), aside written, ledger written, renaming (journal `done: false`), done.

**API surface**:
| Command | Inputs | Output | Exit |
|---|---|---|---|
| `wf [-y] [--jobs N] [caps]` | trust list, scope files, `queue.json`, `report.txt`, `swaps.jsonl`, locks, `claude --version`, git HEADs | report seen, staged swap, ledger, retakes, children, check logs, verify.md lines, ticks, commits | 0 all passed or nothing to do; 1 a step or commit failed; 5 refused; 6 a child exited non zero (spec 0017 AC-6); 130 Ctrl C or cancel |
| `wf run` (internal) | as today, plus `swaps.jsonl` at each guard check | `setups` in run.json, `setup <stamp> taken` in log.txt | as today |
| `wf finish`, `wf unpark`, `wf report`, `wf queue` (internal) | as today | as today, texts per AC-10 | as today; `wf finish` never `locked` |

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| plan | repos | trust list (spec 0008) |
| plan | report | `<state>/report.txt` unless `report.seen` (spec 0018) |
| plan | setup and check steps | live boxes (spec 0019 AC-1, AC-2) |
| plan | running repos and holders | lock files' holder lines (AC-9) |
| stage | live dir | `$CLAUDE_CONFIG_DIR`, else `~/.claude` |
| stage | what is staged | the folders and files `install.sh` writes, plus `CLAUDE.md` and `private` it reads |
| swap | changed set | stage vs live dir compare (AC-4) |
| swap | rename order | settings files last, `settings.json` very last (verify.md P1) |
| run | accepted change | `swaps.jsonl` lines after the run's last baseline (AC-5) |
| retake | head at park, now | `git rev-parse HEAD`; committer time `git log -1 --format=%cI` for old records |
| retake | setup at park, now | newest `swaps.jsonl` stamp |
| retake | version at park, now | first word of `claude --version` |
| retake | cap | the `wf` cap flag vs the record's `cap` (spec 0011 AC-3) |
| commit | retries | fixed: 3 tries, 2 s apart |
| lock | holder line | `os.getpid()`, now, the fixed `<what>` per taker |

**Key invariants**:
- `wf` never stops, waits on, or refuses because of a run. The only waits are the one confirm and its own steps.
- No Claude ever reads a half written file: every live write is a rename of a whole file.
- A run accepts only changes whose exact fingerprint `wf` wrote to the ledger after the run's last baseline; everything else stops it as before.
- Nothing is deleted from the live dir by a swap, except `wf`'s own `*.wf-swap-*` aside files.
- A check step never writes the live dir.
- A failed setup step never touches the live dir.
- Spec 0019's shape rules, backups (the stage is a full copy, and `finish/<stamp>/claude/` backups of every changed path are still taken before the renames), no push, no commit on `main` or `master` all still hold.

**Security model**: the ledger is trusted only as far as the threat model of spec 0007 (an accidental or prompt injected change, not a model working to escape). A call cannot write the live dir (its Edit deny and sandbox already forbid it) and, with AC-5, cannot write the state folder through Edit either; its Bash sandbox already cannot. So a call can neither change `~/.claude` nor forge a ledger line, and a ledger line accepts only a byte exact fingerprint, so a stray change by anything else (another session, a script) still stops runs. A running call sees the new settings and hooks mid call (P1); that is accepted: they are whole files you approved on the confirm screen.

**Configuration required**: none new. `CLAUDE_CONFIG_DIR` (already read by claude and by spec 0014's log) now also names the live dir `wf` swaps and the guard hashes.

**Critical test scenarios** (fake `claude`, temp state, config and live dirs, temp repos):
- One `wf -y` with a report, a copy box, an install box (fake install.sh writing into `$CLAUDE_LIVE_DIR`), a probe box, a park whose HEAD moved and a repo with work: report seen, stage built, ledger line, files renamed with `settings.json` last, boxes ticked, park dropped, child started, check recorded: AC-1 to AC-4, AC-6 to AC-8.
- A held repo lock shows `running:` with the real holder line and exit stays 0; a held swap lock skips setup and checks with the one line and still retakes and builds: AC-2, AC-3, AC-9.
- A failing install: live dir untouched, checks skipped, builds still start, exit 1: AC-3.
- A `swap.json` left `done: false` with aside files and a ledger line: next `wf` finishes the renames; one without a ledger line: asides deleted, nothing renamed; a stray `*.wf-swap-*`: deleted: AC-4.
- `install.sh` with `WF_STAGE=1` into a temp live tree writes no `~/.local/bin` link and no git hook (temp `HOME`, temp clone) and prints the staged line; without it, unchanged: AC-3. The swap then writes those hook copies and the ledger names them; a run holding that repo takes them: AC-4, AC-5.
- A run started between two renames of one swap accepts the later renames: AC-5.
- A guard rebuild after an accepted swap keeps the old hash of a repo git hook that moved without a ledger line, so the next check still stops `guard_changed`: AC-5.
- A park whose only new commit touched `docs/scope` and a `verify.md` stays parked: AC-6.
- Two lock takers racing: the loser never prints `unknown`: AC-9.
- The checks leave a fake live dir byte equal: AC-8.
- A run with a moved `settings.json` whose hash is in a ledger line after its start rebuilds its guard and logs `setup <stamp> taken`; the same change with no ledger line, a ledger line older than the baseline, or a different hash stops `guard_changed`; a new hook script named by the new settings and in the ledger is taken, one not in it stops: AC-5.
- The call argv carries an Edit deny for the state folder: AC-5.
- Each park reason class retaken or kept by its trigger, an old record without `head` judged by committer time, a cap park by a higher cap: AC-6.
- A commit hitting a held `index.lock` retries and then prints the uncommitted line: AC-8.
- A child refused `locked` after the plan counts as skipped: AC-7.
- Corpus test of AC-10 green, and red on a planted `wf finish` in a print: AC-10.

## Build plan

Skateboard: first stop the waiting (locks), then make runs survive a swap, then the swap itself, then retakes, then the one command over all of it, then the words.

0. `install.sh` runner copy into `~/.local/share/wf/<fp>/`, links to it, prune, with its self check, satisfies **AC-12**. First, so later `wf run` calls can edit `runner/`.
1. Holder line written by every lock taker; `wf finish` drops `lock_all` and its `locked` refusal; bare `wf run` plan and children treat a held repo as `running:` skip. Tests in `runner/tests/`, satisfies **AC-9**, **AC-7**
2. One `live_dir()` helper replacing every `~/.claude` in `runner/` (grep `.claude` in `runner/`); `swaps.jsonl` reader, ledger acceptance in `files_changed`, rebuild of the live dir parts only, `setups` and log line, state folder Edit deny, satisfies **AC-5**
3. `install.sh` `WF_STAGE` skip of bin links and git hooks, with its self check; staged setup and swap in `runner/finish.py`: stage copy (0700, cleanup), install with `CLAUDE_LIVE_DIR=<stage>` and `WF_STAGE=1`, changed set plus bin links and git hooks, journal, aside files, ledger, signal block, ordered renames, forward finish or drop of a left journal, orphan sweep, swap lock, satisfies **AC-3**, **AC-4**
4. Park fields `head`, `setup`, `claude`; retake rules per reason (diff outside scope and verify.md, unknown never retakes, caps left to `applies()`) with `retaken on` lines, satisfies **AC-6**
5. Bare `wf` in `runner/wf.py`: refusals, plan from all parts, the screen, confirm, then report seen, swap, retakes, builds, checks beside them, record, tick, commit with retries, exit codes, satisfies **AC-1**, **AC-2**, **AC-7**, **AC-8**
6. Texts in `runner/*.py` and repo copies of `rules/runner-handoff.md`, `rules/scope-contract.md` (copy files: never `./sync.sh` before the live steps below); the corpus test, satisfies **AC-10**
7. `runner/e2e/run.py --beside`, satisfies **AC-11**
8. Live steps, one per box, each ` · waits on you · live`: `cp ~/claude-config/rules/runner-handoff.md ~/.claude/rules/runner-handoff.md`, `cp ~/claude-config/rules/scope-contract.md ~/.claude/rules/scope-contract.md`, `python3 runner/e2e/run.py --beside`, satisfies **AC-10**, **AC-11**

## Consequences

**Positive**:
- One command, and it never stands in a run's way or a run in its way.
- `install.sh` self checks run before anything goes live, so a failed self check no longer leaves a half installed setup.
- Parks clear themselves when their cause changed, with a one line reason when they do not.

**Negative / tradeoffs**:
- A Claude starting in the few milliseconds of the rename loop can see some new and some old files (per file, not whole set; agreed).
- A call running during the swap uses the new settings and hooks for its remaining tool uses (P1; agreed).
- A second `wf` during a long swap skips the setup; its steps wait for the next `wf`.
- Checks beside builds: a feature whose last box is a check closes on the next `wf`.
- The guard rebuild after a swap is a second `freeze_guard` per held repo, a few git commands at a call boundary.

**Neutral**:
- `wf finish`, `wf unpark`, `wf report`, `wf queue`, `wf run` remain for tests, the e2e and Claude's own reads.
- The architecture page names `wf` as the entry point and the swap in invariants 6 and 7.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
