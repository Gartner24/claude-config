# Runner (retired)

## What it is
`wf`, the workflow runner (spec 0001). Retired live on 2026-10-22: `bin/install.sh` no longer copies it to `~/.local/share/wf/<fp>/` (spec 0020) or links `wf` or `next` into `~/.local/bin`. The code is frozen in `_archive/runner/`.

## Where
- `_archive/runner/`: code, `_archive/runner/e2e/`, its tests in `_archive/runner/tests/`, its docs in `_archive/runner/docs/`.
- `_archive/runner/wf.py`: also parses the scope tags (see [scope](scope.md)).

## Rules
- Run its tests by hand, one command: `cd _archive/runner && python3 -m unittest discover -s tests`. Some fail (frozen); see `docs/specs/0072-icm-restructure/verify.md`.
- Python 3 standard library only, tests are `unittest`, external commands go through `subprocess` with argument lists, never a shell string. `bin/claude-config.py` follows the same rules.
- Runner fixtures are flat files (`_archive/runner/tests/fixtures/*.md`) that tests copy into `docs/scope/` or `.workflow/scope/` trees in temp dirs: `.workflow/` is globally gitignored, so a fixture tree there would never be committed. Keep them trimmed and free of client names (public repo).
- `_archive/` links are not checked by `tests/test_layout.py`.

## Also moves
- Nothing live imports it: `claude-home/mods/chip-dash/plan.py` copied its parser.
