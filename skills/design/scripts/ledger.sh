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
import json, os, re, subprocess, sys, time, pathlib

# The active pointer is PER SESSION. It used to be one global file, so two sessions each
# running /design fought over it: the last `init` won, and the other session's Stop hook
# then gated on a ledger from a repo it was not in, citing steps it never ran. Observed
# live with two real runs 77 seconds apart.
#
# CLAUDE_CODE_SESSION_ID is set in the hook and tool environment and matches the session's
# transcript filename. Falling back to "global" keeps a bare shell invocation working.
SESSION = os.environ.get("CLAUDE_CODE_SESSION_ID") or "global"
_CDIR   = pathlib.Path.home() / ".claude"
POINTER = _CDIR / f".design-active-{SESSION}"   # cleared when the gate passes
LAST    = _CDIR / f".design-last-{SESSION}"     # never cleared, so 'show' still works after


def _sweep_stale_pointers(days=7):
    """Session pointers outlive their sessions. Drop ones older than a week."""
    import time as _t
    cutoff = _t.time() - days * 86400
    for f in _CDIR.glob(".design-active-*"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass

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

def stale_files(target, report):
    """Files the audit COVERED that changed after it ran.

    This used to walk the whole target tree, so any edit anywhere invalidated the audit -
    touching a data-layer module, or just running the test suite, blocked a design gate that
    had examined two styled-components files. On the first real run it flagged 5 files, none
    of which the audit had looked at. A gate that cries wolf teaches people to bypass gates.

    Scope to the paths the report itself names. If it names none, fall back to the whole tree
    and SAY SO, because an unscoped check is still better than no check.
    """
    rmt = report.stat().st_mtime
    text = report.read_text(errors="replace")
    covered, seen = [], set()
    for m in re.finditer(r"[\w./-]+\.(?:tsx?|jsx?|mjs|cjs|vue|svelte|astro|css|scss|less|"
                         r"styl|html|php|erb|heex|templ|json|md)\b", text):
        rel = m.group(0).lstrip("./")
        if rel in seen:
            continue
        seen.add(rel)
        fp = target / rel
        if fp.is_file():
            covered.append(fp)

    if covered:
        return [str(f) for f in covered if f.stat().st_mtime > rmt + 1]

    # Nothing citable in the report - fall back to the tree walk.
    skip = {".design", ".git", "node_modules", "dist", "build", ".next", ".venv", "coverage"}
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [x for x in dirs if x not in skip]
        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.path.getmtime(fp) > rmt + 1:
                    out.append(fp)
            except OSError:
                pass
    return out


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

    # Both pipelines write run.json. Initialising /design in a repo that just finished
    # /brand-system would silently destroy the brand run's evidence - every step's
    # reasoning, the competitor arc, the type provenance. Archive it instead. The receipt
    # is the point of the ledger; overwriting one to start another defeats it.
    if run.exists():
        try:
            prev = json.loads(run.read_text())
            tag = prev.get("pipeline", "run")
            stamp = (prev.get("started", "") or time.strftime("%Y-%m-%dT%H:%M:%S")).replace(":", "").replace("-", "")
            archive = d / f"run-{tag}-{stamp}.json"
            archive.write_text(json.dumps(prev, indent=2) + "\n")
            print(f"archived the previous {tag} ledger -> {archive.name}")
        except Exception as e:
            die(f"refusing to overwrite {run}: it exists and could not be archived ({e}).\n"
                f"Move it aside by hand, then re-run init.")

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
    _sweep_stale_pointers()
    POINTER.write_text(str(run) + "\n")
    LAST.write_text(str(run) + "\n")
    print(f"ledger initialised ({pipeline}): {run}")
    print(f"session: {SESSION}")
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
    # Count re-runs of a step. An audit that keeps re-opening is the failure mode this
    # pipeline hit on its first real use: nine design-gate passes over one file in ninety
    # minutes, each triggered by the last one's findings. Prose budgets did not stop it.
    prev = doc["steps"].get(step, {})
    runs = prev.get("runs", 0) + 1
    doc["steps"][step] = {"status": status, "evidence" if status == "RAN" else "reason": val,
                          "runs": runs}
    save(p, doc)
    if runs >= 3:
        print(f"BUDGET: '{step}' has now been closed {runs} times.\n"
              f"        Three passes is the budget. Do not open another - report what stands\n"
              f"        and hand the remaining findings to the human as a list. An artifact\n"
              f"        that survived three audits needs a decision, not a fourth audit.",
              file=sys.stderr)
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
                stale = stale_files(target, art)
                if stale:
                    shown = "\n      ".join(stale[:8])
                    more = f"\n      ... and {len(stale) - 8} more" if len(stale) > 8 else ""
                    failures.append(f"{len(stale)} audited file(s) changed after the gate ran:"
                                    f"\n      {shown}{more}\n      Re-run the gate over these.")

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
