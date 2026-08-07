# Existing Business Diagnostic

An operating business has data, so analyze *reality, not hope*. The job is to read performance and trends, find what's actually driving or draining the business, and recommend where to focus. The trap is describing the business; the value is diagnosing it - finding the one or two levers that matter most.

## 1. Health snapshot - get the numbers first

Ask for / pull whatever the user has. The most diagnostic metrics:

- **Revenue & growth rate** - and the *trend* (accelerating, flat, declining?). Growth rate matters more than absolute size for judging trajectory.
- **Gross margin** - revenue minus direct costs (COGS). Tells you how much each sale actually contributes. Low margin caps everything downstream.
- **Profitability / contribution** - is the business actually making money after all costs, or buying growth at a loss?
- **Customer concentration** - what % of revenue comes from the top 1-3 customers? >30% from one customer is a serious risk.
- **Retention / churn / repeat rate** - the single best signal of whether customers value the product. Growing while churning hard = a leaky bucket.
- **CAC & payback** - is acquisition still profitable, or has it gotten more expensive over time?
- **Cash runway** (if relevant) - months of operating expense in the bank.

If the user can't supply these, that *is* a finding: a business run without knowing its margin, churn, or CAC is flying blind, and step one is instrumentation.

## 2. Diagnose, don't just describe

Move from numbers to causes:

- **Where's the growth (or decline) coming from?** New customers vs. expansion vs. price? Which segment/product/channel is pulling weight and which is dead?
- **What's the binding constraint?** Every business has one bottleneck limiting growth right now - usually one of: demand (can't get enough customers profitably), conversion (traffic but no sales), retention (customers leave), margin (can't make money per sale), or capacity (can't deliver more). Find *the* one. Fixing anything else is wasted effort.
- **Unit economics still working?** Re-run LTV:CAC and payback with current (not founding) numbers. Markets and ad costs drift; a model that worked at launch may be underwater now.
- **Trend vs. snapshot.** One quarter is noise. Look at direction over time. A profitable business shrinking 10%/quarter is in more trouble than a break-even one doubling.

## 3. Defensibility & risk (forward-looking)

- **Moat check** - is the advantage that got them here durable, or eroding (patent expiring, competitor caught up, platform dependence)?
- **Concentration risks** - single big customer, single channel (e.g. one ad platform or one marketplace whose algorithm/policy could change overnight), single supplier, single key person.
- **Margin pressure** - rising costs, commoditization, price competition?

## 4. SWOT to synthesize

Run `references/swot.md` using the *real data* - strengths and weaknesses grounded in the actual metrics, not aspirations. This is where the existing-business analysis crystallizes into a point of view, especially the W-T (existential risk) and S-O (biggest lever) crosses.

## Output template

```
# Diagnostic: [Business]
*Data provided / assumptions: ...*

## Health snapshot
[the key metrics, with trend direction - a small table is fine]

## Diagnosis
- **What's working:** [the engine, with evidence]
- **The binding constraint:** [the ONE bottleneck limiting growth now]
- **Unit economics today:** [re-run, do they still work?]
- **Biggest risk:** [concentration / moat erosion / margin / cash]

## Where to focus (the lever)
[the 1-2 highest-leverage moves, ranked, with rough expected impact  - 
not a laundry list of 12 ideas]

## Verdict & next 2 weeks
[clear point of view on trajectory + the 3 highest-leverage actions,
or "instrument these metrics first" if they're flying blind]
```

The deliverable is focus. A good diagnostic tells an overwhelmed operator the *two things* to work on and the ten things to ignore.
