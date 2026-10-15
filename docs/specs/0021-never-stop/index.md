# 0021 · Never stop: a case for every stop

**Date**: 2026-10-13
**Status**: Accepted (2026-10-13, conductor session, recommended answers per docs/briefs/finish-runner-today.md)
**Paths:** `runner/run.py`, `runner/wf.py`, `runner/report.py`, `runner/ntfy.py`
**Amends**: [0011](../0011-build-decision-queue/index.md) AC-9 (parks), [0014](../0014-runner-resilience/index.md) AC-2 (crash loop), [0008](../0008-failure-and-park-policy/index.md).

## What you're agreeing to
- You queue features, go to sleep, and in the morning they are built. Nothing sets a feature aside in silence.
- Every reason the runner stops today has one case below. Most become a phone question with a recommended answer; the run keeps building everything else, and your answer resumes the feature (the same night, or on the next `wf`).
- Only you stopping it (Ctrl C, Autopilot off) still stops a run. Nothing stops the whole run because of one repo.

## The cases

The source list is `PARKS`, `REPO_STOPS` and `RUN_STOPS` in `runner/run.py` (29 reasons). Each row is what happens instead.

### Feature level (today: the feature parks, silently)
Each becomes a question through the decision queue (spec 0011 AC-11): the feature waits on it, every other feature goes on, the answer resumes it. Options are listed recommended first.

| # | Reason today | Instead |
|---|---|---|
| F1 | `denied` (a tool write or command refused) | Ask: "allow <path or command> for <repo>?" Options: allow once, always (writes the standing permission, spec 0020 brief), skip. On allow the step reruns with that path writable. Never for secrets (credentials, ssh, gh, `~/.claude/private/`). |
| F2 | `blocked` (login, sudo, captcha, 2FA, hardware, missing locked design) | Ask with what is needed. Options: done, go on; skip. |
| F3 | `verify_failed` after its debug attempts | Ask with the failing lines. Options: try again (free text hint), skip. |
| F4 | `no_progress` | Same as F3. |
| F5 | `debug_touched` (debug edited tests or specs) | Ask: keep the edits and go on, or undo them and try again, or skip. |
| F6 | `unchecked` (a pass without its check line) | Rerun the step once by itself with the missing line asked for; ask only if it is still missing. |
| F7 | `design_gate` | Ask with the gate's Must fix items. Options: try again (hint), accept as is, skip. |
| F8 | `budget`, `max_calls`, `call_timeout` (caps) | Ask: give it more (doubles that cap for this feature), skip. |
| F9 | `call_error` (the call crashed) | Retry once by itself; ask only if it fails again (retry, skip). |
| F10 | `manual_box`, `waiting` (a box only you can do) | Later boxes that do not need it go on (spec 0014 AC-8); live steps (`· live`) are done by `wf` (spec 0019/0020); a human step (a browser check) is asked: "done" ticks it. |
| F11 | `no_command`, `no_feature` (the scope box has no command, or the feature is gone) | Ask with the box text: skip the box, or skip the feature. |
| F12 | `app_failed` (the app did not start) | Ask with the app log tail: retry, skip. |

### Repo level (today: that repo stops)
| # | Reason today | Instead |
|---|---|---|
| R1 | on `main`/`master` (`branch`) | Make `feat/<slug>` from the feature heading and go on. No question. |
| R2 | `branch_changed` (someone switched the branch mid run) | Ask: go on on the new branch, or switch back, or stop this repo. |
| R3 | `scope_unreadable` | Ask with the parse error: retry after you fix it, or stop this repo. |
| R4 | `autopilot_off` | Stays a stop: you turned it off. |

