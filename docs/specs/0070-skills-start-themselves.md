# 0070. Workflow skills start themselves, and a skipped step is caught

**Date**: 2026-10-22
**Status**: Accepted
**Paths:** `scripts/spec-paths.py`, `claude-home/hooks/chain-catch.py`, `claude-home/hooks/workflow-start.sh`, `claude-home/settings.json`, `claude-home/mods/wf-handoff/hooks/register.ts`, `claude-home/mods/wf-handoff/tests/**`, `claude-home/rules/skill-map.md`, `claude-home/rules/handoff.md`, `claude-home/CLAUDE.md`, `bin/claude-config.py`

## What you're agreeing to
- When a chat opens in a git repo, it runs `/audit` by itself if the repo has no `AGENTS.md`, then `/scope`; a chat resumed from a handover runs the handover instead, and your team repos never get the automatic `/audit`.
- When a turn ends, a hook checks your plan: if this chat changed files a spec governs and that feature's next box command never ran, the turn cannot end until it runs or the box is ticked ` · skipped` in the scope.
- When a turn ends on a failing test and `/debug` did not run, the turn cannot end until `/debug` runs (it fixes what it finds by itself) or the test passes.
- After 3 blocks in one turn the turn ends anyway and you see what is still owed. A tiny state file per chat holds only that count.

## Summary
Today the 9 workflow skills start only because rule text says so. On 2026-10-22 `/scope` never ran at chat start even though a hook printed "run /scope first", and free form builds skipped the `/develop` chain. This spec gives every skill a trigger in code: the wf-handoff mod starts `/audit` and `/scope` when a chat opens, and a Stop hook (a script Claude Code runs when the model tries to end its turn) refuses to let a turn end while a step from your scope, or a `/debug` for a red test, is owed.

## Context
- `claude-home/hooks/workflow-start.sh` (SessionStart, `startup|clear`) prints one line: no `AGENTS.md` means "/audit first", a scope folder means "run /scope". It is a reminder; the model can and did ignore it. `handover-start.sh` wins on a `/clear` with a live handover.
- The wf-handoff mod already owns `session.start`, knows whether a handover seed is coming, and runs commands with `$.command.run` (`/rollover`, `/clear`, `/resume-from-clear`). Mods run only in interactive chats (`e.isInteractive`).
- The scope contract's next box rule (`rules/scope-contract.md`): a feature's first unticked box outside `## Deferred` names its command in its first backticked span starting with `/`. A box can be ticked ` · skipped`.
- Every spec top file has a `**Paths:**` line (check gates, gate 3); `scripts/spec-paths.py` already maps changed files to the specs whose globs match them.
- Spec 0036 (missed skill detector) only watches and logs; it never starts or blocks anything. This spec does not change it.
- The vendored skills (`/debug`, `/scope`, ...) are overwritten on every pull, so any change to how a skill behaves goes into a rule, never the skill.
- The JSM course briefs (`jsm-course-check.md`, `jsm-course-gated-research.md`) give no per skill trigger and no hook; the trigger per skill is the owner's call (scope row 92).

## Requirements

**User stories**:
- As the owner, I want a chat in a repo to start with `/audit` or `/scope` without me typing it, so that work starts from the plan.
- As the owner, I want a turn that skipped a planned step or ended on a red test to be stopped, so that the chain runs even after a free form prompt.

