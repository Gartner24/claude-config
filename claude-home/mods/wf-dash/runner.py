#!/usr/bin/env python3
"""Design preview facts for the /runner pane, as JSON on stdout.

shortcut: stands in for the runner part of `wf status --json` (specs 0059 AC-1, 0060 AC-4) until rows 72 and 73
build it; it reads active.json, each run's newest run.json and log.txt, and the open questions.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "runner"))
RUNS = Path.home() / ".local/state/wf/runs"
LOG_LINES = 15
CALL = re.compile(r" call (\d+) \S+ .*?: (/\S.*?), transcript ")
END = re.compile(r" end (\d+) ")


def newest_run(tree):
    name = os.path.basename(tree.rstrip("/"))
    found = sorted(RUNS.glob(f"{name}-*"), key=lambda p: p.stat().st_mtime) if name else []
    return found[-1] if found else None


def run_entry(a):
    import wf
    out = {"repo": wf.clean(os.path.basename(a.get("repo") or "")), "feature": wf.clean(a.get("feature") or ""),
           "step": None, "cost": None, "calls": None, "log": [], "startedAt": None, "steps": []}
    folder = newest_run(a.get("tree") or "")
    if folder is None:
        return out
    try:
        r = json.loads((folder / "run.json").read_text())
        calls = r.get("calls") or []
        last = calls[-1] if calls else None
        # a call with no duration is still running; else the runner is between calls, on next_after
        out["step"] = wf.clean((last.get("command") if last and last.get("duration_s") is None else (last or {}).get("next_after")) or "") or None
        out["cost"], out["calls"], out["startedAt"] = r.get("cost_usd"), len(calls), r.get("started")
        # each finished step: what ran, when, how long, what it cost, and whether it worked
        out["steps"] = [{"command": wf.clean(c.get("command") or ""), "started": c.get("started"),
                         "minutes": round((c.get("duration_s") or 0) / 60, 1), "cost": c.get("cost_usd"),
                         "ok": not c.get("is_error") and c.get("exit_code") == 0} for c in calls]
    except (OSError, ValueError):
        pass
    try:
        lines = (folder / "log.txt").read_text(errors="replace").splitlines()
    except OSError:
        lines = []
    out["log"] = [wf.clean(l) for l in lines[-LOG_LINES:]]
    # run.json gets a step only once it ends; the step running now is the log's last "call N" with no "end N" after it
    started, ended = {}, set()
    for l in lines:
        m = CALL.search(l)
        if m:
            started[m.group(1)] = m.group(2)
        m = END.search(l)
        if m:
            ended.add(m.group(1))
    live = [cmd for n, cmd in started.items() if n not in ended]
    if live:
        out["step"] = wf.clean(live[-1])
    return out


def main():
    import auto
    import run
    import wf
    try:
        runs = [run_entry(a) for a in run.read_active() if auto.entry_running(a)]
    except Exception:
        runs = None
    try:
        qs = [{"id": d["id"], "repo": wf.clean(os.path.basename(d.get("repo") or "")), "feature": wf.clean(d.get("feature") or ""),
               "question": wf.clean(d.get("question") or ""), "options": [wf.clean(str(o)) for o in d.get("options") or []],
               "parked": bool(d.get("parked"))}
              for d in run.queue_transact()["decisions"] if d["answer"] is None]
    except Exception:
        qs = None
    print(json.dumps({"runs": runs, "questions": qs}))


if __name__ == "__main__":
    main()
