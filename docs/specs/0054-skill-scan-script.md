# 0054. One skill scan command, run before every skill update

**Date**: 2026-10-17
**Status**: Accepted
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
- **AC-4** (resume, workers, timeouts): reports go to `~/.claude/state/skillspector/<YYYY-MM-DD>/<pass>/` (`static` and `llm` apart). A report is written to a temp name and renamed when complete; resume skips a target only when its report parses as JSON. Workers: 6 static, 3 llm. Each target has a timeout (static 300 s, llm 1800 s); a timeout, a non zero exit with no report, or an unparsable report counts as FAIL, and any FAIL exits 1.
- **AC-5** (verdict): a finding is kept when it is HIGH or CRITICAL and its file does not match the `NOISE` pattern carried over from `~/.local/share/skillspector-delta/triage.py:7` (tests, `__tests__`, benchmarks, evals, examples, fixtures, `node_modules`, `.venv`, CHANGELOG, `.test.`, `_test.`, `test_`). Its key is (stable target name, severity, pattern and text, each with every digit run replaced by `N`), where the stable name is the skill folder name or the plugin key without its version or commit. Kept findings not in `~/.claude/state/skillspector/baseline.json` print, each with `file:line`; exit 1 if any, else 0. Each pass is compared only with the baseline of the same pass. `--accept` adds the current kept findings of that pass to the baseline; the first build run does one bulk `--accept static` of today's state, since A4 found no real issue.
- **AC-6** (delta): `--against <installed name> <candidate path>` scans the installed realpath and the candidate with the same key and prints what the candidate adds; a skill with no installed copy counts every kept finding as added. If either scan fails, it prints `scan failed: <side>` and never "no new findings".
- **AC-7** (update hook): in `update_apply` (`bin/claude-config.py:445-501`), right before `install_folder` (`:488`), the folder about to be installed (`result`, which is the merged copy for an edited entry) is delta scanned (static, 300 s cap) against the live realpath; its added lines print under one heading, then it installs as today. A conflict exit, which installs nothing, skips the scan. Missing skillspector or a failed scan prints one line and installs.
- **AC-8** (plugins): the `/claude-config` skill says: before `claude plugin install`, run `skill-scan static <plugin source path>`; after a background plugin update, run `skill-scan` on its installPath.
- **AC-9** (private): nothing the scan writes lands inside the repo; reports and the baseline live only under `~/.claude/state/skillspector/`.
- **AC-10** (install): `bin/install.sh` links `~/.local/bin/skill-scan` to `scripts/skill-scan.py`, like `fb-ask` and `spec-paths`.
- **AC-11** (probe, build step 1): `skillspector scan <realpath of one small skill> --no-llm --format json -o <tmp>; echo $?` records the exit code and the JSON shape the parser relies on. Recorded in verify notes; the build stops if the format differs from `full.py`'s assumption.

- **AC-12** (narrowing said plainly): the plan says "both passes, rerun before every install". The update hook runs only the static pass (the model pass over one skill can take 20 minutes), and plugins can only be scanned before or after their own install. `skill-scan both` remains the full check you run by hand. Spec 0048 AC-10 gains one sentence: "`update --apply` prints a static skill scan of what it installs, and still never asks."

## Decision
One stdlib Python script that folds `full.py`, `triage.py` and `delta.py` together, a baseline of known false alarms, and an advisory call in `update --apply`.

## Rationale
A blocking gate would stall on false alarms nearly every update; a baseline makes the printed list short enough to read. Plugins have no install hook in claude-config, so a rule is the honest limit.

## Feature design
**Critical test scenarios** (fake `skillspector` on PATH, fake HOME):
- symlinked skill is scanned by its realpath, verifies **AC-1**
- static and llm command lines, verifies **AC-2**
- wrong version exits 2, verifies **AC-3**
- second run the same day skips done targets; a truncated report is scanned again; a timeout and a missing report give exit 1, verifies **AC-4**
- a baseline finding is hidden, a new HIGH prints with file:line and exits 1, a `.venv` finding is hidden, the same finding after a plugin version change and a line shift stays hidden; mutation: drop the baseline compare, red, verifies **AC-5**
- a failed candidate scan prints `scan failed`, never "no new findings", verifies **AC-6**
- `update --apply` on an edited entry scans the merged folder before "installed upstream" and installs even with findings; a conflict exit runs no scan, verifies **AC-7**

## Build plan
1. Format probe, satisfies **AC-11**
2. `scripts/skill-scan.py` targets, passes, pin, resume, verdict, baseline, delta, satisfies **AC-1** to **AC-6**, **AC-9**
3. `update --apply` hook, satisfies **AC-7**
4. install link, skill text, the 0048 sentence, satisfies **AC-8**, **AC-10**, **AC-12**
5. Bulk accept of today's static findings as the baseline, satisfies **AC-5**
6. Tests, all ACs

## Consequences
**Positive**: every skill update shows its new risks before it goes live.
**Negative / tradeoffs**: advisory only; a reader can skip the lines. The model pass over everything takes about 1.5 hours, so it is opt in.
**Neutral**: the OSV lookups skillspector makes send package names out (its own behavior).
