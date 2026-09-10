#!/usr/bin/env bash
# Run ledger. One row per step, per run. Shared by /design and /brand-system.
#
#   ledger.sh init <target-dir> [--pipeline design|brand]
#   ledger.sh set <step> RAN <evidence>      close a row with a path or a quoted token
#   ledger.sh set <step> SKIPPED <reason>    close a row with a reason from the closed set
#   ledger.sh show [path]                    render the table (this is the closing report)
#   ledger.sh check [path]                   gate check; prints failures, exit 1 if not clean
#   ledger.sh done                           clear the active pointer
#
# State: <target>/.design/run.json. Active pointer: ~/.claude/.design-active
set -euo pipefail
exec python3 - "$@" <<'PY'
import json, os, subprocess, sys, time, pathlib

POINTER = pathlib.Path.home() / ".claude" / ".design-active"   # cleared when the gate passes
LAST    = pathlib.Path.home() / ".claude" / ".design-last"     # never cleared, so 'show' still works after

# Each pipeline: ordered steps -> the reasons that step may legally be skipped.
# An empty tuple means never. Free prose is what makes a skip unfalsifiable, so there is none.
PIPELINES = {
    "design": {
        "steps": {
            "detect":     (),
            "reference":  ("user-supplied-reference", "no-source-available"),
            "direction":  (),
            "tokens":     (),
            "source":     ("no-component-need", "hand-roll-justified", "magic-mcp-unavailable"),
            "assemble":   (),
            "assets":     ("no-imagery-needed", "assets-supplied"),
            "motion":     ("no-motion-warranted", "reduced-motion-only"),
            "gate":       (),
            "conversion": ("not-marketing-surface",),
        },
        # the gate step, plus an artifact that must exist, be non-empty, and be newer than
        # every file under the target (so editing after the audit re-opens the gate).
        "gate": {"step": "gate", "artifact": ".design/audit-report.md", "staleness": True},
    },
    "brand": {
        "steps": {
            "brief":     (),
            "reference": ("no-client-material",),
            "direction": (),
            "type":      (),
            "color":     (),
            "logo":      ("logo-supplied",),
            "imagery":   ("no-imagery-scope",),
            "surfaces":  (),
            "audit":     (),
            "emit":      (),
            "signoff":   ("internal-project",),
        },
        # Stronger than design's: a brand board has a checkable SHAPE, so the gate runs a
        # validator instead of only proving a file exists.
        # Overridable: this repo is public and the default names one machine's layout.
        # Set BRAND_VALIDATOR to point at check-brand-system.py wherever it lives.
        "gate": {"step": "emit", "artifact": "brand-system.html", "staleness": False,
                 "validator": os.environ.get("BRAND_VALIDATOR") or str(
                     pathlib.Path.home() /
                     "projects/freelance/website-build-templates/scripts/check-brand-system.py")},
    },
}

def die(msg, code=1):
    print(msg, file=sys.stderr); sys.exit(code)

def ledger_path(explicit=None):
    # explicit arg, then the active run, then walk up from cwd, then the last run.
    # The last-run fallback is what lets 'show' print the closing table after the gate
    # has passed and cleared the active pointer.
    if explicit:
        p = pathlib.Path(explicit).resolve()
        if p.is_dir():
            p = p / ".design" / "run.json"
        if p.exists():
            return p
        die(f"no ledger at {p}")
    for ptr in (POINTER, LAST):
        if ptr.exists():
            p = pathlib.Path(ptr.read_text().strip())
            if p.exists():
                return p
        cur = pathlib.Path.cwd().resolve()
        for d in [cur, *cur.parents]:
            cand = d / ".design" / "run.json"
            if cand.exists():
                return cand
    die("no run found - run 'ledger.sh init <target> [--pipeline design|brand]' first")

def find_artifact(target, name):
    """Locate the gate artifact. It is NOT always at the target root: a real project
    keeps brand-system.html in brand/, and hardcoding <target>/<name> blocked a run
    whose board was present, complete and passing the contract."""
    direct = target / name
    if direct.exists():
        return direct
    skip = {".git", "node_modules", "dist", "build", ".next", ".venv", ".design", "public"}
    best = None
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in skip]
        if name in files:
            cand = pathlib.Path(root) / name
            # prefer the shallowest match, so a stray copy deep in the tree never wins
            if best is None or len(cand.parts) < len(best.parts):
                best = cand
    return best


def steps_of(doc):
    return PIPELINES[doc.get("pipeline", "design")]["steps"]

def save(p, d):
    p.write_text(json.dumps(d, indent=2) + "\n")

argv = sys.argv[1:]
if not argv:
    die("usage: ledger.sh init|set|show|check|done")
cmd = argv[0]

if cmd == "init":
    if len(argv) < 2: die("usage: ledger.sh init <target-dir> [--pipeline design|brand]")
    pipeline = "design"
    if "--pipeline" in argv:
        i = argv.index("--pipeline")
        pipeline = argv[i + 1] if len(argv) > i + 1 else ""
        argv = argv[:i] + argv[i + 2:]
    if pipeline not in PIPELINES:
        die(f"unknown pipeline '{pipeline}'. known: {', '.join(PIPELINES)}")
    target = pathlib.Path(argv[1]).resolve()
    d = target / ".design"
    d.mkdir(parents=True, exist_ok=True)
    run = d / "run.json"
    doc = {
        "pipeline": pipeline,
        "target": str(target),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "steps": {k: {"status": "PENDING"} for k in PIPELINES[pipeline]["steps"]},
        "blocks": 0,
        "escaped": False,
    }
    save(run, doc)
    POINTER.parent.mkdir(parents=True, exist_ok=True)
    POINTER.write_text(str(run) + "\n")
    LAST.write_text(str(run) + "\n")
    print(f"ledger initialised ({pipeline}): {run}")
    print("steps: " + ", ".join(PIPELINES[pipeline]["steps"]))

