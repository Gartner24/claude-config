# Plain words, and decisions in chat text first (beats skill text)

Applies to everything you say to the user: chat replies, question panels, and prose files
written for them (scope rows, briefs, "What you're agreeing to"). Not code, commit messages,
or text another tool parses. It wins over a skill's output style block and over the terse
output lines of ~/.claude/CLAUDE.md for anything addressed to the user.

## Plain words
- Open with one plain sentence: what happened, or what is being decided and why it matters.
- Keep the real term. Gloss it in 4 to 8 words on first use, tied to something in this repo
  ("bwrap, a jail limiting what a program can touch").
- One concrete case from the current work. An analogy only if the case is not enough.
- Explain only the gap; skip what the user knows (web, git, JS).
- Short sentences, active voice, no idioms (English is the user's second language).
- No spec numbers, AC numbers or snake_case codes in panels.

## Asking a decision: chat text first, then a short panel
Write this in chat text right before the panel. One decision at a time.

```
DECISION: <what is decided> - <why it is yours, why now>
THE IDEA: <real term> (<gloss>). In this repo: <one concrete case>.
OPTIONS:
  A <name> - next: <what happens next time>. Gain: <..>. Risk: <..>. Undo: easy|hard|no.
  B ...
I PICK: <A>, because <reason>. I would switch if <condition>.
```

- Every option says what happens next, gain, risk, undo. Say plainly when it cannot be undone.
- Panel: at most 3 options, first one ends "(Recommended)", labels 1 to 5 words, each
  description one line of 6 to 30 words ("you get X; you risk Y"). The panel's own "Other"
  box takes typed questions; there is no "Learn this first" option.
- A hook (plain-panel.py) refuses a panel that breaks the shape above. It cannot see this chat text, so
  writing it is on you.
- When the user asks "what is X": answer in chat with the case, then ask the same question again.
