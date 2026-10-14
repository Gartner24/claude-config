# Morning report (spec 0018): one report at the end of every wf run, built from its run.json records and the
# repos' scope files, saved to <state>/report.txt, sent once as a phone note, and shown at session start until
# you run wf finish or wf report --seen.
import datetime
import os
import re
import tempfile

import ntfy
import run
import telegram
import wf

MAX_LINES = 12
MAX_CHARS = 1000
# Spec 0020 AC-10: the one command marks it seen.
HOOK_HEAD = "wf morning report (shows in every session until you run wf):"
FOLDER = re.compile(r"^(.+)-(\d{8}-\d{6})-(\d+)$")
# Item kinds in AC-2 order; parked and stopped share a slot, kept in feature order.
ORDER = ("built", "parked", "question", "live", "yours", "no record", "no end", "not started")
SLOT = {"stopped": "parked"}


def paths():
    s = run.state_dir()
    return os.path.join(s, "report.txt"), os.path.join(s, "report.seen"), os.path.join(s, "runs")


def scope_items(path):
    """AC-2: live and yours items from a repo's scope file, as the runner finds it (docs/ before .workflow/)."""
    scope_dir, _ = wf.find_scope(path)
    try:
        _, boxes = wf.load_scope(os.path.join(path, scope_dir), []) if scope_dir else (None, [])
    except (OSError, StopIteration):
        # A scope gone or unreadable since the run ended costs its live and yours lines, not the whole note.
        return []
    live, yours = {}, []
    for b in boxes:
        if not b.open or b.skip or not wf.OWED.search(b.text):
            continue
        feature = wf.DISPLAY_TAG.sub("", b.feature).strip() if b.feature else ""
        if wf.LIVE.search(b.text):
            live[feature] = live.get(feature, 0) + 1
        else:
            yours.append({"kind": "yours", "feature": feature, "text": wf.SKIP_AHEAD.sub("", wf.owed_text(b)).strip()})
    return [{"kind": "live", "feature": f, "n": n} for f, n in live.items()] + yours


def open_questions(path, items):
    """Spec 0021 AC-6: every open question of the repo in queue.json, with its recommended answer (its first
    option), filled into the run's own question items or added after them. An unreadable queue adds nothing."""
    try:
        q = run.queue_transact()
    except run.QueueError:
        return items
    asked = [d for d in q["decisions"] if d["repo"] == path and d["answer"] is None and d.get("level") != "run"]
    by_id = {i.get("id"): i for i in items if i.get("kind") == "question"}
    for d in asked:
        item = by_id.get(d["id"])
        if item is None:
            item = {"kind": "question", "id": d["id"], "feature": d["feature"]}
            items.append(item)
        item.update(question=d["question"], recommended=d["options"][0] if d["options"] else None)
    return items


def collect(sources):
    """AC-2: (items, records) over sources in run order. A source is {path, name, folder, code, rec}: folder None
    with code None is a parent row that never started, folder None with a code a child that printed no folder."""
    items, recs = [], []
    for s in sources:
        mine = []
        if s["folder"] is None:
            mine.append({"kind": "not started"} if s["code"] is None else {"kind": "no record", "code": s["code"]})
        else:
            rec = s["rec"]
            if rec is None or not rec.get("ended"):
                mine.append({"kind": "no end"})
            if rec is not None:
                recs.append(rec)
            for e in (rec or {}).get("features", []):
                o, item = e.get("outcome"), {"feature": e.get("feature") or ""}
                if o == "feature_done":
                    item["kind"] = "built"
                elif o == "decision_open":
                    item.update(kind="question", id=e.get("detail") or "")
                elif o in run.PARKS:
                    if o == "waiting":
                        continue
                    item.update(kind="parked", reason=o, detail=e.get("detail"))
                elif o:
                    item.update(kind="stopped", reason=o, folder=s["folder"])
                else:
                    continue
                mine.append(item)
        mine = open_questions(s["path"], mine) + scope_items(s["path"])
        for item in mine:
            item.update(repo=s["path"], name=s["name"])
        items += mine
    items.sort(key=lambda i: ORDER.index(SLOT.get(i["kind"], i["kind"])))
    return items, recs


