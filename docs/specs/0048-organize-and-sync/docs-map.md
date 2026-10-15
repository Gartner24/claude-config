# 0048. Docs map (AC-12)

Every command, fact and decision in the old `README.md`, `AGENTS.md`, `docs/architecture.md` and the 7
old guides, one row each, with its old file and line (at commit `1bb9e93`, before the rewrite) and the
new file and heading it lands in. The headings follow [docs-plan.md](docs-plan.md). No row lands
nowhere; `runner/tests/test_layout.py` `test_docs_map` fails on a row that does, or whose new file
does not exist.

Dropped on purpose (each is a dated history note whose fact is kept elsewhere, a pointer to a file
that moved, or the old `/audit` draft marker): rows D8, S3, S19, S24, S27, S64, S121, S272, S273,
S283, S287, S300, P58, P76, A212.

## README.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| R1 | README.md:1 | Title: claude-config | README.md | What this is |
| R2 | README.md:3 | Personal Claude Code setup kept in git | README.md | What this is |
| R3 | README.md:3-4 | Claude Code reads its setup from ~/.claude, the live dir | README.md | What this is |
| R4 | README.md:4-5 | Repo keeps hand written parts of that folder | README.md | What this is |
| R5 | README.md:5 | wf is a runner that builds queued features | README.md | What this is |
| R6 | README.md:9-10 | One source of truth per kind; edit the winner | README.md | Where things live |
| R7 | README.md:14 | Copied kind: CLAUDE.md, settings, agents, rules, hooks; live wins | README.md | Where things live |
| R8 | README.md:14 | Copied: bin/sync.sh copies live into repo | README.md | Where things live |
| R9 | README.md:14 | Copied: bin/install.sh copies back on a new machine | README.md | Where things live |
| R10 | README.md:15 | Linked kind: skills and commands symlinked into repo; repo wins | README.md | Where things live |
| R11 | README.md:15 | Linked: bin/install.sh makes the links | README.md | Where things live |
| R12 | README.md:16 | Runner kind: runner/ copied to ~/.local/share/wf/<fp>/, repo wins | README.md | Where things live |
| R13 | README.md:16 | Runner: ~/.local/bin/wf links to the copy | README.md | Where things live |
| R14 | README.md:17 | Repo tools in scripts/, two linked into ~/.local/bin | README.md | Where things live |
| R15 | README.md:18 | Frameworks: installer wins, never copied here | README.md | Where things live |
| R16 | README.md:19 | Private files in ~/.claude/private/, live only, never in a repo | README.md | Where things live |
| R17 | README.md:20 | Claude Code state is Claude Code only, never synced | README.md | Where things live |
| R18 | README.md:22 | claude-home/ mirrors ~/.claude at the same relative path | README.md | Where things live |
| R19 | README.md:22-23 | Guides in docs/guides, specs in docs/specs, plan in docs/scope | README.md | Where things live |
| R20 | README.md:25-26 | Conductor session rules go in ~/.claude/.claude/CLAUDE.md | README.md | Where things live |
| R21 | README.md:26-27 | Rules for this repo only go in AGENTS.md | README.md | Where things live |
| R22 | README.md:27-28 | Root CLAUDE.md only imports AGENTS.md, so each loads once | README.md | Where things live |
| R23 | README.md:32-41 | Diagram: what claude loads at start (memory, settings, hooks, skills) | README.md | One session, start to finish |
| R24 | README.md:35 | User memory is ~/.claude/CLAUDE.md plus imports plus rules | README.md | One session, start to finish |
| R25 | README.md:36 | Project memory is the folder's CLAUDE.md, if present | README.md | One session, start to finish |
| R26 | README.md:37 | Settings: user settings.json, then the folder's | README.md | One session, start to finish |
| R27 | README.md:38-39 | Hooks are scripts settings.json names, run on events | README.md | One session, start to finish |
| R28 | README.md:40-41 | Only a skill's one line description loads; body on invoke | README.md | One session, start to finish |
| R29 | README.md:43-46 | Diagram: wf run reads scope, runs claude -p per step in sandbox | README.md | One session, start to finish |
| R30 | README.md:46 | wf records result, ticks the box or asks on phone | README.md | One session, start to finish |
| R31 | README.md:49 | User memory loads everywhere; project memory only in its folder | README.md | One session, start to finish |
| R32 | README.md:50-51 | A skill is a folder with SKILL.md; ours are linked | README.md | One session, start to finish |
| R33 | README.md:51 | Other skills come from frameworks and npx skills add | README.md | One session, start to finish |
| R34 | README.md:52-53 | A hook is a script run on an event; can block a tool call | README.md | One session, start to finish |
| R35 | README.md:54-55 | Private files hold work names; sync and commit hooks refuse them | README.md | One session, start to finish |
| R36 | README.md:59-60 | Guides table header | README.md | Guides |
| R37 | README.md:61 | PLUGINS.md: official plugins | README.md | Guides |
| R38 | README.md:62 | SKILLS.md: community skills and frameworks | README.md | Guides |
| R39 | README.md:63 | MCP.md: MCP servers | README.md | Guides |
| R40 | README.md:64 | HOOKS.md: each hook and where it comes from | README.md | Guides |
| R41 | README.md:65 | USAGE.md: which skill to reach for, routing table | README.md | Guides |
| R42 | README.md:66 | DESIGN-PIPELINE.md: design pipeline setup notes | README.md | Guides |
| R43 | README.md:67 | SKILLS-EVALUATION.md: skills tried, kept or dropped | README.md | Guides |
| R44 | README.md:71 | Each rule below cost something on a real project | README.md | Rules earned the hard way |
| R45 | README.md:75 | Absent answer rendered as definite one (code-review.md) | README.md | Rules earned the hard way |
| R46 | README.md:75 | One defaulted count switched off the account deletion guard | README.md | Rules earned the hard way |
| R47 | README.md:76 | Get the RED back when the test came second (testing.md) | README.md | Rules earned the hard way |
| R48 | README.md:77 | A test that reimplements the logic passes forever | README.md | Rules earned the hard way |
| R49 | README.md:78 | A mock weaker than the real module passes anything | README.md | Rules earned the hard way |
| R50 | README.md:79 | Shell discipline: stale cd, heredoc expansion | README.md | Rules earned the hard way |
| R51 | README.md:80 | Grep before writing against a symbol | README.md | Rules earned the hard way |
| R52 | README.md:82 | ECC language rules are not auto loaded | README.md | Rules earned the hard way |
| R53 | README.md:82-83 | Add one @~/.claude/rules/ecc/<lang>/index.md line to a project CLAUDE.md | docs/guides/DAILY-USE.md | Language rules on demand |
| R54 | README.md:83 | Available languages: typescript, python, golang, rust, java, web, common | docs/guides/DAILY-USE.md | Language rules on demand |
| R55 | README.md:87-93 | Stack overview block | README.md | Stack overview |
| R56 | README.md:88-89 | Plugins list: superpowers, claude-mem, frontend-design, code-review, feature-dev, code-simplifier, ralph-loop, clangd-lsp, ponytail, security-guidance | docs/guides/SETUP.md | Plugins |
| R57 | README.md:90 | Frameworks: gstack, jjstack on top, get-shit-done-cc pinned 1.34.2 hooks only | README.md | Stack overview |
| R58 | README.md:91 | Community skills: impeccable, graphify, 21st.dev, Cloudflare, ECC cherry pick | README.md | Stack overview |
| R59 | README.md:92 | MCP servers: magic and context7 | README.md | Stack overview |
| R60 | README.md:97 | Restore 1: clone, bin/install.sh --dry-run, then bin/install.sh | README.md | Restore on a new machine |
| R61 | README.md:98-99 | Restore 2: install frameworks and plugins from guides | README.md | Restore on a new machine |
| R62 | README.md:100 | Restore 3: merge config/mcp-config.json into ~/.claude.json | README.md | Restore on a new machine |

