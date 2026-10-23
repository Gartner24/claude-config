# Scope (the plan)

## What it is
The plan: feature rows with boxes under `docs/scope/`. The next unticked box is the next step.

## Where
- `docs/scope/scope.md`: the plan file.
- `claude-home/rules-on-demand/scope-contract.md`: the format (header, tags, boxes, next box rule).
- `claude-home/mods/chip-dash/plan.py`: the plan pane parser.

## Rules
- The middle dot `·` is allowed in repo markdown despite the ASCII rule: it is the scope tag separator (`claude-home/rules-on-demand/scope-contract.md`) that the plan parser reads, and `tools/scripts/asciify.py` keeps it.
- Repo work lives only in `docs/scope/`; no TODO or progress files.
- Scope rows that link a moved file get the new path in the same change.

## Also moves
- [mods](mods.md): `plan.py` copies the parser.
- [specs](specs.md): rows link specs.
