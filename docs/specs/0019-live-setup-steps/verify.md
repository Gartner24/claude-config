# Verify: live setup steps in one command · spec 0019

Run 2026-10-13 by `/check verify`, on scratch repos under `$TMPDIR/v19/` with their own
`XDG_CONFIG_HOME`, `XDG_STATE_HOME`, `CLAUDE_LIVE_DIR` and a fake `claude` printing `9.9.9`.
The fixture scope has two features with copy, install and probe boxes, seven boxes that must be
refused, a `done` feature and a `## Deferred` one. The terminal cases ran under `script` (a real pty).

## Commands

- [x] `wf finish <repo> -y` with no trust list -> `refused: untrusted`, exit 5 -> AC-3
  can fail: the trust check is skipped and the steps run on a repo you never allowed.
- [x] `WF_RUN=1 wf finish -y` -> `refused: unattended`, exit 5 -> AC-3
  can fail: an unattended call could run live steps.
- [x] `wf finish < /dev/null` -> `refused: no_tty`, exit 5 -> AC-3
  can fail: a run with no terminal skips the Enter and runs everything.
- [x] `wf finish -y` while another `<state>/locks/*.lock` is held -> `refused: locked: a wf run is going: pid 4242`, exit 5 -> AC-3
  can fail: the lock probe is skipped and a live install runs during a `wf run`.
- [x] A missing repo first on the trust list -> `skipped: .../gone: no folder or no scope`, the next repo goes on -> AC-3
  can fail: a missing repo aborts the whole command, or crashes it.
- [x] Plan in a pty, typed `nope` -> each step printed as `<phase>: <repo>: <features>: <command>`, exit 130, no `finish/` folder, live `rules/a.md` still `old`, no install ran -> AC-3
  can fail: the plan runs before the answer, or a non empty answer runs it.
- [x] The plan lists as yours: `rm -rf x`, `cp -f`, `cp` to another live path, `cp settings.json`, a probe with `--x`, a box with a `` `!` `` (`not a live step: !`), a box with ` · live` only (`live needs waits on you`); the `done` and `## Deferred` boxes do not show; `~/../..<repo>/rules/b.md` is accepted as a copy -> AC-1, AC-2
  can fail: a span outside the four shapes runs, or a tag order or `~` path is refused.
- [x] Enter in a pty -> live `rules/a.md` is `new-a` (byte equal), its backup under `finish/<stamp>/claude/rules/a.md` is `old`; `./install.sh` named by two features ran once (`install-runs.txt` has one line); before it, `rules`, `agents`, `hooks`, `scripts`, `settings.json` are backed up with `hooks/link` still a link -> AC-4
  can fail: no backup, a second install, or a link copied as a file.
- [x] `bad.sh` exits 3 -> `FAIL (exit 3): boom: the probe broke` (the last non blank line, after a blank line), and `y.sh` after it still runs and passes; `step-03.log` holds its output -> AC-4, AC-5
  can fail: a failed check stops the rest, or the record takes the blank last line.
- [x] verify.md: `## Live runs (wf finish)` added under the existing `# Verify 0001`, created for `0002-y` (no verify.md before), and the probe named by both features recorded in both -> AC-5
  can fail: the line goes to the wrong file, or a shared check is recorded once.
- [x] Passed boxes ticked, the failed one and every yours box left open; one commit `chore(wf): wf finish ran 6 live step(s)` holding only `scope.md` and the two verify.md files; `report.seen` created; `next: fix the FAIL lines, then wf finish`, exit 1 -> AC-6, AC-7, AC-8
  can fail: a failed box is ticked, or the commit takes other files.
- [x] Rerun after fixing the probe -> only that check runs, its line appended under the heading, commit `ran 1 live step(s)` without the probe edit, `next: wf run`, exit 0 -> AC-5, AC-7, AC-8
  can fail: ticked boxes run again, or the line goes below the end of the file.
- [x] Live `rules` turned into a file -> both copies FAIL, install and every check print `(not run)`, nothing committed, exit 1 -> AC-4
  can fail: checks run after a failed copy.
- [x] On `main` -> `edits left uncommitted on main`, no new commit -> AC-7
  can fail: a commit lands on `main`.
- [x] A probe that edits the `Copy a live` line mid run -> `box changed, not ticked: Copy a live: ...`, the edited line left `[ ]` -> AC-6
  can fail: the tick writes over a line someone changed.
- [x] SIGINT to `wf finish` during a slow probe -> exit 130, the probe's INT trap wrote its marker (the signal reached its group), no `report.seen`, no verify.md line for the cut check -> AC-4, AC-8
  can fail: Ctrl C leaves the step running unsignalled, or records it as a result.
- [x] `wf next <repo>` on the fixture -> `waits on you: Copy a live: ... · live`, exit 3 -> AC-1
  can fail: `wf run` hands a live box to a call.
- [x] Real `install.sh` into a temp `HOME` and live dir: `autoMode` kept (`kept your autoMode`), no `autoMode` gives none, broken JSON prints `autoMode not kept: Expecting property name...` and installs on, `--dry-run` prints `would keep autoMode` -> AC-9
  can fail: the install drops your live `autoMode`.
  The temp `HOME` makes the later design ledger self check fail (it reads `~/.claude/skills`); with the real `HOME` it passes 107 of 107.
- [x] `wf finish` on this repo with the real live dir, cancelled -> 2 copies, 1 install for features 30 and 13, `runner/e2e/run.py` and `--parallel` as checks, nothing yours -> AC-2, AC-10
  can fail: the real boxes (with their `(AC-N)` suffix) are refused, or the shared copy runs twice.
- [x] `python3 scripts/private-names.py --test` -> `all self checks passed` -> AC-9
  can fail: the install.sh `autoMode` self checks fail.

Not counted: the AC-10 wording in `rules/scope-contract.md` and `rules/runner-handoff.md` was read, not run (a grep for text the change added).

## Acceptance-criteria coverage
- AC-1 met · AC-2 met · AC-3 met · AC-4 met · AC-5 met · AC-6 met · AC-7 met · AC-8 met · AC-9 met · AC-10 met (repo copies; the live copies are this feature's waiting boxes)
