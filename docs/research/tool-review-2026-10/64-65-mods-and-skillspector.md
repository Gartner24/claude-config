# Rows 64 and 65: three "mods" and NVIDIA SkillSpector (2026-10-15)

Sources: setup file 00-current-setup.md; docs https://code.claude.com/docs/en/model-config.md ; changelog https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md ; bundled skill /tmp/claude-1000/bundled-skills/2.1.296/c48b3255bf6ff36a5e0ef4c3b38a27d0/plugin-authoring/ (only reference.md, examples/, types/ there; no SKILL.md file found on disk, find returned only this folder).

## Part A: the three mods

What a "mod" officially is: the built-in plugin-authoring skill says "Make a mod: a change to Claude's own interface or behaviour, such as a live pane or panel, a band above the prompt, a status line, a toast, a slash command, or a hook on tool calls or prompts." reference.md: "The API is early access and moves between releases: the declaration file is the authority." A mod is a plugin folder with .claude-plugin/plugin.json and a hooks module exporting register(on, options). Hooks include agent.spawn (can rewrite a workflow agent's "prompt and model", changelog), turn.start (hears subagents by e.agentId), $.model.complete / $.model.fork, Pane / AbovePrompt UI sites. Check with `claude plugin validate <dir>`.

### 1. Gatekeeper (cheap model for easy work) - KEEP, small gap
- Have: fb-ask/claude-fb tier (~/.claude/rules/cheap-worker.md) for text jobs on free models; subagent model pins (lessons.md: sonnet for search/review, opus only for architecture).
- Official: `haiku` alias, `opusplan` ("uses opus during plan mode, then switches to sonnet for execution", model-config.md line 40), CLAUDE_CODE_SUBAGENT_MODEL, Agent tool model param (model-config.md line 239). No built-in automatic per-prompt router found in docs (unverified for a hidden one).
- A real auto-router would be a mod using prompt.submit + model hooks. Unverified that a hook can switch the main-loop model per prompt; the documented rewrite is on agent.spawn (changelog).
- Verdict: keep. Cheap alternative: try `opusplan` in settings (one line). Do not build a router; the user wants to burn the weekly limit this week, so saving limit is not the goal now.

### 2. Claude talks to Claude (one plans, another builds) - KEEP
- Have: /architect writes the spec, /develop or wf builds one sandboxed `claude -p` per box (setup file line 8); superpowers subagent-driven-development; opusplan available.
- Official equivalents: subagents, agent teams (teammates with models, model-config.md line 239), agent view (changelog line 158).
- Verdict: keep; a mod would only duplicate wf.

### 3. Own panel (see what each agent does) - BUILD only if wanted (low priority)
- Have: status line `wf auto bar` (shows autonomous segment), wf morning report, runs/*/log.txt, phone questions. No live per-agent view.
- Official: a Pane / AbovePrompt hook (reference.md line 117) plus turn.start hearing subagent turns by agentId (changelog line 318) could draw this. Anthropic also ships agent view natively (changelog line 158), unverified how much it shows.
- Verdict: build is feasible, effort ~half a day (hooks module + validate), risk: early-access API moves between releases. Try built-in agent view first. Drop if wf log tail is enough.

## Part B: NVIDIA SkillSpector (found, real)

- Repo: https://github.com/NVIDIA/SkillSpector (License badge: "License: Apache 2.0", Python 3.12+; last commit seen Oct 14, 2026). Docs: https://docs.nvidia.com/skills/scanning-agent-skills . Press: https://www.helpnetsecurity.com/2026/08/03/skillspector-open-source-agent-skill-security-scanner/
- Quote: "Security scanner for AI agent skills. Detect vulnerabilities, malicious patterns, and security risks before installing agent skills." Part of the NVIDIA Verified Skills pipeline.
- Detects: README says "71 vulnerability patterns across 17 categories: prompt injection, data exfiltration, privilege escalation, supply chain, excessive agency, ... memory poisoning, tool misuse, rogue agent, anti-refusal, trigger abuse, dangerous code (AST), taint tracking, YARA signatures, MCP least privilege, and MCP tool poisoning". (NVIDIA docs page says 68, Help Net says 64: counts differ by version.) Risk score 0-100, outputs terminal/JSON/Markdown/SARIF, baseline suppression.
- PyPI/npm: no PyPI package confirmed; README installs from git only. Unverified on PyPI.
- Install (README, exact):
  - `uv tool install git+https://github.com/NVIDIA/skillspector.git`
  - or Docker: `docker build -t skillspector .` then `docker run --rm -v "$PWD:/scan" skillspector scan ./my-skill/ --no-llm`
  - Needs Python 3.12+; here python3 is 3.14.7 (may hit dependency wheels, unverified).
- Run: `skillspector scan ./my-skill/ --no-llm` (static only); also takes a SKILL.md, zip, or git URL. Batch: `python -m contrib.batch_scan.batch_scan ./my-skills/ --no-llm` (from the cloned repo).
- Local or remote: static pass is local. Two network facts: (1) dependency checks query OSV.dev (README: "SC4 queries OSV.dev ... with automatic offline fallback"; Help Net: "--no-llm ... still reach the network"); only package names go out. (2) The LLM pass is on by default unless `--no-llm`; README: SKILLSPECTOR_PROVIDER "Defaults to `nv_build`" (build.nvidia.com, needs NVIDIA_INFERENCE_KEY). With no key it should not run (unverified). Providers include `ollama` and `claude_cli`, so LLM pass can stay local or use our own Claude. Skill text goes to the chosen provider.
- Installed here: NO. `command -v skillspector` empty; `pip show skillspector` not found; `uv tool list` shows only paper-search-mcp, zotero-mcp; no global npm hit.
- Scan all installed skills (proposed, not run):
  `for d in ~/.claude/skills/*/ ~/.claude/plugins/cache/*/*/*/skills/*/; do skillspector scan "$d" --no-llm --format json --output /tmp/ss/$(basename "$d").json; done` (needs the SHAPE-safe script form here; plugin cache layout varies, verify globs). Note ~/.claude/skills/jjstack and getsentry-skills are git repos (never edit); scan read-only. Many dirs are symlinks to claude-config: scan once.

### Comparison
- sentry skill-scanner: /home/santiago/.claude/skills/getsentry-skills/skills/skill-scanner/SKILL.md. Described: "Checks for prompt injection, malicious scripts, excessive permissions, secret exposure, and supply chain risks." Uses `uv run scripts/scan_skill.py <dir>` (static JSON) then the model judges intent; supports "scan all skills". Fully local, no network except what the model uses. Fewer rules, no CVE lookup, no SARIF/score.
- Built-in /security-review: reviews the pending code diff of a repo; not made for skill folders (no hidden-instruction, trigger-shadow or tool-poisoning patterns). Use for code, not for vetting third-party skills.
- Closest alternatives if SkillSpector fails: Snyk agent-scan and Cisco skill-scanner exist per general knowledge; URLs NOT verified in this run (firecrawl was rate limited). Do not rely on them.

## Recommendation
- Row 64: keep all three. Try `opusplan` (effort 1 minute, zero cost) and the built-in agent view. Build the panel only if wanted (about half a day, early-access API risk). No router build.
- Row 65: ADOPT, with `--no-llm` first. Effort: 15 min install via uv, 30 min to script a scan-all loop. Cost: free; no LLM key needed. Run once on all skills and plugins, then on every new skill (the stated rule in the setup file). Keep sentry skill-scanner as the intent-judging second opinion. Skip LLM mode unless using `ollama` or `claude_cli` provider, so skill text stays local. Expect noise on first run (Reddit: "The free scan is noisy", https://www.reddit.com/r/claudeskills/comments/1v9fu2p/how_do_you_safetycheck_new_skills/ , single anecdote); use the baseline suppression file. Needs the user's yes to install (this run was read-only).
