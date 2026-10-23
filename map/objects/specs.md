# Specs

## What it is
The decisions: one numbered folder or file per feature under `docs/specs/`, written by `/architect`.

## Where
- `docs/specs/`: spec top files (`NNNN-*.md` or `NNNN-*/index.md`) and their child files.
- `scripts/spec-paths.py`: warns when a spec's `**Paths:**` files changed; `bin/install.sh` links it as `~/.local/bin/spec-paths`, which `/sync` runs as `spec-paths --spec NNNN`. Self checks: `python3 scripts/spec-paths.py --test` (spec 0015); tests in `tests/test_spec_paths.py`.

## Rules
- Every spec top file carries a `**Paths:**` line right after `**Status**:` (`claude-home/rules-on-demand/check-gates.md` gate 3).
- A spec that governs no file writes `**Paths:** none`.
- Only `/architect` edits spec text; `/sync` may update status, "Amended by" and "built in" lines.

## Also moves
- A file moved by a change must have its `**Paths:**` globs rewritten in the same change; `scripts/ref-check.py verify` lists the ones left behind ([checks](../processes/checks.md)).
- [scope](scope.md): each feature row links its spec.
