# 0062 verify: probe P10 (AC-1)

# 0062 verify: probe P10 (AC-1)

Run 2026-10-18 by a subagent, Claude Code 2.1.303, model haiku. Probe: throwaway `probe-0062` mod in the session scratchpad (`p0062/mod`, never installed; `claude plugin validate` passed, one warning: no author). Hooks module opens the pane with `$.ui.open({ id: 'probe-dash', focus: true, closeOnEscape: true, rows: 10 })` from `/probe-dash`; its `ui.render` hook draws a `Client` (`module: "./client.tsx"`, key `k`, props `{ bodyColumns }`) whose `onKey` calls `surface.post`; a `ui.message` hook logs each post with `$.fs.write` to `p0062/out/log.txt`. Session: `tmux new-session -d -s probe0062 -x 200 -y 50 -c <scratch>/p0062/cwd "claude --plugin-dir <scratch>/p0062/mod --model haiku"`, driven with `tmux send-keys` (keys 0.6 s apart, since a surface post is one per frame and a later post replaces an undelivered one). Session killed after the run.

Verdict: FAIL as AC-1 words it (keys reach `onKey` right after the pane opens with `focus: true`). PASS once a mouse click on the `Client` region has given it the focus. Other criteria PASS.

- [ ] P10 every key reaches `onKey` with the pane opened by `focus: true`. FAIL.
  Command: `/probe-dash` (pane opens, `render ... isFocused=true placement=dock`), then `z`, `5`, `?`, Enter, Tab, Down with no click.
  Observed: no `ui.message` line at all. The first key moved focus off the pane (`render ... isFocused=false`) and the keys typed into the prompt: the log has `prompt.submit "z5?"` and the screen shows `> z5?` sent to the model (Enter submitted it). Tab and Down went to the prompt too. This is the stray-key bug itself, and a `Client` does not cure it on its own.
  can fail: a `ui.message` line for each key; there was none.

- [x] P10b same keys after a click on the `Client` region. PASS.
  Command: SGR mouse press and release at column 60, row 3 (`printf '\e[<0;60;3M'` then `m`, via `tmux send-keys -l`), inside the Client's drawing. Then `z`, `5`, `?`, Enter, Tab, Down.
  Observed log lines, one per key, all with ctrl/shift/meta false: `ui.message {"kind":"key","key":"z"...}`, `"5"`, `"?"`, `"return"`, `"tab"`, `"down"`. `tmux capture-pane`: prompt line `> ` empty, nothing typed, no new `prompt.submit` line in the log after the click. Pane still drawn: first row 84 `#` characters (the Client sized `bodyColumns - 2`), `row one: builds view`, `row two: cols=86 bodyColumns=86`. So the body width equals `bodyColumns` (86 at 200 columns, dock placement) and the rows draw.
  can fail: a key missing from the log, a character in the prompt, or the rows missing from the pane.

- [x] P10c Escape. PASS, in two steps.
  First Escape (Client focused): no `ui.message`, pane stays open and drawn; the doc line holds: "Escape never arrives: it returns the focus" (Client types, `ClientKeyEvent`). So `onKey` never sees Escape and cannot close the pane itself.
  Second Escape: `ui.close {"id":"probe-dash","origin":{"kind":"person"}}`, pane gone. It closes by `closeOnEscape`, not by `onKey`.
  can fail: the pane staying open after Escape.

- Host keys: not exercised (ctrl+c, ctrl+x tab). Per the types, ctrl+x tab is the host's focus chord and a click is the other way to focus; ctrl+c was not sent in the probe so as not to end the session.

## Build rules from this probe
- `focus: true` on `$.ui.open` focuses the Pane, not the `Client`. The Client gets keys only after a click on its region (types, line ~1626: "reached while a click has given it the focus"). A keyboard-only person never reaches `onKey`: the first stray key still falls to the prompt. I found no prop or call that focuses a Client without a click (grep of the API types for focus/click: lines 1117, 1170, 1626, 4154 only).
- Escape needs two presses with a focused Client: the first returns focus from the Client, the second runs `closeOnEscape`. Escape never reaches `onKey`.
- Surface module path is relative to the hooks module (`hooks/client.tsx`), not the plugin root; a surface module has no `$`, it reports through `surface.post` and a `ui.message` hook.
- One post per frame: keys sent faster than about 0.5 s apart can drop (not measured, per the types).
- Consequence for 0062: AC-1 FAIL as worded, so the spec's own rule applies (a FAIL stops the build; row 75 back to `/architect`), unless the owner accepts a click-to-focus dashboard.

# 0062 verify: probe P11 (hidden hotkey buttons, AC-1 of the first amendment)

Run 2026-10-18 by a subagent, Claude Code 2.1.303, model haiku. Throwaway mod in the session scratchpad (`p11/mod`, never installed; `claude plugin validate` passed). Pane opened from `/p11` with `$.ui.open({ id: 'p11', focus: true, closeOnEscape: true, rows: 10 })`; visible buttons `p` (plain, `here`) and `q` (dim); hidden tries each in its own Box between markers: `z` plain with `label=""`, `x` no plain and no label, `y` no plain with `label=""`; a band button `w`. Each `onPress` appended `<key> pressed` to a log. Session: `tmux new-session -d -s p11 -x 200 -y 50 -c <scratch>/p11/cwd "claude --plugin-dir <scratch>/p11/mod --model haiku"`, keys 0.6 s apart with `tmux send-keys`. Session killed after the run.

Verdict: FAIL. No hidden try draws nothing, and Tab lands on them.

- [ ] (a) a hidden try draws nothing. FAIL.
  Observed: `z` draws `a|z: |a` (hotkey, colon, space); `y` draws `c|[  ]|c` (bracket chrome); `x` is refused: `ui.render hook skipped: threw HooksError: JSX element <Button> needs a label`, and the pane draws empty.
  can fail: any glyph or gap between the markers; there were.
- [x] (b) hidden keys reach `onPress`, prompt empty. PASS for `z`, `y`, `p`, `q` (log `z pressed;y pressed;p pressed;q pressed;`, prompt `> ` empty). `w` (band button) with the pane focused went to the prompt and took the focus.
  can fail: a key missing from the log or typed into the prompt.
- [ ] (b2) Tab never lands on a hidden button. FAIL: the third Tab inverted `z: `.
  can fail: an inverted hidden button; there was one.
- (c) way back after focus left the pane: ctrl+x then Tab did NOT return the keys (`z` typed into the prompt, log unchanged). An SGR click inside the pane (`\e[<0;125;2M`, then `m`) did; `z` then logged. One Escape after the click closed the pane (`closeOnEscape`).

## Build rules from this probe
- A Button cannot be hidden: it needs a label, `plain` draws its hotkey and a colon, and the chromed form draws brackets. Tab walks every Button.
- A key with no Button in the focused pane falls to the prompt, band hotkeys included.
- The working way back is a click on the pane, not ctrl+x tab.
- Consequence for 0062: the hidden button plan stops; amended again to click to return (your pick 2026-10-18).
