# 0017 rationale

## Context

`wf run` is one Python process making one `claude -p` call at a time (spec 0004). Bare `wf run` plans across every repo on the trust list, locks them all, and works through their queues one feature at a time (spec 0011). Each repo already has its own lock, guard baseline and park and decision records, and the shared state is safe across processes: `queue.json` changes under `queue.lock` (spec 0011 AC-17), phone replies count for any repo's decision and are skipped once stored (spec 0011 AC-12), and burned codes are written under a lock (`ntfy.burn`). The spec 0009 app runs on the shared localhost, so two apps on one port collide (`app_port_busy`, a run stop). Several features inside one repo at once is a later step: it needs feature 14 (a branch per spec) first.

## Options considered

1. One child process per repo (chosen). Pro: each child is the single repo run already tested; shared state is already safe across processes; small new code. Con: no cross repo view inside a run (the crash loop sees one repo), duplicate plan output (parent and child each print one), one usage limit wait per child rather than one shared.
2. Threads in one process. Pro: one run record, cross repo checks possible. Con: every piece of run state (signals, the call slot, caps, the guard, the app) would have to become thread safe, a large rewrite of tested code.

## Rationale

The goal is more work per night without touching what a repo run does. Every invariant of a single repo run (lock, guard, caps, park memory) already holds per process, so running several processes keeps them all. Parallel is the default (your pick) because that is the point of the feature; `--jobs` is there when your usage window matters. Port clashes are avoided by ordering (your pick) because a clash is a run stop that wastes the night for that repo. Prefixed live lines plus one summary (your pick) keep the terminal readable.
