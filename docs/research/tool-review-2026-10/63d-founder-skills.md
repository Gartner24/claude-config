# emotixco/claude-skills-founder (research 63d)

Facts: MIT, plugin "founder" v2.1.4, 13 skills, created 2026-03-10, last push 2026-10-07, 640 stars, 0 open issues. Clone read in full (all 13 SKILL.md, shared/conventions.md, plugin.json, marketplace.json, commands stubs, evals, example). Not run.

Install: /plugin marketplace add emotixco/claude-skills-founder ; /plugin install founder@emotix. Skills appear as /founder:<name>. Descriptions cost ~1,100 tokens per session (author's figure). The commands/*.md files are v1 stubs that only print install steps.

Security read: no hooks, no scripts, no MCP config, no curl/wget/http URLs, no base64, no "ignore previous" patterns in skills/commands/shared (grep clean, plus read by eye). allowed-tools per skill: Read, Edit(founder/**), WebSearch, WebFetch (landing-page, mvp-scope, persona-gen, user-interviews have no web tools). Risk is small: WebFetch of search results is the normal prompt-injection surface (competitor-matrix, pricing-strategy, go-to-market, fundraise-prep). evals/ has fixture.sh files (fixtures that create founder/ files) - only run by the author's eval harness, never by plugin install. Plugin root reference ${CLAUDE_PLUGIN_ROOT}/shared/conventions.md is read at run time.

founder/ folder: facts.md (dated founder facts, one per line) plus one file per skill (founder/<skill>.md, first line a header comment). Each skill reads upstream files and does not re-ask. Rules: no invented metrics/testimonials (bracket placeholders), sources for outside facts, no em dashes (matches user's ASCII rule), word cap per output. Fit: a founder/ folder at a repo root is a new top-level dir. User's workflow keeps state in docs/scope, docs/specs, .workflow/ - founder/ would sit outside it. Would need gitignore or a decision; fits a side project's repo, not client repos. Not a scope-contract file, so wf ignores it.

Per skill (quality: all are concrete numbered steps with output templates and word caps, not fluff; strongest: conventions.md anti-invention rules)
1. validate-idea - 5 fatal questions, 7-dim scorecard /35, 3 experiments under $200, build/pivot/kill. Overlap: office-hours, plan-ceo-review, business-analyzer, product-manager-review. KEEP-ish (the scorecard + verdict is useful for side projects; check office-hours first).
2. product-brief - problem, audience, value prop, 5-7 MVP features, 90-day KPIs. Overlap: product-manager-review, /scope, /architect. SKIP.
3. persona-gen - 3 personas, pain points quotable, priority matrix. Overlap: customer-research. SKIP (flags personas as hypotheses, good).
4. user-interviews - Mom Test 25-min script, screening, analysis. Overlap: customer-research (partial). KEEP if customer-research lacks a script.
5. competitor-matrix - 5-8 competitors, sourced prices, feature table, gaps, threats. Overlap: business-analyzer, deep-research. Mild overlap; KEEP candidate (sourced, "Not found" rule).
6. pricing-strategy - 6 model scoring, 3 tiers, unit economics, launch vs scale. Overlap: pricing (direct), offers, paywalls. SKIP (SaaS-only; freelance studio uses offers/pricing).
7. mvp-scope - must/should/won't triage, one-sentence MVP, solo build time. Overlap: kano-model, /scope. SKIP or borrow the "15 features -> 8 won't have" rule.
8. landing-page - section-by-section copy, placeholders for testimonials. Overlap: cro, marketing-psychology, copy skills, new-site. SKIP.
9. email-sequence - 5-7 email onboarding/reengagement, under 150 words. Overlap: onboarding, lead-magnets (partial). SKIP.
10. go-to-market - pre-launch, PH/HN/Reddit tactics, channel ranking, budget. Overlap: launch (direct), seo-ops. SKIP.
11. metrics-dashboard - 5 metrics per stage, vanity list, weekly review. Overlap: ab-testing (little), business-analyzer. Low value for a freelance studio. SKIP.
12. pitch-deck - 12-slide outline with takeaway headlines. Overlap: none in the user's set (slides skills only render). Only useful if raising. SKIP unless fundraising.
13. fundraise-prep - readiness score, SAFE/note, 50-investor framework, 12-week plan. Overlap: none. Irrelevant to a solo freelancer/side projects. SKIP.

Verdict: nothing is dangerous, nothing is much better than the user's existing skills. The author's own evals say that on Opus 5, 8 of 10 cases score the same with or without the plugin; the one real gain is updating facts.md when a new number contradicts an old one. Recommendation: do not install the plugin. Steal two ideas: (a) validate-idea's 7-dim scorecard + build/pivot/kill verdict, if office-hours lacks it; (b) the facts.md "input overrides saved fact, say what it replaces" convention and the no-invented-numbers rules, which could go in a customer-research or offers skill. Note: I did not read ~/.claude/skills contents or SKILLS.md (context limit); overlaps are judged from skill names/descriptions in the session skill list, so confirm before dropping anything.
