# Tool review and setup upgrade (October 2026)

Source: your message of 2026-10-15 evening, at the end of the clean branches session. To be done in a new session, after spec 0051 lands.

## Agreed so far, do not ask again
- **The habit**: you regularly take new Claude Code tools (plugins, skills, MCP servers, features) and we decide together whether each is worth adding. claude-mem used to remind us of that; it is off now, so this brief and the plan rows carry it.
- **Every item below needs its own `/deep-research` and a comparison with the existing setup** before any decision. The goal is the best setup, and finishing the week with almost all of the weekly limit used.
- **Order**: start by updating Claude Code through `/claude-config` (row 66), then the rest.
- **Security**: scan every skill or plugin before adopting it with NVIDIA's skill scanner, `skillspector`.
- **Never commit to jjstack** for any of this.
- **The plan below is the whole list** (agreed 2026-10-15): nothing is added, dropped or swapped without your yes, and every session reads it before other work here.
- **A4 answers** (2026-10-15): claude-seo's `curl | bash` install scripts are fine, keep them. Do not install Antigravity: never run the installer jjstack's `antigravity` skill names; the skill itself stays.
- **A5 to A9 may run while the A4 model scan runs** (your ask, 2026-10-16). A5 is PR #26, waiting for your merge.
- **A6 backup** (your answer, 2026-10-16): add a second Ollama Cloud model (for example `qwen3-coder`) as order 3 in both `fb-safe` and `fb-any` in `~/.config/claude-fb/litellm.yaml`. No OpenRouter, no new account or key.
- **D2 answer** (2026-10-16): the graphify test (A8) uses your studio's engine repo under `~/projects/freelance/` (name kept out of this public file).
- **A7 runs in a parallel session** (your answer, 2026-10-16), so this one goes on with A8 meanwhile.

## The plan, enforced until done (agreed 2026-10-15)

This is the whole list. Nothing is added, dropped or swapped without your yes, and every session reads this section before any other work in claude-config. Tick a box only with the evidence named on it. Research behind each line: [docs/research/tool-review-2026-10/](../research/tool-review-2026-10/).

