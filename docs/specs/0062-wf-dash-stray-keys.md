# 0062. wf-dash catches every key while it has the keyboard

**Date**: 2026-10-18
**Status**: Proposed
**Paths:** `claude-home/mods/wf-dash/**`

## What you're agreeing to
- While the wf-dash dashboard has the keyboard, every key you press goes to the dashboard. A key it does not use does nothing; it never types into the chat prompt.
- Escape still closes the dashboard, and every key it uses today keeps working the same way.
- This rests on a mod feature nobody has tried here yet, so the build first tests it in a real terminal and stops if it does not work.

## Summary
Today a key the dashboard has no button for (a filter digit outside Plan, any other letter) falls through to the chat prompt and takes the keyboard, and the "ctrl+x tab returns here" hint did not give the keys back in a tmux test. The fix catches every key in the dashboard itself through a surface module `Client` and its `onKey` handler, so nothing falls through.

## Context
Plan row 75. The look was accepted at critique 29/40 on 2026-10-17, held there mostly by this. The dashboard is a Pane opened with `$.ui.open({ focus: true, closeOnEscape: true })` in `claude-home/mods/wf-dash/hooks/register.tsx`; its keys are hotkey buttons drawn in `panes.tsx`, and a key with no button falls through to the prompt (the design session's finding, Claude Code 2.1.302). A surface module `Client` with `onKey` receives every key: that comes from the mod docs read in that session and is unconfirmed by running. Your choice (2026-10-18): catch every key, over binding more keys on every view.

## Requirements
- **AC-1** (probe P10, build step 1, a box that waits on you, since it needs a logged in interactive session; never while wf builds): in a scratch folder outside `~/.claude`, with a copy of the mod that renders the dashboard through a surface module `Client` with `onKey`, run `claude --plugin-dir <copy>` inside tmux, open `/wf-dash`, and on the Builds view press `z`, `5`, `?`, Enter, Tab and an arrow key, then Escape. PASS when `onKey` logs every one of them, `tmux capture-pane` shows the prompt still empty, the dashboard still draws at its body width (`bodyColumns`) with its rows, and Escape closes the pane (by `closeOnEscape`, or by `onKey` closing it when it sees Escape; record which). Record the command lines and the result in `0062-wf-dash-stray-keys/verify.md`, including any key the host takes before the pane (its focus key, ctrl+c). A FAIL stops the build: nothing else in this spec is built, and row 75 goes back to `/architect` with the other option (bind more keys on every view).
- **AC-2** (catch every key): while the dashboard is focused, every key reaches its `onKey`. A key bound on the current view runs its action; every other key is consumed and does nothing, and never reaches the prompt. Keys the host handles before any pane (recorded by P10) stay the host's.
- **AC-3** (bindings kept): the keys of the locked look keep their meaning and their dim rules (`claude-home/mods/wf-dash/design.md`, Dashboard): `p` `b` `a` `l` views, `1` to `8` Plan filters, `j` `k` `d` `u` `n` `g` on Plan, `j` `k` on Builds and Alerts, `r` refresh, Escape closes; the band chip's `w` hotkey (`band.tsx`) is unchanged. The action and confirm keys of spec 0060 AC-5 go through the same `onKey` when that build adds them.
- **AC-4** (warning removed): the warn line `Keys go to the prompt now: ctrl+x tab returns here` and the code that shows it are removed, since no key falls through any more. `design.md` drops that sentence and rewrites its reason "a key with no button falls through to the prompt" (Dashboard, footer) to say unbound keys are caught.
- **AC-5** (tests): a `*.test.ts` run by `claude plugin test` with `$` mocked: each bound key on each view runs its action; an unbound letter, a digit outside Plan and a symbol are consumed with no action and no prompt write; mutation checked (let one unbound key pass through, red).
- **AC-6** (real terminal, a box that waits on you after the build, since it needs a logged in interactive session): drive the built mod in tmux as P10 does, type stray keys on every view, and show the prompt still empty with `tmux capture-pane`; result in the verify notes. The unattended `/check verify` covers AC-2 to AC-5 through the tests and cites this box.

## Decision
Catch every key in the dashboard through a surface module `Client` and its `onKey`, behind a probe that runs first.

## Build plan
1. Probe P10 (a box that waits on you), satisfies **AC-1**; stop on FAIL
2. Move the dashboard's key handling into the `Client`'s `onKey`, satisfies **AC-2**, **AC-3**
3. Remove the fall through warning, satisfies **AC-4**
4. Tests, satisfies **AC-5**
5. Real terminal check (a box that waits on you), satisfies **AC-6**

## Consequences
**Positive**: no stray key takes the keyboard away from the dashboard.
**Negative / tradeoffs**: one more early access mod surface to retest after every Claude Code update; while the dashboard has focus, you cannot type into the prompt until Escape.
**Neutral**: the files overlap specs 0059 and 0060, so the runner builds them one at a time. No stack: the dashboard it changes is already on main (the locked preview code).
