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

Not run yet. Build step 4 runs them through `wf run` on a scratch repo after specs 0007 and 0008 are built. If P2 fails because the sandbox blocks the report write or the fork, the spec goes back to `/architect`.
