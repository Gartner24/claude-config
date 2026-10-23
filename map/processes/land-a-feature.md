# Land a feature

## When
A feature built on its branch is ready to reach `main`.

## Steps
1. Run the checks that match what changed ([checks](checks.md)).
2. `bin/docs-pr.sh [slug]`: docs only commits on `main` reach origin by a small squash merged PR (a direct push is refused); it refuses a commit outside `docs/` (spec 0051 AC-11).
3. `bin/repo-settings.sh [--check] <owner/repo>`: squash only, delete branch on merge, main only through a PR; `--check` only reads and exits 1 on a difference (spec 0051 AC-10).
4. Code reaches `main` only through a merged PR (`claude-home/rules-on-demand/branch-pr.md`).

## Done when
- The PR is merged and its branch deleted.

## Gotchas
- `jjstack/` is gitignored /review scratch; reports never enter the repo from there.
- Conventional Commits (`feat(scope):`, `fix(scope):`, `chore:`, `docs:`); a gsd hook enforces the format.
