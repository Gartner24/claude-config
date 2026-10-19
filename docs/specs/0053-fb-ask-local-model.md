# 0053. fb-ask can use the laptop model for private text

**Date**: 2026-10-17
**Status**: Accepted
**Paths:** `scripts/fb-ask.py`, `claude-home/rules/cheap-worker.md`, `AGENTS.md`
**Amends**: [0023](0023-cheap-worker-tier/index.md) AC-4, AC-5, AC-6, AC-8, AC-9, AC-12, AC-13 (a `--local` mode)

## What you're agreeing to
- `fb-ask --local` sends the job to the model on your laptop (`fb-local`), never to a cloud model.
- With `--local`, text from client and work repos and text with private names is allowed, because nothing leaves the machine.
- Without `--local`, nothing changes: cloud only, client repos and private names still refused.
- It never runs inside a runner call or while a runner build is going; long inputs (over about 30,000 characters) or anything that would be cut fall back to you.

## Summary
fb-ask hands long, boring text jobs to a free model. It refuses client text because the free models are in the cloud. The laptop model (set up in plan A7) keeps text on the machine, so a `--local` flag lets client text through to it only. It is slow (about 6 words a second, 2 minutes to load), so its limits are set to fit.

## Context
`MODEL = "fb-safe"` is fixed (`scripts/fb-ask.py:27`); the origin gate (`:253-257`) and the names gate (`:139`, `:271`) refuse client and private text. The `fb-local` group already exists in `~/.config/claude-fb/litellm.yaml` (A7: `qwen2.5-coder:14b`, 16k context, keep_alive 2m, 6.1 tok/s, 120 s cold load). Your answers (brief, 2026-10-17): D4 yes through `fb-local` only; skip the names check in local mode.

## Requirements
- **AC-1** (flag): `--local` (a boolean, parse at `fb-ask.py:71-85`) sets the model to `fb-local`. Without it the model stays `fb-safe`; `fb-any` is never used.
- **AC-2** (gates lifted only locally): with `--local`, the origin gate and the names gate are skipped. Without it both are unchanged (`client_repo`, `private_name`, `no_names_list` as spec 0023 AC-4 to AC-6).
- **AC-3** (never in a run, never during a build): `WF_RUN` set gives `fall back: in_call` with or without `--local`. With `--local`, a live wf run (any entry in `~/.local/state/wf/active.json` whose runner lock is held, the check `runner/auto.py:169-171` uses) gives `fall back: wf_building`, so the laptop never swaps during a build.
- **AC-4** (no silent cloud): with `--local`, the `/v1/models` check looks for `fb-local`; missing is `fall back: wrong_proxy`, and no request is ever sent to `fb-safe`.
- **AC-5** (limits): with `--local`, `LOCAL_MAX_INPUT = 30_000` characters (the read caps at `:263` and `:268` use it; over it is `too_large`), `LOCAL_MAX_TOKENS = 1024` for summarize and 512 for classify, extract and commit-msg, `LOCAL_WAIT = 420` s for the answer (a timeout is `fall back: timeout`). Budget from A7: cold load 120 s, prompt 142 tok/s, generation 6.1 tok/s. The cloud values (`:30-33`) are unchanged.
- **AC-5b** (no silent cut): the model's context is 16k tokens (`OLLAMA_CONTEXT_LENGTH=16384` in `/etc/systemd/system/ollama.service.d/override.conf`, set during A7). With `--local`, the reply's `usage.input_tokens` at or above 15,500, or missing, gives `fall back: truncated` and no answer, because Ollama drops the start of an input that does not fit and the answer would read as complete.
- **AC-6** (visible): the stderr line says `fb-ask: local` plus the model name with `--local`, from the flag, not from the reply.
- **AC-7** (self checks): `fb-ask --test` adds, with `fb-ok.txt` absent and `names.txt` present so the gates would refuse: a client repo and a private name pass with `--local` and are refused without it; the request model is `fb-local`; a proxy without `fb-local` gives `wrong_proxy` with zero `fb-safe` requests; `too_large` at 30,001 characters; `truncated` at 15,500 input tokens and on missing usage; `timeout` with `LOCAL_WAIT` patched; `in_call` and `wf_building` with `--local`; the stderr line says local.
- **AC-8** (rule and docs): `claude-home/rules/cheap-worker.md` (still at most 8 lines) says client or work text is allowed only with `--local`, expect about 2 minutes cold and about 6 words a second, input under about 30,000 characters, run it with a 600000 ms tool timeout or in the background, never during a wf build. AGENTS.md's fb-ask command line shows `[--local]`.
- **AC-9** (live probes, after the build, never while wf builds): P1 `fb-ask summarize --local` on a 29,000 character dense log with a fact planted in its first lines; the answer must contain the fact. P2 a local call killed by its timeout, then a second call: record whether LiteLLM's cooldown (`cooldown_time 1800` in `litellm.yaml`) blocks it; if it does, set `num_retries: 0` and a short cooldown on the `fb-local` group and record the change. Commands and results go in verify notes.

## Decision
A boolean `--local` flag in fb-ask, three local limit constants, gates lifted only in that mode. The runner's own fb-ask use (`runner/run.py`, spec 0023 AC-10) stays cloud only.

## Rationale
Nothing leaves the laptop in local mode, so the gates that protect against sending text out protect nothing there, and keeping them would block the client text you asked to allow. A boolean cannot name a cloud group by mistake.

## Build plan
1. `--local` flag, model switch, local limits, truncation and build checks, gates lifted locally, `wrong_proxy` on missing group, satisfies **AC-1** to **AC-6**
2. Self checks, satisfies **AC-7**
3. Rule file and AGENTS.md line, satisfies **AC-8**
4. Live probe, satisfies **AC-9**

## Consequences
**Positive**: client logs and transcripts can be summarized without using your Claude limit.
**Negative / tradeoffs**: slow; the laptop swaps while the model is loaded (A7), so it is never used while wf builds.
**Neutral**: `litellm.yaml` lives outside the repo and is not changed.
