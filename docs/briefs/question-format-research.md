# How to ask the owner decisions (research, 2026-10-22)

Research agent report (14 sources, confidence medium). The format is a synthesis, not yet tried on the owner.

## Bottom line
No teaching behind a click. Put it in chat text right before the panel: one concrete case, a short gloss for each term, what happens next for each option. Then a short panel. Drop "Learn this first". The hook stops banning words and checks that the explanation exists.

## Why the current approach fails
1. People rarely click optional help ("paradox of the active user", Carroll and Rosson 1987; NN/g).
2. Explanation apart from the options = split attention; put it next to them (Chandler and Sweller 1991, 1992).
3. "From zero" hurts people who already know the area (expertise reversal, Kalyuga et al. 2003). Memory `explain-with-context.md` agrees: a case walk worked, an analogy did not.
4. The hook bans words (`plain.jargon()`), even "guard" and "park" in mod names; the owner needs the real term plus a gloss.
5. The panel cannot hold teaching (Claude Code 2.1.308): 2-4 options, labels 1-5 words, one-line descriptions, `preview` single-choice only; "Learn this first" uses one of four slots.
6. Option count is not the problem (Scheibehenne et al. 2010); knowing what each option leads to is (Cochrane 2024 decision aids; Elwyn 2013 Option Grids).

## New format: chat text first, then a short panel
```
DECISION: <what is decided> - <why it is yours, why now>
THE IDEA: <real term> (<4-8 word gloss>). In this repo: <one concrete case>.
OPTIONS:
  A <name> - next: <what happens next time>. Gain: <..>. Risk: <..>. Undo: easy|hard|no.
  B ...
I PICK: <A>, because <reason>. I would switch if <condition>.
```
Panel: one or two questions, recommended option first with "(Recommended)", each description one line "you get X; you risk Y", `preview` only for a visible before/after, no "Learn this first" (the automatic "Other" box takes typed questions).

### Example
```
DECISION: what wf does when bwrap is missing - only you can trade safety for convenience.
THE IDEA: bwrap (a jail limiting what a program can touch). In this repo: every wf step runs inside it,
  so a step cannot read ~/.ssh.
OPTIONS:
  A Refuse - next: `wf run` stops and prints the install command. Gain: no step runs unjailed.
    Risk: a night run does nothing. Undo: easy.
  B Run anyway, warn - next: steps run with full access to your home folder. Gain: work continues.
    Risk: a bad step can read keys. Undo: no, a leaked key stays leaked.
I PICK: A, because B fails open. I would switch if bwrap kept breaking on updates.
```

## Rules to replace plain-questions.md
1. Every panel follows the DECISION / IDEA / OPTIONS / I PICK text; the panel only collects the answer.
2. Keep real terms; gloss each on first use in 4-8 words, tied to something in this repo.
3. One concrete case from the current work; analogy only if the case is not enough.
4. Every option: what happens next, gain, risk, undo. Say plainly when it cannot be undone.
5. Recommend one with a reason and what would change your mind.
6. Explain only the gap; skip what the owner knows (web, git, JS).
7. One decision at a time. Short sentences, active voice, no idioms (English is the owner's second language).
8. "What is X" from the owner: answer in chat with the case, then ask the same question again.
9. No spec numbers, AC numbers or snake_case codes in panels.

## What the hook should check
- Drop: the "Learn this first" requirement and the word ban.
- Keep: at most 3 options; ban on internal codes.
- Add (panel): first option ends "(Recommended)"; each description 6-30 words; labels 1-5 words.
- Add (preceding text, from `transcript_path`): last assistant text has `DECISION:`, `OPTIONS:`, `I PICK:` and one `Undo:` per option.
- Add (terms): any word the old jargon list flags appears in that text followed by "(" and a gloss.
- Tests: `--test` fixtures with and without the explanation text.

Not checked: whether the description-with-preview display bug is fixed; exact header length limit (third party says 12).
