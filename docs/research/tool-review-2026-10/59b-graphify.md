# graphify research (2026-10-15)

Verification key: [curl] = text fetched raw and grep-matched; [api] = GitHub/PyPI JSON; [snippet] = from a search-engine excerpt only, not re-fetched (unverified wording); [inferred] = my reading.

## Verdict

Install is already done (pipx, CLI at ~/.local/bin/graphify; skill 0.9.53 vs PyPI 0.9.91, so stale). Do not wire it in as an always-on tool. Build code-only graphs on 1-2 big repos as an experiment, with a hard A/B test first. Independent evidence says agents rarely use it and it does not beat grep on cost. Never run it on client/work repos until the cloud-backend footgun (issue 4361) is neutralised.

## 1. What it is

- Apache-2.0 [api]. Org Graphify-Labs, repo created 2026-04-03, last push 2026-10-14, ~127k stars, 1,517 open issues, not archived [api]. YC S26 company with a paid "Graphify Cloud" upsell (README banner) [curl].
- PyPI `graphifyy` 0.9.91 (2026-10-14); 259 releases since 2026-04-04, 3 releases in the last 2 days, each "N community pull requests" [api]. Extremely active, high churn; every release bumps the AST cache schema so first build after upgrade re-extracts [api].
- Does: tree-sitter AST over ~40 languages -> NetworkX graph (calls/imports/inherits), Leiden communities, god nodes, `query` / `path` / `explain` CLI, outputs graph.json, GRAPH_REPORT.md, graph.html. Optional semantic LLM pass on docs/PDF/images/video. Edges tagged EXTRACTED / INFERRED. No vectors [curl README].
- Issue themes [api search, titles]: security hardening (#3868 unbounded edge allocation DoS, #3869 core.hooksPath redirect (closed), #3844 skill code injection (closed), #3442 unsanitized text in skill instructions, #2658 pypdf DoS advisories, #4259 CVE request for GHSA-pcc4-rvhr-2pr8, #2011 private vuln reporting returns HTTP 500, #2007 SECURITY.md out of sync with code); privacy (#4361, #2781 below); per-language extraction bugs (C#, SQL, PHP, Java...); "no value over plain Claude Code" (#985).
- Quality concern [inferred]: very fast merge cadence of community PRs plus 1.5k open issues; SECURITY.md was found inconsistent with README on network calls (#2781 body).

## 2. Setup and freshness

- Build: `/graphify .` in the skill (code-only corpus: AST, no subagents) or headless `graphify extract . --code-only` [curl README privacy section]. Output `graphify-out/` in repo root (graph.json, GRAPH_REPORT.md, graph.html, cache/, cost.json, manifest) [curl README + SKILL.md].
- Fresh: `graphify hook install` = git hooks after commit and branch checkout, background; run `graphify update .` after pull/merge; `graphify watch .` needs `watch` extra [curl docs incremental-updates.md]. Skill reference says hook ignores docs/images changes, only code [curl local hooks.md].
- `graphify claude install` writes a `## graphify` section to CLAUDE.md and a PreToolUse hook that nudges Claude toward the graph before search/Read [curl README + local hooks.md]. It is a nudge, not a block.
- MCP: optional extra `graphifyy[mcp]`, `--mcp` stdio server [curl README].
- Gitignore: upstream recommends COMMITTING graphify-out/ for teams, but keep `cost.json` out and optionally `cache/` [curl docs team-workflows]. For your public repo claude-config and any client/work repo: gitignore it (it is source-derived and could embed paths/names; matches your scan-before-push rule) [inferred]. One graph per worktree: set GRAPHIFY_OUT [curl docs].
- Size: "couple of megabytes of JSON" per mejba blog [snippet]; ERPNext 1M LOC = 22,620 nodes / 48,710 edges [curl BENCHMARKS.md]. FastAPI build in Constantin's test was done with a semantic pass costing 3.8M input tokens [snippet, verified file contains the blog; token number not re-grepped]. Not measured by me.

## 3. Cost

- Code AST: zero model tokens, no key [curl README, BENCHMARKS.md "Graph build LLM credits 0"].
- Model tokens only for docs/PDF/images (via your Claude session subagents, or an API key if headless). Video/audio transcribed locally with faster-whisper [curl README].
- Queries: ~2K tokens per `graphify query` call per issue #985 reporter [snippet]. Queries use the session model only as the consumer; the traversal itself is local.
- Fit with "use the weekly limit": it consumes none for code-only builds, so it is free to try; but independent tests show it adds input tokens at query time (below). A docs semantic pass would burn weekly limit through subagents; skip it.
- Gotcha [inferred from SKILL.md]: the skill instructs the host to dispatch general-purpose subagents for any doc/paper/image; only code-only skips this. Use headless `--code-only` to be sure.

## 4. Privacy

- README [curl]: "Code files: processed locally via tree-sitter. Nothing leaves your machine." "No telemetry, no usage tracking, no analytics." Query logging goes to local `~/.cache/graphify-queries.log` (question text, nodes returned); disable with `GRAPHIFY_QUERY_LOG_DISABLE=1`.
- Cloud upsell is only a marketing banner plus a separate paid product; nothing in the OSS README says it phones home [curl README]. I did not read the source or run the CLI, so "no network calls" is a README claim, not verified [unverified].
- Footguns [api]:
  - #4361 (open): headless `extract`/labeling auto-picks a cloud backend from ambient API keys in order gemini, kimi, claude, openai, deepseek, azure, bedrock (AWS_PROFILE/REGION), ollama; labeling falls back to `claude -p` when `claude` is on PATH; no confirmation prompt. Workarounds listed by reporter: explicit local backend, `--code-only` without `--dedup-llm`, `cluster-only --no-label`.
  - #2781 (open): semantic pass sends raw doc text (including .yaml/.yml) to the backend with no secret redaction.
  - Kimi routes to Moonshot servers in China [curl README].
- Safe for client/work repos only if ALL hold: `--code-only`, `--no-label` or no cloud keys/claude on PATH in that shell (env -i or unset GEMINI/ANTHROPIC/OPENAI/AWS vars), no `--dedup-llm`, query log disabled, graphify-out gitignored. The Claude Code session itself still reads graph output into the model, but that is the same exposure as Claude reading the code. Work repos "must never send code off machine": the Claude session already does that for any tool use, so the real question for you is only graphify's own egress; run it with network denied (e.g. `unshare -n` or a firewall rule) as a proof [inferred suggestion].

## 5. How Claude uses it, and evidence

- Mechanisms: `/graphify query|path|explain` (skill), CLI called via Bash, optional MCP, plus CLAUDE.md section and PreToolUse nudge hook [curl README].
- Independent evidence is poor:
  - Constantin Ponfick, FastAPI, 12 questions, with vs without: time +9.2%, total input +49.5%, cost +9.5%, files inspected -14.6%, tool calls -8.6%; agent still grepped/read source after every graph query; verdict "not yet a convincing yes" [curl, blog constantinsblog.eu 2026-09-15; two quote lines grep-confirmed].
  - rentierdigital (DEV, 2026-05-18): 60 sessions on 2 production projects, ~1,500 hook reminders, graph invoked 0 times; "grep won the arbitrage every single time"; says it may win on an unfamiliar inherited repo [curl, line "invoked the graph exactly 0 times" confirmed].
  - r/ClaudeCode thread: "I have never seen the agents actually query the built graph even once" [snippet].
  - Reddit 5-tool benchmark (2026-08-08): graphify -8.9% output tokens vs no tools (p=0.003), but under Claude Code "most of these tools were barely called at all" [snippet; Codex run].
  - Issue #985 (inside the project): .NET monorepo A/B, graphify MCP 1.6-1.9x more costly with weaker answers than plain code agent [snippet].
  - Vendor: ERPNext (1M LOC) n=6 questions, coverage 82.0% vs 70.8% grep baseline, ~140K tokens/query, self-run on their harness [curl BENCHMARKS.md]. "71.5x" compares full corpus to subgraph, mixed docs/images corpus; on pure code mejba estimates 5-10x [snippet].
  - Positive anecdote: mejba found a billing/notification circular dependency via communities; best for onboarding into unknown repos and architecture review [snippet, practitioner blog, seems promotional ("Point me at the repo")].
- Net: structural/overview value is real; "cheaper than grep" is not shown. Agents default to grep unless a hook blocks it.

## 6. Overlap with your setup

- Claude Code Grep/Glob/Read + Explore agent: cover "where is X / who calls Y" better for exact strings; graph adds multi-hop `path` and communities. [inferred + sources above]
- LSP tool (deferred, available): gives compiler-accurate references/definitions on demand with no index to go stale; graphify's AST resolution is heuristic with INFERRED edges (#2948 requests an LSP layer, not shipped) [api].
- scout agent (read-only repo scan returning a compact map) and /scope brownfield scan: already produce the "map" use case per task; graph GRAPH_REPORT.md duplicates that persistently but needs refreshing. [inferred from agent list]
- codemaps (doc-updater, docs/CODEMAPS): prose architecture maps, human-reviewed and git-tracked; GRAPH_REPORT.md is auto-generated and less curated. Overlap is highest here. [inferred]
- MemPalace trial: separate (session memory). graphify's "query log" and `save-result` feedback are not a memory replacement. [inferred]
- Your hook SHAPE rule blocks chained Bash; graphify skill steps use `$(cat ...)` inline python, which your hook rejects (seen this session on similar commands), so the skill's multi-step flow will need CLI mode (`graphify extract`, `graphify query`) rather than the skill's inline blocks [inferred].

## 7. Recommendation

Repos: one own repo that is large and unfamiliar-ish (a mixed TS/Python app under ~/projects with >20k LOC). Skip claude-config (shell/markdown, mostly non-code; doc semantic pass would burn limit; public repo leakage risk). Skip freelance and work repos for now (egress footguns, no proven gain).

Steps (CLI only, code-only, nothing in repo committed):
1. `pipx upgrade graphifyy` (skill is 0.9.53, PyPI is 0.9.91; churn is daily, pin the version after).
2. In a scratch clone or worktree of the chosen repo: `GRAPHIFY_QUERY_LOG_DISABLE=1 env -u GEMINI_API_KEY -u GOOGLE_API_KEY -u ANTHROPIC_API_KEY -u OPENAI_API_KEY graphify extract . --code-only`. Add `graphify-out/` to the global gitignore.
3. Read GRAPH_REPORT.md (god nodes, communities), try `graphify explain` and `path` yourself.
4. Do NOT run `graphify claude install` or the hook yet; the nudge hook was ignored in tests. Instead, for the test, tell Claude in the prompt to use `graphify query/path` first.
5. A/B test: 8-10 real questions (3 exact lookups, 4 cross-cutting "what breaks if I change X", 3 onboarding "how does Y flow"). Run each in a fresh session with and without graph; record total input tokens (from the transcript jsonl), tool calls, time, and grade answers 0-2 against the code. Adopt only if cross-cutting questions win on quality or tokens by >25% and the agent actually calls graphify without a nag.
6. If it wins: `graphify hook install` for freshness (code-only, local) and add one CLAUDE.md line for that repo only. If it loses, `pipx uninstall graphifyy` and remove ~/.claude/skills/graphify (the 41 KB SKILL.md also costs name/description context).

## Sources
- https://github.com/Graphify-Labs/graphify (README, BENCHMARKS.md, SECURITY.md fetched via curl 2026-10-15)
- https://api.github.com/repos/Graphify-Labs/graphify (+ /releases, /issues, issues 4361, 2781, search)
- https://pypi.org/pypi/graphifyy/json
- https://docs.graphify.com/guides/team-workflows, /guides/incremental-updates.md
- https://constantinsblog.eu/posts/graphify-llm-query-tool/
- https://dev.to/rentierdigital/i-installed-a-knowledge-graph-on-claude-code-14-days-later-the-audit-killed-my-enthusiasm-1p1n
- https://www.mejba.me/blog/graphify-knowledge-graph-codebase-claude-code (snippet only)
- https://www.reddit.com/r/ClaudeCode/comments/1tlbog1/are_tools_like_graphify_actually_placeboshype/ (snippet only)
- https://www.reddit.com/r/ClaudeCode/comments/1vilwwm/i_benchmarked_5_token_saving_tools_across_codex/ (snippet only)
- https://github.com/Graphify-Labs/graphify/issues/985, /4361, /2781
- https://news.ycombinator.com/item?id=49301201 (snippet; a competitor's comment, biased)
- Local: ~/.claude/skills/graphify/SKILL.md, references/hooks.md, references/add-watch.md, .graphify_version (0.9.53)

Not done: did not run the graphify CLI, did not read its source, did not verify "no network" beyond docs.
