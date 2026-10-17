# 0054. One skill scan command, run before every skill update

**Date**: 2026-10-17
**Status**: Proposed
**Paths:** `scripts/skill-scan.py`, `bin/claude-config.py`, `bin/install.sh`, `claude-home/skills/claude-config/SKILL.md`, `runner/tests/test_skill_scan.py`
**Amends**: [0048](0048-organize-and-sync/index.md) AC-10 (`update --apply` runs a scan first; it still never asks)

## What you're agreeing to
- One command, `skill-scan`, runs the skillspector security scanner over every installed skill and plugin (quick pass, and the slower model pass when you ask).
- It shows only new serious findings, compared with a list of known false alarms, each with the file and line.
- Every skill update through claude-config scans the new version first and prints its new serious findings, then installs anyway. It never blocks.
- Plugins update outside claude-config, so for them you scan after the fact; the docs say so.
- Reports stay on your laptop, never in the public repo.

## Summary
Plan A4 scanned all 221 skills and plugins by hand with throwaway scripts. This turns that into one command and wires it into skill updates. The scanner raises many false alarms, so it compares against a saved list of known ones and shows only what is new.

## Context
The A4 scripts live outside the repo in `~/.local/share/skillspector-delta/` (`full.py` targets and both passes, `triage.py` noise filter, `delta.py` installed vs candidate). skillspector v2.12.0 is pinned, refuses symlinks (scan the `realpath`), and its model pass uses `SKILLSPECTOR_PROVIDER=claude_cli` (brief A3). A1b's update had about 40 added HIGH findings, all false. Your answer (2026-10-17): show, never block. `update --apply` installs at `bin/claude-config.py` `install_folder` (around `:488`) after staging upstream (`upstream()`, around `:458`). Plugin updates are `fetch: manual` (`:400-402`, `:705-730`).

## Requirements
- **AC-1** (targets): `scripts/skill-scan.py [static|llm|both] [path ...]`. With no path it scans the realpath of every `~/.claude/skills/*` and every `installPath` in `~/.claude/plugins/installed_plugins.json`, nested folders dropped (the `full.py` rule).
- **AC-2** (commands): static runs `skillspector scan <realpath> --no-llm --format json -o <report>`; the model pass sets `SKILLSPECTOR_PROVIDER=claude_cli` and drops `--no-llm`. Static is the default.
- **AC-3** (pin): exits 2 with one line if `skillspector --version` is not v2.12.0, or skillspector is missing.
- **AC-4** (resume): reports go to `~/.claude/state/skillspector/<YYYY-MM-DD>/`; a target that already has a report for that date is skipped; a target whose report is missing after its scan counts as FAIL, and any FAIL exits 1.
- **AC-5** (verdict): HIGH and CRITICAL findings outside `tests/`, `fixtures/` and `.venv/` are compared with `~/.claude/state/skillspector/baseline.json` (key: target, severity, pattern, text). Only added ones print, each with `file:line`. Exit 1 if any were added, else 0. `--accept` adds the current findings to the baseline after you read them.
- **AC-6** (delta): `--against <installed name> <candidate path>` scans both and prints findings the candidate adds.
- **AC-7** (update hook): `claude-config.py update --apply <entry>` runs the delta scan (static) on the staged upstream folder before installing, prints its added HIGH and CRITICAL lines under one heading, then installs as today whatever it found. Missing skillspector prints one line and installs.
- **AC-8** (plugins): the `/claude-config` skill says: before `claude plugin install`, run `skill-scan static <plugin source path>`; after a background plugin update, run `skill-scan` on its installPath.
- **AC-9** (private): nothing the scan writes lands inside the repo; reports and the baseline live only under `~/.claude/state/skillspector/`.
- **AC-10** (install): `bin/install.sh` links `~/.local/bin/skill-scan` to `scripts/skill-scan.py`, like `fb-ask` and `spec-paths`.
- **AC-11** (probe, build step 1): `skillspector scan <realpath of one small skill> --no-llm --format json -o <tmp>; echo $?` records the exit code and the JSON shape the parser relies on. Recorded in verify notes; the build stops if the format differs from `full.py`'s assumption.

## Decision
One stdlib Python script that folds `full.py`, `triage.py` and `delta.py` together, a baseline of known false alarms, and an advisory call in `update --apply`.

## Rationale
A blocking gate would stall on false alarms nearly every update; a baseline makes the printed list short enough to read. Plugins have no install hook in claude-config, so a rule is the honest limit.

## Feature design
**Critical test scenarios** (fake `skillspector` on PATH, fake HOME):
- symlinked skill is scanned by its realpath, verifies **AC-1**
- static and llm command lines, verifies **AC-2**
- wrong version exits 2, verifies **AC-3**
- second run the same day skips done targets; a missing report gives exit 1, verifies **AC-4**
- a baseline finding is hidden, a new HIGH prints with file:line and exits 1, a `.venv` finding is hidden; mutation: drop the baseline compare, red, verifies **AC-5**
- `update --apply` prints the scan heading before "installed upstream" and installs even with findings, verifies **AC-7**

## Build plan
1. Format probe, satisfies **AC-11**
2. `scripts/skill-scan.py` targets, passes, pin, resume, verdict, baseline, delta, satisfies **AC-1** to **AC-6**, **AC-9**
3. `update --apply` hook, satisfies **AC-7**
4. install link, skill text, satisfies **AC-8**, **AC-10**
5. Tests, all ACs

## Consequences
**Positive**: every skill update shows its new risks before it goes live.
**Negative / tradeoffs**: advisory only; a reader can skip the lines. The model pass over everything takes about 1.5 hours, so it is opt in.
**Neutral**: the OSV lookups skillspector makes send package names out (its own behavior).
