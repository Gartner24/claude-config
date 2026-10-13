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

None needs a decision, and nothing is owed:
- M9 push rule probe: PASS on the real claude (run 2, 2026-10-12, `docs/specs/0004-headless-step-loop/verify.md`).

## /check verify (2026-10-12): PASS

Driven through the real `wf.py` in scratch folders (scratch HOME and XDG dirs, real git, bwrap, socat; a stand in `claude` from `runner/tests/test_run.py` `FAKE_CLAUDE`, since this session has no claude login). Script: `verify26.py` in the session scratchpad.

- [x] H3, L12: `wf queue q` prints `answers: run suite yes, app start npm run dev -- --port 3000, app url http://localhost:3000`, no `guard:` line, and creates no state folder.
- [x] H3: `wf run p` (no tty, cancels exit 130) prints `answers: done yes` and `guard: 9 hosts, 20 files`.
- [x] H2: a call that plants an `app start` and `app url` in `AGENTS.md` gives `stopped repo w: guard_changed: AGENTS.md standing answers changed during the run`, and no second call runs.
- [x] L6: with `DATABASE_URL`, `GITHUB_PAT`, `SENTRY_DSN`, `PGPASSWORD`, `STRIPE_KEY`, `REDIS_URL` set, the call env holds only `REDIS_URL`.
- [x] M8, L11 (and its commit review fix), M9, M7: a repo with remote `[git@git.corp.example:2222]:team/repo.git`, an `ssh://git@[fd00::5]:22` remote and a submodule git dir: `deniedDomains` holds `git.corp.example` and `fd00::5`; `denyWrite` ends with the submodule's `config` and `hooks`; the push rules are `Bash(git push*)`, `Bash(git -* push*)`; `Read` denies cover `~/.npmrc` and `~/.claude/anthropic_api_key`.
- [x] M6: server `https://[x` gives `refused: no_ntfy: server must start with https://`, exit 5, no traceback.
- [x] M5: a git that fails `remote -v` gives `refused: no_sandbox: git remote -v failed: boom`, exit 5.
- [x] L10, L4: `wf queue` shows `queued: 2. Live` under a `# Next up` after `## Deferred` (1. Old stays deferred) and `skip: 3. Phone: waiting` for a box that is only `· waits on you`.
- [x] L3: `wf run --help` says "hours the run waits at its end for your phone replies".
- [x] L5: 12 `wf allow` at once, all exit 0, all 12 paths kept, no stray temp files.
- [x] M13 and both snapshot commit reviews: a debug call that edits an ignored `.workflow/specs/0001-a/index.md` parks `debug_touched` naming it; a debug call that swaps `.workflow/specs` for a symlink to `/` parks the same, in 0.2 s.
- [x] M7, M10 on your real home: `docs/specs/0009-headless-verify-test/probes/p2-built.py` (updated for the spec 0011 repo entry) starts the real bwrap jail with your symlinked dotfiles; every hidden secret is refused or empty inside it, your own `Read` denies included (three secret files of your own); the planted hook is still caught.
- [x] M9: the push probe on the real claude, run 2 (spec 0004 `verify.md`).
- [x] H1, L9, L2, M1, M2, M12, L1, L7, L8, L13, M11, M4 and the 3 mutants need injected faults (a phone reply, a usage limit, an app that fails on restart, a held lock); `runner/tests/test_review_fixes.py` drives them, most through real `wf.py` runs: 32 of 32 ok.
- M3: not reachable through `wf run` today. A scope repo inside a git subfolder is refused `branch: no git` at the start check (`wf` reads `<repo>/.git`), before any design check. The `--relative` fix holds at the function level (`TestGitPaths.test_subfolder`, real git). The refusal itself predates this review.

# Second review stack: c95f181..d20a328 (2026-10-12)

Verdict WARN (0 critical, 3 high, 9 medium, 11 low). Receipt: `.git/review-stack/d20a328f7dc0da796390a019a79a9e949f590ad7`. 306 tests OK at d20a328.

## Agreed so far, do not ask again (second round)

- Fix every HIGH and MEDIUM finding below, plus L8 (cheap), each with a test and a mutation check. The other LOW findings stay as reported.
- The private secret file names are removed from the unpushed commits by rewriting only the commits after `origin/feat/autonomous-runner`, replaced by generic wording; nothing already pushed is rewritten. They also sit in the pushed `settings.json` (the synced copy of the live one), which this does not touch: that cleanup belongs to deferred feature 21.
- Then `/check verify`, `/test`, `/sync`; stop before merge or push.

## Assumed (built on your "fix every finding" without an `/architect` run; each is in its spec's second review amendment)

- Push rules: `Bash(git *subtree push*)`, `Bash(git *submodule foreach*push*)`, `Bash(git *lfs push*)` join `DENIED` (spec 0004 AC-4). Whether Claude Code's matcher reads them as intended is the probe rerun owed to you.
- Jail: a hidden folder that is a write bind or holds one is hidden first, and the binds and read only paths go back on top (spec 0009 AC-3 step 3). With a deny on your whole home, the app sees only the repo, the caches and the read only git and dotfile paths there. (First built as a skip, which the commit review showed exposed the whole denied tree.)
- Specs walk: only when git ignores the specs folder (`git check-ignore`, spec 0008 AC-3).
- A test file past 16 MiB keeps no text; any change to it counts as touched (spec 0008 AC-3).
- A file at or under a repo's submodule `.git` (the text frozen at start) is that repo's own for the repo stop vs run stop split, unless another held repo's path or common dir lies there (spec 0011 AC-9); the guard record gains `submodules` (spec 0007 AC-9).
- A submodule not checked out has its `.git` hashed as absent, not denied (the sandbox placeholder would break git); a symlinked submodule `.git` refuses `no_sandbox` (spec 0007 AC-2).
- `read_answers` follows a symlink to a regular file as before, but refuses anything that is not a regular file once opened, and a file past 16 MiB (spec 0006 AC-3).

