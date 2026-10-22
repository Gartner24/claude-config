# Skills, agents and the generated skills guide

## What it is
Own skills and commands (linked live), vendored agents, the downloaded skills named in the manifest, and `docs/guides/SKILLS.md`, which is generated.

## Where
- `claude-home/skills/`, `claude-home/commands/`: linked kind, repo wins.
- `claude-home/agents/`: copied kind, mostly vendored.
- `config/manifest.json`, `config/routing.md`, `scripts/skill-keep.txt`.
- `scripts/skill-keep.py`, `scripts/skill-scan.py`, `scripts/check-routing.py`, `scripts/gen-agent-index.py`.

## Rules
- Do not edit vendored trees: `claude-home/agents/` (27 of 31 from ECC), `claude-home/rules/ecc/` (except the 7 `index.md` and the local additions in `common/code-review.md`, `common/testing.md`), `claude-home/skills/anti-ai-writing/`. Provenance lives in `docs/NOTICE.md`; update it when adding an authored or redistributed path. Its `manifest:start` block is written by `bin/claude-config.py build`.
- `docs/guides/SKILLS.md` is generated: edit `config/manifest.json`, `config/routing.md` or the front matter, then `python3 bin/claude-config.py docs` (regenerates it after touching any claude-home skill or command front matter too). `tests/test_layout.py` fails on a stale copy.
- Only skills in `scripts/skill-keep.txt` keep their description; the others go name-only in `~/.claude/settings.json` (spec 0050). `python3 scripts/skill-keep.py --dry-run` previews; without `--dry-run` it writes, then run `bin/sync.sh` right away or `bin/install.sh` undoes it. Tests: `tests/test_skill_keep.py`.
- `skill-scan [static|llm|both] [path ...] [--accept]` runs skillspector over every skill and plugin and reports only new HIGH/CRITICAL against the baseline (spec 0054). A run with no path skips the trusted packs (gstack, jjstack, ui-ux-pro-max) and prints `skipped (trusted):`; an explicit path or `--against` still scans them. Reports and baseline are in `~/.claude/state/skillspector/` (the sandbox cannot write it, run with `!`); `update --apply` runs `--against`. Tests: `tests/test_skill_scan.py`.
- `python3 scripts/check-routing.py` after editing `config/routing.md` or a skill's triggers; `python3 scripts/gen-agent-index.py --check` after touching `claude-home/agents/` (drop `--check` to regenerate).

## Also moves
- [install](install.md): the manifest drives downloaded skills.
- [specs](specs.md): a skill's behavior is governed by its spec's `**Paths:**`.
