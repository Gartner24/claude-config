# 0035 migrate: the live steps, one at a time

These steps write `~/.claude`, `~/dotfiles` and `~/.config/wf`, which no `wf` call may touch, so
you run each one yourself, in a normal terminal. Run one step, run its check, and go on only when
the check passes. Every step names the command that undoes it.

`<date>` below is the day you start, for example `20261015`. Type it the same in every step.

## Preconditions (all must hold before step 0)

- No `wf` lock held and no run going: `wf queue` shows nothing running.
- No autonomous unit running: `systemctl --user is-active wf-auto` prints `inactive`.
- This branch (spec 0035) and the release branch are merged into `main`, and `~/claude-config`
  is on `main`: `git -C ~/claude-config status -sb` starts with `## main`.
- Only the main checkout: `git -C ~/claude-config worktree list` prints one line. Moving the clone
  in step 9 would break the paths of any other worktree.

## The standard check

Steps below say "standard check". It is these four, all must pass:

```
~/claude-config/install.sh --dry-run >/dev/null; echo $?          # prints 0
python3 -c 'import json; json.load(open("/home/santiago/.claude/settings.json")); json.load(open("/home/santiago/.claude/settings.local.json"))'; echo $?   # prints 0
claude -p "say ok"; echo $?                                       # prints an answer, then 0
wf queue >/dev/null; echo $?                                      # prints 0
```

## Inventory of the live dir (AC-7)

Every top level entry of `~/.claude` on 2026-10-14, with where it ends up. Stays means it is
left where it is. Attic means `~/.claude/backups/attic-<date>/`.

| Entry | Owner | Destination |
|-------|-------|-------------|
| `CLAUDE.md`, `settings.json`, `settings.local.json`, `agents/`, `rules/`, `hooks/`, `scripts/`, `commands/`, `skills/` | this repo (`live/`) | stays |
| `private/` | you | stays, never in a repo |
| `.claude/` (holds `settings.local.json`) | project settings for sessions in `~/.claude` | stays; step 8 adds `CLAUDE.md` |
| `.claude.json`, `.credentials.json`, `projects/`, `sessions/`, `history.jsonl`, `file-history/`, `shell-snapshots/`, `session-env/`, `tasks/`, `todos/` if present, `debug/`, `logs/`, `cache/`, `paste-cache/`, `telemetry/`, `stats-cache.json`, `plugins/`, `ide/`, `jobs/`, `daemon/`, `daemon.lock`, `daemon.log`, `daemon.status.json`, `daemon-auth-cooldown`, `daemon-auth-status.json`, `bridge-spawn/`, `seed-admin/`, `downloads/`, `uploads/`, `feedback/`, `chrome/`, `security/`, `state/`, `conductor/`, `dev-mods/`, `mcp-needs-auth-cache.json`, `.last-cleanup`, `.last-update-result.json`, `.cc-writes/` | Claude Code | stays, framework owned |
| `backups/` | Claude Code and `install.sh` | stays; gets `settings/` and the attic |
| `get-shit-done/`, `gsd-file-manifest.json`, `package.json` | get-shit-done-cc | stays, framework owned |
| `vendor-jsm-skills/` | the JSM skills installer | stays, framework owned |
| `.ponytail-active` | ponytail plugin | stays, framework owned |
| `.skills-manifest.json` | `scripts/skills-audit.sh` | stays |
| `.hub-review-stamp` | the `workflow-start.sh` hook | stays |
| `gh-pr-status-cache.json` | status line | stays |
| `.design-active`, `.design-last` | design pipeline ledger (`live/skills/design/scripts/ledger.sh`) | stays |
| `.design-last-<id>` (9 files), `.design-last-o1` | design pipeline, one per old run | attic, step 4, unless a design run is going |
| `settings.json.bak.*` (11 files), `settings.json.bak-latest` | old `install.sh` backups | attic, step 2 |
| `.claude.json.tmp.<pid>.<id>` | a Claude Code write that never finished | attic, step 3 |
| `skills/.trash/` | removed skills | attic, step 5 |

An entry that appears later and is not in this table stays where it is.

## Steps

### 0. Backups

```
mkdir -p ~/claude-migration-<date>
chmod 700 ~/claude-migration-<date>
tar -C ~ -cpf ~/claude-migration-<date>/dot-claude.tar .claude
chmod 600 ~/claude-migration-<date>/dot-claude.tar
git -C ~/claude-config bundle create ~/claude-migration-<date>/claude-config.bundle --all
cp -a ~/.claude/private ~/claude-migration-<date>/private
```

Check: `tar -tf ~/claude-migration-<date>/dot-claude.tar | grep -c '^.claude/projects/'` prints a
number above 0, and `git bundle verify ~/claude-migration-<date>/claude-config.bundle` says
`is okay`. The backup sits outside `~/.claude` on purpose.

Undo: nothing to undo; the folder is only read later.

### 1. Install from the new layout

The merge moved `skills/` and `commands/` under `live/`, so every skill link in `~/.claude/skills`
points at a folder that is gone until this runs.

```
find ~/claude-config/skills ~/claude-config/commands -mindepth 1 -maxdepth 1 2>/dev/null
```

If that prints a folder (an untracked client skill left behind), move it first:
`mv ~/claude-config/skills/<name> ~/claude-config/live/skills/`. Then edit
`~/.claude/private/gitignore` so each `skills/<name>/` line reads `live/skills/<name>/`.

