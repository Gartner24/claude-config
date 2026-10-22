"""Spec 0061: the runner reads its past runs, keeps a history that outlives pruning, sets baselines and writes
template proposals for problems that repeat. Reads runs/*/run.json, writes only under insights/ (AC-1, AC-8)."""
import fcntl
import hashlib
import html
import json
import math
import os
import re
import statistics
import tempfile

import run
import wf

WINDOW, HOT, NEW_MAX, REPORT_MAX = 10, 3, 3, 4000
ID = re.compile(r"^- \[([0-9a-f]{12})\]", re.M)
INBOX_HEAD = ("# wf proposals\n\nWritten by the runner (spec 0061) from problems that repeat across runs. Nothing here "
              "is applied; promote a good one to a plan row, then run `wf insights --seen`.\n\n")
TEMPLATES = {
    "denied": "{subject} was denied in {n} of the last {w} runs ({ids}; from calls[].denials). Proposal: give that "
              "step the access with `wf allow-writes`, or change the step so it no longer needs it.",
    "timeout": "`{subject}` calls ended in call_timeout in {n} of the last {w} runs ({ids}; from features[].outcome). "
               "Proposal: split that step into smaller boxes, or raise its time cap.",
    "park": "Features parked as `{subject}` in {n} of the last {w} runs ({ids}; from features[].outcome). "
            "Proposal: find what keeps causing it and add a plan row for the fix.",
}


def folder():
    return os.path.join(run.state_dir(), "insights")


def kind(command):
    words = str(command or "").split()
    return words[0] if words else "?"


def denial(d):
    """AC-2: tool plus the file_path of a file tool's input, else the tool name alone; never the command text."""
    tool = run.flat(d.get("tool")) or "?"
    key = run.FILE_TOOLS.get(tool)
    # The input was cut at 200 characters when recorded, so it may not parse as JSON; read the one field instead.
    m = key and re.search(r'"%s": "((?:[^"\\]|\\.)*)"' % key, str(d.get("input") or ""))
    if not m:
        return tool
    try:
        path = json.loads('"' + m.group(1) + '"')
    except ValueError:
        path = m.group(1)
    return f"{tool} `{run.flat(path)}`"


def summary(name, rec):
    calls = [c for c in rec.get("calls") or [] if isinstance(c, dict)]
    kinds = {}
    for c in calls:
        k = kinds.setdefault(kind(c.get("command")), {"duration_s": [], "cost_usd": []})
        for f in k:
            k[f].append(c.get(f))
    feats = [e for e in rec.get("features") or [] if isinstance(e, dict)]
    timeouts = []
    for e in feats:
        if e.get("outcome") == "call_timeout":
            seqs = [n for n in e.get("calls") or [] if isinstance(n, int) and 0 < n <= len(calls)]
            timeouts.append(kind(calls[seqs[-1] - 1].get("command")) if seqs else "?")
    return {"run": name, "ended": rec.get("ended"), "stop_reason": rec.get("stop_reason"),
            "cost_usd": rec.get("cost_usd"), "kinds": kinds,
            "parks": [e["outcome"] for e in feats if e.get("outcome") in run.PARKS],
            "denials": [denial(d) for c in calls for d in c.get("denials") or [] if isinstance(d, dict)],
            "timeouts": timeouts, "retries": sum(1 for c in calls if c.get("retry_of") is not None)}


def read_history(path):
    out, ids = [], set()
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return out
    for line in lines:
        try:
            s = json.loads(line)
        except ValueError:
            continue
        if isinstance(s, dict) and s.get("run") not in ids:
            ids.add(s.get("run"))
            out.append(s)
    return out


def append(path, line):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, (line + "\n").encode("utf-8"))
    finally:
        os.close(fd)


def scan(hist_path, history):
    """AC-2: one summary line per ended run not yet in history. Returns (new lines, corrupt run.json count)."""
    runs, known = os.path.join(run.state_dir(), "runs"), {s.get("run") for s in history}
    new, corrupt = [], 0
    for name in sorted(os.listdir(runs)) if os.path.isdir(runs) else []:
        p = os.path.join(runs, name, "run.json")
        if name in known or not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                rec = json.load(f)
        except (OSError, ValueError):
            rec = None
        if not isinstance(rec, dict):
            corrupt += 1
            continue
        if rec.get("ended") is None:
            continue
        s = summary(name, rec)
        append(hist_path, json.dumps(s))
        new.append(s)
    return new, corrupt


def last(history):
    return sorted(history, key=lambda s: str(s.get("ended") or ""))[-WINDOW:]


def p90(v):
    return sorted(v)[math.ceil(0.9 * len(v)) - 1]


