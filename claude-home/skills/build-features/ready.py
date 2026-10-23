#!/usr/bin/env python3
"""Spec 0074 AC-1, AC-2: the rows /build-features may offer, as JSON on stdout. Run from inside the repo:
`ready.py [--plan <plan.py>]` (default ~/.claude/skills/chip-dash/plan.py). Exit 1 with one line on stderr when
plan.py fails or does not list this repo. Stdlib only."""
import argparse
import glob
import importlib.util
import itertools
import json
import os
import re
import subprocess
import sys

READY_STATUS = ("Proposed", "In Progress", "Accepted")
TIER = re.compile(r"·\s*(Prototype|Alpha|Beta|GA)\s*(?=·|$)")
WORKFLOW = re.compile(r"^\*\*Workflow:\*\*\s*(Prototype|Alpha|Beta|GA)\b", re.M)
ROW = re.compile(r"^(\d+)\.\s*(.*)$")
MAX_OFFER = 12


def run(argv, cwd):
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)
        return p.returncode, p.stdout, p.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, "", str(e)


def load_plan(plan_py):
    spec = importlib.util.spec_from_file_location("plan", plan_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def first_line(*texts):
    return next((l.strip() for t in texts for l in (t or "").splitlines() if l.strip()), "")


def scope_texts(repo):
    for base in ("docs/scope", ".workflow/scope"):
        files = sorted(glob.glob(os.path.join(repo, base, "*.md")))
        if files:
            top = next((f for f in files if os.path.basename(f) in ("scope.md", "index.md")), files[0])
            return open(top, encoding="utf-8", errors="replace").read(), \
                [open(f, encoding="utf-8", errors="replace").read() for f in files]
    return "", []


def offer(repo, plan_py):
    plan = load_plan(plan_py)
    code, out, err = run([sys.executable, "-B", plan_py], repo)
    try:
        data = json.loads(out) if code == 0 else None
    except ValueError:
        data = None
    if not data or not isinstance(data.get("repos"), list):
        raise SystemExit(f"plan.py failed: {first_line(err) or f'exit {code}'}")
    entry = next((r for r in data["repos"] if r.get("path") == repo), None)
    if entry is None or "features" not in entry:
        raise SystemExit(f"plan.py lists no scope for {repo}" + (f": {entry['error']}" if entry and entry.get("error") else ""))

    top, texts = scope_texts(repo)
    raw = {}
    for text in texts:
        for line in text.splitlines():
            m = re.match(r"^###\s+(.*?)\s*$", line)
            if m:
                raw.setdefault(plan.bare(m.group(1)), m.group(1))
    w = WORKFLOW.search(top)
    default_tier = w.group(1) if w else None

    code, out, _ = run(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes/origin"], repo)
    branches = out.split() if code == 0 else []
    code, out, err = run(["gh", "pr", "list", "--json", "number,headRefName"], repo)
    try:
        prs = json.loads(out) if code == 0 else None
    except ValueError:
        prs = None
    pr_error = None if isinstance(prs, list) else (first_line(err) or f"exit {code}")
    code, out, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo)
    base = out.strip() if code == 0 else None

    def overlap(a, b):
        code, out, err = run(["spec-paths", "--overlap", a, b], repo)
        return None if code == 0 else first_line(out, err) or f"spec-paths exit {code}"

    rows = []
    for f in entry["features"]:
        heading = f.get("heading") or ""
        if f.get("state") != "ready to build" or f.get("deferred") or "needs a decision" in raw.get(heading, heading):
            continue
        if f.get("spec") and f.get("specStatus") not in READY_STATUS:
            continue
        m = ROW.match(heading)
        if not m:
            continue
        n, title = int(m.group(1)), m.group(2)
        t = TIER.search(raw.get(heading, ""))
        r = {"row": n, "heading": heading, "spec": f.get("spec"), "tier": t.group(1) if t else default_tier,
             "label": " ".join([f"row {n}"] + [x.strip(",.;:") for x in title.split()[:3]]),
             "offered": True, "reason": None, "notes": []}
        if not r["spec"]:
            r.update(offered=False, reason="no spec, not offered")
            rows.append(r)
            continue
        own = re.compile(rf"^(origin/)?(feat|fix)/{r['spec']}-")
        mine = [b for b in branches if own.match(b)]
        for pr in prs or []:
            head = str(pr.get("headRefName", ""))
            hm = re.match(r"^(feat|fix)/(\d{4})-", head)
            if hm and hm.group(2) == r["spec"]:
                mine.append(f"PR #{pr.get('number')}")
            elif hm:
                hit = overlap(r["spec"], hm.group(2))
                if hit:
                    r["notes"].append(f"may clash with PR #{pr.get('number')}: {hit}")
            else:
                r["notes"].append(f"may clash with PR #{pr.get('number')}, branch has no spec number")
        if pr_error:
            r["notes"].append(f"open PRs not checked: {pr_error}")
        if mine:
            r.update(offered=False, reason=f"already in progress: {', '.join(mine)}")
        rows.append(r)

    offered = [r for r in rows if r["offered"]]
    later = [r["row"] for r in offered[MAX_OFFER:]]
    for r in offered[MAX_OFFER:]:
        r.update(offered=False, reason="not offered this run")
    offered = offered[:MAX_OFFER]
    pairs = []
    for a, b in itertools.combinations(offered, 2):
        hit = overlap(a["spec"], b["spec"])
        if hit:
            pairs.append({"rows": [a["row"], b["row"]], "text": hit})
    return {"repo": repo, "base": base, "rows": rows, "pairs": pairs, "later": later, "prError": pr_error}


def main(argv):
    ap = argparse.ArgumentParser(prog="ready.py")
    ap.add_argument("--plan", default=os.path.expanduser("~/.claude/skills/chip-dash/plan.py"))
    a = ap.parse_args(argv)
    code, out, err = run(["git", "rev-parse", "--show-toplevel"], os.getcwd())
    if code != 0:
        print(f"not in a git repo: {first_line(err)}", file=sys.stderr)
        return 1
    try:
        print(json.dumps(offer(os.path.realpath(out.strip()), a.plan), indent=1))
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
