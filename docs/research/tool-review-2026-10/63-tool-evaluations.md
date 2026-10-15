# Row 63: five tool evaluations (2026-10-15)

Data from api.github.com/repos/<o>/<r> and READMEs on raw.githubusercontent.com. Nothing was run or installed. Install scripts, hooks and source files were NOT read beyond file listings and READMEs (unverified where noted). Setup baseline: research/00-current-setup.md.

| Tool | Stars | License | Last commit | Lang |
|---|---|---|---|---|
| Harvey | 852 | MIT | 2026-10-15 | Python |
| Soup | 9108 | Apache-2.0 | 2026-10-15 | Python |
| MiroFish | 79500 | AGPL-3.0 | 2026-10-01 | Python |
| claude-skills-founder | 640 | MIT | 2026-10-07 | Shell |
| Headroom | 75448 | Apache-2.0 | 2026-10-15 | Python |

## Harvey
- What: "An autonomous sales agent that runs on your Claude Code or Codex subscription." Finds businesses, writes cold email, sends, reads replies (https://github.com/ethanplusai/harvey README). The PDF ~/Downloads/guia-harvey.pdf (Spanish, "GUIA NODESTUDIO") is a paste-in prompt that clones the repo, installs with pip, and has Claude Code run setup.
- Maintenance: active, daily merges, external PRs (Microsoft 365 provider).
- Overlap: none in the dev workflow. Nearest is the `cro`/`offers`/`lead-magnets` marketing skills (no sending). It runs a loop on `claude -p` like wf does, but for sales.
- Security: runs a 15-minute loop on your machine, uses your Claude login ("there is no model API bill"), needs Gmail/Workspace credentials, an email-verifier key, a dashboard on localhost:5555. Sends mail to strangers: README says "CAN-SPAM penalties run to $53,088 per email". Reads scraped pages and prospect replies as prompts (injection surface; README claims model tools are disabled for Codex; Claude-side isolation not verified). Using a subscription for an unattended loop may breach the plan terms: README only says "Check the terms and usage limits of the provider you choose." No telemetry statement found. It competes with the user's weekly Claude limit.
- Fit: user has no stated outbound-sales need. The guide is a how-to for a different audience.
- Verdict: REJECT (unless a freelance outbound campaign is requested; then adapt only in a throwaway VM, approval mode on).

## Soup
- What: "Fine-tune LLMs from one YAML. Layer streaming trains an 8B model on a 4 GB laptop GPU." (api description). `pip install "soup-cli[train]"`, `soup train` (https://github.com/MakazhanAlpamys/Soup).
- Maintenance: very active (commit #1831 today).
- Overlap: none. Not a Claude Code tool, no skill or hook. Needs a GPU for any value; the laptop is an ASUS Vivobook (memory: laptop-hardware.md) and no fine-tuning work exists in the scope.
- Security: pip package with heavy ML deps; downloads models/datasets; telemetry not checked (unverified). Web UI exists.
- Verdict: REJECT (off topic). Revisit only if a fine-tune project appears.

## MiroFish
- What: "A Simple and Universal Swarm Intelligence Engine, Predicting Anything." Multi-agent social simulation to "rehearse the future" (https://github.com/666ghj/MiroFish README).
- Maintenance: last commit 2026-10-01 is "update Star History"; project is popular (79.5k) but the README shows only demos ("Financial Prediction... coming soon"), so prediction accuracy is unproven (unverified).
- Overlap: none. Loosely like `/council` or `consensus` skills, but those are one-shot debate, not a simulation.
- Security: needs an LLM_API_KEY (default Alibaba DashScope URL `https://dashscope.aliyuncs.com/compatible-mode/v1`) and a ZEP_API_KEY (Zep Cloud), i.e. your seed documents go to two third-party clouds. Node 18+ plus Python stack, or docker compose. License AGPL-3.0: any hosted use forces source release.
- Verdict: REJECT. Cost is API billing on a paid key, which conflicts with the subscription-only setup.

## claude-skills-founder
- What: 13 slash skills for founders: `/validate-idea`, `/product-brief`, `/competitor-matrix`, `/pricing-strategy`, `/go-to-market`, `/pitch-deck`, etc. Skills "save its output to a `founder/` folder" and reuse earlier outputs (https://github.com/emotixco/claude-skills-founder README). Install: `/plugin marketplace add emotixco/claude-skills-founder`.
- Maintenance: active, merged PR 2026-10-07; small project (640 stars).
- Overlap: strong. `pricing`, `offers`, `cro`, `launch`, `customer-research`, `kano-model`, `office-hours`, `plan-ceo-review`, `product-manager-review`, `marketing-psychology` already exist in ~/.claude/skills list. Only `/pitch-deck`, `/fundraise-prep`, `/metrics-dashboard` have no equivalent.
- Security: file listing shows `.claude-plugin/plugin.json`, marketplace.json, and only eval fixture shell scripts; no hook files at top level (hooks inside plugin.json not read: unverified). README states "about 1,100 tokens to each session" for descriptions, a small standing cost. Writes only to `founder/`.
- Verdict: ADAPT. Do not install the plugin. If a pitch deck or fundraise need appears, copy those SKILL.md files (MIT) into claude-config with a manifest pin, scan first. Cost: ~1 hour, 0 tokens ongoing.

## Headroom
- What: "Compress tool outputs, logs, files, and RAG chunks before they reach the LLM." Library, local proxy, MCP server; `headroom wrap claude` starts a local proxy and launches the agent routed through it (https://github.com/headroomlabs-ai/headroom README). Claims "20% fewer tokens for coding agents, 60-95% fewer tokens for JSON" (vendor claim, unverified).
- Maintenance: very active (commits within hours, 75k stars).
- Overlap: token goals overlap with context-monitor.js hook (spec 0037), `fb-ask` cheap worker, ponytail (README even recommends Ponytail), graphify. No existing proxy-level compression. Also touches the wf runner: wf runs sandboxed `claude -p` calls (bwrap, deny lists), and a proxy on 127.0.0.1 would need sandbox network allowance (unverified).
- Security (highest of the five): sits between Claude Code and the API, so it sees every prompt, tool output and your Claude auth header. README: "An anonymous beacon is **on by default**... ratios, counters, provider and model IDs, OS and architecture" (off via `HEADROOM_BEACON=off`, `DO_NOT_TRACK=1` or `HEADROOM_OFFLINE=1`). Daily PyPI update check (`HEADROOM_UPDATE_CHECK=off`). `headroom wrap` installs Serena and writes a local-scope MCP server into `~/.claude.json`; `headroom unwrap` reverses it. Heavy install (`headroom-ai[all]`, Rust/ONNX). Compression is lossy by design (CCR "reversible" retrieval claimed, unverified), which can drop log lines the model needed.
- Verdict: ADAPT/trial. Weekly limit is meant to be used up, so saving tokens is low value now. If tried: install in a venv, `--code-memory none`, beacon off, run `headroom proxy` on one disposable session only, not under wf. Effort ~2 hours; compare token use on one fixed task before/after.

## Summary
- Harvey: reject. Soup: reject. MiroFish: reject. claude-skills-founder: adapt (3 skills at most). Headroom: adapt as a gated trial.
- Any adopted item (founder skills, Headroom plugin/MCP entries) must pass NVIDIA skillspector before use (not installed yet; the existing sentry-skills:skill-scanner is a stopgap).
