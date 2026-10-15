# Row 58: Claude Code mods, status line and dashboards (2026-10-15)

## What mods are (official)
- Announced 2026-10-01: "Today we're introducing mods, small TypeScript functions that change how Claude Code works. A mod can rewrite a prompt, add new UI, replace a built-in feature, or add entirely new functionality. ... Mods ship inside plugins." (https://claude.com/blog/claude-code-mods)
- "They work in the Claude Code CLI and desktop app. Mods run with the same access to your machine as Claude Code itself. They aren't sandboxed" (same page).
- Docs: "A mod is a plugin that changes how Claude Code looks and behaves. It's made of JavaScript or TypeScript event handlers ... Use a mod to add ... a pane that charts how full your context is" and "Settings hooks, skills, status lines, and MCP servers work from outside Claude Code ... A mod runs inside Claude Code" (https://code.claude.com/docs/en/plugins/mods/overview).
- Local built-in skill plugin-authoring (loaded via Skill tool; files at /tmp/claude-1000/bundled-skills/2.1.296/*/plugin-authoring/, SKILL.md is not on disk, bundled in the binary): a mod = `.claude-plugin/plugin.json` + `hooks/hooks.json` {"modules":["./register.tsx"]} + `register.tsx` with `export const register: Register = (on, options) => {...}`.
- Surfaces (same skill): pane = `$.ui.open({id,title})` drawn by a `ui.render` hook on `{component:'Pane'}`; band above prompt = `ui.render` on `{component:'AbovePrompt'}`; status line entry = `$.ui.status(text)`; toast = `$.ui.toast`; slash command = `$.command.register`.
- Capabilities from reference.md: `$.clock.every/after` timers, `$.fs` (read/write/list/stat), `$.process.run` (host command by argv), `$.model.complete`, `$.agent` (types file: "One agent loop of this session as `$.agent.list()` returns it", claude-code.d.ts line 122), `$.state` (session) and `$.store` (across sessions).
- Limits: a pane opened unasked seats from 144 columns (110 per `$.ui.open` doc), the terminal fullscreen layout docks panes (reference.md). Mods load via hot reload (user must answer a prompt) or `claude --plugin-dir`; `claude plugin validate`, `claude plugin test`.
- Caution: `$.ui.status` is "a status line entry" - the docs list "status lines" separately from mods, so the settings.json statusLine command still exists. Unverified: whether `$.ui.status` replaces or only appends to the statusLine command output, and whether a mod can read the OAuth 5h/week usage (I found no rate-limit field in the types grep; the existing script calls api.anthropic.com/api/oauth/usage itself, a mod could do the same via `$.process.run` curl or python).

## What people built (HN search 2026-10-01..10-09, GitHub API)
- augiefra/claude-mods (12 stars): "context in tokens, 5-hour and weekly limits vs. the clock, prompt cache countdown, session cost and running agents, in one band above the prompt." https://github.com/augiefra/claude-mods
- ice-lfernandes/claude-code-mods (7): "plan limits and context above the prompt, an allowlist coach ..., subagent tokens, tests in the status line".
- xuanji86/claude-statuspane (10): "floating status card ... model, context, rate limits, cost, branch - plus a progress API any script or mod can feed."
- lurenxing628/claude-code-mod-statusline (1): two-line bar with context, tokens, TPS, cost, cache hit, 5h/week countdown.
- tzafrir/whats-agent-doing (7): box above prompt saying what Claude is doing now. hoobnn/hoobnn-agent-mods (7): status HUD, task progress bar.
- karanb192/claude-code-mods (42): mods plus a builder skill. delexw/miod (MIDI music), Terminal Gym, arcade/Minesweeper, context-diet, context-debloat (toy and context tools).
- Hub: HN thread list https://hn.algolia.com/api/v1/search?query=claude%20code%20mods
- I did not read any of these sources; star counts are low (all under 45), so treat them as unvetted code that runs unsandboxed. Each needs the skillspector scan before use.

## Today's status line (jjstack statusline.sh, read in full)
Segments, joined by dim " | ": model name (cyan) + effort (colored, from input .effort.level) | folder basename | git branch + (+staged ~modified ?untracked, or "clean") | context bar (% from .context_window.used_percentage, green <70, yellow <90, red) | 5h usage bar | week bar (both OAuth, from api.anthropic.com/api/oauth/usage, cached 300 s in /tmp/claude-usage-cache.json) . Fallbacks: API-key mode shows session USD (.cost.total_cost_usd); non-Anthropic ANTHROPIC_BASE_URL shows "via <provider>". auto.py bar() appends the autonomous-mode segment. (/home/santiago/.claude/skills/jjstack/bin/statusline.sh)

## Recommendation: build our own (small), adapt nothing wholesale
Reasons: existing mods are young and unvetted; the existing 5h/week/cost/context segments are what augiefra's band does, so a clone adds little; the real gap is wf and agent visibility, which no public mod covers (wf state is ours). Keep the shell statusLine as the fallback until the mod is proven, so no jjstack dependency removal risk.

Cost and effort: about 1-2 days for a single mod `wf-dash`, TypeScript, ~300 lines, in ~/claude-config (public repo, so no client names). Risk: mods are unsandboxed, API is 2 weeks old and may change (API file is 14k lines, read it first); hot-reload prompt needs the user's yes.

Sketch:
1. Band above prompt (AbovePrompt) replaces the status line: model+effort, folder, branch+dirty, context %, 5h/week bars (port the usage fetch; reuse /tmp cache), autonomous-mode flag read from wf auto state, plus "wf: N running, M parked, K waiting on you" from ~/.local/state/wf/queue.json via `$.fs`, refreshed with `$.clock.every(5000)`. Colors green/yellow/red at 70/90 as today.
2. Agents pane (`$.ui.open`): table from `$.agent.list()` (type, state, tokens) plus background tasks; opened by a slash command `/agents` so it does not need 144 columns unasked.
3. Runner pane: list runs/*/run.json (name, box, state, cost), tail of the newest log.txt (last ~15 lines), parked and phone-question items from queue.json; Button hotkeys only for read actions (open log, copy run path). No write actions on wf state (rule: the conductor must not touch live state).
4. Toast on wf events (box finished, parked, question waiting) from a state-file diff.
5. First step: read examples/band.tsx and pane.tsx in the bundled skill dir, `claude plugin validate`, then one `*.test.ts`.
Alternative cheaper path: keep the shell script, extend it with a wf segment (30 min); do that first if the mod API proves unstable.
