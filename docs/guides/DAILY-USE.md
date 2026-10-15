# Daily use
Type: how to

This is for you, using this setup day to day. It shows the workflow chain, the `wf` runner commands, how to keep this repo and `~/.claude` in sync, and how to pick a skill.

## The workflow chain

The full rules are in [claude-home/CLAUDE.md](../../claude-home/CLAUDE.md) under `## Workflow`, and the skill table is in [claude-home/rules/skill-map.md](../../claude-home/rules/skill-map.md). This is the short version for a person.

1. Start a session in a repo: run `/scope` with no argument. It tells you where things stand. If the repo has no `AGENTS.md`, run `/audit` first. If it has no `docs/scope/`, run `/scope` before any feature work.
2. A big choice is not made yet (stack, data model, provider, page design, how a feature behaves): run `/architect`. It writes a spec. Never decide it inside a build.
3. Build a scoped feature or fix: run `/develop`.
4. What happens next depends on the tier in the scope header:
   - Prototype: stop after `/develop`.
   - Alpha: `/check verify`.
   - Beta: `/check verify`, then `/test`.
   - GA: `/check verify`, `/test`, a review, then `/document`.
5. Then `/sync`, which updates `AGENTS.md`, the scope and any stale specs. Claude runs the rest of the chain itself. It stops only on a failure, a decision it owes you, or a step that pushes, merges, posts or bills.
6. A bug, a failing test or wrong behavior: run `/debug`.
7. Handoffs. A feature still open and the context is full: `/rollover`, then you type `/clear`, then `/resume-from-clear`. A feature closed or a new task: `/save-and-clear`, then you type `/clear`.
8. UI changed: `/check verify` plus `design-gate`. A new design or a restyle: the `design` skill.

Which reviewer to use is in `## Review Rules` of the same CLAUDE.md file. Never run `/review` and `/review-stack` on the same diff.

## Run the runner

`wf` is the workflow runner. It builds the queued features of your repos while you are away, and asks you through your phone when it needs a decision. The rows are listed from the one command you type down to the internals.

| Command | What it does | Spec |
|---|---|---|
| `wf [-y] [--jobs N]` | The one command you type. One confirm screen, then the report, the staged setup swap into `~/.claude`, retakes, builds of every trusted repo, and real checks beside them. A running run is skipped, never stopped. The commands below are its internals. | 0020 |
| `wf run [repo] [--jobs N]` | Builds the queued `· auto` features of one repo, or of every trusted repo when you give no name. With no name it starts one `wf run <repo> -y` child per repo with work, side by side, and `--jobs` caps how many run at once. Locks, run records and `queue.json` live in `$XDG_STATE_HOME/wf`, else `~/.local/state/wf`. | 0011, 0017 |
| `wf queue [repo]` | Read only plan: what is queued, parked, open, and which questions are answered. | 0011 |
| `wf unpark <repo> [feature]` | Clears parks and open questions so the next `wf run` starts them fresh. | 0011 |
| `wf allow <repo>` | Adds the repo to the trust list. `wf run` refuses an `untrusted` repo (exit 5) when it is not in `$XDG_CONFIG_HOME/wf/allowed.json`, else `~/.config/wf/allowed.json`. | 0008 |
| `wf allow-writes <repo> <path>` | Gives standing write permission to that repo's `wf run` calls. It is kept in `~/.config/wf/allow.json`. A never writable set (secrets, live `~/.claude` settings, hooks, rules, PATH dirs, git config) always wins. Refused under `WF_RUN`. An `AGENTS.md` `- allow writes:` line is ignored now. | 0021 (AC-7) |
| `wf finish [target] [-y]` | Runs the ` · live` waits-on-you boxes (cp into `~/.claude`, `bin/install.sh`, e2e, probes) after one Enter, keeps `autoMode`, ticks them, records `verify.md` and commits. Never from an unattended call. The exception: a `wf run` that reaches a live copy box into `rules/`, `agents/`, `commands/` or `skills/` asks on the phone and runs exactly the approved copies itself, pinned by source hash. | 0019, 0041 |
| `wf report [--seen\|--hook]` | Shows the last wf run's morning report. It is also sent to the phone at the end of every run. `--hook` is the `settings.json` SessionStart form and prints only an unseen report. `--seen` stops showing it. `report.txt` lives in the wf state folder. | 0018 |
| `wf ntfy init\|codes\|test` | Phone pings for `wf run` decisions. Config is `~/.config/wf/ntfy.json` (0600). `wf run` refuses without it. | 0005 |
| `wf telegram init\|test` | Your own Telegram bot instead of ntfy. `init` asks for the BotFather token (hidden), binds your chat with a `/start` code and writes `~/.config/wf/telegram.json` (0600). `test` sends one question. | 0029 |
| `wf telegram fetch\|timer on\|off` | Keeps Telegram answers while wf is off. `fetch` saves new updates once into the update log a run reads (same lock as a run). `timer on` writes and enables the `wf-telegram-fetch` user timer (every 5 minutes). `timer off` removes it. | 0039 |
| `wf questions` | Read only: every open question, its options (first one recommended) and links. Bare `wf` lists them first and lets you answer each at the keyboard. Enter skips one. `-y` only lists. | 0039 |
| `wf auto on [repos]\|off [now]\|status\|start\|wait\|take <repos>\|release <repos>\|hook\|bar` | Autonomous mode, one chat per session folder. `/auto on [repos]` (you only, refused under `WF_RUN`) turns on this folder's chat for its own repo plus the ones you name. `start` runs `wf -y --repos ...` as the chat's own `wf-auto-<8 hex>` user unit, and the session relays its questions. `take` and `release` move allowed repos into or out of this chat (Claude may run them, never from another chat). `off` lets the running build finish its current features. `off now` stops the unit. `hook` is the SessionStart and UserPromptSubmit hook. `bar` wraps jjstack's status line. State is in `<state>/auto.json` (version 2, chats keyed by folder). | 0030, 0046 |

