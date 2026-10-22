# Brief 2026-10-21: retire the runner, handoff toggle, one status display

## Agreed so far, do not ask again
- The owner retires the `wf` runner: too slow, hard to talk to, buggy. All work happens in chat from now on.
- Useful runner features may move into chat (all chats, some chats, or dropped). The owner decides per feature from a list with a recommendation each.
- Uninstall means the LIVE install goes (links, copies, hooks, status line, services). The repo code under runner/ stays until the per-feature decisions are made. Run state in ~/.local/state/wf stays (history). Anything removed goes through `gio trash`, never rm.
- Auto handoff at 200k stays, plus: an on/off switch per chat, and the state (on/off) shown in the status display.
- Make the handoff from chat to chat faster without losing quality (owner's point 2.3).
- One status display only: the wf-dash band. The bottom status line (`wf auto bar`, a port of jjstack's statusline.sh) goes for good, and jjstack must not be able to put its own bar back (its `bin/jjstack-statusline-install`, run by jjstack `setup` and `jjstack-upgrade`, installs silently when the statusLine slot is empty).
- The band must show in EVERY chat, not only chats where the mod happens to be loaded.
- The band must keep working with no `wf` installed (it reads `wf status --json` today).
- Agents: max effort high, min low; model by task (haiku lookup, sonnet edits/review, opus design/hard work).
- Later (after these land): restructure claude-config to the icm-architect folder layout (github.com/RinDig/icm-architect). Not part of this batch.
- 2026-10-22: the owner says yes to trashing ~/.config/wf, removing the wf rule text and the auto skill, but only after the parts that are real features are named and kept (list below).
- 2026-10-22: auto handoff is to be stopped until a handoff loss audit is done and fixed; a lost report after a handoff is the failure that started it (this file and retire-runner-features.md were only in a temp scratchpad).

## Runner feature list
Full table with a recommendation per feature: [retire-runner-features.md](retire-runner-features.md). Owner decision per feature still pending.

## Before trashing ~/.config/wf, wf rule text and the auto skill (owner confirmation pending)
- ~/.config/wf/allowed.json (trusted repo list), ntfy.json and telegram.json (phone channel, holds a bot token): only the runner reads them (features 6, 47). Nothing to keep. Revoke the Telegram bot token in BotFather after trashing.
- claude-home/skills/auto: starts and watches the runner (feature 52). Drop. Keep one behavior as a rule: with the owner away or saying "do it yourself", Claude runs steps and answers clear questions itself instead of handing `!` commands (memories do-it-yourself-in-auto, finish-when-away).
- rules/runner-handoff.md: drop the runner parts (Autopilot, `wf allow`, "type wf", `wf queue`). Keep: after /architect accepts a spec, run the next feature's /architect while any still needs a decision (batch first), then build in chat with agents.
- rules/scope-contract.md: keep the scope format (header, tags, boxes, next box rule). Drop `Autopilot`, the auto tag and the four live step shapes; the live box becomes feature 54 (Claude runs it after one yes, then a drift check before ticking).
- rules/check-gates.md, plain-questions.md, standing-answers.md, skill-map.md, branch-pr.md, cheap-worker.md: keep the rules, delete only their "under wf run" sentences and the wf column; branch-pr loses "Opting a repo in" and the runner merge sentence (feature 38 keeps the green checklist for Claude's own merges).
- ~/.claude/private/pr.json: read only by the runner (features 38, 42, 43, 46). Keep until feature 38 is decided; it records which repos Claude may merge in.

## Owner answers 2026-10-22 (do not ask again)
Runner features: every feature not named below follows the recommendation in retire-runner-features.md.
- 9 (caps): drop the code, but keep "finish it yourself": the owner can say "do these features": Claude writes each /scope row, runs the /architect questions for all of them, then sends parallel agents to build them.
- 10, 18, 28 and every other "some chats" feature: the owner does not want features that never reach a chat that later needs them. Make them all-chats rules that switch on by condition (repo has an app, repo has UI, owner says "I am leaving"), not by which chat it is.
- 11 (questions): plain-questions works badly; the owner still gets lost. Run /deep-research on how the owner can understand each question without getting lost; drop "Learn this first" and find an approach where the owner never has to click to learn.
- 31 (parallel agents): yes, with the runner's care: model and effort chosen per agent, and start gates (32) so many agents do not eat all memory and usage at once.
Cleanup: yes to trashing ~/.config/wf, the auto skill and the runner sentences in rules, keeping the parts listed above.
Handoff audit fixes:
- 1 (save everything shown): NO. Too much context, and it would carry bad prompts and mistakes. Look for a real "brain" (memory) approach, maybe a repo from github.com/RinDig, or do not do it.
- 2, 3, 4, 6, 7: yes.
- 5 (wait for helpers): yes, but never interrupt a long agent. Find out whether a running agent can pass to the next chat; if one is interrupted, resume it from where it left off (same agent session), or give agents their own rollover.
- Open question: when are saved temporary files removed, and how are they tracked?
Process: stay automatic. The owner wants to be asked only to explain or architect an idea, or for real decisions Claude judges they must make. No "allow this" questions: the owner will allow every permission Claude asks for.
Workflow: everything follows the JSM agentic engineering course (jsmastery.com/course/agentic-engineering-course), its skills (scope, audit, architect, develop, check, test, document, sync, debug), automatic and better. Check nothing important from the course is missing; check where briefs come from, whether many briefs is bad, and when a brief is deleted.
Decisions 2026-10-22 (second chat):
- Allow rules: yes; added in one owner-run script (apply-decisions.py) because Claude may not grant itself permissions.
- Handoff line: 250k in coding chats, off in plain talk chats (off-by-condition is still to build; 250k set globally for now via AUTO_HANDOFF_TOKENS).
- Data model: the owner approves every data model in /architect; Claude still self-accepts the rest of a spec.
- Agent survival: the two research agents running at the automatic handoff survived the clear and reported into the new chat (first live data point).
- Temp files: router + leaves design from handoff-brain-research.md; open items never auto-deleted, resolved items archived then removed after 14 days or when the feature closes.
- Questions: replace plain-questions.md with the format in question-format-research.md (no Learn this first).
- Briefs: lifecycle from jsm-course-check.md section 3.
- Gated course lessons: deep research on public discussion running (2026-10-22).

## Promised work, do not drop (2026-10-22)
Each becomes a /scope row, then /architect, then parallel agents.
From the course check (jsm-course-check.md):
- [ ] Trim the always-loaded context: one copy of each rule, skill-only rules read on demand, shorter MEMORY.md index.
- [ ] Owner approves every data model (rule edit in apply-decisions.py, owner runs it).
- [ ] Write down why our second review runs on Claude; optional other-model pass on risk paths.
- [ ] After /architect accepts a spec, build in a fresh chat.
- [ ] Brief lifecycle: one brief per feature, /sync checks agreed items landed then deletes it, warns on uncited or broken brief links; split tool-review-2026-10.md by row.
From the brain research (handoff-brain-research.md):
- [ ] Handoff keeps only four kinds (open questions, deliverables still needed, agreed decisions, live state); a writer helper quotes the source of each item or drops it.
- [ ] Index file per feature in a repo, ~/.claude/state/ outside a repo, never /tmp; new chat reads the index only.
- [ ] Tracking: every item has status and date; open items never auto-deleted and show their age; done items archived, removed after 14 days or when the feature closes.
From the question research (question-format-research.md):
- [ ] Replace plain-questions.md with the DECISION / IDEA / OPTIONS / I PICK format; drop Learn this first; rewrite the panel hook to check the explanation exists instead of banning words.
From the runner features:
- [ ] Every some-chats feature becomes an all-chats rule that switches on by condition (app, UI, owner leaving).
From the handoff audit: fixes 2, 3, 4, 5, 6, 7, plus handoff off in plain talk chats.
From the gated course research (jsm-course-gated-research.md):
- [ ] Reviews use another AI provider too (codex skill is installed), not only Claude.
- [ ] Stop-and-reset rule: after 2 failed fixes, stop, start fresh with what was learned.
- [ ] Refuse a Claude co-author trailer in every repo with a commit-msg hook; 3 installed JSM skill files still ask for it (develop/flow/git.md:27, test/SKILL.md:187, sync/agent-prompt.md:177).
- Handoff line stays 250k (owner, 2026-10-22, over the course's ~150k). Do not ask again.

