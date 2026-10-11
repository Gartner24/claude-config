# Verify: Scope contract for the runner · spec 0003 · updated 2026-10-11
_Steps derived from spec 0003 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [ ] In a fresh session (so the new rule file loads), run `/scope` with no argument on this repo -> `docs/scope/scope.md` gains `**Source of truth:** scope` and `**Autopilot:** off` on their own lines right after the `**Workflow:**` line, above the first `##` -> AC-9, AC-10
- [ ] Run `/scope` again on this repo -> neither line is changed or duplicated -> AC-9
- [ ] In a scratch repo with a scope that has no header lines, run `/scope` through `claude -p` (as the runner will) -> the two lines are written, proving the rule loads headless. Billed run, so you start it -> AC-10
- [ ] Ask `/architect` to queue a feature for autopilot -> its heading gains `· auto`; another feature captured without asking gets no tag -> AC-9, AC-10
- [ ] Read `~/.claude/rules/scope-contract.md` -> at most 25 lines, states the header fields, no `**Repo:**`, the hub `Repos` column, `·` status tags, `· auto`, `· skipped`, the next box rule, and the `/scope` and `/architect` instructions -> AC-4, AC-6, AC-8, AC-9
- [ ] `diff ~/.claude/rules/scope-contract.md rules/scope-contract.md` is empty, and `NOTICE.md` lists it as authored -> AC-9

## Commands
- [ ] `python3 -m unittest discover -s runner/tests` -> all pass (TestHeaderContract, TestHeaderWarnings) -> AC-1, AC-2, AC-3, AC-5, AC-7
- [ ] Scratch repo with `**Autopilot:** on` and an open box: `next <repo>` -> confirm line ends `warning: unknown Autopilot value 'on', using off` -> AC-2, AC-3
- [ ] Same repo with every box ticked: `next <repo>` -> `nothing to run in <repo>` then `warning: unknown Autopilot value 'on', using off` -> AC-3
- [ ] Same repo with a box that has no command: `next <repo>` -> exits 3 with the same warning line -> AC-3
- [ ] `next --list` -> six columns, no warning text anywhere -> AC-3
- [ ] `**Autopilot:** Allowed (client signed off)` and `**Autopilot:** **allowed**` -> no warning; `**Autopilot:** allowed-ish` and `**Autopilot:**` (empty) -> the unknown warning with `'allowed-ish'` and `''` -> AC-1 (value token)
- [ ] `**Autopilot:** off` inside an HTML comment, a fenced block, a feature body, or an epic file -> ignored -> AC-1 (header lines)
- [ ] A hub (`~/projects`) with `**Autopilot:** on` added -> `next projects` shows no warning -> AC-3 (hubs skipped)
- [ ] A heading `· in-progress · auto` -> `next` shows the feature without `· auto` and the same command as without the tag -> AC-5 (display)

## Acceptance-criteria coverage
- AC-1: unit tests `test_valid_values_give_no_warning`, `test_malformed_values`, `test_comments_and_fences_ignored`, `test_header_ends_at_heading_or_box`, `test_epic_split_reads_index_only`; command steps 6 and 7
- AC-2: `test_defaults_and_duplicates`; command step 2
- AC-3: `test_warning_on_every_path`, `test_hub_header_not_checked`; command steps 2 to 5 and 8
- AC-4, AC-6, AC-8: rule file read (manual step 5)
- AC-5: `test_auto_tag_and_skipped_boxes`; command step 9
- AC-7: `test_auto_tag_and_skipped_boxes` (contract fixture)
- AC-9: manual steps 1, 2, 4, 5, 6
- AC-10: manual steps 1, 3, 4
