# Research gap fill 66 (2026-10-15)

Tools: curl + r.jina.ai, exa, tavily, GitHub API. Firecrawl not used. Quotes verbatim from fetched text.

## 1. NotebookLM (now branded "Gemini Notebook")
Sources: support.google.com/notebooklm/answer/16213268, /16269187, /16164461; docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise.

Limits (Upgrade page, "Usage Limits (Subject to Change)"):
| Tier | Notebooks | Sources/notebook | Chats/day |
| Standard (free, gmail) | 100 | 50 | 50 |
| Plus (Google AI Plus) | 200 | 100 | 200 |
| Pro (Google AI Pro) | 500 | 300 | 500 |
| Ultra 20TB / 30TB | 500 | 500 / 600 | 2.5K / 5K |
FAQ: "Get 100 notebooks, with up to 50 sources each and 500,000 words each. Have daily limits of 50 chat queries and 3 audio generations." Per source: "500,000 words per source or up to 200MB for local uploads."
Data use: "Your data is protected, and is not used to train Gemini Notebook unless you provide feedback. When you share feedback to help us improve, we may review the full context of that interaction, including your queries, uploads, and the model's responses." Workspace: "will not be reviewed by human reviewers, and will not be used to train AI models."
Grounding: "If the answer isn't in the source material, it won't provide a response." Retrieval: "retrieves the most relevant information based on your question first, then builds a response" (RAG, not full-context).
Official API: only Gemini Notebook Enterprise (Google Cloud, Discovery Engine API v1alpha: notebooks.create/get/share, notebooks.sources.batchCreate/uploadFile; sources API is "Pre-GA", billing required). Consumer app: no official API found, no official MCP found.

Social-post claims:
- Persistent memory across sessions: PARTLY. Notebooks persist, but it is a source store you must feed; nothing writes sessions into it automatically.
- Lower token cost: PLAUSIBLE, unverified. Retrieval happens on Google's side; Claude only gets the answer. Not documented by Google.
- Answers only from saved sessions: PARTLY. Answers only from sources you uploaded; 50 source cap free.
- Free and open source: WRONG for NotebookLM (closed Google service, free tier capped). TRUE only for community MCP wrappers (MIT).
- Minutes to set up: wrappers need a Chrome login to Google and drive the web UI or reverse-engineered RPC; the repos say "No official API". Account/ToS risk: unverified.

Maintained NotebookLM MCP servers (GitHub API, 2026-10-15):
- jacob-bd/gemini-notebook-mcp-cli (formerly notebooklm-mcp-cli): 6319 stars, pushed 2026-10-15, active, CLI + MCP, 53 tools (README warns context cost).
- teng-lin/notebooklm-py: 19750 stars, pushed 2026-10-15 (Python client lib that several servers wrap).
- roomi-fields/notebooklm-mcp: 195 stars, pushed 2026-09-04, REST + MCP.
- julianoczkowski/notebooklm-mcp-2026: 18 stars, pushed 2026-07-26.
- PleasePrompto/notebooklm-mcp: 3436 stars, ARCHIVED, last push 2026-09-10 (do not use).
- Tiny/stale: Cezial 1 star (07-03), rinaldops 0 (06-27), mulyg 1 (03-31), wangjing0 3 (03-03).

## 2. MemPalace
Repo MemPalace/mempalace, MIT, 59584 stars, v3.11.0 released 2026-10-14 (3.10.0 09-16, 3.9.0 08-31), last push 2026-10-15, 836 open issues. README: "stores your conversation history as verbatim text and retrieves it with semantic search. It does not summarize, extract, or paraphrase." Structure: wings/rooms/drawers. Default backend ChromaDB (embedded), others sqlite_exact, rust_exact, milvus, qdrant, pgvector. "Nothing leaves your machine unless you opt in." Embedding model downloaded on first use (~80 MB minilm).
Claude Code: MCP server (stdio, also Docker), `mempalace mine ~/.claude/projects/ --mode convos`, auto-save hooks "for Claude Code, Codex CLI, and Cursor IDE", skills via `npx skills add MemPalace/mempalace`. Benchmark claim: "96.6% R@5 raw on LongMemEval" (self-reported, repo-reproducible).
Security: SECURITY.md exists, GitHub private vuln reporting. Open PRs still pending: #893 "harden hooks, MCP server, and config (security audit)", #1066 "fix 7 audit findings (MCP server, hooks, CI)", #1437 "pre-ingest redaction for transcript auto-indexing" (so secrets in transcripts are indexed verbatim today). Closed: #812 "Security hook injection fix". Its docs warn the separate Chroma HTTP server has unfixed CVE-2026-45829/45833/45830/45831; not applicable to the embedded client.
Verdict on 2-week trial: CONFIRMED, with changes (below).

