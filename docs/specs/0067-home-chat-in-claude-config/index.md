# 0067. Home chat runs from claude-config

**Date**: 2026-10-20
**Status**: Proposed
**Paths:** `bin/move-home-chat.sh`, `runner/tests/test_move_home_chat.py`, `.gitignore`, `AGENTS.md`, `README.md`
**Amends**: [0035](../0035-readable-layout/index.md) AC-5 (where the runner rules live).

## What you're agreeing to

- You open the chat that runs your setup and the runner in `~/claude-config` from now on.
- All of this year's chats and memory notes from `~/.claude` move into the chat folder claude-config already uses, after a full backup. Nothing is overwritten: any real clash stops the script before anything moves.
- The other two chat folder names become pointers to that one folder, so a chat started in `~/.claude` by habit sees the same history and memory.
- The three runner rules and your 59 command approvals move to private files in `~/claude-config` that git never commits.
- You run one script yourself, once, in a plain terminal with every Claude chat and `wf` closed.

## Summary

Claude Code stores chats and memory per start folder, named after the folder's real path (probe P6: starting in the `~/claude-config` shortcut files the chat under `~/dotfiles/claude-config`). So the live claude-config folder is the dotfiles one; an older byte for byte copy sits under the shortcut name. A script merges the `~/.claude` folder and the older copy into the live folder, links both old names to it, and moves the runner rules and approvals. Probes on 2026-10-20 showed Claude Code follows a linked folder for memory, new chats and resume, and loads `CLAUDE.local.md`.

## Requirements

**User stories**:
- As the owner, I open Claude in `~/claude-config` and get the same memory, rules and approvals as today's `~/.claude` chat, and `/resume` finds this year's chats.

Folder names (all under `$HOME/.claude/projects/`): `LIVE` = `-home-santiago-dotfiles-claude-config` (the target), `OLD` = `-home-santiago--claude`, `COPY` = `-home-santiago-claude-config`. Every path is built from `$HOME`, so the test can fake it.

