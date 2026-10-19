# Auto handoff: our handover, fired on its own

Source: the owner's messages of 2026-10-18, after a side by side comparison of our handoff (spec 0057, `/rollover` plus `/handoff`) with alexknowshtml/claude-auto-handoff 0.8.6 (MIT, https://github.com/alexknowshtml/claude-auto-handoff).

## Agreed so far, do not ask again

- Owner's verdict: every part where their mod is better than ours, ours gets. Not a pick of four. Their code is MIT and may be reused (credit it in `docs/NOTICE.md`, scan it with `skill-scan` first).
- Where ours is better, ours stays: the handover is written by the working model through `/rollover` (memory sweep, "Agreed so far" briefs, scope state), never by a cheaper model; the resume reads the whole previous transcript; the twin check stays; quiet inside `wf` runs; background worker sessions still work.
- Copy, each one:
  1. Automatic trigger at a token threshold, checked after every turn and before every model request, counting tool output not yet measured.
  2. Tool gate: past the threshold, new tool calls are refused so one burst of reads cannot overflow; a refused call always ends in a handoff.
  3. The mod runs the clear and seeds the fresh chat itself; the owner types nothing.
  4. Loop guards: a fresh chat hands off no sooner than a set headroom past its own starting size; at most N handoffs in a row before the owner types.
  5. Files, commits and issues of the session pulled from the transcript by code into the handover, never from the model's memory.
  6. A "last request from the owner" section with an answered or not status; when not answered, the fresh chat does it first.
  7. Real numbers in the handover, written by code: tokens at handoff, the threshold and where it came from, the starting size, handoffs since the owner last typed. Any other figure is marked unverified.
  8. A progress panel above the prompt: each step with a spinner, then the result (for example 162k to 45k) and an open link; failures stay until dismissed; a toast on surfaces that draw no band.
  9. A readable page per handover, the chain of handoffs linked in order, served with short links on the Tailscale address (localhost without Tailscale).
  10. A link to the previous handover in the status line or band when a chat came from a handoff.
  11. Editable templates for the handover sections and for what the fresh chat is told.
  12. Settings in `/config` (threshold, max in a row, templates, ignored files, viewer address), plus env vars to override the threshold for one run and to turn it off.
  13. A log of everything the mod does.
- Owed to `/architect`: the threshold for a 1M window (their default 160k is sized for 200k), how this sits with auto-compact at 700k and the compact-keeper mod, and how the mod starts `/rollover` (their code submits a prompt with `$.prompt.submit`; needs a probe).
