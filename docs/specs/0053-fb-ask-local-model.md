# 0053. fb-ask can use the laptop model for private text

**Date**: 2026-10-17
**Status**: Proposed
**Paths:** `scripts/fb-ask.py`, `claude-home/rules/cheap-worker.md`, `AGENTS.md`
**Amends**: [0023](0023-cheap-worker-tier/index.md) AC-4, AC-5, AC-6, AC-8, AC-9, AC-12, AC-13 (a `--local` mode)

## What you're agreeing to
- `fb-ask --local` sends the job to the model on your laptop (`fb-local`), never to a cloud model.
- With `--local`, text from client and work repos and text with private names is allowed, because nothing leaves the machine.
- Without `--local`, nothing changes: cloud only, client repos and private names still refused.
- It never runs inside a runner call, and long inputs (over about 40,000 characters) fall back to you.

## Summary
fb-ask hands long, boring text jobs to a free model. It refuses client text because the free models are in the cloud. The laptop model (set up in plan A7) keeps text on the machine, so a `--local` flag lets client text through to it only. It is slow (about 6 words a second, 2 minutes to load), so its limits are set to fit.

## Context
`MODEL = "fb-safe"` is fixed (`scripts/fb-ask.py:27`); the origin gate (`:253-257`) and the names gate (`:139`, `:271`) refuse client and private text. The `fb-local` group already exists in `~/.config/claude-fb/litellm.yaml` (A7: `qwen2.5-coder:14b`, 16k context, keep_alive 2m, 6.1 tok/s, 120 s cold load). Your answers (brief, 2026-10-17): D4 yes through `fb-local` only; skip the names check in local mode.

## Requirements
- **AC-1** (flag): `--local` (a boolean, parse at `fb-ask.py:71-85`) sets the model to `fb-local`. Without it the model stays `fb-safe`; `fb-any` is never used.
- **AC-2** (gates lifted only locally): with `--local`, the origin gate and the names gate are skipped. Without it both are unchanged (`client_repo`, `private_name`, `no_names_list` as spec 0023 AC-4 to AC-6).
- **AC-3** (never in a run): `WF_RUN` set gives `fall back: in_call` with or without `--local`.
- **AC-4** (no silent cloud): with `--local`, the `/v1/models` check looks for `fb-local`; missing is `fall back: wrong_proxy`, and no request is ever sent to `fb-safe`.
- **AC-5** (limits): with `--local`, `LOCAL_MAX_INPUT = 40_000` characters (over it is `too_large`), `LOCAL_MAX_TOKENS = 1024`, `LOCAL_WAIT = 420` s for the answer (a timeout is `fall back: timeout`). The cloud values (`:30-33`) are unchanged.
- **AC-6** (visible): the stderr line names the model that answered, so a caller sees it ran locally.
- **AC-7** (self checks): `fb-ask --test` adds: a client repo and a private name pass with `--local` and are refused without it; the request model is `fb-local`; a proxy without `fb-local` gives `wrong_proxy` with zero `fb-safe` requests; `too_large` at 40,001 characters with `--local`; `in_call` with `--local`.
- **AC-8** (rule and docs): `claude-home/rules/cheap-worker.md` (still at most 8 lines) says client or work text is allowed only with `--local`, expect about 2 minutes cold and about 6 words a second, input under about 40,000 characters, never during `wf run`. AGENTS.md's fb-ask command line shows `[--local]`.
- **AC-9** (live probe, after the build, never while wf builds): `fb-ask summarize --local` on a 39,000 character file with a fact planted in its first paragraph; the answer must contain the fact (proves no silent cut at 16k). Command and answer go in this spec's verify notes in the PR.

## Decision
A boolean `--local` flag in fb-ask, three local limit constants, gates lifted only in that mode. The runner's own fb-ask use (`runner/run.py`, spec 0023 AC-10) stays cloud only.

## Rationale
Nothing leaves the laptop in local mode, so the gates that protect against sending text out protect nothing there, and keeping them would block the client text you asked to allow. A boolean cannot name a cloud group by mistake.

## Build plan
1. `--local` flag, model switch, local limits, gates lifted locally, `wrong_proxy` on missing group, satisfies **AC-1** to **AC-6**
2. Self checks, satisfies **AC-7**
3. Rule file and AGENTS.md line, satisfies **AC-8**
4. Live probe, satisfies **AC-9**

## Consequences
**Positive**: client logs and transcripts can be summarized without using your Claude limit.
**Negative / tradeoffs**: slow; the laptop swaps while the model is loaded (A7), so it is never used while wf builds.
**Neutral**: `litellm.yaml` lives outside the repo and is not changed.