## 3. Gateways / ANTHROPIC_BASE_URL
code.claude.com/docs/en/llm-gateway: "Any gateway that exposes a supported API format works. Anthropic doesn't endorse, maintain, or audit third-party gateway products, and doesn't support routing Claude Code to non-Claude models through any gateway." "Setting only that variable [ANTHROPIC_BASE_URL], without a gateway credential, doesn't replace the subscription. Requests still route through the gateway, but a saved claude.ai login remains the active credential." With a gateway credential variable or apiKeyHelper active: "the subscription's usage limits don't apply... billed per token". `allowedProviders: ["customEndpoint"]` pins gateway (v2.1.285+). Related pages: gateways, claude-apps-gateway (Anthropic's own gateway), llm-gateway-connect, -rollout, -protocol.
claude-code-router (musistudio): MIT, 37695 stars, not archived, pushed 2026-10-10, v3.1.3 on 2026-10-09 (v3 rewrite with UI, request logs, cost estimates). Supports OpenAI, Anthropic, Gemini, OpenRouter, DeepSeek, etc.

## 4. Self-improving agents
- SWE-agent (20575 stars, MIT, active): records `<instance_id>.traj` JSON of (thought, action, observation, state, query) per step. Does not learn across runs; trajectories are output for analysis/replay.
- OpenHands (91001 stars, MIT, active): event stream, conversation persisted to `persistence_dir`; static skills/microagents (repo.md, AGENTS.md, keyword triggered) are human-authored context. No automatic cross-run learning found.
- Claude Code `/insights`: exists. Docs: "Generate an HTML report analyzing your recent sessions on this machine... features to try. Not available in cloud sessions." Third-party teardown (zolkos.com, not official): reads ~/.claude/projects, caches facets in ~/.claude/usage-data/facets, up to 50 new sessions per run, Haiku, report at ~/.claude/usage-data/report.html, suggests CLAUDE.md rules. It reports; it does not auto-apply.
- Papers: Darwin Godel Machine arXiv 2505.22954 (agent rewrites own code, SWE-bench 20.0% to 50.0%); ExpeL arXiv 2308.10144 (insights + retrieved successful trajectories, no weight updates); Trajectory-Informed Memory Generation arXiv 2603.10600 (strategy/recovery/optimization tips, up to +14.3 pp on AppWorld held-out); ERL arXiv 2603.24639 (+7.8% Gaia2). Survey (2026): evidence best for "fixed experience reuse, chiefly on tasks with tests"; sustained improvement evidence "remains partial". CTIM-Rover: more memory can hurt.

## 5. Skill scanners
- NVIDIA SkillSpector (NVIDIA/SkillSpector): Apache-2.0, 20300 stars, v2.12.0, pushed 2026-10-15. Static checks (22 analyzers, YARA, SARIF) plus optional LLM. CLAUDE LOGIN QUESTION: YES. DEVELOPMENT.md: "CLI providers (`claude_cli`, `gemini_cli`, `opencode_cli`): ... work with no API key". Needs `claude` CLI installed and logged in; set SKILLSPECTOR_PROVIDER=claude_cli (exact env value per docs; not run). Default provider is nv_build (NVIDIA key). `--no-llm` for static only. Note the scanned skill text goes into the LLM prompt (injection risk; code keeps CRITICAL/HIGH findings even if the LLM denies them).
- Snyk Agent Scan (snyk/agent-scan): Apache-2.0, 3139 stars, active. Auto-discovers Claude Code/Cursor etc. MCP servers and skills; checks prompt injection, tool poisoning, tool shadowing, toxic flows, malware payloads, credential handling, hardcoded secrets. CLI free (`uvx`); README notes a background/MDM mode reporting to Snyk Evo (contact sales). Whether the scan sends skill content to Snyk's API: not confirmed from fetched text; check before running.
- Cisco skill-scanner (cisco-ai-defense/skill-scanner): PyPI Apache-2.0 (GitHub shows NOASSERTION), 2604 stars, v2.3.0, active. YAML+YARA, AST/dataflow, optional LLM judge (`--use-llm`, needs key/model), optional VirusTotal, OSV.dev, Cisco AI Defense (paid cloud). Free core.
- Also installed here: sentry-skills:skill-scanner (not researched).
