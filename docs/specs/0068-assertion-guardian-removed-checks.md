# 0068. Assertion Guardian blocks only removed checks

**Date**: 2026-10-20
**Status**: Accepted, built in d764b60
**Paths:** `config/manifest.json`, `config/patches/assertion-guardian.patch`, `bin/claude-config.py`, `tests/test_claude_config.py`

## What you're agreeing to
- A test edit made through the shell (sed, cat >>, rm, cp, tee) is no longer refused before it runs. The command runs, the test check compares each test file before and after, and if a check got removed or looser it puts the files back and says so.
- Adding a test or an assertion is never refused, through an edit tool or the shell. Deleting, skipping or loosening a check, or changing an expected value, still is.
- Deleting a scratch test file that git never saw is allowed. Commands the check cannot undo exactly (git, mv, globs, folders, background runs) are still refused before they run, as today.
- Our change is stored as a patch on the author's copy, so each author update is merged into ours and our change is kept (the same path as the other edited skills).

## Summary
The Assertion Guardian mod (github.com/ccdwyer/assertion-guardian, MIT, installed as a plain copy in `~/.claude/skills/assertion-guardian`) refuses every shell command that names a test file, because it cannot see what the command will do. That was 37 of the 62 refusals across all chats, almost all harmless (rationale.md). The fix: let the command run, compare the files afterwards with the same `weakening()` the edit tools already use, and undo the change when it weakens a check. The mod becomes an `edited` manifest entry so updates merge through spec 0048.

## Context
- `hooks/register.tsx` `check()` (line 51): for Bash it calls `bashSignals()` and denies before running; for Edit and Write it computes the file before and after and calls `weakening()` from `hooks/analyze.ts` (line 470), which already passes additions, moves and stronger matchers.
- `commands()` (`analyze.ts` line 506) splits a command line into simple commands; `shellWrites()` (line 619) names the test files or test folders one simple command writes, as typed (relative, `~`, `$VAR`, globs and folders possible).
- A `tool.call` handler that does `await next(e)` gets the result after the tool ran (`~/.claude/skills/loop-guard/hooks/register.ts` line 17; the result has `deny`, `isError`, `text`, `context`).
- Spec 0048: an `edited` entry is upstream at `pinned` plus a patch; `claude-config.py update --apply` three way merges (`merge()`, line 308), conflicts go to `~/.claude/state/claude-config-conflicts/<name>/`; `restore` (run by `bin/install.sh`) rebuilds a missing edited entry from upstream plus the patch. `installed()` maps `kind: skill` to `~/.claude/skills/<name>`. `build()` skips folders with no `SKILL.md` (line 850) and keeps existing entries, so a hand written entry survives a rebuild. Drift (`linked_kind`, line 96) also skips such folders before counting them seen, so today it would report the entry "missing live" (AC-6 fixes that). `patches()` (line 544) turns an `edited` entry back to `downloaded` and deletes its patch when the live copy equals upstream, so the live copy must carry the change before any sync (AC-8).
- The installed copy's two hook files equal upstream at `ae1de89f090f04e6353b03346541c8a9f3e696db` (probe P1, verify.md); the whole tree is checked at build (AC-6).

