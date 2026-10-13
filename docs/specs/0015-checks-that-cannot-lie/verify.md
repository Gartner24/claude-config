# 0015 verify

## Before accept

- Rule files under `~/.claude/rules/` load in headless `claude -p` calls: confirmed by the spec 0012 headless `/scope` probe (2026-10-12), which followed `rules/scope-contract.md`. No new probe needed for the loading itself.

## Probes after build (AC-10, run by you with `!`)

- P1 planted verify step: record date, Claude Code version, pass or fail.
- P2 `/sync` stale spec warning: record date, version, pass or fail.
- P3 brief item dropped by a spec, named by the cross check: record date, version, pass or fail.