def baselines(window):
    """AC-3: median and p90 per command kind, nulls skipped; runs containing each park, denial and timeout."""
    vals = {}
    for s in window:
        for k, fields in (s.get("kinds") or {}).items():
            for f, v in fields.items():
                vals.setdefault(k, {}).setdefault(f, []).extend(x for x in v if isinstance(x, (int, float)))
    stats = {k: {f: (statistics.median(v), p90(v)) if v else None for f, v in fs.items()} for k, fs in vals.items()}
    counts = {}
    for s in window:
        for template, field in (("park", "parks"), ("denied", "denials"), ("timeout", "timeouts")):
            for subject in set(s.get(field) or []):
                counts.setdefault((template, subject), []).append(s["run"])
    return stats, counts


def key(template, subject):
    return hashlib.sha256(f"{template}\0{subject}".encode()).hexdigest()[:12]


def load_set(path):
    try:
        with open(path, encoding="utf-8") as f:
            v = json.load(f)
    except (OSError, ValueError):
        return set()
    return set(v) if isinstance(v, list) else set()


def write(path, text):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def inbox_ids(text):
    return ID.findall(text or "")


def update():
    """The end of run and `wf insights` step: scan, baselines, at most NEW_MAX new proposals (AC-2 to AC-4)."""
    d = folder()
    os.makedirs(d, mode=0o700, exist_ok=True)
    lock = os.open(os.path.join(d, "lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        # Two children of a bare wf run end at once; one scan at a time, or both append the same run.
        fcntl.flock(lock, fcntl.LOCK_EX)
        hist = os.path.join(d, "history.jsonl")
        history = read_history(hist)
        new, corrupt = scan(hist, history)
        history += new
        window = last(history)
        stats, counts = baselines(window)
        inbox_path, proposed_path = os.path.join(d, "inbox.md"), os.path.join(d, "proposed.json")
        inbox = report_text(inbox_path)
        proposed = load_set(proposed_path) | set(inbox_ids(inbox))
        added = []
        hot = sorted(((t, s, ids) for (t, s), ids in counts.items() if len(ids) >= HOT), key=lambda x: (-len(x[2]), x))
        for template, subject, ids in hot:
            h = key(template, subject)
            if not ids or h in proposed or len(added) >= NEW_MAX:
                continue
            text = TEMPLATES[template].format(subject=subject, n=len(ids), w=len(window), ids=", ".join(ids))
            added.append(f"- [{h}] {run.now()[:10]}: {wf.clean(text)}\n")
            proposed.add(h)
        if added:
            write(inbox_path, (inbox or INBOX_HEAD) + "".join(added))
            write(proposed_path, json.dumps(sorted(proposed)))
        return {"history": len(history), "scanned": len(new), "corrupt": corrupt, "window": len(window),
                "stats": stats, "counts": counts, "added": len(added), "inbox": inbox_path}
    finally:
        os.close(lock)


def report_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        return None


def unseen():
    d = folder()
    seen = load_set(os.path.join(d, "seen.json"))
    return [h for h in inbox_ids(report_text(os.path.join(d, "inbox.md"))) if h not in seen]


def hook_line():
    """AC-6: the session start line, never the proposal text."""
    n = len(unseen())
    return f"wf proposals: {n} new ({os.path.join(folder(), 'inbox.md')})" if n else None


def usage_report():
    """AC-7: Claude Code's /insights page as text, cut to REPORT_MAX characters, or None when absent."""
    text = report_text(os.path.join(run.live_dir(), "usage-data", "report.html"))
    if text is None:
        return None
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
    return wf.clean(" ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split()))[:REPORT_MAX]


def end_of_run():
    """AC-5: after the morning report; a failure is one warning line and never changes the exit code."""
    try:
        update()
    except Exception as e:
        print(f"warning: insights: {run.flat(e)}", flush=True)


def fmt(v):
    return "?" if v is None else "%g" % round(v, 2)


def cmd_insights(args):
    if args.seen:
        d = folder()
        os.makedirs(d, mode=0o700, exist_ok=True)
        path = os.path.join(d, "seen.json")
        write(path, json.dumps(sorted(load_set(path) | set(inbox_ids(report_text(os.path.join(d, "inbox.md")))))))
        return 0
    r = update()
    print(f"wf insights: {r['history']} runs in history, {r['scanned']} new, {r['corrupt']} unreadable run.json skipped")
    print(f"last {r['window']} runs:")
    for k, fs in sorted(r["stats"].items()):
        print("  " + wf.clean(k) + ": " + ", ".join(f"{f} median {fmt(v and v[0])} p90 {fmt(v and v[1])}"
                                                    for f, v in fs.items()))
    for (template, subject), ids in sorted(r["counts"].items(), key=lambda x: (-len(x[1]), x[0])):
        print(f"  {template} {wf.clean(subject)}: {len(ids)} runs" + (" HOT" if len(ids) >= HOT else ""))
    print(f"new proposals: {r['added']}, unseen: {len(unseen())} ({r['inbox']})")
    text = usage_report()
    if text:
        print("\nfrom /insights (data):\n" + text)
    return 0
