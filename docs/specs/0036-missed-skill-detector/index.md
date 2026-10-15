# 0036 · Missed-skill detector

**Date**: 2026-10-14
**Status**: Proposed
**Paths:** `live/settings.json`, `install.sh`, `scripts/private-names.py`, `AGENTS.md`

## What you're agreeing to
- Two small jjstack hooks get switched on: one notes when your message matched a skill's trigger words but no skill ran, the other notes which skill did run. A report command then shows which skills get missed most.
- They only watch and write a log in `~/.jjstack/`; they never block or change a message. They stay off inside unattended `wf` steps.
- The change goes into the repo's `settings.json` and reaches `~/.claude` through `./install.sh`, which refuses a settings file that does not parse, so a typo can never switch off all your settings.
- After a few days of normal use you read one report; that closes the feature.

## Terms used below
- **Hook**: a command Claude Code runs on an event, set in `settings.json` under `hooks`. **UserPromptSubmit** fires when you send a message; **PreToolUse** fires before a tool runs, filtered by a `matcher` (the tool name).
- **Skill tool**: the tool the model calls to load a skill. A skill that "fires" is one loaded through it.
- **Trigger index**: `~/.jjstack/skill-triggers.json`, the trigger phrases of every installed skill, built by `jjstack-extract-triggers` (jjstack `setup` step 10). The detector matches your message against it.
- **Parse check**: reading the file with a JSON parser before it replaces the live one; a file that fails is never installed.

## How the jjstack parts work (read from the files)
- `skill-miss-detect.sh` (UserPromptSubmit): when a message matches a trigger it writes a "pending" note; if the next message arrives and the note is still there, it logs a `trigger_miss`. It also logs `user_correction` for a message `/missed <skill>`, and `wrong_skill` for a correction ("no", "use /x", "wrong skill", or any `/word`) within 5 minutes of a skill firing. Log `~/.jjstack/skill-misses.jsonl`, rotated at 500 lines. Always exits 0 (`~/.claude/skills/jjstack/hooks/skill-miss-detect.sh:82-200`).
- `skill-fired-clear.sh` (PreToolUse on `Skill`): records the firing skill and clears a matching pending note (`~/.claude/skills/jjstack/hooks/skill-fired-clear.sh:30-46`). Without it every match becomes a miss.
- `jjstack-skill-miss-report`: counts by type and top missed skills for 24 h, 72 h and lifetime, and a HOT / WARM / COLD verdict (`~/.claude/skills/jjstack/bin/jjstack-skill-miss-report:84-168`).
- Today neither hook is in `settings.json` (UserPromptSubmit holds only `wf auto hook`, `settings.json:319-327`), and the trigger index dates from 2026-09-02, before the current skill set.

## Acceptance criteria
- **AC-1** (wiring): the repo `settings.json` gains one UserPromptSubmit entry, `[ -n "$WF_RUN" ] || exec ~/.claude/skills/jjstack/hooks/skill-miss-detect.sh`, and one PreToolUse entry with matcher `Skill`, `[ -n "$WF_RUN" ] || exec ~/.claude/skills/jjstack/hooks/skill-fired-clear.sh`. The jjstack files are not edited or copied (vendored trees stay untouched, `AGENTS.md` `## Rules`).
- **AC-2** (off under `wf`): with `WF_RUN` set, both commands exit 0 without starting the jjstack script, so unattended box commands (`/develop x`) never enter the log.
- **AC-3** (sync first): the build runs `./sync.sh` before editing the repo `settings.json`, and the commit's `settings.json` diff holds only the two entries of AC-1. A live edit not yet synced is never overwritten by the install.
- **AC-4** (parse check, dry run too): `./install.sh --dry-run` parses the repo `settings.json` and `settings.local.json` and exits non zero naming the file and the parser error when one fails. Today only a real install parses, after the `$HOME` rewrite (`install.sh:116-118`); that check stays.
- **AC-5** (test): the install self checks in `scripts/private-names.py --test` (which already install into a temp live tree, `scripts/private-names.py:679-711`) gain: a repo `settings.json` with a trailing comma makes `install.sh --dry-run` fail and makes a real install leave the temp live `settings.json` byte for byte unchanged.
- **AC-6** (index): the live step that installs also reruns `~/.claude/skills/jjstack/bin/jjstack-extract-triggers`, so the index covers today's skills.
- **AC-7** (live install): `./install.sh` is a ` · waits on you · live` box (it writes `~/.claude/settings.json`, which no call may write, spec 0021 AC-7). After it, `python3 -c 'import json,sys; json.load(open(sys.argv[1]))' ~/.claude/settings.json` exits 0 and both hook commands appear in it.
- **AC-8** (docs): `HOOKS.md` lists both hooks with their event, what they log and where, and the report command `~/.claude/skills/jjstack/bin/jjstack-skill-miss-report`; `AGENTS.md` `## Commands` gains the report line.
- **AC-9** (read one report): a ` · waits on you` box: after at least 3 days of normal sessions, run the report and write its verdict and top 5 skills into this spec's `verify.md`.

## Build plan
1. Probes P1 to P3, results in `verify.md`.
2. `./sync.sh`, the two settings entries, the dry run parse check and its self check, docs. AC-1 to AC-5, AC-8.
3. Live: `./install.sh` plus the trigger index rebuild, then the parse check on the live file. AC-6, AC-7.
4. Later: read one report. AC-9.

## Probes
Run by you (P1 and P2 call the real `claude`):
- **P1** `WF_RUN` reaches hooks: put a UserPromptSubmit hook `env > /tmp/p1-env.txt` in a temp settings file, run `WF_RUN=probe claude -p --settings /tmp/p1-settings.json "say ok"`, then `grep WF_RUN /tmp/p1-env.txt`. AC-2 rests on it.
- **P2** typed slash commands and the Skill tool: in a normal session type `/scope` and check `~/.jjstack/skill-last-fired.json` afterwards. If a typed command does not go through the Skill tool, the next message logs a false `trigger_miss` whenever the command's words match a trigger; record that the report must be read with it in mind.
- **P3** `/missed <skill>` reaches the hook: type `/missed scope` in a session, then `tail -1 ~/.jjstack/skill-misses.jsonl`. If Claude Code rejects the unknown command before hooks run, `HOOKS.md` says to write "missed /scope" in plain text instead, which the wrong-skill pattern catches.

## Follow-up
- The `wrong_skill` pattern counts any `/word` in a message within 5 minutes of a skill firing (`skill-miss-detect.sh:134-136`), so typing a second command soon after a skill reads as a correction. Vendor behavior, kept; weigh it when reading the report.
- A jjstack update can change both hooks; the settings entries point at its files by path, so an update takes effect with no change here.
