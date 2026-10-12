# 0010 verify: probes and manual checks

Probes on the real `claude` (2.1.296). AC-9 lists the set; each one gets its command and result here.

## P1. A forked skill runs in `claude -p` and writes the report (run 2026-10-12, before acceptance)

Why: the design depends on `design-gate` (a `context: fork` skill) running inside a headless call and leaving `.design/audit-report.md` in the repo.

Setup: a scratch dir with `.claude/skills/forkprobe/SKILL.md`, frontmatter `context: fork`, body: write `.design/audit-report.md` with the lines `# Design audit - probe` and `verdict: PASS`, then reply `WRITTEN`.

```
env -C <scratch>/forkprobe claude -p "Invoke the forkprobe skill with the Skill tool, then report what it returned." \
  --output-format json --permission-mode auto --max-budget-usd 1
```

Result:
- `subtype: success`, `is_error: false`, 2 turns, 11 s. The result says the skill ran as a forked execution and returned `WRITTEN`.
- `.design/audit-report.md` exists with exactly the two lines.
- One `permission_denials` entry: the fork's first try was a `mkdir && printf && cat` chain, refused by your Bash shape hook; it retried in another form and wrote the file. The parent saw only `WRITTEN`, which is why `wf` reads the file, never the claim.
- Not under the spec 0007 sandbox (not built yet). P2 repeats this through `wf run`.

## P2 to P4

Not run yet. They need the real logged in `claude` under `wf run`. A `wf run` call cannot start one: its sandbox hides `~/.claude/.credentials.json`. So you run them from your own terminal. If P2 fails because the sandbox blocks the report write or the fork, or the `design-gate` half of P3 fails, the spec goes back to `/architect`.

Setup for each probe: a scratch git repo on a branch `work` off `main`. It needs `docs/scope/scope.md` with `**Autopilot:** allowed`, plus `wf allow <scratch>`. Use a separate `XDG_STATE_HOME`, and an `XDG_CONFIG_HOME` that holds a copy of your `ntfy.json` (see the `wf run` scratch recipe).

- [ ] P2: give the repo a `design.md`. Use one feature with `/develop` "write `src/components/Nav.tsx`, a nav bar per design.md" and a `Verify it: /check verify` box. Run `wf run <scratch> -y`. Expect `done:`, a `.design/audit-report.md` in the repo with a passing verdict, and in `run.json` a `design.problems` of `[]` and a last call of kind `sync`. -> AC-9, AC-3
- [ ] P3: use one `/develop` box whose text asks the call to invoke the `design` skill, then the `design-gate` skill. Expect a `Skill(design)` denial in the first call's `denials`, and a `design-gate` run that leaves `.design/audit-report.md`. -> AC-9, AC-6
- [ ] P4: use no `design.md`, no brand board and no `.design/`. One `/develop` box asks for a new pricing page. Expect `parked: blocked: no locked design for ...`, and no new `.tsx` or `.html` file in the repo. -> AC-9, AC-5

# Verify: Design enforcement unattended · spec 0010 · updated 2026-10-12
_Steps derived from spec 0010 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [ ] `python3 -m unittest discover -s runner/tests -p test_design.py` -> all pass -> AC-1 to AC-8
- [ ] `python3 -m unittest discover -s runner/tests` -> all pass. The pinned prompt and deny list in `test_run.py` include the AC-5 lines and AC-6 denies. -> AC-5, AC-6
- [ ] A fake claude run where `/develop` writes `src/components/Nav.tsx` and no report exists parks `design_gate`, says `(no report)`, makes no sync call and exits 6 -> AC-3, AC-8
- [ ] The same run plus a later call that writes `.design/audit-report.md` ending `verdict: PASS WITH FINDINGS` reaches `/sync` -> AC-3, AC-4
- [ ] Base: on a branch off `main`, a `.tsx` changed on `main` before the branch point is not in `design.changed`. Committed and uncommitted branch edits are in it. With `main` renamed away, `design.base` is null and every frontend file counts. -> AC-1
- [ ] Rule: `app/page.tsx` and `src/ui/c.ts` count, `lib/ui.ts`, `x.test.tsx`, `dist/app.css` and `vendor.min.css` do not -> AC-2
- [ ] Freshness: a passing report with `st_mtime_ns` one below the file's parks `older than the file`, and an equal one passes -> AC-3
- [ ] Candidates: a FAIL report in the file's folder plus a passing root report covers it, and a report above `c.path` is never read -> AC-3
- [ ] Verdict: the last matching line wins, `**verdict:** stop` reads `STOP`, and the template line and `verdict: PASS (a | b)` never match -> AC-4
- [ ] Park detail: with 6 uncovered files it lists the first 5 in path order behind `6 frontend file(s) not covered ...` -> AC-3
- [ ] Order: a retried sync call does not record a second check, and a `VERIFY FAIL: debug` runs the debug call before the check -> AC-3
- [ ] Record: `design` is null when the run ends before rule 14 (a `BLOCKED:` park), else it holds base, changed, reports and problems -> AC-7

## Acceptance-criteria coverage
- AC-1 base and changed files: Base step · AC-2: Rule step · AC-3: fake run, Freshness, Candidates, Park detail and Order steps · AC-4: Verdict step · AC-5: suite step, P4 · AC-6: suite step, P3 · AC-7: Record step · AC-8: fake run step · AC-9: P2 to P4
