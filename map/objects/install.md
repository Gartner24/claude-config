# Install: how the repo reaches ~/.claude

## What it is
`bin/install.sh` ships `claude-home/` into `~/.claude` (copies and symlinks); `bin/sync.sh` pulls the live copies back. Each kind of file has one source of truth.

## Where
- `bin/install.sh`, `bin/sync.sh`, `bin/claude-config.py`: the three tools.
- `claude-home/`: everything installed, at the same relative path (a file in `claude-home/rules/` is the same file name in `~/.claude/rules/`); guides are in `docs/guides/` (spec 0035).
- `config/manifest.json`: downloaded skills and frameworks.

## Rules (one source of truth per kind)
- Copied (`claude-home/CLAUDE.md`, `claude-home/settings*.json`, `claude-home/agents/`, `claude-home/rules/`, the hand written hooks and scripts listed in `COPIED_FILES` in `bin/claude-config.py`): live wins. Edit the file in `~/.claude`, then `bin/sync.sh`; an edit made here is overwritten on the next sync.
- Linked (`claude-home/skills/`, `claude-home/commands/`): repo wins. They are symlinked into `~/.claude`, so editing here is live.
- Mods (`claude-home/mods/<name>/`): repo wins; see [mods](mods.md).
- Runner: retired, see [runner](runner.md).
- Downloaded skills (spec 0048): named in `config/manifest.json` with source, pin, license and install command, never copied; an edited one is its pin plus `config/patches/<name>.patch` (a `publish: false` or private one keeps its patch in `~/.claude/private/patches/`). Never copy a downloaded skill's files into the repo.
- Frameworks (gstack, jjstack, ECC commands, the JSM skills, plugins): their installer wins, never vendored; the manifest's `frameworks` names each.
- Private (`~/.claude/private/`): live only, never in any repo.
- Claude Code state (`projects/`, `sessions/`, `history.jsonl`, caches): Claude Code only, never synced.
- Scripts hardcode `~/.claude/skills/...` paths: they run through the symlink, not from the repo path.

## Also moves
- A moved path that `~/.claude`, `~/.local/bin` or `settings.json` points at: run `scripts/ref-check.py` ([checks](../processes/checks.md)).
- The commit hooks: [install process](../processes/install.md).

## Gotchas
- The payload copy of `~/.claude/CLAUDE.md` is `claude-home/CLAUDE.md`, which `bin/sync.sh` overwrites and `bin/install.sh` ships (spec 0035 AC-4: it used to sit at the root and load twice).
- The clone lives at `~/dotfiles/claude-config` as a submodule of dotfiles; `~/claude-config` is a link to it (spec 0035 migrate step 9). Session memory and `wf` trees are keyed by the real path, and links that leave the repo climb four levels to reach `~` (`../../../../projects/...` from `docs/scope/`).
- `live` at the top is a temporary link to `claude-home` (spec 0048 AC-15) so old `~/.claude` links keep resolving until `bin/install.sh` relinks them; it is removed in its own live step.
