# 0062. wf-dash binds every letter and digit on every view

**Date**: 2026-10-18 (amended 2026-10-18 after probe P10 failed)
**Status**: Proposed
**Paths:** `claude-home/mods/wf-dash/**`

## What you're agreeing to
- While the dashboard has the keyboard, every letter and digit is bound on every view. A key that does nothing on this view is caught and does nothing; it never types into the chat prompt.
- Keys a dashboard cannot bind at all (Enter, Tab, arrows, symbols) can still fall through. For those the dashboard shows the way back, and that way is tested in a real terminal.
- Escape still closes the dashboard, and every key it uses today keeps working the same way.
- The hidden bindings rest on a mod behavior nobody has tried yet, so the build tests it first and stops if it does not work.

## Summary
Today a key the dashboard has no button for (a filter digit outside Plan, any other letter) falls through to the chat prompt and takes the keyboard. Probe P10 showed the first plan, catching every key in a surface module `Client` with `onKey`, only works after a mouse click, so a keyboard user never reaches it. This amendment takes the other option: every view binds all 26 lowercase letters and the 10 digits as hotkey buttons, the ones the view does not use drawn as nothing, so they are caught. The keys a hotkey cannot name keep the warn line, now pointing at a way back proven in tmux.

## Context
Plan row 75. The look was accepted at critique 29/40 on 2026-10-17, held there mostly by this. The dashboard is a Pane opened with `$.ui.open({ focus: true, closeOnEscape: true })` in `claude-home/mods/wf-dash/hooks/register.tsx`; its keys are hotkey `Button`s drawn by `keyRow` in `panes.tsx`.

Facts this rests on:
- Probe P10, 2026-10-18 ([verify notes](0062-wf-dash-stray-keys/verify.md)): with `focus: true` and no click, the first key moved focus off the pane and typed into the prompt; a `Client` gets keys only after a click on it. Escape never reaches `onKey`.
- Mod API types (Claude Code 2.1.303, `index.d.ts` lines 1113 to 1121): a `Button` `hotkey` is one digit or one lowercase letter, anything else is refused; Shift plus a letter counts as that letter. No `disabled` prop. `dimColor` changes only the drawing; whether a dim button still takes its key is not stated. No documented way to bind a key without drawing a button (`PaneOpenArgs` has no keys option, lines 7550 to 7586).
- Types line 10727: the person returns focus to a pane with ctrl+x tab or a click. The design session saw ctrl+x tab fail in tmux once; P10b saw a click work.

Your choice (2026-10-18, in chat, after P10 failed): bind keys on every view, over accepting click to focus.

