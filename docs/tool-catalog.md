# Tool catalog

Every skill, plugin, mod, hook, MCP server and CLI this setup has used, tried, removed or turned
down, with the reason. Facts as of 2026-10-19.

**Rule:** before installing anything, or starting a `/deep-research` tool review, look it up here.
If it was removed or rejected, the reason below stands until something named in it has changed.
Any install, removal or verdict updates its row in the same change.

Source: "chat" means a Claude Code conversation on that date; the other sources are paths in
this repo. Older verdicts with longer notes: `docs/research/SKILLS-EVALUATION.md`.

## Lessons

- A hook outlives the tool it came from. GSD was deleted on 2026-07-07, and its hooks still ran
  on every edit until 2026-10-19. Removing a tool means removing its `settings.json` entries too.
- A watch-only check that can never act is noise. hookgate ran 3,719 times and changed nothing.
- Check that a tool can actually run before building on it. nano-banana needed paid Gemini
  billing, and the magic MCP did nothing on Astro sites, for months each.
- The most used tool can also be the most fragile. claude-mem had 20k uses and broke the session
  four times (dead worker, 19 GB of orphan processes, blocked prompts, quota burn).
- A plan line is not a yes. A removal waits for the owner's own words.
- Paid tiers, accounts and tracking dashboards are a reason to say no (claude-mem, Build
  Partner, Brave Search).

## In use