def head(items, recs):
    kinds = [i["kind"] for i in items]
    # Spec 0021 AC-5: a repo stop no longer ends the run, so its reason is read from the repo records too.
    ended = [e["ended"] for r in recs for e in r.get("repos", []) if e.get("ended")]
    reasons = list(dict.fromkeys(ended + [r.get("stop_reason") for r in recs if r.get("stop_reason")]))
    if ended and "queue_done" in reasons:
        reasons.remove("queue_done")
    gone = any(k in ("no record", "no end", "not started") for k in kinds)
    if not gone and recs and reasons == ["queue_done"]:
        status = "done"
    else:
        status = " ".join(["stopped", ", ".join("internal_error (crash)" if r == "internal_error" else r for r in reasons)]).strip()
    ended = [datetime.datetime.fromisoformat(r["ended"]) for r in recs if r.get("ended")]
    # ponytail: no run left an end time (every child died before it), so the parent's own clock stands in.
    at = max(ended).astimezone() if ended else datetime.datetime.now()
    calls = [c for r in recs for c in r.get("calls", [])]
    spent = run.spent_line(run.spent(calls))[len("spent: "):]
    return (f"wf {status} {at:%H:%M}: {kinds.count('built')} built, {kinds.count('parked')} parked, "
            f"{kinds.count('question')} open, {spent}")


def next_line(items, name):
    kinds = {i["kind"] for i in items}
    built = ", ".join(dict.fromkeys(name(i) for i in items if i["kind"] == "built"))
    if "live" in kinds:
        return "next: wf" + (f", then review and merge: {built}" if built else "")
    if kinds & {"parked", "stopped", "question", "yours", "no record", "no end", "not started"}:
        return "next: wf"
    return f"next: review and merge: {built}" if built else "next: wf"


def item_line(i, multi, phone, cfg, wide=False):
    """One AC-2 item line. phone: AC-4 labels and scrubbed fields, no detail; else AC-3 real names and details.
    wide: spec 0029 AC-9's longer reason and question cuts for Telegram."""
    reason, question = (80, 300) if wide else (40, 80)
    field = (lambda t, n, fb: ntfy.scrub_field(cfg, t, n, fb)) if phone else (lambda t, n, fb: wf.clean(str(t)))
    name = label(cfg, i) if phone else i["name"]
    k, feature = i["kind"], field(i.get("feature"), 40, "feature")
    if k == "built":
        text = f"built: {feature}"
    elif k == "parked":
        text = f"parked: {feature}: {field(i['reason'], reason, 'reason')}"
        if not phone and i["detail"]:
            text += f": {run.flat(i['detail'])}"
    elif k == "stopped":
        text = f"stopped: {feature}: {field(i['reason'], reason, 'reason')}"
        # Spec 0021 U10: a runner bug stops only its repo; the report points at its traceback.
        if not phone and i["reason"] == "internal_error" and i.get("folder"):
            text += f" (traceback: {os.path.join(i['folder'], 'traceback.txt')})"
    elif k == "question":
        text = f"question {wf.clean(i['id'])}: {feature}"
        # Spec 0021 AC-6: what it asks and the answer it recommends.
        if i.get("question"):
            text += f": {field(i['question'], question, 'question')}"
        if i.get("recommended"):
            text += f" (recommended: {field(i['recommended'], 40, 'answer')})"
    elif k == "live":
        text = f"live: {feature}: {i['n']} step(s)"
    elif k == "yours":
        text = f"yours: {feature}: {field(i['text'], 80, 'step')}"
    elif k == "no record":
        text = f"no record: {name}: exit {i['code']}"
    else:
        text = f"{k}: {name}"
    return text + (f" ({name})" if multi else "")


def label(cfg, i):
    return ntfy.scrub_field(cfg, ntfy.repo_label(cfg, i["repo"]), 40, "repo")


def render(sources, cfg):
    """(full report, phone body) for these sources (AC-2 to AC-4)."""
    items, recs = collect(sources)
    top, multi = head(items, recs), len(sources) > 1
    full = [top] + [item_line(i, multi, False, cfg) for i in items] + [next_line(items, lambda i: i["name"])]
    full += [f"run folder: {s['folder']}" for s in sources if s["folder"]]
    tail, dropped = next_line(items, lambda i: label(cfg, i)), 0
    if "chat_id" in cfg:
        # Spec 0029 AC-9: every item, no cap; telegram.send_report splits it or attaches it as a file.
        return "\n".join(full) + "\n", "\n".join([top] + [item_line(i, multi, True, cfg, True) for i in items] + [tail])
    lines = [item_line(i, multi, True, cfg) for i in items]
    kinds = [i["kind"] for i in items]

    def body():
        more = [f"+{dropped} more on the wf screen"] if dropped else []
        return "\n".join([top] + lines + more + [tail])
    while lines and (len(lines) + 2 + bool(dropped) > MAX_LINES or len(body()) > MAX_CHARS):
        # AC-4: built: lines go first, then other item lines from the end.
        n = max((x for x, k in enumerate(kinds) if k == "built"), default=len(lines) - 1)
        del lines[n], kinds[n]
        dropped += 1
    return "\n".join(full) + "\n", body()


