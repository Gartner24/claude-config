# 0081. Profiles: rationale

## Context
claude-config is one owner's setup: `install.sh` copies one fixed set of files into `~/.claude`, and `sync.sh` copies live edits back ("live wins", invariant 1). The owner wants to share it with a partner who makes videos and sometimes builds tools. The partner needs the same workflow and quality bar, fewer owner only rules, and must not be able to break the engineering core. Both will commit to the same repo, the partner on a Mac.

With "live wins", the partner's sync would copy his live files over the owner's in the repo. There is also nothing that stops Claude, in his session, from editing core hooks or rules.

## Options considered

### Option 1: Repo built profiles with an overwrite check
Profile files in the repo; install builds `~/.claude` from core plus profile; the repo wins; a pre-install check lists live changes it would overwrite.
**Pros**: one owner per file, so D8 (updates touch only your profile) and D14 (custom copies) are simple; no cross person overwrites.
**Cons**: direct live edits stop sticking without a sync.

### Option 2: Live wins, sync splits by profile
Keep editing `~/.claude`; sync works out which profile each change belongs to.
**Pros**: today's habit unchanged.
**Cons**: sync must guess ownership of every change; a wrong guess changes the other person's profile.

### Option 3: A fork per person
Each person keeps a fork and pulls the core.
**Pros**: full isolation.
**Cons**: against D9 and D12 (one shared repo, a standard for anyone); core fixes need merging both ways.

## Rationale
The forces are two people in one repo (D12), a standard for anyone (D9), and updates that touch only your own profile (D8). Only a single source per file satisfies all three without guessing; Option 1 gives that, and your answer adds the safety net: install checks and lists what it would overwrite before it does. The lock is two layers by your choice: the hook saves wasted work in Claude, GitHub code owners are the real gate. `design-gate` stays locked because both profiles depend on it for the same quality bar (D4). Custom profiles apply only to non owner profiles, so your `engineer` flow is unchanged. `creator` waits for your partner's configs instead of an invented starter rule (your answer), so it begins as `engineer` plus the lock.

## Your answers (2026-10-27)
1. Source: repo wins; if live would be overwritten, check what changes or goes missing, then fix it or ask.
2. Names: `engineer` and `creator`.
3. Lock: hook and GitHub.
4. Editable: design and content skills, the taste patches, own custom profiles; not `design-gate`.
5. Custom profiles: non owner profiles only.
6. Switch: `/claude-config profile <name>`, band shows the active profile.
7. Fewer questions: wait for the partner's configs.
8. Data model: as shown.
9. Cross check (Sonnet, 18 gaps): apply all recommended fixes; custom profiles are created automatically by Claude (D14), which the first draft had weakened to a manual command.
