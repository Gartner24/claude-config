# Brief: Assertion Guardian blocks only removed checks

## Agreed so far, do not ask again
- The owner chose on 2026-10-19 (question panel): block only removed or loosened checks, allow added ones.
- The owner will not allow it to run as is in autonomous mode: it blocks harmless edits, each needs `/allow-test-change`, and it stalled the runner twice.
- Where the change lives (owner 2026-10-20, already decided, do not ask again): keep our change and merge each author update into ours without losing our corrections, the spec 0048 `edited` entry and three way merge.
- Shell edits (owner pick 2026-10-20): run, compare, undo.
- Changed expected values (owner pick 2026-10-20): still refused.
- The mod is someone else's (github.com/ccdwyer/assertion-guardian, listed in the claude-mods index, installed at `~/.claude/skills/assertion-guardian`). A local patch is overwritten on update, so the design must say where the change lives.

## Facts for /architect
- Signals it checks are listed in the mod's README: assertions removed, test cases deleted, expected values changed, matchers loosened, vague matchers added, constant assertions added, polarity flipped, data rows removed, skips added, focus added, assertions commented out, failures swallowed, dead branches, snapshots rewritten, test files changed through the shell.
- The logic is in `hooks/analyze.ts`; the hook and the allow band are in `hooks/register.tsx`.
- Open: which of those signals count as "removed or loosened" and which count as noise; whether a changed expected value counts.