elif cmd == "set":
    if len(argv) < 4: die("usage: ledger.sh set <step> RAN|SKIPPED <evidence-or-reason>")
    step, status, val = argv[1], argv[2].upper(), " ".join(argv[3:])
    p = ledger_path(); doc = json.loads(p.read_text()); STEPS = steps_of(doc)
    if step not in STEPS: die(f"unknown step '{step}'. known: {', '.join(STEPS)}")
    if status not in ("RAN", "SKIPPED"): die("status must be RAN or SKIPPED")
    if status == "SKIPPED":
        allowed = STEPS[step]
        if not allowed:
            die(f"step '{step}' may never be skipped. Run it.")
        if val not in allowed:
            die(f"'{val}' is not a legal skip reason for '{step}'. legal: {', '.join(allowed)}")
    doc["steps"][step] = {"status": status, "evidence" if status == "RAN" else "reason": val}
    save(p, doc)
    # The active pointer is global, so a mutation from inside project B used to land in
    # project A's ledger with no sign. Always print the resolved path, and say so loudly
    # when the ledger being written is not the tree you are standing in.
    cwd = pathlib.Path.cwd().resolve()
    tgt = pathlib.Path(doc["target"]).resolve()
    off = not (cwd == tgt or tgt in cwd.parents or cwd in tgt.parents)
    print(f"{step}: {status} ({val})  -> {p}")
    if off:
        print(f"WARNING: that ledger targets {tgt}, which is not the tree you are in ({cwd}).\n"
              f"         If this is a different project, run 'ledger.sh init' for it first.",
              file=sys.stderr)

elif cmd in ("show", "check"):
    p = ledger_path(argv[1] if len(argv) > 1 else None)
    doc = json.loads(p.read_text())
    STEPS = steps_of(doc)
    G = PIPELINES[doc.get("pipeline", "design")]["gate"]
    rows, failures = [], []
    for step in STEPS:
        s = doc["steps"].get(step, {"status": "PENDING"})
        rows.append((step, s["status"], s.get("evidence") or s.get("reason") or ""))
        if s["status"] == "PENDING":
            failures.append(f"step '{step}' is still PENDING")
        elif s["status"] == "SKIPPED" and s.get("reason") not in STEPS[step]:
            failures.append(f"step '{step}' skipped with illegal reason '{s.get('reason')}'")

    gate = doc["steps"].get(G["step"], {})
    target = pathlib.Path(doc["target"])
    if gate.get("status") != "RAN":
        failures.append(f"the '{G['step']}' step did not run - it may never be skipped")
    else:
        art = find_artifact(target, G["artifact"])
        if art is None:
            failures.append(f"gate artifact not found anywhere under {target}: {G['artifact']}")
        elif art.stat().st_size == 0:
            failures.append(f"gate artifact is empty: {art}")
        else:
            if G.get("validator"):
                # A brand board has a checkable shape, so prove conformance, not existence.
                if not pathlib.Path(G["validator"]).exists():
                    # NOT a contract violation. The board may be perfect; the checker is
                    # absent. Saying "does not conform" here would be the same absent-answer
                    # -as-definite-answer defect this gate exists to prevent.
                    failures.append(f"brand validator not installed: {G['validator']}\n"
                                    "      The board's SHAPE was not checked. Install the "
                                    "validator or close this row by hand with a stated reason.")
                else:
                    try:
                        r = subprocess.run(["uv", "run", "--no-project", "--with", "jsonschema==4.25.1",
                                            "python3", G["validator"], str(art)],
                                           capture_output=True, text=True, timeout=120)
                    except subprocess.TimeoutExpired:
                        failures.append("brand validator timed out after 120s - shape NOT checked")
                    else:
                        if r.returncode != 0:
                            head = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][:6]
                            failures.append("brand board does not conform to the output contract:\n      "
                                            + "\n      ".join(head))
            if G.get("staleness"):
                rmt, stale = art.stat().st_mtime, []
                for root, dirs, files in os.walk(target):
                    dirs[:] = [x for x in dirs if x not in
                               (".design", ".git", "node_modules", "dist", "build", ".next", ".venv")]
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            if os.path.getmtime(fp) > rmt + 1: stale.append(fp)
                        except OSError:
                            pass
                    if len(stale) > 3: break
                if stale:
                    failures.append(f"{len(stale)} file(s) changed after the gate ran, "
                                    f"e.g. {stale[0]} - re-run it")

    if cmd == "show":
        w = max(len(r[0]) for r in rows)
        print(f"{'step'.ljust(w)}  status   evidence / reason")
        for step, status, detail in rows:
            print(f"{step.ljust(w)}  {status.ljust(7)}  {detail}")
        if doc.get("escaped"):
            print("\nNOTE: this run was released by the gate escape hatch. It was NOT fully audited.")
    else:
        for f in failures: print(f"BLOCKED: {f}")
        sys.exit(1 if failures else 0)

elif cmd == "done":
    if POINTER.exists(): POINTER.unlink()
    print("run closed")

else:
    die(f"unknown command '{cmd}'")
PY
