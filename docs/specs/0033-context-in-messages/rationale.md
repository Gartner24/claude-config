# 0033 rationale

## Decided without asking (2026-10-14)
Each question was answered with the recommended option, as agreed in docs/briefs/finish-runner-today.md.

1. **Links on ntfy?** Options: links on both channels; links only on Telegram. Pick: Telegram only. An ntfy topic sits on a public server; repo and branch names in links are exactly what the phone scrub keeps off it.
2. **Where does the why for a case question come from?** Options: ask a model; a fixed line per case row. Pick: a fixed line per row (`plain.WHY`); case questions are asked by the runner, not a call.
3. **A path named only in blocked text?** Options: never use it; use it only inside the repo. Pick: only inside the repo. The text is call output, and F1 still asks you before anything is allowed; never writable paths stay refused.
4. **Too long for one Telegram message?** Options: split the question; cut its parts. Pick: cut `did` first, then `steps`, so the question and its buttons stay one message your swipe reply can find.
5. **Commit and file counts in the report?** Options: from GitHub; from the local branch. Pick: local git (`base_sha..branch`), which the runner already reads and which needs no network.
6. **The question's 4 letter id?** Options: hide it; label it on first use. Pick: label it, since typed replies still need it.
