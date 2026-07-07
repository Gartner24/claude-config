# Usage Guide

Decision guide for skill routing. The intent-router reads only the `TRIGGERS`, `BLOCKS`,
and `PRIORITY` fields when scoring a prompt. The `WHAT` and `EXAMPLE` lines are human-facing
- they explain what each skill does and show a prompt that would route to it - and the router
ignores them.

ROUTING-FORMAT-VERSION: 2

**How a block reads:**
- **WHAT** - one line on what the skill does, so you know why it fires.
- **TRIGGERS** - phrases that, if found in your prompt (substring, case-insensitive), score the skill.
- **BLOCKS** - conditions that disqualify the skill even if a trigger matched.
- **PRIORITY** - tiebreaker weight (higher wins); score = trigger_matches x priority.
- **EXAMPLE** - a real prompt that routes here. Phrase your request like this to hit the skill on purpose.

You never have to rely on routing - typing the skill by name (`/council`, `/investigate`)
always wins. Routing is for when you describe the task in plain language instead.

---

## Memory and context

### mem-search
WHAT: Searches previous sessions for how a problem was solved before you redo the work.
TRIGGERS: did we solve this, did we do this before, how did we, remember when, previously, last time, past session, have we already
BLOCKS: nothing - memory check should always fire when these phrases appear
PRIORITY: 10 - always check memory before starting any non-trivial task
EXAMPLE: "did we already fix the AX88179 USB dongle not creating an interface?"

### context-restore
WHAT: Reloads what you were working on so a new session picks up mid-task.
TRIGGERS: resume, continue where, pick up where, last session, where were we, restore context, I was working on
BLOCKS: nothing
PRIORITY: 9
EXAMPLE: "let's continue where we left off on the claude-config cleanup"

### learn-codebase
WHAT: Reads an unfamiliar repo end to end and builds a working mental model before you change anything.
TRIGGERS: learn this codebase, prime the codebase, get up to speed, read all the files, new codebase, unfamiliar repo
BLOCKS: already primed this session
PRIORITY: 8
EXAMPLE: "prime the codebase, I just cloned this repo and need to get up to speed"

---

## Hard decisions

### council
WHAT: Runs a multi-perspective debate with cross-examination on a hard tradeoff, then a compact verdict.
TRIGGERS: should I, which is better, tradeoff, tradeoffs, architecture choice, monolith, microservice, which database, which library, build vs buy, second opinion, not sure which approach, multiple options, launch decision, risk, 3 possible causes, can't decide, help me decide, debate
BLOCKS: simple questions with one clear answer, implementation tasks, bug fixes with obvious cause
PRIORITY: 9
EXAMPLE: "should I use Postgres or SQLite for this, I can't decide - give me a second opinion"

---

## Planning

### brainstorming
WHAT: Explores intent and requirements before any code, so you build the right thing.
TRIGGERS: new feature, let's build, I want to add, design this, let's make, create a, I'm thinking of building, plan this feature, explore this idea, before we start
BLOCKS: already have a plan, executing existing plan, bug fix
PRIORITY: 8
EXAMPLE: "I'm thinking of building a status dashboard for my home server - let's explore it first"

---

## Debugging

### investigate
WHAT: Roots out the cause of a bug or error by reading the code first, not guessing.
TRIGGERS: bug, error, crash, broken, not working, failing, unexpected behavior, wrong output, exception, traceback, it broke, why is this, what's wrong, debug, fix this error
BLOCKS: nothing
PRIORITY: 9
EXAMPLE: "the network interface isn't coming up after the kernel update - why is this failing?"

### systematic-debugging
WHAT: Disciplined hypothesis-and-test loop for bugs that resist a quick read.
TRIGGERS: complex bug, hard to debug, need a systematic approach, methodical debugging
BLOCKS: simple bugs with obvious cause
PRIORITY: 8
EXAMPLE: "this is a complex bug I've chased for hours - I need a systematic approach"

---

## Everyday coding

### qa
WHAT: Actually runs the app/feature to confirm it works, then fixes what's broken.
TRIGGERS: does this work, test this, verify it works, check if it works, run the app, does it work, make sure it works, test the feature, test it manually
BLOCKS: writing tests, code review
PRIORITY: 8
EXAMPLE: "run the app and make sure the login flow actually works"

### review
WHAT: Pre-landing review of your working diff for correctness and cleanup before merge.
TRIGGERS: review this, pre-landing, before I merge, check this PR, code review, review my changes, check my diff, is this ready to merge
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "review my changes before I merge this"

