#!/usr/bin/env bash
# Run ledger. One row per step, per run. Shared by /design and /brand-system.
#
#   ledger.sh init <target-dir> [--pipeline design|brand]
#   ledger.sh set <step> RAN <evidence>      close a row with a path or a quoted token
#   ledger.sh set <step> SKIPPED <reason>    close a row with a reason from the closed set
#   ledger.sh show [path]                    render the table (this is the closing report)
#   ledger.sh check [path]                   gate check; prints failures, exit 1 if not clean,
#                                            exit 3 while paused on the owner's preview
#   ledger.sh await "<what they see>"        pause for the owner's preview (design step 8b)
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
            "preview":    ("not-client-facing",),
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

# Skills each design step must actually INVOKE - through the Skill tool, or the user typing
# the slash command - read back from the session transcript. Each tuple is "any one of";
# "name mode" also requires the args to start with that mode; "prefix-*" matches a family.
#
# Self-reported evidence was the whole failure. The first real client run logged
# "lens=minimalist-ui" and closed a motion step while invoking neither, and the refactor
# silently dropped impeccable's critique and audit from the gate. A skill named in prose is
# not a skill that ran, and reading its SKILL.md with the Read tool is not a run either.
from datetime import datetime

MOTION_SKILLS = ("animate", "transitions-dev", "transitions-polish", "gsap-*", "apple-design",
                 "design-motion-principles", "emil-design-eng", "threejs-*")
REQUIRED = {
    "direction":  [("high-end-visual-design", "minimalist-ui", "industrial-brutalist-ui")],
    "assemble":   [("frontend-design",), ("impeccable",)],
    "assets":     [("assets",)],
    "motion":     [MOTION_SKILLS],
    "gate":       [("design-gate",), ("impeccable critique",), ("impeccable audit",)],
    "conversion": [("cro",)],
}

def required(doc, step, evidence=""):
    groups = list(REQUIRED.get(step, []))
    target = pathlib.Path(doc["target"])
    if step == "direction":
        # Precedence 1 (a signed board) and 3 (a saved direction) need no catalogue skill.
        m = re.search(r"saved=(\S+)", evidence)
        saved = bool(m) and ((target / m.group(1)).exists() or pathlib.Path(m.group(1)).exists())
        if not (saved or find_artifact(target, "brand-system.html")):
            groups.append(("design-dna", "ui-ux-pro-max"))
    if step == "gate" and doc["steps"].get("motion", {}).get("status") == "RAN" and model_invocable("review-animations"):
        groups.append(("review-animations",))
    return groups

def model_invocable(skill):
    # review-animations ships user-only upstream. Requiring a call the model cannot make
    # would trap every unattended run that ships motion, so the requirement switches on only
    # once the local override removing the flag is in place. Until then the gate still
    # demands the report's motion line cite its standards (see check).
    f = _CDIR / "skills" / skill / "SKILL.md"
    try:
        return not re.search(r"^disable-model-invocation:\s*true", f.read_text(errors="replace"), re.M)
    except OSError:
        return False

def invoked(doc):
    """Every (skill, args) this run's sessions invoked since the run started."""
    try:
        since = doc.get("started_epoch") or time.mktime(time.strptime(doc["started"], "%Y-%m-%dT%H:%M:%S"))
    except (KeyError, ValueError):
        since = 0
    proj, files = _CDIR / "projects", []
    for sid in {doc.get("session"), *doc.get("sessions", [])} - {None, "global"}:
        files += [*proj.glob(f"*/{sid}.jsonl"), *proj.glob(f"*/{sid}/subagents/*.jsonl")]
    out = []
    for f in files:
        with open(f, errors="replace") as fh:
            for line in fh:
                if '"Skill"' not in line and "<command-name>" not in line:
                    continue
                try:
                    d = json.loads(line)
                    t = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).timestamp()
                except (ValueError, KeyError, TypeError, AttributeError):
                    continue
                m = d.get("message")
                if t < since or not isinstance(m, dict):
                    continue
                c = m.get("content")
                blocks = c if isinstance(c, list) else [{"type": "text", "text": c}] if isinstance(c, str) else []
                for b in blocks:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_use" and b.get("name") == "Skill":
                        i = b.get("input") or {}
                        out.append((str(i.get("skill", "")).split(":")[-1], str(i.get("args") or "")))
                    elif d.get("type") == "user" and b.get("type") == "text":
                        n = re.search(r"<command-name>/?([\w:.-]+)</command-name>", b.get("text") or "")
                        if n:
                            a = re.search(r"<command-args>(.*?)</command-args>", b["text"], re.S)
                            out.append((n.group(1).split(":")[-1], a.group(1) if a else ""))
    return out

