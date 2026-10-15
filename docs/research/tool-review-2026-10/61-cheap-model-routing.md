# Row 61: routing easy work to cheaper / open models (2026-10-15)

## Today (from files)
- fb-ask: one text job (summarize, triage, extract, classify, commit-msg), no tools, to model group `fb-safe` via local LiteLLM on 127.0.0.1:4000. Exit 3/4 = do it with Claude. Refuses repos not on fb-ok.txt, text with private names, and any wf run call. Source: ~/claude-config/scripts/fb-ask.py (lines 1-35), ~/.claude/rules/cheap-worker.md, spec dir ~/claude-config/docs/specs/0023-cheap-worker-tier.
- claude-fb: Claude Code on the normal config with ANTHROPIC_BASE_URL=http://127.0.0.1:4000. "`fb-safe` (default) = Ollama Cloud gpt-oss:120b -> Groq openai/gpt-oss-120b. `fb-any` ... adds Gemini free then Mistral free." Free Ollama pool is one monthly pool (gemma4:31b, gpt-oss:120b/20b, nemotron). Source: ~/.claude/projects/-home-santiago--claude/memory/claude-fb-fallback.md (4 days old, not re-verified live).
- So routing already exists for text-in/text-out jobs. Missing: tool-using subagents and code edits on cheap models.

## (a) What Claude Code lets you route
- Subagent model order (verbatim): "The per-invocation model parameter / The subagent definition's model frontmatter, where inherit selects the main conversation's model / The CLAUDE_CODE_SUBAGENT_MODEL environment variable ... / The main conversation's model". Before v2.1.251 the env var came first. https://code.claude.com/docs/en/sub-agents
- Mods hook: `agent.spawn` "A subagent or an agent team teammate is about to start ... `next({ ...e, model })` to choose its model, or `{ deny: reason }`". Also `tool.call` can return `{ result }`, which lets a mod answer a tool call itself (e.g. call fb-ask and return its text). https://code.claude.com/docs/en/plugins/mods/reference
  - Limit (inferred, unverified): the model value is a Claude Code model name/alias. Docs I fetched say nothing about a per-subagent base URL, so a non-Claude subagent needs the whole process on a gateway.
- Gateway: ANTHROPIC_BASE_URL is per process. Docs page /llm-gateway could not be fetched (Firecrawl rate limit); gateway claims are unverified from the docs, but our own claude-fb proves it works with LiteLLM (memory file above).
- claude-code-router (CCR): MIT, 37,695 stars, last push 2026-10-10. "a local model gateway and control plane for coding agents ... one stable local endpoint ... routing rules". Routes per request by rules, so one session could send background/small calls elsewhere (rule names not verified; I only grepped the README). https://github.com/musistudio/claude-code-router , https://api.github.com/repos/musistudio/claude-code-router
- LiteLLM (we already run 1.101.0 pinned): can do the same with a custom model group; no per-task classifier built in (unverified).

## (b) Soup (MakazhanAlpamys/Soup)
- It is NOT a router. Verbatim: "Fine-tune and post-train LLMs in one command." Apache-2.0, 9,108 stars, 1,485 forks, 207 open issues, last push 2026-10-15, created 2026-02-20, Python, v0.76.0. https://github.com/MakazhanAlpamys/Soup , https://raw.githubusercontent.com/MakazhanAlpamys/Soup/main/README.md
- Models: any HF text-generation model (Llama 3.x/4, Qwen 2.5/3, Gemma 3, Mistral, DeepSeek, Phi-4); needs a GPU (8 GB+ VRAM for 7B QLoRA; layer streaming claims 8B on 4 GB, BETA).
- It has `soup serve` (OpenAI-compatible server) and an "Anthropic Messages endpoint" per its docs index, so it could serve a model you fine-tuned, but nothing in the README routes tasks. Use only if we later fine-tune our own small classifier/summarizer. Not relevant to saving the weekly limit now.

## (c) Which open models for which task
Evidence I could fetch: gpt-oss model card, https://arxiv.org/pdf/2508.10925 Table 3 (accuracy %, low/medium/high reasoning):
- gpt-oss-120b: SWE-Bench Verified 47.9 / 52.6 / 62.4; Aider Polyglot 24.0 / 34.2 / 44.4; Tau-Bench Retail 49.4 / 62.0 / 67.8; MMLU 85.9 / 88.0 / 90.0; GPQA 67.1 / 73.1 / 80.1.
- gpt-oss-20b: SWE-Bench Verified 37.4 / 53.2 / 60.7; MMLU 80.4 / 84.0 / 85.3.
- Reading: strong on knowledge/QA (MMLU 85.9+), so summarize/classify/extract are safe. Agentic coding (SWE-bench ~50-62) is a vendor number, mid-level; I did not fetch a Claude number to compare (unverified), so do not trust it for edits, review or architecture. Newer open coders (Qwen3-Coder, DeepSeek, Kimi, GLM) not benchmarked here: unverified, no sources fetched (search tool was rate limited).
- Rule of thumb supported by data: reading jobs yes, tool-using code edits no.

## Weekly limit: what routing saves, how to measure
- Savings only come from tokens Claude never sees. fb-ask on a 100k-char log saves that input plus output; a subagent on `model: haiku` still uses Claude quota (weight vs Opus not verified).
- Today's goal (per 00-current-setup.md) is to USE nearly all the weekly limit this week, so new routing now saves quota the user wants to spend. Value is mainly after the limit hits (claude-fb already covers that).
- Measure: (1) fb-ask calls and input chars (add a one-line log in fb-ask, not done: read-only task); (2) wf `call-NN.json` token fields per box, compare box types (field names unverified, check a file); (3) /usage weekly % before and after a week with fb-ask on versus a week without. One week is noisy; use per-job token counts.

## Recommendation: ADAPT (small), reject Soup
- Reject Soup: wrong product (training tool), GPU needed.
- Reject adopting CCR or a mod now: the heavy part (non-Claude model on tool-using subagents) is where quality drops (SWE-bench ~50-62, our own rule says no code edits) and a whole-process gateway swap breaks the Claude-native setup.
- Adapt: (1) widen fb-ask use through habit and a few skill call sites for big-input reads (logs, transcripts, review reports): ~1 hour, no cost. (2) Pin `model: haiku` or sonnet on read-only agents (scout, researcher, Explore) via frontmatter: minutes, saves Claude quota per subagent (weight unverified). (3) Optional later: a ~30-line `agent.spawn` mod that sets haiku for named read-only agents; only if frontmatter proves too manual; ~2 hours incl. skillspector scan.
- Build our own only after measuring: if fb-ask logs show many calls, add a `tool.call` mod to auto-route. Cost low, but not before data.
