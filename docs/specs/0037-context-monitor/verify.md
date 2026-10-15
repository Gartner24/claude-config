# 0037 verify

## Probes

- **P3** license, 2026-10-14: `npm view get-shit-done-cc license repository.url` printed
  `license = 'MIT'` and `repository.url = 'git+https://github.com/gsd-build/get-shit-done.git'`.
  Confirmed. `NOTICE.md` names it.
- **P1** transcript usage, 2026-10-14, partial: inside a `wf run` call (`claude -p`), its own
  transcript under `~/.claude/projects/<cwd slug>/<session>.jsonl` read with
  `jq -c 'select(.type=="assistant") | {sc: .isSidechain, u: .message.usage}'` shows
  `isSidechain: false` and all three of `input_tokens`, `cache_creation_input_tokens`,
  `cache_read_input_tokens` on every assistant line (for example 2 + 212 + 93373).
  Hook input half, 2026-10-15, conductor session, real `claude -p` in an empty folder: the
  PostToolUse input had `transcript_path` naming a file that exists, and its last 20 lines gave
  `{"input_tokens":2,"cache_creation_input_tokens":51248,"cache_read_input_tokens":16599}`.
  Confirmed. The spec's command puts the prompt after `--allowedTools`, which takes many values
  and swallows it; the probe ran `claude -p "<prompt>" --settings <file> --allowedTools "Bash(echo hi)"`.
- **P2** `additionalContext` reaches the model, 2026-10-15, same way: the reply quoted
  `PostToolUse:Bash hook additional context: P2-MARKER`. Confirmed.

## Verify run 2026-10-14 (`/check verify context monitor`, FAIL)

Each step pipes `{"session_id":..,"transcript_path":..}` into `node hooks/context-monitor.js`
with `WF_RUN` unset and `TMPDIR` a temp dir.

- [x] `node hooks/context-monitor.js --test` -> `all checks passed`, exit 0 -> AC-8.
  can fail: a fixture's expected output differs from the hook's.
- [x] One session climbing 100k, 149999, 150000, 200000, 249999, 250000, 350000, 550000,
  649999, 650000, 699000 -> WARNING at 150k, 250k, 350k, 550k, CRITICAL at 650k, silent on the
  rest; state file `{"last":650000}`; exact AC-5 text -> AC-1, AC-4, AC-5.
  can fail: the mark repeats inside a 100k band, or CRITICAL fires twice.
- [x] Newer sidechain line at 900k after a main line at 160k -> WARNING names 160k -> AC-3.
  can fail: the hook reads the sidechain usage.
- [x] `WF_RUN=1` at 700k -> no output, exit 0 -> AC-6. can fail: the env check is dropped.
- [x] Garbage stdin, missing transcript, session id `../x` -> no output, exit 0, no state file
  outside the temp dir -> AC-3, AC-4. can fail: an uncaught throw, or a path escape.
- [x] This repo's three real transcripts (up to 3.6 MB), every usage doubled -> the hook names
  the newest main line's sum (238894 -> 238k, 202410 -> 202k; 56828 silent) -> AC-3.
  can fail: the newest main usage line is outside the 256 KB tail on a real layout.
- [x] Temp repo copy with header WARN_TOKENS 140000 -> `--test` exit 1; settings
  `autoCompactWindow` 800000 -> exit 1; clean copy -> exit 0 -> AC-2.
  can fail: the drift check ignores the header or settings.json.
- [x] `./install.sh --dry-run` -> `would: cp -a .../hooks/context-monitor.js
  ~/.claude/hooks/context-monitor.js` and chmod -> AC-7. can fail: the hook missing from the list.
- [x] `sync.sh` with `CLAUDE_LIVE_DIR` a temp live tree holding the hook -> exit 0, repo copy
  byte identical -> AC-7. can fail: the cp line missing or wrong path.
