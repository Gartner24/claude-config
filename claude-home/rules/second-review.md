# Second review by claude-fb (beats skill text)

- Applies when a review covers a risky change: auth, permissions, security, sandbox, secrets, deletion, payments, migrations. It adds to the paid reviewer and stays when one is added later; it never replaces it.
- Run `git diff <base>...HEAD | fb-ask review` (add `--local` for work or client repos; see `rules/cheap-worker.md` for its limits).
- It is advisory and never edits code. Check each finding against the code, keep only the confirmed ones (with `file:line`), drop the rest.
- Say in the report which findings came from the second pass, and how many were dropped.
- Never block on it: exit 3 or 4, or empty output, means skip it and say so in the report.
