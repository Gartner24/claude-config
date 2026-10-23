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

## Open, next actions (updated 2026-10-22 late)
Merged since the evening update: #186 (review-fix escapes `</` in data blocks), #188 (row 104: a resumed chat follows the folder's on or off both ways). Rows 95, 96, 104 closed to done.md; table rows 95 to 104 added (owner kept a background /scope session's edits; rows 85 and 99 moved back because they still have open boxes). Owner restarted Claude Code after #185.
Owner's chosen order (2026-10-22, "continue with your recommendations"):
1. Row 100 (`/build-features`, spec 0074): run probes P2 and P3 first (see the spec's verify.md); a FAIL goes back to `/architect`, no code before both pass. Then build in a worktree agent, then verify, test, PR, self merge checklist.
2. New row "Assertion Guardian guard gaps" (see "For /architect later"): enroll with `/scope`, then `/architect` with the owner (risk path: self approval of `/allow-test-change`, MultiEdit, symlinks, `ln`, `git apply`).
3. Owner answers 2026-10-22: scan dotfiles before pushing the 28 local commits (done in the next chat); row 89 concurrent Bash leftover left, moved to the guard gaps session; restructure-check interview right before row 97 phase 2.
4. Waiting on first real use: row 101 AC-7 and AC-8 (first `/review-fix <pr> --limit 1`, first `/workflow-builder review-fix --update`); row 103 live check (first `/rollover` then `/clear` shows `## Handoff facts`).

## Agreed so far, do not ask again (chat of 2026-10-22 late)
- Row 105 (blind review fixes): owner "Okay merge when ready". Built in PR #196 (draft, suite 156 ok, 10 mutants). Next: `/review` (risk path: permissions, settings) plus `fb-ask review` second pass, fix findings, mark ready, self merge checklist, then install live and tick the boxes.
- Permissions: "MCP and rules only" (MCP auto start off, no self edit allows, `gh pr merge` stays allowed).
- Context cut goes into row 97 phase 2 design, not its own row.
- Build-features probes: owner said "Run both now". P2 needs the owner to add one line to live `~/.claude/settings.json` (classifier refused the edit as self modification): `"subagentStatusLine": {"type": "command", "command": "/home/santiago/.claude/jobs/fd2083a4/tmp/p2-capture.sh"}` (move the capture script out of the job dir first, it is session scratch). P3: owner asked twice what it is; explained in plain words; still waiting for "A" (run in claude-config, close the draft PR after) or "B" (scratch repo, separate chat).
- Owner wants all of claude-config and ~/.claude finished today. Order agreed: row 105 merge; restructure-check interview; row 97 phase 2 `/architect` (with the context cut); guard gaps `/scope` + `/architect` (folding row 89's spec 0068 Amended line); row 89 install hook folder bug after #196 merges; row 100 after P2 and P3; `/review-fix` first real use on a real PR (rows 101 AC-8, 102).
- Doc for the owner: https://claude.ai/artifact/Y3yRvWwKuefxpDbg1A5WU7 (what was built and why, plus the blind verdict).

## Agreed in the interviews of 2026-10-22 late, do not ask again
- restructure-check: compare behavior outputs on base and PR head; stages capture (haiku), diff (sonnet), judge (sonnet high); own PRs only; details as listed in chat ("Yes, as listed"). Draft PR #200.
- Phase 2 (spec 0077): keep `docs/specs/`, `docs/scope/`, `claude-home/`; then move `bin/`, `scripts/`, `config/` into `tools/` ("after we finish we move held folders too, that way we finish today"); no compatibility links; rules move into skills, loaded by a skill start hook (probe passed, typed slash needs UserPromptSubmit); situation rules keep pointer lines; drop the per-message /scope reminder, keep chat-start /scope and the Stop hook; `~/.claude/MAP.md` pointer file (Claude does edit `~/.claude` directly).
- Guard gaps (spec 0078): approval only when typed by the owner; lock per test file.
- Row 100 built (draft PR #201). Owner answer 2026-10-22: a GA row built by /build-features gets /review once, at merge (AC-9); the build agent does not review it itself. Landing in PR #201 with a spec 0074 amendment.
- Live today: row 105 merged (#196) and installed; `Workflow` allowed; claude-config.py allows narrowed to drift, hook-files, update --plan; live MCP auto start off.

## Agreed and live, chat of 2026-10-23 early, do not ask again
- Merged and installed live (drift none): #192 (private-names gitlink), #200 (restructure-check), #201 (build-features), #205 (0077 PR A, lighter chats: always loaded text 52.7k -> 16.8k chars), #206 (0078 guard gaps), #208 (install copies chain-catch.py and live-tick.py). Docs PRs #203, #204, #207.
- Owner answers: GA rows built by /build-features get /review once, at merge. Live `~/.claude/CLAUDE.md` copied once from the repo (owner: "one time copy, but fix the risk"): checked byte equal to the pre-#205 repo copy first, backed up to `~/.claude/backups/CLAUDE.md.bak.20261023-pre205`. The three Review Rules lines stay always loaded. Guard path check: walk up to the nearest existing folder (spec 0078 AC-4 amended).
- Old live rule files: `~/.claude/backups/rules/2026-10-23/`. Old guardian mod: `~/.claude/backups/skills/assertion-guardian.20261023-pre206` (install never reapplies a changed patch to an existing edited skill; moved live aside, then `claude-config.py restore`; row 110).
- Also merged and installed live later (2026-10-23, drift none): #210 (0077 PR B, `tools/` move), #211 (destructive guard spellings), #212 (restructure-check follow-ups), #213 (install reapplies a changed patch), #214 (Assertion Guardian hidden jobs and folder changes). Rows 97 phase 2, 100, 105, 106, 107, 109, 110 closed or ticked in the docs sync; new rows 111 and 112.
- Owner said "finish by yourself" (2026-10-23, owner asleep); the installs ran under it.
- Assumed spec 0079 (row 108) is still to confirm by the owner.
- In progress: none.
- Owner boxes left: live `/architect x` fresh chat check (row 97), row 101 and 102 first real use, row 103 live rollover check.

## For /architect later (none blocks)
- Blind review findings (`docs/reviews/blind-setup-review-2026-10-22.md`, average 5/10, claims checked against the files): `enableAllProjectMcpServers: true`, `Edit(~/.claude/CLAUDE.md)` and `gh pr merge` pre-allowed; jjstack security hooks not in the repo and not checked by drift; `context-monitor.js` says 200k while `CLAUDE.md` says 250k; `block-destructive.sh` misses `${HOME}`, `$PWD`, `git reset --hard`, `git checkout -- .`; always-loaded text about 18-25k tokens. Not yet shown to the owner as a decision.
- New row "Assertion Guardian guard gaps" (security review 2026-10-22): self approval of `/allow-test-change` (check the command came from the owner), MultiEdit not checked, path and symlink tricks, `ln` and `git apply` not seen as writes; also `/allow-test-change` says "nothing is blocked" while it does approve; also concurrent Bash calls can undo each other's test additions (row 89 leftover, owner 2026-10-22: leave it as a fix, add it here).
- Row 97 phase 2 checks the `~/.claude` map: first whether Claude ever edits `~/.claude` without the repo's map; if not, drop it with one line of reasoning; if yes, only the smallest pointer file, never loaded in normal chats. `~/.claude/private/` stays live only. Nothing of quality is lost today: every behaviour file is live (owner, 2026-10-22, "lets do what you recommend"; landed in the row 97 phase 2 box).
- Dashboard: `checks failing` and `checks pending` cut at 40 columns (a label spec 0071 AC-3 spells).
- Row 101 spec choices: worktree branch names gain `-<n>`; the follows line only prints; `**Paths:**` misses four files.
- Row 91 spec choices: `close` accepts `replaced by D<n>`; detail paths are relative to the index.
- Row 89 leftover: `bin/install.sh` copies the commit hooks into a wrong folder when a global `core.hooksPath` is set.

## Gotchas learned today
- Pushes to GitHub can hang; `git -c protocol.version=0 push` got them through.
- `bin/install.sh` must not run while a live settings entry is deliberately paused: it copies the repo settings live.
- The Assertion Guardian approval only clears a block made in the main chat; repeat an agent's blocked Edit there first.
