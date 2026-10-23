# 03_judge

Judges each difference against the PR's diff: a consequence of the move, or a possible behavior change.

Model: sonnet high

`<run>` below is `<repo>/.workflow/runs/restructure-check/<run id>`; the prompt gives you both values and the
base and head refs.

## Inputs
- `<run>/02_diff/output/differences.md`: the real differences
- `git -C <repo> diff <base>...<head>`: the PR change (use `--stat` first, then read per file as needed)

## Process
1. For each difference, find the changed paths in the diff that explain it.
2. Mark it "expected from the move" and name the moved path (`old -> new`), or "needs a look" and name a `file:line`
   or the command to run. When unsure, it needs a look.
3. Write the report with the verdict line first: `nothing broke` only when every difference is expected, else
   `needs a look: <n> difference(s)`.
4. Do not write files (a workflow subagent's Write is refused for a report file). Return the whole report text in the
   schema's `report` field; the starter writes it to the path below.

## Outputs
- `<run>/03_judge/output/report.md`, written by the starter from the `report` field: verdict line, then each difference with its mark and evidence

## Human check
Every "needs a look" names a file:line or a command.

## Do NOT load
- The full captures in `01_capture`
- Repo files the diff does not touch, unless a "needs a look" needs one cited line