def save(text):
    """AC-3: report.txt written atomically (0600), report.seen removed."""
    txt, seen, _ = paths()
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(txt), prefix="report.txt.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, txt)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    try:
        os.unlink(seen)
    except FileNotFoundError:
        pass


def send(cfg, body):
    """AC-4: one note, 'sent' only on a returned message id. Spec 0029 AC-9: every Telegram message and file."""
    if "chat_id" in cfg:
        return "sent" if telegram.send_report(cfg, body) else "failed: no message id"
    mid = ntfy.Topic(cfg, "", "").publish(body, 3, stopped=lambda: False, title="wf report", tags=[])
    return "sent" if mid else "failed: no message id"


def deliver(sources, cfg):
    """AC-1: build, write and send; the run.json report value. A failure only warns."""
    try:
        full, body = render(sources, cfg)
        save(full)
        return send(cfg, body)
    except Exception as e:
        error = run.flat(str(e)) or type(e).__name__
        print(f"warning: report: {error}", flush=True)
        return f"failed: {error}"


def end_of_run(r):
    """AC-1 for a single repo run: its report value, 'parent' under a bare wf run."""
    if os.environ.get("WF_REPORT") == "parent":
        return "parent"
    repo = r.record["repos"][0]
    return deliver([{"path": repo["repo"], "name": repo["name"], "folder": r.folder, "code": None,
                     "rec": r.record}], r.ntfy)


def load_record(folder):
    """A run folder's run.json, None when missing, unreadable or not a record."""
    try:
        rec = run.read_json(os.path.join(folder, "run.json"))
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) and rec else None


def end_of_parent(r, rows):
    """AC-1, AC-2: one report over a bare wf run's work rows, from their summary fields."""
    sources = []
    for row in rows:
        # A child refused because a run took its repo after the plan (spec 0020 AC-7) did no work to report.
        if not row["work"] or row.get("skip"):
            continue
        folder =None if row["folder"] == "-" else row["folder"]
        sources.append({"path": row["path"], "name": row["name"], "folder": folder, "code": row["code"],
                        "rec": folder and load_record(folder)})
    if sources:
        deliver(sources, r.ntfy)


# -- wf report [--seen | --hook] (AC-5, AC-6) ----------------------------------

def newest_run():
    """(folder name, its time, pid) of the newest run folder, or None."""
    _, _, runs = paths()
    best = None
    for name in os.listdir(runs) if os.path.isdir(runs) else []:
        m = FOLDER.match(name)
        if not m:
            continue
        try:
            at = datetime.datetime.strptime(m.group(2), "%Y%m%d-%H%M%S")
        except ValueError:
            continue
        if best is None or at > best[1]:
            best = (name, at, int(m.group(3)))
    return best


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def read_text(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        return None


def killed_line():
    """AC-6: the line for a newest run that ended without a record, else None."""
    txt, seen, runs = paths()
    newest = newest_run()
    if not newest:
        return None
    name, at, pid = newest
    rec = load_record(os.path.join(runs, name))
    if rec and rec.get("ended") or alive(pid):
        return None
    if os.path.exists(txt) and at <= datetime.datetime.fromtimestamp(os.path.getmtime(txt)):
        return None
    if (read_text(seen) or "").strip() == name:
        return None
    return f"wf run {wf.clean(name)} ended without a record (killed or power loss), see its log.txt"


def shown(text):
    # report.txt holds feature names from repo scopes; their control characters never reach the terminal.
    return "\n".join(wf.clean(l) for l in text.rstrip("\n").split("\n"))


def locks_held():
    locks = os.path.join(run.state_dir(), "locks")
    for f in sorted(os.listdir(locks)) if os.path.isdir(locks) else []:
        fd, who = run.lock_file(os.path.join(locks, f), create=False)
        if fd is not None:
            os.close(fd)
        elif who is not None:
            return True
    return False


def hook():
    if os.environ.get("WF_RUN") or locks_held():
        return
    txt, seen, _ = paths()
    text = read_text(txt)
    if text is not None and not os.path.exists(seen):
        print(HOOK_HEAD)
        print(shown(text))
    line = killed_line()
    if line:
        print(line)


def mark_seen():
    """AC-5: report.seen holds the newest run folder's name, so the killed run line stops showing too."""
    newest = newest_run()
    _, seen, _ = paths()
    os.makedirs(os.path.dirname(seen), mode=0o700, exist_ok=True)
    with open(seen, "w", encoding="utf-8") as f:
        f.write(newest[0] if newest else "")


def cmd_report(args):
    if args.hook:
        try:
            hook()
        except Exception:
            pass
        return 0
    line = killed_line()
    if args.seen:
        mark_seen()
    else:
        text = read_text(paths()[0])
        print("no report yet" if text is None else shown(text))
    if line:
        print(line)
    return 0