def _hit(token, calls):
    name, _, mode = token.partition(" ")
    return any((n == name or (name.endswith("*") and n.startswith(name[:-1])))
               and (not mode or a.strip().lower().startswith(mode)) for n, a in calls)

def missing(doc, step, evidence="", calls=None):
    if doc.get("pipeline", "design") != "design":
        return []
    calls = invoked(doc) if calls is None else calls
    return [g for g in required(doc, step, evidence) if not any(_hit(t, calls) for t in g)]

def say_missing(step, groups):
    return (f"step '{step}' RAN but these skills were never invoked this run: "
            + "; ".join(" or ".join(f"`{t}`" for t in g) for g in groups)
            + "\n      Invoke each with the Skill tool (a mode goes in args, e.g. skill impeccable,"
            + " args \"critique <surface>\").\n      Reading a SKILL.md or naming it in the evidence"
            + " does not count - this reads the session transcript.")

# Quality gates. Everything above proves the pipeline RAN; none of it proved the result was
# any good. The first client redesign under full enforcement closed every row, passed
# design-gate, and shipped a shell impeccable critique had scored 25/40, scroll motion shrunk
# to a fraction of the owner's named reference, and a paid hero video nothing used.
CRITIQUE_MIN = 0.8   # 32/40 on impeccable's heuristic table
HARNESS_PREFIXES = ("Stop hook feedback", "Another Claude session sent a message",
                    "This session is being continued", "(Re-invocation", "Base directory for this skill",
                    "[Image", "Caveat:", "[Request interrupted")
TEXT_EXT = {".astro", ".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".mjs", ".cjs", ".ts",
            ".tsx", ".jsx", ".vue", ".svelte", ".json", ".md", ".mdx", ".php", ".erb", ".liquid",
            ".twig", ".njk", ".heex", ".templ", ".yml", ".yaml", ".toml"}

def run_since(doc):
    try:
        return doc.get("started_epoch") or time.mktime(time.strptime(doc["started"], "%Y-%m-%dT%H:%M:%S"))
    except (KeyError, ValueError):
        return 0

def owner_reply(doc, since):
    """The first thing a person typed after `since`, or None.

    Main transcripts only: a subagent's user records are its parent's prompts.
    ponytail: a heuristic, not authentication. A /loop wakeup re-injects its prompt as a user
    record, so text already seen before `since` does not count, and harness records are dropped
    by prefix. A new harness message shape would slip through - add its prefix here."""
    msgs = []
    for sid in {doc.get("session"), *doc.get("sessions", [])} - {None, "global"}:
        for f in (_CDIR / "projects").glob(f"*/{sid}.jsonl"):
            with open(f, errors="replace") as fh:
                for line in fh:
                    if '"user"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                        t = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).timestamp()
                    except (ValueError, KeyError, TypeError, AttributeError):
                        continue
                    m = d.get("message")
                    if d.get("type") != "user" or d.get("isSidechain") or not isinstance(m, dict):
                        continue
                    c = m.get("content")
                    texts = [c] if isinstance(c, str) else [b.get("text", "") for b in c
                             if isinstance(b, dict) and b.get("type") == "text"] if isinstance(c, list) else []
                    for x in (s.strip() for s in texts):
                        if x and not x.startswith("<") and not x.startswith(HARNESS_PREFIXES):
                            msgs.append((t, x))
    before = {x for t, x in msgs if t < since}
    after = sorted((t, x) for t, x in msgs if t >= since and x not in before)
    return after[0][1] if after else None

