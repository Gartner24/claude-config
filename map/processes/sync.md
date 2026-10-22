# Sync

## When
Before every commit that touches a copied file, and when comparing the repo with `~/.claude`.

## Steps
1. `bin/sync.sh`: `~/.claude` to repo; run before every commit, then `git diff`.
2. `python3 bin/claude-config.py drift`: exits 1 when the repo and `~/.claude` differ.
3. `python3 bin/claude-config.py update --plan` then `update --apply <entry>`: spec 0048, behind the `/claude-config` skill. `update` never asks, the skill asks per entry. Tests: `tests/test_claude_config.py`.
4. `python3 bin/claude-config.py docs`: regenerate `docs/guides/SKILLS.md` ([skills](../objects/skills.md)).

## Done when
- `drift` exits 0.

## Gotchas
- `bin/claude-config.py build` and `update` fetch from GitHub; a sandboxed session is denied github.com, so run them yourself with `!`. Clones are cached in `~/.cache/claude-config/`. `update --plan` takes about 25 minutes: run it in the background.
