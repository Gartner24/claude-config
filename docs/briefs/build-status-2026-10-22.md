# Build status 2026-10-22 (parallel build chat)

## Agreed so far, do not ask again
- Row 97 part a merges on its own checks; part checks count for a stacked row (owner, 2026-10-22).
- Chain-catch counts only edits since the owner's last message; a worktree agent naming a spec releases its row (spec 0070 amended).
- Auto start of `/audit` or `/scope`: keep the spec, all non-work repos (owner answered "All").
- Row 91: the writer waits for running agents; the slot keeps its Open questions section beside the memory (spec 0069 amended twice).
- PR 174's client text: rewritten and force pushed (done).
- Plan's next group key stays `t`.
- Test file edits go through the Edit tool; an Assertion Guardian block waits for the owner's `/allow-test-change`, made from the main chat.

## Merged today
#164 (row 93 dashboard Now view), #165 #167 #175 (row 97 phase 1 a, b, c), #166 #170 (row 92 skills start themselves, chain-catch fix), #169 (row 87 live tick guard), #172 (row 98 helper scripts), #173 (row 89 review leftovers), #174 (row 91 handover memory), #177 (claude-config first install fix). Docs PRs #168, #171.
All live: hooks, rules, CLAUDE.md, templates and settings entries copied; drift shows only the PreToolUse hook order in settings.json (the next `bin/sync.sh` evens it). icm-architect installed properly after #177. Mods (chip-dash, wf-handoff, assertion-guardian) load the new code after a Claude Code restart.

## Open, next actions
1. PR #176 (row 101 workflow builder): reviewed CAUTION, both fixes pushed (00ce337: no `vm`, own literal parser; items required). Merge main into it, run `python3 tests/fast.py` and `check.py --test`, merge.
2. PR #178 (row 103 manual handoff facts): pushed, not reviewed beyond a read of the diff; small (about 120 lines). Merge after #176, then pull main. Live check: the first real `/rollover` then `/clear`.
3. Row 95: its Verify and Test boxes (auto handoff off per folder, fix merged in #147) after #178.
4. Row 100 (`/build-features`, spec 0074): starts after #176 (shares `bin/claude-config.py`); probes P2 and P3 first.
5. Row 102 (review-fix, restructure-check workflows): after #176, through `/workflow-builder`; needs the owner's interview answers.
6. `/sync` close-out for rows 87, 89, 91, 92, 93, 97 (phase 1), 98: AGENTS.md (CLAUDE.md) lines, `spec-paths --spec` warnings, `· done` tags.

## For /architect later (none blocks)
- New row "Assertion Guardian guard gaps" (security review 2026-10-22): self approval of `/allow-test-change` (check the command came from the owner), MultiEdit not checked, path and symlink tricks, `ln` and `git apply` not seen as writes; also `/allow-test-change` says "nothing is blocked" while it does approve.
- Row 97 phase 2 checks the `~/.claude` map: first whether Claude ever edits `~/.claude` without the repo's map; if not, drop it with one line of reasoning; if yes, only the smallest pointer file, never loaded in normal chats. `~/.claude/private/` stays live only. Nothing of quality is lost today: every behaviour file is live (owner, 2026-10-22, "lets do what you recommend"; landed in the row 97 phase 2 box).
- Dashboard: `checks failing` and `checks pending` cut at 40 columns (a label spec 0071 AC-3 spells).
- Row 101 spec choices: worktree branch names gain `-<n>`; the follows line only prints; `**Paths:**` misses four files.
- Row 91 spec choices: `close` accepts `replaced by D<n>`; detail paths are relative to the index.
- Row 89 leftover: `bin/install.sh` copies the commit hooks into a wrong folder when a global `core.hooksPath` is set.

## Gotchas learned today
- Pushes to GitHub can hang; `git -c protocol.version=0 push` got them through.
- `bin/install.sh` must not run while a live settings entry is deliberately paused: it copies the repo settings live.
- The Assertion Guardian approval only clears a block made in the main chat; repeat an agent's blocked Edit there first.
