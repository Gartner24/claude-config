---
name: project-finder
description: Use when the user needs to find, choose, or validate a topic for a thesis, capstone, degree project, or research proposal - topic open or undecided, ideas discarded, "what should I do my thesis on", "is this idea original", "does this already exist", "will this be accepted as a thesis". Also use when an idea exists but has no research question or measurable result yet.
---

# Project Finder

Find and validate a degree-project idea. Topic-agnostic: the method is the same for any field.

## Setup (ask once, then reuse)

Record these at the top of the working file. Never assume them.

| Field | Example | Default |
|---|---|---|
| Local context | country / region the gap targets | UNKNOWN - ask |
| Institution | library access for paywalled papers | UNKNOWN - ask |
| Modality | applied project / research project / other | UNKNOWN - ask |
| Hard requirements | e.g. software mandatory, hardware optional | UNKNOWN - ask |
| Discarded ideas | keep the list, do not re-propose | none |

## 1. The shape of every thesis

**Question -> Method -> Measurable result.**

- **Question** - what you do not know at the start and will know at the end. Answerable, not obvious in advance.
- **Method** - what you do to answer it. Everything you build, code, deploy, wire, or measure lives here. 70-80% of the time.
- **Measurable result** - the evidence. Numbers, comparisons, measurements.

**The software is not the thesis, it is the instrument.** An astronomer's thesis is not "I built a telescope", it is what they found with it.

- Fails: "I developed a platform that does X." -> panel asks: so what? better than what? how do you know?
- Works: "Can X achieve Y versus current method Z? I built it, tested it, and got this result."

If a candidate idea has no question and no measurable result, it is not yet a thesis. Say so.

## 2. Result types that count

Beating the state of the art is not required. Any of these is a valid result:

- **Comparison** - my approach vs the existing one (speed, cost, accuracy, energy).
- **Accuracy** - how well the system matches known ground truth.
- **Characterization** - measuring something nobody has measured. The data *is* the result.
- **Feasibility with numbers** - proving the "impossible" is possible, with metrics.
- **User study** - people complete the task faster, with fewer errors.

Almost anything worth building can become a thesis. The move is deciding **up front what gets measured and against what**.

## 3. Problem first, solution second

Do not start from "I want to build software". Start from a real problem. The solution follows and will be software anyway.

Do not lock into "it has to be an app". Fix the problem first and the form falls out.

## 4. Two valid ways an idea qualifies

1. **Genuinely original** - nobody has done it. Hard, valuable.
2. **New value or new scope** - it exists elsewhere, you add something. The common case: **never applied in the user's local context**.

Search for **both**, not just the first. A well-executed adaptation is a legitimate thesis. Do not stall chasing 100% originality.

## 5. The two search boxes

### Box 1 - Industry/consultancy reports: where there is MOVEMENT

- Sources: McKinsey, Deloitte, Gartner, BCG, PwC, Capgemini, plus sector-specific bodies.
- **Go to the original report, never the news article about it.** Numbers distort in retelling.
- **The right source changes with the field.** Tech -> Gartner, Deloitte. Agriculture -> McKinsey plus academia. Health -> WHO, ministries. Pick per topic.
- **Limit:** these show general trends ("this is growing"), not the specific broken thing.

### Box 2 - Academic studies: the SPECIFIC GAP

This is where the concrete gap lives and where originality gets confirmed.

- Paywalled: ScienceDirect, Springer, Wiley.
- Open: MDPI, arXiv, IEEE (partly), DOAJ, Google Scholar, Semantic Scholar.

**Paywall protocol - the division of labor:**

- Claude **cannot** read full text behind ScienceDirect / Springer / Wiley. Only abstracts, plus open-access full text.
- Claude filters by abstract and flags what is worth the user's time, with title, authors, year, venue, DOI/URL, and why it matters.
- **The user** logs in with their institutional account, downloads the full paper, and judges viability.
- Neither does the other's job. Never claim to have read a paywalled full text.

## 6. The winning play

Find something that **already works in developed countries** -> find the gap: **"this cannot be used here without research or adaptation first"** (geography, climate, infrastructure, regulation, cost, data availability).

That yields both things at once: a **real problem** (already proven useful there) and a **question to answer** (how to make it work here). Fits applied-project modality cleanly.

## 7. Anti-plagiarism duty

Models are trained on what already exists, so they bias toward proposing the known as if it were new. Counter it:

- **Search real sources and cite them.** No ideas invented from memory.
- **State plainly when something ALREADY EXISTS** so the user does not copy it, versus when there is a genuine gap.
- The distinction that matters: **"already exists -> do not copy"** vs **"gap -> opportunity"**.
- Never invent a paper, author, DOI, or statistic. Unknown -> say UNKNOWN.

If it is already done, say so immediately and look for the angle that is still free.

## 8. Is this idea the one

- **Does it light the user up?** Two semesters of carrying it. Motivation is a hard requirement, not a nicety.
- **Does it meet the program's requirements?** (from Setup)
- **Does it have thesis shape?** Question -> method -> measurable result.
- **Original or new scope?** Either is enough.
- **Is it already done?** The originality check.

Any "no" -> keep searching or change the angle. Do not talk the user into a candidate.

## 9. Process

1. **Pick an area that excites them.** Do not force it. Enthusiasm comes from exposure, not from a list - offer varied concrete examples, not a menu of categories.
2. **Box 1** - where is the movement in that area.
3. **Box 2** - the specific gap: original **or** adaptation-to-local-context.
4. **Claude filters** abstracts, flags what is worth reading.
5. **User downloads** full papers with institutional access and judges viability.
6. **Originality check** - already done? Then find the free angle.
7. **Only now define the PROBLEM** -> then the solution.
8. **Justification is written last.** It is the easy part, assembled from Box 1. Do not optimize for "easy to justify"; pick what excites and back it up afterward.

## 10. Candidate record

Keep one block per surviving candidate in the working file:

```
CANDIDATE: <short name>
Area:
Question:
Method (what gets built):
Measurable result + baseline to compare against:
Result type: comparison | accuracy | characterization | feasibility | user study
Qualifies as: original | new scope (local context)
Prior work found: <citations, with DOI/URL>
Already exists?: yes/no + which part
Blocking unknowns:
Excitement (1-5):
Status: exploring | user validating full texts | discarded (reason)
```

## Common mistakes

- Proposing a build with no question attached. Every candidate needs the full triple.
- Presenting a known product/paper as a novel idea. Check before proposing.
- Citing a paper whose abstract was never actually retrieved.
- Jumping to "an app that..." before the problem is defined.
- Pushing a candidate the user is lukewarm about because it looks easy to justify.
- Re-proposing something already on the discarded list.