| Name | Kind | Dates | What it is for | Why kept | Source |
|---|---|---|---|---|---|
| jjstack | framework | 2026-05-25 | /review, /rollover, /resume-from-clear, /save-and-clear, safety hooks | Load bearing; pinned, never committed to. Its status line was replaced by ours (2026-10-19) | docs/guides/SETUP.md; docs/briefs/tool-review-2026-10.md |
| gstack | framework | 2026-05-25 | /qa, /ship, /investigate, browser daemon | Base under jjstack; browser fallback when the Chrome extension drops | docs/guides/SETUP.md |
| JSM skills (scope, architect, develop, check, test, sync, debug, audit, document) | skill pack | 2026-10-01 | The workflow: state in repo files, decision gate | Adopted; our mutation-check tests and design pipeline kept over theirs | chat 2026-10-01 |
| ECC (everything-claude-code) | framework, cherry-picked | 2026-05-25 | Agents, some skills and commands | Whole framework turned down (second memory system, command clashes); a frozen copy of parts kept. Rules excluded from loading 2026-09-24 (about 11k tokens a session) | docs/guides/SETUP.md; chat 2026-05-25 |
| sentry-skills | skill pack | 2026-05-25; removed 2026-07-07; back by 2026-09-03 | skill-scanner, code-review, find-bugs | Back in use; one report-only finding (claude-settings-audit suggests `gh api` as read only) | chat 2026-07-07; tool-review brief A4 |
| anthropic-security-review | toolkit | n/k | Security review scripts | Standalone toolkit | docs/guides/SETUP.md |
| Anthropic document skills (docx, pdf, pptx, xlsx, canvas-design) | skill pack | 2026-07 | Office files, marketing graphics | Official, low risk | SKILLS-EVALUATION.md |
| ponytail | plugin | 2026-06-25 | Lazy senior developer mode | Works every session; why karpathy-guidelines was turned down | chat 2026-10-19 |
| frontend-design | plugin | 2026-05-15 | Baseline UI skill | Part of the design pipeline | chat 2026-07-07 |
| code-review | plugin | 2026-05-15 | `/code-review:code-review` on a PR | Kept; the built-in `/code-review` overlaps it (noted 2026-09-03) | chat 2026-09-03 |
| ralph-loop | plugin | 2026-05-15 | Loop a prompt until done | Used to build ten site templates | chat 2026-07-09 |
| security-guidance | plugin | 2026-07-07 | AI security review on turn end, commit and push | Worth it, but heavy: 247 Opus reviews in 2.5 days (about 38 USD list price, uses the subscription limit). Turn-end reviews found 2 issues in about 105 runs. Caught a real hole (claude on untrusted worktrees) | chat 2026-10-19; chat 2026-10-16 |
| watch (claude-video) | plugin | 2026-10-01 | Watch videos as frames and captions | Used for course videos | chat 2026-10-01 |
| claude-seo | plugin | 2026-07-07; off globally 2026-09-24 | SEO audits for seo-ops and /monthly-ops | Kept, enabled per project to save context; its curl-to-shell installers accepted 2026-10-15 | chat 2026-10-16 |
| loop-guard | mod (claude-mods) | 2026-10-18 | Stops the same failing call being retried | Fired 5 times in a week, right each time | chat 2026-10-19 |
| compact-keeper | mod (claude-mods) | 2026-10-18 | Saves a note when a chat compacts | Rarely fires (compact at 700k, handoff at 200k); owner chose to keep it | chat 2026-10-19 |
| wf runner (`wf`, `next`) | own CLI | 2026-10-11 | Runs scope boxes in fresh sessions, opens draft PRs | The one command the owner wants. Open issue 2026-10-19: on a work repo it marked features done with no changes and took an issue outside the sprint | docs/architecture.md; chat 2026-10-19 |
| wf-dash | own mod | 2026-10-17 | Status band, agents and runner panes; replaces the jjstack status line | Band crashed on every redraw 10-17 to 10-19, fixed in PR #113, owner confirmed | chat 2026-10-19 |
| wf-handoff | own mod | 2026-10-18 | Auto handoff at 200k tokens | Works; handovers lose detail ("losing too much information") | chat 2026-10-19 |
| Status bar (`wf auto bar`) | own | 2026-10-19 | Bottom bar, ported from jjstack's statusline.sh | Only ours, no jjstack bar (owner) | runner/statusbar.py |
| review-stack, spawn-review | own skills | 2026-09-02; 2026-10-16 | Heavy blind-lane review; spawned reviews | Ours, copied out of jjstack | docs/guides/SKILLS.md |
| design, design-gate, assets, brand-system | own skills | rebuilt 2026-09-09 | Gated design pipeline with a run ledger | Kept. Weak spot: the gate opens after 3 blocks (let a run through unfinished 9 times, 2026-10-19) | docs/guides/DESIGN-PIPELINE.md; chat 2026-10-19 |
| seo-ops, content-ops, business-analyzer, video-to-website, astro-patterns, deep-research, claude-config, improve-my-system | own skills | 2026-06 to 2026-10 | Client work and setup upkeep | deep-research forked from ECC 2026-10-11 so an update cannot erase edits | claude-home/skills |
| nano-banana | own skill | 2026-07; rebuilt 2026-09-10 | Gemini image generation | Works only with paid Gemini billing (no free image tier); /assets falls back to prompts | chat 2026-09-10 |
| anti-ai-writing, voice-dna, humanizer | skills | 2026-07-07; 2026-08-06 | De-slop text (/polish chains them) | humanizer overlaps on purpose: mechanical sweep first, voice pass last | SKILLS-EVALUATION.md |
| impeccable, ui-ux-pro-max, design-motion-principles, taste skills (high-end-visual-design, minimalist-ui, industrial-brutalist-ui) | skills | 2026-05-25 to 2026-06-22 | Design critique, catalogs, styles | Part of /design | docs/guides/SETUP.md |
| emilkowalski skills (9), gsap-skills (8), transitions.dev (2), design-dna | skill packs | 2026-08-06 | Motion, GSAP, CSS transitions, tokens from a screenshot | transitions.dev was rejected in 2026-07 and overturned: it is a different layer | SKILLS-EVALUATION.md |
| threejs-skills (10) | skill pack | 2026-08-06 | 3D | No license, stale upstream; drop if no WebGL project lands | SKILLS-EVALUATION.md |
| marketingskills (12 of 50), packshot | skills | 2026-08-06 | CRO layer; product shots (FAL, about 0.12 USD an image) | packshot has no public repo; never publish it | SKILLS-EVALUATION.md |
| Cloudflare, Figma, 21st, chrome-devtools skill sets | skill packs | 2026-07-02 to 2026-09-12 | Platform skills | Vendor sets; Figma skills cannot be published | docs/briefs/untraced-skills.md |
| skill-router, council (jjstack), playwright-best-practices, tailwind, astro skills | skills | 2026-05-25 | Routing, multi-model council, stack skills | Kept; standalone tsenart council replaced by jjstack's | docs/guides/SETUP.md |
| Safety hooks: block-destructive, permission-floor (SECRET_PATH, PIPE_TO_SHELL), SHAPE | hooks | 2026-07 to 2026-09-23 | Block dangerous shell calls; one command per shell call | About 25 correct blocks a week. SHAPE costs time, not money: about 520 blocks a week, one retry each | chat 2026-10-19 |
| injection-guard | hook (jjstack) | n/k | Blocks injected instructions in written files | Worth it. One check is broken (`\n` in a grep pattern, line 69) and prints a warning on every edit; the fix belongs upstream | chat 2026-10-19 |
| plain-panel | own hook | spec 0028 | Refuses jargon in question panels | Works; strict word list (17 refusals a week) | chat 2026-10-19 |
| context-monitor.js | own hook | 2026-10-15 | Context size reminder | Derived from GSD's monitor, which never fired. Now information only (it used to push handoffs at 150k) | docs/guides/HOOKS.md |
| workflow-start, handover-start, claude-config-reminder, error-detector, mcp-reconnect | hooks | 2026-10 | Session start routing, handover load, update reminder, logs | Quiet and cheap | docs/guides/HOOKS.md |
| gstack timeline Stop hook, silent Edit/Write checks | hooks | n/k | Timeline recording and small checks | Cheap; owner said keep | chat 2026-10-19 |
| auto-approve-safe.sh | hook (jjstack) | 2026-05-25 | Audit log only since jjstack #36 | Our local patch dropped 2026-09-23; approves nothing | docs/guides/HOOKS.md |
| review-stack pre-push hook | git hook | 2026-09-09 | Needs a review receipt before push | Opt-in per own repo; removed from bot-reviewed repos 2026-09-16 (same reviewer twice) | chat 2026-09-16 |
| Notification sound hook | hook | 2026-09-30 | Sound when input is needed | Owner picked the sound | chat 2026-09-30 |
| skillspector, skill-scan | CLI; own script | 2026-10-15; 2026-10-17 | Scan skills before install | Static scores are noise; read only new HIGH findings | tool-review brief A3 |
| claude-fb + LiteLLM (pinned 1.101.0), fb-ask | CLI, proxy | 2026-09-24; 2026-10-13 | Free models when the Claude limit hits; cheap text jobs | Weak judgement, simple steps only. LiteLLM 1.82.7 and 1.82.8 were malicious releases | chat 2026-09-24 |
| MCP: context7, deepwiki, exa, tavily, firecrawl, searxng, paper-search, zotero | MCP | 2026-05-25 to 2026-10-11 | Docs and research | Free tiers; searxng runs only while a session is open | chat 2026-10-11 |
| MCP: 21st, mobbin, shadcn, chrome-devtools, claude-in-chrome | MCP | 2026-07 to 2026-09-10 | Design references, components, browser | mobbin is paid; claude-in-chrome drops when RAM runs out | chat 2026-09-10 |
| claude.ai connectors (Figma, Notion, Canva, Google, Claude Docs) | MCP | n/k | Account connectors | Account level | claude mcp list |
| rembg, vtracer, Lighthouse, axe-core, Stripe CLI, cloudflared, git-filter-repo | CLIs | 2026-06 to 2026-09 | Images, audits, webhooks, history rewrite | axe needs `--tags wcag22aa` or target-size never runs | chat 2026-07-03 |

