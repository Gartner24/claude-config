# 0066 verify

**Date**: 2026-10-19
**Build**: branch `feat/0066-the-word-after-stalls-a-feature` at 82ba9a5
**Result**: PASS (4 of 4)

Observed by loading `runner/wf.py` and calling `pick_next(parse_text(...))` on fixture scope text, and by running the real `wf.py next <repo> -y` with a fake `claude` on PATH.

| AC | Observed | can fail |
|----|----------|----------|
| AC-1 | `- [ ] \`/develop a\`` + milestone `build it after the schema lands`: command `/develop a`, owed None, waiting False. Milestone `merge it · waits on you`: owed `merge it`, waiting True. `wf.WAITING` no longer exists. | `NextBox.waiting` still ORs in a word match on the note, or ignores the note box's marker |
| AC-2 | Milestone `Waits On the merge` (mixed case): waiting False, warning `"waits on" is not the marker here, end the box with " · waits on you": Waits On the merge`. The `after` milestone gives no warning. In a `wf` run plan, an unmarked `waits on the merge` on a later queued feature prints the same warning and the feature stays `queued` (`test_queue.py::test_unmarked_waits_on_warns`). | `NEAR_OWED` still only matches `waits on you`, the warning text keeps the old words, or run.py drops the per-feature marker warnings |
| AC-3 | `wf next` on the unmarked repo: exit 0, line `unmarked \| no git \| - \| 1. A \| /develop a \| note: build after schema`, launched. On the marked repo: exit 3, `waits on you: merge it`, not launched. | `launch` prints `waiting: ` for the note, or the owed box launches |
| AC-4 | `test_wf.py::test_words_never_wait` holds both cases; with the old word guess put back it goes red (mutant M1 below). | the test reimplements the logic instead of calling `wf.pick_next` |

## Mutation check (tests this branch added or changed)

| Mutant in source | Test(s) red, green after restore |
|------------------|-------------------------------|
| M1 `waiting` ORs `\b(after\|waits on)\b` on the note again | `test_wf::test_open_parent_takes_first_open_milestone_as_note`, `test_wf::test_words_never_wait` |
| M2 `NEAR_OWED` back to `waits on you` | `test_wf::test_words_never_wait`, `test_queue::test_unmarked_waits_on_warns` |
| M3 warning text back to `"waits on you" is not` | `test_wf::test_owed_box_never_launches`, `test_queue::test_unmarked_waits_on_warns` |
| M4 `launch` prints `waiting: ` | `test_wf::test_happy_path_execs_claude_in_repo` |
| M5 `waiting = False` | `test_wf::test_tab_indented_milestone` |
| M5b note box marker ignored (`owed = owed_text(box)`) | `test_run::test_refusals`, `test_run::test_next_box_inside_feature`, `test_queue::test_rules` |
| M6 run.py marker warnings dropped | `test_queue::test_unmarked_waits_on_warns` |
| M7 `NEAR_OWED` also matches `after` | `test_wf::test_words_never_wait` |

Note: run.py `classify` still has an `if nb.waiting: return "waiting", nb.note` branch after the `nb.owed` check; with AC-1 it can no longer be reached. Harmless, left as is.