### ship
WHAT: Full ship flow - test, review diff, bump version, changelog, commit, push, open PR.
TRIGGERS: ship it, push this, create a PR, commit and push, submit PR, deploy, send it
BLOCKS: not committed yet, failing tests
PRIORITY: 8
EXAMPLE: "ship it - commit, push, and open the PR"

---

## UI / frontend

### ui-ux-pro-max
WHAT: Locks design direction (style + palette + fonts + stack) before anything is built. Step 1 of the design pipeline.
TRIGGERS: new design, redesign, design this, design a page, design a component, from scratch, what style, pick a style, choose a palette, font pairing, pick fonts, choose a stack, design direction, make this look like, style exploration, new page, new section
BLOCKS: nothing
PRIORITY: 9 - lock direction (style + palette + fonts + stack) before anything is built; chain into 21st.dev
EXAMPLE: "redesign the landing page - help me pick a style, palette, and font pairing first"

### 21st.dev
WHAT: Sources real shadcn/Tailwind components via the magic MCP (/ui) instead of hand-rolling. Step 2 of the pipeline.
TRIGGERS: build the UI, build this, scaffold, implement the design, need a navbar, need a hero, need a pricing section, need a table, need a modal, need a card, need a component, find a component, real component, production component, shadcn, block, registry
BLOCKS: stack is not React/Next + Tailwind + shadcn/Radix
PRIORITY: 8 - chain after ui-ux-pro-max; source real components via /ui (magic MCP) instead of hand-rolling
EXAMPLE: "build the pricing section - find a real shadcn component for it"

### impeccable (audit)
WHAT: Audits a UI for accessibility, anti-patterns, responsive and performance issues.
TRIGGERS: audit the UI, check the design, accessibility issues, anti-patterns, a11y, performance issues in UI, responsive check, design quality
BLOCKS: motion specifically
PRIORITY: 8
EXAMPLE: "audit the UI for a11y and responsive issues before I show the client"

### impeccable (polish)
WHAT: Final tightening pass on a near-done UI before shipping.
TRIGGERS: polish this, final pass, ready to ship, clean up the UI, tighten the design, before shipping UI
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "give the dashboard a final polish pass before we ship it"

### impeccable (critique)
WHAT: UX critique of hierarchy, information architecture, and cognitive load.
TRIGGERS: UX review, is the hierarchy clear, does this feel right, UX feedback, information architecture, cognitive load
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "UX review this settings page - is the hierarchy clear or is it overwhelming?"

### design-motion-principles
WHAT: Builds or audits UI motion with the Emil Kowalski lens; catches AI-slop animation.
TRIGGERS: animation, motion, transition, animate this, feels wrong motion, too fast, too slow, spring, easing, framer motion, CSS animation, motion design, this animation, audit animations, motion audit, movement, feels janky, bounce, hover effect feels
BLOCKS: static UI with no animation
PRIORITY: 8
EXAMPLE: "this hover animation feels janky and too fast - audit the motion"

### high-end-visual-design
WHAT: Premium, expensive-feeling aesthetic direction (Stripe/Linear/Vercel calm-and-spacious).
TRIGGERS: premium, polished, high-end, Stripe feel, Linear feel, Vercel feel, calm UI, expensive looking, soft contrast, whitespace heavy
BLOCKS: nothing
PRIORITY: 6
EXAMPLE: "make this landing page feel high-end and expensive, like Linear"

### minimalist-ui
WHAT: Clean editorial minimalism - warm monochrome, typographic contrast, no gradients or heavy shadows.
TRIGGERS: minimal, clean, Notion feel, editorial, restrained, simple layout
BLOCKS: nothing
PRIORITY: 6
EXAMPLE: "I want a minimal, editorial layout - clean and restrained like Notion"

### industrial-brutalist-ui
WHAT: Raw, experimental, high-contrast brutalist direction with bold Swiss type.
TRIGGERS: brutalist, experimental, raw, Swiss type, sharp contrast, bold layout
BLOCKS: nothing
PRIORITY: 6
EXAMPLE: "go brutalist on this - raw, sharp contrast, bold Swiss type"

---

## Code review

### two-stage-review
WHAT: Deeper two-pass review for large or complex diffs.
TRIGGERS: large diff, big PR, many files changed, complex review, thorough review, deep review
BLOCKS: small change
PRIORITY: 7
EXAMPLE: "this is a big PR touching many files - do a thorough two-stage review"

### code-review (high effort)
WHAT: Security-sensitive, high-effort review for production or risky changes.
TRIGGERS: security review, important PR, sensitive change, production code, careful review, security-sensitive
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "careful security review on this auth change before it goes to production"

