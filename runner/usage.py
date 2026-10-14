# Usage limit planning (spec 0022): where you stand in the 5 hour window and the week, read from your account the way
# the status line reads it, and a guess of what the picked features will use, from what past calls used.
# The login token is read in this process for one request and is never printed, logged or saved.
import datetime
import glob
import json
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request

import run

URL = "https://api.anthropic.com/api/oauth/usage"
TIMEOUT = 5
CACHE_S = 60
SAMPLES_KEPT = 2000
RATIO_DAYS = 14
MIN_SAMPLES = 3
MIN_DOLLARS = 1.0
# AC-6: points of the week kept for your own day use.
RESERVE = 10
WINDOWS = ("five_hour", "seven_day")
NOT_LOGIN = "not a subscription login"
_version = []


def cache_path():
    return os.path.join(run.state_dir(), "usage.json")


def samples_path():
    return os.path.join(run.state_dir(), "usage.jsonl")


def when(v):
    """An aware datetime from an ISO string, else None."""
    if not isinstance(v, str):
        return None
    try:
        t = datetime.datetime.fromisoformat(v)
    except ValueError:
        return None
    return t if t.tzinfo else t.astimezone()


def token():
    """AC-1: the subscription login's access token, else None. Never leaves this process except in the one header."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return None
    base = os.environ.get("ANTHROPIC_BASE_URL")
    if base:
        host = (urllib.parse.urlsplit(base).hostname or "").casefold()
        if host != "anthropic.com" and not host.endswith(".anthropic.com"):
            return None
    try:
        with open(os.path.join(run.live_dir(), ".credentials.json"), encoding="utf-8") as f:
            t = json.load(f)["claudeAiOauth"]["accessToken"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return t if isinstance(t, str) and t else None


def parse(data):
    """The answer's two windows as {"used": float, "resets_at": aware datetime or None}, else None."""
    try:
        out = {}
        for w in WINDOWS:
            v = data[w] or {}
            u = v.get("utilization")
            # AC-1: a null utilization reads as 0 with no reset.
            out[w] = {"used": 0.0, "resets_at": None} if u is None else \
                {"used": float(u), "resets_at": when(v.get("resets_at"))}
        return out
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def write_private(path, text, mode="w"):
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | (os.O_APPEND if mode == "a" else os.O_TRUNC), 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, mode, encoding="utf-8") as f:
        f.write(text)


def flat_windows(u):
    return {w: {"used": u[w]["used"], "resets_at": u[w]["resets_at"] and u[w]["resets_at"].isoformat()} for w in WINDOWS}


def cached():
    """AC-2: the last successful read when it is under CACHE_S old, else None."""
    try:
        with open(cache_path(), encoding="utf-8") as f:
            d = json.load(f)
        if 0 <= time.time() - float(d["at_epoch"]) < CACHE_S:
            return parse({w: {"utilization": d[w]["used"], "resets_at": d[w]["resets_at"]} for w in WINDOWS})
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def read():
    """AC-1, AC-2: {"five_hour": {"used", "resets_at"}, "seven_day": {...}}, or (None, reason). One GET with the
    status line's headers, 5 s, a 60 s cache shared by every wf process, and one sample line per new read."""
    hit = cached()
    if hit:
        return hit
    tok = token()
    if tok is None:
        return None, NOT_LOGIN
    if not _version:
        _version.append(run.claude_version() or "unknown")
    req = urllib.request.Request(URL, headers={
        "Authorization": f"Bearer {tok}", "anthropic-beta": "oauth-2025-04-20", "anthropic-version": "2023-06-01",
        "Accept": "application/json", "User-Agent": f"claude-code/{_version[0]}"})
    del tok
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        # Closed here: an unclosed error body used to be reported by the garbage collector with its message.
        code = e.code
        e.close()
        return None, f"usage service: {code}"
    except Exception as e:
        # The class name only: an exception's text is never shown, so nothing of the request can leak through it.
        return None, f"usage service: {type(e).__name__}"
    finally:
        req.headers.clear()
    try:
        u = parse(json.loads(raw))
    except ValueError:
        u = None
    if u is None:
        return None, "usage answer unreadable"
    now = run.wall_now()
    f = flat_windows(u)
    try:
        write_private(cache_path(), json.dumps({"at_epoch": time.time(), **f}))
        write_private(samples_path(), json.dumps({
            "at": now.isoformat(timespec="seconds"), "five_hour": f["five_hour"]["used"],
            "five_hour_resets_at": f["five_hour"]["resets_at"], "seven_day": f["seven_day"]["used"],
            "seven_day_resets_at": f["seven_day"]["resets_at"]}) + "\n", "a")
        trim()
    except OSError:
        pass
    return u