### A. Install or set up (I guide you, in this order)
- [x] A1. Update Claude Code through `/claude-config`, then `drift: none` (row 66): Claude Code 2.1.301 is current, drift none, the update crash on a renamed skill fixed in PR #21
- [x] A1b. Skill updates, your answer 2026-10-15 "yes to all you recommended": apply every `update --plan` entry from ECC, gstack, Cloudflare, Figma, marketing, animation and design, 21st, Chrome DevTools, transitions-dev, transitions-polish, impeccable, design-dna, ui-ux-pro-max, humanizer and minimalist-ui (edited: merge, show any conflict), each group scanned with skillspector before install; `claude plugin update` for superpowers, code-review, feature-dev, frontend-design, security-guidance, code-simplifier, ralph-loop, clangd-lsp, ponytail, claude-seo, watch; remove the old `connect-chrome` (renamed upstream to `open-gstack-browser`, already installed) and the `_gstack-command` entry (gone upstream); graphify waits for A8: done 2026-10-16, 134 skills installed after a static scan of each new version against the old (PR #24), 6 plugins updated (plugins not scanned first, A4 covers them), connect-chrome and _gstack-command removed
- [x] A1c. claude-mem removed for good: plugin uninstalled 2026-10-15 (done); still to remove its manifest entry, its SessionStart hook `claude-mem-install.sh` from settings.json and `bin/install.sh`, and check `chroma-reaper.sh` is still needed: done 2026-10-16 in PR #23; chroma-reaper.sh removed too (it only served claude-mem), the deny rules for its settings file kept
- [x] A2. Update claude-config's docs for the new setup: SETUP.md, DAILY-USE.md, SKILLS.md (row 66): PR #21
- [x] A3. Install skillspector: installed v2.12.0 pinned (`uv tool install "git+https://github.com/NVIDIA/SkillSpector.git@v2.12.0"`); it refuses symlinked paths, so scans must use the real folder (`realpath`); the model pass is `SKILLSPECTOR_PROVIDER=claude_cli` (row 65)
- [ ] A4. Scan every installed skill and plugin with skillspector; remove or report each failure (row 65)
- [ ] A5. Copy your `spawn-review` skill from jjstack's branch into claude-config as yours; no commit to jjstack (row 57)
- [ ] A6. Add free backup models to fb-ask's LiteLLM settings (row 61, Soup research)
- [ ] A7. Local model trial: `ollama-vulkan` (your sudo), `qwen2.5-coder:14b`, context 16k, speed test, one opencode task against claude-fb's cloud model, its own `fb-local` group; never while wf builds (row 67)
- [ ] A8. graphify test: update it, map one large own repo code only with AI keys hidden, 8 to 10 questions with and without the map; keep only if it wins by 25% and Claude uses it unasked, else uninstall it and remove the skill. Never claude-config, client or work repos (row 70)
- [ ] A9. MemPalace trial, after skillspector passes it: Docker, read only mount, loaded by hand, no auto save, one wing per project, no client or work repos, two weeks (row 59)

### B. Build (each gets `/architect`, then the runner)
- [ ] B1. Finish clean branches and PRs: `/check verify` and `/sync` (row 56)
- [ ] B2. Runner with more than 4 features at once: any number, default top 6 (8 max until measured), starts a feature only with over 4.5 GB free memory and the 5 hour use under 80%, the same files rule back from each spec's Paths line, a spec with no Paths runs alone, worktrees kept (row 68)
- [ ] B3. wf-dash, our own mod: status band with jjstack's segments plus wf counts, an agents pane, a runner pane, alerts; the shell status line stays as fallback; replaces jjstack's status line (rows 58, 64, closes 57)
- [ ] B4. Sessions pass work on: SessionStart hook loads a waiting handover (you type only `/clear`), then a probe of a mod doing the `/clear`, built if it works; the handover loads first and memory gets the space left (row 60)
- [ ] B5. Runner that improves itself: reads every run.json while idle, sets baselines, writes proposals to a separate inbox file the session shows you, reads `/insights` too, never edits guards or deny lists (row 62)
- [ ] B6. Cheap work on cheap models: read only helper agents pinned to Haiku, fb-ask used for big inputs; an `agent.spawn` routing mod only after measuring the savings (row 61)
- [ ] B7. Skill scan script: skillspector over every skill and plugin, both passes, rerun before every install (row 65)
- [ ] B8. Local model wired in, only if A7 passes: `fb-local` group in fb-ask for private text (row 67)
- [ ] B9. graphify in the workflow, only if A8 wins: its hook and one CLAUDE.md line in that repo only (row 70)
- [ ] B10. Lead finder (idea from Harvey): a skill that audits local business sites for no website, no booking, an old blog or an incumbent agency, and lists 10 to 20 for you to contact by hand; nothing is ever sent by it (row 69)
- [ ] B11. Reaction tester (idea from MiroFish): Claude agents play your target customers and react to an idea, offer or page, then a summary (row 69)
- [ ] B12. Idea scorecard (idea from claude-skills-founder): a 7 point score ending in build, change course or drop, in your idea review skill (row 69)
- [ ] B13. New number replaces old (idea from claude-skills-founder): a new figure replaces a saved one and says what it replaced, never an invented number; in customer-research and offers (row 69)
- [ ] B14. Session save and check memory first (idea from the NotebookLM post): done locally through the MemPalace trial, nothing to Google (row 59)

### C. Not installing or building, with the reason
- Harvey: unattended Claude on the subscription breaks the terms, no legal footer, poor fit for Colombia.
- Soup: trains models, does not route them; needs a strong GPU.
- MiroFish: two paid outside clouds, unproven, AGPL.
- NotebookLM and its MCP servers: text goes to Google, unofficial browser login, 50 chats a day, "free and open source" is false.
- claude-mem: off for good.
- Headroom: saves tokens against this week's goal, cost tripling bug unreleased; trial later (D3).
- claude-skills-founder as a plugin: duplicates our skills, no gain on Opus 5 by its own evals.
- Other people's mods (claude-mods, claude-statuspane, whats-agent-doing): young, none covers wf.
- Snyk Agent Scan and Cisco skill-scanner: backups only if skillspector misses something.
- claude-code-router and any gateway to non-Claude models for Claude Code: unsupported by Anthropic.
- Gatekeeper auto-router mod and Claude-to-Claude mod: `/architect` then `/develop`, wf and model pins already do it.
- A full repo clone per runner feature: worktrees already isolate each feature and each has its own PR.
- Claude Code itself on the local model: prefill takes minutes and the context does not fit.
- gpt-oss:20b and qwen3-coder:30b locally: larger than the 11 GB the GPU can use.

### D. Open, needs your answer
- [ ] D1. Review leftovers from PR #18 (row 71): add hook scripts, `config/`, skills, agents and `package.json` to the never-self-merge list (recommended yes); date the old branch warning from the first commit (recommended yes); wait for at least one check before a self merge (recommended yes)
- [ ] D2. Which large own repo the graphify test (A8) uses
- [ ] D3. Headroom trial, next week or later
- [ ] D4. fb-ask on client repos when the model is local (only if A7 passes)
- [ ] D5. Kept branches `feat/seo-ops-refs` and `sync-settings`: keep or delete

### E. Housekeeping still open
- [ ] E1. Row 46 missed skill detector: the 3 day report verdict, then `/sync`
- [ ] E2. Row 51 autonomous mode per chat: the two real chats check, then `/sync`
- [ ] E3. Two bugs found today: `bin/repo-settings.sh` failed its first run then passed; `bin/docs-pr.sh` leaves local main diverged after the squash merge (row 71)
- [ ] E4. Small notes from the PR #18 review: stale "combined at the end" line in scope.md, contradicting lines in architecture.md invariant 1 and claude-home/CLAUDE.md:41, `--fill` titles in docs-pr.sh, runner/context.py missing from spec 0051's Paths (row 71)
- [ ] E5. Rebuild the master list after each phase

## Items
1. **Update Claude Code first** (row 66): run `/claude-config` to update and check drift.
2. **Leave jjstack behind** (row 57): you want to mostly drop jjstack. Some skills in it are yours, added there by Claude; find them from jjstack's git history (commits by you), and copy your own skills and the things you use into the claude-config setup. Do not commit to jjstack.
3. **Own status bar and dashboards with Claude Code mods** (row 58): mods were added to Claude Code this week; replace jjstack's status line with our own, much better. Research what people have already built and what we can build. Dashboards are easier now than through the status bar.
4. **Memory tool** (row 59): claude-mem was dropped for its paid tier. Decide between keeping claude-mem, MemPalace, graphify (installed already as a skill), both of the last two (they may serve different purposes), or NotebookLM as a second brain (the `notebooklm-mcp` server, a wrap up skill that saves each session into a notebook, a CLAUDE.md routing rule that checks the notebook first, semantic search next session). Weigh every variable: usage, token cost, memory quality, code memory.
5. **Sessions passing work to each other** (row 60): mods say sessions can now hand work to each other. That may fix the session to session gaps of `/clear` then `/resume-from-clear` and `/rollover`: roll over and pass straight to the next session; the same for the runner.
6. **Cheap model gatekeeper with open models** (row 61): mods can send easy work to a cheaper model. That exists already (`fb-ask`, claude-fb), but it would be better with open source models like claude-fb's or Soup's.
7. **Runner that improves itself** (row 62): from general systems theory, the runner is a system; add feedback so it gets better each run and improves itself while idle.
8. **Tools to evaluate** (row 63), each researched and compared:
   - Harvey: https://github.com/ethanplusai/harvey and https://localleadhub.com/harvey-ai, plus your guide `~/Downloads/guia-harvey.pdf`
   - Soup: https://github.com/MakazhanAlpamys/Soup
   - MiroFish: https://github.com/666ghj/MiroFish
   - claude-skills-founder: https://github.com/emotixco/claude-skills-founder
   - Headroom (token optimization): https://github.com/headroomlabs-ai/headroom
9. **Recommended mods** (row 64): someone recommended three mods; we may do these already, so research whether each is worth it: (1) a gatekeeper that sends easy work to a cheaper model so the limit lasts longer; (2) Claude talks to Claude, one plans and another builds; (3) your own panel showing what each agent does without asking.
10. **Skill security scan** (row 65): run `skillspector` over the installed skills and every new candidate.

## Quoted sources (data, from your message)
Recommended mods (translated from Spanish): "Three that will save you trouble: 1. The gatekeeper: easy work goes to a cheaper model and your limit lasts longer. 2. Claude talks to Claude: one plans, another builds. 3. Your own panel: you see what each agent does without asking."

NotebookLM claim (as you pasted it): create a free notebook "Claude Memory", connect with the free `notebooklm-mcp` server, add a wrap up skill that saves each session, add a routing rule to CLAUDE.md so Claude checks the notebook first, and the next session pulls what it needs by semantic search; claimed benefits: persistent memory, lower token cost, answers only from saved sessions, free infographics and video overviews. These are claims to verify, not facts.

## Research answers (2026-10-15, after the orchestrated research in docs/research/tool-review-2026-10/)
- Row 57: keep jjstack and close the row; only its status line goes (row 58 replaces it); copy `spawn-review` into claude-config as your own.
- Row 61: start it today with everything else ("I think we should start everything today!"), not after the limit is hit.
- Row 65: skillspector runs both the static scan and the model pass on every installed skill.
- Row 62: the self improving runner writes its proposals to a separate inbox file the session shows you; you promote the good ones to plan rows.
- Rows 59 and 60: at session start a waiting handover loads first and memory gets the space left; claude-mem stays off for good.
- Mods: accepted for wf-dash and the handoff mod, each our own code, scanned with skillspector and tested after every Claude Code upgrade.
- All rows start today.