---

## Autonomous

### ralph-loop
WHAT: Keeps Claude running on a task autonomously without manual re-prompting.
TRIGGERS: keep going, run autonomously, don't stop, continue without me, run this in the background, autonomous, loop on this, keep running
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "keep going autonomously until all the tests pass, don't stop to ask me"

---

## Language review and build

### go-review
WHAT: Idiomatic Go review - concurrency, error handling, interfaces.
TRIGGERS: review this go, go code review, review my go, check this go file, go-specific review
BLOCKS: non-go code
PRIORITY: 8
EXAMPLE: "go code review on this - check the goroutine and error handling"

### python-review
WHAT: Python review - PEP 8, idioms, typing, security.
TRIGGERS: review this python, python code review, review my python, check this python
BLOCKS: non-python code
PRIORITY: 8
EXAMPLE: "review my python - check typing and PEP 8 compliance"

### rust-review
WHAT: Rust review - ownership, lifetimes, unsafe usage, idiomatic patterns.
TRIGGERS: review this rust, rust code review, review my rust, check this rust, unsafe rust
BLOCKS: non-rust code
PRIORITY: 8
EXAMPLE: "rust code review - I used some unsafe here, check it's sound"

### fastapi-review
WHAT: FastAPI-specific review of routes, dependencies, and schemas.
TRIGGERS: review this fastapi, fastapi code review, review my endpoint, check this api route
BLOCKS: non-fastapi code
PRIORITY: 8
EXAMPLE: "review my endpoint - check the dependency injection and Pydantic schema"

### build-fix
WHAT: Detects the build system and fixes build/type errors with minimal changes.
TRIGGERS: build error, build failed, compilation error, won't compile, can't build, fix the build, build is broken, linker error
BLOCKS: runtime errors
PRIORITY: 9
EXAMPLE: "the build is broken with a bunch of type errors - fix it"

### go-build
WHAT: Resolves Go build, vet, and module errors.
TRIGGERS: go build error, go compilation error, go module error, go import error
BLOCKS: nothing
PRIORITY: 9
EXAMPLE: "go build is failing on an import cycle - fix it"

### rust-build
WHAT: Resolves cargo build, borrow checker, and lifetime errors.
TRIGGERS: rust build error, cargo error, rust compilation, borrow checker error, lifetime error
BLOCKS: nothing
PRIORITY: 9
EXAMPLE: "cargo build fails with a borrow checker error I can't get past"

### gradle-build
WHAT: Resolves Gradle/Maven/Java/Spring Boot build errors.
TRIGGERS: gradle build error, gradle failed, maven error, java build error, spring boot build
BLOCKS: nothing
PRIORITY: 9
EXAMPLE: "the gradle build failed on a dependency conflict - fix it"

---

## Testing

### tdd-workflow
WHAT: Enforces write-test-first red/green/refactor for new code.
TRIGGERS: TDD, test driven, write tests first, red green refactor, test first, unit test workflow
BLOCKS: adding tests to existing code
PRIORITY: 8
EXAMPLE: "build this parser with TDD - write the tests first"

### e2e-testing
WHAT: Playwright end-to-end tests for critical user flows.
TRIGGERS: e2e test, end to end test, playwright, browser test, user flow test, integration test full stack
BLOCKS: unit tests
PRIORITY: 8
EXAMPLE: "write a Playwright e2e test for the signup user flow"

### test-coverage
WHAT: Finds coverage gaps and the code paths that aren't tested.
TRIGGERS: test coverage, coverage gaps, what is not covered, coverage analysis, missing tests, uncovered code, coverage report
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "show me the coverage gaps - what code isn't tested?"

---

## Multi-agent

### multi-plan
WHAT: Decomposes work into independent tasks for parallel agents.
TRIGGERS: parallel tasks, multi-agent plan, decompose into agents, parallelize this, split into workers, independent tasks, fan out
BLOCKS: sequential single-task work
PRIORITY: 8
EXAMPLE: "these are independent tasks - decompose them so agents can fan out in parallel"

### multi-execute
WHAT: Spawns parallel agents to run an existing multi-agent plan.
TRIGGERS: execute in parallel, run agents in parallel, multi-agent execute, spawn agents for
BLOCKS: no multi-agent plan exists yet
PRIORITY: 7
EXAMPLE: "spawn agents to execute those tasks in parallel"

### multi-workflow
WHAT: Coordinates work across multiple services at once.
TRIGGERS: multi-service workflow, coordinate services, multiple services, full stack agents
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "coordinate a change across the api, worker, and frontend services together"