## Under review

| Name | Kind | Dates | What it is for | Open question | Source |
|---|---|---|---|---|---|
| Assertion Guardian | mod (claude-mods) | 2026-10-18 | Stops tests being weakened | Blocks harmless edits, each needs `/allow-test-change`; stalled the runner twice. Owner will not allow it in autonomous mode. Recommended: block only removed checks | chat 2026-10-19 |
| intent-router | own skill | 2026-05-25 | Route prompts to skills | Never invoked in any chat; CLAUDE.md does its job. Recommended remove | chat 2026-10-19 |
| missed-skill detector (skill-miss-detect, skill-fired-clear) | hooks (jjstack) | 2026-10 | Logs skills that should have fired | Report is noise (top misses: brand-guidelines, threejs-interaction). Recommended remove | chat 2026-10-19 |
| security-guidance turn-end review | plugin setting | 2026-10-19 | Review on every turn end | Recommended `ENABLE_STOP_REVIEW=0`, keep commit and push reviews | chat 2026-10-19 |
| feature-dev, code-simplifier, clangd-lsp | plugins | 2026-05-15 | Agents; C/C++ language server | Removal proposed 2026-07-07 (never used, wrong stack), no answer recorded | chat 2026-07-07 |
| Language packs (rust, go, java, jpa, nestjs, django) | skills | 2026-05-25 | Other stacks | Never invoked in 1,384 sessions; set name-only 2026-09-24 | chat 2026-07-07; token diet |

## Trial

