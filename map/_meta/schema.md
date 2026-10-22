# Map schema

The rules every card in the map folder follows (spec 0072). Cards are short on purpose: one card per part, loaded only when a change touches that part.

## Kinds
- Object card (one file per part): a part of the repo that exists (a folder, a file family, a tool). Template: [object.md](../_templates/object.md).
- Process card (one file per process): something done to the repo, in steps. Template: [process.md](../_templates/process.md).
- [effects](../effects/CONTEXT.md): what a change to one part also moves in another.

## Rules
- A card is at most about 60 lines and says what to do, not why (the why lives in the spec the card names).
- Every `path` or `path:line` a card cites in backticks or a link must exist. `python3 scripts/ref-check.py check <card files>` lists the ones that do not.
- Old `AGENTS.md` lines and where each went: [line-homes.md](line-homes.md).
- A rule appears in one card only. Other cards link to it.
- ASCII only, same as the rest of the repo markdown.
- A card changes in the same commit as the part it describes.
