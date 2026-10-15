# 0048. Probes

## P1 three way merge (2026-10-15, git 2.56.0): pass
Files: base `a b c d e`, mine changes line 2, theirs_clean changes line 5, theirs_conflict changes line 2.
- `git merge-file -p mine base theirs_clean` exit 0, output keeps both edits (`B-mine`, `E-up`).
- `git merge-file -p mine base theirs_conflict` exit 1, output has `<<<<<<< mine` / `=======` / `>>>>>>>` markers around line 2.

## P2 fetch by commit (2026-10-15): pass
- `git ls-remote https://github.com/greensock/gsap-skills.git HEAD` gave `aed9cfd3277740755f6bfc1155c7aa645403b760`.
- `git fetch -q --depth 1 <url> aed9cfd...` into an empty repo exit 0.
- `git show FETCH_HEAD:skills/gsap-core/SKILL.md | sha256sum` = `3887b47e...12b3`, equal to `sha256sum ~/.claude/skills/gsap-core/SKILL.md`.

## Build rerun (2026-10-15, /develop under wf run)
- P1: rerun, pass. `git merge-file -p mine base theirs_clean` exit 0 with `B-mine` and `E-up`; `theirs_conflict` exit 1 with `<<<<<<< mine`, `||||||| base`, `=======`, `>>>>>>> theirs_conflict` around line 2 (git 2.56.0).
- P2 (2026-10-15, docs slice session): still not rerun inside a call, the sandbox still denies github.com. The manifest commit `1bb9e93` was built with network outside the sandbox (its clones sit in `~/.cache/claude-config/`), which fetched every traced source; a by commit `git fetch --depth 1` is first exercised live by `update --apply` (migrate.md).
- P2: not run. The build session's sandbox denies github.com (`deny network-outbound github.com:22 (host is on the deny list)` on `git ls-remote https://github.com/greensock/gsap-skills.git HEAD`). Rerun it in a session with network before the manifest pin walk (build plan slice 3) and `update` (slice 4).
