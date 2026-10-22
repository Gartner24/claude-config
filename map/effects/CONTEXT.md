# Effects: a change here also moves that

| You change | Also check |
|---|---|
| A file under `claude-home/` | [install](../objects/install.md): copied files are overwritten by sync; linked ones are live at once |
| `config/manifest.json`, `config/routing.md`, a skill's front matter | `python3 bin/claude-config.py docs`, then [skills](../objects/skills.md) |
| `claude-home/agents/` | `python3 scripts/gen-agent-index.py --check` |
| `scripts/private-names.py` | rerun `bin/install.sh` so the hook copies refresh ([install process](../processes/install.md)) |
| A spec's governed files | the spec's `**Paths:**` line ([specs](../objects/specs.md)) |
| The scope format | `claude-home/mods/chip-dash/plan.py` ([mods](../objects/mods.md)) and [scope](../objects/scope.md) |
| Any moved or renamed path | `scripts/ref-check.py` snapshot and verify ([checks](../processes/checks.md)) |
| A test | [suite](../objects/suite.md), then a mutation check |
| `CLAUDE.md` | `AGENTS.md` is a symlink to it; never replace the link |