### Phone channel

Make the bot with BotFather, then run `wf telegram init` (spec 0029). With `telegram.json` present, `wf run` uses only Telegram. An invalid file refuses `no_telegram` and never falls back to ntfy. Without the file, ntfy works as before. Only your chat id can answer. A plain message gets a one line hint.

## Keep the repo and ~/.claude in sync

Use the `/claude-config` skill (spec 0048, skill file [claude-home/skills/claude-config/SKILL.md](../../claude-home/skills/claude-config/SKILL.md)). It drives `bin/claude-config.py`. The tool never asks anything itself. The skill asks you, and nothing changes a skill without your yes on that skill.

- `/claude-config drift` (also what you get with no argument): shows where the repo and `~/.claude` differ, grouped as live only, missing live, and differs. Exit 1 means drift was found, not that the tool failed. It changes nothing.
- `/claude-config sync`: copies `~/.claude` into the repo, then shows `git status --short`. It does not commit unless you ask.
- `/claude-config install`: runs `--dry-run` first and shows it. It runs for real only after your yes.
- `/claude-config update`: lists every downloaded skill whose upstream moved, with changed files and line counts. You answer yes or no per entry. On a conflict nothing is installed. You get the files with `<<<<<<<` markers under `~/.claude/state/claude-config-conflicts/<entry>/`, you fix them, and the skill reruns the entry with `--resolved`. Entries marked "update by hand, not checked" are never applied by the tool.

Before every commit in this repo, run `bin/sync.sh` and then look at `git diff`. Files copied from `~/.claude` are overwritten by the next sync, so edit those in `~/.claude`.

The drift check runs only when you ask for it, never at session start. At session start a hook prints one line, "claude-config: upstream not checked for N days, run /claude-config update". It appears when 7 or more days have passed since the last `update --plan`, or when the state file is missing. It only counts days.

The layout of the repo, the manifest and the patches are in [the architecture notes](../architecture.md). Setting up a machine is in [SETUP.md](SETUP.md).

## Pick a skill

Typing the skill name always wins. Type `/review` and you get `/review`. The intent router only helps when you describe what you want instead of naming a skill.

The routing table, the one the intent router reads, is [config/routing.md](../../config/routing.md). The same table is shown in [SKILLS.md](SKILLS.md) under `## Routing`. After you edit it or a skill's triggers, run `python3 scripts/check-routing.py`.

The cheat sheet from the old USAGE guide is kept here, and also in `config/routing.md` under `## Cheat sheet`.