## AGENTS.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| A1 | AGENTS.md:1 | Title: claude-config | README.md | What this is |
| A2 | AGENTS.md:3-4 | Public snapshot of personal ~/.claude setup | README.md | What this is |
| A3 | AGENTS.md:4 | Contents: instructions, settings, agents, rules, hooks, authored skills | README.md | What this is |
| A4 | AGENTS.md:4-5 | Frameworks are documented, never vendored | README.md | Where things live |
| A5 | AGENTS.md:9 | Languages: Markdown, Bash, Python 3, Node (one ESM script) | README.md | Stack overview |
| A6 | AGENTS.md:10 | Framework: none; harness reads the files | README.md | Stack overview |
| A7 | AGENTS.md:11 | Key dependencies: jq (sync.sh) | README.md | Stack overview |
| A8 | AGENTS.md:11 | Key dependencies: fontTools (design font scripts) | README.md | Stack overview |
| A9 | AGENTS.md:11 | Key dependencies: culori, node_modules committed on purpose | README.md | Stack overview |
| A10 | AGENTS.md:12 | No root package manager; design scripts package.json only | README.md | Stack overview |
| A11 | AGENTS.md:16 | Build approach: skateboard, each stage usable alone | docs/scope/scope.md | header (Build approach line) |
| A12 | AGENTS.md:21 | bin/install.sh --dry-run: repo to ~/.claude, then self-checks | AGENTS.md | Commands |
| A13 | AGENTS.md:22 | bin/sync.sh: ~/.claude to repo, run before every commit | AGENTS.md | Commands |
| A14 | AGENTS.md:23 | claude-config.py drift / update, behind /claude-config (spec 0048) | AGENTS.md | Commands |
| A15 | AGENTS.md:23 | drift exits 1 when repo and ~/.claude differ | AGENTS.md | Commands |
| A16 | AGENTS.md:23 | update never asks; the skill asks per entry | AGENTS.md | Commands |
| A17 | AGENTS.md:23 | Tests in runner/tests/test_claude_config.py | AGENTS.md | Commands |
| A18 | AGENTS.md:24 | check-routing.py after editing USAGE.md or skill triggers | AGENTS.md | Commands |
| A19 | AGENTS.md:25 | gen-agent-index.py --check after touching agents/ | AGENTS.md | Commands |
| A20 | AGENTS.md:26 | asciify.py --check: ASCII-only lint | AGENTS.md | Commands |
| A21 | AGENTS.md:27 | block-destructive.sh --test | AGENTS.md | Commands |
| A22 | AGENTS.md:28 | plain-panel.py --test (spec 0028) | AGENTS.md | Commands |
| A23 | AGENTS.md:28 | Panel checks: "Learn this first" last, max 3 options, no jargon | AGENTS.md | Commands |
| A24 | AGENTS.md:29 | context-monitor.js --test (spec 0037) | AGENTS.md | Commands |
| A25 | AGENTS.md:29 | Header numbers must match the code and autoCompactWindow | AGENTS.md | Commands |
| A26 | AGENTS.md:30 | design test-ledger.sh: ledger and Stop hook assertions | AGENTS.md | Commands |
| A27 | AGENTS.md:31 | build-ramp.mjs --check | AGENTS.md | Commands |
| A28 | AGENTS.md:32 | python3 -m unittest discover -s runner/tests; install.sh runs it | AGENTS.md | Commands |
| A29 | AGENTS.md:33 | runner/e2e/run.py: real claude end to end (spec 0014) | AGENTS.md | Commands |
| A30 | AGENTS.md:33 | Run e2e yourself with ! after a Claude Code upgrade or runner change | AGENTS.md | Commands |
| A31 | AGENTS.md:33 | e2e prints PASS or FAIL: <check> | AGENTS.md | Commands |
| A32 | AGENTS.md:33 | e2e --parallel: two real repos side by side (spec 0017) | AGENTS.md | Commands |
| A33 | AGENTS.md:33 | e2e --beside: bare wf -y beside running wf run (spec 0020) | AGENTS.md | Commands |
| A34 | AGENTS.md:33 | e2e --same-repo: three features of a parallel: 2 repo (spec 0027) | AGENTS.md | Commands |
| A35 | AGENTS.md:34 | private-names.py --test (spec 0013) | AGENTS.md | Commands |
| A36 | AGENTS.md:34 | private-names.py check scans repo, exits 0 when clean | AGENTS.md | Commands |
| A37 | AGENTS.md:35 | spec-paths.py --test (spec 0015) | AGENTS.md | Commands |
| A38 | AGENTS.md:35 | install.sh links spec-paths; /sync runs spec-paths --spec NNNN | AGENTS.md | Commands |
| A39 | AGENTS.md:36 | jjstack-skill-miss-report: skills matched but not run (spec 0036) | AGENTS.md | Commands |
| A40 | AGENTS.md:36 | Its two hooks are in HOOKS.md and stay off under WF_RUN | AGENTS.md | Commands |
| A41 | AGENTS.md:37 | fb-ask <task>: cheap worker tier, five tasks (spec 0023) | AGENTS.md | Commands |
| A42 | AGENTS.md:37 | fb-ask exit 3/4 means do it yourself | AGENTS.md | Commands |
| A43 | AGENTS.md:37 | fb-ask --test self checks; install.sh links it | AGENTS.md | Commands |
| A44 | AGENTS.md:38 | wf run [repo] [--jobs N]: queued auto features (spec 0011) | docs/guides/DAILY-USE.md | Run the runner |
| A45 | AGENTS.md:38 | wf run with no name starts one -y child per repo with work (spec 0017) | docs/guides/DAILY-USE.md | Run the runner |
| A46 | AGENTS.md:38 | --jobs caps children; state in $XDG_STATE_HOME/wf else ~/.local/state/wf | docs/guides/DAILY-USE.md | Run the runner |
| A47 | AGENTS.md:39 | wf [-y] [--jobs N]: the one command you type (spec 0020) | docs/guides/DAILY-USE.md | Run the runner |
| A48 | AGENTS.md:39 | Bare wf: confirm, report, setup swap, retakes, builds, checks | docs/guides/DAILY-USE.md | Run the runner |
| A49 | AGENTS.md:39 | A running run is skipped, never stopped; subcommands are internals | docs/guides/DAILY-USE.md | Run the runner |
| A50 | AGENTS.md:40 | wf queue [repo]: read only plan (spec 0011) | docs/guides/DAILY-USE.md | Run the runner |
| A51 | AGENTS.md:41 | wf unpark <repo> [feature]: clear parks and open questions | docs/guides/DAILY-USE.md | Run the runner |
| A52 | AGENTS.md:42 | wf allow <repo>: trust list (spec 0008) | docs/guides/DAILY-USE.md | Run the runner |
| A53 | AGENTS.md:42 | Untrusted repo is refused with exit 5; list in allowed.json | docs/guides/DAILY-USE.md | Run the runner |
| A54 | AGENTS.md:43 | wf allow-writes <repo> <path>: standing write permission (spec 0021) | docs/guides/DAILY-USE.md | Run the runner |
| A55 | AGENTS.md:43 | Kept in ~/.config/wf/allow.json | docs/guides/DAILY-USE.md | Run the runner |
| A56 | AGENTS.md:43 | A never writable set always wins | docs/guides/DAILY-USE.md | Run the runner |
| A57 | AGENTS.md:43 | allow-writes refused under WF_RUN | docs/guides/DAILY-USE.md | Run the runner |
| A58 | AGENTS.md:43 | An AGENTS.md "allow writes:" line is ignored now | AGENTS.md | Standing answers |
| A59 | AGENTS.md:44 | wf finish [target] [-y]: runs live waits-on-you boxes (spec 0019) | docs/guides/DAILY-USE.md | Run the runner |
| A60 | AGENTS.md:44 | finish keeps autoMode, ticks boxes, records verify.md, commits | docs/guides/DAILY-USE.md | Run the runner |
| A61 | AGENTS.md:44 | finish never from an unattended call | docs/guides/DAILY-USE.md | Run the runner |
| A62 | AGENTS.md:44 | wf run asks on phone for live copy boxes, pinned by source hash (spec 0041) | docs/guides/DAILY-USE.md | Run the runner |
| A63 | AGENTS.md:45 | wf report: last morning report, also sent to phone (spec 0018) | docs/guides/DAILY-USE.md | Run the runner |
| A64 | AGENTS.md:45 | report --hook is the SessionStart form, prints only unseen | docs/guides/DAILY-USE.md | Run the runner |
| A65 | AGENTS.md:45 | report --seen stops showing it; report.txt in wf state folder | docs/guides/DAILY-USE.md | Run the runner |
| A66 | AGENTS.md:46 | wf ntfy init / codes / test: phone pings (spec 0005) | docs/guides/DAILY-USE.md | Run the runner |
| A67 | AGENTS.md:46 | ntfy config ~/.config/wf/ntfy.json (0600); wf run refuses without it | docs/guides/DAILY-USE.md | Run the runner |
| A68 | AGENTS.md:47 | wf telegram init / test: Telegram bot instead of ntfy (spec 0029) | docs/guides/DAILY-USE.md | Run the runner |
| A69 | AGENTS.md:47 | init asks BotFather token (hidden), binds chat with /start code | docs/guides/DAILY-USE.md | Run the runner |
| A70 | AGENTS.md:47 | Writes ~/.config/wf/telegram.json (0600); test sends one question | docs/guides/DAILY-USE.md | Run the runner |
| A71 | AGENTS.md:48 | wf telegram fetch / timer on / off (spec 0039) | docs/guides/DAILY-USE.md | Run the runner |
| A72 | AGENTS.md:48 | fetch saves updates once into the log a run reads, same lock as a run | docs/guides/DAILY-USE.md | Run the runner |
| A73 | AGENTS.md:48 | timer on enables wf-telegram-fetch user timer, every 5 minutes; off removes it | docs/guides/DAILY-USE.md | Run the runner |
| A74 | AGENTS.md:49 | wf questions: read only list of open questions (spec 0039) | docs/guides/DAILY-USE.md | Run the runner |
| A75 | AGENTS.md:49 | Bare wf lists questions first, answer at keyboard, Enter skips, -y only lists | docs/guides/DAILY-USE.md | Run the runner |
| A76 | AGENTS.md:50 | wf auto on / off [now] / status / start / wait / take / release / hook / bar (specs 0030, 0046) | docs/guides/DAILY-USE.md | Run the runner |
| A77 | AGENTS.md:50 | /auto on [repos] user only, refused under WF_RUN; one chat per session folder | docs/guides/DAILY-USE.md | Run the runner |
| A78 | AGENTS.md:50 | start runs wf -y --repos as the chat's wf-auto-<8 hex> user unit | docs/guides/DAILY-USE.md | Run the runner |
| A79 | AGENTS.md:50 | take/release move repos in or out of this chat; Claude may run them, never from another chat | docs/guides/DAILY-USE.md | Run the runner |
| A80 | AGENTS.md:50 | off lets build finish current features; off now stops the unit | docs/guides/DAILY-USE.md | Run the runner |
| A81 | AGENTS.md:50 | hook is SessionStart and UserPromptSubmit hook; bar wraps jjstack's status line | docs/guides/DAILY-USE.md | Run the runner |
| A82 | AGENTS.md:50 | State in <state>/auto.json (version 2, chats keyed by folder) | docs/guides/DAILY-USE.md | Run the runner |
| A83 | AGENTS.md:55 | Specs live in docs/specs/NNNN-title.md or NNNN-title/index.md | docs/architecture.md | Specs |
| A84 | AGENTS.md:55 | 0001 runner stack | docs/architecture.md | Specs |
| A85 | AGENTS.md:55 | 0002 next | docs/architecture.md | Specs |
| A86 | AGENTS.md:55 | 0003 scope contract | docs/architecture.md | Specs |
| A87 | AGENTS.md:55 | 0004 wf run | docs/architecture.md | Specs |
| A88 | AGENTS.md:55 | 0005 decision parking and phone pings | docs/architecture.md | Specs |
| A89 | AGENTS.md:55 | 0006 standing answers | docs/architecture.md | Specs |
| A90 | AGENTS.md:55 | 0007 push guard | docs/architecture.md | Specs |
| A91 | AGENTS.md:55 | 0008 failure and park policy | docs/architecture.md | Specs |
| A92 | AGENTS.md:55 | 0009 headless verify and test | docs/architecture.md | Specs |
| A93 | AGENTS.md:55 | 0010 design enforcement | docs/architecture.md | Specs |
| A94 | AGENTS.md:55 | 0011 build and decision queue | docs/architecture.md | Specs |
| A95 | AGENTS.md:55 | 0012 waiting boxes owed to you | docs/architecture.md | Specs |
| A96 | AGENTS.md:55 | 0013 work names out of the public repo | docs/architecture.md | Specs |
| A97 | AGENTS.md:55 | 0014 runner resilience | docs/architecture.md | Specs |
| A98 | AGENTS.md:55 | 0015 checks that cannot lie | docs/architecture.md | Specs |
| A99 | AGENTS.md:55 | 0016 guard hook false alarms | docs/architecture.md | Specs |
| A100 | AGENTS.md:55 | 0017 several repos at once | docs/architecture.md | Specs |
| A101 | AGENTS.md:55 | 0018 morning report | docs/architecture.md | Specs |
| A102 | AGENTS.md:55 | 0019 live setup steps | docs/architecture.md | Specs |
| A103 | AGENTS.md:55 | 0020 one command wf | docs/architecture.md | Specs |
| A104 | AGENTS.md:55 | 0021 never stop (every park reason asks a question) | docs/architecture.md | Specs |
| A105 | AGENTS.md:55 | Every spec top file carries a **Paths:** line after **Status**: | AGENTS.md | Rules |
| A106 | AGENTS.md:59 | Everything installed into ~/.claude sits under claude-home/ at same path | README.md | Where things live |
| A107 | AGENTS.md:59 | Guides are in docs/guides/ (spec 0035) | README.md | Where things live |
| A108 | AGENTS.md:60 | Copied files list; live wins | AGENTS.md | Rules |
| A109 | AGENTS.md:60 | Edit the file in ~/.claude then bin/sync.sh | AGENTS.md | Rules |
| A110 | AGENTS.md:60 | An edit made here is overwritten on next sync | AGENTS.md | Rules |
| A111 | AGENTS.md:61 | Linked: skills and commands, repo wins, editing here is live | AGENTS.md | Rules |
| A112 | AGENTS.md:62 | Runner: repo wins; install.sh copies to ~/.local/share/wf/<fp>/ (spec 0020) | AGENTS.md | Rules |
| A113 | AGENTS.md:63 | Frameworks: their installer wins, never vendored | README.md | Where things live |
| A114 | AGENTS.md:64 | Private: live only, never in any repo | README.md | Where things live |
| A115 | AGENTS.md:65 | Claude Code state: Claude Code only, never synced | README.md | Where things live |
| A116 | AGENTS.md:66 | Rules for this repo only go in this file | AGENTS.md | Rules |
| A117 | AGENTS.md:66 | Rules for sessions started in ~/.claude go in ~/.claude/.claude/CLAUDE.md | AGENTS.md | Rules |
| A118 | AGENTS.md:67 | runner/ is the wf workflow runner (spec 0001) | docs/architecture.md | Components |
| A119 | AGENTS.md:67 | install.sh symlinks wf.py to ~/.local/bin/wf and next | AGENTS.md | Rules |
| A120 | AGENTS.md:67 | Called as next, it acts as wf next | AGENTS.md | Rules |
| A121 | AGENTS.md:67 | Edit the runner here, not the installed copy | AGENTS.md | Rules |
| A122 | AGENTS.md:67 | Python 3 stdlib only, tests are unittest | AGENTS.md | Rules |
| A123 | AGENTS.md:67 | External commands via subprocess argument lists, never shell strings | AGENTS.md | Rules |
| A124 | AGENTS.md:68 | Repo is public: no client or employer names, repos, domains, env-file names | AGENTS.md | Rules |
| A125 | AGENTS.md:68 | bin/sync.sh strips autoMode from settings.json | AGENTS.md | Rules |
| A126 | AGENTS.md:68 | Client skills are gitignored | AGENTS.md | Rules |
| A127 | AGENTS.md:69 | Do not edit vendored trees: agents/ (27 of 31 from ECC) | AGENTS.md | Rules |
| A128 | AGENTS.md:69 | Do not edit rules/ecc/ except 7 index.md and local additions in code-review.md, testing.md | AGENTS.md | Rules |
| A129 | AGENTS.md:69 | Do not edit skills/anti-ai-writing/ | AGENTS.md | Rules |
| A130 | AGENTS.md:69 | Provenance in NOTICE.md; update it when adding authored or redistributed path | AGENTS.md | Rules |
| A131 | AGENTS.md:70 | ASCII only in repo-owned markdown | AGENTS.md | Rules |
| A132 | AGENTS.md:71 | Conventional Commits with listed prefixes | AGENTS.md | Rules |
| A133 | AGENTS.md:71 | A gsd hook enforces the commit format | AGENTS.md | Rules |
| A134 | AGENTS.md:72 | Comments explain why, naming the past failure | AGENTS.md | Rules |
| A135 | AGENTS.md:73 | Self-checks are the tests; script changes ship with their assertion | AGENTS.md | Rules |
| A136 | AGENTS.md:74 | Banned attribution phrase in tests built from two joined halves | AGENTS.md | Rules |
| A137 | AGENTS.md:74 | Push scan pr.attribution_hits never relaxed for tests (spec 0045) | AGENTS.md | Rules |
| A138 | AGENTS.md:78 | Root CLAUDE.md only imports AGENTS.md | AGENTS.md | Gotchas |
| A139 | AGENTS.md:78 | Payload copy of ~/.claude/CLAUDE.md is claude-home/CLAUDE.md | AGENTS.md | Gotchas |
| A140 | AGENTS.md:78 | sync.sh overwrites it; install.sh ships it | AGENTS.md | Gotchas |
| A141 | AGENTS.md:78 | It used to sit at the root and load twice (spec 0035 AC-4) | AGENTS.md | Gotchas |
| A142 | AGENTS.md:79 | asciify.py skips agents/, rules/, anti-ai-writing, node_modules/ | AGENTS.md | Gotchas |
| A143 | AGENTS.md:79 | Without --check asciify rewrites files; run --check first | AGENTS.md | Gotchas |
| A144 | AGENTS.md:80 | Middle dot is allowed despite ASCII rule | AGENTS.md | Gotchas |
| A145 | AGENTS.md:80 | It is the scope tag separator wf.py parses; asciify keeps it | AGENTS.md | Gotchas |
| A146 | AGENTS.md:81 | jjstack/ is gitignored /review scratch; reports never enter from there | AGENTS.md | Gotchas |
| A147 | AGENTS.md:82 | Clone lives at ~/dotfiles/claude-config, a submodule of dotfiles | AGENTS.md | Gotchas |
| A148 | AGENTS.md:82 | ~/claude-config is a link to it (spec 0035 migrate step 9) | AGENTS.md | Gotchas |
| A149 | AGENTS.md:82 | Session memory and wf trees keyed by real path | AGENTS.md | Gotchas |
| A150 | AGENTS.md:82 | Links leaving the repo climb four levels to reach ~ | AGENTS.md | Gotchas |
| A151 | AGENTS.md:83 | Private names in ~/.claude/private/ (names.txt, work.md, gitignore, fragments), never in repo | AGENTS.md | Gotchas |
| A152 | AGENTS.md:83 | Without names.txt, sync.sh and every commit fail closed | AGENTS.md | Gotchas |
| A153 | AGENTS.md:83 | sync.sh moves name bearing settings entries into fragments; install.sh merges back | AGENTS.md | Gotchas |
| A154 | AGENTS.md:83 | pre-commit and commit-msg hooks are copies of private-names.py, not links | AGENTS.md | Gotchas |
| A155 | AGENTS.md:83 | After editing the checker, rerun install.sh | AGENTS.md | Gotchas |
| A156 | AGENTS.md:83 | Hit lines print names.txt line number, never the name | AGENTS.md | Gotchas |
| A157 | AGENTS.md:84 | Runner fixtures are flat files in runner/tests/fixtures/*.md | AGENTS.md | Gotchas |
| A158 | AGENTS.md:84 | Tests copy them into docs/scope or .workflow/scope in temp dirs | AGENTS.md | Gotchas |
| A159 | AGENTS.md:84 | .workflow/ is globally gitignored, so a fixture tree there is never committed | AGENTS.md | Gotchas |
| A160 | AGENTS.md:84 | Keep fixtures trimmed and free of client names | AGENTS.md | Gotchas |
| A161 | AGENTS.md:85 | Scripts hardcode ~/.claude/skills/ paths; run through the symlink | AGENTS.md | Gotchas |
| A162 | AGENTS.md:86 | claude -p (2.1.296) never offers AskUserQuestion | AGENTS.md | Gotchas |
| A163 | AGENTS.md:86 | wf run steps ask via DECISION NEEDED plus OPTION lines (spec 0005) | AGENTS.md | Gotchas |
| A164 | AGENTS.md:86 | Rerun verify.md check 1 probe after a Claude Code upgrade | AGENTS.md | Gotchas |
| A165 | AGENTS.md:86 | Android ntfy app cannot type into a topic; reply via topic page in browser | AGENTS.md | Gotchas |
| A166 | AGENTS.md:87 | Scope header issues or mixed: wf rereads linked issue before every call (spec 0024) | AGENTS.md | Gotchas |
| A167 | AGENTS.md:87 | Only gh issue view and one read only gh api graphql query, runner's own env | AGENTS.md | Gotchas |
| A168 | AGENTS.md:87 | call_env drops GH_TOKEN; calls keep their GitHub deny | AGENTS.md | Gotchas |
| A169 | AGENTS.md:87 | A scope repo never runs gh | AGENTS.md | Gotchas |
| A170 | AGENTS.md:87 | Baselines live in wf state folder under issues/ | AGENTS.md | Gotchas |
| A171 | AGENTS.md:88 | Standing answers take run suite, done (spec 0006) | AGENTS.md | Gotchas |
| A172 | AGENTS.md:88 | app start plus app url together (spec 0009) | AGENTS.md | Gotchas |
| A173 | AGENTS.md:88 | With both, verify and debug calls run the app in a bwrap jail with pinned headless chrome-devtools MCP | AGENTS.md | Gotchas |
| A174 | AGENTS.md:88 | app url must be http(s)://localhost, 127.0.0.1 or [::1] with port | AGENTS.md | Gotchas |
| A175 | AGENTS.md:88 | Bumping MCP_PACKAGE reruns spec 0009 probes P2 to P7, updates BROWSER_TOOLS | AGENTS.md | Gotchas |
| A176 | AGENTS.md:88 | parallel: <n> (1 to 4, needs branches: per spec) builds n features at once | AGENTS.md | Gotchas |
| A177 | AGENTS.md:88 | Each parallel feature in own worktree under ~/.local/share/wf-trees/<repo>-<hash>/ | AGENTS.md | Gotchas |
| A178 | AGENTS.md:88 | Repo's own checkout is never switched (spec 0027) | AGENTS.md | Gotchas |
| A179 | AGENTS.md:89 | Spec 0010 rests on design-gate (context: fork) running in claude -p | AGENTS.md | Gotchas |
| A180 | AGENTS.md:89 | design-gate writes .design/audit-report.md; rerun verify.md P1, P2 after upgrade | AGENTS.md | Gotchas |
| A181 | AGENTS.md:89 | Prompt line stops Skill(design); deny only provable with direct claude -p (P3) | AGENTS.md | Gotchas |
| A182 | AGENTS.md:90 | branches: per spec builds on feat/<NNNN>-<slug>, squashed to one commit before first push (spec 0026) | AGENTS.md | Gotchas |
| A183 | AGENTS.md:90 | With push: draft PR the wf process (never a call) pushes and opens draft PR | AGENTS.md | Gotchas |
| A184 | AGENTS.md:90 | Push follows private names and attribution scans (runner/pr.py) | AGENTS.md | Gotchas |
| A185 | AGENTS.md:90 | Refusing pre-push hook keeps branch local, never --no-verify | AGENTS.md | Gotchas |
| A186 | AGENTS.md:90 | Never marks ready; merges only on "merge now" (spec 0031) | AGENTS.md | Gotchas |
| A187 | AGENTS.md:91 | Hand opened PRs configured in ~/.claude/private/pr.json, never in a repo (spec 0031) | AGENTS.md | Gotchas |
| A188 | AGENTS.md:91 | pr.json keyed by owner/name or owner/* | AGENTS.md | Gotchas |
| A189 | AGENTS.md:91 | adopt: true adopts and watches; merge: true allows "merge now" tap | AGENTS.md | Gotchas |
| A190 | AGENTS.md:91 | wf merges itself, never a model | AGENTS.md | Gotchas |
| A191 | AGENTS.md:92 | Review requests on only via "review_requests": true in pr.json (spec 0032) | AGENTS.md | Gotchas |
| A192 | AGENTS.md:92 | Draft call reads only pr.diff and files.txt in a fresh review-<n>/, never a checkout | AGENTS.md | Gotchas |
| A193 | AGENTS.md:92 | Review post (reviews.post) runs only on exact "post as my review" | AGENTS.md | Gotchas |
| A194 | AGENTS.md:93 | Phone channel (spec 0029): make bot with BotFather, then wf telegram init | docs/guides/DAILY-USE.md | Run the runner |
| A195 | AGENTS.md:93 | With telegram.json present wf run uses only Telegram | AGENTS.md | Gotchas |
| A196 | AGENTS.md:93 | Invalid file refuses no_telegram, never falls back; without it ntfy | AGENTS.md | Gotchas |
| A197 | AGENTS.md:93 | Only your chat id can answer; plain message gets a one line hint | AGENTS.md | Gotchas |
| A198 | AGENTS.md:94 | Every wf run call guarded outside the model (spec 0007): stripped credentials, Bash sandbox, hashed hook and git config | AGENTS.md | Gotchas |
| A199 | AGENTS.md:94 | wf run refuses no_sandbox without bwrap and socat on PATH | AGENTS.md | Gotchas |
| A200 | AGENTS.md:94 | After upgrade rerun run-wf-probe.py (about 2 minutes, run with !), record in verify.md | AGENTS.md | Gotchas |
| A201 | AGENTS.md:94 | Model sometimes ignores probe step order; classifier lockout hides later sandbox results | AGENTS.md | Gotchas |
| A202 | AGENTS.md:94 | DENIED push rules have own probe push-rule.sh (default mode, git allowed) | AGENTS.md | Gotchas |
| A203 | AGENTS.md:94 | Run push-rule.sh with !, rerun after upgrade, record in spec 0004 verify.md | AGENTS.md | Gotchas |
| A204 | AGENTS.md:98 | Standing answer run suite: yes | AGENTS.md | Standing answers |
| A205 | AGENTS.md:99 | Standing answer done: yes | AGENTS.md | Standing answers |
| A206 | AGENTS.md:100 | Standing answer branches: per spec | AGENTS.md | Standing answers |
| A207 | AGENTS.md:101 | Standing answer push: draft PR | AGENTS.md | Standing answers |
| A208 | AGENTS.md:102 | Standing answer parallel: 4 | AGENTS.md | Standing answers |
| A209 | AGENTS.md:103 | Standing answer suite: python3 runner/tests/fast.py | AGENTS.md | Standing answers |
| A210 | AGENTS.md:107 | Agent Skill and MCP discovery declined (2026-10-11) | AGENTS.md | Agent skills |
| A211 | AGENTS.md:111 | Context file: skills/design/AGENTS.md, design scripts, ledger, Stop hook | AGENTS.md | Context files |
| A212 | AGENTS.md:113 | Drafted by /audit; curated lines are flagged, not overwritten | AGENTS.md | dropped: the /audit draft marker; the file is now curated by hand, so later /audit runs flag rather than overwrite it |

## docs/architecture.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| H1 | docs/architecture.md:1 | Title: Runner architecture | docs/architecture.md | (title) |
| H2 | docs/architecture.md:3 | One page view: parts, data flow, rules everywhere | docs/architecture.md | (intro) |
| H3 | docs/architecture.md:3 | /architect reads this first and updates it when an invariant changes | docs/architecture.md | (intro) |
| H4 | docs/architecture.md:3 | Spec link list 0001 to 0020 with short names | docs/architecture.md | Specs |
| H5 | docs/architecture.md:5 | Goal: builds scoped features overnight, pings only for decisions, never pushes or designs | docs/architecture.md | (intro) |
| H6 | docs/architecture.md:11 | Part: scope files, the plan and queue, boxes, tags, header | docs/architecture.md | Components |
| H7 | docs/architecture.md:12 | Part: specs, written by /architect only | docs/architecture.md | Components |
| H8 | docs/architecture.md:13 | Part: AGENTS.md standing answers, reread only to stop on change | docs/architecture.md | Components |
| H9 | docs/architecture.md:14 | Part: bare wf, the one command (spec 0020) | docs/architecture.md | Components |
| H10 | docs/architecture.md:15 | Part: next, interactive launcher | docs/architecture.md | Components |
| H11 | docs/architecture.md:16 | Part: wf run, unattended loop, queue (spec 0011) | docs/architecture.md | Components |
| H12 | docs/architecture.md:17 | Part: wf report (spec 0018) | docs/architecture.md | Components |
| H13 | docs/architecture.md:18 | Part: wf finish, live boxes, no repo lock (spec 0019) | docs/architecture.md | Components |
| H14 | docs/architecture.md:19 | Part: wf queue and wf unpark | docs/architecture.md | Components |
| H15 | docs/architecture.md:20 | Part: claude -p calls, prompt, brief, deny list, budget, timeout | docs/architecture.md | Components |
| H16 | docs/architecture.md:21 | Part: phone channel, Telegram or ntfy (spec 0029) | docs/architecture.md | Components |
| H17 | docs/architecture.md:22 | Part: runner copy per content fingerprint (spec 0020 AC-12) | docs/architecture.md | Components |
| H18 | docs/architecture.md:23 | Part: state folder layout (spec 0014, 0011, 0018, 0019) | docs/architecture.md | Components |
| H19 | docs/architecture.md:24 | Part: hooks that run inside every claude -p call | docs/architecture.md | Components |
| H20 | docs/architecture.md:25 | Part: always loaded rules (scope-contract, spec-gate, handoff, check-gates, lessons) | docs/architecture.md | Components |
| H21 | docs/architecture.md:26 | Part: app jail and browser under bwrap (spec 0009) | docs/architecture.md | Components |
| H22 | docs/architecture.md:27 | Part: autonomous mode, /auto on (spec 0030) | docs/architecture.md | Components |
| H23 | docs/architecture.md:28 | Part: inhibitor keeps machine awake | docs/architecture.md | Components |
| H24 | docs/architecture.md:32-53 | Data flow diagram from /architect to feature finished | docs/architecture.md | Data flow |
| H25 | docs/architecture.md:46-47 | Run stop goes to run.json; repo stop goes to next repo | docs/architecture.md | Data flow |
| H26 | docs/architecture.md:48-52 | Park, DECISION NEEDED, next box, feature done paths | docs/architecture.md | Data flow |
| H27 | docs/architecture.md:55 | Run picks answered questions first, then queued features; waits --max-wait | docs/architecture.md | Data flow |
| H28 | docs/architecture.md:55 | "Spec 0011 is not built yet" statement | docs/architecture.md | Data flow |
| H29 | docs/architecture.md:57 | A call never reports a box done; wf believes only files | docs/architecture.md | Data flow |
| H30 | docs/architecture.md:57 | Only scrubbed ping text leaves the machine | docs/architecture.md | Data flow |
| H31 | docs/architecture.md:61 | Inv 1: calls never push or merge; never marks PR ready | docs/architecture.md | Invariants (hold everywhere) |
| H32 | docs/architecture.md:61 | Inv 1: draft PR flow pushes only spec branches after scans (spec 0026) | docs/architecture.md | Invariants (hold everywhere) |
| H33 | docs/architecture.md:61 | Inv 1: adopt: true adopts own open PRs (spec 0031) | docs/architecture.md | Invariants (hold everywhere) |
| H34 | docs/architecture.md:61 | Inv 1: merge only via gh pr merge --match-head-commit after exact "merge now" | docs/architecture.md | Invariants (hold everywhere) |
| H35 | docs/architecture.md:61 | Inv 1: foreign change to code-running files stops adopted PR calls (spec 0031 AC-12) | docs/architecture.md | Invariants (hold everywhere) |
| H36 | docs/architecture.md:61 | Inv 1: review_requests posts review only on exact "post as my review" (spec 0032) | docs/architecture.md | Invariants (hold everywhere) |
| H37 | docs/architecture.md:61 | Inv 1: draft call reads PR as text only, hooks off, no MCP, no network | docs/architecture.md | Invariants (hold everywhere) |
| H38 | docs/architecture.md:61 | Inv 1: wf run runs no git write; wf finish makes one local commit (spec 0019) | docs/architecture.md | Invariants (hold everywhere) |
| H39 | docs/architecture.md:61 | Inv 1: prompt line and deny list are a backstop; env git push and gh api get past (review 2026-10-12) | docs/architecture.md | Invariants (hold everywhere) |
| H40 | docs/architecture.md:61 | Inv 1: spec 0007 holds it outside model: no credential, Bash sandbox, tool denies, hashed files | docs/architecture.md | Invariants (hold everywhere) |
| H41 | docs/architecture.md:61 | Inv 1: threat model is accidental or injected push, not an escaping model | docs/architecture.md | Invariants (hold everywhere) |
| H42 | docs/architecture.md:61 | Inv 1: same threat model for app and browser (spec 0009); no more hardening rounds | docs/architecture.md | Invariants (hold everywhere) |
| H43 | docs/architecture.md:62 | Inv 2: never decides design or accepts a spec unattended | docs/architecture.md | Invariants (hold everywhere) |
| H44 | docs/architecture.md:62 | Inv 2: boxes not on the allow list are refused | docs/architecture.md | Invariants (hold everywhere) |
| H45 | docs/architecture.md:62 | Inv 2: accepting a spec has no standing answer, never will (spec 0006) | docs/architecture.md | Invariants (hold everywhere) |
| H46 | docs/architecture.md:62 | Inv 2: unfixed panels become pings | docs/architecture.md | Invariants (hold everywhere) |
| H47 | docs/architecture.md:62 | Inv 2: UI with no locked design parks blocked; design, brand-system denied in calls | docs/architecture.md | Invariants (hold everywhere) |
| H48 | docs/architecture.md:62 | Inv 2: frontend change closes only with fresh design-gate report, else parks design_gate (spec 0010) | docs/architecture.md | Invariants (hold everywhere) |
| H49 | docs/architecture.md:63 | Inv 3: paid steps never run unattended; not on allow list | docs/architecture.md | Invariants (hold everywhere) |
| H50 | docs/architecture.md:63 | Inv 3: light /code-review only inside spec 0032 isolated call, never ultra | docs/architecture.md | Invariants (hold everywhere) |
| H51 | docs/architecture.md:63 | Inv 3: no API key, token, secret or cloud credential reaches a call (spec 0008) | docs/architecture.md | Invariants (hold everywhere) |
| H52 | docs/architecture.md:64 | Inv 4: pings only for DECISION NEEDED and spec 0026, 0031, 0032 questions | docs/architecture.md | Invariants (hold everywhere) |
| H53 | docs/architecture.md:64 | Inv 4: short ack after your reply (spec 0033); question carries from: block | docs/architecture.md | Invariants (hold everywhere) |
| H54 | docs/architecture.md:64 | Inv 4: one re-ping per run for earlier open question (spec 0011) | docs/architecture.md | Invariants (hold everywhere) |
| H55 | docs/architecture.md:64 | Inv 4: self started test pings, wf connected message, one line hint (spec 0029) | docs/architecture.md | Invariants (hold everywhere) |
| H56 | docs/architecture.md:64 | Inv 4: one morning report note when a run ends (spec 0018) | docs/architecture.md | Invariants (hold everywhere) |
| H57 | docs/architecture.md:64 | Inv 4: no other ping for start, finish or failure | docs/architecture.md | Invariants (hold everywhere) |
| H58 | docs/architecture.md:65 | Inv 5: never automatic: Autopilot allowed, auto tag, accept spec, tier | docs/architecture.md | Invariants (hold everywhere) |
| H59 | docs/architecture.md:65 | Inv 5: starting a run is yours; wf auto start counts as started by you (spec 0030) | docs/architecture.md | Invariants (hold everywhere) |
| H60 | docs/architecture.md:65 | Inv 5: push or PR outside opt in repos, marking ready, merge without "merge now", design direction | docs/architecture.md | Invariants (hold everywhere) |
| H61 | docs/architecture.md:65 | Inv 5: marking done only via done: yes on the box wf computed as last (spec 0006) | docs/architecture.md | Invariants (hold everywhere) |
| H62 | docs/architecture.md:66 | Inv 6: run needs Autopilot allowed, wf allow, named branch, repo lock (spec 0008) | docs/architecture.md | Invariants (hold everywhere) |
| H63 | docs/architecture.md:66 | Inv 6: feature needs auto tag and ticked (spec) box (spec 0011) | docs/architecture.md | Invariants (hold everywhere) |
| H64 | docs/architecture.md:66 | Inv 6: one call at a time per repo; bare wf run one child per repo (spec 0017) | docs/architecture.md | Invariants (hold everywhere) |
| H65 | docs/architecture.md:66 | Inv 6: one feature at a time per repo; touched repos locked until exit | docs/architecture.md | Invariants (hold everywhere) |
| H66 | docs/architecture.md:66 | Inv 6: lock takers write holder line; wf skips a held repo (spec 0020) | docs/architecture.md | Invariants (hold everywhere) |
| H67 | docs/architecture.md:66 | Inv 6: swaps.jsonl fingerprints let a run take a live setup change | docs/architecture.md | Invariants (hold everywhere) |
| H68 | docs/architecture.md:66 | Inv 6: dirty repo with park or question starts no other feature | docs/architecture.md | Invariants (hold everywhere) |
| H69 | docs/architecture.md:66 | Inv 6: Autopilot, branch, scope rechecked after every call and wait | docs/architecture.md | Invariants (hold everywhere) |
| H70 | docs/architecture.md:66 | Inv 6: parallel: N exception, own worktree per feature, combined at end (specs 0027, 0043) | docs/architecture.md | Invariants (hold everywhere) |
| H71 | docs/architecture.md:67 | Inv 7: box done only when scope says so | docs/architecture.md | Invariants (hold everywhere) |
| H72 | docs/architecture.md:67 | Inv 7: wf run writes nothing in a repo; only calls do | docs/architecture.md | Invariants (hold everywhere) |
| H73 | docs/architecture.md:67 | Inv 7: wf finish ticks live boxes and appends to verify.md (spec 0019) | docs/architecture.md | Invariants (hold everywhere) |
| H74 | docs/architecture.md:68 | Inv 8: budget and timeout per call; call and hour caps per run | docs/architecture.md | Invariants (hold everywhere) |
| H75 | docs/architecture.md:68 | Inv 8: wait cap per decision; clean stop on Ctrl C, SIGHUP, SIGTERM | docs/architecture.md | Invariants (hold everywhere) |
| H76 | docs/architecture.md:68 | Inv 8: max 2 /debug calls; usage limit wait 6 h; 91 minutes outage waits (spec 0014) | docs/architecture.md | Invariants (hold everywhere) |
| H77 | docs/architecture.md:68 | Inv 8: crash_loop stop when two features park with same error | docs/architecture.md | Invariants (hold everywhere) |
| H78 | docs/architecture.md:68 | Inv 8: 120 s app ready; sweep of WF_RUN processes (spec 0009) | docs/architecture.md | Invariants (hold everywhere) |
| H79 | docs/architecture.md:68 | Inv 8: run.json with stop reason on every path | docs/architecture.md | Invariants (hold everywhere) |
| H80 | docs/architecture.md:68 | Inv 8: reasons are park, repo stop or run stop (specs 0008, 0011) | docs/architecture.md | Invariants (hold everywhere) |
| H81 | docs/architecture.md:68 | Inv 8: --max-calls and 2 debug attempts per feature; --max-hours, limit wait, --max-wait per run | docs/architecture.md | Invariants (hold everywhere) |
| H82 | docs/architecture.md:72 | wf run decides by first word of box command, two for /check verify | docs/architecture.md | Skills and commands under wf run |
| H83 | docs/architecture.md:72 | Unlisted commands refused manual_box or stop the run | docs/architecture.md | Skills and commands under wf run |
| H84 | docs/architecture.md:72 | Waiting box refused waiting before command check (spec 0012) | docs/architecture.md | Skills and commands under wf run |
| H85 | docs/architecture.md:72 | later boxes go on tag lets build pass; final /sync waits (spec 0014) | docs/architecture.md | Skills and commands under wf run |
| H86 | docs/architecture.md:76 | /develop runs; pings for owed decision or unfixed panel | docs/architecture.md | Skills and commands under wf run |
| H87 | docs/architecture.md:77 | /check verify runs; drives app when named (spec 0009) | docs/architecture.md | Skills and commands under wf run |
| H88 | docs/architecture.md:77 | /check verify runs design-gate on frontend change (spec 0010) | docs/architecture.md | Skills and commands under wf run |
| H89 | docs/architecture.md:77 | Pass without CAN FAIL CHECKED line parks unchecked (spec 0015) | docs/architecture.md | Skills and commands under wf run |
| H90 | docs/architecture.md:77 | /check verify pings for done offer unless done: yes | docs/architecture.md | Skills and commands under wf run |
| H91 | docs/architecture.md:78 | /test runs; pass without MUTATION CHECKED parks unchecked | docs/architecture.md | Skills and commands under wf run |
| H92 | docs/architecture.md:78 | /test pings for Run tests? unless run suite: yes; done offer unless done: yes | docs/architecture.md | Skills and commands under wf run |
| H93 | docs/architecture.md:79 | /debug runs; pings for a fix choice it cannot make | docs/architecture.md | Skills and commands under wf run |
| H94 | docs/architecture.md:80 | /document runs; Doc type fixed answer | docs/architecture.md | Skills and commands under wf run |
| H95 | docs/architecture.md:81 | /sync runs only as final call of a feature (spec 0014) | docs/architecture.md | Skills and commands under wf run |
| H96 | docs/architecture.md:82 | /architect, /scope, /audit refused | docs/architecture.md | Skills and commands under wf run |
| H97 | docs/architecture.md:83 | design, design-gate, brand-system, assets as a box refused; in a call design and brand-system denied, design-gate runs | docs/architecture.md | Skills and commands under wf run |
| H98 | docs/architecture.md:84 | /check review, other /check words, /review, /code-review, /review-stack, /jj-security-review refused | docs/architecture.md | Skills and commands under wf run |
| H99 | docs/architecture.md:85 | /ship, /pr, /land-and-deploy, /document-release, deploys refused | docs/architecture.md | Skills and commands under wf run |
| H100 | docs/architecture.md:86 | /rollover, /save-and-clear, /resume-from-clear, /clear refused | docs/architecture.md | Skills and commands under wf run |
| H101 | docs/architecture.md:87 | Any other command refused | docs/architecture.md | Skills and commands under wf run |
| H102 | docs/architecture.md:88 | Box with no command stops (exit 3 at start, no_command mid run) | docs/architecture.md | Skills and commands under wf run |
| H103 | docs/architecture.md:90 | Fixed answers: Doc type recommended, Save verify steps to verify.md, Agent skills not now (spec 0005) | docs/architecture.md | Skills and commands under wf run |
| H104 | docs/architecture.md:90 | Standing answers per repo: run suite and done (spec 0006) | docs/architecture.md | Skills and commands under wf run |
| H105 | docs/architecture.md:90 | No standing answer touches a design or spec panel | docs/architecture.md | Skills and commands under wf run |
| H106 | docs/architecture.md:92 | next is not bound by this table; opens any command after your Enter | docs/architecture.md | Skills and commands under wf run |

# Docs map part B (SKILLS, PLUGINS, MCP, SKILLS-EVALUATION)

Planned destinations come from docs-plan.md. `config/manifest.json` headings name the field that records the fact.

## docs/guides/SKILLS.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| S1 | docs/guides/SKILLS.md:1 | Page title: Skills | docs/guides/SETUP.md | `## Downloaded skills` |
| S2 | docs/guides/SKILLS.md:3 | Skills outside plugins; reinstall by hand on a new machine (now: restore from manifest) | docs/guides/SETUP.md | `## Downloaded skills` |
| S3 | docs/guides/SKILLS.md:5 | Versions table last verified 2026-09-02 (dated heading) | docs/guides/SKILLS.md | `dropped: dated history note; versions kept in rows below` |
| S4 | docs/guides/SKILLS.md:9 | gstack version 1.79.0.0 | docs/guides/SETUP.md | `## Keep it current` |
| S5 | docs/guides/SKILLS.md:9 | gstack update: git merge --ff-only origin/main then ./setup | config/manifest.json | `frameworks.gstack.install` |
| S6 | docs/guides/SKILLS.md:10 | jjstack version 0.36.0 | docs/guides/SETUP.md | `## Keep it current` |
| S7 | docs/guides/SKILLS.md:10 | jjstack update: same steps in its folder | docs/guides/SETUP.md | `## Keep it current` |
| S8 | docs/guides/SKILLS.md:10 | Stash the local hooks/auto-approve-safe.sh tweak before updating jjstack | docs/guides/SETUP.md | `## Keep it current` |
| S9 | docs/guides/SKILLS.md:11 | get-shit-done-cc 1.34.2 is pinned | config/manifest.json | `frameworks.get-shit-done.pinned` |
| S10 | docs/guides/SKILLS.md:11 | Do not run npx get-shit-done-cc to update | docs/guides/SETUP.md | `## Keep it current` |
| S11 | docs/guides/SKILLS.md:12 | impeccable version 4.1.3 | docs/guides/SETUP.md | `## Keep it current` |
| S12 | docs/guides/SKILLS.md:12 | impeccable update: npx skills add pbakaus/impeccable --skill impeccable -a claude-code -g -y | config/manifest.json | `entries.impeccable.install` |
| S13 | docs/guides/SKILLS.md:13 | graphify version 0.9.53 | docs/guides/SETUP.md | `## Keep it current` |
| S14 | docs/guides/SKILLS.md:13 | graphify update: pipx upgrade graphifyy then graphify install claude | docs/guides/SETUP.md | `## Keep it current` |
| S15 | docs/guides/SKILLS.md:14 | @21st-dev/cli version 1.17.0 | docs/guides/SETUP.md | `## Keep it current` |
| S16 | docs/guides/SKILLS.md:14 | 21st CLI update: npm install -g @21st-dev/cli@latest | docs/guides/SETUP.md | `## Keep it current` |
| S17 | docs/guides/SKILLS.md:15 | Claude Code version 2.1.259 | docs/guides/SETUP.md | `## Keep it current` |
| S18 | docs/guides/SKILLS.md:15 | Claude Code update: claude update | docs/guides/SETUP.md | `## Keep it current` |
| S19 | docs/guides/SKILLS.md:17 | Router, taste, motion, security-review, sentry and other sets re-pulled 2026-09-02 and current | docs/guides/SKILLS.md | `dropped: dated history note; each skill is listed with its source in the manifest` |
| S20 | docs/guides/SKILLS.md:22 | ECC cherry-pick is deliberately frozen | docs/guides/SETUP.md | `## Frameworks` |
| S21 | docs/guides/SKILLS.md:23 | Upstream ECC has 41 more agents and 15 more language rule folders we lack | docs/guides/SETUP.md | `## Frameworks` |
| S22 | docs/guides/SKILLS.md:24 | Local rules carry hand-earned additions; re-copying upstream would overwrite them | docs/guides/SETUP.md | `## Frameworks` |
| S23 | docs/guides/SKILLS.md:25 | Adopt ECC changes selectively by hand, or not at all | docs/guides/SETUP.md | `## Frameworks` |
| S24 | docs/guides/SKILLS.md:27 | Added 2026-08-06 with git clone --depth=1, no pinned version | docs/guides/SKILLS.md | `dropped: dated history note; each skill is in the manifest` |
| S25 | docs/guides/SKILLS.md:28 | Sets added: emilkowalski (9), gsap (8), threejs (10), transitions.dev (2), design-dna, humanizer, 12 marketingskills | docs/guides/SKILLS.md | `## Downloaded skills` |
| S26 | docs/guides/SKILLS.md:29 | packshot is zip only, back it up | docs/guides/SKILLS.md | `## Downloaded skills` |
| S27 | docs/guides/SKILLS.md:30 | Sections below carry the install command for each skill | docs/guides/SKILLS.md | `dropped: pointer to this file's own sections` |
| S28 | docs/guides/SKILLS.md:32 | Upgrade order: gstack ./setup first, then jjstack's | docs/guides/SETUP.md | `## Keep it current` |
| S29 | docs/guides/SKILLS.md:33 | gstack setup overwrites shared skill symlinks (qa, review, ship, office-hours) | docs/guides/SETUP.md | `## Keep it current` |
| S30 | docs/guides/SKILLS.md:34 | jjstack setup re-points them at jjstack wrappers | docs/guides/SETUP.md | `## Keep it current` |
| S31 | docs/guides/SKILLS.md:34 | /jjstack-repair fixes a wrong upgrade order | docs/guides/SETUP.md | `## Keep it current` |
| S32 | docs/guides/SKILLS.md:37 | Section: Skill frameworks | docs/guides/SKILLS.md | `## Frameworks` |
| S33 | docs/guides/SKILLS.md:39 | Only jjstack is needed; it installs gstack as a dependency | docs/guides/SETUP.md | `## Frameworks` |
| S34 | docs/guides/SKILLS.md:41 | jjstack heading | docs/guides/SKILLS.md | `## Frameworks` |
| S35 | docs/guides/SKILLS.md:42 | jjstack source is in the private work.md | config/manifest.json | `frameworks.jjstack.source` |
| S36 | docs/guides/SKILLS.md:45 | git clone the jjstack source into ~/.claude/skills/jjstack | config/manifest.json | `frameworks.jjstack.install` |
| S37 | docs/guides/SKILLS.md:46 | cd into jjstack and run ./setup | config/manifest.json | `frameworks.jjstack.install` |
| S38 | docs/guides/SKILLS.md:48 | jjstack setup clones and sets up garrytan/gstack if missing | docs/guides/SETUP.md | `## Frameworks` |
| S39 | docs/guides/SKILLS.md:48 | gstack need not be installed separately | docs/guides/SETUP.md | `## Frameworks` |
| S40 | docs/guides/SKILLS.md:50 | jjstack adds a product/UX layer on gstack: code quality, product, developer experience | docs/guides/SKILLS.md | `## Frameworks` |
| S41 | docs/guides/SKILLS.md:50 | All jjstack skills are symlinked into ~/.claude/skills/ | docs/guides/SETUP.md | `## Frameworks` |
| S42 | docs/guides/SKILLS.md:52 | jjstack 0.36.0 new: /antigravity and /deepseek second opinions, beside /codex | docs/guides/SKILLS.md | `## Frameworks` |
| S43 | docs/guides/SKILLS.md:54 | jjstack new: /consensus four-vendor panel | docs/guides/SKILLS.md | `## Frameworks` |
| S44 | docs/guides/SKILLS.md:55 | jjstack new: /groom dedups memories and skills | docs/guides/SKILLS.md | `## Frameworks` |
| S45 | docs/guides/SKILLS.md:56 | jjstack new: /plan-edit sectioned plan edits with diffs | docs/guides/SKILLS.md | `## Frameworks` |
| S46 | docs/guides/SKILLS.md:56 | jjstack new: /qa-build-loop replaces removed /qa-loop | docs/guides/SKILLS.md | `## Frameworks` |
| S47 | docs/guides/SKILLS.md:57 | jjstack new: /reconnect-mcp | docs/guides/SKILLS.md | `## Frameworks` |
| S48 | docs/guides/SKILLS.md:57 | jjstack new: /save-and-clear, /save-and-exit, /resume-from-clear and /rollover | docs/guides/SKILLS.md | `## Frameworks` |
| S49 | docs/guides/SKILLS.md:60 | Known jjstack 0.36.0 bug: reconstruct_cwd cannot undo a slug with a dot folder | docs/guides/SETUP.md | `## Frameworks` |
| S50 | docs/guides/SKILLS.md:62 | Claude Code encodes / and . both as -, so the path resolves wrong | docs/guides/SETUP.md | `## Frameworks` |
| S51 | docs/guides/SKILLS.md:63 | Causes the one test/smoke.sh failure; that test also hardcodes the author's path | docs/guides/SETUP.md | `## Frameworks` |
| S52 | docs/guides/SKILLS.md:65 | Impact today none: only gbrain paths call it and gbrain is not installed | docs/guides/SETUP.md | `## Frameworks` |
| S53 | docs/guides/SKILLS.md:67 | Left unpatched on purpose: a second local diff costs more than it saves | docs/guides/SETUP.md | `## Frameworks` |
| S54 | docs/guides/SKILLS.md:69 | Re-check after any jjstack upgrade and before /setup-gbrain | docs/guides/SETUP.md | `## Keep it current` |
| S55 | docs/guides/SKILLS.md:71 | Permission gate is jjstack permission-floor.py plus deny rules from hooks/permissions.policy.json | docs/guides/SETUP.md | `## Frameworks` |
| S56 | docs/guides/SKILLS.md:72 | No local jjstack diff is kept any more | docs/guides/SETUP.md | `## Frameworks` |
| S57 | docs/guides/SKILLS.md:74 | gstack adds /autoplan, /investigate, /qa, /ship, /review, /office-hours, /retro, browser automation | docs/guides/SKILLS.md | `## Frameworks` |
| S58 | docs/guides/SKILLS.md:74 | gstack does not add the gsd-* skills | docs/guides/SKILLS.md | `## Frameworks` |
| S59 | docs/guides/SKILLS.md:78 | get-shit-done-cc heading: installs gsd-* skills | docs/guides/SKILLS.md | `## Frameworks` |
| S60 | docs/guides/SKILLS.md:79 | GSD source: github.com/gsd-build/get-shit-done | config/manifest.json | `frameworks.get-shit-done.source` |
| S61 | docs/guides/SKILLS.md:80 | GSD npm package get-shit-done-cc | config/manifest.json | `frameworks.get-shit-done.source` |
| S62 | docs/guides/SKILLS.md:83 | GSD install: npx get-shit-done-cc | config/manifest.json | `frameworks.get-shit-done.install` |
| S63 | docs/guides/SKILLS.md:85 | Pinned at 1.34.2 on purpose; do not upgrade blind | config/manifest.json | `frameworks.get-shit-done.pinned` |
| S64 | docs/guides/SKILLS.md:85 | Upstream is on 1.42.3 | docs/guides/SKILLS.md | `dropped: dated upstream version note` |
| S65 | docs/guides/SKILLS.md:86 | gsd-* skills purged on purpose, commit 33f5b27 | docs/guides/SETUP.md | `## Frameworks` |
| S66 | docs/guides/SKILLS.md:87 | Rerunning npx get-shit-done-cc reinstalls 50+ skills and undoes the purge | docs/guides/SETUP.md | `## Frameworks` |
| S67 | docs/guides/SKILLS.md:88 | Only what the hooks still need is kept | docs/guides/SETUP.md | `## Frameworks` |
| S68 | docs/guides/SKILLS.md:90 | Load-bearing: ~/.claude/get-shit-done/ workflow engine read by gsd hooks | docs/guides/SETUP.md | `## Frameworks` |
| S69 | docs/guides/SKILLS.md:92 | Load-bearing: ~/.claude/gsd-file-manifest.json | docs/guides/SETUP.md | `## Frameworks` |
| S70 | docs/guides/SKILLS.md:93 | Load-bearing: gsd-* hooks in ~/.claude/hooks/ wired in settings.json | docs/guides/SETUP.md | `## Frameworks` |
| S71 | docs/guides/SKILLS.md:95 | No ~/.claude/skills/gsd-* skill is installed, on purpose | docs/guides/SETUP.md | `## Frameworks` |
| S72 | docs/guides/SKILLS.md:98 | Correction: listed sub-skills (dev-philosophy, heal, kano-model, lean ... github-setup) come from jjstack, not GSD | docs/guides/SKILLS.md | `## Frameworks` |
| S73 | docs/guides/SKILLS.md:103 | They are symlinks into ~/.claude/skills/jjstack/skills/ | docs/guides/SKILLS.md | `## Frameworks` |
| S74 | docs/guides/SKILLS.md:104 | /council is jjstack too, not standalone tsenart/council-skill | docs/guides/SKILLS.md | `## Frameworks` |
| S75 | docs/guides/SKILLS.md:109 | Section: Routing | docs/guides/SKILLS.md | `## Routing` |
| S76 | docs/guides/SKILLS.md:111 | skill-router heading | docs/guides/SKILLS.md | `## Routing` |
| S77 | docs/guides/SKILLS.md:112 | skill-router source github.com/chrishan17/skill-router | config/manifest.json | `entries.skill-router.source` |
| S78 | docs/guides/SKILLS.md:115 | skill-router install: npx skills add chrishan17/skill-router/skills/skill-router -a claude-code -g -y | config/manifest.json | `entries.skill-router.install` |
| S79 | docs/guides/SKILLS.md:117 | skill-router groups skills behind one entry, fixes trigger reliability, cuts context bloat, 40+ agents | docs/guides/SKILLS.md | `## Routing` |
| S80 | docs/guides/SKILLS.md:118 | skill-router always active, intercepts skill selection | docs/guides/SKILLS.md | `## Routing` |
| S81 | docs/guides/SKILLS.md:122 | intent-router heading | docs/guides/SKILLS.md | `## Routing` |
| S82 | docs/guides/SKILLS.md:123 | intent-router source is this repo claude-home/skills/intent-router/SKILL.md | docs/guides/SKILLS.md | `## Your own skills` |
| S83 | docs/guides/SKILLS.md:126 | intent-router install: mkdir and cp SKILL.md into ~/.claude/skills | docs/guides/SETUP.md | `## Restore on a new machine` |
| S84 | docs/guides/SKILLS.md:129 | Fresh clone alternative: git clone Gartner24/claude-config then cp SKILL.md | docs/guides/SETUP.md | `## Restore on a new machine` |
| S85 | docs/guides/SKILLS.md:135 | intent-router reads USAGE.md at runtime, scores TRIGGERS/BLOCKS/PRIORITY, invokes best match | docs/guides/SKILLS.md | `## Routing` |
| S86 | docs/guides/SKILLS.md:135 | Fires only on ambiguous prompts, silent otherwise | docs/guides/SKILLS.md | `## Routing` |
| S87 | docs/guides/SKILLS.md:136 | Requires USAGE.md; falls back to a built-in table | docs/guides/SKILLS.md | `## Routing` |
| S88 | docs/guides/SKILLS.md:137 | Personal rules baked in | docs/guides/SKILLS.md | `## Routing` |
| S89 | docs/guides/SKILLS.md:138 | mem-search fires first on memory-check signals | docs/guides/SKILLS.md | `## Routing` |
| S90 | docs/guides/SKILLS.md:139 | council fires before implement skills on decision signals | docs/guides/SKILLS.md | `## Routing` |
| S91 | docs/guides/SKILLS.md:140 | Motion dispatch: animate, transitions-dev, gsap-*, apple-design, review-animations | docs/guides/SKILLS.md | `## Routing` |
| S92 | docs/guides/SKILLS.md:141 | investigate wins on runtime bugs; build/type errors go to build-fix and resolvers | docs/guides/SKILLS.md | `## Routing` |
| S93 | docs/guides/SKILLS.md:143 | New skill: add a routing block to USAGE.md and commit | docs/guides/SKILLS.md | `## Routing` |
| S94 | docs/guides/SKILLS.md:144 | intent-router always active | docs/guides/SKILLS.md | `## Routing` |
| S95 | docs/guides/SKILLS.md:148 | Section: Decision-making | docs/guides/SKILLS.md | `## Routing` |
| S96 | docs/guides/SKILLS.md:150 | council heading | docs/guides/SKILLS.md | `## Frameworks` |
| S97 | docs/guides/SKILLS.md:151 | council comes from jjstack; symlink, updates with jjstack; nothing separate to install | docs/guides/SKILLS.md | `## Frameworks` |
| S98 | docs/guides/SKILLS.md:152 | It superseded standalone tsenart/council-skill | docs/guides/SKILLS.md | `## Frameworks` |
| S99 | docs/guides/SKILLS.md:154 | council: independent analysis, cross-examination, final verdict | docs/guides/SKILLS.md | `## Frameworks` |
| S100 | docs/guides/SKILLS.md:155 | 0.36.0 adds automatic Competitor-did-it pass on an impossible verdict | docs/guides/SKILLS.md | `## Frameworks` |
| S101 | docs/guides/SKILLS.md:157 | council use: architecture, strategy, risk, launch decisions, multi-cause debugging | docs/guides/SKILLS.md | `## Frameworks` |
| S102 | docs/guides/SKILLS.md:158 | /consensus runs the idea across Claude, Codex, AGY, DeepSeek | docs/guides/SKILLS.md | `## Frameworks` |
| S103 | docs/guides/SKILLS.md:163 | Section: Design typography and quality | docs/guides/SKILLS.md | `## Downloaded skills` |
| S104 | docs/guides/SKILLS.md:165 | impeccable heading | docs/guides/SKILLS.md | `## Downloaded skills` |
| S105 | docs/guides/SKILLS.md:166 | impeccable source github.com/pbakaus/impeccable | config/manifest.json | `entries.impeccable.source` |
| S106 | docs/guides/SKILLS.md:169 | impeccable install command | config/manifest.json | `entries.impeccable.install` |
| S107 | docs/guides/SKILLS.md:171 | impeccable: 23 design commands, 61 anti-pattern rules, built on frontend-design | docs/guides/SKILLS.md | `## Downloaded skills` |
| S108 | docs/guides/SKILLS.md:172 | impeccable current version 4.1.3 | docs/guides/SETUP.md | `## Keep it current` |
| S109 | docs/guides/SKILLS.md:173 | impeccable key commands: critique, audit, polish, shape, bolder, quieter, distill, animate, live | docs/guides/SKILLS.md | `## Downloaded skills` |
| S110 | docs/guides/SKILLS.md:174 | Run critique and audit before shipping UI; audit is technical, critique is UX | docs/guides/SKILLS.md | `## Downloaded skills` |
| S111 | docs/guides/SKILLS.md:175 | v4: teach is gone, use /impeccable init (PRODUCT.md) and document (DESIGN.md) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S112 | docs/guides/SKILLS.md:175 | v4: craft is a deprecated alias | docs/guides/SKILLS.md | `## Downloaded skills` |
| S113 | docs/guides/SKILLS.md:175 | v4: subagents ship as .toml/.yaml under agents/ | docs/guides/SKILLS.md | `## Downloaded skills` |
| S114 | docs/guides/SKILLS.md:179 | Section: Design motion | docs/guides/SKILLS.md | `## Downloaded skills` |
| S115 | docs/guides/SKILLS.md:181 | design-motion-principles heading | docs/guides/SKILLS.md | `## Downloaded skills` |
| S116 | docs/guides/SKILLS.md:182 | design-motion-principles source kylezantos/design-motion-principles | config/manifest.json | `entries.design-motion-principles.source` |
| S117 | docs/guides/SKILLS.md:185 | clone upstream to /tmp/dmp | config/manifest.json | `entries.design-motion-principles.install` |
| S118 | docs/guides/SKILLS.md:186 | mkdir ~/.claude/skills/design-motion-principles | config/manifest.json | `entries.design-motion-principles.install` |
| S119 | docs/guides/SKILLS.md:187 | cp -a skills/design-motion-principles contents into skills folder | config/manifest.json | `entries.design-motion-principles.install` |
| S120 | docs/guides/SKILLS.md:188 | remove the temp clone | config/manifest.json | `entries.design-motion-principles.install` |
| S121 | docs/guides/SKILLS.md:190 | Per-file curl loop replaced 2026-07-29 because a fixed list skipped new reference files | docs/guides/SKILLS.md | `dropped: dated history note; manifest install copies the whole folder` |
| S122 | docs/guides/SKILLS.md:193 | Three lenses: Kowalski restraint, Krehel polish, Tompkins creative; build and audit modes | docs/guides/SKILLS.md | `## Downloaded skills` |
| S123 | docs/guides/SKILLS.md:194 | Use for UI with motion; run audit before shipping; Kowalski lens cuts motion slop | docs/guides/SKILLS.md | `## Downloaded skills` |
| S124 | docs/guides/SKILLS.md:195 | Superseded in practice by the emilkowalski set | docs/guides/SKILLS.md | `## Downloaded skills` |
| S125 | docs/guides/SKILLS.md:196 | Kept because audit mode emits an HTML report with looping demos | docs/guides/SKILLS.md | `## Downloaded skills` |
| S126 | docs/guides/SKILLS.md:201 | emilkowalski/skills heading: 12 upstream, 9 installed, added 2026-08-06 | docs/guides/SKILLS.md | `## Downloaded skills` |
| S127 | docs/guides/SKILLS.md:202 | emilkowalski source github.com/emilkowalski/skills | config/manifest.json | `entries.animate.source` |
| S128 | docs/guides/SKILLS.md:205 | clone emilkowalski/skills to /tmp/emil | config/manifest.json | `entries.animate.install` |
| S129 | docs/guides/SKILLS.md:206 | loop cp each skill folder into ~/.claude/skills | config/manifest.json | `entries.animate.install` |
| S130 | docs/guides/SKILLS.md:207 | remove the temp clone | config/manifest.json | `entries.animate.install` |
| S131 | docs/guides/SKILLS.md:209 | animate: build motion from scratch | docs/guides/SKILLS.md | `## Downloaded skills` |
| S132 | docs/guides/SKILLS.md:209 | review-animations: critique a diff | docs/guides/SKILLS.md | `## Downloaded skills` |
| S133 | docs/guides/SKILLS.md:210 | improve-animations: audit a whole codebase, plans for cheaper models | docs/guides/SKILLS.md | `## Downloaded skills` |
| S134 | docs/guides/SKILLS.md:211 | find-animation-opportunities: read-only hunt | docs/guides/SKILLS.md | `## Downloaded skills` |
| S135 | docs/guides/SKILLS.md:212 | animation-vocabulary: reverse-lookup glossary | docs/guides/SKILLS.md | `## Downloaded skills` |
| S136 | docs/guides/SKILLS.md:213 | apple-design: WWDC fluid interfaces for web | docs/guides/SKILLS.md | `## Downloaded skills` |
| S137 | docs/guides/SKILLS.md:214 | emil-design-eng: underlying philosophy | docs/guides/SKILLS.md | `## Downloaded skills` |
| S138 | docs/guides/SKILLS.md:215 | prototype and pick-ui-library also installed | docs/guides/SKILLS.md | `## Downloaded skills` |
| S139 | docs/guides/SKILLS.md:216 | Earns slot: primary source behind design-motion-principles' strongest lens; nine granular skills | docs/guides/SKILLS.md | `## Downloaded skills` |
| S140 | docs/guides/SKILLS.md:219 | Pipeline fit: /design step 6 motion and step 7 audit | docs/guides/SKILLS.md | `## Routing` |
| S141 | docs/guides/SKILLS.md:220 | Prefer animate over design-motion-principles build mode; review-animations for a diff, improve-animations for an app | docs/guides/SKILLS.md | `## Routing` |
| S142 | docs/guides/SKILLS.md:225 | gsap-skills heading: 8 skills, added 2026-08-06 | docs/guides/SKILLS.md | `## Downloaded skills` |
| S143 | docs/guides/SKILLS.md:226 | gsap-skills source github.com/greensock/gsap-skills | config/manifest.json | `entries.gsap-core.source` |
| S144 | docs/guides/SKILLS.md:226 | 13.1k stars, official GreenSock | docs/guides/SKILLS.md | `## Downloaded skills` |
| S145 | docs/guides/SKILLS.md:229 | clone greensock/gsap-skills | config/manifest.json | `entries.gsap-core.install` |
| S146 | docs/guides/SKILLS.md:230 | loop cp skills | config/manifest.json | `entries.gsap-core.install` |
| S147 | docs/guides/SKILLS.md:231 | remove the temp clone | config/manifest.json | `entries.gsap-core.install` |
| S148 | docs/guides/SKILLS.md:233 | gsap skills list: core, timeline, scrolltrigger, react, frameworks, plugins, performance, utils | docs/guides/SKILLS.md | `## Downloaded skills` |
| S149 | docs/guides/SKILLS.md:236 | Earns slot: official, maintained, nothing local covered GSAP | docs/guides/SKILLS.md | `## Downloaded skills` |
| S150 | docs/guides/SKILLS.md:237 | Includes gsap.matchMedia reduced-motion patterns | docs/guides/SKILLS.md | `## Downloaded skills` |
| S151 | docs/guides/SKILLS.md:238 | Use gsap for scroll, pinned sections, timelines; simple CSS transitions use transitions-dev | docs/guides/SKILLS.md | `## Downloaded skills` |
| S152 | docs/guides/SKILLS.md:243 | transitions.dev heading: 2 skills, added 2026-08-06 | docs/guides/SKILLS.md | `## Downloaded skills` |
| S153 | docs/guides/SKILLS.md:244 | transitions.dev source github.com/Jakubantalik/transitions.dev | config/manifest.json | `entries.transitions-dev.source` |
| S154 | docs/guides/SKILLS.md:247 | clone transitions.dev | config/manifest.json | `entries.transitions-dev.install` |
| S155 | docs/guides/SKILLS.md:248 | loop cp skills | config/manifest.json | `entries.transitions-dev.install` |
| S156 | docs/guides/SKILLS.md:249 | remove the temp clone | config/manifest.json | `entries.transitions-dev.install` |
| S157 | docs/guides/SKILLS.md:251 | transitions-dev: production CSS transitions for dropdowns, modals, tabs, accordions | docs/guides/SKILLS.md | `## Downloaded skills` |
| S158 | docs/guides/SKILLS.md:252 | transitions-polish: tune existing motion against a motion-token scale | docs/guides/SKILLS.md | `## Downloaded skills` |
| S159 | docs/guides/SKILLS.md:254 | Earns slot: copy-paste layer under principles skills; only motion-token vocabulary | docs/guides/SKILLS.md | `## Downloaded skills` |
| S160 | docs/guides/SKILLS.md:259 | Section: reverse-engineering a reference | docs/guides/SKILLS.md | `## Downloaded skills` |
| S161 | docs/guides/SKILLS.md:261 | design-dna heading, added 2026-08-06 | docs/guides/SKILLS.md | `## Downloaded skills` |
| S162 | docs/guides/SKILLS.md:262 | design-dna source github.com/zanwei/design-dna | config/manifest.json | `entries.design-dna.source` |
| S163 | docs/guides/SKILLS.md:265 | clone zanwei/design-dna | config/manifest.json | `entries.design-dna.install` |
| S164 | docs/guides/SKILLS.md:266 | mkdir design-dna folder | config/manifest.json | `entries.design-dna.install` |
| S165 | docs/guides/SKILLS.md:267 | cp SKILL.md, references, docs | config/manifest.json | `entries.design-dna.install` |
| S166 | docs/guides/SKILLS.md:268 | remove the temp clone | config/manifest.json | `entries.design-dna.install` |
| S167 | docs/guides/SKILLS.md:270 | design-dna turns screenshot/URL into Design DNA JSON: tokens, style, effects | docs/guides/SKILLS.md | `## Downloaded skills` |
| S168 | docs/guides/SKILLS.md:272 | Then generates matching UI from that JSON plus your content | docs/guides/SKILLS.md | `## Downloaded skills` |
| S169 | docs/guides/SKILLS.md:273 | Earns slot: nothing else extracts a design from a reference | docs/guides/SKILLS.md | `## Downloaded skills` |
| S170 | docs/guides/SKILLS.md:275 | Pipeline fit: /design step 1, before ui-ux-pro-max when a client shows a site | docs/guides/SKILLS.md | `## Routing` |
| S171 | docs/guides/SKILLS.md:280 | Section: Design 3D | docs/guides/SKILLS.md | `## Downloaded skills` |
| S172 | docs/guides/SKILLS.md:282 | threejs-skills heading: 10 skills, added 2026-08-06 | docs/guides/SKILLS.md | `## Downloaded skills` |
| S173 | docs/guides/SKILLS.md:283 | threejs source github.com/CloudAI-X/threejs-skills | config/manifest.json | `entries.threejs-geometry.source` |
| S174 | docs/guides/SKILLS.md:286 | clone CloudAI-X/threejs-skills | config/manifest.json | `entries.threejs-geometry.install` |
| S175 | docs/guides/SKILLS.md:287 | loop cp skills | config/manifest.json | `entries.threejs-geometry.install` |
| S176 | docs/guides/SKILLS.md:288 | remove the temp clone | config/manifest.json | `entries.threejs-geometry.install` |
| S177 | docs/guides/SKILLS.md:290 | threejs skills: fundamentals, geometry, materials, lighting, textures, shaders, loaders, animation, interaction, postprocessing | docs/guides/SKILLS.md | `## Downloaded skills` |
| S178 | docs/guides/SKILLS.md:294 | Use only on real WebGL work | docs/guides/SKILLS.md | `## Downloaded skills` |
| S179 | docs/guides/SKILLS.md:295 | Pairs with gsap-scrolltrigger and design-dna visual effects | docs/guides/SKILLS.md | `## Downloaded skills` |
| S180 | docs/guides/SKILLS.md:299 | Section: visual taste | docs/guides/SKILLS.md | `## Downloaded skills` |
| S181 | docs/guides/SKILLS.md:301 | Three variants of one repo; install one, two or all three | docs/guides/SKILLS.md | `## Downloaded skills` |
| S182 | docs/guides/SKILLS.md:303 | high-end-visual-design (soft) heading | docs/guides/SKILLS.md | `## Downloaded skills` |
| S183 | docs/guides/SKILLS.md:304 | taste-skill source github.com/Leonxlnx/taste-skill | config/manifest.json | `entries.high-end-visual-design.source` |
| S184 | docs/guides/SKILLS.md:307 | high-end-visual-design install command | config/manifest.json | `entries.high-end-visual-design.install` |
| S185 | docs/guides/SKILLS.md:309 | Style: polished, calm, expensive; Linear, Vercel, Stripe | docs/guides/SKILLS.md | `## Downloaded skills` |
| S186 | docs/guides/SKILLS.md:313 | minimalist-ui heading | docs/guides/SKILLS.md | `## Downloaded skills` |
| S187 | docs/guides/SKILLS.md:317 | minimalist-ui install command | config/manifest.json | `entries.minimalist-ui.install` |
| S188 | docs/guides/SKILLS.md:319 | Style: editorial product UI; Notion, Linear | docs/guides/SKILLS.md | `## Downloaded skills` |
| S189 | docs/guides/SKILLS.md:323 | industrial-brutalist-ui (BETA) heading | docs/guides/SKILLS.md | `## Downloaded skills` |
| S190 | docs/guides/SKILLS.md:327 | industrial-brutalist-ui install command | config/manifest.json | `entries.industrial-brutalist-ui.install` |
| S191 | docs/guides/SKILLS.md:329 | Style: hard mechanical, Swiss type, experimental; BETA | docs/guides/SKILLS.md | `## Downloaded skills` |
| S192 | docs/guides/SKILLS.md:333 | Section: Design comprehensive | docs/guides/SKILLS.md | `## Downloaded skills` |
| S193 | docs/guides/SKILLS.md:335 | ui-ux-pro-max heading | docs/guides/SKILLS.md | `## Downloaded skills` |
| S194 | docs/guides/SKILLS.md:336 | ui-ux-pro-max: 67 styles, 96 palettes, 57 font pairings, 25 charts, 13 stacks | docs/guides/SKILLS.md | `## Downloaded skills` |
| S195 | docs/guides/SKILLS.md:337 | Use for style exploration or a full stack decision; pairs with impeccable | docs/guides/SKILLS.md | `## Downloaded skills` |
| S196 | docs/guides/SKILLS.md:339 | Full design pipeline order; setup and kickoff prompt in DESIGN-PIPELINE.md | docs/guides/SKILLS.md | `## Routing` |
| S197 | docs/guides/SKILLS.md:343 | Section: Client site build system (custom) | docs/guides/SKILLS.md | `## Your own skills` |
| S198 | docs/guides/SKILLS.md:345 | Custom skills and commands for the freelance website business | docs/guides/SKILLS.md | `## Your own skills` |
| S199 | docs/guides/SKILLS.md:346 | Full how-to lives in the build system repo WORKFLOW.md | docs/guides/SKILLS.md | `## Your own skills` |
| S200 | docs/guides/SKILLS.md:348 | astro-patterns skill heading | docs/guides/SKILLS.md | `## Your own skills` |
| S201 | docs/guides/SKILLS.md:349 | astro-patterns: Astro conventions for the freelance stack | docs/guides/SKILLS.md | `## Your own skills` |
| S202 | docs/guides/SKILLS.md:352 | astro-patterns use: building or reviewing Astro sites; auto-fires | docs/guides/SKILLS.md | `## Your own skills` |
| S203 | docs/guides/SKILLS.md:354 | /design command heading | docs/guides/SKILLS.md | `## Your own commands` |
| S204 | docs/guides/SKILLS.md:355 | /design runs the pipeline: direction, components, assemble, motion, audit | docs/guides/SKILLS.md | `## Your own commands` |
| S205 | docs/guides/SKILLS.md:357 | You can supply style, brand, assets or Figma URL; rest is proposed | docs/guides/SKILLS.md | `## Your own commands` |
| S206 | docs/guides/SKILLS.md:359 | /new-site command heading | docs/guides/SKILLS.md | `## Your own commands` |
| S207 | docs/guides/SKILLS.md:360 | /new-site orchestrates a full client website build | docs/guides/SKILLS.md | `## Your own commands` |
| S208 | docs/guides/SKILLS.md:363 | One command instead of a checklist; see WORKFLOW.md | docs/guides/SKILLS.md | `## Your own commands` |
| S209 | docs/guides/SKILLS.md:365 | /monthly-ops command heading | docs/guides/SKILLS.md | `## Your own commands` |
| S210 | docs/guides/SKILLS.md:366 | /monthly-ops runs a client's monthly retainer cycle and drafts the report | docs/guides/SKILLS.md | `## Your own commands` |
| S211 | docs/guides/SKILLS.md:368 | Hard-stops for your review; runs MONTHLY-OPS-GUIDE runbooks | docs/guides/SKILLS.md | `## Your own commands` |
| S212 | docs/guides/SKILLS.md:370 | seo-ops skill heading | docs/guides/SKILLS.md | `## Your own skills` |
| S213 | docs/guides/SKILLS.md:371 | seo-ops: recurring SEO/AEO for a live client site | docs/guides/SKILLS.md | `## Your own skills` |
| S214 | docs/guides/SKILLS.md:373 | Run-time counterpart to SEO-GUIDE; used by /monthly-ops SEO add-on | docs/guides/SKILLS.md | `## Your own skills` |
| S215 | docs/guides/SKILLS.md:375 | content-ops skill heading | docs/guides/SKILLS.md | `## Your own skills` |
| S216 | docs/guides/SKILLS.md:376 | content-ops: site copy and blog content in client voice, no AI slop | docs/guides/SKILLS.md | `## Your own skills` |
| S217 | docs/guides/SKILLS.md:378 | Uses voice-dna and anti-ai-writing; obeys SEO-GUIDE topical rules | docs/guides/SKILLS.md | `## Your own skills` |
| S218 | docs/guides/SKILLS.md:380 | voice-dna and anti-ai-writing heading | docs/guides/SKILLS.md | `## Your own skills` |
| S219 | docs/guides/SKILLS.md:381 | voice-dna: per-client voice profile from ~20 samples | docs/guides/SKILLS.md | `## Your own skills` |
| S220 | docs/guides/SKILLS.md:382 | anti-ai-writing: final de-slop pass; both feed content-ops | docs/guides/SKILLS.md | `## Your own skills` |
| S221 | docs/guides/SKILLS.md:382 | Third party artemnovitckii/content-skills, MIT, tracked in this repo | docs/guides/SKILLS.md | `## Your own skills` |
| S222 | docs/guides/SKILLS.md:385 | humanizer heading, added 2026-08-06 | docs/guides/SKILLS.md | `## Downloaded skills` |
| S223 | docs/guides/SKILLS.md:386 | humanizer source github.com/blader/humanizer | config/manifest.json | `entries.humanizer.source` |
| S224 | docs/guides/SKILLS.md:386 | 34k stars, MIT | docs/guides/SKILLS.md | `## Downloaded skills` |
| S225 | docs/guides/SKILLS.md:389 | clone blader/humanizer | config/manifest.json | `entries.humanizer.install` |
| S226 | docs/guides/SKILLS.md:390 | mkdir humanizer folder | config/manifest.json | `entries.humanizer.install` |
| S227 | docs/guides/SKILLS.md:391 | cp SKILL.md and scripts | config/manifest.json | `entries.humanizer.install` |
| S228 | docs/guides/SKILLS.md:392 | remove the temp clone | config/manifest.json | `entries.humanizer.install` |
| S229 | docs/guides/SKILLS.md:394 | humanizer rewrites 33 named AI-writing tells from Wikipedia guide | docs/guides/SKILLS.md | `## Downloaded skills` |
| S230 | docs/guides/SKILLS.md:397 | Overlaps anti-ai-writing on purpose; different jobs | docs/guides/SKILLS.md | `## Downloaded skills` |
| S231 | docs/guides/SKILLS.md:398 | anti-ai-writing is voice-aware; humanizer is a mechanical sweep with a script | docs/guides/SKILLS.md | `## Downloaded skills` |
| S232 | docs/guides/SKILLS.md:399 | Run humanizer first, anti-ai-writing last; not both blind | docs/guides/SKILLS.md | `## Downloaded skills` |
| S233 | docs/guides/SKILLS.md:402 | nano-banana, video-to-website, business-analyzer heading | docs/guides/SKILLS.md | `## Your own skills` |
| S234 | docs/guides/SKILLS.md:403 | nano-banana: controlled imagery via Gemini, used in /brand-system and assets | docs/guides/SKILLS.md | `## Your own skills` |
| S235 | docs/guides/SKILLS.md:404 | video-to-website: scroll hero from a video as an Astro island, in /new-site | docs/guides/SKILLS.md | `## Your own skills` |
| S236 | docs/guides/SKILLS.md:405 | business-analyzer: market/pricing/competitive discovery, in /new-site intake | docs/guides/SKILLS.md | `## Your own skills` |
| S237 | docs/guides/SKILLS.md:406 | All three live in claude-config skills and are symlinked | docs/guides/SKILLS.md | `## Your own skills` |
| S238 | docs/guides/SKILLS.md:408 | packshot heading, added 2026-08-06 | docs/guides/SKILLS.md | `## Downloaded skills` |
| S239 | docs/guides/SKILLS.md:409 | packshot source: hand-delivered zip, no public repo | docs/guides/SKILLS.md | `## Downloaded skills` |
| S240 | docs/guides/SKILLS.md:410 | Original zip kept at ~/Downloads/PACKSHOT CLAUDE SKILL-*.zip | docs/guides/SETUP.md | `## Downloaded skills` |
| S241 | docs/guides/SKILLS.md:411 | Not vendored, lives only in ~/.claude/skills/packshot; back up before wiping a machine | docs/guides/SETUP.md | `## Downloaded skills` |
| S242 | docs/guides/SKILLS.md:413 | packshot: audits photos, picks staging, writes material narrative, renders packshot | docs/guides/SKILLS.md | `## Downloaded skills` |
| S243 | docs/guides/SKILLS.md:415 | Renders on FAL via fal-ai/nano-banana-2/edit, about $0.12 per image | docs/guides/SKILLS.md | `## Downloaded skills` |
| S244 | docs/guides/SKILLS.md:416 | Requires FAL_KEY in env or project .env; skill stops without it | docs/guides/SKILLS.md | `## Downloaded skills` |
| S245 | docs/guides/SKILLS.md:418 | Python deps in venv ~/.claude/skills/packshot/.venv (25 MB) | docs/guides/SETUP.md | `## Downloaded skills` |
| S246 | docs/guides/SKILLS.md:419 | Arch PEP 668 refuses system pip; pipx cannot expose a library with no CLI | docs/guides/SETUP.md | `## Downloaded skills` |
| S247 | docs/guides/SKILLS.md:423 | Rebuild venv: python3 -m venv .venv and pip install fal-client requests | docs/guides/SETUP.md | `## Restore on a new machine` |
| S248 | docs/guides/SKILLS.md:426 | Skill uses .venv/bin/python, never system python3 | docs/guides/SETUP.md | `## Downloaded skills` |
| S249 | docs/guides/SKILLS.md:427 | Local adaptations heading | docs/guides/SETUP.md | `## Downloaded skills` |
| S250 | docs/guides/SKILLS.md:428 | Step 1 rewired from a /brand skill to read brand-system.html from /brand-system | docs/guides/SETUP.md | `## Downloaded skills` |
| S251 | docs/guides/SKILLS.md:430 | No brand system found is a valid outcome, not a hard stop | docs/guides/SETUP.md | `## Downloaded skills` |
| S252 | docs/guides/SKILLS.md:431 | Output moved to ./packshots/[output-name]/ | docs/guides/SETUP.md | `## Downloaded skills` |
| S253 | docs/guides/SKILLS.md:432 | Script path fixed to ~/.claude/skills/packshot/generate-packshot.py | docs/guides/SETUP.md | `## Downloaded skills` |
| S254 | docs/guides/SKILLS.md:434 | Added Requirements section and per-generation cost callouts | docs/guides/SETUP.md | `## Downloaded skills` |
| S255 | docs/guides/SKILLS.md:435 | nano-banana is the free Gemini path; packshot is paid FAL with ghost-mannequin prompts | docs/guides/SKILLS.md | `## Downloaded skills` |
| S256 | docs/guides/SKILLS.md:436 | Reach for nano-banana first unless the job is a commercial product shot | docs/guides/SKILLS.md | `## Downloaded skills` |
| S257 | docs/guides/SKILLS.md:441 | Section: Marketing and conversion (added 2026-08-06) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S258 | docs/guides/SKILLS.md:443 | marketingskills heading: 12 of 50 | docs/guides/SKILLS.md | `## Downloaded skills` |
| S259 | docs/guides/SKILLS.md:444 | marketingskills source github.com/coreyhaines31/marketingskills; 43k stars, MIT | config/manifest.json | `entries.cro.source` |
| S260 | docs/guides/SKILLS.md:447 | clone marketingskills | config/manifest.json | `entries.cro.install` |
| S261 | docs/guides/SKILLS.md:448 | loop over the 12 chosen names | config/manifest.json | `entries.cro.install` |
| S262 | docs/guides/SKILLS.md:450 | cp each named skill into ~/.claude/skills | config/manifest.json | `entries.cro.install` |
| S263 | docs/guides/SKILLS.md:452 | remove the temp clone | config/manifest.json | `entries.cro.install` |
| S264 | docs/guides/SKILLS.md:454 | Not installed: copywriting, copy-editing, content-strategy, social, emails, seo-audit, ai-seo, programmatic-seo, schema, site-architecture, image, video | docs/guides/SKILLS.md | `## Downloaded skills` |
| S265 | docs/guides/SKILLS.md:456 | Reason: content-ops, article-writing, seo-ops, voice-dna, business-analyzer already cover it | docs/guides/SKILLS.md | `## Downloaded skills` |
| S266 | docs/guides/SKILLS.md:457 | image and video would collide by name | docs/guides/SKILLS.md | `## Downloaded skills` |
| S267 | docs/guides/SKILLS.md:458 | Revisit if a client job needs one; install line takes a name | docs/guides/SKILLS.md | `## Downloaded skills` |
| S268 | docs/guides/SKILLS.md:460 | marketing-psychology: 72 named mental models | docs/guides/SKILLS.md | `## Downloaded skills` |
| S269 | docs/guides/SKILLS.md:462 | CRO family: cro, signup, onboarding, popups, paywalls, pricing, offers, ab-testing | docs/guides/SKILLS.md | `## Downloaded skills` |
| S270 | docs/guides/SKILLS.md:463 | /new-site had no conversion layer before | docs/guides/SKILLS.md | `## Downloaded skills` |
| S271 | docs/guides/SKILLS.md:464 | launch, lead-magnets, customer-research: GTM and discovery, feed business-analyzer | docs/guides/SKILLS.md | `## Downloaded skills` |
| S272 | docs/guides/SKILLS.md:466 | Pointer: SKILLS-EVALUATION.md logs every skill considered | docs/guides/SKILLS.md | `dropped: pointer to a file that moves; links get updated` |
| S273 | docs/guides/SKILLS.md:467 | Pointer: PLUGINS.md lists claude-seo, security-guidance | docs/guides/SKILLS.md | `dropped: pointer to a file that moves; links get updated` |
| S274 | docs/guides/SKILLS.md:471 | Section: Undocumented at install time (inventoried 2026-07-29) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S275 | docs/guides/SKILLS.md:473 | Source listed UNKNOWN where unverifiable; do not guess a URL | docs/guides/SKILLS.md | `## Downloaded skills` |
| S276 | docs/guides/SKILLS.md:477 | 21st.dev skill set (7 skills) heading | docs/guides/SKILLS.md | `## Downloaded skills` |
| S277 | docs/guides/SKILLS.md:478 | The 7 21st skills: ai, cli-use, design-sync, registry, ui-build, ui-explore, ui-review | docs/guides/SKILLS.md | `## Downloaded skills` |
| S278 | docs/guides/SKILLS.md:479 | They drive the 21st CLI @21st-dev/cli, global npm | docs/guides/SETUP.md | `## Keep it current` |
| S279 | docs/guides/SKILLS.md:480 | Keep CLI current with npm install -g @21st-dev/cli@latest | docs/guides/SETUP.md | `## Keep it current` |
| S280 | docs/guides/SKILLS.md:481 | Distinct from magic MCP: MCP generates, CLI searches/installs/publishes | docs/guides/SETUP.md | `## MCP servers` |
| S281 | docs/guides/SKILLS.md:483 | Cloudflare skill set (12 skills) heading | docs/guides/SKILLS.md | `## Downloaded skills` |
| S282 | docs/guides/SKILLS.md:484 | Cloudflare source github.com/cloudflare/skills | config/manifest.json | `entries.agents-sdk.source` |
| S283 | docs/guides/SKILLS.md:485 | Installed as a batch 2026-07-02; source traced 2026-07-29 | docs/guides/SKILLS.md | `dropped: dated history note; source is in the manifest` |
| S284 | docs/guides/SKILLS.md:488 | The 12 Cloudflare skill names | docs/guides/SKILLS.md | `## Downloaded skills` |
| S285 | docs/guides/SKILLS.md:492 | 2026-09-02: sandbox-sdk split into sandbox-stable, sandbox-next, sandbox-migrate-to-next | docs/guides/SKILLS.md | `## Downloaded skills` |
| S286 | docs/guides/SKILLS.md:494 | sandbox-sdk deleted locally; sandbox-migrate-to-next was not installed (manifest now lists it) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S287 | docs/guides/SKILLS.md:494 | cloudflare, email-service, turnstile-spin re-copied; seven were identical | docs/guides/SKILLS.md | `dropped: dated history note` |
| S288 | docs/guides/SKILLS.md:496 | turnstile-spin orphans survived the re-copy, unresolved | docs/guides/SKILLS.md | `## Downloaded skills` |
| S289 | docs/guides/SKILLS.md:498 | Upstream's recommended install: clone once, symlink, git pull updates all 12 | docs/guides/SETUP.md | `## Downloaded skills` |
| S290 | docs/guides/SKILLS.md:501 | git clone cloudflare/skills to ~/.config/cloudflare-skills | docs/guides/SETUP.md | `## Downloaded skills` |
| S291 | docs/guides/SKILLS.md:502 | loop of ln -sfn per skill into ~/.claude/skills | docs/guides/SETUP.md | `## Downloaded skills` |
| S292 | docs/guides/SKILLS.md:508 | Current install is a copy, not a symlink, so it does not self-update | docs/guides/SETUP.md | `## Downloaded skills` |
| S293 | docs/guides/SKILLS.md:510 | turnstile-spin drifted: upstream rewrote it, SKILL.md now canonical | docs/guides/SKILLS.md | `## Downloaded skills` |
| S294 | docs/guides/SKILLS.md:512 | Local copy carries scripts/fetch-secret.sh, worker-deploy.sh, templates/worker/ upstream dropped | docs/guides/SKILLS.md | `## Downloaded skills` |
| S295 | docs/guides/SKILLS.md:514 | Refresh turnstile-spin by cloning and cp -a its folder | config/manifest.json | `entries.turnstile-spin.install` |
| S296 | docs/guides/SKILLS.md:520 | Refresh leaves three orphans; delete by hand once sure you did not write them | docs/guides/SKILLS.md | `## Downloaded skills` |
| S297 | docs/guides/SKILLS.md:523 | Not installed from that repo: commands build-agent.md, build-mcp.md, rules/workers.mdc | docs/guides/SKILLS.md | `## Downloaded skills` |
| S298 | docs/guides/SKILLS.md:526 | Loose extras heading | docs/guides/SKILLS.md | `## Your own skills` |
| S299 | docs/guides/SKILLS.md:527 | A private doc-ecosystem re-sync skill, kept local, not published | docs/guides/SKILLS.md | `## Your own skills` |
| S300 | docs/guides/SKILLS.md:528 | web-perf was once listed here; it is Cloudflare's | docs/guides/SKILLS.md | `dropped: dated history note; web-perf is in the manifest` |
| S301 | docs/guides/SKILLS.md:530 | review-stack heading: owned, in this repo | docs/guides/SKILLS.md | `## Your own skills` |
| S302 | docs/guides/SKILLS.md:531 | Symlinked to ~/.claude/skills/review-stack; used to live only in ~/.claude | docs/guides/SKILLS.md | `## Your own skills` |
| S303 | docs/guides/SKILLS.md:534 | Dispatches regression-hunter, pr-intent-verifier, security-reviewer, database-reviewer, language reviewer, code-reviewer in parallel | docs/guides/SKILLS.md | `## Your own skills` |
| S304 | docs/guides/SKILLS.md:536 | Takes local changes or a PR number | docs/guides/SKILLS.md | `## Your own skills` |
| S305 | docs/guides/SKILLS.md:538 | Not a replacement for /code-review (built into the CLI binary, no file on disk) | docs/guides/SKILLS.md | `## Your own skills` |
| S306 | docs/guides/SKILLS.md:540 | review-stack invokes /code-review itself as a seventh reviewer | docs/guides/SKILLS.md | `## Your own skills` |
| S307 | docs/guides/SKILLS.md:541 | Never launches ultra; billed, only the user starts it | docs/guides/SKILLS.md | `## Your own skills` |
| S308 | docs/guides/SKILLS.md:544 | Blind lane: same diff reviewed again with no intent, context, memory or git history | docs/guides/SKILLS.md | `## Your own skills` |
| S309 | docs/guides/SKILLS.md:547 | Blind tree built from git ls-files / tar plus a generated packet | docs/guides/SKILLS.md | `## Your own skills` |
| S310 | docs/guides/SKILLS.md:549 | Report gains a Disagreements section; blind findings dismissed only by file:line | docs/guides/SKILLS.md | `## Your own skills` |
| S311 | docs/guides/SKILLS.md:551 | sealed uses isolated claude -p subprocesses; USD 5-19 a run, opt-in | docs/guides/SKILLS.md | `## Your own skills` |
| S312 | docs/guides/SKILLS.md:552 | Prose-only diffs skip the blind lane | docs/guides/SKILLS.md | `## Your own skills` |
| S313 | docs/guides/SKILLS.md:555 | Spec conformance: top three spec files by changed paths go to pr-intent-verifier | docs/guides/SKILLS.md | `## Your own skills` |
| S314 | docs/guides/SKILLS.md:560 | Stacked branches: BASE auto-detected as nearest parent branch; report states what the base hides | docs/guides/SKILLS.md | `## Your own skills` |
| S315 | docs/guides/SKILLS.md:564 | Receipts: run writes .git/review-stack/<sha>; pre-push hook refuses a commit with none | docs/guides/SKILLS.md | `## Your own skills` |
| S316 | docs/guides/SKILLS.md:567 | Fixed output structure and one ASCII severity scheme | docs/guides/SKILLS.md | `## Your own skills` |
| S317 | docs/guides/SKILLS.md:570 | Actionable comments anchored at path:line with suggestion blocks | docs/guides/SKILLS.md | `## Your own skills` |
| S318 | docs/guides/SKILLS.md:574 | Multi-repo sessions: pins REPO_DIR, SLUG, BASE and passes absolute paths | docs/guides/SKILLS.md | `## Your own skills` |
| S319 | docs/guides/SKILLS.md:576 | PR mode uses a throwaway git worktree, never gh pr checkout | docs/guides/SKILLS.md | `## Your own skills` |
| S320 | docs/guides/SKILLS.md:580 | graphify heading | docs/guides/SKILLS.md | `## Downloaded skills` |
| S321 | docs/guides/SKILLS.md:581 | graphify source Graphify-Labs/graphify (formerly safishamsi); a Python package | config/manifest.json | `entries.graphify.source` |
| S322 | docs/guides/SKILLS.md:584 | pipx install graphifyy (package graphifyy, CLI graphify) | config/manifest.json | `entries.graphify.install` |
| S323 | docs/guides/SKILLS.md:585 | pipx upgrade graphifyy | docs/guides/SETUP.md | `## Keep it current` |
| S324 | docs/guides/SKILLS.md:586 | graphify install claude rewrites the skill and registers it in CLAUDE.md | config/manifest.json | `entries.graphify.install` |
| S325 | docs/guides/SKILLS.md:588 | Skill carries .graphify_version; CLI warns if it drifts from the package | docs/guides/SKILLS.md | `## Downloaded skills` |
| S326 | docs/guides/SKILLS.md:589 | graphify turns a folder into a knowledge graph; trigger /graphify | docs/guides/SKILLS.md | `## Downloaded skills` |
| S327 | docs/guides/SKILLS.md:593 | Section: Specialized | docs/guides/SKILLS.md | `## Your own skills` |
| S328 | docs/guides/SKILLS.md:595 | Client CMS skill heading | docs/guides/SKILLS.md | `## Your own skills` |
| S329 | docs/guides/SKILLS.md:596 | A client CMS skill, private, not vendored, excluded in .gitignore | docs/guides/SKILLS.md | `## Your own skills` |
| S330 | docs/guides/SKILLS.md:597 | Use for client website work only | docs/guides/SKILLS.md | `## Your own skills` |
| S331 | docs/guides/SKILLS.md:599 | anthropic-security-review heading | docs/guides/SKILLS.md | `## Frameworks` |
| S332 | docs/guides/SKILLS.md:600 | Python security review toolkit from Anthropic, not a SKILL.md skill | docs/guides/SKILLS.md | `## Frameworks` |
| S333 | docs/guides/SKILLS.md:601 | Location ~/.claude/skills/anthropic-security-review/ | config/manifest.json | `frameworks.anthropic-security-review.install` |
| S334 | docs/guides/SKILLS.md:603 | getsentry-skills heading | docs/guides/SKILLS.md | `## Frameworks` |
| S335 | docs/guides/SKILLS.md:604 | Sentry skills aware of Sentry error tracking | docs/guides/SKILLS.md | `## Frameworks` |
| S336 | docs/guides/SKILLS.md:605 | Location ~/.claude/skills/getsentry-skills/ | config/manifest.json | `frameworks.getsentry-skills.install` |
| S337 | docs/guides/SKILLS.md:609 | ECC cherry-pick heading | docs/guides/SKILLS.md | `## Frameworks` |
| S338 | docs/guides/SKILLS.md:611 | ECC source github.com/affaan-m/ecc | config/manifest.json | `frameworks.ecc.source` |
| S339 | docs/guides/SKILLS.md:612 | Install method manual cherry-pick, not bin/install.sh | docs/guides/SETUP.md | `## Frameworks` |
| S340 | docs/guides/SKILLS.md:613 | Not installed: hooks/, scripts/, settings.json, MCP configs, configure-ecc, security-scan agent, instinct system, continuous-learning | docs/guides/SETUP.md | `## Frameworks` |
| S341 | docs/guides/SKILLS.md:613 | Reason: they conflict with jjstack/gsd/claude-mem | docs/guides/SETUP.md | `## Frameworks` |
| S342 | docs/guides/SKILLS.md:615 | Agents installed heading | docs/guides/SKILLS.md | `## Frameworks` |
| S343 | docs/guides/SKILLS.md:617 | Language reviewers and resolvers heading | docs/guides/SKILLS.md | `## Frameworks` |
| S344 | docs/guides/SKILLS.md:618 | go-reviewer, go-build-resolver | docs/guides/SKILLS.md | `## Frameworks` |
| S345 | docs/guides/SKILLS.md:619 | python-reviewer | docs/guides/SKILLS.md | `## Frameworks` |
| S346 | docs/guides/SKILLS.md:620 | typescript-reviewer | docs/guides/SKILLS.md | `## Frameworks` |
| S347 | docs/guides/SKILLS.md:621 | rust-reviewer, rust-build-resolver | docs/guides/SKILLS.md | `## Frameworks` |
| S348 | docs/guides/SKILLS.md:622 | java-reviewer, java-build-resolver | docs/guides/SKILLS.md | `## Frameworks` |
| S349 | docs/guides/SKILLS.md:623 | build-error-resolver (generic) | docs/guides/SKILLS.md | `## Frameworks` |
| S350 | docs/guides/SKILLS.md:625 | General purpose agents heading | docs/guides/SKILLS.md | `## Frameworks` |
| S351 | docs/guides/SKILLS.md:626 | architect, code-architect, code-reviewer, code-explorer | docs/guides/SKILLS.md | `## Frameworks` |
| S352 | docs/guides/SKILLS.md:627 | planner, tdd-guide, security-reviewer | docs/guides/SKILLS.md | `## Frameworks` |
| S353 | docs/guides/SKILLS.md:628 | refactor-cleaner, doc-updater, docs-lookup | docs/guides/SKILLS.md | `## Frameworks` |
| S354 | docs/guides/SKILLS.md:629 | e2e-runner, loop-operator | docs/guides/SKILLS.md | `## Frameworks` |
| S355 | docs/guides/SKILLS.md:630 | database-reviewer, performance-optimizer | docs/guides/SKILLS.md | `## Frameworks` |
| S356 | docs/guides/SKILLS.md:631 | silent-failure-hunter, chief-of-staff | docs/guides/SKILLS.md | `## Frameworks` |
| S357 | docs/guides/SKILLS.md:632 | pr-test-analyzer, a11y-architect | docs/guides/SKILLS.md | `## Frameworks` |
| S358 | docs/guides/SKILLS.md:634 | review-stack's two hand-written owned agents | docs/guides/SKILLS.md | `## Your own skills` |
| S359 | docs/guides/SKILLS.md:635 | regression-hunter: what worked before and stops working after | docs/guides/SKILLS.md | `## Your own skills` |
| S360 | docs/guides/SKILLS.md:636 | Seven hunts; best is bugfix reversal via git log -L | docs/guides/SKILLS.md | `## Your own skills` |
| S361 | docs/guides/SKILLS.md:638 | pr-intent-verifier: does the change do what the PR says and nothing else | docs/guides/SKILLS.md | `## Your own skills` |
| S362 | docs/guides/SKILLS.md:639 | Requirement checklist from the linked issue; each COVERED needs file:line | docs/guides/SKILLS.md | `## Your own skills` |
| S363 | docs/guides/SKILLS.md:641 | Rules installed heading ~/.claude/rules/ecc/ | docs/guides/SKILLS.md | `## Frameworks` |
| S364 | docs/guides/SKILLS.md:643 | ECC rules are not auto-loaded; add @imports to project CLAUDE.md | docs/guides/SKILLS.md | `## Frameworks` |
| S365 | docs/guides/SKILLS.md:644 | Import line @~/.claude/rules/ecc/<language>/index.md | docs/guides/SKILLS.md | `## Frameworks` |
| S366 | docs/guides/SKILLS.md:647 | Languages: common, typescript, python, golang, rust, java, web | docs/guides/SKILLS.md | `## Frameworks` |
| S367 | docs/guides/SKILLS.md:649 | Skills installed heading | docs/guides/SKILLS.md | `## Frameworks` |
| S368 | docs/guides/SKILLS.md:651 | ECC language pattern skills (golang, python, rust, java, jpa, fastapi, django) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S369 | docs/guides/SKILLS.md:653 | ECC frontend/backend skills (frontend-patterns, backend-patterns, api-design, nextjs, nestjs, vite, prisma) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S370 | docs/guides/SKILLS.md:655 | ECC infrastructure skills (deployment, docker, postgres, migrations, redis) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S371 | docs/guides/SKILLS.md:657 | ECC architecture skills (hexagonal, ADRs, coding-standards, error-handling, git-workflow) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S372 | docs/guides/SKILLS.md:659 | ECC workflow skills (tdd-workflow, e2e-testing, search-first, autonomous-loops, iterative-retrieval, deep-research, production-audit, codebase-onboarding) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S373 | docs/guides/SKILLS.md:661 | ECC tools skills (mcp-server-patterns, github-ops, benchmark, api-connector-builder, article-writing) | docs/guides/SKILLS.md | `## Downloaded skills` |
| S374 | docs/guides/SKILLS.md:663 | Commands installed heading ~/.claude/commands/ | docs/guides/SKILLS.md | `## Frameworks` |
| S375 | docs/guides/SKILLS.md:665 | ECC language commands (/go-review ... /fastapi-review) | docs/guides/SKILLS.md | `## Frameworks` |
| S376 | docs/guides/SKILLS.md:667 | ECC multi-agent commands (/multi-plan ... /multi-frontend) | docs/guides/SKILLS.md | `## Frameworks` |
| S377 | docs/guides/SKILLS.md:669 | ECC general commands (/plan, /build-fix, /refactor-clean ... /plan-prd) | config/manifest.json | `frameworks.ecc.install` |
| S378 | docs/guides/SKILLS.md:671 | Reinstall on new machine heading | docs/guides/SETUP.md | `## Restore on a new machine` |
| S379 | docs/guides/SKILLS.md:673 | Agents and rules come from this repo, not upstream | docs/guides/SETUP.md | `## Restore on a new machine` |
| S380 | docs/guides/SKILLS.md:674 | Re-copying upstream would overwrite rules/ecc/common code-review.md and testing.md additions | docs/guides/SETUP.md | `## Frameworks` |
| S381 | docs/guides/SKILLS.md:675 | Re-copying drops the two hand-written agents | docs/guides/SETUP.md | `## Frameworks` |
| S382 | docs/guides/SKILLS.md:680 | cp -a agents/. ~/.claude/agents/ | docs/guides/SETUP.md | `## Restore on a new machine` |
| S383 | docs/guides/SKILLS.md:681 | mkdir -p ~/.claude/rules | docs/guides/SETUP.md | `## Restore on a new machine` |
| S384 | docs/guides/SKILLS.md:682 | cp -a rules/. ~/.claude/rules/ | docs/guides/SETUP.md | `## Restore on a new machine` |
| S385 | docs/guides/SKILLS.md:685 | cp block-destructive.sh into ~/.claude/hooks/ | docs/guides/SETUP.md | `## Restore on a new machine` |
| S386 | docs/guides/SKILLS.md:686 | cp chroma-reaper.sh into ~/.claude/scripts/ | docs/guides/SETUP.md | `## Restore on a new machine` |
| S387 | docs/guides/SKILLS.md:687 | chmod +x both | docs/guides/SETUP.md | `## Restore on a new machine` |
| S388 | docs/guides/SKILLS.md:688 | bash block-destructive.sh --test must print all self-checks passed | docs/guides/SETUP.md | `## Restore on a new machine` |
| S389 | docs/guides/SKILLS.md:691 | ECC skills and commands are not vendored; they come from upstream | docs/guides/SETUP.md | `## Restore on a new machine` |
| S390 | docs/guides/SKILLS.md:695 | git clone --depth=1 affaan-m/ECC to /tmp/ecc | docs/guides/SETUP.md | `## Restore on a new machine` |
| S391 | docs/guides/SKILLS.md:698 | loop copying the ~40 ECC skills | config/manifest.json | `entries.api-design.install` |
| S392 | docs/guides/SKILLS.md:708 | cp -r each skill into ~/.claude/skills/ | config/manifest.json | `entries.api-design.install` |
| S393 | docs/guides/SKILLS.md:712 | mkdir -p ~/.claude/commands | docs/guides/SETUP.md | `## Restore on a new machine` |
| S394 | docs/guides/SKILLS.md:713 | loop copying 27 ECC commands | config/manifest.json | `frameworks.ecc.install` |
| S395 | docs/guides/SKILLS.md:719 | cp each command into ~/.claude/commands/ | config/manifest.json | `frameworks.ecc.install` |
| S396 | docs/guides/SKILLS.md:722 | remove the temp clone | docs/guides/SETUP.md | `## Restore on a new machine` |
| S397 | docs/guides/SKILLS.md:726 | Available but not installed heading | docs/guides/SETUP.md | `## Frameworks` |
| S398 | docs/guides/SKILLS.md:728 | Skipped to keep install focused; no conflicts; clone ECC and copy | docs/guides/SETUP.md | `## Frameworks` |
| S399 | docs/guides/SKILLS.md:730 | Agents not installed heading | docs/guides/SETUP.md | `## Frameworks` |
| S400 | docs/guides/SKILLS.md:732 | git clone ECC | docs/guides/SETUP.md | `## Frameworks` |
| S401 | docs/guides/SKILLS.md:734 | Optional agent fastapi-reviewer | docs/guides/SETUP.md | `## Frameworks` |
| S402 | docs/guides/SKILLS.md:735 | Optional agent django-reviewer | docs/guides/SETUP.md | `## Frameworks` |
| S403 | docs/guides/SKILLS.md:736 | Optional agent django-build-resolver | docs/guides/SETUP.md | `## Frameworks` |
| S404 | docs/guides/SKILLS.md:737 | Optional agent code-simplifier | docs/guides/SETUP.md | `## Frameworks` |
| S405 | docs/guides/SKILLS.md:738 | Optional agent comment-analyzer | docs/guides/SETUP.md | `## Frameworks` |
| S406 | docs/guides/SKILLS.md:739 | Optional agent type-design-analyzer | docs/guides/SETUP.md | `## Frameworks` |
| S407 | docs/guides/SKILLS.md:740 | Optional agent harness-optimizer | docs/guides/SETUP.md | `## Frameworks` |
| S408 | docs/guides/SKILLS.md:741 | remove the temp clone | docs/guides/SETUP.md | `## Frameworks` |
| S409 | docs/guides/SKILLS.md:744 | Skills not installed heading | docs/guides/SETUP.md | `## Frameworks` |
| S410 | docs/guides/SKILLS.md:748 | Optional skill code-tour | docs/guides/SETUP.md | `## Frameworks` |
| S411 | docs/guides/SKILLS.md:749 | Optional skill benchmark-optimization-loop | docs/guides/SETUP.md | `## Frameworks` |
| S412 | docs/guides/SKILLS.md:750 | Optional skill frontend-a11y | docs/guides/SETUP.md | `## Frameworks` |
| S413 | docs/guides/SKILLS.md:751 | Optional skill product-lens | docs/guides/SETUP.md | `## Frameworks` |
| S414 | docs/guides/SKILLS.md:752 | Optional skill context-budget | docs/guides/SETUP.md | `## Frameworks` |
| S415 | docs/guides/SKILLS.md:753 | Optional skill regex-vs-llm-structured-text | docs/guides/SETUP.md | `## Frameworks` |
| S416 | docs/guides/SKILLS.md:754 | Optional skill agentic-engineering | docs/guides/SETUP.md | `## Frameworks` |
| S417 | docs/guides/SKILLS.md:755 | Optional skill ai-first-engineering | docs/guides/SETUP.md | `## Frameworks` |
| S418 | docs/guides/SKILLS.md:756 | Optional skill blueprint | docs/guides/SETUP.md | `## Frameworks` |
| S419 | docs/guides/SKILLS.md:757 | Optional skill prompt-optimizer | docs/guides/SETUP.md | `## Frameworks` |
| S420 | docs/guides/SKILLS.md:758 | Optional skill exa-search | docs/guides/SETUP.md | `## Frameworks` |
| S421 | docs/guides/SKILLS.md:759 | Optional skill design-system | docs/guides/SETUP.md | `## Frameworks` |
| S422 | docs/guides/SKILLS.md:760 | Optional skill plan-orchestrate | docs/guides/SETUP.md | `## Frameworks` |
| S423 | docs/guides/SKILLS.md:764 | Commands not installed heading | docs/guides/SETUP.md | `## Frameworks` |
| S424 | docs/guides/SKILLS.md:767 | Optional command feature-dev | docs/guides/SETUP.md | `## Frameworks` |
| S425 | docs/guides/SKILLS.md:768 | Optional command skill-health | docs/guides/SETUP.md | `## Frameworks` |
| S426 | docs/guides/SKILLS.md:769 | Optional command update-codemaps | docs/guides/SETUP.md | `## Frameworks` |

## docs/guides/PLUGINS.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| P1 | docs/guides/PLUGINS.md:1 | Page title: Plugins | docs/guides/SETUP.md | `## Plugins` |
| P2 | docs/guides/PLUGINS.md:3 | Plugins installed via claude plugin install; auto-update on launch | docs/guides/SETUP.md | `## Plugins` |
| P3 | docs/guides/PLUGINS.md:5 | Core pair heading: superpowers + claude-mem | docs/guides/SETUP.md | `## Plugins` |
| P4 | docs/guides/PLUGINS.md:8 | The two were installed together as a unit | docs/guides/SETUP.md | `## Plugins` |
| P5 | docs/guides/PLUGINS.md:9 | superpowers: structured workflows for debugging, TDD, review, planning | docs/guides/SETUP.md | `## Plugins` |
| P6 | docs/guides/PLUGINS.md:10 | claude-mem: persistent memory across sessions | docs/guides/SETUP.md | `## Plugins` |
| P7 | docs/guides/PLUGINS.md:12 | Neither is useful without the other | docs/guides/SETUP.md | `## Plugins` |
| P8 | docs/guides/PLUGINS.md:15 | superpowers v6.3.0 | docs/guides/SETUP.md | `## Keep it current` |
| P9 | docs/guides/PLUGINS.md:16 | superpowers source claude-plugins-official/superpowers | docs/guides/SETUP.md | `## Plugins` |
| P10 | docs/guides/PLUGINS.md:17 | superpowers install: claude plugin install superpowers | docs/guides/SETUP.md | `## Plugins` |
| P11 | docs/guides/PLUGINS.md:18 | superpowers skills list (13 skills) | docs/guides/SETUP.md | `## Plugins` |
| P12 | docs/guides/PLUGINS.md:20 | Foundation plugin, always loaded, other skills integrate with it | docs/guides/SETUP.md | `## Plugins` |
| P13 | docs/guides/PLUGINS.md:24 | claude-mem v13.24.0 | docs/guides/SETUP.md | `## Keep it current` |
| P14 | docs/guides/PLUGINS.md:25 | claude-mem source thedotmack/claude-mem | docs/guides/SETUP.md | `## Plugins` |
| P15 | docs/guides/PLUGINS.md:26 | claude-mem install: claude plugin install claude-mem | docs/guides/SETUP.md | `## Plugins` |
| P16 | docs/guides/PLUGINS.md:27 | claude-mem skills list (15 skills) | docs/guides/SETUP.md | `## Plugins` |
| P17 | docs/guides/PLUGINS.md:29 | Run /learn-codebase on a new repo; /mem-search to recall | docs/guides/SETUP.md | `## Plugins` |
| P18 | docs/guides/PLUGINS.md:33 | frontend-design heading | docs/guides/SETUP.md | `## Plugins` |
| P19 | docs/guides/PLUGINS.md:34 | frontend-design source claude-plugins-official/frontend-design | docs/guides/SETUP.md | `## Plugins` |
| P20 | docs/guides/PLUGINS.md:35 | frontend-design install | docs/guides/SETUP.md | `## Plugins` |
| P21 | docs/guides/PLUGINS.md:36 | frontend-design adds /frontend-design | docs/guides/SETUP.md | `## Plugins` |
| P22 | docs/guides/PLUGINS.md:38 | Anthropic's baseline UI skill; impeccable and taste build on it | docs/guides/SETUP.md | `## Plugins` |
| P23 | docs/guides/PLUGINS.md:42 | code-review heading | docs/guides/SETUP.md | `## Plugins` |
| P24 | docs/guides/PLUGINS.md:43 | code-review source claude-plugins-official/code-review | docs/guides/SETUP.md | `## Plugins` |
| P25 | docs/guides/PLUGINS.md:44 | code-review install | docs/guides/SETUP.md | `## Plugins` |
| P26 | docs/guides/PLUGINS.md:45 | /code-review:code-review reviews a GitHub PR with parallel agents and posts one comment | docs/guides/SETUP.md | `## Plugins` |
| P27 | docs/guides/PLUGINS.md:46 | Effort levels, ultra, --comment, --fix belong to the built-in /code-review (no file on disk) | docs/guides/SETUP.md | `## Plugins` |
| P28 | docs/guides/PLUGINS.md:46 | CLAUDE.md says which to use | docs/guides/SETUP.md | `## Plugins` |
| P29 | docs/guides/PLUGINS.md:48 | Focused diff review before merging; pairs with gstack /review | docs/guides/SETUP.md | `## Plugins` |
| P30 | docs/guides/PLUGINS.md:52 | feature-dev heading | docs/guides/SETUP.md | `## Plugins` |
| P31 | docs/guides/PLUGINS.md:53 | feature-dev source | docs/guides/SETUP.md | `## Plugins` |
| P32 | docs/guides/PLUGINS.md:54 | feature-dev install | docs/guides/SETUP.md | `## Plugins` |
| P33 | docs/guides/PLUGINS.md:55 | feature-dev adds agents code-architect, code-explorer, code-reviewer | docs/guides/SETUP.md | `## Plugins` |
| P34 | docs/guides/PLUGINS.md:57 | Subagents used internally by skills needing codebase analysis | docs/guides/SETUP.md | `## Plugins` |
| P35 | docs/guides/PLUGINS.md:61 | code-simplifier v1.0.0 | docs/guides/SETUP.md | `## Keep it current` |
| P36 | docs/guides/PLUGINS.md:62 | code-simplifier source | docs/guides/SETUP.md | `## Plugins` |
| P37 | docs/guides/PLUGINS.md:63 | code-simplifier install | docs/guides/SETUP.md | `## Plugins` |
| P38 | docs/guides/PLUGINS.md:65 | Refactors recent code as a subagent; use after a feature before review | docs/guides/SETUP.md | `## Plugins` |
| P39 | docs/guides/PLUGINS.md:69 | ralph-loop v1.0.0 | docs/guides/SETUP.md | `## Keep it current` |
| P40 | docs/guides/PLUGINS.md:70 | ralph-loop source | docs/guides/SETUP.md | `## Plugins` |
| P41 | docs/guides/PLUGINS.md:71 | ralph-loop install | docs/guides/SETUP.md | `## Plugins` |
| P42 | docs/guides/PLUGINS.md:72 | ralph-loop adds /ralph-loop and /cancel-ralph | docs/guides/SETUP.md | `## Plugins` |
| P43 | docs/guides/PLUGINS.md:74 | Autonomous loop runner for long background tasks | docs/guides/SETUP.md | `## Plugins` |
| P44 | docs/guides/PLUGINS.md:78 | clangd-lsp v1.0.0 | docs/guides/SETUP.md | `## Keep it current` |
| P45 | docs/guides/PLUGINS.md:79 | clangd-lsp source | docs/guides/SETUP.md | `## Plugins` |
| P46 | docs/guides/PLUGINS.md:80 | clangd-lsp install | docs/guides/SETUP.md | `## Plugins` |
| P47 | docs/guides/PLUGINS.md:82 | C/C++ LSP integration | docs/guides/SETUP.md | `## Plugins` |
| P48 | docs/guides/PLUGINS.md:86 | ponytail v4.9.0 | docs/guides/SETUP.md | `## Keep it current` |
| P49 | docs/guides/PLUGINS.md:87 | ponytail source DietrichGebert/ponytail, third-party marketplace | docs/guides/SETUP.md | `## Plugins` |
| P50 | docs/guides/PLUGINS.md:88 | ponytail install: claude plugins marketplace add, then claude plugins install ponytail@ponytail | docs/guides/SETUP.md | `## Plugins` |
| P51 | docs/guides/PLUGINS.md:89 | ponytail skills list | docs/guides/SETUP.md | `## Plugins` |
| P52 | docs/guides/PLUGINS.md:91 | ponytail: lazy senior dev mode with a YAGNI ladder, shortest diff | docs/guides/SETUP.md | `## Plugins` |
| P53 | docs/guides/PLUGINS.md:91 | Active every session via SessionStart hook; state in ~/.claude/.ponytail-active | docs/guides/SETUP.md | `## Plugins` |
| P54 | docs/guides/PLUGINS.md:91 | Levels lite/full/ultra; switch with /ponytail <level>; stop with 'stop ponytail' | docs/guides/SETUP.md | `## Plugins` |
| P55 | docs/guides/PLUGINS.md:95 | security-guidance v2.0.7 | docs/guides/SETUP.md | `## Keep it current` |
| P56 | docs/guides/PLUGINS.md:96 | security-guidance source claude-plugins-official (Anthropic) | docs/guides/SETUP.md | `## Plugins` |
| P57 | docs/guides/PLUGINS.md:97 | security-guidance install with @claude-plugins-official | docs/guides/SETUP.md | `## Plugins` |
| P58 | docs/guides/PLUGINS.md:99 | Installed 2026-07-07 | docs/guides/SETUP.md | `dropped: dated history note; plugin is listed` |
| P59 | docs/guides/PLUGINS.md:99 | Passive net: regex warnings on Edit/Write, diff review on Stop, flow analysis on commit | docs/guides/SETUP.md | `## Plugins` |
| P60 | docs/guides/PLUGINS.md:100 | Complements on-demand review-stack | docs/guides/SETUP.md | `## Plugins` |
| P61 | docs/guides/PLUGINS.md:100 | Set ENABLE_STOP_REVIEW=0 to skip per-turn Stop review if cost bites | docs/guides/SETUP.md | `## Plugins` |
| P62 | docs/guides/PLUGINS.md:105 | Marketplace added, plugin not installed heading | docs/guides/SETUP.md | `## Plugins` |
| P63 | docs/guides/PLUGINS.md:107 | claude-seo marketplace added, plugin not installed | docs/guides/SETUP.md | `## Plugins` |
| P64 | docs/guides/PLUGINS.md:108 | claude-seo source AgriciDaniel/claude-seo, MIT | docs/guides/SETUP.md | `## Plugins` |
| P65 | docs/guides/PLUGINS.md:109 | Marketplace registered as agricidaniel-claude-seo in settings.json and known_marketplaces.json | docs/guides/SETUP.md | `## Plugins` |
| P66 | docs/guides/PLUGINS.md:111 | claude-seo install: claude plugin install claude-seo@agricidaniel-claude-seo | docs/guides/SETUP.md | `## Plugins` |
| P67 | docs/guides/PLUGINS.md:113 | claude-seo: 25 sub-skills and 18 GEO/AEO agents, audit-only, no account access, no auto-publish | docs/guides/SETUP.md | `## Plugins` |
| P68 | docs/guides/PLUGINS.md:114 | Complements build-time SEO-GUIDE.md (guide = spec, plugin = audit) | docs/guides/SETUP.md | `## Plugins` |
| P69 | docs/guides/PLUGINS.md:115 | Wired into seo-ops and /monthly-ops SEO add-on | docs/guides/SETUP.md | `## Plugins` |
| P70 | docs/guides/PLUGINS.md:119 | Keeping plugins current heading | docs/guides/SETUP.md | `## Keep it current` |
| P71 | docs/guides/PLUGINS.md:122 | loop over marketplaces: claude-plugins-official thedotmack ponytail agricidaniel-claude-seo | docs/guides/SETUP.md | `## Keep it current` |
| P72 | docs/guides/PLUGINS.md:123 | claude plugin marketplace update <name> | docs/guides/SETUP.md | `## Keep it current` |
| P73 | docs/guides/PLUGINS.md:125 | claude plugin list | docs/guides/SETUP.md | `## Keep it current` |
| P74 | docs/guides/PLUGINS.md:126 | claude plugin update <plugin>@<marketplace> | docs/guides/SETUP.md | `## Keep it current` |
| P75 | docs/guides/PLUGINS.md:128 | Restart Claude Code afterwards; updates are staged | docs/guides/SETUP.md | `## Keep it current` |
| P76 | docs/guides/PLUGINS.md:129 | Versions last verified 2026-09-02 | docs/guides/SETUP.md | `dropped: dated history note` |

## docs/guides/MCP.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| M1 | docs/guides/MCP.md:1 | Page title: MCP Servers | docs/guides/SETUP.md | `## MCP servers` |
| M2 | docs/guides/MCP.md:3 | Two MCP servers active; magic configured in ~/.claude.json | docs/guides/SETUP.md | `## MCP servers` |
| M3 | docs/guides/MCP.md:4 | context7 enabled in settings.local.json and declared in ~/.mcp.json | docs/guides/SETUP.md | `## MCP servers` |
| M4 | docs/guides/MCP.md:6 | context7 heading | docs/guides/SETUP.md | `## MCP servers` |
| M5 | docs/guides/MCP.md:8 | context7 source: claude.ai connectors plus stdio entry in ~/.mcp.json written by jjstack ./setup | docs/guides/SETUP.md | `## MCP servers` |
| M6 | docs/guides/MCP.md:9 | Stdio command npx -y @upstash/context7-mcp | docs/guides/SETUP.md | `## MCP servers` |
| M7 | docs/guides/MCP.md:9 | Setup skips if a context7 key exists, so rerun is safe | docs/guides/SETUP.md | `## MCP servers` |
| M8 | docs/guides/MCP.md:11 | Enabled via enabledMcpjsonServers: [context7] in settings.local.json | docs/guides/SETUP.md | `## MCP servers` |
| M9 | docs/guides/MCP.md:13 | context7 fetches live docs for any library, framework, SDK or CLI | docs/guides/SETUP.md | `## MCP servers` |
| M10 | docs/guides/MCP.md:15 | Training data may be stale; context7 has current docs | docs/guides/SETUP.md | `## MCP servers` |
| M11 | docs/guides/MCP.md:17 | Use for API syntax, config, migration, CLI usage; Claude reaches for it automatically | docs/guides/SETUP.md | `## MCP servers` |
| M12 | docs/guides/MCP.md:20 | New machine: Claude Code settings, MCP, enable the context7 connector | docs/guides/SETUP.md | `## Restore on a new machine` |
| M13 | docs/guides/MCP.md:24 | magic (21st-dev) heading | docs/guides/SETUP.md | `## MCP servers` |
| M14 | docs/guides/MCP.md:26 | magic package @21st-dev/magic@latest | docs/guides/SETUP.md | `## MCP servers` |
| M15 | docs/guides/MCP.md:27 | magic type stdio via npx | docs/guides/SETUP.md | `## MCP servers` |
| M16 | docs/guides/MCP.md:29 | magic generates UI components from the 21st.dev library | docs/guides/SETUP.md | `## MCP servers` |
| M17 | docs/guides/MCP.md:31 | Use for a production-quality starting component | docs/guides/SETUP.md | `## MCP servers` |
| M18 | docs/guides/MCP.md:33 | Config for ~/.claude.json mcpServers.magic | docs/guides/SETUP.md | `## MCP servers` |
| M19 | docs/guides/MCP.md:35 | JSON: type stdio | docs/guides/SETUP.md | `## MCP servers` |
| M20 | docs/guides/MCP.md:39 | JSON: command npx | docs/guides/SETUP.md | `## MCP servers` |
| M21 | docs/guides/MCP.md:40 | JSON: args -y @21st-dev/magic@latest | docs/guides/SETUP.md | `## MCP servers` |
| M22 | docs/guides/MCP.md:41 | JSON: env API_KEY placeholder | docs/guides/SETUP.md | `## MCP servers` |
| M23 | docs/guides/MCP.md:49 | Get API key at 21st.dev | docs/guides/SETUP.md | `## MCP servers` |
| M24 | docs/guides/MCP.md:51 | Adding MCP servers heading | docs/guides/SETUP.md | `## MCP servers` |
| M25 | docs/guides/MCP.md:54 | Edit ~/.claude.json and add to mcpServers | docs/guides/SETUP.md | `## MCP servers` |
| M26 | docs/guides/MCP.md:55 | Or use the settings UI: /config | docs/guides/SETUP.md | `## MCP servers` |

## docs/guides/SKILLS-EVALUATION.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| E1 | docs/guides/SKILLS-EVALUATION.md:1 | Title: Skills Evaluation Log | docs/research/SKILLS-EVALUATION.md | `## Skills Evaluation Log` |
| E2 | docs/guides/SKILLS-EVALUATION.md:3 | Intro: every third-party skill considered, verdict, wiring; evaluated 2026-07 | docs/research/SKILLS-EVALUATION.md | `## Skills Evaluation Log` |
| E3 | docs/guides/SKILLS-EVALUATION.md:8 | Rule: nothing installed-and-forgotten; adopted skills registered and referenced | docs/research/SKILLS-EVALUATION.md | `## Skills Evaluation Log` |
| E4 | docs/guides/SKILLS-EVALUATION.md:11 | Adopted table (11 rows: seo-ops ... graphify) | docs/research/SKILLS-EVALUATION.md | `## Adopted` |
| E5 | docs/guides/SKILLS-EVALUATION.md:27 | Rejected table (distribb, NotFair, claude-ads x2, taste, transitions.dev overturned, ux-designer, artifacts-builder) | docs/research/SKILLS-EVALUATION.md | `## Rejected (logged so we don't re-litigate)` |
| E6 | docs/guides/SKILLS-EVALUATION.md:40 | Rejected 2026-08-06 table (genjutsu ... IG carousel) | docs/research/SKILLS-EVALUATION.md | `## Rejected 2026-08-06 (design/marketing intake round)` |
| E7 | docs/guides/SKILLS-EVALUATION.md:57 | The 20 unsourced names from that carousel and why unresolved | docs/research/SKILLS-EVALUATION.md | `## The 20 unsourced names from that carousel` |
| E8 | docs/guides/SKILLS-EVALUATION.md:70 | Adopted 2026-08-06 table (emilkowalski ... packshot) | docs/research/SKILLS-EVALUATION.md | `## Adopted 2026-08-06` |
| E9 | docs/guides/SKILLS-EVALUATION.md:83 | Content-writing pack: dumbify, storytelling, viral-hooks, install by subdir | docs/research/SKILLS-EVALUATION.md | `## Content-writing pack (situational - install per need)` |
| E10 | docs/guides/SKILLS-EVALUATION.md:87 | SaaS list: use and ignore choices | docs/research/SKILLS-EVALUATION.md | `## SaaS (subscriptions, not skills - see REVISION-PLAN sec. 9)` |

# Docs map part C (HOOKS.md, DESIGN-PIPELINE.md, USAGE.md)

## docs/guides/HOOKS.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| K1 | docs/guides/HOOKS.md:3-4 | Most hooks are auto-managed; reinstalling gstack, jjstack, claude-mem restores them | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K2 | docs/guides/HOOKS.md:4-5 | Two hooks are hand-written in this repo: block-destructive.sh, chroma-reaper.sh | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K3 | docs/guides/HOOKS.md:11 | gsd-check-update.js (get-shit-done-cc): update check at session start | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K4 | docs/guides/HOOKS.md:12 | gsd-session-state.sh: injects project state reminder at session start | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K5 | docs/guides/HOOKS.md:13 | gsd-context-monitor.js not wired since spec 0037; context-monitor.js replaces it | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K6 | docs/guides/HOOKS.md:13 | Reason: it read a bridge file only gsd's status line writes, never fired | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K7 | docs/guides/HOOKS.md:14 | gsd-phase-boundary.sh: detects .planning/ writes to track phase progress | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K8 | docs/guides/HOOKS.md:15 | gsd-prompt-guard.js: guards prompts on Write/Edit | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K9 | docs/guides/HOOKS.md:16 | gsd-read-guard.js not wired: on disk, no settings.json entry | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K10 | docs/guides/HOOKS.md:17 | gsd-workflow-guard.js: enforces GSD workflow rules on Write/Edit | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K11 | docs/guides/HOOKS.md:18 | gsd-validate-commit.sh: enforces Conventional Commits on Bash | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K12 | docs/guides/HOOKS.md:19 | claude-mem-install.sh (claude-mem): ensures claude-mem node_modules are installed | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K13 | docs/guides/HOOKS.md:20 | auto-approve-safe.sh (jjstack): permission gate using Haiku for safe ops | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K14 | docs/guides/HOOKS.md:21 | error-detector.sh (jjstack): records failed Bash commands to a JSONL log | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K15 | docs/guides/HOOKS.md:22 | injection-guard.sh (jjstack): scans Write/Edit .md content for prompt injection | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K16 | docs/guides/HOOKS.md:23 | mcp-reconnect.sh (jjstack): reconnects MCP servers on tool failure | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K17 | docs/guides/HOOKS.md:23 | mcp-reconnect.sh is not symlinked; settings.json calls ~/.claude/skills/jjstack/hooks/ | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K18 | docs/guides/HOOKS.md:24 | skill-miss-detect.sh: UserPromptSubmit hook, spec 0036 | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K19 | docs/guides/HOOKS.md:24 | Logs to ~/.jjstack/skill-misses.jsonl, rotated at 500 lines | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K20 | docs/guides/HOOKS.md:24 | trigger_miss: message matched trigger words (skill-triggers.json), no skill ran | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K21 | docs/guides/HOOKS.md:24 | user_correction logged for /missed <skill> | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K22 | docs/guides/HOOKS.md:24 | wrong_skill: a correction ("no", "use /x", any /word) within 5 minutes of a skill firing | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K23 | docs/guides/HOOKS.md:24 | skill-miss-detect never blocks; off when WF_RUN is set | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K24 | docs/guides/HOOKS.md:25 | skill-fired-clear.sh: PreToolUse on Skill, spec 0036 | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K25 | docs/guides/HOOKS.md:25 | Records firing skill in ~/.jjstack/skill-last-fired.json, clears its pending note | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K26 | docs/guides/HOOKS.md:25 | skill-fired-clear is off when WF_RUN is set | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K27 | docs/guides/HOOKS.md:25 | Command: ~/.claude/skills/jjstack/bin/jjstack-skill-miss-report (24 h, 72 h, lifetime, HOT/WARM/COLD) | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K28 | docs/guides/HOOKS.md:26 | block-destructive.sh: hand-written PreToolUse gate on Bash | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K29 | docs/guides/HOOKS.md:26 | It hard-blocks rm -rf on absolute, home, parent, wildcard targets | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K30 | docs/guides/HOOKS.md:27 | context-monitor.js: derived from get-shit-done-cc, lives in claude-home/hooks/ | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K31 | docs/guides/HOOKS.md:27 | PostToolUse on Bash/Edit/Write/MultiEdit/Agent/Task; reads session transcript | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K32 | docs/guides/HOOKS.md:27 | Warns at 150k tokens (again every 100k) to finish step and /rollover; once at 650k | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K33 | docs/guides/HOOKS.md:27 | context-monitor is silent under wf (spec 0037) | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K34 | docs/guides/HOOKS.md:27 | Command: node claude-home/hooks/context-monitor.js --test | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K35 | docs/guides/HOOKS.md:28 | review-stack-pre-push is a git hook, not a Claude Code hook | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K36 | docs/guides/HOOKS.md:28 | Symlink it to a repo's .git/hooks/pre-push; never in a bot-reviewed repo | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K37 | docs/guides/HOOKS.md:28 | Refuses push with no /review-stack receipt or a BLOCK receipt; calls no model | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K38 | docs/guides/HOOKS.md:29 | gate.sh: Stop hook, registered from SKILL.md frontmatter of design and brand-system | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K39 | docs/guides/HOOKS.md:29 | gate.sh exits 0 unless ~/.claude/.design-active exists | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K40 | docs/guides/HOOKS.md:29 | With an open run it exits 2 with unclosed ledger rows, at most twice | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K41 | docs/guides/HOOKS.md:29 | Third stop releases and marks the run escaped:true | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K42 | docs/guides/HOOKS.md:29 | Abandoned (>24h) or unreadable ledger also releases | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K43 | docs/guides/HOOKS.md:29 | Verified by claude-home/skills/design/scripts/test-ledger.sh | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K44 | docs/guides/HOOKS.md:30 | chroma-reaper.sh: background reaper, once per session, stops chroma process pile-up | docs/guides/HOOKS.md | `## Where each hook comes from` |
| K45 | docs/guides/HOOKS.md:34-39 | Autocompact not overridden; old CLAUDE_AUTOCOMPACT_PCT_OVERRIDE 100 removed | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K46 | docs/guides/HOOKS.md:36-39 | Threshold is min(window*pct/100, window-13000); the override only fires earlier | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K47 | docs/guides/HOOKS.md:39 | Default already leaves a 13k summary buffer | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K48 | docs/guides/HOOKS.md:41-42 | Model not pinned; opus[1m] pin removed in commit 82fcf80 | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K49 | docs/guides/HOOKS.md:42 | Model is chosen at runtime (/model or session default) | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K50 | docs/guides/HOOKS.md:44-45 | permissions.defaultMode auto plus skipAutoPermissionPrompt true, paired with auto-approve-safe.sh | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K51 | docs/guides/HOOKS.md:45-47 | Auto-mode classifier still blocks git reset --hard and some git merge shapes | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K52 | docs/guides/HOOKS.md:46-47 | When blocked: run it yourself with the ! prefix or use a narrower command | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K53 | docs/guides/HOOKS.md:49-50 | block-destructive.sh is the backstop surviving auto-mode; refused rm -rf runs by hand | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K54 | docs/guides/HOOKS.md:52-53 | Since jjstack 0.4x (upstream #36, 2026-09-09) auto-approve-safe is audit log and relay only | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K55 | docs/guides/HOOKS.md:53-55 | Policy is permissions.deny in settings.json (jjstack permissions.policy.json merged, defaultMode auto) | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K56 | docs/guides/HOOKS.md:55-57 | permission-floor.py: PreToolUse deny for ten unbounded shapes | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K57 | docs/guides/HOOKS.md:56-57 | The ten shapes: root/home targets, curl-to-shell, upload, secret paths, block devices, fork bomb, power, sudo-destructive, force-push trunk, push --mirror | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K58 | docs/guides/HOOKS.md:57-58 | Old local Haiku-prompt patch and upstream PR #31 retired | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K59 | docs/guides/HOOKS.md:60-62 | gsd-read-guard.js is on disk but unwired; read-before-edit comes from the harness | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K60 | docs/guides/HOOKS.md:64 | Status line is jjstack/bin/statusline.sh, shows project state | docs/guides/HOOKS.md | `## Settings the hooks rely on` |
| K61 | docs/guides/HOOKS.md:68 | Hook paths are hardcoded to /home/santiago/ | docs/guides/SETUP.md | `## Restore on a new machine` |
| K62 | docs/guides/HOOKS.md:69 | Step 1: install jjstack (installs gstack and hook symlinks) | docs/guides/SETUP.md | `## Restore on a new machine` |
| K63 | docs/guides/HOOKS.md:70-72 | Step 1b: install get-shit-done-cc; ships 8 gsd-* hooks, settings.json references 6 | docs/guides/SETUP.md | `## Restore on a new machine` |
| K64 | docs/guides/HOOKS.md:71-72 | Without 1b the session starts with dead hook entries | docs/guides/SETUP.md | `## Restore on a new machine` |
| K65 | docs/guides/HOOKS.md:72 | Pin get-shit-done-cc at 1.34.2 (pin note in SKILLS.md) | docs/guides/SETUP.md | `## Frameworks` |
| K66 | docs/guides/HOOKS.md:73 | Step 2: install the claude-mem plugin | docs/guides/SETUP.md | `## Restore on a new machine` |
| K67 | docs/guides/HOOKS.md:74 | Step 3: copy settings.json and fix /home/santiago/ paths for the new home | docs/guides/SETUP.md | `## Restore on a new machine` |
| K68 | docs/guides/HOOKS.md:75 | Step 4: settings.local.json can be copied as-is | docs/guides/SETUP.md | `## Restore on a new machine` |

## docs/guides/DESIGN-PIPELINE.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| D1 | docs/guides/DESIGN-PIPELINE.md:1 | Title: Design pipeline - setup and use | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D2 | docs/guides/DESIGN-PIPELINE.md:3-10 | Warning: old `claude mcp add magic ... API_KEY` command is broken, do not run | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D3 | docs/guides/DESIGN-PIPELINE.md:7 | Old command: claude mcp add magic --scope user --env API_KEY=... npx -y @21st-dev/magic@latest | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D4 | docs/guides/DESIGN-PIPELINE.md:9-10 | That command made the server that failed every session for months | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D5 | docs/guides/DESIGN-PIPELINE.md:10-12 | @21st-dev/magic is a shim; service moved to https://21st.dev/api/mcp | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D6 | docs/guides/DESIGN-PIPELINE.md:12 | Auth changed from API_KEY env var to x-api-key header | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D7 | docs/guides/DESIGN-PIPELINE.md:12-14 | /ui and /21 were never commands, only tool-description conventions, now gone | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D8 | docs/guides/DESIGN-PIPELINE.md:3 | Rewritten 2026-09-09 | docs/guides/DESIGN-PIPELINE.md | dropped: dated history note, the fact lives in the new text |
| D9 | docs/guides/DESIGN-PIPELINE.md:16 | Almost nothing to set up; read One-time, then use /design | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D10 | docs/guides/DESIGN-PIPELINE.md:22 | Three skills run the pipeline, not a retyped prompt | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D11 | docs/guides/DESIGN-PIPELINE.md:26 | /brand-system owns client identity; run ledger + Stop hook; emit closes when board passes checker | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D12 | docs/guides/DESIGN-PIPELINE.md:27 | /design owns surfaces in any stack; ledger + Stop hook; gate cannot be skipped | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D13 | docs/guides/DESIGN-PIPELINE.md:28 | /assets owns imagery, icons, shapes, background removal; triage table | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D14 | docs/guides/DESIGN-PIPELINE.md:28 | Most assets are coded or fetched, not generated | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D15 | docs/guides/DESIGN-PIPELINE.md:30-32 | /design-gate is the blind auditor, runs forked with no memory of the build | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D16 | docs/guides/DESIGN-PIPELINE.md:32 | Reason: an auditor that argued for a choice cannot grade it | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D17 | docs/guides/DESIGN-PIPELINE.md:33-34 | A signed brand-system.html outranks everything | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D18 | docs/guides/DESIGN-PIPELINE.md:34 | /design transcribes the :root tokens, does not re-derive them | docs/guides/DESIGN-PIPELINE.md | `## What runs the pipeline` |
| D19 | docs/guides/DESIGN-PIPELINE.md:38-47 | Preinstalled MCPs, nothing to do: mobbin, shadcn, 21st, chrome-devtools | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D20 | docs/guides/DESIGN-PIPELINE.md:43 | mobbin: real shipped app screens inline as images; paid plan, OAuth | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D21 | docs/guides/DESIGN-PIPELINE.md:44 | shadcn: component sourcing, any registry; no key, user-scoped | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D22 | docs/guides/DESIGN-PIPELINE.md:45 | 21st: inspiration, React+Tailwind only; x-api-key | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D23 | docs/guides/DESIGN-PIPELINE.md:46 | chrome-devtools: real perf measurement, drives Brave in a throwaway profile | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D24 | docs/guides/DESIGN-PIPELINE.md:49 | If /mcp does not list one, restart the session; MCP servers load at start | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D25 | docs/guides/DESIGN-PIPELINE.md:51-55 | Command: bash ~/.claude/skills/assets/scripts/gemini-key.sh set (paste key, hidden) | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D26 | docs/guides/DESIGN-PIPELINE.md:55 | Command: bash ~/.claude/skills/assets/scripts/gemini-key.sh test (proves billing on) | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D27 | docs/guides/DESIGN-PIPELINE.md:58-60 | Image generation is not on the Gemini free tier; a consumer subscription gives no API quota | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D28 | docs/guides/DESIGN-PIPELINE.md:60 | Key must be on a billing-enabled project; budget $2-4 per site | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D29 | docs/guides/DESIGN-PIPELINE.md:61-62 | Without a key /assets gives paste-ready prompts for the Gemini app | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D30 | docs/guides/DESIGN-PIPELINE.md:63-65 | Optional per project: pnpm dlx shadcn@latest mcp init --client claude | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D31 | docs/guides/DESIGN-PIPELINE.md:64-65 | That pins shadcn into repo .mcp.json for teammates; not needed for you | docs/guides/DESIGN-PIPELINE.md | `## One time setup` |
| D32 | docs/guides/DESIGN-PIPELINE.md:71-73 | Command: /design [what + where] is the whole prompt | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D33 | docs/guides/DESIGN-PIPELINE.md:75-76 | Old kickoff block now lives in the skill, enforced not suggested | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D34 | docs/guides/DESIGN-PIPELINE.md:76-79 | Add context only if it changes the answer: reference image/URL, brand colours, Figma link, CSS | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D35 | docs/guides/DESIGN-PIPELINE.md:78-79 | What you supply is locked as given; what you omit is decided and stated | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D36 | docs/guides/DESIGN-PIPELINE.md:80-81 | For a client build run /brand-system first, else /design proposes an unsigned direction | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D37 | docs/guides/DESIGN-PIPELINE.md:86 | Step detect: which stack, from the repo | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D38 | docs/guides/DESIGN-PIPELINE.md:87 | Step reference: real shipped UI first - Mobbin, Refero, public galleries | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D39 | docs/guides/DESIGN-PIPELINE.md:88 | Step direction: brand-system > design-dna on a reference > saved direction > ui-ux-pro-max | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D40 | docs/guides/DESIGN-PIPELINE.md:89 | Step tokens: direction becomes tokens.css, which makes it stack-agnostic | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D41 | docs/guides/DESIGN-PIPELINE.md:90 | Step source: shadcn MCP, then the per-stack matrix | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D42 | docs/guides/DESIGN-PIPELINE.md:91 | Step assemble: frontend-design + impeccable | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D43 | docs/guides/DESIGN-PIPELINE.md:92 | Step assets: /assets | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D44 | docs/guides/DESIGN-PIPELINE.md:93-94 | Step motion: animate; marketing measured against reference effects, product-ui against review-animations | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D45 | docs/guides/DESIGN-PIPELINE.md:95 | Step preview: owner sees the first finished section before the rest | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D46 | docs/guides/DESIGN-PIPELINE.md:96-98 | Step gate: impeccable critique >= 32/40, impeccable audit, review-animations if motion | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D47 | docs/guides/DESIGN-PIPELINE.md:97-98 | Then blind design-gate with each section beside the primary reference; generated assets must be used; cannot be skipped | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D48 | docs/guides/DESIGN-PIPELINE.md:99 | Step conversion: cro/pricing/signup/paywalls, marketing surfaces only | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D49 | docs/guides/DESIGN-PIPELINE.md:102-104 | Every listed skill must be invoked; a RAN row is refused unless a call is in the transcript | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D50 | docs/guides/DESIGN-PIPELINE.md:103-104 | Typing the slash command or a subagent counts; naming it or reading SKILL.md does not | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D51 | docs/guides/DESIGN-PIPELINE.md:106-107 | Each step closes a row in <project>/.design/run.json with evidence or a closed-vocabulary skip reason | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D52 | docs/guides/DESIGN-PIPELINE.md:107-109 | Stop hook refuses to end the turn while a row is open | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D53 | docs/guides/DESIGN-PIPELINE.md:108-109 | Closing table is generated from run.json, so it cannot claim a step that did not run | docs/guides/DESIGN-PIPELINE.md | `## Use it` |
| D54 | docs/guides/DESIGN-PIPELINE.md:114-116 | Rule 1: fonts and colours are searched, never picked from a list | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D55 | docs/guides/DESIGN-PIPELINE.md:115-116 | A lookup table gives no variety: every site got the same faces | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D56 | docs/guides/DESIGN-PIPELINE.md:116-117 | Old brand guide: 25 families in a 6-row table, Inter recommended in half | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D57 | docs/guides/DESIGN-PIPELINE.md:119-120 | Command: python3 ~/.claude/skills/design/scripts/fontsearch.py --adjectives loud active --anti calm --category Display --seed <client-slug> | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D58 | docs/guides/DESIGN-PIPELINE.md:121 | Command: node ~/.claude/skills/design/scripts/build-ramp.mjs --hue <deg> --sat 0.9 | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D59 | docs/guides/DESIGN-PIPELINE.md:124-125 | --seed <client-slug> is mandatory: samples the qualifying band, not the ranking top | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D60 | docs/guides/DESIGN-PIPELINE.md:125-127 | --min-pop 300 floor excludes Inter, Roboto, Poppins, Montserrat, Open Sans, Lato, Playfair | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D61 | docs/guides/DESIGN-PIPELINE.md:127 | Still leaves 189 quality-72+ Display families | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D62 | docs/guides/DESIGN-PIPELINE.md:129-130 | Rule 2: most assets should never touch an image model | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D63 | docs/guides/DESIGN-PIPELINE.md:129-132 | Icons from Iconify; backgrounds, grain, blobs are code; OG cards rendered text; mockups are real screenshots | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D64 | docs/guides/DESIGN-PIPELINE.md:131-133 | Portraits are a hard stop asking for a real photograph | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D65 | docs/guides/DESIGN-PIPELINE.md:132-133 | Generation is for conceptual and atmospheric imagery, about one asset in five | docs/guides/DESIGN-PIPELINE.md | `## The two rules that matter most` |
| D66 | docs/guides/DESIGN-PIPELINE.md:138 | Long-form material lives in the skills so it loads on demand | docs/guides/DESIGN-PIPELINE.md | `## Reference material` |
| D67 | docs/guides/DESIGN-PIPELINE.md:140 | skills/design/references/craft.md: 36-item AI-tell checklist, 25 ranked craft moves | docs/guides/DESIGN-PIPELINE.md | `## Reference material` |
| D68 | docs/guides/DESIGN-PIPELINE.md:141 | skills/design/references/stacks.md: stack detection, component matrix, token schema | docs/guides/DESIGN-PIPELINE.md | `## Reference material` |
| D69 | docs/guides/DESIGN-PIPELINE.md:142 | skills/design/references/reference-lock.md: Mobbin/Refero, gallery ladder, ToS limits | docs/guides/DESIGN-PIPELINE.md | `## Reference material` |
| D70 | docs/guides/DESIGN-PIPELINE.md:143 | skills/assets/references/: generation, sourcing, shapes, editing, prompting | docs/guides/DESIGN-PIPELINE.md | `## Reference material` |
| D71 | docs/guides/DESIGN-PIPELINE.md:144 | ~/projects/freelance/website-build-templates/guides/BRAND-SYSTEM-GUIDE.md: the craft layer | docs/guides/DESIGN-PIPELINE.md | `## Reference material` |
| D72 | docs/guides/DESIGN-PIPELINE.md:146-147 | Command: bash ~/.claude/skills/design/scripts/test-ledger.sh (37 assertions) verifies tooling | docs/guides/DESIGN-PIPELINE.md | `## Reference material` |

## docs/guides/USAGE.md

| # | Old file:line | Item | New file | New heading |
|---|---|---|---|---|
| U1 | docs/guides/USAGE.md:1-6 | Intro: decision guide for skill routing; router reads TRIGGERS, BLOCKS, PRIORITY only | config/routing.md | `# Usage Guide` (intro, unchanged) |
| U2 | docs/guides/USAGE.md:8 | ROUTING-FORMAT-VERSION: 2 | config/routing.md | `# Usage Guide` (intro, unchanged) |
| U3 | docs/guides/USAGE.md:10-15 | Format notes: WHAT, TRIGGERS, BLOCKS, PRIORITY, EXAMPLE meanings and scoring | config/routing.md | `# Usage Guide` (intro, unchanged) |
| U4 | docs/guides/USAGE.md:17-18 | Typing a skill by name always wins; routing is for plain language | config/routing.md | `# Usage Guide` (intro, unchanged) |
| U5 | docs/guides/USAGE.md:24 | mem-search | config/routing.md | `### mem-search` (also in docs/guides/SKILLS.md `## Routing`) |
| U6 | docs/guides/USAGE.md:31 | context-restore | config/routing.md | `### context-restore` (also in docs/guides/SKILLS.md `## Routing`) |
| U7 | docs/guides/USAGE.md:38 | learn-codebase | config/routing.md | `### learn-codebase` (also in docs/guides/SKILLS.md `## Routing`) |
| U8 | docs/guides/USAGE.md:49 | council | config/routing.md | `### council` (also in docs/guides/SKILLS.md `## Routing`) |
| U9 | docs/guides/USAGE.md:60 | brainstorming | config/routing.md | `### brainstorming` (also in docs/guides/SKILLS.md `## Routing`) |
| U10 | docs/guides/USAGE.md:71 | investigate | config/routing.md | `### investigate` (also in docs/guides/SKILLS.md `## Routing`) |
| U11 | docs/guides/USAGE.md:78 | systematic-debugging | config/routing.md | `### systematic-debugging` (also in docs/guides/SKILLS.md `## Routing`) |
| U12 | docs/guides/USAGE.md:89 | qa | config/routing.md | `### qa` (also in docs/guides/SKILLS.md `## Routing`) |
| U13 | docs/guides/USAGE.md:96 | review | config/routing.md | `### review` (also in docs/guides/SKILLS.md `## Routing`) |
| U14 | docs/guides/USAGE.md:103 | ship | config/routing.md | `### ship` (also in docs/guides/SKILLS.md `## Routing`) |
| U15 | docs/guides/USAGE.md:114 | design | config/routing.md | `### design` (also in docs/guides/SKILLS.md `## Routing`) |
| U16 | docs/guides/USAGE.md:121 | brand-system | config/routing.md | `### brand-system` (also in docs/guides/SKILLS.md `## Routing`) |
| U17 | docs/guides/USAGE.md:128 | assets | config/routing.md | `### assets` (also in docs/guides/SKILLS.md `## Routing`) |
| U18 | docs/guides/USAGE.md:135 | design-gate | config/routing.md | `### design-gate` (also in docs/guides/SKILLS.md `## Routing`) |
| U19 | docs/guides/USAGE.md:142 | ui-ux-pro-max | config/routing.md | `### ui-ux-pro-max` (also in docs/guides/SKILLS.md `## Routing`) |
| U20 | docs/guides/USAGE.md:149 | 21st.dev | config/routing.md | `### 21st.dev` (also in docs/guides/SKILLS.md `## Routing`) |
| U21 | docs/guides/USAGE.md:156 | impeccable (audit) | config/routing.md | `### impeccable (audit)` (also in docs/guides/SKILLS.md `## Routing`) |
| U22 | docs/guides/USAGE.md:163 | impeccable (polish) | config/routing.md | `### impeccable (polish)` (also in docs/guides/SKILLS.md `## Routing`) |
| U23 | docs/guides/USAGE.md:170 | impeccable (critique) | config/routing.md | `### impeccable (critique)` (also in docs/guides/SKILLS.md `## Routing`) |
| U24 | docs/guides/USAGE.md:177 | animate | config/routing.md | `### animate` (also in docs/guides/SKILLS.md `## Routing`) |
| U25 | docs/guides/USAGE.md:184 | transitions-dev | config/routing.md | `### transitions-dev` (also in docs/guides/SKILLS.md `## Routing`) |
| U26 | docs/guides/USAGE.md:191 | transitions-polish | config/routing.md | `### transitions-polish` (also in docs/guides/SKILLS.md `## Routing`) |
| U27 | docs/guides/USAGE.md:198 | gsap (scroll, timeline, plugins) | config/routing.md | `### gsap (scroll, timeline, plugins)` (also in docs/guides/SKILLS.md `## Routing`) |
| U28 | docs/guides/USAGE.md:205 | apple-design | config/routing.md | `### apple-design` (also in docs/guides/SKILLS.md `## Routing`) |
| U29 | docs/guides/USAGE.md:212 | review-animations / improve-animations / find-animation-opportunities | config/routing.md | `### review-animations / improve-animations / find-animation-opportunities` (also in docs/guides/SKILLS.md `## Routing`) |
| U30 | docs/guides/USAGE.md:219 | animation-vocabulary | config/routing.md | `### animation-vocabulary` (also in docs/guides/SKILLS.md `## Routing`) |
| U31 | docs/guides/USAGE.md:226 | design-motion-principles | config/routing.md | `### design-motion-principles` (also in docs/guides/SKILLS.md `## Routing`) |
| U32 | docs/guides/USAGE.md:233 | design-dna | config/routing.md | `### design-dna` (also in docs/guides/SKILLS.md `## Routing`) |
| U33 | docs/guides/USAGE.md:240 | threejs | config/routing.md | `### threejs` (also in docs/guides/SKILLS.md `## Routing`) |
| U34 | docs/guides/USAGE.md:247 | high-end-visual-design | config/routing.md | `### high-end-visual-design` (also in docs/guides/SKILLS.md `## Routing`) |
| U35 | docs/guides/USAGE.md:254 | minimalist-ui | config/routing.md | `### minimalist-ui` (also in docs/guides/SKILLS.md `## Routing`) |
| U36 | docs/guides/USAGE.md:261 | industrial-brutalist-ui | config/routing.md | `### industrial-brutalist-ui` (also in docs/guides/SKILLS.md `## Routing`) |
| U37 | docs/guides/USAGE.md:272 | two-stage-review | config/routing.md | `### two-stage-review` (also in docs/guides/SKILLS.md `## Routing`) |
| U38 | docs/guides/USAGE.md:279 | code-review (high effort) | config/routing.md | `### code-review (high effort)` (also in docs/guides/SKILLS.md `## Routing`) |
| U39 | docs/guides/USAGE.md:290 | ralph-loop | config/routing.md | `### ralph-loop` (also in docs/guides/SKILLS.md `## Routing`) |
| U40 | docs/guides/USAGE.md:301 | go-review | config/routing.md | `### go-review` (also in docs/guides/SKILLS.md `## Routing`) |
| U41 | docs/guides/USAGE.md:308 | python-review | config/routing.md | `### python-review` (also in docs/guides/SKILLS.md `## Routing`) |
| U42 | docs/guides/USAGE.md:315 | rust-review | config/routing.md | `### rust-review` (also in docs/guides/SKILLS.md `## Routing`) |
| U43 | docs/guides/USAGE.md:322 | fastapi-review | config/routing.md | `### fastapi-review` (also in docs/guides/SKILLS.md `## Routing`) |
| U44 | docs/guides/USAGE.md:329 | build-fix | config/routing.md | `### build-fix` (also in docs/guides/SKILLS.md `## Routing`) |
| U45 | docs/guides/USAGE.md:336 | go-build | config/routing.md | `### go-build` (also in docs/guides/SKILLS.md `## Routing`) |
| U46 | docs/guides/USAGE.md:343 | rust-build | config/routing.md | `### rust-build` (also in docs/guides/SKILLS.md `## Routing`) |
| U47 | docs/guides/USAGE.md:350 | gradle-build | config/routing.md | `### gradle-build` (also in docs/guides/SKILLS.md `## Routing`) |
| U48 | docs/guides/USAGE.md:361 | tdd-workflow | config/routing.md | `### tdd-workflow` (also in docs/guides/SKILLS.md `## Routing`) |
| U49 | docs/guides/USAGE.md:368 | e2e-testing | config/routing.md | `### e2e-testing` (also in docs/guides/SKILLS.md `## Routing`) |
| U50 | docs/guides/USAGE.md:375 | test-coverage | config/routing.md | `### test-coverage` (also in docs/guides/SKILLS.md `## Routing`) |
| U51 | docs/guides/USAGE.md:386 | multi-plan | config/routing.md | `### multi-plan` (also in docs/guides/SKILLS.md `## Routing`) |
| U52 | docs/guides/USAGE.md:393 | multi-execute | config/routing.md | `### multi-execute` (also in docs/guides/SKILLS.md `## Routing`) |
| U53 | docs/guides/USAGE.md:400 | multi-workflow | config/routing.md | `### multi-workflow` (also in docs/guides/SKILLS.md `## Routing`) |
| U54 | docs/guides/USAGE.md:407 | multi-backend | config/routing.md | `### multi-backend` (also in docs/guides/SKILLS.md `## Routing`) |
| U55 | docs/guides/USAGE.md:414 | multi-frontend | config/routing.md | `### multi-frontend` (also in docs/guides/SKILLS.md `## Routing`) |
| U56 | docs/guides/USAGE.md:425 | search-first | config/routing.md | `### search-first` (also in docs/guides/SKILLS.md `## Routing`) |
| U57 | docs/guides/USAGE.md:432 | deep-research | config/routing.md | `### deep-research` (also in docs/guides/SKILLS.md `## Routing`) |
| U58 | docs/guides/USAGE.md:439 | iterative-retrieval | config/routing.md | `### iterative-retrieval` (also in docs/guides/SKILLS.md `## Routing`) |
| U59 | docs/guides/USAGE.md:450 | security-scan | config/routing.md | `### security-scan` (also in docs/guides/SKILLS.md `## Routing`) |
| U60 | docs/guides/USAGE.md:461 | cro | config/routing.md | `### cro` (also in docs/guides/SKILLS.md `## Routing`) |
| U61 | docs/guides/USAGE.md:468 | pricing | config/routing.md | `### pricing` (also in docs/guides/SKILLS.md `## Routing`) |
| U62 | docs/guides/USAGE.md:475 | signup / onboarding / paywalls / popups | config/routing.md | `### signup / onboarding / paywalls / popups` (also in docs/guides/SKILLS.md `## Routing`) |
| U63 | docs/guides/USAGE.md:482 | marketing-psychology | config/routing.md | `### marketing-psychology` (also in docs/guides/SKILLS.md `## Routing`) |
| U64 | docs/guides/USAGE.md:489 | offers / launch / lead-magnets / customer-research | config/routing.md | `### offers / launch / lead-magnets / customer-research` (also in docs/guides/SKILLS.md `## Routing`) |
| U65 | docs/guides/USAGE.md:500 | /write | config/routing.md | `### /write` (also in docs/guides/SKILLS.md `## Routing`) |
| U66 | docs/guides/USAGE.md:507 | /polish | config/routing.md | `### /polish` (also in docs/guides/SKILLS.md `## Routing`) |
| U67 | docs/guides/USAGE.md:514 | /academic | config/routing.md | `### /academic` (also in docs/guides/SKILLS.md `## Routing`) |
| U68 | docs/guides/USAGE.md:521 | project-finder | config/routing.md | `### project-finder` (also in docs/guides/SKILLS.md `## Routing`) |
| U69 | docs/guides/USAGE.md:528 | humanizer | config/routing.md | `### humanizer` (also in docs/guides/SKILLS.md `## Routing`) |
| U70 | docs/guides/USAGE.md:535 | update-docs | config/routing.md | `### update-docs` (also in docs/guides/SKILLS.md `## Routing`) |
| U71 | docs/guides/USAGE.md:542 | plan-prd | config/routing.md | `### plan-prd` (also in docs/guides/SKILLS.md `## Routing`) |
| U72 | docs/guides/USAGE.md:549 | article-writing | config/routing.md | `### article-writing` (also in docs/guides/SKILLS.md `## Routing`) |
| U73 | docs/guides/USAGE.md:560 | seo-ops | config/routing.md | `### seo-ops` (also in docs/guides/SKILLS.md `## Routing`) |
| U74 | docs/guides/USAGE.md:567 | content-ops | config/routing.md | `### content-ops` (also in docs/guides/SKILLS.md `## Routing`) |
| U75 | docs/guides/USAGE.md:574 | anti-ai-writing | config/routing.md | `### anti-ai-writing` (also in docs/guides/SKILLS.md `## Routing`) |
| U76 | docs/guides/USAGE.md:581 | voice-dna | config/routing.md | `### voice-dna` (also in docs/guides/SKILLS.md `## Routing`) |
| U77 | docs/guides/USAGE.md:588 | nano-banana | config/routing.md | `### nano-banana` (also in docs/guides/SKILLS.md `## Routing`) |
| U78 | docs/guides/USAGE.md:595 | video-to-website | config/routing.md | `### video-to-website` (also in docs/guides/SKILLS.md `## Routing`) |
| U79 | docs/guides/USAGE.md:602 | business-analyzer | config/routing.md | `### business-analyzer` (also in docs/guides/SKILLS.md `## Routing`) |
| U80 | docs/guides/USAGE.md:613 | hexagonal-architecture | config/routing.md | `### hexagonal-architecture` (also in docs/guides/SKILLS.md `## Routing`) |
| U81 | docs/guides/USAGE.md:620 | architecture-decision-records | config/routing.md | `### architecture-decision-records` (also in docs/guides/SKILLS.md `## Routing`) |
| U82 | docs/guides/USAGE.md:627 | codebase-onboarding | config/routing.md | `### codebase-onboarding` (also in docs/guides/SKILLS.md `## Routing`) |
| U83 | docs/guides/USAGE.md:634 | production-audit | config/routing.md | `### production-audit` (also in docs/guides/SKILLS.md `## Routing`) |
| U84 | docs/guides/USAGE.md:645 | benchmark | config/routing.md | `### benchmark` (also in docs/guides/SKILLS.md `## Routing`) |
| U85 | docs/guides/USAGE.md:656 | pr | config/routing.md | `### pr` (also in docs/guides/SKILLS.md `## Routing`) |
| U86 | docs/guides/USAGE.md:663 | review-pr | config/routing.md | `### review-pr` (also in docs/guides/SKILLS.md `## Routing`) |
| U87 | docs/guides/USAGE.md:674 | quality-gate | config/routing.md | `### quality-gate` (also in docs/guides/SKILLS.md `## Routing`) |
| U88 | docs/guides/USAGE.md:681 | refactor-clean | config/routing.md | `### refactor-clean` (also in docs/guides/SKILLS.md `## Routing`) |
| U89 | docs/guides/USAGE.md:688 | checkpoint | config/routing.md | `### checkpoint` (also in docs/guides/SKILLS.md `## Routing`) |
| U90 | docs/guides/USAGE.md:699 | skill-create | config/routing.md | `### skill-create` (also in docs/guides/SKILLS.md `## Routing`) |
| U91 | docs/guides/USAGE.md:708-756 | Cheat sheet section | config/routing.md | `## Cheat sheet` (also in docs/guides/DAILY-USE.md `## Pick a skill`) |
| U92 | docs/guides/USAGE.md:757-790 | Reference skills section: use by name, never routed | config/routing.md | `## Reference skills (no routing - use by name)` |
