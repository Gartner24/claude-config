#!/usr/bin/env python3
"""Scan installed skills and plugins with skillspector, show only new serious findings (spec 0054).

  skill-scan [static|llm|both] [path ...] [--accept]
      no path: every ~/.claude/skills/* and every plugin installPath, by realpath, nested folders dropped.
      Prints HIGH/CRITICAL findings missing from the baseline, each with file:line; exit 1 if any or any
      target failed. --accept adds the current findings of that pass to the baseline instead.
  skill-scan --against <installed name or path> <candidate path>
      static scan of both, prints what the candidate adds (claude-config update --apply runs this).

Reports and the baseline live in ~/.claude/state/skillspector/, never in a repo.
Python 3 standard library only.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PIN = "v2.12.0"
WORKERS = {"static": 6, "llm": 3}
TIMEOUT = {"static": 300, "llm": 1800}
# A4 triage: findings in tests, benchmarks, fixtures and changelogs were all false alarms.
NOISE = re.compile(r"(^|/)(tests?|__tests__|benchmarks?|fixtures?|evals?|examples?|node_modules|\.venv)/"
                   r"|CHANGELOG|\.test\.|_test\.|test_")


def home():
    return Path.home() / ".claude"


def state():
    return home() / "state" / "skillspector"


def pinned():
    try:
        out = subprocess.run(["skillspector", "--version"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return "skill-scan: skillspector not found on PATH"
    if PIN not in out.split():
        return f"skill-scan: skillspector {PIN} needed, found: {out.strip() or 'no version'}"
    return None


def plugins():
    """realpath of every plugin installPath -> its key without version, e.g. superpowers@claude-plugins-official."""
    f = home() / "plugins" / "installed_plugins.json"
    if not f.exists():
        return {}
    data = json.loads(f.read_text()).get("plugins", {})
    return {os.path.realpath(e["installPath"]): key for key, v in data.items() for e in v}


def targets(paths):
    """realpath -> stable name. A folder inside another target is already covered by that scan."""
    names = plugins()
    if paths:
        found = {os.path.realpath(p): None for p in paths}
    else:
        skills = home() / "skills"
        found = {os.path.realpath(p): None for p in (skills.iterdir() if skills.is_dir() else []) if p.is_dir()}
        found.update(dict.fromkeys(names))
    keep = [p for p in found if not any(p != q and p.startswith(q + "/") for q in found)]
    return {p: names.get(p) or Path(p).name for p in sorted(keep)}


def run_scan(path, out, mode):
    """Scan into out via a temp name; returns None on success, else why it failed."""
    part = out.with_name(out.name + ".part")
    part.unlink(missing_ok=True)
    cmd = ["skillspector", "scan", path, "--format", "json", "-o", str(part)]
    env = dict(os.environ)
    if mode == "static":
        cmd.append("--no-llm")
    else:
        env["SKILLSPECTOR_PROVIDER"] = "claude_cli"
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=TIMEOUT[mode])
    except subprocess.TimeoutExpired:
        part.unlink(missing_ok=True)
        return f"timeout after {TIMEOUT[mode]} s"
    if load(part) is None:
        part.unlink(missing_ok=True)
        return f"exit {r.returncode}, no readable report: {r.stderr.strip()[-200:]}"
    part.rename(out)
    return None


def load(f):
    try:
        return json.loads(f.read_text())
    except (OSError, ValueError):
        return None


def norm(s):
    return re.sub(r"\d+", "N", s)


def kept(report, name):
    """(key, file:line, text) of every HIGH/CRITICAL finding outside the noise paths."""
    rows = []
    for i in report.get("issues", []):
        loc = i.get("location") or {}
        if i.get("severity") not in ("HIGH", "CRITICAL") or NOISE.search(loc.get("file") or ""):
            continue
        text = (i.get("finding") or i.get("code_snippet") or "").strip()
        key = (name, i["severity"], norm(i.get("pattern") or "?"), norm(text))
        rows.append((key, f"{loc.get('file')}:{loc.get('start_line')}", text))
    return rows


def show(key, where, text):
    return f"{key[0]}  {key[1]} {key[2][:100]} @ {where}: {' '.join(text.split())[:120]}"


def scan_pass(mode, tgts, accept):
    out = state() / datetime.date.today().isoformat() / mode
    out.mkdir(parents=True, exist_ok=True)

    def one(p):
        f = out / (p.replace(str(Path.home()), "~").strip("/").replace("/", "__") + ".json")
        if load(f) is not None:
            return p, f, None
        return p, f, run_scan(p, f, mode)

    rows, failed = [], 0
    with ThreadPoolExecutor(WORKERS[mode]) as pool:
        for p, f, err in pool.map(one, tgts):
            if err:
                failed += 1
                print(f"FAIL {mode} {p}: {err}")
            else:
                rows += kept(load(f), tgts[p])
    bf = state() / "baseline.json"
    base = load(bf) or {}
    known = {tuple(k) for k in base.get(mode, [])}
    if accept:
        known |= {k for k, _, _ in rows}
        base[mode] = sorted(known)
        bf.write_text(json.dumps(base, indent=1) + "\n")
        print(f"{mode}: baseline holds {len(known)} findings")
        return failed
    new = [r for r in rows if r[0] not in known]
    for r in new:
        print(show(*r))
    print(f"{mode}: {len(tgts)} targets, {len(new)} new serious findings, {failed} failed")
    return failed + len(new)


def against(installed, candidate):
    live = Path(installed) if "/" in installed else home() / "skills" / installed
    name = plugins().get(os.path.realpath(live)) or live.name
    with tempfile.TemporaryDirectory() as tmp:
        sides = {"installed": os.path.realpath(live), "candidate": os.path.realpath(candidate)}
        files = {s: Path(tmp) / f"{s}.json" for s in sides}

        def one(s):
            if s == "installed" and not os.path.isdir(sides[s]):
                return s, None  # a new skill: every candidate finding counts as added
            return s, run_scan(sides[s], files[s], "static")

        with ThreadPoolExecutor(2) as pool:
            errs = dict(pool.map(one, sides))
        bad = [s for s, e in errs.items() if e]
        if bad:
            for s in bad:
                print(f"scan failed: {s} ({errs[s]})")
            return 1
        old = {k for k, _, _ in kept(load(files["installed"]), name)} if files["installed"].exists() else set()
        added = [r for r in kept(load(files["candidate"]), name) if r[0] not in old]
    for r in added:
        print(show(*r))
    if not added:
        print("no new findings")
    return 1 if added else 0


def main(argv):
    err = pinned()
    if err:
        print(err)
        return 2
    if argv[:1] == ["--against"]:
        if len(argv) != 3:
            print("usage: skill-scan --against <installed name or path> <candidate path>")
            return 2
        return against(argv[1], argv[2])
    accept = "--accept" in argv
    argv = [a for a in argv if a != "--accept"]
    mode = argv.pop(0) if argv and argv[0] in ("static", "llm", "both") else "static"
    tgts = targets(argv)
    bad = 0
    for m in (("static", "llm") if mode == "both" else (mode,)):
        bad += scan_pass(m, tgts, accept)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
