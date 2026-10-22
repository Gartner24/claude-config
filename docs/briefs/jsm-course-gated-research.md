# JSM course: what the paid lessons teach (research, 2026-10-22)

Research agent report. No paid lesson seen in full. Sources: official one-line summaries of every lesson (course page data), the free lesson "The Agent Loop" (8 free lessons, not 7), Adrian's blog posts on jsmastery.com/blogs, his launch thread on X (2026-09-23), the skills repo (main still 43b69e4; branch `fix/behavior` 2026-08-09 adds the author's audit `docs/current-isssue.md` and 15 tickets), the older repo `jsm-agent-skill` (`/remember`, `/recover`). Reddit, Hacker News, Dev.to: nothing. Pirate copies exist and were skipped.

## 1. What the gated lessons teach
- The Agent Loop (free): read, decide, act, observe; one bad early read steers every later loop; control what it reads, how clearly it decides, how closely you check; catch drift "in loop 3, not loop 30".
- Clearing vs. Compacting: clear "the moment you change tasks"; compact only on one task grown long; rot starts long before the window is full; progress lives in files and commits, not scrollback; "clear more often than feels comfortable". Topic switching in one session causes repetition and forgetting.
- CLAUDE.md & AGENTS.md: How They Load: three types of context (always-on, on-demand, the code); a challenge "trimming a bloated context setup" into a lightweight instructions file.
- /sync: a stale spec is worse than none; make reconciling a regular loop step that reads git history, not memory. How it is automated is not public.
- Why a Second Mind Matters: self-grading fails; demo uses a separate non-authoring model; challenge "Three Reviewers, One Feature": author model, second model, alternative provider model. X principle 4: never let a model review its own work. Blog: different model, fresh eyes; match the proof to the stakes.
- Recover a Broken Session: halt loops, inspect false assumptions, shrink prompts, rewind checkpoints, clear or compact. `/recover`: sort into isolated bug, polluted session, or wrong foundation; after two failed root-cause guesses re-sort; polluted session -> "Reset Note" (building what, what went wrong, what to avoid, where to restart), end the session, start fresh.
- `/remember`: memory.md holds only the latest state, asks before overwriting, never stores what code or context files hold, never secrets; on restore shows a 4-line "where we are".
- Other: deep model tiers decide, fast tiers execute; subagents for isolated tasks; Final Pro Tip: architect many specs upfront, batch-build in one automated session; "Make It Lie to You": break the app to test false passes; specs keep build decisions apart from human reasoning.

## 2. What we miss or contradict, most important first
1. Reviews never use a different AI provider (course says it four ways). Change: one review pass from another provider on risk paths and GA (a `codex` skill is installed); confirm the /architect cross check really uses a different model.
2. No "stop and reset" rule. Change: after two failed fixes for the same bug, stop, write a reset note into the feature's brief, hand off to a fresh chat.
3. Always-on context still large (confirms jsm-course-check.md finding 1; author's audit: past a volume, more prose stops buying compliance; /architect alone ~25k tokens).
4. Handoff too late and topics mixed. Change: hand off at about 150k; treat a switch to an unrelated repo or task as a clear point, even in the conductor chat. (Conflicts with the owner's 250k decision: ask the owner.)
5. Installed JSM skills still ask for a Claude co-author line: `~/.claude/skills/develop/flow/git.md:27`, `test/SKILL.md:187`, `sync/agent-prompt.md:177`. Only rules/no-attribution.md stops it. Change: a local commit-msg hook that refuses the trailer in every repo.
6. Resume does not ask to confirm (by design). Optional: print a 4-line "where we are" first.

Already matching: /sync in the chain, stale spec warnings, batch specs first, verify steps that can fail, small subagents for lookups.

## 3. Changes to jsm-course-check.md
- 8 free lessons, not 7.
- Finding 2 partly fixed (owner approves data models, 2026-10-22).
- Finding 3 (second review on another model) moves to first place.
- Finding 4 partly wrong: we already roll over after /architect; the real gaps are no clear after /scope, the handoff line, and mixed topics in the conductor chat.
- Upstream `fix/behavior` tickets that affect us: 2 (/check lacks Edit and AskUserQuestion), 4 (README order diagram wrong), 5 (hardcoded co-author line), 13 ("done" fires before review at GA), 15 (no behavior tests).
- Briefs: JSM tickets stand alone and memory.md keeps only latest state; both back "one brief per feature, delete when done".

## 4. Nothing found beyond the summary
Cheat sheet contents; What the Agent Sees, How Agents Read Your Codebase, Context Windows, Tokens; Reading a Session That Went Bad; Module 4 (MCP, subagents) beyond summaries; Module 6 (skills); Module 7; Nine Skills, Reading a Spec, demos of /architect, /develop, /audit; Modules 9, 11, 12; The Loop You'll Actually Run; every quiz. Nothing public on parallel agents.
