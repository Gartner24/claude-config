# 02_diff

Compares the two captures and lists every real difference, after removing noise by named rules.

Model: sonnet medium

`<run>` below is `<repo>/.workflow/runs/restructure-check/<run id>`; the prompt gives you both values.

## Inputs
- `<run>/01_capture/output/base/`: the base side captures
- `<run>/01_capture/output/head/`: the head side captures

## Process
1. List the files of both sides. A file on one side only is a difference (a missing command is itself a difference).
2. Normalize noise in both sides before comparing, and number each rule you apply: temp and worktree paths
   (`<run>/01_capture/<side>/tree` to `<TREE>`), timings and durations, run ids, commit shas, dates. Add no other rule.
3. Diff each pair. For every difference left, write one entry with both sides quoted (the differing lines, with a few
   lines of context).
4. List at the end every normalization rule and how many lines it removed.
5. Write the outputs below, then return the schema the prompt names.

## Outputs
- `<run>/02_diff/output/differences.md`: one entry per real difference (command slug, base quote, head quote), then the
  normalization rules with counts

## Human check
No difference was dismissed as noise without the rule that removed it.

## Do NOT load
- Any repo file; only the two capture folders
- Stage 03 files
