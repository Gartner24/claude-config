# Calculator asset

Loaded when a client needs a link-worthy asset (MONTHLY-OPS-GUIDE sec. 6 step 2), or when
`core-update-triage.md` / the results page shows a tool is the expected format for a query the client
already targets. Builds ONE genuinely useful calculator page in the client's own site stack.

One calculator per real customer task, never a page per keyword: no "X calculator for [city]" or
per-variant copies (SEO-GUIDE sec. 1-2, scaled content abuse). If an existing service page is where the
buyer asks the question, the calculator can live there as a section instead of a new URL.

## Step 1 - pick the calculator
From the client's niche, propose up to 5 ideas, each tied to something buyers already search or ask the
client (GSC queries, the client's FAQ, quote requests). Table: name | what it works out | the real query
or question behind it. Common shapes: cost or quote estimator, savings or ROI, sizing or quantity,
break-even or margin, repayment. The operator and client pick one.

## Step 2 - get real numbers
Ask for the client's prices or rates, the figures they use when quoting, where they operate, and who
checks the maths (name and qualification). A missing figure may use a published source, cited and flagged
for the client to confirm. Never invent a rate, source or credential.

## Step 3 - build it
An Astro page (or component dropped into an existing page) in the client's repo, following the site's
existing layout, tokens and SEO component (unique title and description, one H1, canonical, breadcrumbs).
Everything except the live result is server-rendered HTML; the calculator is a small inline script or
island with no new dependency.

Page sections, in order:
1. **The answer above the tool:** H1 naming what it works out; plain text saying what it calculates, for
   whom, where it applies, and the typical answer for the most common case. No word count target.
2. **The calculator:** labelled inputs with units and sensible defaults, as few fields as the answer
   needs, input validation (required, no negatives), result shown immediately. **No email, phone or
   contact gate before the result.**
3. **Your result, explained:** in words as well as a number: meaning, likely range, what moves it, which
   service fits.
4. **What each input means:** one sentence each, with where to find the figure.
5. **How it works:** formula, every assumption and rate, the source of each, and the last-checked date,
   in the HTML (not only in the script).
6. **Worked example:** inputs, each step, the answer.
7. **Common answers:** an HTML table of results for the usual cases, readable without running the tool.
8. **When it does not apply:** limits, when the estimate stops being reliable, when to get a quote.
9. **Who made and checked it:** name, qualification, link to their profile or author page, last-checked
   date, short change note. Placeholders like [Name, qualification] if not supplied.
10. **Next step:** the service the result points to, related pages, one CTA with the phone as text.

Schema: no FAQPage, no HowTo. BreadcrumbList matching the visible breadcrumbs is enough; the visible
method, example and table are what search engines and AI read.

Script: no external libraries, clear names, results update when inputs are complete (or on a button) with
no reload, numbers formatted for the client's locale and currency (es-CO uses `.` for thousands and `,`
for decimals; use `Intl.NumberFormat`). Accessible labels, focus states, contrast; mobile-first; prints
cleanly.

## Step 4 - before publish
- Run five real cases from the client's records; answers match what actually happened.
- Every rate matches current prices and its source; last-checked date shown.
- Every [placeholder] filled.
- View source: answer, method, worked example and common answers present as text.
- Link it from the relevant service pages and nav or hub; ship; IndexNow (seo-ops re-index step).
- Re-check rates on a schedule the client agrees to; a stale rate is worse than no calculator.

## Output
The idea table (step 1), then the page and component files in the client's repo, then the pre-publish
checklist with results. Copy in the client's language (en, or es-CO for Colombian clients).
