# 0037 · Context monitor: one set of thresholds that actually fires

**Date**: 2026-10-14
**Status**: Accepted
**Paths:** `claude-home/hooks/context-monitor.js` (new, a copied file like `claude-home/hooks/block-destructive.sh`), `claude-home/settings.json`, `tools/bin/sync.sh`, `tools/bin/install.sh`, `AGENTS.md`

## What you're agreeing to
- The context warning follows your own rule in `~/.claude/CLAUDE.md`: a nudge once a session passes about 150k tokens (finish the step, then `/rollover` or `/save-and-clear`), and a stronger one 50k tokens before autocompact at 700k.
- Its comments and its code state the same numbers, and a self check fails if they ever drift apart.
- Today the warning never fires at all, because the file it reads is no longer written. The new version reads the session's own transcript instead, so it works with any status line.
- It moves into your own hooks (copied and synced like `block-destructive.sh`), so a get-shit-done update cannot undo it. It stays silent inside unattended `wf` steps.

## Terms used below
- **Context**: the tokens the model holds for the session so far. **Autocompact**: Claude Code's automatic, lossy summary when context reaches a limit; here `autoCompactWindow: 700000` (`settings.json:531`).
- **PostToolUse hook**: a command Claude Code runs after each tool call; text it returns as `additionalContext` is shown to the model.
- **Bridge file**: `/tmp/claude-ctx-<session>.json`, which the old monitor reads and only gsd's status line script writes.
- **Transcript**: the session's `.jsonl` log; each assistant line carries `message.usage`, whose input, cache creation and cache read token counts add up to the context size at that turn.

## What the code does today
- The header says WARNING at 35% remaining and CRITICAL at 25% (`~/.claude/hooks/gsd-context-monitor.js:14-16`); the code uses 10% and 5% (`gsd-context-monitor.js:25-26`).
- It exits silently when the bridge file is missing (`gsd-context-monitor.js:69-75`). Only `gsd-statusline.js` writes it (`~/.claude/hooks/gsd-statusline.js:40-53`), but the status line in use is jjstack's `statusline.sh` (live `settings.json`) or `wf auto bar`, which wraps it (`runner/auto.py:256`, repo `settings.json:484`). Neither writes the bridge, and no `/tmp/claude-ctx-*` file exists (checked 2026-10-14). The monitor has not fired for these sessions.
- Neither threshold fits this setup. Remaining percent is of the whole 1M window, and autocompact runs at 700k used, which is 30% remaining: 10% and 5% are never reached before compaction, and 25% is past it. Only the 35% line (650k used) would fire, 50k before compaction.

## Acceptance criteria
- **AC-1** (numbers and their sources): `WARN_TOKENS = 150000` (`~/.claude/CLAUDE.md` `### Context`: "Past ~150k tokens: finish the current step and suggest `/rollover`"), `AUTOCOMPACT_TOKENS = 700000` (`settings.json` `autoCompactWindow`), `CRITICAL_TOKENS = AUTOCOMPACT_TOKENS - 50000`. The header comment states these three numbers and nothing else about thresholds.
- **AC-2** (comments match code): `node hooks/context-monitor.js --test` fails when the header comment's numbers differ from the constants, and when `AUTOCOMPACT_TOKENS` differs from `autoCompactWindow` in the repo `settings.json`.
- **AC-3** (reads the transcript): the hook reads at most the last 256 KB of `transcript_path` from its input, takes the newest assistant line that is not a sidechain (`isSidechain` not true) and has `message.usage`, and sums `input_tokens`, `cache_creation_input_tokens` and `cache_read_input_tokens`. No usage found, or any read or parse error: exit 0 with no output.
- **AC-4** (when it speaks): WARNING when used tokens first reach 150k, and again at each further 100k (250k, 350k, ...) below CRITICAL; CRITICAL once when used tokens first reach 650k. The last level spoken is kept per session in `os.tmpdir()/context-monitor-<session>.json` (session ids with `/`, `\` or `..` rejected, as today, `gsd-context-monitor.js:51-53`).
- **AC-5** (what it says): WARNING: "Context: <n>k tokens used. Rule (`~/.claude/CLAUDE.md` Context): finish the current step, then `/rollover` mid feature or `/save-and-clear` at a boundary." CRITICAL: "Context: <n>k tokens used; autocompact (lossy) runs at 700k. Do not start new work: finish this step and `/rollover` now." ASCII only.
- **AC-6** (silent under `wf`): with `WF_RUN` set the hook exits 0 at once.
- **AC-7** (wiring): `settings.json` PostToolUse runs `node ~/.claude/hooks/context-monitor.js` in place of `gsd-context-monitor.js` (`settings.json:335`), same matcher. The gsd file stays where its installer put it, unwired. `sync.sh` and `install.sh` copy `hooks/context-monitor.js` like the other copied hooks (`sync.sh:44-47`, `install.sh:36-40`); `NOTICE.md` lists it as derived from get-shit-done-cc with that project's license line; `HOOKS.md` gets its row; `AGENTS.md` `## Commands` gets the `--test` line and `## Rules` lists it among the copied files.
- **AC-8** (self check): `--test` feeds fixture transcripts (149999, 150000, 249999, 250000, 649999, 650000 tokens; a sidechain line newer than the main one; a truncated last line; no usage at all) and asserts the output of each, plus AC-2 and AC-6.
- **AC-9** (live): copying the hook into `~/.claude/hooks/` and `./install.sh` are ` · waits on you · live` boxes (they write `~/.claude`, spec 0021 AC-7); after them, `python3 -c 'import json,sys; json.load(open(sys.argv[1]))' ~/.claude/settings.json` exits 0.

## Build plan
1. Probes P1 to P3, results in `verify.md`.
2. `hooks/context-monitor.js` with its `--test`, from the gsd file minus the bridge, the `.planning` checks and the GSD message variants. AC-1 to AC-6, AC-8.
3. Wiring, sync and install lists, docs. AC-7.
4. Live copy and install. AC-9.

## Probes
Run by you (P1 and P2 call the real `claude`):
- **P1** hook input and transcript usage: a PostToolUse hook `cat > /tmp/p1-hook.json` in a temp settings file, `claude -p --settings /tmp/p1-settings.json "run: echo hi"`; then `jq -r .transcript_path /tmp/p1-hook.json` names a file, and `tail -n 20 <that file> | jq -c 'select(.type=="assistant") | .message.usage'` shows the three token fields. AC-3 rests on it.
- **P2** the model sees `additionalContext` from PostToolUse: a hook that prints `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"P2-MARKER"}}`, then `claude -p --settings /tmp/p2-settings.json "run: echo hi, then quote any P2 text you were given"`; the reply contains P2-MARKER.
- **P3** license: `npm view get-shit-done-cc license` (for the `NOTICE.md` line).

## Follow-up
- On a 200k window model, autocompact runs near 167k, before CRITICAL can be reached; the 150k WARNING still comes first. Recorded, not handled.
- A get-shit-done update may wire its own monitor back into `settings.json`; `./sync.sh` then shows it in the diff.
