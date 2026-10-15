# 0035 verify

## Probes (build plan step 1), 2026-10-14, Claude Code in a `wf run` call

- **P1** double load in claude-config. `env -C ~/claude-config claude -p "/context"`.
  Memory files: `~/.claude/CLAUDE.md` (User, 4.5k), `~/claude-config/CLAUDE.md` (Project, 4.5k,
  the same text), `~/claude-config/.claude/CLAUDE.md` (Project, 81), `~/claude-config/AGENTS.md`
  (Project, 4.4k). Confirmed: the global instructions load twice. After the merge the root
  `CLAUDE.md` is only `@AGENTS.md` and `.claude/CLAUDE.md` is gone; rerun the same probe and expect
  `~/.claude/CLAUDE.md` once and `AGENTS.md` once.
- **P2** double load in `~/.claude`. `env -C ~/.claude claude -p "/context"`. Memory files:
  `~/.claude/CLAUDE.md` once (User), the rules, the private import, and that folder's MEMORY.md.
  Confirmed: no double load, so `~/.claude/.claude/CLAUDE.md` needs no warning about it.
- **P3** memory key through a symlink: not run. Inside this sandbox `claude -p "say ok"` answers
  `Not logged in` (`/context` needs no login, a model call does), and the call cannot write
  `~/.claude/projects` anyway. It only decides `migrate.md` step 11, so you run it before step 9:
  `mkdir -p /tmp/p3real && ln -s /tmp/p3real /tmp/p3link && cd /tmp/p3link && claude -p "say ok"`,
  then `ls ~/.claude/projects | grep p3`.
- **P4** submodule from an existing clone, on throwaway copies.
  `git clone ~/dotfiles $TMPDIR/p4dot`, `cp -a ~/claude-config $TMPDIR/p4dot/claude-config`
  (one sandbox mount file, `.git/config.lock`, could not be copied; it is not repo data), then
  `git -C $TMPDIR/p4dot submodule add git@github.com:Gartner24/claude-config.git claude-config`
  printed `Adding existing repo at 'claude-config' to the index` with no network use.
  `git -C $TMPDIR/p4dot status --short` showed `M .gitmodules` and `A claude-config`, and the
  copy's `git branch` listed the same 29 branches as the original. Confirmed. The temp folders
  could not be removed from the call (the guard hook refuses `rm -rf` on absolute paths); remove
  `$TMPDIR/p4dot`, `$TMPDIR/p3real` and `$TMPDIR/p3link` yourself.


## /check verify, 2026-10-15, second run after the fix commit and its revert (PASS after the spec 0021 link fix)

- [x] `HOME=<tmp> CLAUDE_LIVE_DIR=<tmp>/.claude ./install.sh`: every tracked file under `live/`
  is at the same path in the temp live dir except `settings.local.json` (install has never
  copied it, same on main); 21 skill and command links all point into `live/` -> AC-3.
  Passed. Can fail: install.sh still reading `agents/` or `skills/` at the repo top. (Install
  exits 1 only because the design ledger self check needs `~/projects/...` fixtures that a temp
  HOME lacks; with the real HOME it is 107/107.)
- [x] Second temp install: the backup is `backups/settings/settings.json.bak.<stamp>`, 0
  `bak` entries at the live dir top -> AC-7. Passed. Can fail: install.sh writing
  `settings.json.bak.*` beside settings.json.
- [x] `CLAUDE_LIVE_DIR=<tmp> ./sync.sh` in a clone of HEAD, with a marker line added to the temp
  `rules/lessons.md` -> exit 0, the marker is in `live/rules/lessons.md`, no top level `rules/`
  or `agents/`, root `CLAUDE.md` still `@AGENTS.md` -> AC-3, AC-4. Passed. Can fail: sync.sh
  copying into the old paths or over the root `CLAUDE.md`.
- [x] `env -C <clone of HEAD> claude -p "/context"` -> Memory files: `~/.claude/CLAUDE.md` once
  (User, 4.5k), the clone's `CLAUDE.md` (Project, 4 tokens), `AGENTS.md` once (4.7k) -> AC-4.
  Passed. Can fail: the root `CLAUDE.md` still a full copy of the global instructions, or
  `.claude/CLAUDE.md` still tracked.
- [x] `finish.shape` on the worktree: `cp live/rules/branch-pr.md ~/.claude/rules/branch-pr.md`
  -> copy, rel `rules/branch-pr.md`; `live/settings.json`, old `rules/branch-pr.md` and a
  `~/.claude/live/...` target -> None -> AC-3. Passed. Can fail: the `live/` prefix not stripped.
- [x] Every top level entry of `~/.claude` named in migrate.md or README -> AC-7. Passed with a
  note: 26 entries not named (`statsig`, `workflows`, `policy-limits.json`, ...) are 0 byte files
  this sandbox's mounts created at 02:49 today; migrate.md line 53 keeps any unlisted entry in
  place. Step 2 moves backups by glob (16 now, the table still says 11). Can fail: a real
  entry missing from the table.
- [x] README: six kinds in the map plus a repo tools row, session diagram, 954 words,
  `asciify.py --check` changes 0 files, the rules match `AGENTS.md` `## Rules` -> AC-1, AC-2,
  AC-5. Passed. Can fail: a kind missing or a rule contradicting AGENTS.md.
- [x] Link check over tracked markdown -> AC-3. Passed after your answer "fix it in this feature
  anyway": `docs/specs/0021-never-stop/index.md:6` linked `../0008-failure-and-park-policy/`, now
  `../0008-failure-park-policy/index.md`, which exists. Before the fix the check listed it. The
  two `scope.md` links to `../../../projects/...` resolve from `~/claude-config` (the target
  exists; migrate.md step 12); the `../specs/...` hits in spec 0034 sit inside code quotes, not
  real links; the 0045 and 0046 links are only in the uncommitted plan copy from main. Can fail:
  a moved guide with an old link left behind.
- [x] Every `AGENTS.md` command -> AC-9. Passed: `check-routing.py` (routing OK, 0 self route
  failures, fixed in c5d0baa), `install.sh --dry-run`, `gen-agent-index --check`,
  `asciify --check`, `block-destructive --test`, `plain-panel --test`, `test-ledger.sh` 107/107,
  `build-ramp --check`, `private-names --test`, `spec-paths --test`, `runner/tests/fast.py`
  (752, 0 failed), `unittest discover` (752, OK). Can fail: a script still naming the old
  top level paths.
