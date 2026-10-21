# 0067. Verify

## Probes before accept (run 2026-10-20, Claude Code on this machine)

| Probe | Command | Result |
|---|---|---|
| P1 memory through a linked folder | `bash docs/specs/0067-home-chat-in-claude-config/probes/link.sh` (start folder A, its projects folder a symlink to a target holding a memory note with a probe word; `claude -p` asked for the word) | pass: answered `PELICAN42` |
| P2 new chat written through the link | same script, `ls` of the target | pass: `0a99d1cd-....jsonl` appeared in the target |
| P3 resume from another folder linked to the same target | same script, `claude -p --resume <id>` started in folder B | pass: answered `PELICAN42` from the earlier chat |
| P4 `CLAUDE.local.md` loads | `bash docs/specs/0067-home-chat-in-claude-config/probes/local.sh` | pass: answered `HERON77` |
| P6 start folder that is a symlink | `bash docs/specs/0067-home-chat-in-claude-config/probes/symcwd.sh` (start `claude -p` in a symlink to a real folder) | the chat lands in the folder named after the real path; none is made for the typed name. So `~/claude-config` chats go to `-home-santiago-dotfiles-claude-config` |
| P5 existing folders | compare script (2026-10-20) | 424 shared chat names identical, 12 only in the dotfiles folder, 0 name clashes between the `~/.claude` and claude-config folders, memory folders identical |

Not probed: whether the interactive `/resume` picker lists a moved chat whose recorded start folder is `~/.claude`. Build plan step 5 checks it by hand after the move.
