# Verify: Autonomous mode per chat · spec 0046 · updated 2026-10-15
_Steps derived from spec 0046 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Run each command with a scratch `XDG_STATE_HOME`, `XDG_CONFIG_HOME` and `HOME` so the live state is never touched, and an allow list naming two scratch git repos `a` and `b` beside each other, plus `c` in another folder.

## Commands
- [ ] Version 1 `auto.json` with `"on": true` -> `wf auto status` in its folder names every allowed repo; any change writes `"version": 2` -> AC-1
- [ ] Version 1 file with `"on": false` -> `wf auto status` says `autonomous: off` -> AC-1
- [ ] `wf auto on` in repo `a` -> `autonomous: on in a: a`; `wf auto on b` from a plain folder -> that chat holds `b` -> AC-2
- [ ] `wf auto on x` (substring), `wf auto on -y`, `wf auto on 'b;id'` -> refused, nothing written -> AC-2
- [ ] Repo held by a chat whose bar ran in the last 10 minutes: `wf auto on <it>` elsewhere leaves it out with `held by the chat in ...`; `wf auto take <it>` refuses -> AC-4
- [ ] Same repo after that chat's `seen` is over 10 minutes old: `wf auto take` still refuses (only the user moves it); `wf auto on <it>` takes it and prints `taken from the chat in ..., idle since ...; its briefs: ...` -> AC-2, AC-4
- [ ] First hook after on prints one `suggested repos:` line (same parent folder or GitHub owner, at most 6), never again -> AC-3
- [ ] `wf auto take` with 7 names, a `-` name, an unlisted name, or a repo whose runner lock is held -> refused -> AC-3
- [ ] `wf auto release b` -> `released: b`; with the chat's unit active, take and release add `applies at the next wf auto start` -> AC-4
- [ ] `wf auto start` -> systemd-run unit `wf-auto-<8 hex>` with `WF_AUTO_FOLDER=<folder>` and `wf -y --repos <each repo>`; a chat with no repos -> `refused: no repos` -> AC-5
- [ ] `wf -y --repos <a>` plans and lists questions only for `a` -> AC-5
- [ ] A unit run with `WF_AUTO_FOLDER=A` ends `auto_off` after chat A's `/auto off`, while a unit with `WF_AUTO_FOLDER=B` goes on -> AC-5, AC-8
- [ ] `wf auto wait` in chat A returns a question only of A's repos, run ended only for A's unit -> AC-6
- [ ] `wf auto bar` in chat A: `AUTO idle, <q> question(s)` counting only A's repos; running counts only A's active.json rows; another folder: `auto: <n> chat(s) on` -> AC-7
- [ ] `/auto off now` in A stops only A's unit (`systemctl --user stop wf-auto-<hash of A>`) -> AC-8
- [ ] `python3 -m unittest discover -s runner/tests -p 'test_auto*.py'` green, every new test mutation checked -> AC-10

## UI / manual
- [ ] Two real Claude sessions in two folders each type `/auto on`; each bar shows only its own repos; `wf auto take` of the other's repo is refused -> AC-11

## Value sourcing
- [ ] chat key: run the hook from a subfolder of a chat folder -> it resolves to that chat
- [ ] a chat's repos: `/auto on` in a git worktree -> the chat holds the main checkout, not the worktree
- [ ] suggested repos: a repo in another folder with the same GitHub owner is suggested; one with another owner is not
- [ ] live: set `seen` 9 then 11 minutes back -> refusal text switches from "release it there first" to "only the user takes it"
- [ ] unit name: two chats get two different `wf-auto-<hash>` names
- [ ] question scope: a decision whose `repo` is another chat's repo never shows in this chat's hook, wait or bar

## Acceptance-criteria coverage
- AC-1 migration steps, chat key step · AC-2 on steps · AC-3 suggest and take steps · AC-4 live holder, release · AC-5 start, --repos, auto_off · AC-6 wait · AC-7 bar · AC-8 off now · AC-9 unchanged (phone) · AC-10 unit tests · AC-11 manual
