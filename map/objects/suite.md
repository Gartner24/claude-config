# The suite

## What it is
The tests for live code. Self-checks are the tests.

## Where
- `tests/fast.py`: runs the suite; `python3 tests/fast.py`. Standing answer: run suite yes.
- `tests/test_layout.py`: repo shape, links, the entry file and its link.
- `tests/test_map.py`: every old `AGENTS.md` line has a home in `map/_meta/line-homes.md`.
- `config/test-preferences.json`: the suite command for `/test`.

## Rules
- A change to a script ships with its assertion in the matching `--test` / `--check` / `test-*.sh`.
- Comments explain why, usually naming the past failure ("this used to..."). Keep that style when fixing a script.
- A test or probe that needs a banned attribution phrase as input builds it from two joined string halves (`"Co-Authored-" + "By: ..."`), so no file holds the whole phrase; the push scan (`pr.attribution_hits`) is never relaxed for tests (spec 0045).
- Mutation check every test added or changed (`claude-home/rules/lessons.md`).

## Also moves
- [runner](runner.md): the archived runner tests are not part of the suite.
- [checks](../processes/checks.md): the other self-check commands.
