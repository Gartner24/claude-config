# Brief: /review-stack of the runner branch, d02d329..c95f181 (2026-10-12)

Verdict WARN (0 critical, 4 high, 13 medium, 13 low). Receipt: `.git/review-stack/c95f1811ed25d4df89955e48f72d2b55bf8f62b2`. 271 tests OK at c95f181.

## Agreed so far, do not ask again

- Fix every HIGH, MEDIUM and LOW code finding below, plus the 3 surviving mutants. Each fix ships with a test, and each test gets a mutation check (break the fix, watch that test go red, restore; clear `__pycache__`, run with `-B`).
- Nothing is recorded as residual unless fixing it needs a decision the build cannot make. Any such item goes in `## Residual` below and is reported to you.
- The plan (`plan()`, the confirm screen) gets back `answers:` (spec 0006 AC-7) and `guard: <n> hosts, <k> files` (spec 0007 AC-9), and adds `app start` and `app url`. Standing answers are read once at the confirm.
- Three spec decisions go to one `/architect` run, and only these three:
  1. `AGENTS.md` `app start` is frozen at the confirm and shown in the plan (finding H2). A call that edits it later does not change what runs.
  2. Amend spec 0009 for 0011's per call app logs: a fresh `app-<seq>.log` per call and a restart on resume replace AC-3 `-rK` logs and AC-10 "one app object across resumes" (finding H4).
  3. Widen the `paid()` env strip (spec 0008 AC-7): `PGPASSWORD`, `*_KEY`, `*_PAT`, `DATABASE_URL`, `SENTRY_DSN` (finding L6).
- After the spec is accepted: build the fixes, run the suite, stop before any merge or push.
- 0006 AC-7 and 0007 AC-9 are restored as written; no amendment needed for them (finding H3). Their verify.md lines get real tests behind them.
- Settled by `/architect` 2026-10-12, accepted (in place amendments):
  - 0011 AC-6: per repo `answers:` and `guard:` lines in the plan (`flat()`, counts are `len(guard.hosts)` and `len(guard.guarded_files)`, no guard line in `wf queue`). Standing answers read once per run, and reread before each call and at feature end only to stop the repo `guard_changed` when the parsed values changed (your pick: watch the answers section). 0006 and 0007 got "moved to the plan block" pointers.
  - 0011 AC-7: pick skips an answered Decision whose feature has a Park that applies (H1).
  - 0011 AC-13: an answered Decision whose feature is no longer queued is stale (L9, your pick: drop it).
  - 0009 AC-3, AC-10: one `app-<seq>.log` per call that starts the app, a resume is its own call with its own `app` object; a retry never restarts the app (H4).
  - 0008 AC-7: `_KEY`, `_PAT` endings and exact `PGPASSWORD`, `DATABASE_URL`, `SENTRY_DSN`; the app gets the same env (L6).
  - 0007 AC-8 missing `claude` exits 1 is 0011 AC-4, so that part of L13 needs no code change.
- Second panel 2026-10-12 (fixes whose text an accepted spec quotes), your picks, all recommended:
  - M7: six common secret files (`~/.npmrc`, `~/.config/git/credentials`, `~/.docker/config.json`, `~/.pypirc`, `~/.kube`, `~/.claude/anthropic_api_key`) join `CREDENTIAL_PATHS` (steps and app); the jail also hides every exact path `~/.claude/settings.json` denies with `Read(//...)`.
  - M9: `Bash(git * push*)` becomes `Bash(git -* push*)` (first built as `-c`, `-C`, `--` forms; the commit security review found `git -P push` past them, so one rule for any option); spec 0004 argv updated; a real claude probe is owed (you run it with `!`).
  - M8 submodule hooks and config guarded like the main repo's; M10 hidden paths bound at their real path; M12 design record per feature entry.
  - L2 the answering reply's id is stored on the record and skipped on later reads; L10 any `#` or `##` heading ends `## Deferred`.
