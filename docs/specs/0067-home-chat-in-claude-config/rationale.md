# 0067. Rationale

## Context

Claude Code files chats and auto memory under `~/.claude/projects/<start folder with / and . as ->`. The owner's setup and runner chat starts in `~/.claude`, so its 90 chats and 52 memory notes sit in `-home-santiago--claude`. The owner asked on 2026-10-02 whether to work from claude-config, was told to stay, and on 2026-10-20 asked to move all sessions and memory to claude-config and keep working there. It reached personal plan item 9 but never claude-config's plan (now scope row 86).

claude-config already has two chat folders, one per path name (`~/claude-config` is a symlink to `~/dotfiles/claude-config`): 424 and 436 chats, all 424 shared names byte for byte identical, and identical 37 note memory folders (checked 2026-10-20). Claude Code names the folder after the real path (probe P6), so the dotfiles named folder is the live one and the other is an older copy. The three runner rules sit in `~/.claude/.claude/CLAUDE.md` (spec 0035 AC-5) and 59 command approvals in `~/.claude/.claude/settings.local.json`. The repo is public, so private files must stay out of git.

Moving files a running chat writes to can corrupt them, and the chat doing the planning lives in the folder being moved.

## Options considered

### Option 1: Merge into the claude-config folder and link the old names (chosen)
Pros: one history and one memory under every name; a habit start in `~/.claude` loses nothing. Cons: needs Claude Code to follow a symlinked folder (probed, passes); one manual run.

### Option 2: Share memory through a link, leave chats where they are
Pros: no chat files move. Cons: `/resume` in `~/claude-config` misses this year's chats, which the owner wants moved.

### Option 3: Copy memory once, start chats fresh
Pros: no links, no probe. Cons: two memories drift apart; old chats only reachable from `~/.claude`.

## Rationale

The owner asked for the whole move, not a split, so Option 1 is the only one that meets the scope row's Done when. Linking instead of leaving the old folders empty means a script, hook, or habit that still starts in `~/.claude` (the wf-handoff mod, the rollover slot) keeps finding the same memory and slots. Running it by hand with Claude closed is the only way to avoid the moving chat writing into its own moved file, and the backup makes every step undoable.

## References

**Project sources**: spec 0035 AC-5; personal plan item 9; scope row 86; brief `docs/briefs/tool-review-2026-10.md` E6.
