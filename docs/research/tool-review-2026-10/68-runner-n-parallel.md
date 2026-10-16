# 68 - wf runner: n features in parallel (research, read-only)

## Key finding first
The premise "features touching the same files never run together" is NOT true today. Spec 0043 AC-2 removed it.
Same-file features run at the same time; the only guard left is a note after each call. Re-adding it is a choice,
not "keeping" a rule (0043 index.md:10, :30, :75).

## 1. Where the 4 is set and what depends on it
- Standing answer `- parallel: 4` in /home/santiago/claude-config/AGENTS.md:82. Value set hard-coded:
  run.py:236 `"parallel": ("1","2","3","4")`; hint text run.py:241 ("parallel: 1-4"); AGENTS.md:68 says "1 to 4".
  Parse: run.py:4037 (parallel needs `branches: per spec`).
- Scheduler: run.py:5835 `parallel()`. `limit = a.jobs or len(jobs)` (5867) caps all children (--jobs, wf.py:645/658);
  per repo cap at run.py:5901-5903: `sum(k.get("key")==j["key"] for k in running) < j["limit"]`, with `limit=int(answers["parallel"])`
  set in tree_jobs (run.py:5659). One child at a time passes start checks (`starting`, 5895).
- Each child = `wf.py run <worktree> -y --only-feature <f>` subprocess in its own session (5912-5916).
- clashes() run.py:5616-5625: for two worktrees of one repo only an app port clash blocks. Else they run together.
- Not the parallel cap: pr.MAX_DEPTH=3 (stack depth, pr.py:23, :2108), auto.MAX_TAKE=6 (repos per `wf auto`, auto.py:30), MAX_DEBUG=2, MAX_ISSUES=5.
- Same-file rule today:
  - Scheduling: none (clashes ignores Paths; docstring run.py:5617-5619).
  - Data kept: pr.globs() pr.py:2051 reads the spec top file `**Paths:**` globs (AGENTS.md/CLAUDE.md/verify.md and scope dir excluded);
    pr.overlap() pr.py:2068 (fnmatch either way or folder prefix) is defined but the scheduler no longer calls it (only pr.hits() is used, run.py:2305).
    None globs = overlaps everything.
  - Runtime: Run.drift() run.py:2297-2310, called after each call (run.py:3676), only `self.note(...)`. The `paths_overlap` question
    (CASES F15, run.py:307) still exists but nothing raises it on this path.
  - Cost: conflicts appear at merge time. Spec 0051 AC-6 merges origin/<default> into the branch (plain merge; conflict -> `merge_conflict`
    question), under merge_lock (pr.py:1155-1166, taken at :1263 and :1415).
- Other things that scale with n: worktree per feature (pr.make_tree pr.py:2090-2125), active.json + per-call sibling deny list
  (siblings_now run.py:2313, rebuilt each call, grows with n), plan_lock (pr.py:398), queue.json/queue.lock, one app port per repo
  (web features cannot run side by side), 3-deep stack cap.
- Usage handling already exists: ~/.local/state/wf/usage.json(.jsonl) hold five_hour and seven_day percent with reset times; runs wait on usage_limit.
  Last sample 2026-10-15 16:14: five_hour 6, seven_day 19.

## 2. Worktrees vs full clones
Worktrees share one object store, refs, config and hooks; each has its own HEAD and index. index.lock is per worktree
(`.git/worktrees/<name>/index.lock`). Shared locking remains for ref updates, packed-refs, gc and object writes, held for ms.
One third-party report with 13 agents saw ref-lock failures and proposes retry with ~200 ms backoff:
https://claudeissues.com/issue/55724-agent-isolation-worktree-parallel-agents-lose-work-due-to-git-lock-contention-au (single report, not authoritative).
Summaries: https://augmentcode.com/guides/git-worktrees-parallel-ai-agent-execution , https://blog.openreplay.com/git-worktrees-ai-agents/
Repo probe: spec 0027 P1 (index.md:38) = 2 worktrees x 50 commits, clean fsck; rerun at n=8+. wf already runs git with hooks off
(wf.GIT_SAFE wf.py:48: core.hooksPath=/dev/null, fsmonitor off), so hook races are not an issue.

A clone would add: no shared locks, no sibling-edit leak via the common dir (today needs the sibling deny list + carve around commondir,
run.py:2313-2320), simple `rm -rf` cleanup, parallel gc safe.
A clone would cost: disk/clone time (full copy; `--shared`/`--reference` re-couples to the source), n fetches, gitignored setup repeated
(same as worktrees), loss of cross-branch visibility (pr.records, merged(), checkout_of use `wf.worktrees(main)`, pr.py:1168-1175) so a registry
is needed, and the trust/guard model keyed on git common dir (common_dir run.py:5594, clashes, key_of, tree_path) plus spec 0027 AC-3/AC-7 and
0051 AC-7 get rewritten.
"Each agent pushes separately": already true. Each feature has its own branch and PR, pushed by the runner after the names and attribution scans.
Pushes of different branches do not conflict, so a clone changes nothing there.
Other tools (search results, not verified at source): Conductor, claude-squad, Crystal and Claude Code's `--worktree` isolation use git worktrees;
Codex cloud isolates per task in a container. WebSearch gave no direct page for Conductor/claude-squad/Crystal/Codex; treat as unconfirmed.
Verdict: worktrees are fine to ~8-10 agents on one machine. A clone fixes a lock problem not shown here and needs a big rewrite. Cheaper fix if a
lock failure appears: retry wrapper around wf.git branch/worktree/commit (spec 0027 already names "a retry rule like spec 0020 AC-8").

