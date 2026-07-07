# B2B Analysis — selling to businesses

B2B means another organization is the buyer. The defining features: fewer, larger customers; a *buying committee* rather than one person; longer sales cycles; purchases justified by ROI, not desire. Analyze accordingly.

## 1. The buyer (this is where most B2B analysis fails)

"Businesses" don't buy — *people inside businesses* do, and usually several of them.

- **Ideal Customer Profile (ICP):** Define the *company* you serve best — size, industry, geography, tech stack, the trigger that makes them need you now. A sharp ICP beats a broad one; "companies that just raised a Series A and have no in-house X" is worth more than "SMBs."
- **The buying committee:** Identify each role and what they care about:
  - **Champion** — feels the pain, wants your product, sells internally for you.
  - **Economic buyer** — controls budget, signs off; cares about ROI and risk.
  - **End users** — live with it daily; care about whether it actually works.
  - **Blockers** — IT/security/legal/procurement; can kill a deal over compliance, integration, or contract terms.
  - In SMB, these can collapse into one person (often the owner). In enterprise, there can be 6-10. Know which world you're in.
- **The economic case:** B2B buyers need a number. Does your product make them money, save them money, reduce risk, or save time that converts to money? Quantify it. "Saves 10 hrs/week per analyst = ~$X/yr" is the sentence that closes deals.

## 2. The sales motion (and whether the economics survive it)

The motion must match the price point. This is the single most common B2B killer.

| ACV (annual contract value) | Viable motion |
|---|---|
| < ~$1-2k | Must be self-serve / product-led. Human sales loses money. |
| ~$2k-25k | Inside sales / low-touch, light demos, fast cycle |
| ~$25k-100k+ | Field sales, multi-stakeholder, pilots, procurement |
| $100k+ | Enterprise: long cycles, security review, custom terms |

If your price is $1,200/yr but the deal needs three calls and a security questionnaire, the unit economics are dead on arrival. Either raise price, or strip the motion to self-serve.

## 3. Unit economics (the numbers that decide it)

- **CAC** (cost to acquire a customer) — fully loaded: marketing + sales salaries + tooling, divided by customers won.
- **LTV** (lifetime value) — ACV × gross margin × average customer lifetime (1 / annual churn).
- **LTV:CAC** — rule of thumb ≥ 3:1 is healthy; < 1:1 means you lose money on every customer.
- **CAC payback** — months to recover CAC from gross profit; < 12 months is good for SMB, < 18-24 for enterprise.
- **Net revenue retention (NRR)** — for existing businesses, the best single health metric. >100% means you grow even with zero new customers (expansion > churn). >120% is excellent.
- **Logo vs. revenue churn** — losing small accounts but keeping big ones can still be healthy.

If the user has no numbers yet (new business), estimate the two that matter most — likely ACV and CAC — and stress-test whether the motion can possibly work at that price.

## 4. Moat / defensibility

B2B moats are stronger than B2C ones when they exist:
- **Switching costs** — once embedded in workflow/data, ripping you out is painful.
- **Integrations** — the more systems you connect to, the stickier.
- **Data/network effects** — your product gets better with more usage/customers.
- **Compliance/certifications** — SOC 2, ISO, industry approvals are real barriers.
- **Distribution** — a partnership or channel competitors can't easily replicate.

A B2B product with no switching costs and no integration depth is a feature, not a company — flag this.

## 5. Competitive landscape

- Who do they buy instead of you, *including* "spreadsheet + intern" and "do nothing"? Status quo is your real competitor.
- Where do you win, where do you lose, and is that a stable advantage or a temporary head start?
- Porter's Five Forces is useful here: buyer power (few big buyers = high power), supplier power, new entrants, substitutes, rivalry.

## Output template

```
# B2B Analysis: [Business]
*Assumptions: ...*

## ICP & buying committee
[who buys, who decides, who blocks, the economic case]

## Sales motion vs. price
[is the motion viable at this ACV? the killer check]

## Unit economics
[CAC, LTV, LTV:CAC, payback, NRR if existing — with the math]

## Moat
[what stops a competitor or the customer's IT team from replacing you]

## Competitive position
[incl. status quo; where you win/lose]

## Verdict & next 2 weeks
[go/no-go/fix-this-first + 3 cheap validation actions —
e.g. 5 customer-discovery calls, one fake-door landing page, one signed LOI]
```
