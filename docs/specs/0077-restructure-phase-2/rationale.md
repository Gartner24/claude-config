# 0077 rationale

## Context
Phase 1 (spec 0072) built the whole tree icm-architect proposed for this repo (`docs/briefs/icm-research.md` step 5), which kept the held paths in place. The blind review of 2026-10-22 (`docs/reviews/blind-setup-review-2026-10-22.md`) scored the setup 5/10, mainly for about 13k tokens of rules loaded into every chat. The owner asked to finish the restructure today, including moving the held folders after the rest.

## Options considered
- **Held folders.** Keep all (ICM's own pick); move the movable ones into `tools/` (chosen, owner: "after we finish we move held folders too"); also rename `claude-home/`. `docs/specs/` and `docs/scope/` cannot move: the downloaded workflow skills hardcode them and are overwritten on every pull.
- **Old paths.** Clean break (chosen) or links for two weeks. Links would hide the missed referrers restructure-check exists to find.
- **Context cut.** Move rules into skills (chosen); compress and keep all loaded; leave it. ICM: an entry file under about 60 lines that only routes, 2k to 8k tokens per step, one home per fact.
- **How a moved rule loads.** A hook at skill start (chosen) or path scoped rules. Workflow rules follow skills, not file paths, and the downloaded skills cannot hold them.
- **Nudges.** Drop the per-message reminder, keep chat-start `/scope` and the Stop hook (chosen); keep both; drop both.

## Rationale
The cut is where the measured cost is. The tools move is the owner's call; it is done last, after the behavior PR, so restructure-check can show each PR's differences separately. The `~/.claude` map check found that past chats did edit `~/.claude` directly, also from work, freelance and university folders (37 transcripts touch its rules, hooks, skills or settings), so by the owner's earlier rule only the smallest pointer file is added.

## References
- `docs/briefs/icm-research.md` (ICM invariants, step 5 tree)
- `docs/reviews/blind-setup-review-2026-10-22.md`
- Owner answers in chat, 2026-10-22 (held folders, layout, old paths, context cut, nudges, rule loading)
