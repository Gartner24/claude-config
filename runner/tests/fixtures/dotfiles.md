# Scope: dotfiles restructure

Trimmed copy of a real scope (the `(existing)` tag style). The header mentions
system files like `/etc/keyd`, which must never read as a command.

## At a glance

| # | Feature | Phase | Status |
|---|---------|-------|--------|
| A | Shell config (zsh, p10k) | Existing | existing |
| 1 | Repo layout and linking method | Foundation | in-progress |
| 2 | Program inventory | Foundation | planned |
| 3 | zsh through the new layout | Slice 1 | done |

## Already in the repo

### A. Shell config (zsh, p10k) (existing)
`.zshrc` and `.p10k.zsh`, symlinked from home.

## Foundations

### 1. Repo layout and linking method (in-progress)
**Done when:** a spec records the layout.
- [x] Design it (spec): `/architect repo layout and linking method`
- [ ] Build it: `/develop repo layout and linking method`
  - [x] Deny list, commit hook and profile lists (AC-3, AC-9)
  - [x] `dot install` and `dot status` for stow packages (AC-2, AC-4)
  - [x] `dot sync` with scoped staging and submodule guard (AC-10)
  - [ ] claude-config as a submodule, called by dot install and sync (AC-16), after its branch is merged
- [x] Verify it: `/check verify repo layout and linking method`

### 2. Program inventory (needs a decision)
- [ ] Design it (spec): `/architect program inventory`

## Slice 1: zsh through the new layout

### 3. zsh through the new layout (done)
- [x] Build it: `/develop zsh through the new layout`
- [x] Verify it: `/check verify zsh through the new layout`

## Deferred
- [ ] Design it (spec): `/architect claude-config reorganization`
