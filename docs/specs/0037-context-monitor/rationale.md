# 0037 rationale

## Why
Personal plan row 6: `hooks/gsd-context-monitor.js` comments say it warns at 35% and 25% remaining, the code uses 10% and 5%. Done when one is picked and comments and code agree. Reading the code showed a bigger problem: the monitor depends on a bridge file nothing writes any more, so neither pair of numbers has ever produced a warning in these sessions. Picking numbers without fixing that would close the row and change nothing, so the spec does both.

## Decided without asking (2026-10-14)
Per `docs/briefs/finish-runner-today.md`, the recommended option was taken for every question.

| Question | Options | Pick |
|---|---|---|
| Threshold unit | percent remaining (35/25, or 10/5); tokens used | Tokens used. Your rules are in tokens (150k nudge, 700k autocompact, `~/.claude/CLAUDE.md` `### Context` and `05-new-workflow.md` section 5), and a percent of a 1M window means something different on a 200k one. |
| Which numbers | the comment's 35/25; the code's 10/5; 150k and autocompact minus 50k | 150k and 650k. 10/5 never fire before autocompact (700k used = 30% remaining); 25 is past it; 35 alone matches 650k. 150k is the rule you already follow by hand, so the hook only reminds you of it. 50k before autocompact leaves room to write the rollover handover. |
| How often | every 5 tool calls while low (today, `gsd-context-monitor.js:28`, `:115`); once per level | Once per level (150k, then every 100k, then 650k). From 150k to 650k at a debounce of 5 calls it would repeat hundreds of times. |
| Where the size comes from | restore the bridge in the status line (`wf auto bar`); switch back to gsd's status line; read the transcript | The transcript. It needs no status line at all and gives tokens directly; the bridge only ever carried a percent. Adding a bridge to `wf auto bar` would tie a gsd hook to the runner, and gsd's status line would replace jjstack's. |
| Edit the gsd file or own a copy | edit in place; own copy under a new name | Own copy, `hooks/context-monitor.js`. The gsd file carries `gsd-hook-version: 1.34.2` and gsd's update check flags changed hooks, so an in-place edit would be reverted. A new name keeps the two apart. |
| GSD specific parts | keep the `.planning/config.json` opt out and the `STATE.md` message variants; drop them | Drop them. No repo here uses `.planning/`; the messages now name your own rule instead. |
| Under `wf run` | warn; silent | Silent. Each `wf` step is a fresh session with a budget cap, and the warning tells the model to inform a user who is not there. |
| Message tone | advisory (gsd's choice, its issue 884); directive | Directive, naming the rule: your `CLAUDE.md` asks Claude to run `/rollover` itself past 150k, so the hook repeats that instruction rather than a vaguer one. |