def critique_failures(doc, target):
    """impeccable saves each critique to .impeccable/critique/<stamp>__<slug>.md with its score
    in the front matter. The newest report per slug since init must clear the bar."""
    since, newest = run_since(doc), {}
    for f in (target / ".impeccable" / "critique").glob("*__*.md"):
        if f.stat().st_mtime < since:
            continue
        slug = f.name.split("__", 1)[1]
        if slug not in newest or f.stat().st_mtime > newest[slug].stat().st_mtime:
            newest[slug] = f
    if not newest:
        return ["no impeccable critique report saved this run (.impeccable/critique/) - the gate "
                "grades its score, so the critique has to run on this surface"]
    out = []
    for slug, f in sorted(newest.items()):
        head = f.read_text(errors="replace")[:2000]
        tot = re.search(r"^total_score:\s*(\d+(?:\.\d+)?)", head, re.M)
        mx = re.search(r"^max_score:\s*(\d+(?:\.\d+)?)", head, re.M)
        if not (tot and mx and float(mx.group(1)) > 0):
            out.append(f"critique report has no total_score / max_score: {f.name}")
        elif float(tot.group(1)) / float(mx.group(1)) < CRITIQUE_MIN:
            out.append(f"impeccable critique scored {tot.group(1)}/{mx.group(1)} on {slug[:-3]}; the bar is "
                       f"{round(CRITIQUE_MIN * float(mx.group(1)))}. Improve the design and critique it again - "
                       "fixing its P1 list is not the same as reaching the bar")
    return out

def report_line(rtext, key):
    return next((l.strip() for l in rtext.splitlines() if l.strip().lower().startswith(key + ":")), None)

def reference_failures(target, rtext):
    if not (target / ".design" / "reference-lock.md").exists():
        return []
    line = report_line(rtext, "reference")
    m = line and re.search(r"(\d+)\s+sections?\s+compared.*?(\d+)\s+worse", line, re.I)
    if not m:
        return ["a reference lock exists but the report has no 'reference: <n> sections compared against "
                "<primary>, <m> worse' line - the build was never put beside what it had to match"]
    if int(m.group(1)) == 0:
        return ["the report compared 0 sections against the reference"]
    if int(m.group(2)) > 0:
        return [f"{m.group(2)} section(s) judged worse than the reference - {line[:140]}"]
    return []

def motion_reference_failures(doc, target, rtext):
    row = doc["steps"].get("motion", {})
    if row.get("status") != "RAN" or "register=marketing" not in row.get("evidence", ""):
        return []
    out = []
    mr = target / ".design" / "motion-reference.md"
    if not mr.exists() or mr.stat().st_size == 0:
        out.append("register=marketing but .design/motion-reference.md is missing - the reference's effects were never measured")
    line = report_line(rtext, "motion-reference")
    m = line and re.search(r"(\d+)\s+(?:effects?\s+)?below", line, re.I)
    if not m:
        out.append("marketing motion but the report has no 'motion-reference: <k> effects below reference' line")
    elif int(m.group(1)) > 0:
        out.append(f"{m.group(1)} effect(s) built below the reference's magnitude - {line[:140]}")
    return out

