# Checks (self-checks and lints)

## When
After touching the part named in the comment.

## Steps
```bash
python3 tests/fast.py                                # the suite: only tests for live code
python3 scripts/ref-check.py --test                  # move checker self checks (spec 0072 AC-1)
python3 scripts/ref-check.py check map/objects/*.md  # a card cites a path that does not exist
python3 scripts/asciify.py --check                   # ASCII-only lint on repo-owned markdown
python3 scripts/private-names.py --test              # private names checker and the AGENTS.md link guard
bash claude-home/hooks/block-destructive.sh --test   # guard hook self-checks
python3 claude-home/hooks/plain-panel.py --test      # panel hook: at most 3 options, first "(Recommended)", short labels, no internal codes
bash claude-home/hooks/handover-start.sh --test      # handover on /clear hook (spec 0057); needs the real jjstack slot script
python3 claude-home/hooks/skill-rules.py --test      # skill rules hook (spec 0077 AC-4): loads rules-on-demand/ files per map.json
claude plugin test claude-home/mods/wf-handoff       # /handoff and auto handoff mod (specs 0057, 0063, 0064); `claude plugin validate` beside it
claude plugin test claude-home/mods/chip-dash        # band and panes (specs 0058 to 0060, 0064, 0065); `claude plugin validate` beside it
python3 bin/claude-config.py hook-files            # every live settings.json hook command names a file that exists
node claude-home/hooks/context-monitor.js --test     # context warning hook (spec 0037): header numbers match the code and autoCompactWindow
bash claude-home/skills/design/scripts/test-ledger.sh  # design ledger and Stop hook
node claude-home/skills/design/scripts/build-ramp.mjs --check
```
`scripts/ref-check.py`: snapshot before a move, `verify SNAP --map-from-git BASE` after.

## Done when
- Each command exits 0.

## Gotchas
- `scripts/asciify.py` has no `--help`: any flag but `--check` rewrites files. Always run `--check` first. It skips `claude-home/agents/`, `claude-home/rules/`, `anti-ai-writing` and `node_modules/`.
