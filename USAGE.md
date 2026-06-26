# Usage Guide

Decision guide for skill routing. The intent-router reads TRIGGERS/BLOCKS/PRIORITY fields.
ROUTING-FORMAT-VERSION: 1

---

## Memory and context

### mem-search
TRIGGERS: did we solve this, did we do this before, how did we, remember when, previously, last time, past session, have we already
BLOCKS: nothing - memory check should always fire when these phrases appear
PRIORITY: 10 - always check memory before starting any non-trivial task

### context-restore
TRIGGERS: resume, continue where, pick up where, last session, where were we, restore context, I was working on
BLOCKS: nothing
PRIORITY: 9

### learn-codebase
TRIGGERS: learn this codebase, prime the codebase, get up to speed, read all the files, new codebase, unfamiliar repo
BLOCKS: already primed this session
PRIORITY: 8

---

## Project init

### gsd-new-project
TRIGGERS: new project, start a project, initialize project, fresh project, from scratch, create a roadmap, new repo setup
BLOCKS: existing project, adding a feature, small change
PRIORITY: 9

---

## Hard decisions

### council
TRIGGERS: should I, which is better, tradeoff, tradeoffs, architecture choice, monolith, microservice, which database, which library, build vs buy, second opinion, not sure which approach, multiple options, launch decision, risk, 3 possible causes, can't decide, help me decide, debate
BLOCKS: simple questions with one clear answer, implementation tasks, bug fixes with obvious cause
PRIORITY: 9

---

## Planning

### brainstorming
TRIGGERS: new feature, let's build, I want to add, design this, let's make, create a, I'm thinking of building, plan this feature, explore this idea, before we start
BLOCKS: already have a plan, executing existing plan, bug fix
PRIORITY: 8

### gsd-plan-phase
TRIGGERS: plan this, break this down, create tasks, make a plan, roadmap, phase plan, detailed plan, implementation plan
BLOCKS: new project, ambiguous idea
PRIORITY: 7

### gsd-execute-phase
TRIGGERS: execute the plan, run the plan, start phase, implement phase, do the plan
BLOCKS: no plan exists yet
PRIORITY: 7

---

## Debugging

### investigate
TRIGGERS: bug, error, crash, broken, not working, failing, unexpected behavior, wrong output, exception, traceback, it broke, why is this, what's wrong, debug, fix this error
BLOCKS: nothing
PRIORITY: 9

### systematic-debugging
TRIGGERS: complex bug, hard to debug, need a systematic approach, methodical debugging
BLOCKS: simple bugs with obvious cause
PRIORITY: 8

---

## Everyday coding

### qa
TRIGGERS: does this work, test this, verify it works, check if it works, run the app, does it work, make sure it works, test the feature, test it manually
BLOCKS: writing tests, code review
PRIORITY: 8

### review
TRIGGERS: review this, pre-landing, before I merge, check this PR, code review, review my changes, check my diff, is this ready to merge
BLOCKS: nothing
PRIORITY: 8

### ship
TRIGGERS: ship it, push this, create a PR, commit and push, submit PR, deploy, send it
BLOCKS: not committed yet, failing tests
PRIORITY: 8

---

## UI / frontend

### ui-ux-pro-max
TRIGGERS: new design, redesign, design this, design a page, design a component, from scratch, what style, pick a style, choose a palette, font pairing, pick fonts, choose a stack, design direction, make this look like, style exploration, new page, new section
BLOCKS: nothing
PRIORITY: 9 - lock direction (style + palette + fonts + stack) before anything is built; chain into 21st.dev

### 21st.dev
TRIGGERS: build the UI, build this, scaffold, implement the design, need a navbar, need a hero, need a pricing section, need a table, need a modal, need a card, need a component, find a component, real component, production component, shadcn, block, registry
BLOCKS: stack is not React/Next + Tailwind + shadcn/Radix
PRIORITY: 8 - chain after ui-ux-pro-max; source real components via /ui (magic MCP) instead of hand-rolling

### impeccable (audit)
TRIGGERS: audit the UI, check the design, accessibility issues, anti-patterns, a11y, performance issues in UI, responsive check, design quality
BLOCKS: motion specifically
PRIORITY: 8

### impeccable (polish)
TRIGGERS: polish this, final pass, ready to ship, clean up the UI, tighten the design, before shipping UI
BLOCKS: nothing
PRIORITY: 7

### impeccable (critique)
TRIGGERS: UX review, is the hierarchy clear, does this feel right, UX feedback, information architecture, cognitive load
BLOCKS: nothing
PRIORITY: 7