### multi-backend
WHAT: Parallel agents across multiple backend services.
TRIGGERS: backend agents, multiple backend services, parallel backend work, backend orchestration
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "run parallel backend work across the auth and billing services"

### multi-frontend
WHAT: Parallel agents across multiple frontend tasks.
TRIGGERS: frontend agents, multiple frontend tasks, parallel frontend work, frontend orchestration
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "parallelize these frontend tasks across agents"

---

## Research

### search-first
WHAT: Researches how something works before writing code against it.
TRIGGERS: research before, look this up first, check before coding, understand before implementing, what does X do, how does X work
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "before coding, look up how the 21st.dev magic MCP API actually works"

### deep-research
WHAT: Multi-source web research with cited synthesis.
TRIGGERS: deep research, thorough research, comprehensive research, research this topic, explore this in depth
BLOCKS: simple questions with obvious answers
PRIORITY: 7
EXAMPLE: "do thorough, cited research on local-first sync engines"

### iterative-retrieval
WHAT: Progressively narrows context across retrieval steps.
TRIGGERS: progressively refine, retrieve context iteratively, build up context step by step, narrow down
BLOCKS: nothing
PRIORITY: 6
EXAMPLE: "build up the context step by step, narrowing down to the relevant module"

---

## Security

### security-scan
WHAT: Scans the codebase for vulnerabilities (OWASP, secrets, injection).
TRIGGERS: security scan, vulnerability scan, check for vulnerabilities, security audit, scan for issues, security check
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "run a security scan on this repo for vulnerabilities and leaked secrets"

---

## Docs and writing

### update-docs
WHAT: Syncs README and docs to the current state of the code.
TRIGGERS: update the docs, sync documentation, update readme, docs are outdated, documentation needs updating
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "the docs are outdated - sync the README to the current code"

### plan-prd
WHAT: Writes a product requirements document / spec from an idea.
TRIGGERS: write a PRD, product requirements document, requirements doc, spec this out, write the spec, product spec
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "spec this out as a PRD before we build it"

### article-writing
WHAT: Drafts long-form technical articles or blog posts in a consistent voice.
TRIGGERS: write an article, technical article, write a blog post, write about this, draft an article, technical writing
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "draft a technical blog post about debugging the USB ethernet driver"

---

## Client services (retainer)