**Acceptance criteria**:
- **AC-1** (checks first, nothing changed on failure): the script exits 1 with a message, before writing anything, when any of these hold:
  - `pgrep -x claude` or `pgrep -f 'python[0-9.]* .*(/\.local/bin/wf|/wf\.py)( |$)'` finds a pid other than the script's own and its parent (each pid named, a claude pid with its command line). wf runs as `~/.local/bin/wf` or an installed `wf.py`, never as `runner/wf.py` (found in review 2026-10-20);
  - another copy holds the lock `$HOME/.claude/move-home-chat.lock` (`flock -n`);
  - `pgrep`, `flock`, `jq`, `tar` or `cmp` is missing;
  - free space in `~/Documents` is below the size of `OLD`, `LIVE` and `COPY` together (`du -s`);
  - any entry under `OLD`, `COPY` or `LIVE` is not a regular file or a folder;
  - git in `$HOME/claude-config` does not ignore `CLAUDE.local.md` (same check as AC-7's);
  - `OLD` or `COPY` exists but is neither a real folder nor a symlink to `LIVE`;
  - an AC-7 approvals file does not parse, or the source has `permissions` keys other than `allow` (they would be lost);
  - a same day backup kept under AC-2 does not read back with `tar tzf`;
  - the clash pass (AC-3, AC-4, AC-6) finds a clash.
- **AC-2** (backup): it writes `$HOME/Documents/claude-chats-backup-<date +%F>.tar.gz` (mode 600) with `tar -C / czf` of the paths that exist among `OLD`, `LIVE`, `COPY`, `$HOME/.claude/.claude/`, `$HOME/claude-config/.claude/settings.local.json`, `$HOME/claude-config/CLAUDE.local.md`. Missing ones are left out, not an error. Then `tar tzf` with output discarded must exit 0, and the entry count is printed. On any failure the partial archive is deleted and the script exits 1 with nothing moved.
- **AC-3** (merge chats): for `OLD` then `COPY`, every entry except `memory/` merges into `LIVE`, file by file (a folder already in `LIVE`, such as `rollover/` or a per chat folder, merges one file at a time; a folder only in the source moves whole with `mv`). A file already in `LIVE` with identical content (`cmp`) is deleted from the source, since the backup holds it. Clash = same relative path, different content, in `LIVE` or between `OLD` and `COPY`; the clash pass finds every clash before anything moves, and names them all (on 2026-10-20: none, `COPY` is 424 identical chats, `OLD` shares only `memory/` and `rollover/` with `LIVE`).
- **AC-4** (merge memory): every note in `OLD/memory/` and `COPY/memory/` other than `MEMORY.md` merges into `LIVE/memory/` by the AC-3 rule; a note with the same name and different content is a clash (none on 2026-10-20). Lines of `OLD/memory/MEMORY.md` that are not blank and not already in `LIVE/memory/MEMORY.md` (exact match after trimming trailing spaces) are appended under `## From ~/.claude (moved <date>)`, written only when at least one line is appended. `COPY/memory/MEMORY.md` is dropped when it is identical to `LIVE`'s, else appended the same way. The script then prints, on stdout, pairs of notes in `LIVE/memory/` whose frontmatter `description:` lines (first `---` block) are identical, as possible duplicates; it deletes none and the exit code does not change.
- **AC-5** (links, last step): `OLD` and `COPY` are removed with `rmdir` (fails if anything is left: the script exits 1 and leaves the folder) and recreated as symlinks to the absolute path of `LIVE`. A folder already a symlink whose `readlink` is `LIVE` is skipped. When both are such links and the AC-6 and AC-7 sources are gone, the script prints `already moved` and exits 0 with no backup.
- **AC-6** (rules): `$HOME/.claude/.claude/CLAUDE.md` is written to `$HOME/claude-config/CLAUDE.local.md` (mode 600) with its first line replaced by `# Runner rules for the home chat (private, not committed; spec 0067)`. If the target already exists: identical to that result means skip, different means a clash (AC-1). The source is deleted only after the target is compared equal to the result. `CLAUDE.local.md` is added to the repo `.gitignore` by the build (the script does not edit the repo).
- **AC-7** (approvals): `permissions.allow` of `$HOME/.claude/.claude/settings.local.json` is merged (union, existing order first, no duplicates) into `$HOME/claude-config/.claude/settings.local.json`, keeping that file's other keys (a missing target or `permissions` key starts from `{}`). The result is written with `jq` to a temp file in the same folder, parsed again with `jq empty`, then moved over the target; the source is deleted only after that move. A parse failure exits 1 and leaves both files as they were. The MCP keys are not carried (no `.mcp.json` in either folder). The script refuses (AC-1) when `git -C $HOME/claude-config check-ignore -q .claude/settings.local.json` fails.
- **AC-8** (order, rerun): the steps run in this order: checks, backup, chats, memory, rules, approvals, links, report. Each step skips work already done, so a rerun after a failure finishes the job.
- **AC-9** (report): it prints top level entries moved, files skipped as identical, notes moved, index lines appended, approvals added (new count minus old), and the backup path.
- **AC-10** (docs): `AGENTS.md` and `README.md` say the home chat opens in `~/claude-config` and its private rules are in `CLAUDE.local.md`. Spec 0035 gets an `**Amended by**` line naming this spec. Checked by review.
- **AC-11** (test): `runner/tests/test_move_home_chat.py` runs the script with `HOME` set to a temp dir and a stub `pgrep` first on `PATH`. It covers AC-1 (busy pid, lock, a clash: nothing changed), AC-2 (archive exists, mode 600), AC-3 (identical file skipped, folder merged file by file, folder moved whole), AC-4 (index lines appended once), AC-5 (links, rerun prints `already moved`), AC-6 and AC-7 (merge, missing target).

## Decision

Merge into the live claude-config chat folder and link the old names to it (your picks 2026-10-20: move everything, merge memory, move old chats, link the old folder, fold in the copy folder, private rules file, full backup, you run it with Claude closed; cross check fixes applied on your pick). The target is the dotfiles named folder because Claude Code names the folder after the real path (probe P6). Rejected: share memory only by a link while chats stay split; start fresh.

## Feature design

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| busy check | running pids | `pgrep -x claude`, `pgrep -f 'python[0-9.]* .*(/\.local/bin/wf\|/wf\.py)( \|$)'`, minus `$$` and `$PPID` |
| backup name | date | `date +%F` at run time |
| merge | folder paths | `$HOME/.claude/projects/` plus the three names above |
| links | target | absolute `LIVE` path |
| rules | new first line | AC-6 text |
| approvals | allow list | the two `settings.local.json` files |

**Key invariants**: nothing is removed unless it is in the backup or proven identical in `LIVE`; a clash never overwrites; no step leaves a half merged state that a rerun cannot finish.

**Security model**: everything stays on this machine. `CLAUDE.local.md` and `settings.local.json` never enter git (the repo is public); the backup is mode 600.

## Build plan

1. `bin/move-home-chat.sh` (AC-1 to AC-9).
2. `runner/tests/test_move_home_chat.py` (AC-11); mutation check each test.
3. `.gitignore`, `AGENTS.md`, `README.md`, the spec 0035 amended line (AC-6, AC-10).
4. Run it yourself: close every Claude chat and `wf`, open a plain terminal, run `bash ~/claude-config/bin/move-home-chat.sh` · waits on you
5. Check it yourself: run `claude` in `~/claude-config`, ask "what do your memory notes say about the conductor session", and open `/resume` to see this year's chats listed (if not, `claude --resume <id>` still opens them) · waits on you
6. Update the memory notes that say the conductor runs from `~/.claude` (`conductor-session.md`, `session-per-family.md`) and personal plan item 9's note (AC-10).

## Migration plan

**Strategy**: one run of one script, after a full backup.
**Rollback**: `rm` the two links (not `rm -r`), then `tar xzf <backup> -C /`. Restore adds files back; it does not remove files the run added to `LIVE`.
**Risks**: the `/resume` picker may filter by the start folder recorded inside each chat (resume by id works across folders, probe P3; the picker is checked in step 5). Claude Code's own old chat cleanup runs through the link and only removes old entries, as it does today.

## Consequences

- One home folder for setup and runner work, and one memory.
- The memory index grows to about 90 lines; possible duplicates are listed, not merged.
- Chats started in `~/.claude` no longer get the runner rules or approvals (they moved), only the shared memory.
- The backup takes about 1.4 GB in `~/Documents` until you delete it.

## Rationale

Reasoning and options: see [rationale.md](rationale.md). Probes: [verify.md](verify.md).
