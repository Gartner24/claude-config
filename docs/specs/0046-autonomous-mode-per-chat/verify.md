# Verify: Autonomous mode per chat · spec 0046 · updated 2026-10-15
_Steps derived from spec 0046 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Run each command with a scratch `XDG_STATE_HOME`, `XDG_CONFIG_HOME` and `HOME` so the live state is never touched, and an allow list naming two scratch git repos `a` and `b` beside each other, plus `c` in another folder.

## Commands
- [x] Version 1 `auto.json` with `"on": true` -> `wf auto status` in its folder names every allowed repo; any change writes `"version": 2` -> AC-1
- [x] Version 1 file with `"on": false` -> `wf auto status` says `autonomous: off` -> AC-1
- [x] `wf auto on` in repo `a` -> `autonomous: on in a: a`; `wf auto on b` from a plain folder -> that chat holds `b` -> AC-2
- [x] `wf auto on x` (substring), `wf auto on -y`, `wf auto on 'b;id'` -> refused, nothing written -> AC-2
- [x] Repo held by a chat whose bar ran in the last 10 minutes: `wf auto on <it>` elsewhere leaves it out with `held by the chat in ...`; `wf auto take <it>` refuses -> AC-4
- [x] Same repo after that chat's `seen` is over 10 minutes old: `wf auto take` still refuses (only the user moves it); `wf auto on <it>` takes it and prints `taken from the chat in ..., idle since ...; its briefs: ...` -> AC-2, AC-4
- [x] First hook after on prints one `suggested repos:` line (same parent folder or GitHub owner, at most 6), never again -> AC-3
- [x] `wf auto take` with 7 names, a `-` name, an unlisted name, or a repo whose runner lock is held -> refused -> AC-3
- [x] `wf auto release b` -> `released: b`; with the chat's unit active, take and release add `applies at the next wf auto start` -> AC-4
- [x] `wf auto start` -> systemd-run unit `wf-auto-<8 hex>` with `WF_AUTO_FOLDER=<folder>` and `wf -y --repos <each repo>`; a chat with no repos -> `refused: no repos` -> AC-5
- [x] `wf -y --repos <a>` plans and lists questions only for `a` -> AC-5
- [x] A unit run with `WF_AUTO_FOLDER=A` ends `auto_off` after chat A's `/auto off`, while a unit with `WF_AUTO_FOLDER=B` goes on -> AC-5, AC-8
- [x] `wf auto wait` in chat A returns a question only of A's repos, run ended only for A's unit -> AC-6
- [x] `wf auto bar` in chat A: `AUTO idle, <q> question(s)` counting only A's repos; running counts only A's active.json rows; another folder: `auto: <n> chat(s) on` -> AC-7
- [x] `/auto off now` in A stops only A's unit (`systemctl --user stop wf-auto-<hash of A>`) -> AC-8
- [x] `python3 -m unittest discover -s runner/tests -p 'test_auto*.py'` green, every new test mutation checked -> AC-10

## UI / manual
- [ ] Two real Claude sessions in two folders each type `/auto on`; each bar shows only its own repos; `wf auto take` of the other's repo is refused -> AC-11

## Value sourcing
- [x] chat key: run the hook from a subfolder of a chat folder -> it resolves to that chat
- [x] a chat's repos: `/auto on` in a git worktree -> the chat holds the main checkout, not the worktree
- [x] suggested repos: a repo in another folder with the same GitHub owner is suggested; one with another owner is not
- [x] live: set `seen` 9 then 11 minutes back -> refusal text switches from "release it there first" to "only the user takes it"
- [x] unit name: two chats get two different `wf-auto-<hash>` names
- [x] question scope: a decision whose `repo` is another chat's repo never shows in this chat's hook, wait or bar

## Run 2026-10-15 (/check verify)
Real `wf` CLI (`runner/wf.py`) on scratch repos under `$TMPDIR/v46`, scratch HOME and XDG folders, fake `systemd-run` and `systemctl` on PATH logging their argv; bare `wf --repos` under a pseudo terminal, cancelled at the confirm prompt. Every Commands and Value sourcing step above passed. 15 deliberate breaks, each restored after: each changed the output of its step (live always false, substring names, version 1 with no repos, take from an idle chat, questions and running counts not scoped, suggestions with no owner filter, take ignoring the runner lock, off now stopping a shared unit, bar never marking seen, auto_off ending every chat's unit, a worktree as its own repo, briefs never listed, `--repos` ignored in the plan and in the questions screen). Left for `/test`: the mutation check of the unit tests (AC-10; `test_auto*.py` 33 tests green). Left for you: AC-11.

## Run 2026-10-15 (/test)
Added `TestWorktree` (a worktree chat holds its main checkout) and `TestDrive` (panel, take, brief before release). All 31 new or changed tests in `test_auto.py` and `test_auto_chats.py` mutation checked, 33 mutants, each red on its own test and green after restore (`test_auto*.py` 35 tests green). Whole suite `python3 runner/tests/fast.py`: 842 tests, 0 failed.

## Acceptance-criteria coverage
- AC-1 migration steps, chat key step · AC-2 on steps · AC-3 suggest and take steps · AC-4 live holder, release · AC-5 start, --repos, auto_off · AC-6 wait · AC-7 bar · AC-8 off now · AC-9 unchanged (phone) · AC-10 unit tests · AC-11 manual
