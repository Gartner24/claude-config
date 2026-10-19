# 0054 verify notes

Notes for the flat spec [0054-skill-scan-script.md](../0054-skill-scan-script.md).

## AC-11 format probe (build step 1, 2026-10-17)

```
skillspector --version
  -> SkillSpector v2.12.0
skillspector scan ~/dotfiles/claude-config/claude-home/skills/claude-config --no-llm --format json -o /tmp/claude/probe-0054.json
  -> exit 0, "Report saved to: /tmp/claude/probe-0054.json"
```

Top level keys: `skill`, `risk_assessment`, `components`, `structured_summaries`, `issues`,
`suppressed_count`, `suppressed`, `metadata`, `execution_successful`, `analysis_completeness`.
That skill had no issues, so the issue shape was read from an A4 report of the same version
(`~/.local/share/skillspector-delta/a4-static/`, 224 reports, 8908 HIGH or CRITICAL): each issue has
`severity`, `pattern`, `finding`, `code_snippet`, and `location.file` plus `location.start_line`.
This is what `full.py`, `triage.py` and `delta.py` assumed, so the build went on.

# Verify: skill scan · spec 0054

Run 2026-10-17 with the real skillspector v2.12.0 under a fake HOME (a clean skill, a risky
skill with a `tests/` copy, and a plugin whose installPath holds a nested skill that is also
linked under `skills/`). Scripts in `$TMPDIR/v0054/`. A logging stand in for skillspector was
used only for the model pass (the real one calls Claude for minutes) and the pin checks.

## Commands
- [x] `skill-scan` (no path) -> 3 targets (nested folder dropped), 5 new HIGH each with `file:line`, `tests/` copy hidden, exit 1; reports named by realpath under `<HOME>/.claude/state/skillspector/2026-10-17/static/` -> AC-1, AC-2, AC-5 · can fail: scanning the symlink path or keeping the nested target
- [x] `skill-scan --accept` -> "static: baseline holds 5 findings", exit 0 -> AC-5 · can fail: accept not writing the baseline
- [x] Truncate one report, move the plugin to 1.1.0 with a line shift, add one real finding -> only the new finding prints, the truncated report is rescanned (new mtime, full size), exit 1 -> AC-4, AC-5 · can fail: version or line digits kept in the key, resume trusting a broken report
- [x] Rerun the same day -> no report mtime changes -> AC-4 · can fail: resume rescanning done targets
- [x] Model pass through the logging stand in -> argv has no `--no-llm`, `SKILLSPECTOR_PROVIDER=claude_cli`, `.part` temp name, own `llm/` folder -> AC-2, AC-4 · can fail: `--no-llm` left on the model pass
- [x] Model pass finding already in the static baseline -> still prints, exit 1 -> AC-5 · can fail: one baseline shared by both passes
- [x] Version v2.11.0 -> one line, exit 2; skillspector absent -> one line, exit 2 -> AC-3 · can fail: pin check skipped
- [x] A scan exiting 3 with no report, and a scan past a 2 s timeout -> two FAIL lines, exit 1, no `.part` left -> AC-4 · can fail: a failed target counted as clean
- [x] `--against risky <candidate adding one finding>` -> only that finding, exit 1; same content -> "no new findings", exit 0; no installed copy -> every finding, exit 1; missing candidate -> `scan failed: candidate`, exit 1 -> AC-6 · can fail: a failed scan read as "no new findings"
- [x] Real `claude-config update --apply s` on an edited entry, upstream adds a risky script -> scan lines print before "installed upstream", the merged copy (your edit plus upstream) installs, exit 0; a conflict exits 2 with no scan line -> AC-7 · can fail: scanning upstream instead of the merged copy, or blocking on findings
- [x] `bin/install.sh --dry-run` -> `skill-scan -> scripts/skill-scan.py` link line; the script runs through a link -> AC-10 · can fail: the link missing or the script failing when run through it
- [x] `git status` after every run -> no new file in the repo -> AC-9 · can fail: reports written to the current folder

## AC-13 trusted list (2026-10-18)

Run the real script as a command under a fake HOME with a logging stand in for skillspector: trusted
packs `gstack` (holding `qa`, also linked as `skills/qa`) and `ui-ux-pro-max`, no `jjstack` folder,
and separate folders `gstack-upgrade`, `other`, `packs/jjqa`. Driver: `/tmp/claude/verify0054/drive.py`.

- [x] `skill-scan` -> first line `skipped (trusted): gstack, ui-ux-pro-max` (no `jjstack`), scanned only `gstack-upgrade`, `other`, `packs`, the `qa` link not promoted, exit 0 -> AC-13 · can fail: filter dropped (mutant scanned `gstack` and `ui-ux-pro-max`, 5 targets)
- [x] `skill-scan both` in a fresh HOME -> the skip line once, both passes scan the same 3 targets (static with no provider, llm with `claude_cli`) -> AC-13 · can fail: only the exact pack folder matched (mutant scanned `gstack/qa` in both passes, 4 targets)
- [x] `skill-scan <HOME>/.claude/skills/gstack` -> scans `gstack`, no skip line -> AC-13 · can fail: the explicit path filtered too
- [x] `skill-scan --against gstack <candidate>` -> scans both the installed `gstack` and the candidate -> AC-13, AC-7 · can fail: the update hook skipping a trusted pack
- [x] Real `~/.claude`, read only `targets([])` with no scan -> `skipped (trusted): gstack, jjstack, ui-ux-pro-max`, 227 targets, none under the three packs; `gstack-upgrade` and `open-gstack-browser` (own folders) kept -> AC-13 · can fail: a trusted pack name not matching the real install

## Read only (not counted as can fail)
- AC-8: `/claude-config` skill names `skill-scan static <plugin source path>` before install and `skill-scan <installPath>` after a background update.
- AC-12: spec 0048 AC-10 carries the sentence; the scope row names the static only hook.
- AC-11: format probe above.

## Owed to you
- Bulk baseline of today's real skills (`skill-scan static --accept`, scope box `· waits on you`). The mechanism is verified above; the real baseline file does not exist yet.