| Scenario | Route | Say something like |
|----------|-------|--------------------|
| Bug with 3+ possible causes | `/council` then `/investigate` | "3 possible causes for this crash, help me decide which to chase" |
| New page/screen | taste skill -> `/impeccable shape` -> build -> `/impeccable audit` -> `/impeccable polish` | "design a new pricing page from scratch" |
| Full design pipeline | `/design` (or describe it) | "/design a dashboard - reuse project context, audit before showing me" |
| Client's monthly retainer cycle | `/monthly-ops <client>` | "run this month's SEO/content/GBP ops for <client>" |
| Match a reference design | `design-dna` (before ui-ux-pro-max) | "make it look like this screenshot, pull the tokens out" |
| Add motion to something | `animate` | "animate this SVG logo, draw the paths in on load" |
| Plain CSS transition | `transitions-dev` | "make the modal open smoothly and the accordion expand" |
| Scroll-driven / pinned / parallax | `gsap-scrolltrigger` (+ `gsap-react`) | "pin the hero and scrub the timeline on scroll" |
| Gesture, spring, drag, sheet | `apple-design` | "the bottom sheet should be draggable and feel like iOS" |
| Animation feels wrong | `review-animations` (diff) / `improve-animations` (whole app) | "audit the motion across this app, prioritized list" |
| Timing/easing inconsistent | `transitions-polish` | "durations are hardcoded everywhere, align to a token scale" |
| Don't know what the effect is called | `animation-vocabulary` | "what's it called when the list rubber-bands?" |
| Motion report with looping demos | `design-motion-principles` audit mode | "generate the HTML motion report for the client" |
| 3D / WebGL / shaders | `threejs-*` (+ gsap if scroll-linked) | "load this GLTF and add bloom postprocessing" |
| Commit / PR body / issue / docs | `/write` | "write the PR body for this branch" |
| Text sounds like AI | `/polish` | "this reads like ChatGPT, polish it" |
| Thesis / paper / lit review | `/academic` | "write the methodology section in APA" |
| Need a thesis topic | `project-finder` | "field is open, help me find a project" |
| Marketing page not converting | `cro` (+ `pricing` / `signup` / `paywalls`) | "the pricing page isn't converting, what's wrong?" |
| Why would someone buy this | `marketing-psychology` | "what principle should this pricing page lean on?" |
| Code works but messy | `/smart-simplify` | "this works but it's messy, simplify it" |
| Dead code / unused symbols | `/refactor-clean` | "remove the unused functions in this file" |
| Second opinion on architecture | `/council` | "which is better here, monolith or microservices?" |
| Starting a long session | `/context-restore` or `/learn-codebase` | "continue where we left off" / "prime this codebase" |
| Shipping a PR | `/review` -> fix -> `/ship` | "review my diff, then ship it" |
| Reviewing someone else's PR | `/review-pr` | "review this PR: <url>" |
| Full deploy pipeline | `/land-and-deploy` | "land and deploy this" |
| Build / compile error | `/build-fix` (or `/go-build`, `/rust-build`, `/gradle-build`) | "the build is broken, fix it" |
| Go code review | `/go-review` | "go code review on this file" |
| Python code review | `/python-review` | "review my python" |
| Rust code review | `/rust-review` | "rust review, check the unsafe block" |
| TDD from scratch | `/tdd-workflow` | "build this with TDD, tests first" |
| E2E test with Playwright | `/e2e-testing` | "write a Playwright e2e for the signup flow" |
| Coverage gaps | `/test-coverage` | "what code isn't covered by tests?" |
| Security vulnerabilities | `/security-scan` | "scan this repo for vulnerabilities" |
| Tasks that can run in parallel | `/multi-plan` then `/multi-execute` | "these are independent, fan out across agents" |
| Research before coding | `/search-first` | "look up how X works before we code against it" |
| Write an ADR | `/architecture-decision-records` | "write an ADR for this decision" |
| Production readiness check | `/production-audit` | "is this production ready?" |
| Write a PRD | `/plan-prd` | "spec this out as a PRD" |
| Create a reusable skill | `/skill-create` | "extract this as a skill" |
| New to this codebase | `/codebase-onboarding` | "explain how this project is organized" |

## Language rules on demand

The ECC language rules are not loaded on their own. To use one in a project, add one line to that project's `CLAUDE.md`, for example:

```
@~/.claude/rules/ecc/typescript/index.md
```

The languages you can use are `typescript`, `python`, `golang`, `rust`, `java`, `web` and `common`.
