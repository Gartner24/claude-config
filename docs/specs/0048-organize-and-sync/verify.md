# 0048. Probes

## P1 three way merge (2026-10-15, git 2.56.0): pass
Files: base `a b c d e`, mine changes line 2, theirs_clean changes line 5, theirs_conflict changes line 2.
- `git merge-file -p mine base theirs_clean` exit 0, output keeps both edits (`B-mine`, `E-up`).
- `git merge-file -p mine base theirs_conflict` exit 1, output has `<<<<<<< mine` / `=======` / `>>>>>>>` markers around line 2.

## P2 fetch by commit (2026-10-15): pass
- `git ls-remote https://github.com/greensock/gsap-skills.git HEAD` gave `aed9cfd3277740755f6bfc1155c7aa645403b760`.
- `git fetch -q --depth 1 <url> aed9cfd...` into an empty repo exit 0.
- `git show FETCH_HEAD:skills/gsap-core/SKILL.md | sha256sum` = `3887b47e...12b3`, equal to `sha256sum ~/.claude/skills/gsap-core/SKILL.md`.
