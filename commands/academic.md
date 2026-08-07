---
description: Write academic prose - thesis chapters, papers, abstracts, literature reviews, methodology and results sections. Enforces question/method/measurable-result structure, refuses invented citations, then runs the /polish gate with the academic register guard on.
---

# Academic

Produce the academic writing described in `$ARGUMENTS`.

If `$ARGUMENTS` is empty, ask what section and for which project.

## Step 0 - Is there a project yet?

If the topic is undecided, or the piece has no research question, **stop and run `project-finder`
first.** There is nothing to write until there is a question. Come back here once the candidate
record has a Question, a Method, and a Measurable result.

## Step 1 - Set the frame (ask once, reuse)

| Field | Why it changes the writing |
|---|---|
| Language | Spanish or English. Affects register, connectives, and citation conventions. |
| Citation style | APA / IEEE / Vancouver / ABNT. Affects in-text form and reference list. |
| Institution + program | House template, required sections, page limits. |
| Section being written | Abstract, intro, lit review, method, results, discussion, conclusion. |
| Audience | Advisor draft, committee submission, or journal. |

Unknown means ask, not guess. A thesis rejected on format is rejected regardless of content.

## Step 2 - Structural discipline

Every piece stays anchored to the same spine, from `project-finder`:

**Question -> Method -> Measurable result.**

- **Intro** ends on the question. If a reader cannot state the question after reading the intro,
  the intro failed.
- **Method** is where everything built, coded, deployed, or measured lives. It is the longest
  section. Write it so someone else could repeat it.
- **Results** report what was measured against what baseline. Numbers, not adjectives.
- **Discussion** interprets. It does not introduce new results.
- The software is the instrument, never the contribution. "I built X" is not a finding;
  "X achieved Y against baseline Z" is.

## Step 3 - Citation discipline (hard rules)

- **Never invent a citation.** Not an author, not a year, not a title, not a DOI, not a page
  number, not a journal. A fabricated reference is the single fastest way to fail a defense.
- Cite only sources actually retrieved in this session or supplied by the user. If a claim needs
  a source you do not have, write `[CITATION NEEDED: <the specific claim>]` and leave it. A visible
  gap is recoverable; a fake reference is not.
- Behind a paywall (ScienceDirect, Springer, Wiley) you see the abstract only. **Never write as
  though you read the full text.** Mark it `[ABSTRACT ONLY - verify full text]` so the user knows
  to pull it with institutional access.
- Quoting means exact words plus a locator. If you cannot reproduce it exactly, paraphrase and
  cite instead.
- Say plainly when prior work already covers something. "This already exists -> do not copy" versus
  "this is the gap" is the distinction that protects the whole project.

## Step 4 - Polish gate (required)

Run `/polish`, with the **academic register guard** explicitly on.

Strip: inflated symbolism, promotional language ("groundbreaking", "revolutionary", "seamlessly"),
filler, vague attributions ("studies show", "experts agree", "it is widely known") that are not
backed by an actual citation, em dashes and any non-ASCII.

Keep: formal hedging ("these results suggest", "this may indicate"), passive voice in the method
section, and precise repetition of a defined technical term. Academic writing is supposed to sound
like this. Do not let the de-slop pass sand it into a blog post.

## Step 5 - Output

Markdown by default. Run `make-pdf` when the user wants something submittable.

End with:
- Every `[CITATION NEEDED]` and `[ABSTRACT ONLY]` marker, listed, so they cannot be missed.
- Word count against the limit if one was given.
- What you could not verify.

## Not this command

- Choosing or validating the topic -> `project-finder`
- Commits, PRs, issues, engineering docs -> `/write`
- Marketing or blog prose -> `content-ops` / `article-writing`