### design-motion-principles
TRIGGERS: animation, motion, transition, animate this, feels wrong motion, too fast, too slow, spring, easing, framer motion, CSS animation, motion design, this animation, audit animations, motion audit, movement, feels janky, bounce, hover effect feels
BLOCKS: static UI with no animation
PRIORITY: 8

### high-end-visual-design
TRIGGERS: premium, polished, high-end, Stripe feel, Linear feel, Vercel feel, calm UI, expensive looking, soft contrast, whitespace heavy
BLOCKS: nothing
PRIORITY: 6

### minimalist-ui
TRIGGERS: minimal, clean, Notion feel, editorial, restrained, simple layout
BLOCKS: nothing
PRIORITY: 6

### industrial-brutalist-ui
TRIGGERS: brutalist, experimental, raw, Swiss type, sharp contrast, bold layout
BLOCKS: nothing
PRIORITY: 6

---

## Code review

### two-stage-review
TRIGGERS: large diff, big PR, many files changed, complex review, thorough review, deep review
BLOCKS: small change
PRIORITY: 7

### code-review (high effort)
TRIGGERS: security review, important PR, sensitive change, production code, careful review, security-sensitive
BLOCKS: nothing
PRIORITY: 8

---

## Autonomous

### ralph-loop
TRIGGERS: keep going, run autonomously, don't stop, continue without me, run this in the background, autonomous, loop on this, keep running
BLOCKS: nothing
PRIORITY: 7

---

## Language review and build

### go-review
TRIGGERS: review this go, go code review, review my go, check this go file, go-specific review
BLOCKS: non-go code
PRIORITY: 8

### python-review
TRIGGERS: review this python, python code review, review my python, check this python
BLOCKS: non-python code
PRIORITY: 8

### rust-review
TRIGGERS: review this rust, rust code review, review my rust, check this rust, unsafe rust
BLOCKS: non-rust code
PRIORITY: 8

### fastapi-review
TRIGGERS: review this fastapi, fastapi code review, review my endpoint, check this api route
BLOCKS: non-fastapi code
PRIORITY: 8

### build-fix
TRIGGERS: build error, build failed, compilation error, won't compile, can't build, fix the build, build is broken, linker error
BLOCKS: runtime errors
PRIORITY: 9

### go-build
TRIGGERS: go build error, go compilation error, go module error, go import error
BLOCKS: nothing
PRIORITY: 9

### rust-build
TRIGGERS: rust build error, cargo error, rust compilation, borrow checker error, lifetime error
BLOCKS: nothing
PRIORITY: 9

### gradle-build
TRIGGERS: gradle build error, gradle failed, maven error, java build error, spring boot build
BLOCKS: nothing
PRIORITY: 9

---

## Testing

### tdd-workflow
TRIGGERS: TDD, test driven, write tests first, red green refactor, test first, unit test workflow
BLOCKS: adding tests to existing code
PRIORITY: 8

### e2e-testing
TRIGGERS: e2e test, end to end test, playwright, browser test, user flow test, integration test full stack
BLOCKS: unit tests
PRIORITY: 8

### test-coverage
TRIGGERS: test coverage, coverage gaps, what is not covered, coverage analysis, missing tests, uncovered code, coverage report
BLOCKS: nothing
PRIORITY: 8

---

## Multi-agent

### multi-plan
TRIGGERS: parallel tasks, multi-agent plan, decompose into agents, parallelize this, split into workers, independent tasks, fan out
BLOCKS: sequential single-task work
PRIORITY: 8

### multi-execute
TRIGGERS: execute in parallel, run agents in parallel, multi-agent execute, spawn agents for
BLOCKS: no multi-agent plan exists yet
PRIORITY: 7

### multi-workflow
TRIGGERS: multi-service workflow, coordinate services, multiple services, full stack agents
BLOCKS: nothing
PRIORITY: 7

### multi-backend
TRIGGERS: backend agents, multiple backend services, parallel backend work, backend orchestration
BLOCKS: nothing
PRIORITY: 7

### multi-frontend
TRIGGERS: frontend agents, multiple frontend tasks, parallel frontend work, frontend orchestration
BLOCKS: nothing
PRIORITY: 7

---

## Research

### search-first
TRIGGERS: research before, look this up first, check before coding, understand before implementing, what does X do, how does X work
BLOCKS: nothing
PRIORITY: 8

