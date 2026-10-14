# 0020. One command: wf (verify)

## Probes (before accept)

### P1: what a running call sees when its config is swapped
Command: `python3 docs/specs/0020-one-command-wf/probes/p1-midcall-swap.py`. Run 2026-10-13, Claude Code 2.1.296. A temp `CLAUDE_CONFIG_DIR` (your login copied in, then removed; nothing of the live `~/.claude` touched). Its `settings.json` sets a PreToolUse Bash hook script that logs `v1`. The call runs six Bash tool calls, two of them `sleep 12`. About 15 s in, the hook script is renamed over with one logging `v2`, and `settings.json` is renamed over with one that adds a PostToolUse hook logging `post`.

Result, log in order: `v1`, `v1`, `swapped`, `post`, `v2`, `post`, `v2`, `post`, `v2`, `post`, `v2`, `post`. `RESULT hooks_per_tool_use=True settings_reread_mid_call=True`. The first `post` fired for a tool use whose PreToolUse had run under the old settings.

Rerun the same day with the call limited to `--allowedTools Bash(echo:*) Bash(sleep:*)` and the temp folder as its working folder (the first run used `bypassPermissions`, flagged by a security review): the same order and the same `RESULT` line.

Confirmed: a running call rereads `settings.json` mid call and runs hook scripts fresh on each tool use. So AC-4 renames `settings.json` last, and the spec accepts that an in flight call uses the new setup for its remaining tool uses. Rerun after a Claude Code upgrade.

### P2: why a `wf run` call cannot edit `runner/` (AC-12)
Command, run 2026-10-13 against the live `~/.claude/settings.json`: `python3 -B -c "import sys,json,os; sys.path.insert(0,'runner'); import run; s=json.load(open(os.path.expanduser('~/.claude/settings.json'))); t=run.hook_tokens([s],'<repo>'); print([x for x in t if 'wf' in x]); print([d for d in run.deny_paths('<repo>','<repo>/.git',t) if '<repo>' in d])"`.

Result: the tokens are `~/.local/bin/wf` and `<repo>/runner/wf.py`; the repo paths in the deny list are `.claude`, `.git` and `runner`. Confirmed: `runner/` is denied because the SessionStart hook `wf report --hook` names the link and `deny_paths` adds the folder of its real path. Not Claude Code resolving links in the `~/.local/bin` rule, as first guessed. Rerun after AC-12 lands: `runner` must be gone from that list.

## Live runs (wf finish)

- 2026-10-14, Claude Code 2.1.299: `python3 runner/e2e/run.py --beside` FAIL (exit 1): kept: /tmp/wf-e2e-8qdq5e8n/config
- 2026-10-14, Claude Code 2.1.299: `python3 runner/e2e/run.py --beside` PASS (second try; the first failed because the temp config dir had no skills, fixed in the fixture)

## Check verify (2026-10-14)

Run against the real `runner/wf.py` on temp repos, a temp state and config folder, and a temp live dir (`CLAUDE_CONFIG_DIR`), with a fake `claude` on `PATH` (a version line, or a sleep then no JSON). Nothing of the live `~/.claude` was touched. Unit suite: 702 tests, 1 failure (`test_questions.TestTimer.test_on_off`, spec 0039), which passes with `WF_RUN` unset: it fails only because this check ran inside a `wf run` call.

- [x] `WF_RUN=1 wf -y` -> exit 5 `refused: unattended`; `wf` with stdin not a terminal -> exit 5 `refused: no_tty` -> AC-1. can fail: the refusals are dropped and wf starts a swap from inside a call.
- [x] `wf` on a pty, answer `y` -> exit 130, live `rules/a.md` still `old`, no `report.seen` -> AC-2. can fail: any non empty answer goes on.
- [x] Screen order `report:`, `setup:`, `checks:`, `retake:`, `parked:`, `build:` (numbered `1. b: 1. Alpha`), `usage:`, `running: h: 777 ... wf run h`, `yours:` -> AC-2, AC-9, AC-13. can fail: a held repo is refused instead of listed with its holder.
- [x] `wf -y`: copy and staged install swapped (`a.md` new, ledger names both files, mode 0600, no `*.wf-swap-*` left), probes ran after, verify.md line recorded, boxes ticked, one commit, `report.seen` written -> AC-3, AC-4, AC-8. can fail: a failed or skipped swap still ticks the boxes.
- [x] Park whose head moved by a code commit -> `retake: r: 2. Two: verify_failed (a new commit)` and dropped from queue.json; park whose only new commit touched `docs/scope` -> `parked: ... retaken on a new commit`, kept -> AC-6. can fail: a scope only commit retakes.
- [x] Second `wf -y` -> `nothing to do`, exit 0 -> AC-2.
- [x] Pty answer `9` (not on the list) -> exit 130; `wf --only 2 -y` -> child `[b]` queued only `2. Beta`, run.json features only `2. Beta` -> AC-13, AC-7. can fail: the pick is ignored and every feature builds.
- [x] Lock files hold `73 ... wf setup swap` and `95 ... wf run b` -> AC-9. can fail: a taker leaves the file empty and a loser prints `unknown`.
- [x] Beside: `wf run A -y` mid call (fake claude sleeping), then `wf -y` swaps B's hook copy -> `wf` exit 0 with `running: A`, A logs `setup <stamp> taken`, run.json `setups` has one entry, a second call followed; a hand edit of the same hook during a fresh run of A -> `guard_changed` -> AC-5, AC-7, AC-11 (fake claude; the real claude run is the Live runs PASS above). can fail: a ledger accepted swap stops the run, or a hand change is taken.
- [x] `swap.json` `done: false` with a ledger line -> `finished an interrupted swap`, `a.md` new; without one -> `dropped an interrupted swap`, `a.md` old; stray aside deleted both times -> AC-4. can fail: an unledgered aside is renamed into place.
- [x] Held `.git/index.lock` -> about 6 s of retries, then `edits left uncommitted in B: ...`, exit 1 -> AC-8. can fail: no retry, or a silent loss of the commit.
- [x] SIGINT to `wf -y` with a child mid call -> `[A] stopped: interrupted`, exit 130 -> AC-8. can fail: the child keeps building after Ctrl C.
- [x] Grep of the AC-10 patterns over `runner/` and both rule files, repo and live copies: no string constant or rule line matches (one hit is a code comment in `runner/report.py:3`, outside the corpus) -> AC-10. can fail: a print tells you to type `wf finish`.
- [x] `readlink -f ~/.local/bin/wf` -> `~/.local/share/wf/21b4cb9c12bd/wf.py`, equal to `runner_fp` of the repo; copy holds no `tests` or `e2e`; P2 rerun: repo deny paths are `.claude` and `.git` only, `~/.local/share/wf` denied; `install.sh --dry-run` prints the `would: copy runner/*.py` line -> AC-12. can fail: the link points into the repo and `runner/` is denied again.
