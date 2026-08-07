---
description: De-slop any text - run humanizer (33 named AI tells) then anti-ai-writing (voice-aware), then enforce the ASCII/no-em-dash house rule. Works on text you wrote, text Claude wrote, or a file path.
---

# Polish

De-slop the text in `$ARGUMENTS`. It may be pasted text, a file path, or empty.

If `$ARGUMENTS` is empty, ask what to polish. If it is a path, read the file and edit in place.

This is the gate `/write` and `/academic` call as their required final step. It also stands alone -
run it on anything, including prose you wrote yourself.

## Pass order - it matters

1. **`humanizer`** - mechanical sweep for the 33 named tells from Wikipedia's "Signs of AI writing":
   inflated symbolism, promotional language, superficial `-ing` analyses, vague attributions,
   em dash overuse, rule of three, AI vocabulary, negative parallelisms, filler phrases.
2. **`anti-ai-writing`** - voice-aware pass. If a `voice-dna.md` exists for this client or project,
   load it first and edit toward that profile, not toward generic "natural."
3. **House rules** (from `~/.claude/CLAUDE.md`, non-negotiable):
   - ASCII only. No em dashes, en dashes, smart quotes, Unicode bullets, arrows, or ellipsis chars.
     Plain hyphens and straight quotes.
   - No sycophantic openers or closing fluff.
   - No inline prose padding. Cut anything that adds length without adding information.

Run them in that order. humanizer first because it is mechanical and high-recall; anti-ai-writing
second because it is the judgment pass and should see already-cleaned text. Reversing this wastes
the voice pass on tells the sweep would have caught anyway.

## Register guard

Do not flatten register in the name of sounding human.

- **Academic and technical prose** legitimately uses formal hedging ("these results suggest"),
  passive voice in method sections, and precise repetition of a defined term. Leave them.
  Strip inflated symbolism and promotional language; keep the formality.
- **Commit messages and issues** are terse by design. Do not pad a one-line commit into a paragraph
  because it "reads better."
- The target is *this author writing clearly*, not *the median blog post*.

## Verify before returning

Run this on the result. It must print nothing:

```bash
LC_ALL=C grep -n '[^ -~]' <file>
```

Any hit is a non-ASCII character that survived - fix it and re-run. If the text was pasted rather
than in a file, write it to the scratchpad and check there.

## Output

Return the polished text. Then, in at most three lines, list what changed by category
(e.g. "12 em dashes, 3 promotional phrases, 1 rule-of-three"). No before/after essay.
If nothing needed changing, say so in one line - do not invent edits to look useful.
