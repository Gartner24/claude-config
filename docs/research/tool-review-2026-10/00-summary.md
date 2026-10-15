# Tool review 2026-10: research summary

Claude Code version: 2.1.301 (row 66 is an action, not researched).
Current setup baseline: 00-current-setup.md. Each row's full report is <row>-<slug>.md in this folder.
Spot checks: I re-checked two citations per report with curl or by reading the source file. All passed except one small count noted under row 57.

## Per row

### 57. Own skills in jjstack - REJECT the move (keep jjstack pinned and external)
- Evidence: jjstack upstream is github.com/JesperJurcenoks/jjstack (`git remote -v`, checked). The user's commits are small fixes to upstream files, already merged upstream: statusline (#66), consensus (#32), auto-approve hook, skill name collisions. I found 8 commits by author; the report says 9. The only new item is `spawn-review`, and it sits on branch feat/spawn-review, not on main. All 54 jjstack skills in ~/.claude/skills are symlinks to jjstack. 4 hooks are symlinks too, plus 3 hooks and the status line run from jjstack paths. jjstack is MIT.
- Effort: optional, about 1 h to copy statusline.sh alone with a NOTICE row. Row 58 makes even that unnecessary.
- Open: push or drop spawn-review? Is "drop jjstack" still the goal, given that nothing in it is solely yours?

### 58. Own status bar and dashboards - BUILD OUR OWN mod (`wf-dash`)
- Evidence: Anthropic's mods announcement (claude.com/blog/claude-code-mods, 2026-10-01) and the docs page (code.claude.com/docs/en/plugins/mods/overview, HTTP 200). The bundled plugin-authoring skill documents `$.ui.status`, `$.ui.open` panes, `$.agent.list`, `$.clock.every` and the AbovePrompt band (grep checked). Mods others built (claude-mods, claude-statuspane, whats-agent-doing) are young, under 45 stars, and none covers wf.
- Plan: a band carrying jjstack's segments (model and effort, folder, branch and dirty count, context, 5 h and weekly bars) plus wf counts; an agents pane; a runner pane (run.json list and log tail); toasts on wf events. Keep the shell status line as fallback.
- Effort: 1-2 days.
- Open: can `$.ui.status` replace the statusLine command? Can a mod read the 5 h and weekly usage without the OAuth curl? Mods are not sandboxed, so scan ours like any plugin.

### 59. Memory - keep graphify for code, TRIAL MemPalace for sessions, REJECT NotebookLM, leave claude-mem off
- Evidence: claude-mem's engine is free (Apache-2.0). Pro is USD 30/month and adds cloud sync. Free mode still burns observer tokens. MemPalace: MIT, local, no LLM, 59.6k stars, created 2026-04, 836 open issues (API checked). Its benchmark claims are disputed on HN. NotebookLM: the popular PleasePrompto/notebooklm-mcp is archived (checked: archived=true, last push 2026-09-10). It drives Chrome with Google cookies, all session text goes to Google, and there is a chat cap of about 50 per day (third-party source, unverified). Most of the pasted claims are false or unverified.
- Effort: MemPalace trial 1-2 h, about 2 weeks of use, own and freelance repos only, after a skillspector scan.
- Open: does memory from work repos ever leave the machine? (Currently no.) Is claude-mem's overdue decision (due ~2026-10-08) now final as "off"?

### 60. Sessions pass work to each other - ADAPT
- Evidence: the mod API has `command.run`, `prompt.submit` (asUser) and `session.end` with reason clear (grep checked in the bundled skill). A SessionStart hook with source `clear` can inject the handover as additionalContext (limit 10,000 characters). wf already continues sessions with `claude -p --resume` (run.py:2937, checked).
- Plan: build the hook route now (about 1 h; the user still types /clear). Probe the mod route (the mod runs /clear, then submits /resume-from-clear) in a scratch session before building it.
- Open: is a mod allowed to run the built-in /clear? Does the submitted prompt survive the clear? Guard against resuming the same handover twice.

### 61. Cheap model gatekeeper - ADAPT small; REJECT Soup as a router
- Evidence: Soup is a fine-tuning CLI, not a router: "Fine-tune LLMs from one YAML" (GitHub API, checked). fb-ask already routes through LiteLLM (fb-ask.py, checked) to gpt-oss-120b on Ollama Cloud, falling back to Groq. gpt-oss-120b scores 47.9-62.4 on SWE-Bench Verified (arXiv 2508.10925): good enough for reading jobs, too weak for edits. Claude Code routes subagents through the `model` frontmatter field, CLAUDE_CODE_SUBAGENT_MODEL, or a mod's `agent.spawn` hook.
- Plan: use fb-ask more on big inputs (about 1 h). Pin haiku on read-only agents (minutes). Add an agent.spawn mod only after measuring savings.
- Open: routing saves limit only on tokens Claude never sees. This week's goal is to spend the limit, so is it worth building now or after you hit the limit?

