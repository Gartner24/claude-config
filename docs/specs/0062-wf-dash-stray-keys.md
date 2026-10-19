# 0062. wf-dash names the way back that works: a click

**Date**: 2026-10-18 (amended twice on 2026-10-18, after probes P10 and P11 failed)
**Status**: Accepted
**Paths:** `claude-home/mods/wf-dash/**`

## What you're agreeing to
- A key the dashboard does not use can still type into the chat prompt and take the keyboard. A mod cannot stop that (probes P10 and P11).
- When that happens, the warning under the top line says `click the dashboard to return`, the one way back that worked in a real terminal. It no longer names ctrl+x tab, which did not work.
- Escape still closes the dashboard, and every key it uses today keeps working the same way.

## Summary
Today a key the dashboard has no button for falls through to the chat prompt and takes the keyboard, and the warn line points at ctrl+x tab, which did not give the keys back. Two probes found no way for a mod to catch those keys, and found that a mouse click on the dashboard always gives them back. So the fix is the hint: it names the click.

## Context
Plan row 75. The look was accepted at critique 29/40 on 2026-10-17, held there mostly by this. The dashboard is a Pane opened with `$.ui.open({ focus: true, closeOnEscape: true })` in `claude-home/mods/wf-dash/hooks/register.tsx`; its keys are hotkey `Button`s drawn by `keyRow` in `panes.tsx`, and the warn line is drawn at `panes.tsx` when the pane is not focused (`!focused`).

Facts this rests on ([verify notes](0062-wf-dash-stray-keys/verify.md)), Claude Code 2.1.303:
- P10: a surface module `Client` with `onKey` gets keys only after a click, so it does not catch a keyboard user's stray key.
- P11: a hotkey button cannot be hidden. A `plain` button with an empty label draws `z: `, a button with an empty label draws `[  ]`, a button with no label is refused and blanks the pane, and Tab lands on these buttons. A hotkey can only be one lowercase letter or digit anyway (API types line 1113), so Enter, Tab and arrows could never be caught.
- P11: after focus left the pane, ctrl+x then Tab did not return the keys (the key typed into the prompt); a mouse click on the pane did.

Your choices on 2026-10-18, in chat: first, bind keys on every view (over click to focus); after P11 failed, click to return with the hint fixed (over also drawing the dashboard's keys dim on every view).

## Requirements
- **AC-1** (probes, done): P10 and P11 are recorded in the verify notes. Nothing to build.
- **AC-2** (the hint): the warn line shown while the pane is not focused reads exactly `Keys go to the prompt now: click the dashboard to return`. It no longer mentions ctrl+x tab. Shown and hidden by the same `!focused` rule as today.
- **AC-3** (bindings kept): the keys of the locked look keep their meaning, labels and dim rules (`claude-home/mods/wf-dash/design.md`, Dashboard); the band chip's `w` hotkey (`band.tsx`) is unchanged. No row, column or layout moves.
- **AC-4** (design note): `design.md` (Dashboard, footer) replaces `ctrl+x tab returns here` (the host's key to focus a pane) with `click the dashboard to return`, and says a mod cannot catch a key it has no button for (probes P10, P11).
- **AC-5** (tests): a `*.test.ts` run by `claude plugin test` with `$` mocked: unfocused, the pane shows the AC-2 line exactly; focused, it does not; no text in the mod still says `ctrl+x tab`. Mutation checked (put the old text back, red).
- **AC-6** (real terminal, a box that waits on you after the build, since it needs a logged in interactive session): in tmux, open the built dashboard, press a key it does not use, see the AC-2 line, click the dashboard, and show a dashboard key works again with `tmux capture-pane`. Results in the verify notes.

## Decision
Accept that a stray key can leave the dashboard, and make the hint name the click, the way back that works.

## Rationale
A mod has no way to catch a key without a drawn button (P11), and no keyboard way back works (P11 (c)). The honest fix is a hint that is true. Drawing the dashboard's own keys on every view would catch a few common keys at the cost of a busier screen; you chose not to.

## Build plan
1. Change the warn line text, satisfies **AC-2**, **AC-3**
2. Change the `design.md` sentence, satisfies **AC-4**
3. Tests, satisfies **AC-5**
4. Real terminal check (a box that waits on you), satisfies **AC-6**

## Consequences
**Positive**: the hint is true, so you always know how to get the keyboard back.
**Negative / tradeoffs**: a stray key still types into the prompt; you need the mouse to come back. Retest after a Claude Code update in case the host adds a way to catch keys.
**Neutral**: the files overlap specs 0059 and 0060, so the runner builds them one at a time.

## Options considered
- Catch every key in a `Client` `onKey`: dropped, P10 showed it needs a click.
- Bind every letter and digit with hidden buttons: dropped, P11 showed a button cannot be hidden and Tab lands on it.
- Draw the dashboard's own keys dim on every view: catches a few common keys, busier screen; you declined it on 2026-10-18.
