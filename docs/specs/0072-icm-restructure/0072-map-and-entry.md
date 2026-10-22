# 0072b. Map cards, CLAUDE.md entry, AGENTS.md link

## Summary
Second PR of phase 1. It writes the `map/` cards, turns `CLAUDE.md` into the short entry file, and makes `AGENTS.md` a link to it that a commit cannot break. Branch `feat/0072-map-and-entry`, stacked on 0072a only while 0072a is unmerged.

## Scope
Acceptance criteria AC-6 to AC-10 of [index.md](index.md); build plan tasks 5 to 7 and 9.

## Where today's AGENTS.md lines go (owner, 2026-10-22)
| Today | New home |
|---|---|
| Commands list | `map/processes/install.md`, `sync.md`, `checks.md`; the 4 most used stay in `CLAUDE.md` |
| Copied vs linked vs mods vs downloaded skills | `map/objects/install.md` |
| Public repo, private names, no attribution, ASCII, commit format | `CLAUDE.md` |
| Vendored trees, generated SKILLS.md, spec `**Paths:**` | `map/objects/skills.md`, `map/objects/specs.md` |
| Gotchas | the card of the part each is about |
| Standing answers, agent skills, context files | `CLAUDE.md` |

## Notes for the build
- Probe result (verify.md): the Edit and Write tools refuse a symlink and name its target, so they keep the link; `sed -i` replaces the link with a normal file. That is why AC-9 (commit refusal) is required, not optional.
- Rationale: one real file means a skill that edits `AGENTS.md` with the Edit or Write tool is refused with `CLAUDE.md` named as the target, and a shell edit that replaces the link is stopped at commit; drift cannot reach git.
