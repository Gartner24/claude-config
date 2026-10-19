# 0060 verify: probes run before the build (AC-6)

Run 2026-10-17 with the throwaway `wf-probe` mod, Claude Code 2.1.302.

- [x] P6 a Pane opens beside the conversation: `/probe-pane` gave `{"isPlaced": true}` and drew at the terminal width. PASS. (Corrected by the run of 2026-10-18 below: it draws beside the conversation, and `viewport.columns` is the conversation width, not the pane width.)
- [x] P7 `$.agent.list()` returns subagents only (one general-purpose helper listed while it ran; "0 agent loops" in a session with none). The main session is not in the list, so the agents pane labels the main session itself. PASS.
- [ ] P8 stopping a background task from a mod: not run yet.
- [x] P9 `$.prompt.submit` runs as a turn: called from `$.clock.after(1500, ...)` after the `command.run` hook returned, the transcript showed "Prompt from the wf-probe plugin" and the reply "probe submit ok". PASS with that rule.

Build rule from P9: the "start the next step" action returns from its hook first and submits from `$.clock.after`, never awaited inside the hook.

## Probes P6 to P9 rerun (AC-6)

Run 2026-10-18 by a subagent, Claude Code 2.1.303, model haiku. Probe source: throwaway `probe-0060` mod in the session scratchpad (never installed; `claude plugin validate` passed, warnings: no author, "gating hook without .catch"). Session: `tmux new-session -d -s probe0060 -x 200 -y 50 -c <scratch>/p0060/cwd "claude --plugin-dir <scratch>/p0060/mod --model haiku"`, driven with `tmux send-keys`; every observation logged by the mod through `$.fs.write(path, text)` to `<scratch>/p0060/out/log.txt`. Session killed after the run; no `sleep 600` process left. Side effect outside scratch: accepting the folder-trust prompt added the scratch cwd to `~/.claude.json` (one project entry, not removed).

- [x] P6 a Pane draws: PASS for opening, with a correction on width.
  Command: `/p6` runs `$.ui.open({ id: 'probe0060', title: 'probe0060', focus: true, closeOnEscape: true, rows: 21 })`; a `ui.render` hook on `{ component: 'Pane', requestId: 'probe0060' }` draws a header and a 400-digit ruler.
  Log: `P6 ui.open resolved {"isPlaced":true}`, `P6 render viewport={"columns":31,"rows":50,"isFullscreen":true}`.
  Screen (200x50 terminal): the pane opens beside the conversation, which is squeezed to 31 columns (`Claude Code v2.1.303|`), with a close mark at the far right. The 400-digit ruler wrapped every 86 columns, though the pane area spans about 166. `rows: 21` was ignored: the pane was full height (50).
  Correction to the 2026-10-17 note ("drew at the terminal width"): `e.viewport.columns` is 31 here, the width of the narrowed conversation, not the pane and not the terminal. Text wraps at about half the pane area (86 of about 166 columns, cause not found).
  can fail: the pane not placed (`isPlaced` false) or nothing drawn beside the conversation

- [x] P7 `$.agent.list()` returns this session's agents. PASS, subagents only.
  Command: ask the model for one background general-purpose subagent and one background `Bash sleep 600`, then `/p7`.
  Log: `P7 agent.list count=1 [{"id":"adb64a871383588af","description":"Sleep 60 then reply done","type":"general-purpose","status":"running"}]`. Entry fields: `id`, `description`, `type`, `status`. The background shell (`bq189x8l1`) and the main session are not in the list.
  can fail: an empty list while a subagent ran

- [x] P8 stopping a background task from a mod works. PASS with `$.tool.call({ tool: 'TaskStop', task_id })`.
  Command: the mod reads the id from the background Bash result text (`Command running in background with ID: bq189x8l1.`, matched with `/ID:\s*([A-Za-z0-9_-]+)/`), then `/p8` calls `$.tool.call({ tool: 'TaskStop', task_id: 'bq189x8l1' })`.
  Log: `P8 TaskStop resolved {"result":{"message":"Successfully stopped task: bq189x8l1 (sleep 600)","task_id":"bq189x8l1","task_type":"local_bash","command":"sleep 600"},"text":"..."}`. `pgrep -af "^sleep 600"` before the call showed the process (pid 1495932) and after it showed none (exit 1). No permission dialog appeared (auto mode on in this session; not tested with prompts on).
  Not tested: stopping a subagent by its id.
  can fail: the call rejecting, or the `sleep 600` process still alive after it

