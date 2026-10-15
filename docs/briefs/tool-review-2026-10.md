# Tool review and setup upgrade (October 2026)

Source: your message of 2026-10-15 evening, at the end of the clean branches session. To be done in a new session, after spec 0051 lands.

## Agreed so far, do not ask again
- **The habit**: you regularly take new Claude Code tools (plugins, skills, MCP servers, features) and we decide together whether each is worth adding. claude-mem used to remind us of that; it is off now, so this brief and the plan rows carry it.
- **Every item below needs its own `/deep-research` and a comparison with the existing setup** before any decision. The goal is the best setup, and finishing the week with almost all of the weekly limit used.
- **Order**: start by updating Claude Code through `/claude-config` (row 66), then the rest.
- **Security**: scan every skill or plugin before adopting it with NVIDIA's skill scanner, `skillspector`.
- **Never commit to jjstack** for any of this.

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
