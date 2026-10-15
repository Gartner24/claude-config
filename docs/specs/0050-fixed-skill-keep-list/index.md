# 0050 · A fixed list of described skills

**Date**: 2026-10-15
**Status**: In Progress
**Paths:** `scripts/skill-keep.py`, `scripts/skill-keep.txt`, `runner/tests/test_skill_keep.py`, `live/settings.json`

## What you're agreeing to
- A short list in claude-config names the skills that keep their description in every session: 37 names, the 36 of your own skills used in the last 30 days plus `save-and-exit`.
- A script sets every other installed skill and command to name only. It still runs when you type it or a rule names it. Nothing is deleted.
- Your six long descriptions (browse, resume-from-clear, review, review-stack, save-and-clear, save-and-exit) stay exactly as they are, at full length.
- Plugin skills stay on. The script reports every installed plugin, turned off ones and sentry-skills included, with how many skills and commands each adds.
- You run the script yourself (it writes `~/.claude/settings.json`), then `./sync.sh` right away, before any `install.sh`, or the install undoes it.

## Summary

Plan row 55, from the research review of spec 0048 (section 5). Claude Code already drops the least used descriptions when over its budget (about 29 of yours are described in a session today), so this feature replaces that automatic choice with a fixed one you control. Your answers of 2026-10-15: keep the used ones; keep the six long descriptions unchanged, no file edits ("this are really important"); keep all plugins and only report them; a keep list plus a script, so the list stays trimmed when new skills arrive. Source: [brief](../../briefs/organize-and-sync.md), [research](../../research/organize-and-sync-review-2026-10-15.md).

## Requirements

**Acceptance criteria**:
- **AC-1** (keep list): `scripts/skill-keep.txt` holds one skill name per line; blank lines and lines starting with `#` are ignored. Its first content is exactly the 37 names in *Keep list* below. A name matches an installed skill folder name or a command file name without `.md`.
- **AC-2** (installed names): the script reads installed names from `$CLAUDE_LIVE_DIR` (default `~/.claude`): every `skills/<name>/SKILL.md` (links followed) and every `commands/<name>.md`. Plugin skills are never written to `skillOverrides`.
- **AC-3** (overrides written): for each installed name, a name in the keep list loses its `skillOverrides` entry when that entry is `name-only`; a name not in the keep list gets `name-only`. An existing `off` or `user-invocable-only` value is never changed. Entries for names not installed are left as they are. No other key in `settings.json` changes. Existing keys keep their order; new `skillOverrides` keys are appended at the end, never sorted. Private named skills are handled the same way; after `./sync.sh` their entries live only in the private fragment (spec 0013).
- **AC-4** (safe write): before writing, the script copies the old file to `$CLAUDE_LIVE_DIR/backups/settings/settings.json.bak.<YYYYmmdd-HHMMSS>` (the same folder `install.sh` uses), writes a temp file with `json.dumps(indent=2, ensure_ascii=False)` plus a trailing newline, parses it with `json.load`, gives it the original file's mode, then replaces the original. A settings file that does not parse stops the script with exit 1 and changes nothing.
- **AC-5** (dry run): `--dry-run` prints each change as `name-only: <name>` or `described: <name>`, and `kept as <value>: <name>` for a kept name held at `off` or `user-invocable-only`, and writes nothing.
- **AC-6** (report, every installed plugin): every run prints `described: <n> own skills` (installed own names with no `skillOverrides` entry after the run), then one line per installed plugin, then the total of described own skills plus skills of enabled plugins. Installed plugins are (a) every key of `plugins/installed_plugins.json` `plugins`, folder `plugins[key][0].installPath`, enabled only when `enabledPlugins.get(key) is True`; and (b) every `skills/<dir>/.claude-plugin/plugin.json` (the way sentry-skills is loaded), named by its `name` field, always enabled. Each line reads `plugin <name>: <k> skills, <c> commands (not controlled)`, or `plugin <name>: off` for a disabled one, where `<k>` counts `skills/*/SKILL.md` and `<c>` counts `commands/*.md` under the plugin folder. A plugin whose folder is missing prints `plugin <name>: folder missing` and is never skipped silently. A kept name that is not installed prints `warning: kept skill not installed: <name>` and the run still exits 0.
- **AC-7** (sync, order): after a real run the script's last line is `next: run ./sync.sh now, before any install.sh`. `./sync.sh` brings the change into `live/settings.json`, private names stripped as today (spec 0013). The script itself never writes the repo copy. `install.sh` rebuilds the live file from the repo copy, so an install before the sync undoes the run (the AC-4 backup still holds it).
- **AC-8** (tests): `runner/tests/test_skill_keep.py` loads the script with `importlib.util.spec_from_file_location` from a path built from the repo root (as `test_wf.py` does), and runs it against a temp `CLAUDE_LIVE_DIR` only, never the real `~/.claude`. It covers AC-1 to AC-7 (both plugin sources, an off plugin, a missing folder), each test mutation checked.
- **AC-9** (no private names in the list): `scripts/skill-keep.txt` holds no private name; the repo's `private-names.py check` passes on it.

