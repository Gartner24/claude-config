# 0018. Morning report: rationale

## Context

The 2026-10-13 night run built features 24, 25, 28 and 29, ended at 03:20 and sent nothing. Architecture invariant 4 allowed pings only for decisions, so a finished, parked or crashed run was silent by design. You woke up to six manual steps over four features and had to read four scope sections and a run folder to find them.

The run already records everything a summary needs: `run.json` holds each feature's outcome and the stop reason, and the scope files hold every open waits-on-you box. The phone channel exists (ntfy, spec 0005) with scrubbing rules for a public topic. What is missing is one place that turns those into a short message, and a way for the next Claude session to see it too.

## Options considered

### Option 1: report built at run end, saved, sent once, shown by a session hook

The run builds the report from `run.json` and the scope files, saves it, sends one note; a SessionStart hook prints it until you act.

**Pros**:
- Uses only data the run already writes.
- The phone and the session show the same facts.
- Works for crashes and limits, because `run()` always reaches its end.

**Cons**:
- A run killed outright cannot report; only the session hook notices.
- A new hook in `~/.claude` settings.

### Option 2: a separate timer that checks for finished runs

A systemd timer scans run folders every few minutes and sends a note for any ended run.

**Pros**:
- Also catches killed runs, by noticing a dead pid.

**Cons**:
- A second moving part to install and keep alive, outside the repo's tests.
- Duplicate or missed notes when its state drifts from the run's.

### Option 3: no phone note, session report only

**Pros**:
- No extra buzz.

**Cons**:
- Fails the brief: you want the note on the phone in the morning.

## Rationale

The run is the only component that knows for sure it ended and why, and its `finally` path already runs for every stop reason, so sending from there covers crashes and limits with no new process. A timer would add an always on service for the one case (a killed run) the session hook already covers. One note per `wf run` command follows spec 0017's model, where the parent owns the summary.

The cap (12 lines, 1000 characters) keeps the note readable in the expanded notification and far below ntfy's size where a message turns into an attachment. Showing the report in every session until you act was your pick: missing it costs more than seeing it twice. `wf finish` clears it because running it is acting on the report; `wf report --seen` covers nights with nothing to finish.

The hook stays silent under `WF_RUN` and while any lock is held, so no unattended call gets the report in its context even if the env var does not reach the hook process.
