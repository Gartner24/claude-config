# Skills Evaluation Log

Every third-party skill/tool considered for this stack, its verdict, and where it's wired. The
antidote to loose, forgotten skills (like the client CMS skill once was). Evaluated 2026-07 during the
services-pivot revision. Full research + rationale: `~/Downloads/marketing-playbook/REVISION-PLAN.md` sec. 3/sec. 9.

**Rule:** nothing is installed-and-forgotten. Adopted -> lives in `claude-config/skills/` (or PLUGINS.md),
registered in `USAGE.md` + `SKILLS.md`, and referenced by the command that uses it (`/new-site`,
`/monthly-ops`, `/brand-system`).

## Adopted

| Skill / tool | Kind | Status | Wired into | Notes |
|---|---|---|---|---|
| **seo-ops** | our skill | authored (`skills/seo-ops`) | `/monthly-ops` SEO add-on | Recurring SEO from SEO-GUIDE + MONTHLY-OPS-GUIDE; uses claude-seo |
| **content-ops** | our skill | authored (`skills/content-ops`) | `/monthly-ops` Content + `/new-site` copy | Uses voice-dna + anti-ai-writing; SEO-GUIDE topical rules |
| **anti-ai-writing** | 3rd-party (artemnovitckii) | installed (`skills/anti-ai-writing`) | content-ops | MIT; de-slop final pass |
| **voice-dna** | 3rd-party method (artemnovitckii) | installed (`skills/voice-dna`) | content-ops | Build a `voice-dna.md` per client from ~20 samples |
| **claude-seo** | plugin (AgriciDaniel) | **INSTALLED** 2026-07-07 (checklist) | seo-ops / `/monthly-ops` / `/new-site` | 10.7k*, MIT, audit-only, no account access |
| **security-guidance** | plugin (Anthropic) | **USER INSTALLS** (checklist) | review workflow (passive) | Set `ENABLE_STOP_REVIEW=0` to cap per-turn cost |
| **canvas-design** | skill (Anthropic) | **USER INSTALLS** (checklist) | `/brand-system` collateral | OG/social/marketing graphics |
| **nano-banana** | our skill (from local) | authored (`skills/nano-banana` + Gemini script) | `/brand-system` + `/new-site` assets | Gemini API (not kie); structured-prompt realism |
| **video-to-website** | our skill (from local) | authored (`skills/video-to-website`, Astro) | `/new-site` premium hero + `/design` | Ported vanilla GSAP -> Astro island + Cloudflare |
| **business-analyzer** | 3rd-party (local) | relocated to `claude-config/skills` + symlinked | `/new-site` discovery (business-analyzer skill) | Audience / competitive / financials / pricing-GTM / SWOT |
| **graphify** | dev tool (pip) | **USER INSTALLS** (`pipx install graphifyy`) | meta - index the whole system | Knowledge graph of code+docs; NOT video |

## Rejected (logged so we don't re-litigate)