def trim():
    """AC-2: usage.jsonl keeps its newest SAMPLES_KEPT lines."""
    with open(samples_path(), encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) > SAMPLES_KEPT:
        write_private(samples_path(), "".join(lines[-SAMPLES_KEPT:]))


def samples():
    out = []
    try:
        with open(samples_path(), encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict) and when(d.get("at")):
                    out.append(d)
    except OSError:
        pass
    return out


def run_calls():
    """AC-3: the call records of the newest RUNS_KEPT run folders."""
    folders = sorted(glob.glob(os.path.join(glob.escape(run.state_dir()), "runs", "*", "run.json")),
                     key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)[-run.RUNS_KEPT:]
    calls = []
    for p in folders:
        try:
            with open(p, encoding="utf-8") as f:
                rec = json.load(f)
            calls += [c for c in rec.get("calls") or [] if isinstance(c, dict)]
        except (OSError, ValueError, AttributeError):
            continue
    return calls


def kind_key(call):
    """AC-3: the box command's first word, the first two for /check verify; /debug and /sync for those calls."""
    if call.get("kind") == "debug":
        return "/debug"
    if call.get("kind") == "sync":
        return "/sync"
    return command_key(call.get("command"))


def command_key(command):
    words = str(command or "").split()
    return " ".join(words[:2]) if words[:2] == ["/check", "verify"] else (words[0] if words else "")


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def tokens(call):
    t = call.get("tokens")
    vals = [num(v) for v in t.values()] if isinstance(t, dict) else []
    return sum(vals) if vals and None not in vals else None


def medians(calls):
    out = {"n": len(calls)}
    for name, get in (("cost_usd", lambda c: num(c.get("cost_usd"))), ("duration_s", lambda c: num(c.get("duration_s"))),
                      ("tokens", tokens)):
        vals = [v for v in map(get, calls) if v is not None]
        out[name] = statistics.median(vals) if vals else None
    return out


def estimates(calls=None):
    """AC-3: {"keys": {key: medians}, "all": medians or None}; limited and outage calls left out."""
    calls = [c for c in (run_calls() if calls is None else calls) if not c.get("limited") and not c.get("outage")]
    keys = {}
    for c in calls:
        keys.setdefault(kind_key(c), []).append(c)
    return {"keys": {k: medians(v) for k, v in keys.items()}, "all": medians(calls) if calls else None}


def estimate(est, key):
    """AC-3: a key's medians, those over all calls under MIN_SAMPLES samples, None with no calls at all."""
    m = est["keys"].get(key)
    return m if m and m["n"] >= MIN_SAMPLES else est["all"]


def ended(call):
    t, d = when(call.get("started")), num(call.get("duration_s"))
    return t + datetime.timedelta(seconds=d) if t and d is not None else None


def ratios(calls=None, lines=None, now=None):
    """AC-4: window percent per dollar for each window, learned from consecutive samples with the same reset and the
    dollars of the calls that ended between them; None under MIN_DOLLARS of matched calls."""
    calls = run_calls() if calls is None else calls
    lines = samples() if lines is None else lines
    now = now or run.wall_now()
    cut = now - datetime.timedelta(days=RATIO_DAYS)
    lines = [d for d in lines if when(d["at"]) >= cut]
    ends = [(ended(c), num(c.get("cost_usd"))) for c in calls]
    ends = [(e, c) for e, c in ends if e and c is not None]
    out = {}
    for w in WINDOWS:
        rise = dollars = 0.0
        for a, b in zip(lines, lines[1:]):
            if a.get(f"{w}_resets_at") != b.get(f"{w}_resets_at") or num(a.get(w)) is None or num(b.get(w)) is None:
                continue
            ta, tb = when(a["at"]), when(b["at"])
            spent = [c for e, c in ends if ta < e <= tb]
            if not spent:
                continue
            rise += max(b[w] - a[w], 0)
            dollars += sum(spent)
        out[w] = rise / dollars if dollars >= MIN_DOLLARS else None
    return out


