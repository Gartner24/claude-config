# Runner handoff (beats skill text)

The user wants the runner to do the building and Claude to tell them every manual step. They
will not remember the flow; you do.

## After /architect accepts a spec
1. If the repo's scope header says `**Autopilot:** allowed`, tag the feature heading `· auto`,
   put `/sync` as its last box, and mark any step that writes `~/.claude` or `.git/hooks` as
   `· waits on you`. When that step is one of the four `wf finish` shapes (`rules/scope-contract.md`),
   write it one step per box with ` · live` too; a human step goes in its own box without ` · live`.
   Commit.
2. Check runner readiness and list only what is missing, each with the exact command:
   - scope header `**Autopilot:** allowed` (the user sets it; say the line to add);
   - repo trusted: `wf allow <repo path>` (check `~/.config/wf/allowed.json`);
   - current branch is not `main`/`master` (give `git -C <repo> switch -c feat/<slug>`);
   - web app with no `- app start:` / `- app url:` in AGENTS.md (ask for them);
   - UI feature with no locked `design.md` (route to `design`).
3. Batch first: if any other feature in this repo's plan, or in a hub row that names this repo
   (work, freelance, personal), still says `needs a decision`, do not hand off to the runner yet.
   Name the next one and run its `/architect` in this session (or, past ~150k tokens, `/rollover`
   with that `/architect` as the next command). Only when none is left, go to step 4.
4. End the turn with: "Ready for the runner: type `wf run <repo>` in a terminal (or `wf run`
   for every trusted repo)." This replaces the `/clear` handoff for a queued feature.

Never route an accepted spec to `/develop` in chat because the repo is not runner ready. A missing
`Autopilot: allowed` or `wf allow` is a setup step to list in step 2, not a reason to build in
chat. Build in chat only when the user says so for that feature.

## At session start in a repo
Run `wf queue` (read only). If anything finished, parked or waits on you since the last run,
say it first in one short list, with the next command for each: review and merge for finished
work, the fix for a park, the box for a waits-on-you step.

## After a wf run ends
When the user says a run ended, read `wf queue` and the run's `run.json`, then give the morning
steps: what was built, the review command for this repo (`## Review Rules`), and the merge and
push commands. Never push or merge without the user's yes.