- [x] P9 `$.prompt.submit` runs as a turn. PASS with the P9 rule.
  Command: `/p9` returns `{ text }` from its `command.run` hook and schedules `$.clock.after(1500, () => $.prompt.submit({ text: 'Reply with exactly: probe9 submit ok' }))`.
  Log: `P9 hook returning, submit scheduled`, 1.6 s later `P9 submit resolved {"text":"Reply with exactly: probe9 submit ok","origin":{"kind":"plugin","name":"probe-0060"}}`, then `turn.complete agent=- answer="probe9 submit ok"`. Screen: block "Prompt from the probe-0060 plugin ... starts this turn in the user's place".
  can fail: the submit rejected, or no turn starting from it

## Build rules learned
- `$.fs.write` takes `(path, text)` positionally, not an object.
- A helper that gets `$` must be a top-level function declaration (the validator refuses `const log = ($) => ...` inside `register`).
- Size the dashboard from its own fixed layout, never from `e.viewport.columns` (31 with a side pane open, the conversation's width); do not rely on `rows` either (ignored). Re-measure with the real design before trusting any width.
- `$.agent.list()` never shows background shells: the Agents view must keep saying so (AC-3). Stopping a shell works through `$.tool.call({ tool: 'TaskStop', task_id })`; the shell's id comes only from the Bash result text, so the mod cannot list shells to stop.
- Start-next-step: return from the hook first, submit from `$.clock.after` (unchanged).
- After Escape closes a pane, the first Enter is swallowed; in tmux driving, send Enter again.

## /check verify, 2026-10-18 (wf run): FAIL, one specced action not built

Commands
- [x] `python3 runner/wf.py plan --json` on the real machine: exit 0, 26 scopes (3 hubs, 23 repos), no worktree path and no duplicate path, row 73 `building` (its run is in `active.json`), row 46 `in review` with PR 76, row 75 `waits on you`, hub rows listed. -> AC-1
  can fail: a worktree listed as its own repo, a running feature shown as its next box's state, a hub with no rows
- [x] Scratch fixture through the real CLI (`WF_ROOTS`, `XDG_STATE_HOME` in a temp folder): every state comes out (waits on you, to publish, in review with PR 12, done, dropped, done (untagged), needs a design, ready to build, in progress), spec 0007 `Accepted`, spec 0099 `unknown`, an ESC in a spec Status line never reaches the JSON, a missing epic file is listed as a warning. -> AC-1
  can fail: a missing spec file printed blank, a local PR record read as in review, a raw escape byte in the output
- [x] `wf answer` through the real CLI: option 7 of 2 exits 2 `wrong option: 7, pick 1 to 2`; a number for a typed-answer question exits 2; an unknown id exits 1; under `WF_RUN` exits 5 `refused: user_only` and stores nothing; `ab12 1` exits 0 `answered: ab12 Yes (keyboard)` and the queue holds `Yes`; again exits 1 `already answered`; the next `wf plan` no longer lists it. -> AC-5
  can fail: an out of range number stored as the answer, a second answer overwriting the first, an unattended call answering
- [x] The mod drawn from the real `wf plan --json` (a scratch copy of the mod with a render test, `claude plugin test`): default Needs you view, all 8 filters with their groups, Builds with 3 runs and `now verify`, Agents with the background shells line, Alerts empty text. -> AC-2, AC-2a, AC-3, AC-4, AC-4a
  can fail: a filter showing another state's features, Builds missing a running run
- [x] `claude plugin test claude-home/mods/wf-dash`: 38 pass (one command `/wf-dash`, view letters, start submits only after yes from the clock, safe list, answer and stop confirms, stale plan kept, Alerts newest first). `claude plugin validate`: passed. -> AC-2, AC-5, AC-7
  can fail: `/plan` registered, a start submitted before yes
- [x] `python3 -m unittest runner/tests/test_wf_plan.py`: 9 pass; `python3 runner/tests/fast.py`: 1051 tests, 0 failed. -> AC-7

Specced but missing
- [ ] AC-5 "stop ... a background task": only agents from `$.agent.list()` get a stop (`panes.tsx`, Agents view). Probe P8 passed, with the shell id read from the Bash result text, so the action stays in the spec, but no code captures shell ids or offers to stop one. -> `/develop`

Design gate (frontend files changed): pass 1 found one must-fix (the action row and confirm grew the pane past its 14 rows, so the confirm keys could fall off). Fixed in this step: the action now takes rows from inside each view's budget (Plan's 3-row detail block, Builds' list budget), a start confirm that cannot show whole on two lines is not offered, and three new tests went red on four mutants. Pass 3 of 3: PASS WITH FINDINGS. Open in its report: plan warnings under All open still add a row each, a too-long step is shown only as a cut note, and 9 should-fixes.

Spec text drift for `/architect` (not a failure): AC-5 says the start is "submitted as a prompt"; the mod runs it with `$.command.run`, because the host refuses `$.prompt.submit` of slash text (spec 0063 probe P1) and `$.command.run` from a timer works (0063 P3, 0057 P2).

Left to the box: Install the mod update live after its scan (a real session: the pane beside the chat, the chip click, a start running as a turn, TaskStop on a subagent id, which P8 did not test).

## /check verify rerun, 2026-10-18 (wf run): FAIL, the same specced action is still not built

No code changed since the run above (last code commit 7603998). Rerun:
- [x] `claude plugin test claude-home/mods/wf-dash`: 38 pass, 0 fail. -> AC-2 to AC-5, AC-7
  can fail: `/plan` registered, a start submitted before yes, a stop with no confirm
- [x] `python3 -m unittest runner/tests/test_wf_plan.py`: 9 pass. -> AC-1, AC-5, AC-7
  can fail: a local PR record read as in review, a second answer overwriting the first
- [x] `python3 runner/wf.py plan --json` on the real machine: exit 0, 26 scopes (3 hubs), 26 distinct paths, none under wf-trees; row 73 `building`, row 75 `waits on you`, row 46 `done` with PR 76 (its heading is tagged done now). -> AC-1
  can fail: a worktree listed as its own repo, a running feature shown as its next box's state
- Design gate: `.design/audit-report.md` (20:19) is newer than every frontend file of the mod (newest `panes.tsx`, 20:17), so not rerun.

Specced but missing (unchanged)
- [ ] AC-5 "stop ... a background task": `TaskStop` is called only for `$.agent.list()` agents (`hooks/register.tsx:48`); nothing reads a shell id from a Bash result and the Agents view still says shells are not listed (`panes.tsx:503`). -> `/develop`
- [x] Built 2026-10-18: the Agents view lists this chat's background shells, read from `$.session.messages()` Bash results (`Command running in background with ID: <id>`), less ones a later successful TaskStop, a `<task-id>ID</task-id>` task notice (format checked in a real transcript), or the mod's own stop ended; each shows `started` (never `running`), a dim line says one may have ended unseen, and `x` then `y` calls `$.tool.call({ tool: 'TaskStop', task_id })` (`hooks/register.tsx` `shells()`, `panes.tsx` AgentsSection). Tests in `dashboard.test.ts`: "a background shell ... calls TaskStop with its id" (red on: Bash results not read; no stop offered for a shell; the mod's own stop not remembered) and "a shell that a task notice or a TaskStop ended is not offered as running" (red on: task notice ignored; model TaskStop ignored). `claude plugin test`: 40 pass; `claude plugin validate`: passed; `runner/tests/fast.py`: 1051 tests, 0 failed.

## /check verify, third run, 2026-10-18 (wf run): FAIL, the shell list can push the confirm keys off the pane

Code checked: up to 131897c (the background shell stop, built after the second run).

Commands
- [x] `claude plugin test claude-home/mods/wf-dash`: 41 pass, 0 fail. `claude plugin validate`: passed, and it lists `$.session.messages (via shells)` and `$.tool.call (via perform)`. -> AC-2 to AC-5, AC-7
  can fail: `/plan` registered, a start submitted before yes, a shell stop with no confirm
- [x] The message shape `shells()` reads is the host's real one: in the Claude Code 2.1.303 binary, each tool use row gets its result's `text` and `isError` merged in (`eye`, beside `rowsOf`), and user rows carry their text, so `u.text`, `u.isError` and `m.text` are real fields, not test only ones. -> AC-5
  can fail: a result text only under `toolResults`, so no shell would ever be found in a real session
- [x] Mutants on `hooks/register.tsx` (backed up, restored, `git status` clean after): a model TaskStop ignored -> "a shell that a task notice or a TaskStop ended is not offered as running" red; every stop read as failed -> "a background shell ... calls TaskStop with its id" red. -> AC-5
  can fail: a shell stop test that stays green while the stop is broken
- [x] `python3 -B -m unittest runner/tests/test_wf_plan.py`: 9 pass. -> AC-1, AC-5, AC-7
- [x] `python3 runner/wf.py plan --json` on the real machine: exit 0, 26 scopes, 26 distinct paths, none under wf-trees, 3 hubs (17, 5 and 0 rows), no spec with a blank status; row 73 `building`, row 75 `waits on you`, row 46 `done` with PR 76, row 77 `in progress` past its waiting Tailscale box. -> AC-1
  can fail: a worktree listed as its own repo, a running feature shown as its next box's state, a spec status printed blank
- [x] `wf answer` through the real CLI on a scratch queue (`XDG_STATE_HOME` in a temp folder): `ab12 7` exits 2 `wrong option: 7, pick 1 to 2`; `zz99 1` exits 1 `no question zz99`; with `WF_RUN` set exits 5 `refused: user_only`, nothing stored; `ab12 2` exits 0 `answered: ab12 SQLite (keyboard)`, stored `SQLite`; again exits 1 `already answered: ab12`. -> AC-5
  can fail: an out of range number stored, a second answer overwriting the first, an unattended call answering

Design gate (frontend files changed after the last report): pass 4, past its 3 pass budget, verdict STOP, findings 10 -> 16. Report: `claude-home/mods/wf-dash/.design/audit-report.md`.
- [ ] Must fix, new: the Agents view has no row budget. Shells pile up over a long chat, and with the stop confirm open the view takes 15 of its 14 rows at 100 columns with 1 agent and 7 shells (20 with 12), and overflows from 8 shells at 56 columns, so the `y` / `c` keys and the cursor fall off the bottom (`panes.tsx:494-510`, `:575`). Fix: page it the way Alerts does (`:526`). -> AC-3, AC-5, `/debug`
- [ ] Must fix, carried: plan warnings under All open draw rows outside the budget (`panes.tsx:349`, `:225`). -> AC-2a, `/debug`
- Should fix, new (in the report): `started` has no `agentStatus` token so it draws full strength, not dim (`tokens.ts:84-92`); a failed message read looks like no shells (`hooks/register.tsx:46-48`); a shell that ended unseen stays listed and its stop shows a red error every time (TaskStop answers `is not running (status: completed)`, `hooks/register.tsx:69-71`); the "no agents listed" note disappears when only shells are listed (`panes.tsx:493`).

Noted, not a failure: `~/projects/work/site-comparison` is a repo scope whose features are all `existing` with no boxes, so the old rule "no boxes means hub" (spec 0002, `runner/wf.py:420`) lists it as a hub with 0 rows; nothing open is hidden.

Left to the box: Install the mod update live after its scan (a real session: the pane beside the chat, the chip click, a start running as a turn, a shell and a subagent stopped from the Agents view).

## /check verify, fourth run, 2026-10-19 (wf run): FAIL, the plan warnings fix fails its own test

Code checked: 2e10c03 plus uncommitted fixes for both design gate must fixes in `panes.tsx` and `dashboard.test.ts` (not committed by the step that wrote them).

Commands
- [ ] `claude plugin test claude-home/mods/wf-dash`: 42 pass, 1 fail. The new test "plan warnings under All open take their rows from the list page, and too many are counted" fails: with 2 warnings it expects the page key `page down 1/4`, the mod draws `page down 1/3` (logged by a `console.log('NODE', ...)` left in the test). So the warnings do not take their rows out of the list page as the fix claims. -> AC-2a, `/debug`
  can fail: warnings drawn on top of a full page, so the pane grows past its rows
- [x] Same run: "a long agent list pages with the cursor, so the stop confirm stays inside the pane" passes (12 shells, cursor on the last, `+N more` / `N above` shown, `Stop shell Shell 11?` visible). The Agents row budget must fix looks fixed, but it is uncommitted and not yet re-audited. -> AC-3, AC-5
  can fail: all 12 shells drawn, so the first agent row stays on screen
- [x] `claude plugin validate claude-home/mods/wf-dash`: passed. -> AC-2
- [x] `python3 -B -m unittest runner/tests/test_wf_plan.py`: 9 pass. -> AC-1, AC-5, AC-7
  can fail: a local PR record read as in review, a second answer overwriting the first
- [x] `python3 runner/tests/fast.py`: 1051 tests, 0 failed.

Design gate: not rerun. Its report (`claude-home/mods/wf-dash/.design/audit-report.md`, 22:04) is older than `panes.tsx` (22:10) and says STOP: the pass budget is spent and you decide what happens next. Rerun it after `/debug` lands both fixes.

Also for `/debug`: remove the `console.log('NODE', ...)` line from `dashboard.test.ts`, and fix the spacing in `w =><Text` and `',async (`.

## /check verify, fifth run, 2026-10-19 (wf run): PASS

Code checked: 9ef8b43 plus the uncommitted `panes.tsx` and `dashboard.test.ts` fixes for both design gate must fixes. The `console.log` and the spacing noted above are gone (grep finds none).

Commands
- [x] `claude plugin test claude-home/mods/wf-dash`: 43 pass, 0 fail, including "plan warnings under All open take their rows from the list page, and too many are counted" (2 warnings: `page down 1/3`, 8 list lines on 3-row pages; 6 warnings: `w 1` shown, `w 2` cut, `+4 more plan warnings`) and "a long agent list pages with the cursor, so the stop confirm stays inside the pane". -> AC-2, AC-2a, AC-3, AC-4, AC-5, AC-7
  can fail: warnings drawn on top of a full page, or every shell drawn so the confirm keys fall off the pane
- [x] Mutant on `panes.tsx` (backed up, restored, `cmp` identical after): `room` without `- warns.length` -> the warnings test red, received `page down 1/2`. -> AC-2a
  can fail: a warnings test that stays green while the warnings still add rows
- [x] Mutant on `panes.tsx`: `agents.map` instead of `agents.slice(start, start + fit).map` -> the long agent list test red, the first agent `Look things up` still drawn. -> AC-3, AC-5
  can fail: an agents paging test that stays green while the whole list is drawn
- [x] `claude plugin validate claude-home/mods/wf-dash`: passed; calls `$.session.messages (via shells)` and `$.tool.call (via perform)`. -> AC-2, AC-5
  can fail: `/plan` or another old command registered, a hook the host refuses
- [x] `python3 -B -m unittest runner/tests/test_wf_plan.py`: 9 pass (answer: option out of range exits 2, second answer exits 1, under `WF_RUN` exits 5 `refused: user_only`). -> AC-1, AC-5, AC-7
  can fail: a local PR record read as in review, a second answer overwriting the first, an unattended call answering
- [x] `python3 runner/wf.py plan --json` on the real machine: exit 0, 26 scopes, 26 distinct paths, none under wf-trees, 3 hubs (17, 5 and 0 rows), no feature with a spec and a blank status; row 73 `building`, row 75 `waits on you`; the claude-config warning names the malformed waits-on-you marker. -> AC-1
  can fail: a worktree listed as its own repo, a running feature shown as its next box's state, a hub with no rows
- [x] `python3 runner/tests/fast.py`: 1051 tests, 0 failed.

Design gate (pass 5, outside the 3 pass budget, scoped to this diff): PASS WITH FINDINGS, report `claude-home/mods/wf-dash/.design/audit-report.md` newer than every mod file. Both pass 4 must fixes closed (Agents: 0 of 18,468 scratch renders past the pane, 12,411 on the old code; Plan warnings: never taller than with no warnings, 663 breaks on the old code). Open should fixes, for a later `/debug` (not a must fix): an empty All open tab with 5 or more warnings in a docked pane gets a list box of height 0 (`panes.tsx:316`, fix `Math.max(2, ...)`); at 40 columns the Plan filter keys wrap 3 rows past the pane (older than this diff); `k` from the bottom of a paged Agents list scrolls instead of moving the cursor; 8 carried should fixes.

Left to the box: Install the mod update live after its scan (a real session: the pane beside the chat, the chip click, a start running as a turn, a shell and a subagent stopped from the Agents view).
