
## Build checks of 2026-10-15 (recovered from the build folder, never committed)

## Commands
- [x] Real jjstack hooks end to end through the two repo `settings.json` commands, `sh -c` and `bash -c`, HOME a temp tree (jjstack linked, index copied): a matching message then a second one logs one `trigger_miss` for `tdd-workflow`; a matching message, the `Skill` hook for `tdd-workflow`, then a second message logs nothing and writes `skill-last-fired.json`; with `WF_RUN` set the state folder is untouched; all exits 0, no stdout -> AC-1, AC-2 (2026-10-15: as expected). can fail: a command without the `WF_RUN` guard writes `skill-last-fired.json` under `WF_RUN` (seen on a guard stripped copy: assertion failed), and a missing entry or a matcher other than `Skill` fails the entry count
- [x] Parse HEAD~1 and HEAD `settings.json`, drop the two new entries from HEAD -> the two are equal -> AC-3 (2026-10-15: equal). can fail: any other change in the commit's `settings.json` makes them differ
- [x] `install.sh --dry-run` from `git archive HEAD` into a temp live tree: good settings exit 0; `settings.json` with a trailing comma exit 1 `refused: <path>/settings.json does not parse: ... Illegal trailing comma ...`; a real install of it exit 1 with the live `settings.json` hash unchanged and nothing copied; `settings.local.json` of `{` exit 1 naming that file -> AC-4, AC-5 (2026-10-15: as expected). can fail: the same run on HEAD~1 `install.sh` exits 0 on both dry runs and copies 136 entries before the real install fails
- [x] `python3 -B scripts/private-names.py --test` -> `all self checks passed` -> AC-5, AC-6 (repo side) (2026-10-15: passed). can fail: its 0036 AC-4 assertion needs a non zero dry run, which HEAD~1 `install.sh` does not give
- [ ] `ls -l ~/.jjstack/skill-triggers.json` after the live install -> dated the install day -> AC-6 (2026-10-15: still 2026-09-02, not rebuilt)
- [ ] `python3 -c 'import json,sys; json.load(open(sys.argv[1]))' ~/.claude/settings.json` and `grep -c 'skill-miss-detect\|skill-fired-clear' ~/.claude/settings.json` -> exit 0, count 2 -> AC-7 (2026-10-15: parses, count 0; the commit is only on this branch, so no live install has carried it, though the plan's install box is ticked)
- [x] `~/.claude/skills/jjstack/bin/jjstack-skill-miss-report` with HOME the temp tree after one logged miss -> exit 0, 24 h and 72 h list `tdd-workflow` with 1 `trigger_miss`, COLD verdict -> AC-8 (2026-10-15: as expected); `HOOKS.md` and `AGENTS.md` name that path. can fail: a report path that does not exist, or hooks that log nothing, leaves `tdd-workflow` out
- [ ] After 3 days of sessions, run the report, write its verdict and top 5 skills here -> AC-9 (later)

## Probes (run by you, none recorded yet)
- [ ] P1 `WF_RUN` reaches hooks in a real `claude -p` call. Seen so far: `WF_RUN` is set in this `wf` call's own tool environment, which hooks inherit; the hook env itself is not yet observed.
- [ ] P2 a typed `/scope` writes `~/.jjstack/skill-last-fired.json`
- [ ] P3 `/missed scope` reaches the hook (`tail -1 ~/.jjstack/skill-misses.jsonl`)

## Acceptance-criteria coverage
- AC-1 met · AC-2 met (hook side; P1 open) · AC-3 met · AC-4 met · AC-5 met · AC-6 repo side met, live left to the box: Install it live after the merge, from main · AC-7 left to the box: Install it live after the merge, from main · AC-8 met · AC-9 left to the box: After 3 days, run the report and write its verdict into verify.md
- 2026-10-15: you chose to reopen the install box as an after merge step and pass verify on the repo side checks.
