# 0028 · Understand everything: rationale

## Context

Scope feature 23, widened 2026-10-13: everything Claude says to you, in every session and in the runner's reports and phone questions, is in words you can follow, with a way to learn any idea first. What exists today:

- `rules/plain-questions.md` (live in `~/.claude/rules/`, always loaded) asks for plain wording in questions and a from zero explanation when you say you do not follow. It covers questions only, and the learn path only after you are already lost.
- Nine vendored skills carry an `OUTPUT-STYLE` block (`~/.claude/skills/{develop,check,test,debug,sync,document,audit,scope,architect}/SKILL.md`) asking for plain language. They are overwritten on every pull, so nothing can be added there (the same reason `rules/check-gates.md` exists, spec 0015).
- The runner speaks to you in its own words, and today those are its internal codes. A case question is built as `f"{reason}: {flat(detail)}"` (`runner/run.py:1387`), so the phone reads `verify_failed: ...`. The report prints `parked: <feature>: <reason>` with the same codes (`runner/report.py:142`), and its head lists stop reasons by code (`runner/report.py:107`). A question a call asks reaches the phone as its question line and option labels only (`runner/ntfy.py:249` to `:266`); any explanation the model wrote above the `DECISION NEEDED:` line never leaves the machine, because the prompt tells it to put explanations there (`runner/run.py:146`).

## Research

Sources opened on 2026-10-13. Quotes are only from these pages.