- [ ] FAIL, AC-7: `sync.sh` checks every other copied hook for private names before copying
  (`sync.sh:23-25`, spec 0013: a refused sync leaves the repo unchanged), but not
  `hooks/context-monitor.js`. A made up name in the live hook: sync copies it into the repo and
  only the after copy scan fails (`sync done, but the repo holds a private name`). The same
  name in live `plain-panel.py`: `sync refused ... nothing was copied`. Fix: add
  `"$LIVE/hooks/context-monitor.js"` to the `check` list, and a case to the
  `private-names.py --test` sync checks.
  Fixed 2026-10-15: `sync.sh` checks `$LIVE/hooks/context-monitor.js` before copying, and
  `private-names.py --test` gained the case (mutation checked: red without the sync line, green with it).
- [ ] NOT APPLIED, AC-9: the scope box "Install it live" is ticked, but
  `~/.claude/hooks/context-monitor.js` does not exist and live `settings.json` PostToolUse still
  runs `gsd-context-monitor.js`. The install likely ran from a checkout without this branch.
  Rerun `./install.sh` from this branch (or after merge) and untick the box until then.
- P1 hook input half and P2: confirmed 2026-10-15 on the real `claude -p` (Probes above).
- Docs rows (`NOTICE.md`, `HOOKS.md`, `AGENTS.md`) read, present; not counted, a read of text
  the change added cannot fail.

## Verify run 2026-10-15 (`/check verify context monitor`, PASS for AC-1 to AC-8)

Each hook step pipes `{"session_id":..,"transcript_path":..}` into the real
`node hooks/context-monitor.js` with `WF_RUN` unset and `TMPDIR` a temp dir.

- [x] `node hooks/context-monitor.js --test` -> `context-monitor: all checks passed`, exit 0 -> AC-8.
  can fail: a fixture's expected output differs from the hook's.
- [x] One session climbing 100000, 149999, 150000, 200000, 249999, 250000, 350000, 550000,
  649999, 650000, 699000 -> WARNING at 150k, 250k, 350k, 550k, CRITICAL at 650k, silent on the
  rest, exact AC-5 text, state file `{"last":650000}` -> AC-1, AC-4, AC-5.
  can fail: a repeat inside a 100k band, CRITICAL twice, or a threshold off by one.
- [x] Main line 160k, newer sidechain line 900k -> WARNING names 160k -> AC-3.
  can fail: the hook reads the sidechain usage.
- [x] `WF_RUN=1` at 700k -> no output, exit 0, no state file -> AC-6. can fail: the env check is dropped.
- [x] Garbage stdin, missing transcript, session id `../x` -> no output, exit 0, no
  `context-monitor-x*` file outside the temp dir -> AC-3, AC-4. can fail: an uncaught throw, or a path escape.
- [x] The three newest real transcripts (1.6 to 2.1 MB), every usage doubled -> the hook names
  the sum of the newest main usage line in the last 256 KB as jq computes it (188172 -> 188k,
  220410 -> 220k, 208990 -> 208k) -> AC-3. can fail: a wrong field sum, or the wrong line on a real layout.
- [x] Temp copies: header WARN_TOKENS 140000, header CRITICAL_TOKENS 600000, settings
  `autoCompactWindow` 800000, code WARN_TOKENS 100000 -> `--test` exit 1 each; clean copy exit 0 -> AC-2.
  can fail: the drift check ignores the header, the code or settings.json.
- [x] Repo `settings.json:331-337` PostToolUse matcher `Bash|Edit|Write|MultiEdit|Agent|Task` runs
  `node .../hooks/context-monitor.js`; no `gsd-context-monitor` left in it. `./install.sh --dry-run`
  -> `would: cp -a .../hooks/context-monitor.js ~/.claude/hooks/context-monitor.js` and chmod -> AC-7.
  can fail: the hook missing from the install list or still the gsd file wired.
- [x] `python3 scripts/private-names.py --test` green; with `"$LIVE/hooks/context-monitor.js"` cut
  from the `sync.sh` check list it goes red (`FAIL: AC-4 sync refuses a name in live
  hooks/context-monitor.js`), green again after restore -> AC-7 (the 2026-10-14 FAIL, now fixed).
  can fail: sync copies the hook before checking it for private names.
- `python3 runner/tests/fast.py` -> 751 tests, 0 failed.
- AC-9 not run here: it writes `~/.claude`, which this step cannot. The scope box "Install it
  live after the merge" owns it (`./install.sh` from main, then the `json.load` check).
