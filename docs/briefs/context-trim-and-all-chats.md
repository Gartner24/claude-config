# Always-loaded context and all-chats rules (draft, 2026-10-22)

Measured by a read-only agent; tokens = characters / 4. Owner decisions pending.

## Part 1: what loads in every chat
- Our files: about 20.8k tokens (CLAUDE.md 3.3k, rules 8.0k, project AGENTS.md files 5.3k, MEMORY.md 3.9k).
- Skill list: about 12-15k (estimate).
- The other 60k+ of the 95-113k start is the system prompt, tool schemas, MCP server instructions (Figma, Notion, Exa, Firecrawl, DeepWiki, ...) and deferred tool names. Not measured.

| # | Cut | Saves | Risk |
|---|---|---|---|
| 1 | Runner text everywhere (agent already removing it) | ~6.5k | low |
| 2 | MEMORY.md entries to title + short clause; drop entries that repeat a rule | ~1.5k | low |
| 3 | Text loaded twice (CLAUDE.md routing/context/reviewer blocks vs handoff.md, skill-map.md) | ~1.2k | low-medium |
| 4 | Trim dotfiles AGENTS.md commands and gotchas | ~0.3k | low |
| 5 | Skill-only rules read on demand (check-gates, scope-contract, branch-pr, review-fix, ...) | ~5.4k | medium-high: needs a hook or pointer, the skills are vendored |
| 6 | ~60 unused skills name-only or disabled | ~0.5-1k | medium |

Never cut (protect-important-skills): impeccable, design-gate, rollover, save-and-clear, resume-from-clear, sync, architect, scope, check, test, develop, debug, audit, review, browse.

## Part 2: some-chats features as all-chats rules
| Row | Feature | Switches on when | Lives in |
|---|---|---|---|
| 10 | App start + browser verify | AGENTS.md has app start and app url, and a verify runs | check-gates.md line |
| 18 | Design enforcement | diff touches frontend files | design-check script, /sync runs it |
| 20 | Issue reread | scope Source is an issue | step-brief hook, scope-contract line |
| 28 | Keep awake | owner says leaving / finish it | rule line, optional prompt hook |
| 31 | Parallel features in worktrees | "do these features" or 2+ features ready | rule line + spec-paths --overlap |
| 32 | Start gates (4.5 GB free, under 80% 5h use) | before any extra agent | script called from row 31 |
| 38 | Self-merge checklist | own or personal repo, about to merge | branch-pr.md line |
| 42 | Review comment loop | open PR with comments | /loop 10m + iterate-pr |
| 44 | Foreign change check | branch has someone else's commits | rule line, maybe a script |
| 46 | Isolated review of others' PRs | owner asks to review someone's PR | review-isolated script |
| 59 | Scope marker warnings | any /scope or /sync | wf-dash scope parser |

## Connected services (measured 2026-10-22, tokens per chat are estimates, calls = last 30 days)
Total about 17k tokens per chat.
- Used: firecrawl ~7.5k (42 calls), Figma ~1.9k (18), Claude Docs ~1.1k (20), claude-in-chrome ~0.5k (425), chrome-devtools ~0.3k (1592), exa (11), Google Calendar (9), mobbin (37), zotero (1).
- Never used, about 5k together: Notion ~1.5k, deepwiki ~1.1k, paper-search ~0.7k, 21st ~0.6k, Canva ~0.45k, Gmail ~0.3k, LunarCrush, Google Drive, shadcn, tavily, searxng, Ketryx.
- Local ones go with `claude mcp remove <name>`; claude.ai ones (Notion, Canva, Gmail, LunarCrush, Drive, Ketryx) in claude.ai Settings > Connectors.