### 62. Runner that improves itself - BUILD OUR OWN
- Evidence: run records already carry duration, cost, tokens, denials and retries per call. About 40 reason codes are defined (run.py:273-282, checked). Only loops inside one run exist (caps, crash_loop, retakes); nothing aggregates across runs. The row 46 miss detector senses and compares but acts on nothing. Prior art: Reflexion (arXiv 2303.11366, checked), Agent Workflow Memory, Voyager. DGM and ADAS are rejected, because self-editing code clashes with the guard threat model.
- Plan: a stdlib aggregator over runs/*/run.json that sets baselines and turns a repeated reason code into a proposed scope row or brief. It only writes text and never edits guards or deny lists. It runs while wf is idle, at zero token cost.
- Effort: 150-250 lines and one spec.
- Open: proposals as scope rows (they would show in the queue), or a separate inbox file?

### 63. Five tools
- Harvey: REJECT. It is an autonomous cold-email sender with Gmail credentials and CAN-SPAM exposure, with no dev overlap. The Spanish guide is only an install prompt.
- Soup: REJECT. Fine-tuning, needs a GPU (Apache-2.0, 9.1k stars, checked).
- MiroFish: REJECT. AGPL-3.0, needs paid LLM and Zep Cloud keys, unproven.
- claude-skills-founder: ADAPT. Take only /pitch-deck, /fundraise-prep and /metrics-dashboard as manifest pins; the rest duplicates skills we have.
- Headroom: ADAPT as a gated trial (Apache-2.0, 75.4k stars, checked). It is a local proxy that sees all traffic, with telemetry on by default (turn off with HEADROOM_BEACON=off). `headroom wrap` edits ~/.claude.json. Little value while the goal is to spend the limit.
- Caveat: security findings are from READMEs only; install scripts were not read.

### 64. Three recommended mods
- Gatekeeper: KEEP what we have (fb-ask, model pins, `opusplan`). Building an auto-router is not justified.
- Claude to Claude: KEEP. /architect then /develop and wf already split planning from building, and superpowers subagents do the same.
- Own panel: BUILD, and fold it into row 58's wf-dash. Do not build it twice.

### 65. skillspector - ADOPT with `--no-llm`
- Evidence: github.com/NVIDIA/SkillSpector exists (HTTP 200, checked). Apache-2.0, 68-71 detection patterns. Install: `uv tool install git+https://github.com/NVIDIA/skillspector.git`. Scan: `skillspector scan <dir> --no-llm`. The static scan is local apart from OSV.dev lookups. The LLM pass defaults to build.nvidia.com; ollama and claude_cli providers are also offered. Not installed here.
- Effort: about 45 min to install and script a scan over ~/.claude/skills/* and plugin skills. The install needs your yes.
- Open: run the LLM pass through claude_cli, which costs limit (fits this week's goal), or stay static only?

## Suggested order for the week (aims to use most of the weekly limit)
1. Row 66: update Claude Code with /claude-config (first, as the brief says).
2. Row 65: install skillspector and scan every installed skill. Everything after this is gated on it, and the LLM pass via claude_cli spends limit usefully.
3. Row 58 + row 64 panel: /architect, then build wf-dash (band, agents pane, runner pane). It removes jjstack's status line dependency, the biggest piece of row 57.
4. Row 60: hook route now; probe the mod route in the same mod work (shared API).
5. Row 62: spec and build the aggregator and proposer (a medium build, good use of the limit).
6. Row 59: scan MemPalace, then a 2-week trial; graphify stays.
7. Row 57: close it: decide spawn-review, then mark the row satisfied by row 58 (no move).
8. Row 63 leftovers: claude-skills-founder pins and the Headroom trial, after scans. Do these last, since Headroom cuts token use, which works against this week's goal.
9. Row 61: after the limit is hit, measure, then decide on an agent.spawn mod.

## Conflicts between rows
- Row 57 vs 58: row 57's "Done when" asks that the status line no longer need jjstack. Row 58 meets that without moving any skill, so row 57 shrinks to the spawn-review decision.
- Row 59 vs 60: the handoff (slot plus transcript) and a memory tool (MemPalace mining ~/.claude/projects) both inject context at SessionStart. Both together risk duplicated context and the 10,000-character additionalContext cap. Decide which owns SessionStart.
- Row 61 / 63 (Headroom) vs the week's goal: both save tokens, while the goal is to spend the limit. Schedule them last.
- Row 64 vs 58: same panel, build once.
- Rows 58, 60 and 61 all rest on mods, which are not sandboxed and are early access. Each mod needs a skillspector scan and a probe after every Claude Code upgrade (like the existing spec 0007 and 0009 probes).
- The brief's premise for row 61 ("open models like Soup's") is wrong: Soup trains models, it does not route them.