### Keep list
The skills you or Claude used from 2026-09-15 to 2026-10-15 (counted from the chat logs), own skills and commands only, plus `save-and-exit` by your answer:
`design-gate`, `impeccable`, `rollover`, `save-and-clear`, `save-and-exit`, `resume-from-clear`, `sync`, `architect`, `design`, `check`, `test`, `develop`, `scope`, `debug`, `audit`, `document`, `auto`, `review`, `review-stack`, `browse`, `deep-research`, `cro`, `marketing-psychology`, `high-end-visual-design`, `minimalist-ui`, `ui-ux-pro-max`, `design-dna`, `design-motion-principles`, `assets`, `brand-system`, `animate`, `animation-vocabulary`, `review-animations`, `gsap-scrolltrigger`, `write`, `polish`, `new-site`.

`transitions-dev` (used once) stays name only, as it is today: its description is 1,730 characters, over the 1,536 Claude Code shows.

## Decision

A plain list file and one stdlib Python script, run by hand. Settings stay the one source Claude Code reads; the list only decides what the script writes there.

**Implementation skills**: none.

## Value sourcing

| Value | Source |
|---|---|
| Kept names | `scripts/skill-keep.txt` (AC-1) |
| Installed names | `skills/*/SKILL.md`, `commands/*.md` under `$CLAUDE_LIVE_DIR` (AC-2) |
| Installed plugins, on or off, and their counts | `plugins/installed_plugins.json` `plugins[key][0].installPath` with `enabledPlugins`, plus `skills/*/.claude-plugin/plugin.json` `name`; `skills/*/SKILL.md` and `commands/*.md` under each folder (AC-6) |
| Backup name | today's local time, `%Y%m%d-%H%M%S` (AC-4) |

## Build plan

1. `scripts/skill-keep.txt` and `scripts/skill-keep.py` with `--dry-run`, the write, the backup and the report (AC-1 to AC-6).
2. `runner/tests/test_skill_keep.py` against a temp live dir (AC-8).
3. You run `python3 scripts/skill-keep.py --dry-run`, then without it, then `./sync.sh` (AC-7). This writes `~/.claude`, so it waits on you.

## Consequences

- A skill installed later starts name only until you add it to the list and rerun.
- A skill that falls out of use keeps its description until you edit the list.
- Spec 0048 moves `scripts/` to `bin/`, `install.sh` to `bin/install.sh` and `live/` to `claude-home/`; these files and the test's one path line move with it, and `/claude-config` can run the script later. Whichever of 0048 and 0050 merges second rebases onto the other; no hard conflict.

## Follow-up

- Plan row 46 (missed skill report, due 2026-10-18) shows whether a name only skill should have picked itself; add any such skill to the list.

## Rationale

See [rationale.md](rationale.md).
