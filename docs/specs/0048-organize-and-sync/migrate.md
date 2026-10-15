# 0048 migrate: the live steps, one at a time

These steps write `~/.claude`, which no `wf` call may touch, so you run each one yourself, in a
normal terminal. Run one step, then its check, and go on only when the check passes. Every step
names the command that undoes it.

`<date>` below is the day you start, for example `20261016`. Type it the same in every step.

## Preconditions (all must hold before step 0)

- No `wf` lock held and no run going: `wf queue` shows nothing running.
- No autonomous unit running: `systemctl --user list-units 'wf-auto-*' --no-legend` prints nothing.
- The spec 0048 branch is merged into `main`, and `~/claude-config` is on `main`:
  `git -C ~/claude-config status -sb` starts with `## main`.
- The repo still holds the `live -> claude-home` link: `readlink ~/claude-config/live` prints `claude-home`.
  It keeps every skill link in `~/.claude` working until step 2.

## The standard check

Steps below say "standard check". All five must pass:

```
~/claude-config/bin/install.sh --dry-run >/dev/null; echo $?      # prints 0
python3 -c 'import json, os; [json.load(open(os.path.expanduser(f"~/.claude/{f}"))) for f in ("settings.json", "settings.local.json")]'; echo $?   # prints 0
claude -p "say ok"; echo $?                                       # prints an answer, then 0
find ~/.claude/skills -maxdepth 1 -xtype l | wc -l                # prints 0 (no broken skill link)
wf queue >/dev/null; echo $?                                      # prints 0
```

## The skill names check (AC-15)

Before step 1, record which skills open:

```
find ~/.claude/skills -mindepth 1 -maxdepth 1 -exec test -r {}/SKILL.md \; -printf '%f\n' | sort > ~/claude-migration-<date>/skills-before.txt
```

After every step, compare by name, not only by count:

```
find ~/.claude/skills -mindepth 1 -maxdepth 1 -exec test -r {}/SKILL.md \; -printf '%f\n' | sort > ~/claude-migration-<date>/skills-now.txt
comm -23 ~/claude-migration-<date>/skills-before.txt ~/claude-migration-<date>/skills-now.txt   # prints nothing
```

## Step 0: backups (AC-14)

```
mkdir -p ~/claude-migration-<date>
tar -C ~ -cf ~/claude-migration-<date>/dot-claude.tar .claude && chmod 0600 ~/claude-migration-<date>/dot-claude.tar
git -C ~/claude-config bundle create ~/claude-migration-<date>/claude-config.bundle --all
```

Check: `tar -tf ~/claude-migration-<date>/dot-claude.tar | head -1` prints `.claude/`, and
`git bundle verify ~/claude-migration-<date>/claude-config.bundle` ends with `is okay`.
Then record `skills-before.txt` (above).
Undo: nothing to undo; delete the folder only after spec 0048's follow up date.

## Step 1: install the new layout

The first live step after the merge, so the runner copy is fresh before any other live box runs.
It relinks every skill and command from `live/` to `claude-home/`, copies the reminder hook and
its settings entry, and rebuilds any missing edited skill from its patch.

```
~/claude-config/bin/install.sh
```

Check: the standard check, the skill names check, and no link still goes through `live/`:
`find ~/.claude/skills ~/.claude/commands -maxdepth 1 -type l -lname '*/live/*' | wc -l` prints 0.
Undo: `cp "$(ls -t ~/.claude/backups/settings/settings.json.bak.* | head -1)" ~/.claude/settings.json`;
the old links still work through the `live` link.

## Step 2: remove the compatibility link (AC-15)

Only after step 1's check passed.

```
git -C ~/claude-config rm -q live
git -C ~/claude-config commit -m "chore: remove the live compatibility link (spec 0048 AC-15)"
```

Check: the standard check and the skill names check.
Undo: `git -C ~/claude-config revert --no-edit HEAD`.

## Step 3: build the manifest (needs the network)

The build session had no access to GitHub, so probe P2 and the history walk run here.

```
cd "$(mktemp -d)" && git init -q && git fetch -q --depth 1 https://github.com/greensock/gsap-skills.git "$(git ls-remote https://github.com/greensock/gsap-skills.git HEAD | cut -f1)" && git show FETCH_HEAD:skills/gsap-core/SKILL.md | sha256sum; sha256sum ~/.claude/skills/gsap-core/SKILL.md
python3 ~/claude-config/bin/claude-config.py build
python3 ~/claude-config/scripts/private-names.py check
```

Check: the two sha256 values match (P2; record them in verify.md), `build` ends with
`accounting: 0 skill(s) not accounted for`, and the names check exits 0. Review
`git -C ~/claude-config diff --stat config/`, then commit `config/`.
Undo: `git -C ~/claude-config checkout -- config/`. The private store copies under
`~/.claude/private/skills/` are additions only; leave them.

## Step 4: drift and the old audit

```
python3 ~/claude-config/bin/claude-config.py drift
```

Check: it prints `drift: none`, or every item left is one you expected (say which).
Then the old override guard is covered by the new tool: industrial-brutalist-ui, minimalist-ui
and high-end-visual-design show as `edited` in `config/manifest.json`, and drift does not list
them. Only then retire the old audit:

```
git -C ~/claude-config rm -q scripts/skills-audit.sh
git -C ~/claude-config commit -m "chore: retire skills-audit.sh, its checks live in claude-config.py (spec 0048 AC-7)"
mv ~/.claude/.skills-manifest.json ~/claude-migration-<date>/
```

Undo: `git -C ~/claude-config revert --no-edit HEAD` and move the file back.
