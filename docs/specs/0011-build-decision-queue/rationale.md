# 0011. Build queue and decision queue: rationale

## Context

`wf run` (spec 0004) builds the feature of the first open box in one repo and ends on the first stop. Spec 0008 sorted every reason into a park (only this feature is stuck) or a stop (the run must end), but a park still ends the run, so one `sudo` or one failed verify wastes the rest of a night. Spec 0005 waits in place for a phone answer, up to 12 hours, holding the run on one question while other work sits idle.

Research section 0 fixed the target: the queue is the scope files themselves (accepted spec, unticked build boxes, `auto` tag), no new queue file, one feature at a time per repo, and you wake up to finished work plus a short list of questions. Spec 0003 already defines `· auto`; spec 0008 already keeps a trust list (`allowed.json`) of repos you opted in.

Forces: `wf` writes nothing in a repo (invariant 7), so any memory between runs lives in the state folder. All features in a repo share one working tree and one branch until feature 14, and skills often leave work uncommitted. A feature linked spec stays `Proposed` until built, so spec status cannot mark a feature as ready. ntfy.sh keeps messages about 12 hours. `claude -p --resume` can continue a session long after it ended, as long as the transcript exists.

## Options considered

### Option 1: Queue state in `wf`, decisions kept in one state file

`wf` plans from the scopes of every trusted repo, runs one feature at a time, and records parks and open decisions in `<state>/queue.json`; a reply resumes the asking session in this run or the next.

**Pros**: a question never blocks other work; a reply is never wasted; parks are remembered, so a stuck feature does not repeat every night.
**Cons**: one more file to validate and lock; resumes can come hours later; a dirty park blocks its repo.

### Option 2: Move on, but forget at run end

Same loop, but parks and open decisions live only in `run.json`; the next run starts every feature fresh.

**Pros**: no state file, nothing to clear by hand.
**Cons**: a feature parked on `sudo` parks again every night; an answer that arrives after the run ends is lost and the step redoes its work in a new session.

### Option 3: Repo by repo, waiting in place

Keep spec 0005's blocking wait; only hard parks move on, and the run finishes one repo (decisions included) before the next.

**Pros**: smallest change to specs 0004 and 0005; easy to read in the terminal.
**Cons**: one slow answer holds up every other queued feature, which is the problem feature 10 exists to fix.

### Option 4: Separate queue file per run

A `queue` file you write by hand listing features in order.

**Pros**: explicit order independent of scope layout.
**Cons**: contradicts the settled "no new queue file"; drifts from the scope as features change.

## Rationale

Option 1 is the only one that meets the done when and the research goal together: a park or a question stops only its feature (the forces "one feature at a time per repo" and "wake up to finished work plus questions"), while the state folder keeps the answer and the park across runs without writing in a repo. Option 2 fails on the 12 hour ntfy window and on repeated nightly parks; Option 3 keeps the blocking wait; Option 4 breaks a settled requirement.

Choices made with you: the trust list is the repo list (it is already your explicit opt in); a feature is queued only with `· auto` and a ticked `(spec)` box (spec status cannot say "confirmed"); answers resume before new work; locks are taken for every repo at start so nothing touches a repo with an open decision; a failing repo is a skip, not a refusal of the night; `--max-calls` and debug attempts count per feature so one feature cannot starve the rest; repo state reasons end only that repo, except `guard_changed` on a file outside the repo (settings and hooks that run in every repo's calls), which ends the run; a decision persists and is re-pinged once per run.

Changed with you after the cross check: only `call_error` parks are retried by the next run on their own. `budget`, `max_calls` and `call_timeout` are remembered like the others, because a feature too big for its caps would otherwise burn a full cap of usage every night until you notice; a rerun with a higher value for that cap, or `wf unpark`, clears them. Exit 0 means no park or open question is left in any repo the run held, so a wrapper reading 0 knows nothing needs you. One usage limit wait per run stays; more waits could spend your weekly usage overnight.

Calls made at write time, with the runner up:
- Tree rule: a dirty repo with any Park or Decision record starts no feature, answered resumes allowed. Runner up (the first draft): a per record `dirty` owner, which made any park the owner of your own uncommitted changes and needed two owners to be ranked; the simple rule is stricter and needs no field.
- A Decision record leaves `queue.json` only after its resume is classified, so a crash or stop during the resume never loses your answer; a resume that keeps failing is treated as stale. Runner up: delete at resume start, which loses the answer on any failure.
- `wf queue` is read only and stale parks are deleted only under the repo lock by `wf run` or `wf unpark`, so it cannot race a running `wf`. Runner up (first draft): `wf queue` deletes them.
- Mid feature box refusals (`waiting`, `manual_box`, `no_command`, `no_feature`) are not recorded as parks: they clear by themselves when files change elsewhere (a `waiting` note names another feature), and a section hash would not see that. Runner up: record them, which would keep a waiting feature parked after its blocker is done.
- Section hash over raw lines rather than parsed boxes: any edit you make inside the feature unparks it, which is the intent. Runner up: hash of box states only, which misses an edited note.
- Replies accepted for any record in `queue.json` (first answer wins) rather than only by the run holding the repo: an answer to a skipped repo is still kept within ntfy's window. Runner up: only the holder, which loses replies while that repo is skipped.
- Re-ping failure is a warning, a first ping failure stays the `ping_failed` run stop of spec 0005: the question already reached the phone once.