def asset_failures(target):
    """A generated or fetched asset must ship, or say why it does not."""
    mf = target / ".design" / "assets-manifest.json"
    if not mf.exists():
        return ["assets RAN but .design/assets-manifest.json does not exist"]
    try:
        data = json.loads(mf.read_text())
    except ValueError as e:
        return [f"assets manifest is not valid JSON: {e}"]
    items = data.get("assets", []) if isinstance(data, dict) else data
    skip = {".design", ".git", "node_modules", "dist", "build", ".next", ".venv", "assets-src", ".impeccable"}
    parts = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [x for x in dirs if x not in skip]
        for f in files:
            if os.path.splitext(f)[1] in TEXT_EXT:
                try:
                    with open(os.path.join(root, f), errors="replace") as fh:
                        parts.append(fh.read())
                except OSError:
                    pass
    blob, out = "\n".join(parts), []
    for a in items if isinstance(items, list) else []:
        if not isinstance(a, dict) or "unused" in a or re.search(r"reference|rejected|superseded", str(a.get("status", "")), re.I):
            continue
        files = a.get("files") or []
        if not files and (a.get("model") or a.get("source")):
            out.append(f"asset '{a.get('id')}' was generated or fetched but records no shipped files - "
                       "add \"files\": [...] or \"unused\": \"<reason>\"")
        for f in files:
            if pathlib.Path(f).name not in blob:
                out.append(f"asset '{a.get('id')}': {f} is not referenced anywhere in the site")
    return out

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
    # .impeccable holds critique reports written after the audit - not audited files.
    skip = {".design", ".git", "node_modules", "dist", "build", ".next", ".venv", "coverage", ".impeccable"}
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
        except Exception:
            prev = {}
        owner = prev.get("session")
        if owner and owner != SESSION and "--force" not in sys.argv:
            optr = _CDIR / f".design-active-{owner}"
            if optr.exists() and (time.time() - optr.stat().st_mtime) < 86400:
                die(f"session {owner} already has a {prev.get('pipeline','design')} run open here:\n"
                    f"  {target}\n\n"
                    f"Two sessions sharing one ledger overwrite each other silently: this init\n"
                    f"would archive their rows, and they would then write into yours believing\n"
                    f"it is theirs. Neither session gets told.\n\n"
                    f"Finish or stop that run first  ->  bash ledger.sh show {target}\n"
                    f"If it is genuinely dead, delete {optr} or re-run with --force.")
        try:
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
        "session": SESSION,
        "sessions": [SESSION],   # every session that owned this run; adopt appends
        "target": str(target),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "started_epoch": time.time(),   # skill calls before this belong to another run
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
    owner = doc.get("session")
    if owner and owner != SESSION:
        optr = _CDIR / f".design-active-{owner}"
        if optr.exists() and (time.time() - optr.stat().st_mtime) < 86400:
            die(f"refusing to write: this ledger belongs to session {owner}, still open.\n"
                f"  {p}\n"
                f"Run 'ledger.sh init <target>' for your own run, or wait for that one to end.")
    if step not in STEPS: die(f"unknown step '{step}'. known: {', '.join(STEPS)}")
    if status not in ("RAN", "SKIPPED"): die("status must be RAN or SKIPPED")
    if status == "SKIPPED":
        allowed = STEPS[step]
        if not allowed:
            die(f"step '{step}' may never be skipped. Run it.")
        if val not in allowed:
            die(f"'{val}' is not a legal skip reason for '{step}'. legal: {', '.join(allowed)}")
    # Motion must be built by a motion skill, not freehanded. The first real run shipped a
    # scroll-driven animation while invoking zero motion skills; the routing was prose only.
    # A named skill in the evidence is a floor, not proof of invocation - same contract as
    # the closed skip vocabulary.
    if step == "motion" and status == "RAN" and doc.get("pipeline", "design") == "design":
        if not re.search(r"skill=(animate|transitions-dev|transitions-polish|gsap-[a-z]+|"
                         r"apple-design|design-motion-principles|emil-design-eng|threejs-[a-z]+)\b", val):
            die("motion RAN needs the skill that built it, as skill=<name>, e.g.\n"
                "  ledger.sh set motion RAN \"skill=animate; <what animates and why>\"\n"
                "Known: animate, transitions-dev, transitions-polish, gsap-*, apple-design,\n"
                "design-motion-principles, emil-design-eng, threejs-*. If nothing earned motion,\n"
                "skip it as no-motion-warranted.")
        # Product-UI motion standards (300ms, restraint) applied to a marketing site's scroll
        # motion is how the owner's named reference got rebuilt too faint to notice.
        reg = re.search(r"register=(product-ui|marketing)\b", val)
        if not reg:
            die("motion RAN needs its register: register=product-ui (menus, dialogs, hover, toasts) or\n"
                "register=marketing (scroll reveals, parallax, pinned sequences, smooth scroll).")
        mr = pathlib.Path(doc["target"]) / ".design" / "motion-reference.md"
        if reg.group(1) == "marketing" and (not mr.exists() or mr.stat().st_size == 0):
            die("register=marketing needs .design/motion-reference.md first: every effect of the motion\n"
                "reference measured (distance, scroll range or duration, easing, smooth scroll, pin length)\n"
                "beside what we built. See /design step 8.")
    design = doc.get("pipeline", "design") == "design"
    if design and status == "RAN" and step in ("assemble", "assets", "motion") \
            and doc["steps"].get("preview", {}).get("status") == "PENDING":
        die(f"'{step}' closes when the whole surface is built, and the rest of the surface is built only\n"
            "after the owner has seen the first finished section. Build that one section, then:\n"
            "  ledger.sh await \"<what they are looking at>\"   (step 8b)")
    if design and step == "preview" and status == "RAN":
        aw = doc.get("awaiting")
        if not aw:
            die("preview RAN needs the owner to have seen it. Run ledger.sh await \"<what they are looking\n"
                "at>\", show the screenshots, end the turn, and close this row after they reply.")
        said = owner_reply(doc, aw["since"])
        if said is None:
            die("the owner has not replied since the preview was posted. End the turn and wait.")
        val = f"{val} | owner: {said[:160]}"
        doc.pop("awaiting", None)
    if status == "RAN":
        gaps = missing(doc, step, val)
        if gaps:
            die(say_missing(step, gaps))
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
    # Paused on the owner's preview: exit 3 lets the Stop hook end the turn. The moment they
    # reply this stops applying, so a session that stops again without closing the row is blocked.
    aw = doc.get("awaiting")
    if cmd == "check" and aw and owner_reply(doc, aw["since"]) is None:
        print(f"AWAITING OWNER since {time.strftime('%H:%M', time.localtime(aw['since']))}: {aw.get('what', '')}")
        sys.exit(3)
    rows, failures = [], []
    calls = invoked(doc) if cmd == "check" and doc.get("pipeline", "design") == "design" else []
    for step in STEPS:
        s = doc["steps"].get(step, {"status": "PENDING"})
        rows.append((step, s["status"], s.get("evidence") or s.get("reason") or ""))
        if s["status"] == "PENDING":
            failures.append(f"step '{step}' is still PENDING")
        elif s["status"] == "RAN" and cmd == "check":
            # Re-verified here, not only at `set`: a hand-edited row never went through set.
            gaps = missing(doc, step, s.get("evidence", ""), calls)
            if gaps:
                failures.append(say_missing(step, gaps))
        elif s["status"] == "SKIPPED" and s.get("reason") not in STEPS[step]:
            failures.append(f"step '{step}' skipped with illegal reason '{s.get('reason')}'")
    if cmd == "check" and doc.get("pipeline", "design") == "design" \
            and doc["steps"].get("assets", {}).get("status") == "RAN":
        failures += asset_failures(pathlib.Path(doc["target"]))

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
            if doc.get("pipeline", "design") == "design":
                # The report must say what it concluded about motion. A run that built motion
                # must have that motion audited against review-animations' standards - "this
                # round added zero animation" is not an audit of the animation that exists.
                rtext = art.read_text(errors="replace")
                mline = next((l for l in rtext.splitlines() if l.strip().lower().startswith("motion:")), None)
                mrow = doc["steps"].get("motion", {})
                if mline is None:
                    failures.append("audit report has no 'motion:' line - motion was not reported on")
                elif mrow.get("status") == "RAN" and "review-animations" not in mline:
                    failures.append("motion step RAN but the report's motion line does not cite "
                                    "review-animations standards:\n      " + mline.strip()[:120])
                failures += critique_failures(doc, target)
                failures += reference_failures(target, rtext)
                failures += motion_reference_failures(doc, target, rtext)
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
        elif doc.get("escape_cleared"):
            print(f"\nNOTE: this run was released by the escape hatch once, then passed the full gate at {doc['escape_cleared']}.")
    else:
        for f in failures: print(f"BLOCKED: {f}")
        if not failures and doc.get("escaped"):
            # The mark says "not audited". A later full pass makes that false; keep the history.
            doc["escaped"] = False
            doc["escape_cleared"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            save(p, doc)
        sys.exit(1 if failures else 0)

elif cmd == "adopt":
    # Take ownership of an existing ledger from THIS session, without re-initialising it.
    # A run started before per-session pointers existed has no owner and no pointer, so its
    # gate sits inert. This adopts it in place - no restart, no lost rows. Also the upgrade
    # path for anyone whose run predates that change.
    if len(argv) < 2: die("usage: ledger.sh adopt <target-dir>")
    target = pathlib.Path(argv[1]).resolve()
    run = target / ".design" / "run.json"
    if not run.exists(): die(f"no ledger at {run}")
    doc = json.loads(run.read_text())
    owner = doc.get("session")
    if owner and owner != SESSION:
        optr = _CDIR / f".design-active-{owner}"
        if optr.exists() and (time.time() - optr.stat().st_mtime) < 86400:
            die(f"session {owner} still owns this ledger. Stop that run first, or delete {optr}.")
    # Keep the previous owners: skills they invoked for this run are still in THEIR transcript.
    doc["sessions"] = sorted({*doc.get("sessions", []), *([owner] if owner else []), SESSION})
    doc["session"] = SESSION
    # Re-arming a run the escape hatch released: gate.sh counts blocks on the ledger, so a count
    # left at 3 would release it again on the very next stop and the re-armed gate would never block.
    doc["blocks"] = 0
    save(run, doc)
    POINTER.parent.mkdir(parents=True, exist_ok=True)
    POINTER.write_text(str(run) + "\n")
    LAST.write_text(str(run) + "\n")
    op = [k for k, v in doc["steps"].items() if v["status"] == "PENDING"]
    print(f"adopted {doc.get('pipeline','design')} run at {run}")
    print(f"  session: {SESSION}")
    print(f"  open rows: {', '.join(op) if op else 'none'}")

elif cmd == "await":
    # Pause for the owner: the preview (step 8b), or any other decision only they can make mid-run.
    # check returns 3 until they reply, so the Stop hook lets the turn end instead of spending its
    # three blocks on a question only a person can answer. This used to work for the preview row
    # alone; a second question (pick a pattern: A, B or C) exhausted the blocks and released the
    # run as unaudited.
    if len(argv) < 2: die('usage: ledger.sh await "<what the owner is looking at>"')
    p = ledger_path(); doc = json.loads(p.read_text())
    doc["awaiting"] = {"since": time.time(), "what": " ".join(argv[1:])}
    save(p, doc)
    print("Waiting for the owner. Show the screenshots, the motion and the reference beside them, ask\n"
          "one question, then END THE TURN. Do not build the rest of the surface. In a /loop do not\n"
          "schedule a wakeup - their reply resumes the run. Then: ledger.sh set preview RAN \"<their words>\"")

elif cmd == "done":
    if POINTER.exists(): POINTER.unlink()
    print("run closed")

else:
    die(f"unknown command '{cmd}'")
PY