1. **Define a term where you use it, and do not leave out the term.** Digital.gov, *Avoid jargon* (https://digital.gov/guides/plain-language/principles/avoid-jargon): "When we say not to use jargon, we're not advocating leaving out necessary technical terms." and "When you have no way to express an idea except to use technical language, make sure to define your terms." Its heading "Define a word where you use it" argues against a separate glossary. Digital.gov, *Accessibility for content designers* (https://digital.gov/guides/accessibility-for-teams/content-design): "Include in-line definitions for scientific, legal, or technical terms that you must use." and defining terms in line "creates a much more continuous reading experience for the user."
   Used for: the rule keeps technical words that carry meaning and glosses each one in a few words at first use (AC-1). The existing rule already did this for questions; it now covers every message.

2. **Plain style basics.** Digital.gov, *Writing for understanding* (https://digital.gov/guides/plain-language/writing/): content is easier to understand with "Shorter words", "Short sections", "Active voice", "Present tense". Digital.gov, *Style* (https://digital.gov/guides/plain-language/writing/style), on abbreviations: they "constantly demand the reader to look back at earlier pages", and "Always define an abbreviation the first time you use it."
   Used for: the "Plain words" section of the rule, and putting `AC-<n>` and `spec <nnnn>` on the jargon list (AC-7): in a message to you they are abbreviations you must look up elsewhere.

3. **Progressive disclosure: a short first layer, more on request, and an obvious way to get it.** Nielsen, *Progressive Disclosure*, NN/g (https://www.nngroup.com/articles/progressive-disclosure/): "Initially, show users only a few of the most important options." then "Offer a larger set of specialized options upon request." It names two things to get right: the split ("the primary list can't contain too many options") and that "It must be obvious how users progress from the primary to the secondary disclosure levels". It also says the smaller first display helps advanced users too: "For advanced users, the smaller initial display also saves them time".
   Used for: a short gloss in line plus a full explanation only when asked (the rule), an explicit visible "Learn this first" option instead of a hidden convention (AC-3, AC-10), and at most 3 real options per question (AC-3).

4. **Do not slow down people who already know it: the expertise reversal effect.** Introduction to the *Instructional Science* special issue on the expertise reversal effect (2009) (https://link.springer.com/article/10.1007/s11251-009-9102-0): "What could be beneficial for beginning learners might get detrimental for advanced learners." and "The major instructional design implication of these studies is the need to adjust instructional methods and procedures as learners acquire more experience in a specific domain." Tetzlaff, Simonsmeier, Peters and Brod, meta-analysis, *Learning and Instruction* 98, 2025 (https://www.sciencedirect.com/science/article/pii/S0959475225000660): "Low prior knowledge learners learn better from high-assistance instruction (d = 0.505). High prior knowledge learners learn better from low-assistance instruction (d = -0.428)." and "providing novices with assistance has a stronger effect than withholding assistance from experts."
   Used for: the long explanation is opt in, the in line gloss is a few words, and the rule says "never a lecture". The asymmetry is why the learn path is offered on every question rather than only when Claude guesses you need it: missing a novice costs more than one extra option costs an expert.

5. **Explain from zero with a concrete example.** The Learning Scientists, *Learn to Study Using... Concrete Examples* (https://www.learningscientists.org/blog/2016/8/25-1): "Abstract ideas can be vague and hard to grasp. Moreover, human memory is designed to remember concrete information better than abstract information". The same group's podcast notes (https://www.learningscientists.org/learning-scientists-podcast/2018/1/3/episode-10-concrete-examples): "It's important for us to also make the link between the concrete examples to the abstract ideas."
   Used for: the explanation order in the rule (what it is, one everyday example, why it matters here) and the `LEARN:` line asking for one everyday example (AC-8).

6. **Checking understanding without testing the person.** AHRQ, *Use the Teach-Back Method: Tool 5*, Health Literacy Universal Precautions Toolkit (https://www.ahrq.gov/health-literacy/improve/precautions/tool5.html, text read through the search tool's page extract): "Remember, you are checking how well you explained something, not testing the patient." "'Do you understand?' and 'Does that make sense?' are NOT teach-back questions. Patients are likely to answer 'yes' whether they understand or not." and "If teach-back uncovers a misunderstanding, explain things using a different approach".
   Used for: the rule bans "do you understand?" and quizzes. Asking you to say it back would slow every expert answer (finding 4), so the check is your answer itself: when it or a follow up shows a mix up, Claude explains again a different way. This is the one teach-back idea that costs an expert nothing.

## Options considered

### Option 1: grow the rule, add a panel hook, plain words and a learn line in the runner (chosen)
**Pros**: reaches every session through an always loaded rule, so vendored skills need no edit; the hook makes "every panel has a learn option" checkable instead of hoped for; the runner's own text, which no rule can reach, becomes plain through a tested table; the phone gets the explanation that today stays on the machine.
**Cons**: a hook can refuse panels and cost a retry; 13 percent of past questions had 4 options and must be split; the report's words change, so its tests change.

### Option 2: rule only
**Pros**: one file, no code.
**Cons**: the Done when needs a panel in a fresh session to offer the learn path, and nothing can show a rule was followed. Runner text is written by code, not by Claude, so a rule cannot change it.

### Option 3: edit the vendored skills' output style blocks
**Cons**: overwritten on every pull (spec 0015's reason for `check-gates.md`). Rejected.

### Option 4: a glossary file Claude links to
**Cons**: finding 1 argues for defining words where they are used, not in a list elsewhere; a phone note cannot open a local file. Rejected.

## Decided without asking (2026-10-13)

Per `docs/briefs/finish-runner-today.md` (the conductor answers design questions with the recommended option), each question, its options, and the pick:

1. **Where does the rule live?** Options: grow `rules/plain-questions.md`; a new `rules/plain-words.md`; `~/.claude/CLAUDE.md`. Pick: grow `rules/plain-questions.md`, keeping its file name. The scope row says it grows that file, `NOTICE.md` and `rules/review-fix.md` already name it, and a new file would leave two rules saying overlapping things.
2. **Edit `~/.claude/CLAUDE.md` too?** Options: add a pointer line; leave it. Pick: leave it. Rules are always loaded; the rule says it wins over CLAUDE.md's terse output lines for text addressed to you, and those lines (code first, no inline prose) still govern code answers.
3. **How does a panel offer the learn path?** Options: an explicit last option "Learn this first"; rely on the harness's free text or "Chat about this" path; a line in the question text. Pick: an explicit option (finding 3: the way to the second layer must be obvious). Cost: one of 4 option slots.
4. **Questions with 4 real options?** Options: split them; allow 5 by dropping the learn option there; exempt them. Pick: split. Probe P1 found 126 of 953 past questions at 4 options; NN/g's "can't contain too many options" supports fewer.
5. **Enforce with a hook?** Options: PreToolUse hook that refuses; rule only; a Stop hook audit. Pick: the refusing hook, because a rule alone cannot be checked (the Done when needs it to hold in a fresh session). P3 confirms it works; if it does not, fall back to the rule alone.
6. **Check jargon in panels too?** Options: yes when the runner's word list can be imported; no. Pick: yes, skipped when the import fails, so the hook never depends on the runner being installed.
7. **Check understanding?** Options: ask you to say it back; ask "is that clear?"; no check, explain again on a sign of a mix up. Pick: the last (finding 6 and finding 4).
8. **Phone: how does a call's question carry teaching?** Options: a `LEARN:` line in the ping; a second note with the explanation; nothing, the report only. Pick: a `learn:` line in the same ping (one buzz, the explanation next to the question). Cut to 300 characters to keep the note short.
9. **Phone: a learn path beyond that line?** Options: a `learn this first` option that resumes the call to explain more and ask again; none. Pick: the option. It reuses the existing resume (one call, counted against the feature's call cap), so it needs no new machinery.
10. **Runner case questions (spec 0021): a learn option too?** Options: same option; the learn line only. Pick: the learn line only. These questions are written by code with a fixed explanation per reason, and a resume would have no session that knows more. The full detail stays in `wf` and `report.txt`.
11. **Report words: keep the codes beside the plain words?** Options: plain only; plain plus the code in brackets. Pick: plain only in anything you read; codes stay in run.json and log.txt for debugging.
12. **A model question full of jargon under `wf run`?** Options: record and go on; rewrite it; refuse and rerun. Pick: record and go on (spec 0021, never stop). The record shows whether the prompt line works.
13. **Corpus for the panel claim?** Options: every panel asked after the hook install, from local transcripts; a fixture set. Pick: the real transcripts (rule `lessons.md`: a universal claim needs a corpus assertion on the real artifact), with zero panels counted as a failure rather than a vacuous pass.
14. **The `wf` screen lines?** Options: in this spec; follow up. Pick: follow up; the request named reports and phone questions.

## Consequences
- Panels get one extra option and sometimes split into two questions.
- The morning report reads differently; anyone matching its old words (the `runner-handoff.md` rule reads it as prose, no parser) is unaffected.
- A `learn this first` answer on the phone costs one call of the feature's cap.