- Cross check: another model (standing). Comma inside an `app start` value in the `answers:` line stays ambiguous, accepted.

## Findings

### HIGH

- H1 `runner/run.py:955`. An answered decision is picked again forever when the resume's `start_app` raises `app_failed` (:1609, before the record is deleted at :1635). `run_feature` parks (:1558), `pick()` returns answered decisions first without checking parks (:953-958), no call is made, only `--max-hours` stops it. Fix: skip an answered decision whose feature has a live park in `pick`, or delete the record when a Stop is raised before `classify` while `resume` is set.
- H2 `runner/run.py:2341`, `read_answers` :1774-1820. A call can write `- app start: <cmd>` into `<repo>/AGENTS.md` (not in `deny_paths`); the next `wf run` runs it in the jail, and `plan()` never shows it. Fix: decision 1 above.
- H3 specs 0006 AC-7 and 0007 AC-9. The `answers:` and `guard:` confirm parts were dropped by the 0011 plan rewrite (run.py:1040-1043); verify.md for 0006 (lines 5, 10, 28) and 0007 (line 124) cite tests that no longer check them. Fix: restore both in `plan()`.
- H4 spec 0009 AC-3, AC-10 contradict the built per call logs (run.py:1607-1609, test_browser.py:566); 0009 verify.md:197-199 describes the old output. Fix: decision 2 above.

### MEDIUM

- M1 `run.py:1531`. `limit_rerun` is not reset per feature; after a `guard_changed` repo stop the next feature's `loop` skips assigning `last`/`base`/`app` and dies on UnboundLocalError (`internal_error`). Fix: reset it in `run_feature`.
- M2 `run.py:1564`. `stop_app()` outside the `try` lets `Stop(guard_changed, repo=True)` escape `run_feature` and end every repo (0011 AC-9). Fix: catch it there and `end_repo`.
- M3 `run.py:1864`. `git diff --name-only` is top relative; a scope repo in a git subfolder loses its frontend changes, the design gate passes. TEST_BASE has the same mismatch. Fix: `--relative`.
- M4 `run.py:1691`. `snapshot()` ignores git's exit code, so a git failure turns the debug guard off. Fix: raise as `git_paths` does.
- M5 `run.py:682`. `git remote -v` unchecked; on failure the repo's own remote is not denied. Fix: refuse `no_sandbox`.
- M6 `ntfy.py:73`. `urlsplit` ValueError escapes `global_checks` (catches only `ntfy.Invalid`, run.py:513). Fix: raise `Invalid`.
- M7 `run.py:55`, `:45`. `JAIL_HIDDEN` and `CREDENTIAL_PATHS` miss `~/.claude/anthropic_api_key`, three secret files of your own (named only in your `~/.claude/settings.json` `Read` denies), `~/.npmrc`, `~/.config/git/credentials`, `~/.docker/config.json`, `~/.pypirc`, `~/.kube`.
- M8 `run.py:758-760`. Submodule git dirs (`<common>/modules/*/hooks`, `config`) are writable and not hashed.
- M9 `run.py:34`. `Bash(git * push*)` also denies `git stash push`, `git subtree push`, and commits whose message contains " push".
- M10 `run.py:731-735`. bwrap fails "Can't mount on symlink destination" when a `JAIL_HIDDEN` path is a symlink; every app start parks `app_failed` on a machine with symlinked dotfiles.
- M11 `run.py:673-676`. Any `OSError` from `listdir` on the hooks folder reads as "no hooks". Catch only `FileNotFoundError`.
- M12 `run.py:1310`. The design record is one slot, overwritten per feature (0010 AC-7).
- M13 `run.py:1691` with `.workflow/`. Untracked specs under the globally ignored `.workflow/` are invisible to the debug guard (0008 AC-3).
- Mutants that survive the suite: M10 `APP_URL` (run.py:159) accepting `0.0.0.0`; M41 `under()` (run.py:2316) without the trailing `/`; M8 `untrusted()` (run.py:2013) without `realpath`.

### LOW