## 3. Real limits for n
RAM now: 23.1 GB total, 12.4 GB available, 10.8 GB used, 6.5 of 8 GB swap used already. One interactive `claude` here: 442 MB and 806 MB RSS (ps).
No per-`claude -p` figure exists in run.json or ram-watch logs; helpers (bwrap, MCP node, headless Brave for UI features, the app, the suite) add more.
Budget ~1.5 GB per building feature (estimate) -> ~8 on 12 GB free, ~6 given swap is already half used.
ram-watch.sh (/home/santiago/.claude/scripts/claude-ram-watch.sh) kills the biggest helper when MemAvailable < 3 GB (log: kill on 2026-10-14 at 2.9 GB),
so the machine already hits that floor. The fast suite (spec 0043 AC-7) uses cpu_count processes per run, so n suites at once oversubscribe CPU;
likely the sharper limit than RAM. nproc not read (a tool hook blocked chained calls) - check it.
Claude plan: 5-hour and weekly pools are shared by all sessions (and claude.ai chat); Anthropic no longer publishes exact numbers; no documented
concurrent-session cap found. Third-party: https://portkey.ai/blog/claude-code-limits , https://www.datacamp.com/tutorial/claude-code-usage-limits ,
https://inventivehq.com/blog/claude-code-rate-limits-explained . n sessions burn the same pool n times faster (spec 0043 Risks, line 103). This is the
real cap, not the machine.
GitHub: PR create/merge are content-creating calls. Secondary limits: ~80 content requests/min, 500/hour, 100 concurrent, 900 points/min per endpoint,
writes cost 5 points (https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api, seen via GHES copies). One PR per feature is a few
POSTs plus polling GETs; n=8 is far below unless polling is aggressive.
Merge lock (pr.py:1155): one update + test + merge per repo at a time. Each merge moves main, so the next waiting PR merges main in and reruns main's
suite (spec 0051 edge cases, line 59). n finished features land in ~n x (merge + suite) time; past ~6 extra agents mostly queue at the lock.
Other serial points: start checks one child at a time (run.py:5895), plan_lock, queue.lock, one app port per repo, stacked specs wait for their base.

## 4. Recommendation
n = a ceiling plus a live brake, not a fixed 4 and not RAM alone.
1. Replace the 1-4 enum with an integer >=1 (ceiling default 6; 8 max until measured). Update run.py:236, :241, AGENTS.md:68, parse test.
2. Admission test at each spawn in parallel() (run.py:5895 loop, it already polls): start another child only if running < n AND MemAvailable
   (/proc/meminfo) > 3 GB floor + 1.5 GB AND usage.json five_hour < ~80 (and a weekly threshold). Otherwise the job stays in `waiting`.
3. Same-file rule: decide it explicitly via /architect (it amends 0043 AC-2 and 0027 AC-4). Option A (your wish): in the pick at run.py:5901 add
   `not any(pr.overlap(j["globs"], k["globs"]) for k in running if k.get("tree"))`. globs are already on each job row (tree_jobs sets them).
   Caveat: globs None (no Paths line) = overlaps all = runs alone; keep drift() as a net. Option B: leave it and rely on 0051 AC-6 merge conflicts;
   conflict questions rise with n. A is cheaper.
4. Keep worktrees. Add a lock retry in wf.git for ref-touching commands. Rerun spec 0027 P1 at n=8 with fsck.
5. Optional: skip the main-suite rerun at merge when main did not move (spec 0051 AC-5 wording says rerun; amend only if safe).
Tests: ANSWER_KEYS accepts n>4 and rejects 0/non-integer; scheduler test with 8 jobs and overlapping globs asserting overlapping jobs never in
`running` together and disjoint ones do (mutation: drop the clause -> red); None globs runs alone; admission test with fake /proc/meminfo and
usage.json (mock must expose every field the code reads); e2e `--same-repo` (spec 0027 AC-10) restore the "C waits for A" assert; git stress P1 at n=8.
Risks: usage pool drained n times faster; swap-heavy machine -> helper kills; wrong or missing Paths; finished work waiting at the merge lock while
holding worktrees; GitHub secondary limits only with heavy polling; accepted specs 0027/0043 change -> /architect first, not a build.

Not verified: nproc, per-`claude -p` RSS, Conductor/claude-squad/Crystal/Codex specifics, any Anthropic first-party concurrency doc.
