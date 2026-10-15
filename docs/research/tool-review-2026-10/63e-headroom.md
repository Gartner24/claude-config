# Headroom (headroomlabs-ai/headroom) - research, 2026-10-15

Source: shallow clone at scratchpad/clones/headroom (HEAD dated Thu Oct 15 2026), read only, nothing run.

## What it is
Local proxy/library that compresses "tool outputs, logs, RAG chunks, files, and conversation history" before the LLM (README). Python + Rust core, Apache 2.0, pip/uv/npm/docker.
Pieces: SmartCrusher (JSON), CodeCompressor (AST), Kompress-v2-base (HF text model, ONNX), CCR (originals cached locally, model calls `headroom_retrieve`), cross-agent memory, `headroom learn` (writes CLAUDE.local.md), optional output shaper.

## How it saves tokens
- Compression of NEW tool output only ("Live-zone compression - only new bytes are compressed... The frozen prefix stays byte-identical, so the provider cache survives, and history is never dropped").
- Source code mostly passes through (limitations.mdx: "Source code -- passes through unchanged"; recent 4 messages and anything when prompt says analyze/review/fix/debug are protected). System prompts untouched. Images not compressed. grep results not compressed.
- Output shaper (off by default, HEADROOM_OUTPUT_SHAPER=1): appends "be terse" note to END of system prompt, lowers thinking effort on tool-result turns. Estimated (counterfactual) savings only.
- Opt-in model router (rewrites model to a cheaper one) - off by default.

## Claimed savings and independence
README proof table (own benchmark, `benchmarks/index_proof_table.py`, seeded, synthetic MCP-style payloads): 21% code search, 57% SRE incident, 42% codebase exploration, 30% issue triage. Accuracy table N=100 (GSM8K 0.870 vs 0.870; TruthfulQA 0.530 vs 0.560 "no detectable difference"). All self-run; no independent benchmark found. limitations.mdx itself says: "The compression figures below are not from a published, repeatable benchmark suite -- we could not trace a prior version of this table to one." and agentic conversations: "Not independently measured for this page". "Skip it if ... Short conversational exchanges, prose, and already-dense payloads see little or no reduction."
Savings scale with repetitive JSON/logs; Claude Code sessions are mostly code reads/edits (passthrough), so expect low.

## Hook-in and what it changes
- `headroom wrap claude`: starts local proxy (default port 8787), launches claude with ANTHROPIC_BASE_URL=http://127.0.0.1:<port> and ENABLE_TOOL_SEARCH=true. Registers Serena MCP in ~/.claude.json (local scope per project, or user scope) by default; `--code-memory none` skips. Can write .claude/settings.local.json (--project-settings), a SessionStart self-heal hook in settings.json, and env block in ~/.claude/settings.json for `headroom install`. `headroom unwrap claude` reverts. Wrap code reads/writes settings.json and settings.local.json (wrap.py).
- `headroom mcp install`: MCP server with headroom_compress / headroom_retrieve / headroom_stats.
- Alternative: run `ANTHROPIC_BASE_URL=http://localhost:8787 claude` by hand, no file edits.

## What it sees
Everything: the proxy sits on every request/response, including OAuth bearer tokens in headers (forwarded upstream). Compression is local ("no prompt or file content is sent anywhere to be compressed"). Logs: ~/.headroom/logs/proxy-<port>.log; `--log-messages` and `--log-file` JSONL can store full content (off by default; docs warn logs "can hold request and response" content). CCR store keeps originals locally. Optional HEADROOM_KOMPRESS_ENDPOINT = real egress (unset by default).

## Telemetry
- Upload beacon ON by default: telemetry/beacon.py `BEACON_DEFAULT_ON = True`, "fail-open: an unrecognized value uploads". Schema v2 payload: counters, ratios, skip reasons, provider+model ids, OS/arch, cache behaviour, session shape, harness and configuration; random per-install UUID (not hardware derived). Claims never prompts/code/paths (server allowlist).
- Off: `HEADROOM_BEACON=off`, `DO_NOT_TRACK=1`, or `HEADROOM_OFFLINE=1` (air-gap, also stops update check, downloads). Inspect: `headroom telemetry --show`.
- Also: daily PyPI update check (HEADROOM_UPDATE_CHECK=off), model downloads from huggingface.co, cdn.pyke.io.
- HEADROOM_TELEMETRY (local /stats) off by default.

