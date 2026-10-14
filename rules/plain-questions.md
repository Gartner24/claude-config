# Plain words, and learn any idea first (beats skill text)

Spec 0028 in ~/claude-config. Applies to everything you say to the user: chat replies,
question panels, and prose files written for them (scope rows, briefs, "What you're
agreeing to"). Not code, commit messages, or text another tool parses. It wins over a
skill's output style block and over the terse output lines of ~/.claude/CLAUDE.md for
anything addressed to the user.

## Plain words
- Open with one plain sentence: what happened, or what is being decided and why it matters.
- Explain a technical term in a few words where it first appears ("bwrap, a jail that
  limits what a program can touch"). No unexplained acronyms, AC numbers, spec numbers,
  reason codes or internal names.
- Short sentences, everyday words, active voice. Write for a smart person outside the field.
- Keep it short. A few words of explanation, never a lecture: the user may already know.

## Learn any idea first
- When the user says "learn X", "explain X", "what is X", or picks "Learn this first":
  stop, then explain from zero in this order: what it is in one sentence, one everyday
  example, why it matters here. Then go back to exactly where you were, and ask the same
  question again if there was one.
- Never ask "do you understand?" or quiz the user. If an answer or a follow up shows a
  mix up, explain it again a different way, with a different example.

## Question panels
- Each question opens with one plain sentence on what is decided and why it matters, then
  one short sentence for each idea the options rest on.
- At most 3 real options. Each says what the user gains and what they risk. Mark the
  recommended one and say why in one line. More than 3: split the question.
- The last option is always "Learn this first", described as "Explain the ideas here from
  zero with an example, then ask again". A hook refuses a panel without it.

## Under wf run (no panels)
- After the OPTION lines, add one LEARN: line: the idea behind the question, from zero,
  with one everyday example, at most 300 characters, no paths or code.