### Run level (today: the whole run stops)
| # | Reason today | Instead |
|---|---|---|
| U1 | `interrupted` (Ctrl C) | Stays a stop: you asked for it. |
| U2 | `run_limit` (the 8 hour cap) | Ask: keep going for another 8 hours, or stop. Default when unanswered: stop starting new features, finish the ones running. |
| U3 | `usage_limit` | Sleep to the reset and go on (spec 0008 already pauses); never end the run for it. |
| U4 | `api_outage` | Keep waiting with growing gaps up to the wait cap (12 h), then ask. |
| U5 | `guard_changed` | Changes made by the run's own allowed steps and by `wf` (spec 0020 ledger) are accepted. Any other change stops only the repo it touches, with a question: accept the new setup and go on, or stop this repo. |
| U6 | `crash_loop` | Stops only that repo, with a question: retry, stop this repo. |
| U7 | `app_port_busy` | Stops only that repo, with a question naming what holds the port: retry, stop this repo. |
| U8 | `spawn_failed` (claude did not start) | Retry 3 times, a minute apart; then ask: retry, stop. |
| U9 | `ping_failed` (the phone service is down) | Keep building; questions stay in the queue and in the morning report; retry the ping every 10 minutes. |
| U10 | `internal_error` (a runner bug) | Stops only that repo, with the traceback in the report. |

## Acceptance criteria
- **AC-1**: every reason in `PARKS`, `REPO_STOPS`, `RUN_STOPS` maps to exactly one row above; a test fails when a reason is added to the code without a row.
- **AC-2**: a feature-level reason opens a decision (spec 0011) with the options above, recommended first, and the rest of the queue goes on.
- **AC-3**: each answer resumes the feature with the action named in its row (rerun with a path allowed, a doubled cap, a hint passed to the call, a ticked human box, or skip, which marks the feature `· skipped` for this run only).
- **AC-4**: R1 makes the branch with no question.
- **AC-5**: only U1 and R4 end a run or repo without a question; no repo-level reason ends the whole run.
- **AC-6**: the morning report lists every open question with its recommended answer.
- **AC-7** (standing permission, F1): a repo's standing write permission lives only in `~/.config/wf/allow.json` (`{"<repo realpath>": ["<abs path>", ...]}`, mode 0600), a folder no call can read or write. Only the runner writes it, when you answer F1 "always" (phone or keyboard), or `wf allow-writes <repo> <path>` run at your terminal (refused when `WF_RUN` is set). An `AGENTS.md` `- allow writes:` line is no longer read: a call can edit that file, so the run prints one warning that it is ignored and where the setting lives now. A fixed never writable set wins over any entry, as written and resolved: every secret path, the live claude dirs' `settings*.json`, `hooks/`, `rules/`, `agents/`, `skills/`, `scripts/`, `commands/`, `private/` and `CLAUDE.md`, `~/.claude.json`, your shell rc files, `~/.local/bin` and every `PATH` dir, `~/.local/share/wf`, `~/.local/share/claude`, wf's state folder, `~/.config/wf`, the repo's git common dir `config`, `hooks` and `info`, `~/.gitconfig` and `~/.config/git`. An entry under one is refused with a warning, one holding one leaves it denied, and F1 never offers "allow" for one (only "try again / skip"). Calls get the remaining paths writable (Edit allow and sandbox `allowWrite`, removed from the deny list), and the guard accepts changes to them made during a call of that run, the same way it accepts a `wf` swap (spec 0020 AC-5): the run hashes the allowed paths after each of its own calls and takes that as the new baseline, never for a never writable path. A change between calls, or by anything else, still stops that repo. On F1 and U5, an answer that matches no option is "skip" or "stop this repo", never the recommended option.
- **AC-8** (report names repos, feature 34): the report and the phone note name a repo by its folder name, unless that name matches the private names list (`scripts/private-names.py`), which keeps today's `repo-<hash>`.
- **AC-9** (push guard coverage, spec 0007 follow-up): the guard also hashes the files `~/.gitconfig` and `~/.config/git/config` include (`include.path`, `includeIf`), a `core.hooksPath` outside the git hooks folder, and `<git common dir>/info/attributes`.
- **AC-10** (run folders, spec 0014 follow-up): at the end of each run, run folders beyond the newest 50 are deleted, never one a run still holds.

## Build plan
1. The case table in code (one dict from reason to action), AC-1 test.
2. Feature-level questions and their resume actions (F1 to F12).
3. Repo and run level downgrades (R1 to R3, U2 to U10).
4. Report lines (AC-6).
