# 0025 rationale

## Context

- Spec 0017 made bare `wf run` a parent of one child per repo. Its accepted gap (0017 Consequences, decision `w8d0 2` of 2026-10-13): each child takes its guard baseline at its own start, so a guarded file one repo's call changes is part of the next repo's baseline and goes unnoticed. Always so for a repo nested in another, which 0017 AC-3 starts only after the outer one ends; also for any repo waiting on a `--jobs` slot.
- Before 0017 the single process held every repo and `files_changed` (run.py:1195-1225) saw such a change and stopped the repos it touched.
- The parent already has the right baseline: `bare_checks` (run.py:809-838) runs `repo_checks` and so `freeze_guard` (run.py:869) for every repo during the plan, before the confirm (finish.py:951 for bare `wf`). It throws it away when it starts the children (run.py:3688-3748).
- The child re-hashes its baseline at its own confirm (run.py:2739-2743), so any check has to compare against the plan's hashes, not its own.
- Spec 0021 says how a guard change is handled: U5, a repo level question (`accept the new setup and go on`, `stop this repo`), the rest goes on. The child already has every piece: `end_repo` asks (run.py:1654-1664), `pick` holds the repo while the question is open (run.py:1604-1608), `end_wait` waits for it (run.py:2338-2340), `repo_answer` takes the answer and re-baselines on accept (run.py:1666-1695).
- Spec 0020 AC-5: a change whose fingerprint `wf` wrote to `swaps.jsonl` is a swap you approved, never a stop (`accepted_by`, run.py:548). The `wf` swap runs after the plan and before the builds, so without this filter every swap night would ask.

## Options considered

1. Who checks: (a) the child, against the plan baseline handed over in a file (chosen): reuses the whole U5 path (ask with a run folder, wait, answer, re-baseline), and the check runs at the last moment before the repo's first call. (b) The parent, before each start: needs the question, phone polling and a wait loop in the parent, which has no run folder (`self.folder` None, run.py:653) and blocks on child output (run.py:3749). (c) One shared baseline file all children compare at each guard check: changes the in-run guard of every child, much larger.
2. What a change does: (a) the U5 question, repo waits, rest goes on (chosen, spec 0021). (b) Skip the repo with the file named, as the scope row's old "Done when" said: a silent set-aside, which 0021 forbids. (c) Stop the whole run: 0021 AC-5 forbids a repo reason ending the run.
3. How the baseline reaches the child: (a) a 0600 file in the state folder and a hidden flag (chosen): calls cannot write the state folder (spec 0020 AC-5 Edit deny, and the Bash sandbox). (b) An environment variable: large, and inherited by every process the child starts. (c) Stdin: the child's stdin is `/dev/null` by design (0017 AC-1).

## Decided without asking (2026-10-13)

Per docs/briefs/finish-runner-today.md.

| Question | Options | Pick |
|---|---|---|
| Who runs the check? | child against the plan baseline; parent before each start; shared baseline for all checks | Child, baseline handed over in a file |
| What happens on a change? | U5 question, rest goes on; skip the repo; stop the run | U5 question (spec 0021), accept recommended first |
| Is a `wf` swap a change? | no, ledger accepted; yes | No (spec 0020 AC-5) |
| Are standing answers part of the check? | yes; no | Yes: the plan showed them, a change after the confirm is unseen behind `-y` (same reason as spec 0011 AC-6) |
| Unanswered question at the end of the night | stays open, next `wf` waits on it; dropped; repo built anyway | Stays open and in the morning report |
| Several changed files | one question naming the first and the count; one question per file | One question per repo |

## Consequences

- A change to a global file (a `~/.claude` hook or settings file) asks once in every repo that starts after it, one question per repo.
- A repo that waits on its question keeps its `--jobs` slot while it waits (same as any child waiting at its end, 0017 AC-7).
- Repos already running when the change happens are covered by their own in-run guard, as today (each stops on its own U5 question).