## Subscription login and `claude -p`
- Docs say tool-search deferral works "(both streaming and non-streaming, subscription and API-key auth)". Proxy forwards the auth header; Remote Control gate is the known casualty: Claude Code 2.1.196+ disables `/remote-control` when ANTHROPIC_BASE_URL is not api.anthropic.com; server-managed settings are also skipped; 1M window and tool deferral gated by the same base-URL check (Headroom restores via `--1m` / `_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL`, ENABLE_TOOL_SEARCH). For a 1M-context user this matters: must use `--1m` (default model fallback claude-opus-5).
- `claude -p`: `headroom wrap claude -- -p` is documented in help text; also `wrap --project-settings` exists so daemon-spawned Claude workers inherit the base URL. Not independently verified by me. Unattended runner would need the proxy running as a persistent service (`headroom install`).
- Not verified: whether Anthropic's terms allow routing subscription OAuth through a third-party local proxy; it is a loopback hop to api.anthropic.com, but unconfirmed.

## Prompt cache compatibility (critical)
Default `--mode cache`: compress only newest delta, replay prior turns byte-for-byte. But CHANGELOG (Unreleased, fixed) records a real bug: "reported as ~4.4x cache-creation inflation and a 2.5-3x net cost increase under Claude Code" caused by parallel subagents sharing one prefix tracker (#2085). Fixed in unreleased; so released versions may still have it. For a subscription limit, cache misses on a 1M-context session are the single biggest way to burn the week. Also the verbosity note is appended at END of system prompt (claimed cache-safe).

## Quality risk
Lossy compression of tool results (JSON arrays sampled, "adaptive K", up to 15 items kept; errors/outliers always kept), model told it can call headroom_retrieve. Risk: model misses an omitted row; extra retrieve round trips. Output shaper "terse" + lower effort can degrade reasoning on routine steps. TruthfulQA etc. are not agentic-coding evals. Prompt-injection note: retrieved content is data.

## Interaction with this setup
Skills/rules/hooks text is system-prompt/prefix: not compressed (system prompts preserved). So the fixed per-session overhead (rules, skills list) gets no savings; savings only on big tool outputs (logs, JSON, MCP results). Context monitor hook sees a smaller context, which may confuse thresholds.

## Maintenance
Very active: huge CHANGELOG, many issue numbers (>2000), Discord, Trendshift. Commercial company (Enterprise tier, perks banner) - open-core; OSS stays Apache 2.0. Large, fast-moving code (wrap.py > 9000 lines) = more surface for breakage. Native wheels macOS ARM + Linux.

## License
Apache 2.0.

## Comparable tools
- Claude Code native: auto-compact, /compact, prompt caching, tool search (built in), subagents for output isolation.
- Caveman / Ponytail style output trimming (README itself recommends Ponytail, Serena, Graphify, Caveman as companions).
- RTK-style CLI output filters (hook-based, no proxy) - not checked here.
- Hosted: Compresr, The Token Company (text sent to their API; README comparison). OpenAI compaction.
- Cheapest equivalent with no proxy: hooks/wrappers that trim command output before it enters context.

## Verdict on the weekly-limit goal
This week's goal is to use almost the whole weekly limit; token saving works against that goal, and Headroom adds risk (proxy on every request, base-URL gates, cache-bust bug history) with likely low gain on code-heavy sessions. Fits "later", when the limit becomes the constraint. Not this week.

## Safe trial (later)
1. Never install into ~/.claude. Separate venv/uv tool, pinned version, not [all].
2. Set HEADROOM_BEACON=off and DO_NOT_TRACK=1 (or HEADROOM_OFFLINE=1 after models are downloaded) before first run; no --log-messages.
3. Do not use `headroom wrap` or `install` first (they edit ~/.claude.json, settings.json). Use env only: `ANTHROPIC_BASE_URL=http://127.0.0.1:8787 ENABLE_TOOL_SEARCH=true claude` in a scratch repo; with `--code-memory none` if wrapping.
4. Check `/context`, `headroom perf`, and cache_read vs cache_creation tokens on 2-3 sessions before/after; abort if cache creation rises.
5. Test `claude -p` once with a trivial prompt; confirm subscription login works and 1M still works (`--1m`).
6. Leave the unattended runner off the proxy until a week of interactive data is clean.
