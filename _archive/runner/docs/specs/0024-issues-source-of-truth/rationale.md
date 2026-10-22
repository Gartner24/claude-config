# 0024. Issues and mixed source of truth (rationale)

## Context

Scope feature 16: per repo `**Source of truth:** scope | issues | mixed`. With `issues` or `mixed`, the runner rereads the linked GitHub issue before every step; a change after the spec was written is asked about with the diff; a `scope` repo never calls GitHub. Brief: [docs/briefs/finish-runner-today.md](../../briefs/finish-runner-today.md) item 15. The scope row says the feature "parks"; spec 0021 turned every park into a question with the rest going on, so this spec asks.

What exists today:
- Spec 0003 parses and validates the header (`runner/wf.py:25-27`, `95-131`), and says `issues` and `mixed` have no behavior until this feature (spec 0003 line 146).
- `wf run` calls cannot reach GitHub: forge hosts and the repo's remotes are denied in the sandbox (`runner/run.py:69-70`, `1027`, `1044`), `GH_TOKEN` and friends are dropped from the call env (`runner/run.py:57`, `2979`), and `~/.config/gh` is unreadable (`runner/run.py:60`). The runner process itself runs with your environment and login.
- Each step is one `self.call(...)` inside `loop` (`runner/run.py:2484-2536`); the guard check right before it (`2501-2503`) is where a per step check already lives.
- A feature is a level 3 section with its raw lines and its `(spec)` boxes (`runner/run.py:421-442`).
- Scope rows link issues in several shapes on their `Source:` line: full URLs, `owner/repo#n`, and a bare `#n` meaning the repo's own.

## Options considered

### What "changed after the spec was written" compares against
1. **The issue as it was when the `(spec)` box was ticked, rebuilt from GitHub's edit history, then stored (chosen).** Catches edits made between accepting the spec and the first run, and gives a real diff.
2. A snapshot taken at the first reread. Simple, but misses every edit made before the first run, which is the common case (spec accepted, issue refined, run that night).
3. `updatedAt` newer than the spec. No diff to show, and labels, assignees and bot comments bump it.
4. A snapshot written by `/architect` into the spec folder. Exact, but `/architect` is not authored in this repo, and older specs have none.

### Where the reread runs
1. **The runner process, before each call (chosen).** It is the only place with a GitHub login; calls stay sealed.
2. Inside the call. Impossible by design (spec 0007), and loosening it for reads would open a push path.

### What a change does
1. **A spec 0021 question (F13), the feature waits, the rest goes on (chosen).**
2. Park silently. Ruled out by spec 0021.
3. Build on anyway and report. Builds to a requirement that may be stale, the costly failure in your own rules ("the ticket is the spec").

## Decided without asking (2026-10-13)
Per the brief, the recommended option was taken for every question.

| Question | Options | Pick |
|---|---|---|
| Baseline for "changed" | issue at spec accept (edit history), stored; snapshot at first reread; `updatedAt`; `/architect` snapshot | Issue at spec accept, stored after first build. First reread is the fallback when the history cannot be read. |
| Spec time | commit that ticked the `(spec)` box; spec file's commit; spec `**Date**` | The ticking commit: every feature has that box (spec 0011 AC-2), not every row links its spec file. |
| What counts as a change | body, new non bot comments, closed; plus title, labels | Body, new non bot comments, closed. Titles and labels rarely carry the requirement and would ask too often. |
| Recommended answer | update the spec first; go on as is | Update the spec first: building to an outdated requirement wastes the night's work, and the feature only waits, the rest builds. |
| No linked issue in an `issues` repo | build as `scope`, report line; ask; refuse | Build as `scope`, report line. Asking for every unlinked feature is noise. |
| GitHub unreadable | go on with the stored baseline, report line; ask; stop | Go on, report line. Not reading is not a change. |
| Several issues on one feature | all, up to 5; the first only | All, up to 5. |
| `issues` versus `mixed` for the runner | same behavior; different | Same: in both the issue holds the requirement and the scope holds the boxes the runner works through. A difference, if any, belongs to `/scope`. |
| Give the issue to the call? | yes, as data in the prompt; no | Yes, capped at 20,000 characters. A call cannot read it any other way, and `/develop` must read the issue it builds. |
| Where the baseline lives | state folder; the repo | State folder: `wf run` writes nothing in a repo (architecture invariant 7). |

## Risks
- The edit history query is the one outside behavior this rests on (P2). If GitHub returns only summaries, edits made before the first run are missed and the spec says so.
- Issue text written by other people reaches a call. It is labeled as data, never instructions, the same as fetched pages (`runner/run.py:149`), and the calls' guard (spec 0007) does not depend on the model obeying it.
- Comments edited after the baseline are not compared; only new ones are.