def feature_cost(feature, est):
    """AC-5: (dollars, seconds, first call dollars) over the feature's open boxes the runner would run plus one
    /sync, or None when an estimate is unknown."""
    keys = [command_key(b.command()) for b in feature.boxes
            if b.open and not b.skip and b.command() and not run.sync_box(b.command())] + ["/sync"]
    parts = [estimate(est, k) for k in keys]
    if any(p is None or p["cost_usd"] is None or p["duration_s"] is None for p in parts):
        return None
    return sum(p["cost_usd"] for p in parts), sum(p["duration_s"] for p in parts), parts[0]["cost_usd"]


def at_text(t):
    return t.astimezone().strftime("%a %H:%M")


def plan(picked, u=None, est=None, ratio=None):
    """AC-5 to AC-7 for picked [(repo, Feature)] in screen order: {"lines", "start" (aware datetime or None for now),
    "week" (per feature week percent or None)}. Never refuses: an unknown outcome starts now."""
    u = read() if u is None else u
    est = estimates() if est is None else est
    ratio = ratios() if ratio is None else ratio
    lines, reason = [], None
    if isinstance(u, tuple):
        reason = u[1]
    else:
        lines.append(f"now: 5h {u['five_hour']['used']:g}% (resets {reset_text(u, 'five_hour')}), "
                     f"week {u['seven_day']['used']:g}% (resets {reset_text(u, 'seven_day')})")
    costs = [feature_cost(f, est) if est["all"] else None for _, f in picked]
    week = [c[0] * ratio["seven_day"] if c and ratio["seven_day"] is not None else None for c in costs]
    if est["all"] is None:
        reason = reason or "no past calls"
    elif None in costs:
        reason = reason or "no estimate for a step"
    elif None in ratio.values():
        reason = reason or "no usage samples yet"
    if reason:
        lines.append(f"unknown ({reason}), starts now")
        return {"lines": lines, "start": None, "week": week}
    dollars = sum(c[0] for c in costs)
    by_repo = {}
    for (repo, _), c in zip(picked, costs):
        by_repo[repo] = by_repo.get(repo, 0) + c[1]
    p5, pw = dollars * ratio["five_hour"], dollars * ratio["seven_day"]
    lines.append(f"need: ~{p5:.0f}% of a 5h window, ~{pw:.0f}% of the week, ~{max(by_repo.values(), default=0) / 3600:.1f}h "
                 f"(from {est['all']['n']} past calls)")
    left = 100 - u["seven_day"]["used"] - RESERVE
    start, margin = None, run.LIMIT_MARGIN
    if pw > left:
        r = u["seven_day"]["resets_at"]
        start = (r or run.wall_now()) + margin
        lines.append(f"does not fit the week: starts at {at_text(start)}")
        k, total = 0, 0.0
        for w in week:
            total += w
            if total > left:
                break
            k += 1
        lines.append(f"fits now: 1-{k}" if k else "fits now: none")
    # this used to check only costs[0]: a later repo's big first call started a run its 5h window could not hold
    elif any(100 - u["five_hour"]["used"] < c[2] * ratio["five_hour"]
             for c in {r: c for (r, _), c in reversed(list(zip(picked, costs)))}.values()):
        start = (u["five_hour"]["resets_at"] or run.wall_now()) + margin
        lines.append(f"5h window nearly used: starts at {at_text(start)}")
    else:
        lines.append("fits, starts now")
    return {"lines": lines, "start": start, "week": week}


def reset_text(u, w):
    r = u[w]["resets_at"]
    return at_text(r) if r else "unknown"
