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