| Skill | Reason |
|---|---|
| **distribb** | Backlink-exchange link scheme + Microworkers + auto-publish = Google manual-action risk. No license. |
| **NotFair** | Auto-mutates LIVE Google/Meta ad accounts + site files. Value = ads we're deferring. |
| **Hainrixz/claude-ads** | Unofficial "community MCPs" + auto-publish + pipe-to-shell install. |
| **AgriciDaniel/claude-ads** | Clean/audit-only but ads deferred - SKIP-for-now, bookmark for when ads return. |
| **taste** | Redundant with `impeccable` + `ui-ux-pro-max` (Charlie's article even says "taste OR Impeccable"). |
| ~~**transitions.dev**~~ | ~~Redundant with `design-motion-principles`.~~ **OVERTURNED 2026-08-06** - see Adopted. |
| **ux-designer** | Redundant with the frontend-design + impeccable + a11y pipeline. |
| **artifacts-builder** | React-in-chat; we build Astro. Redundant with the pipeline. |

### Rejected 2026-08-06 (design/marketing intake round)

| Skill | Reason |
|---|---|
| **AThevon/genjutsu** | 186* - lowest of the batch. "Award-winning UI, premium animation, creative direction" is exactly `impeccable` + `ui-ux-pro-max` + `frontend-design`. No distinct layer. |
| **LottieFiles/motion-design-skill** | 902*. Universal motion principles - now triple-covered by `design-motion-principles` AND the emilkowalski set. Weakest of the three sources. |
| **karpathy-guidelines** (multica-ai) | The 200k-star repo is ONE skill: behavioral guardrails against LLM overcomplication and non-surgical edits. That is what ponytail mode + our CLAUDE.md already enforce, harder and with a persistence contract. |
| **gstack design-review** | Already installed via jjstack. The awesomeskill.ai listing is the same skill. |
| **anthropics/skill-creator** | Already installed as an official plugin (`plugins/marketplaces/claude-plugins-official/plugins/skill-creator`). |
| **impeccable** | Already at 4.1.3. |
| **Dialkit** | Not a skill - an npm package (`dialkit@1.4.3`), a runtime control panel for tweaking UI values. Install per-project if a build wants it, not into the skill namespace. |
| **Whisper** | Not a skill - OpenAI's speech-to-text model. |
| **HeyGen / Hedra** | Not skills - avatar-video SaaS. |
| **Codrops "Claude mascot with SVG+GSAP"** | Not a skill - a blog article. The technique is covered by `gsap-core` + `gsap-timeline`. |
| **35 of 47 marketingskills** | copywriting, copy-editing, content-strategy, social, emails, seo-audit, ai-seo, programmatic-seo, schema, site-architecture, image, video, etc. Covered by `content-ops` / `article-writing` / `seo-ops` / `voice-dna`; `image` and `video` would also collide by name. 12 adopted - see SKILLS.md. |
| **"42 skills" IG carousel** (juanbertorello.ia) | **Unattributable.** Slides 2-6 of 7 seen; slide 1 (the source) missing. ~22 of the 42 map to marketingskills / gstack / taste-skill / Anthropic's canvas-design. The other 20 have no located source - full list in the carousel section below. Get slide 1 before re-evaluating. |

### The 20 unsourced names from that carousel

`refactoring-ui`, `top-design`, `web-typography`, `microinteractions`, `ux-heuristics`,
`gpt-image`, `image-enhancer`, `theme-factory`, `excalidraw-diagram`, `content-studio`,
`hooked-ux`, `improve-retention`, `design-everyday-things`, `lean-ux`, `storybrand-messaging`,
`made-to-stick`, `voice-jcb`, `humanise-text`, `social-content`, `verify-work`.

Several read as book adaptations (Refactoring UI, Hooked, The Design of Everyday Things,
Lean UX, Building a StoryBrand, Made to Stick) and `voice-jcb` reads like the author's own
initials - so this is likely his private collection, not a public repo. Only slide 1/7 or his
bio link will resolve it. Repo-existence checks were not completed: GitHub code search hit the
5k/hr rate limit mid-audit, so "no source" here means "not located", not "confirmed absent".

### Adopted 2026-08-06

| Skill / tool | Kind | Status | Wired into | Notes |
|---|---|---|---|---|
| **emilkowalski/skills** (9) | 3rd-party (26.4k*) | installed (`~/.claude/skills/`) | `/design` steps 6-7 | Primary source behind design-motion-principles' Kowalski lens. `animate` is now the default motion skill. |
| **greensock/gsap-skills** (8) | 3rd-party, official (13.1k*) | installed | `/design` step 6 (scroll/timeline) | Nothing local covered GSAP. Includes matchMedia reduced-motion. |
| **transitions.dev** (2) | 3rd-party (2.5k*) | installed | `/design` steps 6-7 | **Overturns the 2026-07 rejection.** That call treated it as a principles skill; it is not. design-motion-principles says *whether and why* to animate; transitions-dev ships the concrete per-component CSS, and `transitions-polish` tokenizes existing hardcoded durations - which nothing else here does. Different layer, not a duplicate. |
| **zanwei/design-dna** | 3rd-party (1.3k*) | installed | `/design` step 1 | Reverse-engineers a reference screenshot/URL into token JSON. ui-ux-pro-max picks from a catalog; this extracts from a real design. |
| **threejs-skills** (10) | 3rd-party (2.9k*) | installed | `/design` step 6 (3D only) | User confirmed 3D work. Dead weight otherwise - drop if no WebGL project lands. |
| **blader/humanizer** | 3rd-party (34k*, MIT) | installed | content pipeline, before anti-ai-writing | Knowingly overlaps `anti-ai-writing`. Mechanical 33-pattern sweep vs our voice-aware pass. Run humanizer first, anti-ai-writing last. |
| **marketingskills** (12 of 50) | 3rd-party (MIT) | installed | `/design` step 8, `/new-site`, `business-analyzer` | marketing-psychology + CRO family + launch/lead-magnets/customer-research. `/new-site` had no conversion layer. |
| **packshot** | hand-delivered zip | installed + adapted | `/brand-system` assets | **No public repo - the zip in ~/Downloads is the only copy.** Needs `pip install fal-client` + `FAL_KEY`; ~$0.12/image on FAL. Rewired to read `brand-system.html`; output to `./packshots/`. |

## Content-writing pack (situational - install per need)
`dumbify` / `storytelling` / `viral-hooks` (artemnovitckii/content-skills) overlap existing `article-writing`;
`viral-hooks` only if short-form social. Install a subdir with `npx skills add artemnovitckii/content-skills/<name>`.

## SaaS (subscriptions, not skills - see REVISION-PLAN sec. 9)
USE: Saltly Leads (lead-gen), BrightLocal (GBP add-on), kie.ai/Gemini (images), AnswerThePublic (content),
Refero (design ref), Screen Studio/Loom (client videos). IGNORE: getautoseo (autopilot churn - our
competitor, not a tool we use), Droplytics/Bigged (wrong audience), Meshy (off-profile), Higgsfield.
