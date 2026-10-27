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

## Amendment PR D: the partner's setup (2026-10-27)

### What arrived
The partner's zip (3,305 files, his own secret scan: 0 secrets) holds his `~/.claude` (settings, three hooks, rules, four agents, skills, memory), his private studio repo and tool folders. Compared with this repo:
- Same as ours: `anti-ai-writing`, `deep-research`, `python-reviewer`.
- Ours is newer: `watch-reels` (ours adds `batch.py`, `post.py` and the fixes of PRs 229 to 232), `block-destructive.sh` (ours 814 lines, his a 163 line older copy patched for macOS; row 119 makes ours portable).
- New: `instagram-reels-design`, `lemo-opuscar`, 13 official Remotion skills, `careful-worker`, `mechanical-worker`, `web-researcher`, `engineering.md`, `work-guard.py`, `install-guard.py`, a statusline script.
- Private by his own README: his work rules (Telegram, boss, privacy), memory, the studio repo with creator names, the tools registry.

### Options and picks
1. How creator asks less. Rule overlay (picked; you added that `/scope` and `/audit` stay, with changed behavior) vs its own `CLAUDE.md` (drifts from your fixes) vs CLAUDE.md sections switched off (new field, headings become an interface).
2. How `/scope` and `/audit` behave. Start but quiet (picked) vs offer only (plans drift) vs start only where code is (mixed folders still start).
3. Private parts. His own private layer (picked, same mechanism as yours) vs a private companion repo vs his guards made generic core hooks (kept as a follow up idea).
4. His settings. New optional `settings` profile field (picked, so any creator gets the defaults; data model approved) vs his private fragment only.
5. Model routing. Agents into core, routing rule creator only (picked) vs all creator only (needs an agents field) vs merged into `lessons.md` (grows your always loaded rules).

### Decided by the architect (recommend items)
- Remotion skills come from their upstream as pinned `downloaded` manifest entries, not copied from the zip: the manifest already does this for 21st and others, and it keeps license and updates honest.
- `engineering.md` is dropped: `lessons.md` already holds its test and review rules. Runner up: a creator rule, rejected as a duplicate.
- His statusline is not core: the band (AC-9) shows the profile; he may keep his own statusLine in his private fragment.
- Private rules keep their subfolder (`rules/work/`), pending the AC-25 probe; runner up is flattening with a prefix.
- Inside the claude-config repo the ASCII rule holds for everyone, so the overlay allows accents only outside it.

### Cross check (Sonnet, 15 gaps, 2026-10-27)
You chose "Apply all fixes". Applied: routing rule is a rewrite (his work rules are private); private rules tracked in state and skipped by sync; rules build order and name clash refusal; character check counts what loads, named fallback for the probe; profile owned settings keys recorded and removed on a switch; full settings build order; AC-3 judged at PR B plus a new engineer check (AC-26); license set MIT and Apache-2.0 only; lemo-opuscar and instagram-reels-design get manifest rows and join creator editable; private names read from named places and checked on docs and commits too; polish keeps accents outside the repo; quiet is best effort; his must keep rules mapped in a table; ponytail pinned; missing private hook warned.
