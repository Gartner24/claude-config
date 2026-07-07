# Skills Evaluation Log

Every third-party skill/tool considered for the this stack, its verdict, and where it's wired. The
antidote to loose, forgotten skills (like `inboundsavvy-webmaster` once was). Evaluated 2026-07 during the
services-pivot revision. Full research + rationale: `~/Downloads/marketing-playbook/REVISION-PLAN.md` §3/§9.

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
| **claude-seo** | plugin (AgriciDaniel) | **USER INSTALLS** (checklist) | seo-ops / `/monthly-ops` / `/new-site` | 10.7k*, MIT, audit-only, no account access |
| **security-guidance** | plugin (Anthropic) | **USER INSTALLS** (checklist) | review workflow (passive) | Set `ENABLE_STOP_REVIEW=0` to cap per-turn cost |
| **canvas-design** | skill (Anthropic) | **USER INSTALLS** (checklist) | `/brand-system` collateral | OG/social/marketing graphics |
| **nano-banana** | our skill (from local) | A2 - adapt to Gemini API | `/brand-system` + `/new-site` assets | Replaces manual Nano Banana step; Gemini API (not kie) |
| **video-to-website** | our skill (from local) | A2 - adapt to Astro/CF | `/new-site` premium hero + `/design` | Port vanilla GSAP -> Astro island |
| **business-analyzer** | 3rd-party (local) | loose in `~/.claude/skills` - relocate to claude-config | `/brand-system` + `/new-site` discovery | Client discovery / financials / pricing-GTM |
| **graphify** | dev tool (pip) | **USER INSTALLS** (`pip install graphifyy`) | meta - index the whole system | Knowledge graph of code+docs; NOT video |

## Rejected (logged so we don't re-litigate)

| Skill | Reason |
|---|---|
| **distribb** | Backlink-exchange link scheme + Microworkers + auto-publish = Google manual-action risk. No license. |
| **NotFair** | Auto-mutates LIVE Google/Meta ad accounts + site files. Value = ads we're deferring. |
| **Hainrixz/claude-ads** | Unofficial "community MCPs" + auto-publish + pipe-to-shell install. |
| **AgriciDaniel/claude-ads** | Clean/audit-only but ads deferred - SKIP-for-now, bookmark for when ads return. |
| **taste** | Redundant with `impeccable` + `ui-ux-pro-max` (Charlie's article even says "taste OR Impeccable"). |
| **transitions.dev** | Redundant with `design-motion-principles`. |
| **ux-designer** | Redundant with the frontend-design + impeccable + a11y pipeline. |
| **artifacts-builder** | React-in-chat; we build Astro. Redundant with the pipeline. |

## Content-writing pack (situational - install per need)
`dumbify` / `storytelling` / `viral-hooks` (artemnovitckii/content-skills) overlap existing `article-writing`;
`viral-hooks` only if short-form social. Install a subdir with `npx skills add artemnovitckii/content-skills/<name>`.

## SaaS (subscriptions, not skills - see REVISION-PLAN §9)
USE: Saltly Leads (lead-gen), BrightLocal (GBP add-on), kie.ai/Gemini (images), AnswerThePublic (content),
Refero (design ref), Screen Studio/Loom (client videos). IGNORE: getautoseo (autopilot churn - our
competitor, not a tool we use), Droplytics/Bigged (wrong audience), Meshy (off-profile), Higgsfield.
