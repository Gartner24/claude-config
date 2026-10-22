# 0033 rationale

## Decided without asking (2026-10-14)
Each question was answered with the recommended option, as agreed in docs/briefs/finish-runner-today.md.

1. **Links on ntfy?** Options: links on both channels; links only on Telegram. Pick: Telegram only. An ntfy topic sits on a public server; repo and branch names in links are exactly what the phone scrub keeps off it.
2. **Where does the why for a case question come from?** Options: ask a model; a fixed line per case row. Pick: a fixed line per row (`plain.WHY`); case questions are asked by the runner, not a call.
3. **A path named only in blocked text?** Options: never use it; use it only inside the repo. First pick: inside the repo. Security review: never use it, since the model would choose which path you are asked to allow; only a denial the call's own permission record holds counts.
4. **Too long for one Telegram message?** Options: split the question; cut its parts. Pick: cut `did` first, then `steps`, so the question and its buttons stay one message your swipe reply can find.
5. **Commit and file counts in the report?** Options: from GitHub; from the local branch. Pick: local git (`base_sha..branch`), which the runner already reads and which needs no network.
7. **Paths in blocked steps on Telegram?** The phone scrub drops every token with a `/`, which would cut the very command a step needs. Options: scrub steps like other text; keep paths in steps on Telegram only, block list still applied. Pick: keep them on Telegram (your private chat with your bot); ntfy scrubs as today.
8. **The report's next step with its reason?** Options: change the run wide `next:` line; add the reason to each built line. Pick: each built line, which is per feature as asked; the run wide line stays as the one command to type.
6. **The question's 4 letter id?** Options: hide it; label it on first use. Pick: label it, since typed replies still need it.
9. **Security review: call text in questions that grant something.** Options: show it like any other context; show the runner's facts and fixed reason, the call's words only quoted as unverified, no steps. Pick: the latter, so a repo or PR that steers the call cannot steer your yes.
