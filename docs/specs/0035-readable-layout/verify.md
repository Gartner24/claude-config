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
