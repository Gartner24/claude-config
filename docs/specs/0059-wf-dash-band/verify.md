# 0059 verify: probes run before the build (AC-6)

Run 2026-10-17 with the throwaway `wf-probe` mod (`claude --plugin-dir`, and hot reloaded in the conductor session), Claude Code 2.1.302.

- [x] P1 AbovePrompt band draws on the terminal surface: green line "wf-probe band: five_hour 10%, seven_day 42%" above the prompt. PASS.
- [x] P2 toast on load: "wf-probe loaded: ..." shown top right. PASS.
- [x] P3 `$.session.usage()` rate limits: `rateLimits` is a list of `{kind: "five_hour" | "seven_day", percentUsed, resetsAt}` (field names to use), matching the status line within 1 point (band 10%/42%, bar 10%/43%). `context.percent` is null until the session's first model reply (band showed `?`, then 6%). PASS.
- [x] P4 `$.process.run(["wf", "queue"])` from a mod: exit 0, first line "claude-config on main, 0 changes". PASS.
- [ ] P4b session id shared between the status line stdin and the mod: not run; the build checks it first and, if absent, keys the short bar marker by cwd.
- [x] P5 the mod loads in a new session: `session.start` logged on each start, also after a hot reload. PASS. `$.state` persistence not exercised; the build keeps toast ids in a file next to its marker.

# 0059 verify: the build (`/check verify`, 2026-10-18)

Driven with the real CLI on scratch state folders (`XDG_STATE_HOME`), scripts kept outside the repo. A second
process held a real run lock, so the stale lock filter was exercised for real.

## Commands
- [x] `wf status --json` with no state at all prints `{"running": null, "parked": [], "questions": []}` and creates no `wf` state folder → AC-1, AC-5. can fail: a missing `active.json` read through `read_active()` would print `[]`.
- [x] Broken `active.json` and `queue.json` print `null` for all three fields → AC-1. can fail: a reader that swallows the parse error as an empty list.
- [x] A live run (lock held by another process) and a stale entry: `running` lists only the live one, its id is the run folder ending in the holder's pid (not the older folder of the same tree, not the `-ab` folder); `parked` is the unanswered parked decision; `questions` both unanswered ones with their title; the answered one is left out; every file under the runner's state is unchanged after the call → AC-1, AC-5. can fail: picking the newest folder by name, or dropping the lock filter.
- [x] After the lock holder exits, `running` is `[]` → AC-1. can fail: an entry kept without its held lock.
- [x] `wf auto bar` with a marker under 15 s old prints the short bar (`work`); another session id, and the same marker made 16 s old, print the full bar → AC-4. can fail: a marker keyed by folder, or no age check.
- [x] `wf auto bar` writes `<session>.effort` only from `.effort.level` (`medium`, then `xhigh`), not from `CLAUDE_CODE_EFFORT_LEVEL` alone, leaves the file untouched for an unchanged level, ignores `../x` as a level or a session id, and writes nothing when the mod folder does not exist → AC-2, AC-5. can fail: reading `statusbar.effort()` with its env fallback.
- [x] Five real `wf status --json` readings fed through the mod's own `alertTick` (bun, `$` faked): no toast on the first tick; then `finished: 1. A - in work`, `stuck: 5. P - ...`, `question: 6. Q - ...`, each with `timeoutMs: 15000` and in the alert list; an all `null` tick and a partly `null` tick toast nothing; after `$.state` was dropped (a reload) the returning question did not toast again (read from its `.toasts` file); the only file written is that `.toasts` file → AC-3, AC-5. can fail: a `null` field read as empty, or no file fallback.
- [x] `$.fs.write` creates missing folders (the type file of Claude Code 2.1.302 says "creating it and its directories as needed"), so the marker makes `~/.local/state/wf-dash` the effort handover needs → AC-4.
- [x] `claude plugin validate claude-home/mods/wf-dash` passes; `claude plugin test` 27 of 27; `python3 runner/tests/fast.py` 1033 tests, 0 failed → AC-7.

## Fixed during verify (design-gate must fix items)
- The narrow band cut off its `stale` mark: the mark's cells now come out of the count budget, and when even the first count does not fit beside it only `stale` shows. Test `the stale mark fits the 31-cell column too`; both guards mutated and seen red.
- A `facts.py` that always failed left the band at "wf-dash: reading status" all session, then (after the first fix) froze the counts: until `facts.py` first answers, the band is built with `?` fields and live counts. No test loads `register.tsx`, so this has no test in the repo yet (left for `/test`); the third design-gate pass drove it with a scratch harness and saw it red on the old line.
- design-gate: pass 3 (asked for by you) PASS with 7 should fix items, report in `claude-home/mods/wf-dash/hooks/.design/audit-report.md`.

## Left to the box: Install the mod live after its scan
- The band drawn above the prompt with effort, usage and counts in a real session (AC-2), real toasts at the top right (AC-3), the bottom bar going short beside it (AC-4), P4b (the status line's session id equals `$.session.id()`), and `skill-scan` on the mod folder (AC-7). They need an interactive Claude Code session.