**Acceptance criteria**:
- **AC-1** (start: audit): when an interactive chat starts in a git repo with no root `AGENTS.md`, and no handover seed is pending, the mod runs `/audit` by itself, then `/scope` (no argument) when the `/audit` turn completes (`turn.complete`, chain phase `idle`). A chat start is a `session.start` event, or an owner `/clear` seen as `session.end` with reason `clear` (no `session.start` follows a `/clear`, probe P3 in `register.ts`; build step 1 probe (d)). The start runs at most once per chat id, kept in the mod's chain file so a mod reload does not start it again. If the owner types before the queued `/scope` runs, the queued `/scope` is dropped.
- **AC-2** (start: scope): when such a chat starts in a git repo that has `AGENTS.md`, the mod runs `/scope` (no argument) by itself. Folders that are not a git repo get nothing. Bot-reviewed repos (origin under the orgs named in `~/.claude/private/work.md`, read with `git remote get-url origin`) never get the automatic `/audit`; they get `/scope` only when they have a scope folder, else the printed line. `workflow-start.sh` prints its line only where the mod does not start a skill (the mod writes `~/.claude/state/auto-handoff/<session>.started` before the hook would print, and the hook skips when it exists); a mod test and a hook self check cover it.
- **AC-3** (handover wins): a chat started with a live handover slot, or seeded by the auto handoff, never gets AC-1 or AC-2.
- **AC-4** (catch: owed box): at each turn end, `chain-catch.py` (a Stop hook) collects the files this chat changed: the transcript's `Edit`, `Write`, `MultiEdit` and `NotebookEdit` targets only. Edits made through Bash (sed, a heredoc) are not seen; that is an accepted miss. It maps them to specs through their `**Paths:**` globs with a new `spec-paths --files <path>...` mode (the same matcher `spec-paths.py` uses for its warnings), skipping specs with `**Paths:** none`, and finds each spec's feature: the scope heading block whose pointer or `Spec` line links `specs/NNNN-`, skipping features tagged `· done`, `· dropped` or `· existing`. The scope is read by the contract rule: `docs/scope/` when it exists, else `.workflow/scope/`; every `*.md` in that folder (a split scope's `index.md` plus its epic files) is read. For each such feature whose next box command was not run, it blocks the turn end with the reason `owed: <command> (row <n> <heading>)`, at most 3 lines plus `and <k> more`.
- **AC-5** (what counts as run): a box's command is its first backticked span starting with `/`; a box with no such span is never owed. The command ran when this chat's transcript has a Skill tool call, or an owner message carrying `<command-name>/<name></command-name>`, whose skill name and first argument word both match the box's (`/check verify x` needs `check` plus `verify`; `/check review` does not count). A box that is ticked in the scope is done, whichever chat ran it, so a chat resumed from a handover never owes a step the last chat finished.
- **AC-6** (release by skip, and waiting boxes): a box ticked and ending ` · skipped` is done; the next unticked box is checked instead (AC-4 again). A box ending ` · waits on you · later boxes go on` is passed over to the next box; a box ending ` · waits on you` alone is never owed and stops the scan for that feature.
- **AC-7** (catch: debug): when the last test run of the turn failed and no `/debug` ran in this chat since that run, the turn end is blocked with `owed: /debug <command>`. A test run is a Bash call in the main chat (not a subagent, not a background task) whose command contains, anywhere in its text, the repo's suite command (the `suite:` line under `## Standing answers` in `AGENTS.md`) or one of `pytest`, `npm test`, `pnpm test`, `bun test`, `go test`, `cargo test`, `claude plugin test`, `python3 -m unittest`. It failed when the tool result has `is_error` true or names a non zero exit code; a result with neither (a piped run, for example) counts as unknown and is not owed. It is released when `/debug` ran after the failure or a later run of the same command passed. A test written red on purpose is blocked until the cap (AC-9); that is an accepted cost.
- **AC-14** (docs only chats): a chat whose edits are all under `docs/` or `.workflow/` is never caught by AC-4, since spec Paths never name `docs/` (check gates, gate 3).
- **AC-15** (handoff turns pass): the catch lets the turn end when the wf-handoff chain phase is not `idle` (it reads `~/.claude/state/auto-handoff/<root>.json`, found through `<session>.root` as the mod does), and in a turn that ran `/rollover`, `/handoff`, `/save-and-clear` or `/resume-from-clear`. A test covers a gated turn ending.
- **AC-8** (debug fixes by itself): `rules/handoff.md` says `/debug` started by the catch, or by any failing test, applies its minimal fix without asking, and still stops under `rules/stop-and-reset.md` after 2 failed fixes.
- **AC-9** (cap): the hook counts blocks per turn in the state file (data model below), written to a temp file then renamed. Stops 1 to 3 of one turn are blocked; the 4th stop passes, and the hook prints `owed step not done: <owed lines>` to the owner (Stop hook `systemMessage`) and logs it. As a second guard, a stop with `stop_hook_active` true and `blocks` at 3 or more always passes. A turn starts at the last transcript entry of type `user` whose content is a string or text blocks typed by the owner: not a `tool_result`, not `isMeta`, not a hook or skill injection, not a command the mod sent. A new such entry starts a new count.
- **AC-10** (where it runs): the catch runs only in an interactive main chat: never for a subagent (`SubagentStop` is not hooked), never when `WF_RUN` or `TM_WORKER_NAME` is set, never in a headless `claude -p` run (how to tell is build plan step 1's probe), and never outside a git repo or in a repo with no `docs/scope/` or `.workflow/scope/`.
- **AC-11** (fails open): any error in `chain-catch.py` (a parse error, a missing file, a git failure) lets the turn end and writes one line to `~/.claude/state/chain-catch/errors.log`; the hook never blocks because it broke.
- **AC-12** (rules match the code): `rules/skill-map.md` gets a "Starts by" column (mod start, catch, or session) for the 9 skills, and `claude-home/CLAUDE.md` `### Route by situation` names the catch in one line.
- **AC-13** (tests): `chain-catch.py --test` covers AC-4 (an edit under a spec's Paths with the next box unrun blocks; the same after the command ran passes; a done feature passes), AC-5 (`/check review` does not release `/check verify`; a ticked box passes), AC-6 (a skipped box moves to the next one; a later boxes go on box is passed over), AC-7 (red then no debug blocks; red then green passes; no exit code passes), AC-9 (4th stop passes and reports; an injected user entry does not reset the count), AC-10 (worker env passes), AC-11 (a broken scope passes and logs), AC-14 (docs only passes) and AC-15 (a gated chain passes), each mutation checked. `spec-paths.py --test` covers `--files`. Mod tests cover AC-1 to AC-3 (the `/clear` path, once per chat across a reload, a bot-reviewed origin gets no `/audit`) with `claude plugin test claude-home/mods/wf-handoff`, and `workflow-start.sh` skips its line when the `.started` file exists.

## Decision
**Chosen**: catch plus start (owner, 2026-10-22, all panel answers):
1. A mod starts skills at chat start; a Stop hook catches skipped steps for the rest (not a real start for every skill, not stronger reminders).
2. The catch reads the scope's next box plus this chat's edits through spec Paths (not a fixed chain, not a state file the skills write).
3. A block ends when the command runs or the box is ticked ` · skipped`, with a cap of 3 blocks per turn (not once per turn, not owner only release).
4. At chat start both `/audit` (no `AGENTS.md`) and `/scope` run by themselves; bot-reviewed team repos never get the automatic `/audit` (cross check fix, owner: "Apply all twelve").
5. `/debug` is caught on a failing test, and it fixes its findings by itself (owner's note on the panel: "it should fix the findings automatically").

Trigger per skill: `/audit` and `/scope` mod start; `/architect`, `/develop`, `/check`, `/test`, `/document`, `/sync` the owed box catch (whichever is the feature's next box); `/debug` the failing test catch.

## Rationale
The reminder line already existed and failed, so only code that cannot be ignored meets the row's "Done when". Starting `/scope` and `/audit` at chat start is safe to automate because the right skill there never depends on the task; mid chat the right skill does, so the catch leaves the choice to the model and only refuses to drop a step. Reading the scope's next box means the catch owes exactly what your plan says is next, and the skip mark puts every skipped step in git where you see it. The cap keeps an unattended chat moving on a wrong block.

## Options considered
1. Start mode: **catch plus start** (picked); real start for every skill (the mod guesses intent from events and may start a wrong skill mid task); stronger reminders (today's design, failed).
2. Owed source: **scope next box plus edits** (picked); a fixed chain on any edit (many false blocks on typo fixes); a state file the skills write (vendored skills are overwritten, so only rules could make them write it).
3. Release: **run or mark skipped, cap 3** (picked); block once per turn (becomes a reminder); only the owner releases (an unattended chat stalls).
4. Chat start: **both run themselves** (picked, owner accepts that `/audit` writes `AGENTS.md` and `CLAUDE.md` into any git repo opened without one); `/scope` with `/audit` as a line; `/scope` only in own repos.
5. Debug: **catch a failing test** (picked); a reminder after two failures; rule text only.

## Feature design

**Data model** (owner approved 2026-10-22): `~/.claude/state/chain-catch/<session id>.json`, one per chat, deleted by the hook when older than 14 days.
| Field | Type | Meaning |
|---|---|---|
| `session` | text | the chat's session id (Stop hook input `session_id`) |
| `turn` | text | uuid of the owner message that started the current turn; a different one resets `blocks` |
| `blocks` | number 0 to 3 | turn ends blocked in this turn |
| `owed` | list of text | the owed lines of the last block, shown to the owner when the cap lets the turn end |

**Interface**: `chain-catch.py` reads the Stop hook JSON on stdin (`session_id`, `transcript_path`, `cwd`, `stop_hook_active`), prints `{"decision": "block", "reason": "<owed lines>"}` to block, or `{"systemMessage": "owed step not done: ..."}` at the cap, else nothing; exit 0 always. `chain-catch.py --test` runs the self checks. It is registered in `claude-home/settings.json` under `hooks.Stop` and listed in `COPIED_FILES` in `bin/claude-config.py`. Python 3 stdlib only, external commands through `subprocess` argument lists.

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| start | repo or not | `git rev-parse --show-toplevel` from the chat's cwd |
| start | `AGENTS.md` present | the file at the repo top |
| start | handover pending | the mod's own seed flag, and `jjstack-rollover-slot status` |
| start | bot-reviewed repo | `git remote get-url origin` against the orgs in `~/.claude/private/work.md` |
| start | already started | the mod's chain file for this chat id |
| catch | changed files | transcript `Edit`, `Write`, `MultiEdit`, `NotebookEdit` targets |
| catch | spec for a file | `spec-paths --files` (the `**Paths:**` globs of each spec top file) |
| catch | handoff under way | wf-handoff chain file phase |
| catch | feature for a spec | scope heading block linking `specs/NNNN-` |
| catch | owed command | the feature's next box (scope contract) |
| catch | command ran | transcript Skill calls and owner `<command-name>` tags |
| catch | test command | `AGENTS.md` `suite:` line, else the fixed list in AC-7 |
| catch | test failed | the Bash tool result's `is_error` or exit code |
| catch | turn | the uuid of the last owner message in the transcript |
| catch | interactive | build plan step 1 probe |

**Key invariants**: the catch never blocks more than 3 times per turn; it never blocks because of its own error; it never edits the scope (only the model ticks ` · skipped`).

**Critical test scenarios**: an edit to a Paths file with "Verify it" next and unrun blocks, then passes after `/check verify` (AC-4, AC-5); a skipped box passes (AC-6); red test then stop blocks, green test passes (AC-7); 4th stop passes with the report (AC-9); a worker env passes (AC-10); a scope that does not parse passes and logs (AC-11).

## Build plan
1. Probes, results in `docs/specs/0070-skills-start-themselves/verify.md`; any FAIL stops the build and goes back to `/architect`: (a) a Stop hook printing `{"decision":"block","reason":...}` makes the model continue, and `stop_hook_active` is true on the next stop; (b) what in the Stop hook input or env tells a headless `claude -p` run from an interactive one; (c) the wf-handoff mod can `$.command.run` `/scope` at `session.start` of a fresh chat, and `/scope` after the `/audit` turn ends; (d) after an owner `/clear`, `session.end` with reason `clear` lets the mod run `/scope` in the new chat. Satisfies the unknowns of **AC-1**, **AC-7**, **AC-10**.
2. `spec-paths --files` mode with its self check, then `claude-home/hooks/chain-catch.py` with `--test`, registered under `hooks.Stop`, added to `COPIED_FILES`, satisfies **AC-4** to **AC-7**, **AC-9** to **AC-11**, **AC-14**, **AC-15**, part of **AC-13**.
3. wf-handoff mod start, with mod tests, and the matching skip in `workflow-start.sh`, satisfies **AC-1** to **AC-3**, rest of **AC-13**.
4. Live rule edits (copied files, live wins): `~/.claude/rules/handoff.md` (AC-8), `~/.claude/rules/skill-map.md` and `~/.claude/CLAUDE.md` (AC-12), `~/.claude/settings.json` Stop hook (parse it after editing), then `bin/sync.sh` · waits on you if the sandbox refuses the write.

## Consequences
**Positive**: the chain runs after free form builds; a red test leads to `/debug`; every skipped step is a ` · skipped` mark in git.
**Negative / tradeoffs**: a wrong block costs up to 3 extra model turns; `/audit` writes `AGENTS.md` and `CLAUDE.md` into any git repo opened without one (team repos excepted), someone else's clone included; a test written red on purpose is blocked until the cap.
**Neutral**: an edit to a file no spec's Paths names, or made through Bash, is never caught; a test run with no exit code in its result is never caught; spec 0036's logging is unchanged.