## Requirements
- **AC-1** (probe P11, build step 1, a box that waits on you, since it needs a logged in interactive session; never while wf builds): in a scratch folder outside `~/.claude`, with a throwaway mod whose pane draws one visible button (`hotkey="p"`, label `here`, `plain`), one dim button (`hotkey="q"`, `dimColor`), and three hidden button tries, each in its own `Box` with no `columnGap`: `hotkey="z"` with `plain` and `label=""`; `hotkey="x"` with no `plain` and no label; `hotkey="y"` with no `plain` and `label=""`. Each `onPress` logs through `$.fs.write`. Show the band too, run `claude --plugin-dir <copy>` in tmux, open the pane with `focus: true`, and press `z`, `x`, `y`, `q`, `w`, `p`, Tab, then Escape. Record: (a) which hidden tries draw nothing (`tmux capture-pane` shows no glyph, gap or inverted cell where they sit, also while their key is pressed); (b) do the hidden keys, `q` and `w` reach the pane's `onPress` and leave the prompt empty; (b2) does Tab ever put the focus on a hidden button; (c) after Tab moves focus away, do keys reach the pane again after ctrl+x tab, and after a click on the pane. Write the command lines and results in `0062-wf-dash-stray-keys/verify.md`. PASS needs at least one hidden try passing (a), and (b) and (b2) passing; the build uses that try. A FAIL stops the build: nothing else in this spec is built, and row 75 goes back to `/architect` (no quiet switch to drawn dim keys).
- **AC-2** (every letter and digit bound): on every view (Plan, Builds, Agents, Alerts, and the stop confirm of spec 0060 AC-5, which counts as a fifth view) each of `a` to `z` and `0` to `9` is the hotkey of exactly one button in the pane, `w` included (the band's `w` presses only while the band has the focus; P11 (b) checks it). A key the view uses runs its action as today; a used key drawn dim because it would do nothing (`j` with nothing below) still counts as used and does nothing. Every other key is a catch button drawn the way P11 proved, whose `onPress` does nothing. The used set comes from the keys the view actually draws (the items handed to `keyRow` and the action and confirm rows), never a hand list. The catch buttons sit in one block at the pane's root, outside every `keyRow`, so they add no gaps.
- **AC-3** (bindings kept): the keys of the locked look keep their meaning, labels and dim rules (`claude-home/mods/wf-dash/design.md`, Dashboard): `p` `b` `a` `l` views, `1` to `8` Plan filters, `j` `k` `d` `u` `n` `g` on Plan, `j` `k` on Builds and Alerts, `r` refresh, Escape closes; the band chip's `w` hotkey (`band.tsx`) is unchanged. No row, column or layout of the look moves.
- **AC-4** (the way back for the rest): Enter, Tab, arrows and symbols cannot be hotkeys and may still fall through. The warn line under the top line stays, shown only when the pane has lost focus (as today, `panes.tsx` `!focused`), and names the way back that P11 (c) proved: `Keys go to the prompt now: ctrl+x tab returns here` if only ctrl+x tab worked, `Keys go to the prompt now: click the dashboard to return` if only the click did, `Keys go to the prompt now: ctrl+x tab or a click returns here` if both did. If neither worked in P11, the build stops and row 75 goes back to `/architect`. `design.md` rewrites "a key with no button falls through to the prompt" (Dashboard, footer) to say letters and digits are always caught and only other keys can fall through.
- **AC-5** (tests): a `*.test.ts` run by `claude plugin test` with `$` mocked: on each of the five views, the pane's buttons carry each of the 36 keys exactly once; pressing a catch key runs no action; pressing a used key runs that view's action as before. Every existing row keeps its width (the cells `rowCells` counts are unchanged). These tests prove the binding, not that a key arrives from a real terminal (that is AC-6). Mutation checked: drop one catch button on one view, the test goes red.
- **AC-6** (real terminal, a box that waits on you after the build, since it needs a logged in interactive session): drive the built mod in tmux as P11 does, type every letter and digit on every view, and show with `tmux capture-pane` that the prompt stays empty and the layout matches the look; then press Tab, see the warn line, use the way back it names, and show the keys reach the pane again. Results in the verify notes. The unattended `/check verify` covers AC-2 to AC-5 through the tests and cites this box.

## Decision
Bind all 36 letters and digits on every view as hotkey buttons, the unused ones drawn as nothing, behind a probe that runs first. Keep the warn line for the keys no hotkey can name, pointing at the way back the probe proved. The surface module `Client` plan is dropped (P10: it needs a click).

## Build plan
1. Probe P11 (a box that waits on you), satisfies **AC-1**; stop on FAIL
2. One catch block at the pane's root in `panes.tsx` that takes the keys the current view draws and adds a hidden button for every other letter and digit, satisfies **AC-2**, **AC-3**
3. Warn line wording and the `design.md` sentence, satisfies **AC-4**
4. Tests, satisfies **AC-5**
5. Real terminal check (a box that waits on you), satisfies **AC-6**

## Consequences
**Positive**: no letter or digit takes the keyboard away from the dashboard, with no click needed.
**Negative / tradeoffs**: Enter, Tab, arrows and symbols can still fall through; the warn line and its way back cover them. The hidden buttons rely on an undocumented drawing of an empty label, retested after every Claude Code update. While the dashboard has focus, you cannot type into the prompt until Escape.
**Neutral**: the files overlap specs 0059 and 0060, so the runner builds them one at a time. No stack: the dashboard it changes is already on main.

## Rationale
Hotkey buttons are the one key path that works with `focus: true` and no click (the dashboard's keys work today). Binding every key a hotkey can name closes the gap as far as the mod API allows, and the warn line covers the rest without claiming more than is proven.

## Options considered
- Catch every key in a `Client` `onKey` (the first plan): dropped, P10 showed it needs a click.
- Accept click to focus: you declined it on 2026-10-18.
- Bind only the dashboard's own keys on every view, drawn dim: leaves every other letter falling through, and adds visible buttons to views that do not use them. Not built on a P11 FAIL without you choosing it in `/architect`.
- Note from the API types (line 1131): a `plain` button draws "the hotkey in the accent color, a colon, the label", so the `plain` hidden try may well fail; that is why P11 tries three.
