# 0064. Auto handoff display: band progress, viewer pages, handoff link

**Date**: 2026-10-18
**Status**: Proposed
**Paths:** `claude-home/mods/wf-handoff/**`, `claude-home/mods/wf-dash/**`
**Stacks on:** 0063

## What you're agreeing to
- While a handoff runs, the wf-dash band shows each step with a spinner, then "handed off, 210k to 95k" with an open link, for 10 seconds.
- Failures and pauses stay in the band until you dismiss them or type; without wf-dash, or on the phone or VS Code, they arrive as toasts.
- Each handover gets a readable page, the chain of handoffs linked in order, served on your Tailscale address (this laptop only until Tailscale is set up).
- A chat that came from a handoff shows a short link to its handover in the band.
- You install Tailscale yourself; until then everything works on localhost.

## Summary

Spec 0063 makes the handoff fire on its own. This spec shows it: progress in the wf-dash band (the strip above the prompt), a readable page for every handover served to your own devices over Tailscale (a private network between your devices), and a link back to the handover in the band of the fresh chat. It reuses the panel, viewer and server code of alexknowshtml/claude-auto-handoff (MIT). The build starts once the wf-dash band (spec 0059) is merged.

## Context

A handoff that runs on its own needs to be visible: the owner must see it start, see it finish, and see when it failed or paused. Their mod draws its own panel above the prompt; ours already has the wf-dash band there, and two strips would fight. Their mod also serves each brief as a page on the Tailscale address so it opens on a phone; this laptop has no Tailscale yet, and the owner chose to install it.

The pages hold handover text, which can carry private repo and client names, so where they are served matters: never on a public interface.

## Requirements

**User stories**:
- As the owner, I want to see a handoff happen and its result without reading logs.
- As the owner, I want to open a handover on my phone.

**Acceptance criteria**:
- **AC-1** (panel file): the wf-handoff mod writes `~/.claude/state/auto-handoff/panel.json` on every phase change of spec 0063: `{session, phase, steps: [{label, state}], result, sticky, link}`. Steps: "writing the handover", "clearing", "starting the fresh chat". "starting the fresh chat" is done once the seed command has run and the fresh chat's starting size has been read (spec 0063 AC-1, AC-6); `session` and `previous` come from the chain state of spec 0063.
- **AC-2** (band): the wf-dash band reads that file on its tick and, when its `session` matches or its `session` is the previous chat of this one, draws one line: the running step with a braille spinner, or `handed off · <before>k -> <after>k · <short link>` for 10 seconds (the band cannot be clicked, so it prints the link as text), or the failure or pause text. `sticky` lines stay until the owner types or presses the band's dismiss key.
- **AC-3** (toast fallback): when wf-dash is not loaded, or `$.session.surfaces()` holds a surface that draws no band (mobile, VS Code), the start, the result, and every sticky line also go out as a toast (`$.ui.toast`, 30 s for sticky).
- **AC-4** (pages): each handover gets `~/.claude/state/auto-handoff/pages/<session id>.html`, rendered when spec 0063 adds the facts block (before the clear consumes the slot) with the previous handover of the chain linked; at seed time the previous page is rendered again to add its next link. All slot text is HTML escaped. Code reused from their `viewer.ts`, written with `$.fs.write` (no `mkdir`).
- **AC-5** (server): a page server (their `server.ts`) starts with the first session that loads the mod and serves `/<first 8 of the session id>-<16 random hex characters>` as that page (the random part is kept in the chain state, so links cannot be guessed). When the port answers no request, or the running server's bind address differs from what this session's bind rule gives (Tailscale came up), the next session to load the mod takes over: it stops a server it can identify as the mod's own and starts its own. It binds only to the Tailscale IPv4 address when `tailscale ip -4` answers, else `127.0.0.1`; never `0.0.0.0` or another interface. Address from the `viewer` setting (spec 0063 AC-10, format `[host:]port`), default `tailscale:3846`; blank means no server and the link is the `file://` path. A session that finds the port taken leaves the running server alone and logs one line.
- **AC-6** (link): a chat that came from a handoff shows `handover: <short link>` in the band, taken from the chain state (`link`, written by the mod when it adds the facts block), since the slot is consumed by `/resume-from-clear`. The mod also writes `viewer: <link>` into the facts block so the fresh chat sees it.
- **AC-7** (Tailscale): installing and logging in to Tailscale is a box that waits on you; nothing in this spec installs it. When it comes up later, the next new session serves on the Tailscale address.
- **AC-8** (tests and scan): panel file, band line, toast fallback, page render, bind rule and link are covered by `claude plugin test` for both mods; both pass `skill-scan` before their live install, a box that waits on you.

## Options considered

### Option 1: Progress in the wf-dash band through a file
**Pros**: one strip above the prompt; mods stay independent (a file contract, no shared code).
**Cons**: the band polls the file on its tick, so a step can show up to one tick late.

### Option 2: Its own panel, like theirs
**Pros**: works without wf-dash.
**Cons**: two strips above the prompt; the owner picked the band.

## Decision

**Chosen option**: Option 1, with toasts as the fallback.

## Rationale

The owner chose the band. A file keeps the two mods free of each other's code, and toasts cover every place the band is not drawn, which their mod also does.

## Feature design

**Data model sketch**: `panel.json` as in AC-1; pages under `pages/`; chain state (spec 0063) gains `link` and `pageKey` (the random part).

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| band line | phase, steps, result | `panel.json` written by spec 0063's phase changes |
| result | before and after tokens | tokens at handoff (spec 0063 AC-5) and the first measured size of the new session |
| server bind | address | `tailscale ip -4`, else `127.0.0.1` |
| link | short link | `viewer` setting host and port, the first 8 characters of the session id, and `pageKey` from the chain state |

**Key invariants**: the server never binds to anything but the Tailscale address or loopback; a sticky line never disappears on its own.

**Security model**: pages are readable only on this machine or the owner's tailnet.

**Critical test scenarios**:
- Happy path: a handoff shows three steps, then the result for 10 s, verifies **AC-1**, **AC-2**.
- Failure: a missing slot shows a sticky line until the owner types, verifies **AC-2**.
- No band: with wf-dash unloaded the result arrives as a toast, verifies **AC-3**.
- Bind: with no Tailscale the server listens on 127.0.0.1 only, verifies **AC-5**.

## Build plan

1. Panel file writes from the spec 0063 phases, satisfies **AC-1**
2. Band line in wf-dash and toast fallback, satisfies **AC-2**, **AC-3**
3. Pages and server with the bind rule, satisfies **AC-4**, **AC-5**
4. Seed time header line and band link, satisfies **AC-6**
5. Tests and scan, satisfies **AC-8**

## Consequences

**Positive**: a handoff is visible on the laptop and the phone.
**Negative / tradeoffs**: a page server process runs while a session is open; wf-dash now reads one more file.
**Neutral**: needs the wf-dash band merged first; Tailscale is your step.