| Name | Kind | Dates | What it is for | Status | Source |
|---|---|---|---|---|---|
| MemPalace | memory tool (Docker) | 2026-10-16, review about 2026-10-30 | Local search over past chats (`mp`) | By hand only; never its plugin (auto-save hooks, writes CLAUDE.md). Specific queries work, vague ones do not | scope row 59 |
| Ollama local model (fb-local) | local model | 2026-10-17 | Private text jobs | Opt-in only, never a fallback: 6.1 tokens/s, 2 min cold load | tool-review brief A7 |
| Headroom | proxy | 2026-10-17, later | Token compression | Postponed: telemetry on by default, unreleased cost bug | tool-review brief D3 |
| Ghostty | terminal | 2026-09-30 | Alacritty replacement | Owner prefers tmux splits so far | chat 2026-09-30 |

## Removed

| Name | Kind | Dates | What it was for | Why removed | Source |
|---|---|---|---|---|---|
| get-shit-done-cc (GSD) | framework + hooks | 2026-05-25 to 2026-07-07; hooks 2026-10-19 | Planning framework | Two skills used once, no `.planning/` anywhere. Its hooks ran node 3 times per edit for nothing until 2026-10-19 | chat 2026-07-07; chat 2026-10-19 |
| hookgate | Stop hook | 2026-09-24 to 2026-10-19 | Check that a turn is really finished | Watch-only and its provider returns no confidence, so it could never act (3,719 runs, 476 flags, no effect) | chat 2026-09-30; chat 2026-10-19 |
| claude-mem | plugin | 2026-04-08 to 2026-10-15; data deleted 2026-10-19 | Memory across sessions | Kept breaking (dead worker, 19 GB orphan processes, blocked prompts), burned quota, then a paid Gemini key; paid tier. Memory files and briefs replace it | tool-review brief A1c |
| claude-mem chroma-reaper and install hooks | hooks | 2026-07-14 to 2026-10-16 | Served claude-mem | Its tool was gone. The reaper's own pgrep matched itself, so it never ran for two months | chat 2026-09-10 |
| superpowers | plugin | 2026-04-08 to 2026-10-19 (disabled) | Workflow skills | Intro pasted into every chat (about 400 times) while CLAUDE.md overrode its main rule; our workflow covers it | chat 2026-10-19 |
| aside | mod (claude-mods) | 2026-10-18 to 2026-10-19 | Side questions | Never worked; the one test went to the main chat | chat 2026-10-19 |
| collision-guard | mod (claude-mods) | 2026-10-18 to 2026-10-19 | Warn when two sessions edit one file | Never fired | chat 2026-10-19 |
| graphify | CLI + skill | 2026-07-07 to 2026-10-19 | Code knowledge graph | A/B test: +35% input tokens, no speed gain, never used unasked | docs/research/tool-review-2026-10/ |
| jjstack status line | status line | to 2026-10-19 | Bottom bar | Flickered and vanished; ours replaced it | chat 2026-10-19 |
| magic MCP (@21st-dev/magic) | MCP | 2026-06-26 to 2026-09-10 | UI components | React only, key rejected for months; made a design step a silent no-op. Replaced by the 21st and shadcn MCPs | chat 2026-09-10 |
| gsd-context-monitor | hook | to 2026-10-15 | Context warnings | Read a file only GSD's status line wrote, so it never fired | docs/guides/HOOKS.md |
| CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=100 | setting | 2026-06-02 to 2026-09-09 | "Turn autocompact off" | Did nothing | chat 2026-09-09 |
| ECC rules auto-load | rules | to 2026-09-24 | Language rules | Restated defaults; cost about 11k tokens a session. Lessons kept in rules/lessons.md | token diet 2026-09 |
| skill-creator, morning, linkedin-profile, import-memory | skills | to 2026-10-15 | Misc | skill-creator duplicated the official plugin; others unused | backups attic 2026-10-15 |
| connect-chrome, _gstack-command | skills | to 2026-10-16 | gstack | Renamed or gone upstream | tool-review brief A1b |
| tsenart council-skill | skill | 2026-05-25 | Council | Replaced by jjstack's council | docs/guides/SETUP.md |
| qwen3-coder:480b-cloud | model | to 2026-07-15 | claude-fb model | Retired by Ollama; gemma4 replaced it | chat 2026-10-16 |
| temp_git_* plugin cache folders | leftovers | to 2026-10-19 | Failed installs | Nothing used them | chat 2026-10-19 |

## Rejected (never installed)