### deep-research
TRIGGERS: deep research, thorough research, comprehensive research, research this topic, explore this in depth
BLOCKS: simple questions with obvious answers
PRIORITY: 7

### iterative-retrieval
TRIGGERS: progressively refine, retrieve context iteratively, build up context step by step, narrow down
BLOCKS: nothing
PRIORITY: 6

---

## Security

### security-scan
TRIGGERS: security scan, vulnerability scan, check for vulnerabilities, security audit, scan for issues, security check
BLOCKS: nothing
PRIORITY: 8

---

## Docs and writing

### update-docs
TRIGGERS: update the docs, sync documentation, update readme, docs are outdated, documentation needs updating
BLOCKS: nothing
PRIORITY: 7

### plan-prd
TRIGGERS: write a PRD, product requirements document, requirements doc, spec this out, write the spec, product spec
BLOCKS: nothing
PRIORITY: 7

### article-writing
TRIGGERS: write an article, technical article, write a blog post, write about this, draft an article, technical writing
BLOCKS: nothing
PRIORITY: 7

---

## Architecture

### hexagonal-architecture
TRIGGERS: hexagonal architecture, ports and adapters, clean architecture, DDD, domain driven design, decouple layers
BLOCKS: nothing
PRIORITY: 7

### architecture-decision-records
TRIGGERS: ADR, architecture decision record, document this decision, record this architecture choice, write an ADR
BLOCKS: nothing
PRIORITY: 8

### codebase-onboarding
TRIGGERS: onboard to this codebase, understand this codebase, explain the structure, how is this project organized
BLOCKS: nothing
PRIORITY: 7

### production-audit
TRIGGERS: production audit, production readiness, is this production ready, production checklist, ready for prod, pre-production
BLOCKS: nothing
PRIORITY: 7

---

## Performance

### benchmark
TRIGGERS: benchmark this, performance benchmark, measure performance, how fast is this, perf test, latency benchmark
BLOCKS: nothing
PRIORITY: 7

---

## PR workflow

### pr
TRIGGERS: create a PR, open a PR, make a pull request, submit PR, open pull request
BLOCKS: nothing
PRIORITY: 8

### review-pr
TRIGGERS: review this PR, PR review, review pull request, look at this PR, someone else's PR
BLOCKS: nothing
PRIORITY: 8

---

## Quality and refactoring

### quality-gate
TRIGGERS: quality check, quality gate, check quality, is this good enough, pre-merge quality, verify quality
BLOCKS: nothing
PRIORITY: 7

### refactor-clean
TRIGGERS: dead code, remove unused code, clean up dead code, refactor clean, unused functions, remove unused
BLOCKS: nothing
PRIORITY: 7

### checkpoint
TRIGGERS: save checkpoint, checkpoint this, mark progress, save verification state
BLOCKS: nothing
PRIORITY: 6

---

## Skill management

### skill-create
TRIGGERS: create a skill, generate a skill, new skill, skill from git history, extract this as a skill, make a skill
BLOCKS: nothing
PRIORITY: 8

---

## Cheat sheet

| Scenario | Route |
|----------|-------|
| Bug with 3+ possible causes | `/council` then `/investigate` |
| New page/screen | taste skill -> `/impeccable shape` -> build -> `/impeccable audit` -> `/impeccable polish` |
| Animation feels wrong | `/design-motion-principles` audit mode |
| Code works but messy | `/smart-simplify` |
| Dead code / unused symbols | `/refactor-clean` |
| Second opinion on architecture | `/council` |
| Starting a long session | `/context-restore` or `/learn-codebase` |
| Shipping a PR | `/review` -> fix -> `/ship` |
| Reviewing someone else's PR | `/review-pr` |
| Full deploy pipeline | `/land-and-deploy` |
| Build / compile error | `/build-fix` (or `/go-build`, `/rust-build`, `/gradle-build`) |
| Go code review | `/go-review` |
| Python code review | `/python-review` |
| Rust code review | `/rust-review` |
| TDD from scratch | `/tdd-workflow` |
| E2E test with Playwright | `/e2e-testing` |
| Coverage gaps | `/test-coverage` |
| Security vulnerabilities | `/security-scan` |
| Tasks that can run in parallel | `/multi-plan` then `/multi-execute` |
| Research before coding | `/search-first` |
| Write an ADR | `/architecture-decision-records` |
| Production readiness check | `/production-audit` |
| Write a PRD | `/plan-prd` |
| Create a reusable skill | `/skill-create` |
| New to this codebase | `/codebase-onboarding` |

---

## Reference skills (no routing - use by name)

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
