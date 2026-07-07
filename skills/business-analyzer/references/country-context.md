# Country & Jurisdiction Context

Where a business operates changes almost everything: market size, what's legal, how you get paid, how you're taxed, what currency risk you carry, and how expensive it is to hire. Never assume a US/global playbook transfers to another country. Use web search (`research.md`) to get current, country-specific facts — laws and rates change.

## For a single target country, look up what the decision needs

- **Market** — size of the *specific* segment in this country, growth, and local buying behavior.
- **Economic indicators** — GDP per capita and inflation (purchasing power and pricing), currency stability (FX risk if you price/cost in another currency), and adoption metrics that matter to the model (internet, smartphone, card/digital-payment penetration, banking inclusion).
- **Regulatory & tax** — what's required to legally sell this product/service: licenses, consumer/data rules, VAT/sales tax (e.g. IVA in much of LatAm), invoicing/e-invoicing requirements, and income/corporate tax basics. Only the parts that bear on the decision.
- **Business formation** — what entity types exist, rough cost/time to register, and whether a local entity is even needed to start.
- **Payments** — how locals actually pay (cards vs. bank transfer vs. local wallets vs. cash-on-delivery), which gateways serve the country, and payout/settlement realities. This is often the make-or-break for digital businesses in emerging markets.
- **Labor** — only if hiring: contractor vs. employee rules, mandatory benefits, severance, recent labor reforms.
- **Local competitors** — who already serves this market locally (different from the global players).

## PESTEL — structured macro lens

When entering or expanding, run the relevant PESTEL factors (skip what's irrelevant — don't fill boxes for the sake of it):

- **Political** — stability, government attitude to the sector, trade policy.
- **Economic** — growth, inflation, FX, interest rates, consumer/business spending power.
- **Social** — demographics, culture, language, trust in digital/online, buying habits.
- **Technological** — infrastructure, internet/mobile penetration, relevant platform adoption.
- **Environmental** — only where it bears on the business (logistics, regulation, sourcing).
- **Legal** — regulation specific to the product, data/privacy regime, IP enforcement, contract enforceability.

The point is to surface the 2-3 macro factors that actually change the decision, not a six-box essay.

## Cross-border / international expansion

Selling into multiple countries adds layers — and digital vs. physical goods differ sharply:

- **Localization** — language, currency display, local payment methods, cultural fit. Often decisive for conversion.
- **Payments & FX** — can you collect in local currency and get paid out? What are the fees and settlement times? Currency volatility on receivables.
- **Tax** — cross-border VAT/GST on digital services (many countries now tax foreign digital sellers), customs/duties on physical goods, and **permanent-establishment / nexus** risk (selling into a country can create a tax obligation there). This is where users most need a real accountant — flag it.
- **Data & privacy** — GDPR (EU/UK), and country-specific regimes (e.g. LGPD in Brazil, Colombia's data-protection law). Affects what you can collect and how.
- **Logistics & support** — fulfillment, returns, and time-zone/language support for physical goods or high-touch services.
- **Regulatory divergence** — what's allowed in one country may be restricted in another (especially fintech, health, data).

Rule of thumb: **digital products** scale across borders far more easily (no logistics, but watch digital-VAT and data rules); **physical goods** hit customs, logistics, and per-country cost walls fast.

## Caution

Give the *business* implications of country facts, but do not give definitive legal or tax advice. For entity choice, cross-border tax, regulated sectors, and employment, state clearly that a local lawyer/accountant is needed — name *what* to ask them, so the user walks in prepared.

## Output (when country is the focus)

```
## Country context: [Country]
- Market: [size/growth for the segment, with source+date]
- Economy: [the 2-3 indicators that matter here]
- Regulatory/tax: [what's required; flag what needs a professional]
- Payments: [how people pay; gateway/payout reality]
- Local competition: [who's already there]

## PESTEL — decisive factors only
[the 2-3 macro factors that change the decision]

## Implications & verdict
[what this means for the decision + the country-specific killer risk]
```