### seo-ops
WHAT: Runs the monthly recurring SEO/AEO for a LIVE client site - claude-seo audit, page-2 internal links, GSC language mining, structured-data upkeep, IndexNow re-index.
TRIGGERS: monthly seo, seo ops, recurring seo, seo retainer, aeo ops, re-index, indexnow, page 2 internal links, seo audit for client
BLOCKS: build-time SEO of a brand-new site (that's SEO-GUIDE via /new-site)
PRIORITY: 8
EXAMPLE: "run this month's SEO ops for camisetasdiez - audit + page-2 internal links"

### content-ops
WHAT: Writes site copy + blog content that gets a client FOUND, in their voice, never AI slop (build-time copy or the monthly blog add-on).
TRIGGERS: write content, blog post, website copy, page copy, content ops, topical content, write for client, blog cadence, get found content
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "write this month's 4 blog posts for the plumber - from their real customer questions"

### anti-ai-writing
WHAT: Final de-slop pass on any written content - makes it sound like a specific person, not AI.
TRIGGERS: sounds like ai, de-slop, anti-ai, make it human, generic writing, ai tells, final writing pass
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "this draft reads like AI - run the anti-ai pass"

### voice-dna
WHAT: Builds a reusable voice profile from ~20 real samples so content matches a specific person's voice.
TRIGGERS: voice profile, sound like me, my voice, client voice, voice dna, match my writing
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "build a voice-dna from these 20 posts so content sounds like the client"

---

## Architecture

### hexagonal-architecture
WHAT: Ports-and-adapters / clean architecture structuring and DDD decoupling.
TRIGGERS: hexagonal architecture, ports and adapters, clean architecture, DDD, domain driven design, decouple layers
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "restructure this with ports and adapters to decouple the layers"

### architecture-decision-records
WHAT: Captures a decision as a structured ADR with context and alternatives.
TRIGGERS: ADR, architecture decision record, document this decision, record this architecture choice, write an ADR
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "write an ADR documenting why we chose Postgres over SQLite here"

### codebase-onboarding
WHAT: Produces an onboarding guide - architecture map, entry points, conventions.
TRIGGERS: onboard to this codebase, understand this codebase, explain the structure, how is this project organized
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "explain how this project is organized so I can onboard to it"

### production-audit
WHAT: Production-readiness audit against a checklist before going live.
TRIGGERS: production audit, production readiness, is this production ready, production checklist, ready for prod, pre-production
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "is this production ready? run a production-readiness audit"

---

## Performance

### benchmark
WHAT: Measures performance / latency and detects regressions.
TRIGGERS: benchmark this, performance benchmark, measure performance, how fast is this, perf test, latency benchmark
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "benchmark this function - how fast is it and is there a regression?"

---

## PR workflow

### pr
WHAT: Creates a pull request from your committed work.
TRIGGERS: create a PR, open a PR, make a pull request, submit PR, open pull request
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "open a PR for this branch"

### review-pr
WHAT: Reviews an existing pull request (often someone else's).
TRIGGERS: review this PR, PR review, review pull request, look at this PR, someone else's PR
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "review this PR for me: https://github.com/org/repo/pull/42"

---

## Quality and refactoring

### quality-gate
WHAT: Pre-merge quality check - is the change good enough to land.
TRIGGERS: quality check, quality gate, check quality, is this good enough, pre-merge quality, verify quality
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "run a quality gate - is this good enough to merge?"

### refactor-clean
WHAT: Safely finds and removes dead code and unused symbols, verifying after each removal.
TRIGGERS: dead code, remove unused code, clean up dead code, refactor clean, unused functions, remove unused
BLOCKS: nothing
PRIORITY: 7
EXAMPLE: "find and remove the dead code and unused functions in this module"

### checkpoint
WHAT: Saves a verification checkpoint to mark progress.
TRIGGERS: save checkpoint, checkpoint this, mark progress, save verification state
BLOCKS: nothing
PRIORITY: 6
EXAMPLE: "checkpoint this - mark progress before I try the risky change"

---

## Skill management

### skill-create
WHAT: Turns a repeated workflow (or git history) into a reusable skill.
TRIGGERS: create a skill, generate a skill, new skill, skill from git history, extract this as a skill, make a skill
BLOCKS: nothing
PRIORITY: 8
EXAMPLE: "extract this debugging flow as a reusable skill"

---

## Cheat sheet

| Scenario | Route | Say something like |
|----------|-------|--------------------|
| Bug with 3+ possible causes | `/council` then `/investigate` | "3 possible causes for this crash, help me decide which to chase" |
| New page/screen | taste skill -> `/impeccable shape` -> build -> `/impeccable audit` -> `/impeccable polish` | "design a new pricing page from scratch" |
| Full design pipeline | `/design` (or describe it) | "/design a dashboard - reuse project context, audit before showing me" |
| Client's monthly retainer cycle | `/monthly-ops <client>` | "run this month's SEO/content/GBP ops for camisetasdiez" |
| Animation feels wrong | `/design-motion-principles` audit mode | "this transition feels janky, audit the motion" |
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

---

## Reference skills (no routing - use by name)

These never route automatically. Invoke them by name when you want the pattern reference.

| Skill | When to use |
|-------|------------|
| `golang-patterns` | Go idioms, interfaces, error handling |
| `golang-testing` | Go test patterns, table tests, benchmarks |
| `python-patterns` | Python idioms, dataclasses, typing |
| `python-testing` | pytest, fixtures, parametrize |
| `rust-patterns` | Rust idioms, ownership, traits |
| `rust-testing` | Rust test patterns, cargo test |
| `java-coding-standards` | Java idioms, naming, structure |
| `jpa-patterns` | JPA/Hibernate queries, entities |
| `fastapi-patterns` | FastAPI routes, dependencies, schemas |
| `django-patterns` | Django models, views, ORM |
| `frontend-patterns` | React, Next.js component patterns |
| `backend-patterns` | API, database, caching patterns |
| `nestjs-patterns` | NestJS modules, controllers, DI |
| `nextjs-turbopack` | Next.js Turbopack config and migration |
| `vite-patterns` | Vite config, plugins, HMR |
| `prisma-patterns` | Prisma schema, queries, migrations |
| `postgres-patterns` | PostgreSQL query optimization, indexing |
| `database-migrations` | Migration patterns across ORMs |
| `redis-patterns` | Redis data structures, caching, pub/sub |
| `api-design` | REST API design, pagination, errors |
| `docker-patterns` | Dockerfile, Compose, networking |
| `deployment-patterns` | CI/CD, health checks, rollbacks |
| `coding-standards` | Language-agnostic code quality rules |
| `error-handling` | Error patterns across languages |
| `git-workflow` | Commit format, branch strategy |
| `mcp-server-patterns` | Building MCP servers |
| `api-connector-builder` | Connecting to external APIs |
