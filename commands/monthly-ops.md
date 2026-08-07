---
description: Run one client's monthly retainer cycle - Care base + each add-on the client bought (SEO/AEO, Content, GBP, Reviews, Backlinks) + AI-visibility, then draft the monthly client report for your review. Executes the runbooks in MONTHLY-OPS-GUIDE.md. Stops before anything ships to the client.
---

# Monthly Ops

Run the recurring retainer cycle for ONE client. `$ARGUMENTS` = client name (+ optional: which month, or
"just <add-on>" to run a single runbook). This command **executes the runbooks**; it never invents the
process - the process lives in the guide.

**Spec (the binding runbooks):** `~/projects/freelance/website-build-templates/guides/MONTHLY-OPS-GUIDE.md`
**Build-time SEO source of truth (cross-ref, do not restate):** `guides/SEO-GUIDE.md` / `PRODUCT-SEO-GUIDE.md`
**Business inputs (retainer scope, pricing, report template):** `~/projects/freelance/business`
**Client site + engine:** the client's own repo (`~/projects/freelance/<client>`).

## Step 1 - Load the client's retainer scope
Determine which add-ons this client pays for (Care base is always on). Source, in order: the client's retainer
record in `business`; a `retainer.md` in the client repo; else **ask** and confirm. Only run the
runbooks they bought - never do unpaid work, never skip paid work.

## Step 2 - Care base (always) - MONTHLY-OPS-GUIDE sec. 0
Uptime/TLS, dependency+security (engine `OPERATIONS.md` sec. 4.1), backup check, IndexNow re-index of changed
URLs, a CWV glance. Log health green/amber/red.

## Step 3 - Run each active add-on runbook (only the ones bought)
Follow the guide section for each, invoking the wired tool/skill at each step:
- **SEO/AEO Ops** (sec. 1) -> `claude-seo` audit + GSC page-2 internal links + language mining + structured-data
  check + IndexNow.
- **Content** (sec. 2) -> AnswerThePublic/GSC questions -> interview -> `content-ops` (voice-dna + anti-ai-writing)
  -> optimize per SEO-GUIDE -> `Nano Banana` image if needed -> publish -> internal links -> IndexNow. Priced
  per post; write exactly the plan's count.
- **GBP Management** (sec. 3) -> BrightLocal citations + services optimization + review replies + GBP posts +
  local rank tracking.
- **Reviews** (sec. 4) -> confirm the engine review-request flow is firing / send the monthly ask; moderate +
  respond.
- **Backlinks** (sec. 5) -> EARNED only (competitor analysis, link-worthy asset, real pitches). Never buy/exchange/
  automate links.

## Step 4 - AI-visibility check - sec. 6
Run 3-5 buyer prompts in ChatGPT/Perplexity/Gemini/Claude; record mentions vs competitors; note one action.

## Step 5 - Draft the monthly report - sec. 7
Assemble the report (LaTeX template in `business`): Health, then a section per bought add-on, then
AI-visibility, then "next month" (2-3 focuses). Keep it honest (amber/red included).

## Step 6 - Gate (HARD)
**Stop. Present the drafted report + everything queued to publish (content, GBP posts, links) for the
operator's review.** Nothing ships to the client or goes live until you approve. Then publish the approved
items, re-index (IndexNow), and send the report.

## Anti-patterns (guide sec. 10)
No bulk auto-AI content, no automated/reciprocal/paid links, no page-per-keyword, no ranking guarantees, no
shipping without review. We're the human, penalty-safe alternative to autopilot tools - that discipline is the
product.