| Name | Kind | Date | What it is | Why not | Source |
|---|---|---|---|---|---|
| NotebookLM + notebooklm-mcp | service, MCP | 2026-10-15 | Second brain | Text goes to Google, unofficial login, 50 chats a day, repo archived | tool-review brief C |
| OmniRoute | gateway | 2026-09-30 | Model router | claude.ai cookie proxy (ban risk), critical RCE | chat 2026-09-30 |
| claude-code-router and other non-Claude gateways | gateway | 2026-10-15 | Model routing | Unsupported by Anthropic | tool-review brief C |
| Brave Search MCP | MCP | 2026-10-11 | Web search | Needs a card, bills past the free credit | chat 2026-10-11 |
| Refero MCP | MCP | 2026-09-10 | Design references | Paid plan only | chat 2026-09-10 |
| Official figma and chrome-devtools plugins | plugins | 2026-09-12 | Same tools again | Duplicate the connector and the MCP already in use | chat 2026-09-12 |
| Snyk Agent Scan, Cisco skill-scanner | scanners | 2026-10-15 | Skill scanning | Backups only if skillspector misses something | tool-review brief C |
| Soup | CLI | 2026-10-15 | Fine-tuning | Not a router; needs a strong GPU | tool-review brief C |
| Harvey | CLI | 2026-10-15 | Cold email sender | Sends mail unattended with Gmail credentials; idea kept as a lead finder that never sends | tool-review brief C |
| MiroFish | CLI | 2026-10-15 | Audience simulation | AGPL, two paid clouds, unproven; idea kept as a reaction tester | tool-review brief C |
| claude-skills-founder | plugin | 2026-10-15 | Founder skills | Duplicates ours; two ideas borrowed | tool-review brief C |
| Claude Build Partner | plugin | 2026-10-17 | Self-improving setup | Account, tracking dashboard, paid tier; rebuilt free as improve-my-system | tool-review brief |
| claude-mods, claude-statuspane, whats-agent-doing (as status tools) | mods | 2026-10-15 | Status bars, dashboards | Young, none covers wf | tool-review brief C |
| claude-queue, blast-radius, cc-mod-park, transcript-redactor | mods (claude-mods) | 2026-10-18 | Prompt queue, impact map, mod park, secret redactor | Not picked: queue could fight wf-dash for the prompt line, cc-mod-park rewrites settings, redactor touches every command | chat 2026-10-18 |
| claude-auto-handoff | mod | 2026-10-18 | Auto handoff | Not installed; every part that beats ours is copied into wf-handoff (MIT, credited) | docs/briefs/auto-handoff.md |
| Gatekeeper router mod, Claude-to-Claude mod | mod ideas | 2026-10-17 | Routing | Model pins, fb-ask and /architect then /develop already do it | tool-review brief C |
| Antigravity installer | CLI | 2026-10-15 | Named by a jjstack skill | Owner: never run it (the skill stays) | tool-review brief A4 |
| ecc-agentshield | scanner | 2026-05-25 | Config scan | Not worth a workflow change | chat 2026-05-25 |
| StudioHawk SEO skills (54) | skill pack | 2026-09-30 | SEO | About 6.3k listing tokens, trigger clashes; 8 ideas adapted into seo-ops | chat 2026-09-30 |
| genjutsu | skill pack | 2026-08-06, again 2026-09-30 | Design | A second design pipeline, 6 to 13M tokens a run | SKILLS-EVALUATION.md |
| LottieFiles motion-design-skill | skill | 2026-08-06, again 2026-09-30 | Motion | Covered three times over | SKILLS-EVALUATION.md |
| karpathy-guidelines | skill | 2026-08-06 | Coding guardrails | ponytail and CLAUDE.md do it harder | SKILLS-EVALUATION.md |
| taste (standalone), ux-designer, artifacts-builder | skills | 2026-07-07 | Design | Duplicate the pipeline; React-in-chat while we build Astro | SKILLS-EVALUATION.md |
| distribb, NotFair, Hainrixz claude-ads | skills | 2026-07-07 | SEO links, ads | Link scheme risk; mutates live ad accounts; unsafe install | SKILLS-EVALUATION.md |
| AgriciDaniel claude-ads | skill | 2026-07-07 | Ads audit | Clean, but no ads work yet; revisit when ads start | SKILLS-EVALUATION.md |
| 35 of 47 marketingskills, dumbify, storytelling, viral-hooks | skills | 2026-08-06 | Copy, social | Covered by content-ops, article-writing, seo-ops | SKILLS-EVALUATION.md |
| Unvetted video-watching skill from the web | skill | 2026-06-29 | Watch videos | Unvetted code; ffmpeg frames did the job (watch plugin later) | chat 2026-06-29 |
| Local /review in bot-reviewed repos | practice | 2026-09-16 | Review | The team bot already runs the same reviewer | CLAUDE.md Review Rules |
