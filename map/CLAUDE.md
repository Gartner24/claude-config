# Map of claude-config

Open the card for the part you change; nothing else needs loading. How to walk the map and the names that collide: [CONTEXT.md](CONTEXT.md). Card format: [_meta/schema.md](_meta/schema.md).

## Objects (what exists)
| Card | Part |
|---|---|
| [install](objects/install.md) | copied, linked, downloaded and live-only files; `bin/install.sh` |
| [mods](objects/mods.md) | `wf-handoff`, `chip-dash` |
| [rules](objects/rules.md) | `claude-home/rules/`, `claude-home/rules-on-demand/`, hooks (skill rules hook), `fb-ask` |
| [skills](objects/skills.md) | skills, agents, manifest, generated SKILLS.md |
| [specs](objects/specs.md) | `docs/specs/`, `**Paths:**`, `spec-paths` |
| [scope](objects/scope.md) | `docs/scope/`, the plan format |
| [suite](objects/suite.md) | `tests/`, how tests are written |
| [runner](objects/runner.md) | `_archive/runner/`, retired `wf` |

## Processes (what you do)
| Card | When |
|---|---|
| [install](processes/install.md) | new machine, hooks refresh |
| [sync](processes/sync.md) | before a commit, drift, update |
| [checks](processes/checks.md) | self-checks and lints |
| [land a feature](processes/land-a-feature.md) | branch to merged PR |
| [handoff](processes/handoff.md) | context full, task switch |

## Effects
[effects/CONTEXT.md](effects/CONTEXT.md): what a change to one part also moves.
