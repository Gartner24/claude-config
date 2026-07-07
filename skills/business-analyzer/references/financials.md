# Financial Projections

Turn the strategy into numbers so the user can see whether it actually makes money and where the sensitivities are. Projections are structured *assumptions*, not facts — label them as such, show every input, and never present a forecast as certainty. This is business modeling, not accounting or tax advice; flag when a real accountant is needed.

## Start with the unit, then scale

Don't model the whole company before you understand one sale.

- **Contribution margin per unit** = price − variable costs (COGS, payment fees, shipping, support per unit). This is what each sale actually contributes toward fixed costs and profit. If it's negative, nothing downstream matters — stop and fix it.
- **Gross margin %** = contribution / price. Tells you how much room you have for everything else (digital products: often 70-90%; physical goods: often 20-50%).

## Break-even

The clearest single number for a new business:

```
Break-even units = Fixed costs (per period) / Contribution margin per unit
```

Then sanity-check it against reality: "We need 420 customers/month to break even — given our channel and conversion, how long does that take, and is it plausible?" A break-even point you can't realistically reach is a no-go signal.

## Simple projection (12-36 months)

Build it transparently, month by month or quarter by quarter:

```
Revenue        = customers × price × purchase frequency
- COGS / variable costs
= Gross profit
- Operating expenses (salaries, tools, rent, marketing spend)
= Operating profit / (loss)
```

Drive it off **explicit assumptions** the user can challenge: starting customers, monthly growth rate, churn, CAC, price, fixed costs. The assumptions *are* the model — list them at the top. For subscription models, track the customer base as: start + new − churned each period (a leaky bucket compounds fast).

## Cash & runway (if pre-profit)

- **Burn rate** = monthly cash out − cash in.
- **Runway** = cash in bank / monthly burn. Months until you must be profitable or raise. Below ~6 months is a flashing light.

## Sensitivity — best / base / worst

A single forecast is false precision. Show three cases by flexing the 2-3 assumptions that matter most (usually growth rate, churn, and CAC or price):

- **Base** — realistic.
- **Best** — things go well.
- **Worst** — growth is half, CAC double, churn higher. Does the business survive this? If worst-case is fatal and plausible, that's the risk to manage.

## Key ratios to report

- Gross / contribution margin
- LTV:CAC (≥ 3:1 healthy) and CAC payback (months)
- Net revenue retention (existing businesses)
- Break-even point and time-to-break-even
- Runway (if relevant)

## Output template

```
# Financial Projection: [Business]

## Assumptions (the model rests on these)
[price, customers, growth %, churn, CAC, COGS, fixed costs — each labeled, sourced where possible]

## Unit economics & break-even
[contribution margin, gross margin %, break-even units + reality check]

## Projection (base case)
[revenue → gross profit → operating profit, over the horizon — a small table]

## Sensitivity
[best / base / worst on the key levers; does worst-case survive?]

## Key ratios & verdict
[the ratios + a plain-language read on whether/when this makes money,
and the biggest financial risk]
```

If currencies are involved (costs in one, revenue in another), state the FX assumption and flag the volatility risk — see `country-context.md`.