```
cd ~/claude-config && ./install.sh
```

Check: the standard check, plus `find ~/.claude/skills ~/.claude/commands -maxdepth 1 -xtype l`
prints nothing (no broken links).

Undo: `git -C ~/claude-config checkout <main before the merge>`, then `./install.sh`.

### 2. Old settings backups to the attic

```
mkdir -p ~/.claude/backups/attic-<date>
mv ~/.claude/settings.json.bak.* ~/.claude/settings.json.bak-latest ~/.claude/backups/attic-<date>/
```

Check: the standard check.

Undo: `mv ~/.claude/backups/attic-<date>/settings.json.bak* ~/.claude/`

### 3. The stale `.claude.json` temp file to the attic

Only while no Claude session is open (it may be a write in progress otherwise).

```
mv ~/.claude/.claude.json.tmp.* ~/.claude/backups/attic-<date>/
```

Check: the standard check.

Undo: `mv ~/.claude/backups/attic-<date>/.claude.json.tmp.* ~/.claude/`

### 4. Old design pointers to the attic

Only when no design run is going: `cat ~/.claude/.design-active` is empty or names no open run.

```
mv ~/.claude/.design-last-* ~/.claude/backups/attic-<date>/
```

Check: the standard check, plus `bash ~/.claude/skills/design/scripts/test-ledger.sh` passes.

Undo: `mv ~/.claude/backups/attic-<date>/.design-last-* ~/.claude/`

### 5. The skills trash to the attic

```
mv ~/.claude/skills/.trash ~/.claude/backups/attic-<date>/skills-trash
```

Check: the standard check.

Undo: `mv ~/.claude/backups/attic-<date>/skills-trash ~/.claude/skills/.trash`

### 6. The two live files this change edited

`live/CLAUDE.md` (the guide path) and `live/rules/scope-contract.md` (the `live/` copy shape)
changed in the repo. They are copied files, so copy them live:

```
cp ~/claude-config/live/CLAUDE.md ~/.claude/CLAUDE.md
cp ~/claude-config/live/rules/scope-contract.md ~/.claude/rules/scope-contract.md
```

Check: the standard check, plus `cd ~/claude-config && ./sync.sh && git status --short` shows no
change to either file.

Undo: `tar -C ~ -xpf ~/claude-migration-<date>/dot-claude.tar .claude/CLAUDE.md .claude/rules/scope-contract.md`

### 7. Probe P2 again

Already run on 2026-10-14 (see `verify.md`): `~/.claude/CLAUDE.md` loads once in a session started
in `~/.claude`. Rerun it after a Claude Code upgrade:
`cd ~/.claude && claude -p "/context"`, the Memory files table lists `~/.claude/CLAUDE.md` once.

### 8. Rules for conductor sessions

Create `~/.claude/.claude/CLAUDE.md` with the rules that only apply to sessions started in
`~/.claude`. Start it with this line, then add the rules:

```
# Rules for sessions started in ~/.claude (project memory; ~/.claude/CLAUDE.md is the user memory and loads once here, probe P2 2026-10-14)
```

Check: `cd ~/.claude && claude -p "/context"`, the Memory files table lists
`~/.claude/.claude/CLAUDE.md` as Project and `~/.claude/CLAUDE.md` once.

Undo: `rm ~/.claude/.claude/CLAUDE.md`

### 9. claude-config becomes a child repo of dotfiles

First run probe P3 (`verify.md`) and note which name the memory folder takes. Then:

```
mv ~/claude-config ~/dotfiles/claude-config
ln -s ~/dotfiles/claude-config ~/claude-config
git -C ~/dotfiles submodule add git@github.com:Gartner24/claude-config.git claude-config
git -C ~/dotfiles commit -m "chore: claude-config as a submodule"
```

The clone is moved, never recloned, so every branch, tag and stash stays. Probe P4 showed
`submodule add` adopts the existing clone without touching the network.

Check: `git -C ~/dotfiles/claude-config branch | wc -l` prints the same number as before the move,
`git -C ~/dotfiles status --short` is clean, `ls -l ~/claude-config` shows the link, and the
standard check passes.

Undo: `git -C ~/dotfiles reset --hard HEAD~1`, `rm ~/claude-config`,
`mv ~/dotfiles/claude-config ~/claude-config`, then `git -C ~/dotfiles config --remove-section submodule.claude-config`.

### 10. Trust the new real path

```
wf allow ~/dotfiles/claude-config
```

Check: `wf queue ~/dotfiles/claude-config` exits 0 and lists this repo's plan.

Undo: remove the new entry from `~/.config/wf/allowed.json`.

### 11. Session memory for the new path

Only if probe P3 showed the memory folder named after the real path:

```
cp -a ~/.claude/projects/-home-santiago-claude-config ~/.claude/projects/-home-santiago-dotfiles-claude-config
```

Copied, not moved, so sessions started through the old path keep theirs.

Check: start `claude` in `~/claude-config`, run `/memory`, the MEMORY.md list is the old one.

Undo: `rm -r ~/.claude/projects/-home-santiago-dotfiles-claude-config`

### 12. Links that leave the repo

`docs/scope/scope.md` links to `../../../projects/docs/briefs/...`. From `~/dotfiles/claude-config`
that climbs into `~/dotfiles`, not `~`. Check:
`ls ~/dotfiles/claude-config/docs/scope/../../../projects` fails after step 9; if it does, rewrite
those two links to `../../../../projects/...` in a normal commit.
