# 01_sort

Sorts every confirmed finding into one group by the review-fix rule and splits the fix now findings into file groups.

Model: sonnet low

`<run>` below is `<repo>/.workflow/runs/review-fix/<run id>`; the prompt gives you both values.

## Inputs
- `<run>/input/findings.md`: the findings to sort
- `~/.claude/rules/review-fix.md`: the rule that defines the groups and the stopping point

## Process
1. Read only the cited lines of each finding. Drop a finding with no `file:line` and count it.
2. Put each remaining finding in exactly one group: fix now, ask, or never automatic (rule `review-fix.md`).
3. Group the fix now findings by file; findings in the same file stay in one group. Return each group as one item.
4. In round 2 (the prompt gives the round), a MEDIUM or lower finding is not a fix now item: list it under Leftovers. A HIGH or CRITICAL finding goes under ask.
5. Write the outputs below, then return the schema the prompt names.

## Outputs
- `<run>/01_sort/output/sorted.md`: every finding with its group, the file groups, the leftovers (round 2) and the count of dropped findings

## Human check
Every finding is in exactly one group.

## Do NOT load
- Code beyond the lines the findings cite
- The full review report