- L1 `run.py:1019`. A repo skipped as `scope_unreadable` in `plan()` keeps its lock fd.
- L2 `run.py:1434`. A re-read reply bumps `ignored` on the decision it answered.
- L3 `wf.py:608`. `--max-wait` help is stale (now a per run end wait budget).
- L4 `wf.py:72`. A box whose text is only the marker gives `owed == ""`, read as not owed.
- L5 `run.py` `cmd_allow`. No lock on `allowed.json`; a shared `.tmp` name races two `wf allow`; no fsync.
- L6 `run.py:89` `paid()`. Misses `PGPASSWORD`, `*_KEY`, `*_PAT`, `DATABASE_URL`, `SENTRY_DSN`. Decision 3 above.
- L7 `wf.py` ~233. `wf.git` has no timeout.
- L8 `run.py:1754`. `internal_error` keeps only the last exception line.
- L9 `run.py:958`. A resumed decision does not recheck `f.queued` (tag removed or `· done`).
- L10 `wf.py:160-183`. A `#` heading after `## Deferred` keeps later `###` features deferred.
- L11 `run.py:2237`. `url_host` splits an IPv6 remote `[::1]` on `:`.
- L12 `run.py:268`. `wf queue` creates `queue.lock` (0011 AC-20 says it changes nothing).
- L13 0006 AC-6 `last_box` (run.py:1507-1517) false for a lone open milestone under a ticked parent; 0007 AC-8 missing `claude` exits 1, not `no_sandbox` (run.py:508-510). Also: ntfy ack failure is silent.

## Build result (2026-10-12)

Every HIGH, MEDIUM and LOW finding above is fixed, plus the 3 surviving mutants. Each fix has a test (`runner/tests/test_review_fixes.py`, and updated tests in `test_run.py`, `test_queue.py`, `test_design.py`, `test_wf.py`), and each passed a mutation check: 41 mutants, each one fix reverted alone, all red (`mutate.py` in the session scratchpad). Suite: 300 tests OK.

Notes from the build:
- H4 needed no code change: the code already wrote one log per call; spec 0009 now says so, pinned by `test_browser.TestLifecycle.test_decision_restarts`.
- L2: a time based fix was tried first and reverted (two replies in the same second broke it); the stored `reply` id replaced it.
- L10: `test_wf` had pinned the old rule on purpose (spec 0002's literal text); it now pins the amended rule.
- M8: a new hook file in a submodule is stopped by `denyWrite`, an existing one by its hash, same as the main repo's hooks.
- The 0007 AC-8 part of L13 is spec 0011 AC-4 (exit 1), no code change.
- The background security review of `0f31657` found 3 issues in these fixes, all fixed with a test and a mutation check (47 mutants, all red; 301 tests OK): the push rule list let `git -P push` through (now `Bash(git -* push*)`); the bracketed scp form `[user@host:port]:path` gave `user@host:port` as the host (now the host alone); the specs walk followed a planted `.workflow/specs` symlink and read links and FIFOs (now walked only inside the repo, links hashed by target text, only regular files read, at most 16 MiB each).

## Residual

- Push rule bypasses (commit review of `126ecf5`): `git -c alias.p=push p` and a quoted `git "push"` match no glob; the old `git * push*` missed them too, so not a regression. Residual under the spec 0007 Threat model (deliberate escape; the guard is no credentials plus denied hosts) and your "no more hardening rounds" rule.
- The same review's size cap finding is fixed, and the next review (of `94a1a84`) caught that hashing the whole file let a sparse `truncate -s 1T` file hang wf. Final rule: read at most 16 MiB per file; a bigger file's hash adds its size, inode and ctime, which any write moves and no call can set back. Tests for both (a 4 TiB sparse file ends in under 3 s), each mutation checked.

None needs a decision. One check is owed and only you can run it (it needs the real claude login):
- M9 push rule probe: `bash docs/specs/0004-headless-step-loop/probes/push-rule.sh`, expected results in that spec's `verify.md`.