## Requirements
- **AC-1** (shell plan): a new exported `shellPlan(command, cwd)` in `analyze.ts` returns `{ snapshotUpdate, targets, refuseBefore }` from `commands()` and `shellWrites()` over every simple command of the line (pipes, `;`, `&&` chains, `bash -c` included). Each target is resolved to an absolute path against `cwd`. `refuseBefore` is true when any target: is still not absolute, contains `~`, `$` or a backtick, contains a glob character (`*`, `?`, `[`), is an existing folder, or came from a `git` subcommand or `mv`; or when the line has a `cd`, `pushd` or `popd` before a target. `cwd` is the session's working folder as the mod API gives it (probe P3); with no such value every relative target sets `refuseBefore`.
- **AC-2** (still refused before running, today's text): a bulk snapshot update, `refuseBefore`, a `run_in_background` call with any target, and a target that is not valid UTF-8 text. A command that writes a test file it does not name (a script, a glob the parser misses) is not caught, as today; the README states it as a known gap.
- **AC-3** (run, compare, undo): for any other Bash call with targets:
  1. if the call's fingerprint is in `allowed`, remove it and return `next(e)` with no compare (allow once, spent only here);
  2. before: read each target's text, or note it absent; a failed read refuses before running;
  3. `r = await next(e)` inside `try`/`finally`, so the compare below also runs when the call throws, times out or is aborted; if `r.deny` is set, return `r` untouched;
  4. after: read each target again (absent if gone). A failed read counts as a signal for that target;
  5. for each changed target: if it is gone, the baseline is `previous()` (HEAD's text; `null` when git never had it), else the before text. `weakening(baseline ?? '', after ?? '', path)`. A gone target whose `previous()` is `null` passes;
  6. no signals: return `r` unchanged;
  7. any signals: for every target, put back its before state (rewrite the text, re-create a deleted file with its old mode, delete a file that did not exist before) only if its current text still equals what step 4 read; otherwise name it "changed again, not restored". Set the `blocked` atom with the fingerprint and return `{ deny: <refusal> }` (the model reads "Bash ran, and a plugin withheld its result: <refusal>"; a returned core result with `isError`/`text` never reaches the model, probe P2), also when a file could not be put back. The refusal says the command ran, every named test file was put back (so harmless additions in the same command are undone too), names any file not put back, lists the signals, notes that other effects of the command (a build, a commit) are not undone, and names `/allow-test-change`.
- **AC-4** (allow once): `/allow-test-change` and the band's "allow once" work for the AC-3 refusal: the identical command rerun runs without the compare, once.
- **AC-5** (additions never refused, refusals kept): tests prove these pass with no signal: an Edit adding a test case; a Write of a new test file; `cat >> a.test.ts <<EOF` adding a case; `sed -i` adding an assertion; `cp` restoring a test file to its committed text; `rm` of an untracked `zz-x.test.ts`. And these are refused and undone: `sed -i` removing an assertion, changing an expected value, adding `.skip`, flipping `.not`; `rm` of a committed test file; `python3 -c` rewriting a test file without its assertions; a file changed again by another writer before the undo is reported, not overwritten. The Edit and Write paths keep every current signal, including changed expected values (`weakened()` unchanged).
- **AC-6** (survives updates): the change is built in a scratch folder exported from upstream at `pinned`, after checking `folder_hash(~/.claude/skills/assertion-guardian) == folder_hash(upstream at pinned)` for the whole tree (a mismatch stops the build). `config/manifest.json` gets entry `assertion-guardian`: `kind: skill`, `status: edited`, `fetch: git`, `source: github:ccdwyer/assertion-guardian`, `path: .`, `pinned: ae1de89f090f04e6353b03346541c8a9f3e696db`, `base_hash` = `folder_hash()` of upstream at that commit, `license: MIT`, `publish: true`, `install: copy github.com/ccdwyer/assertion-guardian into ~/.claude/skills/assertion-guardian`, `framework: null`. The patch is `make_patch(upstream at pinned, scratch)` stored with `store_patch()`. `build()` fills the license text for every git entry with a public patch through `legal_texts()`, not only folders with `SKILL.md`, so `write_notice()` writes the MIT block. `linked_kind()` counts a live folder with a manifest entry as seen even without `SKILL.md`, so drift checks its hash and patch instead of reporting it missing. Python tests cover both `claude-config.py` changes and a rebuild from upstream at `pinned` plus the patch that matches the scratch folder byte for byte (this also proves `git archive` of path `.` works, probe P4).
- **AC-7** (tests and scan): new cases in the mod's `tests/assertion-guardian.test.tsx` for AC-1 to AC-5 with `$.fs`, `$.process.run` and `next` mocked to the shape the code reads; `claude plugin test` and `claude plugin validate` on the scratch folder; each new test mutation checked (rules/check-gates.md); `scripts/skill-scan.py --against ~/.claude/skills/assertion-guardian <scratch folder>` before the live install.
- **AC-8** (live install, waits on you, right after the build and before any sync): move `~/.claude/skills/assertion-guardian` to the trash, run `bin/install.sh` (its `restore` rebuilds it from upstream plus the patch; needs github.com reachable), then `python3 bin/claude-config.py drift` shows nothing for it. Until this box is ticked, `bin/sync.sh` is not run (it would delete the patch, Context).

## Options considered
- Shell edits: run, compare, undo (picked); refuse only commands whose effect can be predicted (sed, cat >>) and guess the rest; turn the shell check off.
- Where the change lives: patch on the author's copy (picked); a copy in `claude-home/mods/` linked live (breaks on the first update, rationale.md).

## Rationale
See [rationale.md](0068-assertion-guardian-removed-checks/rationale.md).

## Decision
Run, compare, undo for shell edits whose targets can be undone exactly; everything else as the mod does today. The change is a patch on the author's copy, not a copy in `claude-home/mods/`: a linked repo folder would be replaced by `install_folder()` on the first update, and the patch path is the one the owner already chose for keeping our changes through updates.

## Build plan
1. Probes P2 and P3 (verify.md); stop on a P2 failure. Whole tree hash check and scratch export, part of **AC-6**
2. `shellPlan()` and the run, compare, undo path in the scratch folder, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**
3. Mod tests, README gap line, scan, satisfies **AC-5**, **AC-7**
4. `claude-config.py` drift and notice changes with Python tests, manifest entry, patch, rebuild test, satisfies **AC-6**
5. Live install box, before any sync, satisfies **AC-8**

## Consequences
**Positive**: about 37 of 62 past refusals would not happen; the runner stops stalling on scratch test files.
**Negative / tradeoffs**: a weakening shell edit now runs and is undone, so other effects of the same command (a build, a commit chained after it) stay; git, mv, glob, folder and background commands are still refused before running.
**Neutral**: changed expected values stay refused (owner pick).