## Findings (second round)

### HIGH
- S1 `runner/tests/test_run.py:329`: no test pinned a non-empty `answers:` plan line.
- S2 `runner/run.py:179`: TEST_BASE lacked `--relative` (the other half of M3).
- S3 `docs/specs/0009-headless-verify-test/verify.md:211` and this brief: three private secret file names in a public repo.

### MEDIUM
- S4 `run.py:1891`: `read_answers`, reread after every call, followed a planted FIFO or `/dev/zero` link and hung wf.
- S5 `run.py:74`: `git subtree push`, `git submodule foreach git push` (and `git lfs push`) no longer denied.
- S6 `run.py:706`: submodule guard missed in place `.git` folders, `.git` pointers, `config.worktree` and include targets.
- S7 `run.py:712`: unguarded submodule `listdir`, and `os.walk` without `onerror`.
- S8 `run.py:776`: a Read deny holding the repo put a tmpfs over the repo bind.
- S9 `run.py:1784`: the specs walk also ran over tracked `docs/specs`, hashing its ignored files.
- S10 `run.py:925`, `:965`: `survey()` `- set(live)` and the `decision_lines` parked flag had no test going red.
- S11 specs 0008 AC-3, 0007 AC-8, 0011 AC-13 lagged the code.
- S12 `run.py:1808`: an edit past the cap of a big test file was not seen by `touched()`.
- L8 (first round, partial): the trace reached stderr only.

## Build result (second round)

Every finding above is fixed. Tests in `runner/tests/test_review_fixes2.py` (16) plus updated `test_run.py`, `test_browser.py`, `test_review_fixes.py`. Mutation check: 31 mutants, each one fix reverted alone; 30 went red on the named test. The survivor was a CRLF translation in `read_answers` that the parser never needed, so it was removed. Suite: 322 tests OK.

The background security reviews of the fix commit found 5 issues in these fixes, all fixed with a test and a mutation check: the jail skip exposed the denied tree (now hidden first, binds on top); a submodule not checked out was unwatched (now hashed absent); a symlinked submodule `.git` went unhashed (now refused); `own_file` resolved the submodule folder at check time, so a call could swap it for a link to `/` (now the frozen `.git` text); and it ignored another held repo whose common dir lies in the submodule (now checked).

Owed to you: the push rule probe rerun on the real claude (steps 9 to 11, spec 0004 `verify.md`).

## /check verify, second round (2026-10-12): PASS

Driven through the real `wf.py` in scratch folders (scratch HOME and XDG dirs, real git and bwrap; the stand in `claude` from `runner/tests/test_run.py` `FAKE_CLAUDE`). Script: `verify27.py` in the session scratchpad.

- [x] S1: `wf queue q` prints `answers: run suite yes, app start npm run dev -- --port 3000, app url http://localhost:3000`; `wf run` on an app repo prints `answers: app start <cmd>, app url http://127.0.0.1:<port>` and `guard: 9 hosts, 6 files`.
- [x] S4: a call that swaps `AGENTS.md` for a FIFO gives `stopped repo demo: guard_changed: AGENTS.md standing answers changed during the run`, one call, in 0.1 s.
- [x] S5: the call's `--disallowedTools` holds `Bash(git *subtree push*)`, `Bash(git *submodule foreach*push*)`, `Bash(git *lfs push*)`. Whether the real claude denies them is the probe rerun owed to you.
- [x] S6: with an in place submodule and an absorbed one with an include: `denyWrite` holds both `config` and `hooks`, the pointer, both `config.worktree` and the include target; `Edit(/<repo>/lib/.git/**)` is denied; `submodules` lists both `.git` paths; a call that rewrites the pointer gives `stopped repo demo: guard_changed: <repo>/vend/.git changed`.
- [x] S7: an unreadable submodule hooks folder and an unreadable folder under `modules` each give `refused: no_sandbox: cannot list <folder>: Permission denied`, exit 5.
- [x] S8: the real bwrap jail with `Read(//<home>/**)`: the app reads and writes the repo (`repo visible`, `new`), a file elsewhere in the denied home is gone, the denied vault lists empty.
- [x] S9, S12: on a real repo, the snapshot holds `docs/specs/index.md` and not the ignored `__pycache__/p.pyc`; a skip appended past 16 MiB of a 17 MiB test file gives `touched() == ['tests/test_big.py']`.
- [x] S2: a real `/test loop` call's prompt says `git diff --relative --name-only --diff-filter=ACMR`.
- [x] S10: `wf queue` on a parked answered decision shows `resume:`, `parked: 1. A: blocked: test park (wf unpark to retry)` and `nothing to run`.
- [x] L8: an internal error prints `stopped: internal_error: RuntimeError: forced failure`, and `traceback.txt` in the run folder holds the whole trace.
- [x] Commit review fixes (absent and symlinked submodule `.git`, `own_file` frozen text and shared common dir): `test_review_fixes2.TestSubmodules`, real `wf.py` runs, 7 of 7 ok.
- S3: no commit after `origin/feat/autonomous-runner` adds the three names (`git log -G` over the range is empty); the final tree matched the pre-rewrite tree byte for byte.
