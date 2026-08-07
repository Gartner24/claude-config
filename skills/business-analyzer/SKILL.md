---
name: business-analyzer
description: Produce rigorous, data-backed business and strategy analysis  -  SWOT, B2B and B2C analysis, market and competitive analysis, pricing/go-to-market, financial projections, and country/jurisdiction context  -  for a NEW idea or an EXISTING business, grounded in CURRENT real-world data via web search. Use whenever the user wants to evaluate, validate, plan, size, price, or critique a business, product, startup, side project, or market opportunity, domestically or internationally. Trigger on requests like "do a SWOT on...", "is this a good business idea", "analyze my B2B / B2C model", "how big is the market for X in [country]", "who are my competitors", "what should I charge", "should I expand to [country]", "build financial projections", "should I build this", "evaluate this company", even if the user never says "SWOT" or "analysis". Default to this skill for any strategic business reasoning that benefits from named frameworks and current data rather than a freeform answer.
---

# Business Analyzer

A skill for producing decision-grade business analysis grounded in current, real-world data  -  not generic advice and not stale assumptions. The goal is always to help the user make a *better decision*: whether to build, where to expand, how to position, what to charge, or whether to keep investing. Frameworks and data are tools toward that decision, never the deliverable on their own.

## Core principles

1. **Reach a defensible conclusion.** Bad analysis lists facts; good analysis reaches a verdict and shows its reasoning. Every analysis ends with a clear point of view (go / no-go / pivot, or the ranked risks and the next actions that reduce them) and names the single factor most likely to sink the business.
2. **Ground it in current data.** Market sizes, competitor prices, regulations, tax regimes, and economic conditions change and are country-specific. Do not analyze from memory or assumption when a fact is checkable  -  gather it (see Step 2). Date-stamp data and separate hard fact from estimate from assumption.
3. **Be honest.** If an idea has a fatal flaw  -  no buyer, no moat, hostile unit economics, a market that doesn't exist  -  say so plainly and early. A flattering analysis that lets someone waste a year is a failure.
4. **Match the user's reality.** A bootstrapped solo founder in Colombia and a VC-backed US team face different constraints, costs, and rules. Tailor everything to their actual resources, country, and goals.

## Step 1  -  Establish context

Before analyzing, nail down (from the conversation, or by asking at most 2-3 tight questions):

1. **New or existing?** An idea is judged on *evidence of demand and feasibility*; an operating business on *performance, trends, and defensibility*.
2. **What's the actual decision?** Start it? Keep going? Expand to a country? Price it? Position against X? The decision determines which frameworks lead.
3. **B2B or B2C (or both)?** Buyer, motion, and economics differ.
4. **Which country / market?** Domestic, a specific target country, or international/cross-border? This drives market size, regulation, tax, payments, and currency considerations. If unstated, ask or assume the user's home market and say so.
5. **What's already known?** Pull any numbers, traction, or facts the user gave. Don't re-ask for what's in context.

If the user gave enough to proceed, proceed  -  state assumptions explicitly at the top instead of interrogating them.

## Step 2  -  Gather current data (do this before concluding)

This skill does not fetch data on its own; it directs you to. Use **web search** (and any connected data tools/MCP connectors) to pull current facts. If web search is unavailable, say so and label every market figure as an unverified estimate.

Read `references/research.md` for sourcing discipline. At minimum, gather what the specific decision needs:

- **Market size & growth** for the *exact* segment and *country*  -  build bottom-up (customers x price) and cross-check against any top-down figure. Beware vendor-inflated TAM.
- **Competitors & their pricing**  -  real current prices, positioning, and target segments.
- **Regulatory / tax / formation facts** for the relevant jurisdiction  -  only what affects the decision.
- **Macro/country indicators** when expanding or entering a new market (see `references/country-context.md`).

Always note the date and source of figures, and flag conflicts between sources rather than picking one silently.

## Step 3  -  Select the framework(s)

Match the decision to the lens. Read the relevant reference file(s) before writing  -  they contain the checklists, the data to gather, and the failure modes to avoid. Most real requests combine 2-3; that's expected and good.

| User's situation / ask | Lead framework(s) | Reference file(s) |
|---|---|---|
| "Is this a good idea / should I build this?" (new) | New-business validation + SWOT | `new-business.md`, `swot.md` |
| "Evaluate / assess my existing business" | Existing-business diagnostic + SWOT | `existing-business.md`, `swot.md` |
| "Do a SWOT" (explicit) | SWOT (properly, with TOWS) | `swot.md` |
| Sells to companies | B2B analysis | `b2b.md` |
| Sells to consumers | B2C analysis | `b2c.md` |
| "How big is the market / who are competitors?" | Research + competitive analysis | `research.md`, `competitive.md` |
| "Should I enter / expand to [country]?" / international | Country context + research | `country-context.md`, `research.md` |
| "What should I charge / how do I go to market?" | Pricing & GTM | `pricing-gtm.md` |
| "Build projections / break-even / is it profitable?" | Financials | `financials.md` |

Cross-cutting: any analysis touching a specific country pulls in `country-context.md`; any analysis making a market-size or competitor claim pulls in `research.md`.

## Step 4  -  Produce the analysis

Follow the output template in the reference you're leading with. Across all frameworks:

- **Evidence over assertion.** "TAM is large" is worthless. "~X businesses in [country], paying ~Y, reachable via Z" is analysis. Cite sources and dates for current data.
- **Name the killer risk.** Lead with the one thing most likely to sink it.
- **Force-rank.** A SWOT with 9 weaknesses or a plan with 12 ideas is useless. Surface the 1-3 that move the decision.
- **End with a decision and next actions.** Three concrete, cheap things (time, not money) to validate or de-risk the biggest unknown in the next two weeks.
- **Show the math.** For any economics or projection, show the calculation and the assumptions feeding it.

## Step 5  -  Format

A clear written analysis in chat for a gut-check; a structured document (markdown/docx) when the user wants something to keep, share, or pitch. Build a file when it's substantial (multi-framework, reusable, investor-facing). Offer a visual (SWOT quadrant, positioning map, unit-economics or projection breakdown) when it genuinely clarifies  -  but the written reasoning is the product.

## What NOT to do

- Don't produce a four-quadrant SWOT of vague platitudes  -  the #1 failure mode (see `swot.md`).
- Don't state market sizes, prices, or regulations from memory when they're checkable  -  search.
- Don't validate an idea just because the user is excited. The job is the truth, delivered constructively.
- Don't drown the user in every framework  -  pick the 1-2 that answer their question.
- Don't give definitive legal, tax, or securities advice. Flag clearly when something needs a local lawyer or accountant, especially for cross-border tax, entity formation, and regulated industries.
