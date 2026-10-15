# Row 59: memory setup for Claude Code (2026-10-15)

## Facts (GitHub API 2026-10-15 unless noted)
| Tool | Stars | Last push | License |
|---|---|---|---|
| claude-mem (thedotmack) | 101k | 2026-10-15 | Apache-2.0 |
| MemPalace/mempalace | 59.6k (836 open issues) | 2026-10-15 | MIT |
| Graphify-Labs/graphify | 126.9k (1517 open issues) | 2026-10-14 | Apache-2.0 |
| PleasePrompto/notebooklm-mcp | 3.4k | 2026-09-10, ARCHIVED | MIT |

Sources: https://api.github.com/repos/thedotmack/claude-mem , /repos/MemPalace/mempalace , /repos/Graphify-Labs/graphify , /repos/PleasePrompto/notebooklm-mcp

## claude-mem: paid vs free
- Free: "The local claude-mem engine is open source. CMEM Pro is the paid hosted observation and cloud sync service." (https://claude-mem.ai)
- Paid: "CMEM Pro: Hosted observation, cloud sync, and your private MCP link. 30 Day Free Trial. Then $30/month." Same page.
- README: sign-in "unlocks the claude-mem observer with a 30 Day Free Trial: memory runs off-plan... When the free trial ends, memory automatically falls back to your Anthropic plan unless you subscribe." (https://github.com/thedotmack/claude-mem README)
- Cost trap (local memory file token-diet-2026-09): the observer ran on the user's Claude quota, then paid Gemini cost ~20k COP. Free mode is not free in tokens: a background model summarizes every tool call.
- Recall: 3 layers, "search ... ~50-100 tokens/result", "get_observations ... ~500-1,000 tokens/result", "~10x token savings" (README, the project's own claim, unverified).
- Privacy: local SQLite + Chroma; `<private>` tags exclude content; cloud sync is optional and sends data to cmem.ai.
- Lost by disabling: automatic capture of every session's decisions and searchable history across repos. Replaced partly by auto-memory files, briefs, scope rows, /rollover. Disabled since 2026-10-01 (jsm-workflow-adoption.md); the "ask around 2026-10-08" follow-up is overdue.

## MemPalace
- README: "Local-first AI memory. Verbatim storage, pluggable backend, 96.6% R@5 raw on LongMemEval - zero API calls." Default ChromaDB; MCP server; auto-save hooks for Claude Code; `mempalace mine ~/.claude/projects/ --mode convos`. (https://github.com/MemPalace/mempalace)
- Warning in README: "Claude Code sessions expire in 30 days without auto-save hooks wired."
- Benchmark claims disputed on HN: "Milla Jovovich's MemPalace Claims 100% on LoCoMo. Its Benchmarks.md Disagrees" (https://news.ycombinator.com/item?id=47673538). Celebrity-launched, young (created 2026-04-05). 836 open issues.
- Stores conversations verbatim, not code understanding. Fully local; embeddings local unless you set an external endpoint.

## graphify (installed)
- SKILL.md: code/docs/papers/images/video into a knowledge graph; `/graphify query|path|explain`; fast path reads graphify-out/graph.json if present.
- README: "Code is parsed with tree-sitter AST: deterministic, no LLM, nothing leaves your machine. (Docs, PDFs, images and video use your assistant's model...)" "Not a vector index." (https://github.com/Graphify-Labs/graphify)
- It is code/document memory, not session memory. Upsell: Graphify Cloud (14-day trial).

## NotebookLM claims check
Claim: "create a free notebook" - TRUE, free plan exists. Limits (third party, not Google): 100 notebooks, 50 sources each, 50 chat queries/day, 3 audio and 3 video overviews/day (https://elephas.app/blog/notebooklm-source-limits). Unverified against Google.
Claim: "connect with the free notebooklm-mcp server" - FALSE as stated for the popular one: PleasePrompto/notebooklm-mcp README: "This project is no longer maintained. As of September 2026 the repository is archived... It may stop working when the upstream services change." Other tools (notebooklm-py, qiaomu-anything-to-notebooklm 6.2k stars) exist, all unofficial.
How it works: "It drives a real Chrome via Patchright (stealth + persistent fingerprint)", Google login cookies kept in a local Chrome profile ("no encrypted credential store"). Browser automation, not an official API. Official NotebookLM Enterprise API exists but is alpha and paid (search summary, https://pkg.go.dev/github.com/LocalKinAI/notebooklm-go). Google ToS: no Google statement found (unverified); other clients say "High-volume / commercial scraping likely violates Google's Terms of Service." Risks: undocumented endpoints break, cookie risk to your main Google account.
Claim: "wrap up skill saves each session" - feasible (a skill that uploads text as a source), but uploads each session's text to Google. UNVERIFIED that sources can be added unattended reliably.
Claim: "routing rule in CLAUDE.md to check notebook first" - feasible, but adds a slow browser round trip (seconds to minutes) before work and spends the 50/day query cap.
Claim: "next session pulls what it needs by semantic search" - PARTLY TRUE: NotebookLM does retrieval over sources, but it answers via Gemini and returns prose, not exact records.
Claim: "lower token cost" - UNVERIFIED/doubtful: answers are cheap in Claude tokens, but every call is an MCP browser call plus the answer text; claude-mem/MemPalace do the same locally with fewer moving parts.
Claim: "answers only from saved sessions" - TRUE by NotebookLM design (grounded in sources) but Gemini can still misquote; no exact-match guarantee.
Claim: "free infographics and video overviews" - PARTLY TRUE: Audio and video overviews are free with a daily cap (3/day per elephas); infographics unverified. Irrelevant for memory.
Privacy: all session text goes to Google. Violates the rule that client/work repos must not leak (work-org etc.). Reject for those repos.

## Comparison
| | claude-mem | MemPalace | graphify | NotebookLM MCP |
|---|---|---|---|---|
| Day to day | automatic hooks, search tools | hooks + mine + MCP | manual /graphify, query | manual wrap-up skill, browser |
| Token cost/session | observer model on every tool call (the 2026-09 cost problem); recall cheap | no LLM, local embeddings; recall cheap | build free for code; query small | low Claude, but quota 50/day |
| Memory quality | LLM summaries, may drop detail | verbatim, good retrieval, disputed benchmark claims | n/a (no sessions) | Gemini prose |
| Code understanding | no | no | yes (AST, ~40 languages) | no |
| Privacy | local; cloud opt-in | local | local for code | all to Google |
| Maintenance | active, Bun+Chroma worker, bugs seen | active, 836 issues | active | archived, fragile |

## Recommendation
- NotebookLM second brain: REJECT (archived server, browser automation, data to Google, ToS unclear, daily caps).
- Keep graphify for code, public/own repos. Already installed; cost 0; run per repo when needed. ADOPT as is.
- Session memory: ADAPT, do not add a new tool yet. Our auto-memory + briefs + /rollover already cover decisions; the gap is searching old transcripts. Cheapest fix: trial MemPalace locally on own/freelance repos only (`mempalace mine ~/.claude/projects/ --mode convos --wing <repo>`), no LLM cost, measure for 2 weeks. Effort ~1-2 hours; scan with skillspector first (not installed). Keep claude-mem disabled (observer token cost was the pain; Pro is $30/month and sends data to cmem.ai). Exclude work/client project folders from mining.
- Not both MemPalace and graphify at once as a "stack": different jobs (sessions vs code); fine to run both, but add MemPalace only after trial.
- Build our own: not worth it unless the trial fails.
