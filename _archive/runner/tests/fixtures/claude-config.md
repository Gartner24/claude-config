# Scope: claude-config

Trimmed copy of a real scope (the `· done` tag style).

## At a glance

| # | Feature | Phase | Status |
|---|---------|-------|--------|
| A | Sync and install | Existing | existing |
| 1 | Runner stack and layout | Foundation | done |
| 3 | `next <repo>` | Release 1 | in-progress |

## Existing

### A. Sync and install · existing
`bin/sync.sh` pulls live `~/.claude` into the repo.

## Foundations

### 1. Runner stack and layout · done
- [x] Design it (spec): `/architect runner stack and layout`
- [ ] Scaffold from the decision: `/develop runner stack and layout`

## Release 1: next step in one command

### 3. `next <repo>` · in-progress
- [x] Design it (spec): `/architect next repo command`
- [x] Build it: `/develop next repo command`
   - [x] `wf next` and the `next` shortcut (AC-13, AC-14)
   - [ ] fzf picker, worktrees, `--list` (AC-2, AC-4, AC-12, AC-15)
- [ ] Verify it: `/check verify next repo command`
