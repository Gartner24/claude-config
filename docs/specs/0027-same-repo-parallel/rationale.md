# 0027 rationale

## Context

Brief `docs/briefs/finish-runner-today.md` item 17 ("Several features of the same repo at once, needs 16"); personal scope row 23 left it as "a separate, later step: it needs ... a branch per spec first, so two builds never edit the same files". Spec 0026 gives each feature its own branch and keeps what is built in `queue.json` `prs` records, not in one branch's scope.

What the code does today:
- Spec 0017 runs one child process per repo (`parallel`, `runner/run.py:3684-3780`); each child is a complete single repo run with its own lock, guard, run folder and waits, and shared state (`queue.json`) is already safe across processes.
- `clashes` (`runner/run.py:3678-3681`) keeps children apart that share a port, a git common dir, or a folder.
- `untrusted` (`runner/run.py:3063-3069`) wants the exact real path on the trust list; `repo_lock` (`:3267-3270`) is keyed by path.
- Spec 0007 already guards a linked worktree (its `.git` file, `commondir`, `gitdir`, `config.worktree`) and lets a call commit there.

## Options considered

1. A child per feature worktree, reusing spec 0017 (chosen). Pro: every per run invariant (lock, guard, caps, park memory, signals) holds per process as it does today; the new code is scheduling plus worktree upkeep. Con: shared git common dir needs the `clashes` exception and the Edit denies of AC-7.
2. Threads inside one repo run. Rejected for the same reason spec 0017 rejected threads: all run state would need to become thread safe.
3. Separate clones per feature. Rejected: no shared object store, every clone needs its own trust entry and remote setup, and stacked branches (spec 0026) would have to travel between clones.

## Decided without asking (2026-10-13)

Per `docs/briefs/finish-runner-today.md`. Each: question, options, pick.

1. Opt in how? Options: always parallel in `branches: per spec` repos; a `parallel: <n>` standing answer. Pick: the standing answer, 1 to 4, since parallel calls burn usage faster and some repos have one app port.
2. Where do worktrees live? Options: beside the repo (`<repo>.wf/`); under `~/.cache`; under the state folder; under `~/.local/share/wf-trees/`. Pick: `~/.local/share/wf-trees/`. Beside the repo puts them in the folders `next` scans as projects; `~/.cache` is a write path of every call (`runner/run.py:71`), so any call could write any feature's tree; the state folder is Edit denied to calls (spec 0020 AC-5); `~/.local/share/wf` is denied too (spec 0020 AC-12), hence a sibling folder name.
3. When are two features too close? Options: same spec; overlapping `**Paths:**` globs; a dry run diff. Pick: overlapping globs, the Paths line every spec already carries (spec 0015). No Paths line means it runs alone, the safe side.
4. Files every feature touches (scope, AGENTS.md, verify.md)? Options: count them, which makes every pair overlap; leave them out. Pick: leave them out and accept possible merge conflicts there (Follow-up), or parallel never happens.
5. A feature that drifts into a sibling's Paths mid build? Options: go on; undo; wait. Pick: question with "wait for the other to finish" recommended, which keeps "never two features on the same Paths at once" true without throwing work away.
6. Keep records under the worktree path or the repo? Pick: the repo (main checkout) plus a `tree` field, so questions and parks survive a worktree's removal and the report names the repo you know.
7. When to remove a worktree? Options: when the feature ends; when its PR merges or closes. Pick: when its PR merges or closes, since review rounds (spec 0026 AC-12) run in it; never with `--force`.
8. Same app port? Options: run side by side and let the app fail; serialize; a port per worktree. Pick: serialize, as spec 0017 does for repos; a port per worktree is a follow-up.

## Rationale

The fastest safe path is to treat each feature worktree as one more "repo" for the spec 0017 parent, with two additions: a Paths test before starting, and a drift check after each call. Everything a single run guarantees stays per process. Merged results never mix because no code path moves commits between sibling branches and no call can edit a sibling's folder.
