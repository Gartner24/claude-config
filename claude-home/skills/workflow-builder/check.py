#!/usr/bin/env python3
"""Spec 0076 AC-5: check one workflow in claude-home/workflows/<name>/.

  check.py <name>   one line per problem and exit 1, else `ok` and exit 0
  check.py --test   self checks: a good workflow passes, and each fixture breaks it one way

CLAUDE_HOME_DIR (the repo's claude-home/) and CLAUDE_LIVE_DIR (~/.claude) are for the self checks only.
Python 3 standard library only; the script itself is read by node (walk.mjs beside this file).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME_DIR = Path(os.environ.get("CLAUDE_HOME_DIR") or HERE.parents[1])
LIVE = Path(os.environ.get("CLAUDE_LIVE_DIR") or Path.home() / ".claude")
SECTIONS = ("Inputs", "Process", "Outputs", "Human check", "Do NOT load")
# ICM's 2,000 to 8,000 tokens a stage; the root plus the largest stage must fit, references/ left out on purpose
TOKEN_CAP = 8000
STAGE = re.compile(r"^\d\d_[a-z0-9][a-z0-9-]*$")


def sections(text):
    """`## Title` -> body lines (stripped, empty ones dropped)."""
    out, cur = {}, None
    for ln in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None and ln.strip():
            out[cur].append(ln.strip())
    return out


def model_line(text):
    m = re.search(r"^Model:\s*(\S+)\s+(\S+)\s*$", text, re.M)
    return (m.group(1), m.group(2)) if m else None


def input_paths(lines):
    """Backticked paths in the Inputs section that the check can resolve; placeholders and run outputs skipped."""
    for ln in lines:
        for p in re.findall(r"`([^`]+)`", ln):
            if "<" in p or "{" in p or ".workflow/runs/" in p:
                continue
            if p.startswith("~/.claude/workflows/"):
                yield p, HOME_DIR / p[len("~/.claude/"):]
            elif p.startswith("~/.claude/"):
                yield p, LIVE / p[len("~/.claude/"):]
            elif p.startswith("claude-home/"):
                yield p, HOME_DIR.parent / p


def walk(script):
    with tempfile.TemporaryDirectory() as tmp:
        # A workflow body runs inside an async function (top level await and return), so node checks it wrapped.
        body = re.sub(r"^export\s+const\s+meta\b", "const meta", script.read_text(), count=1, flags=re.M)
        wrapped = Path(tmp) / "wrapped.cjs"
        wrapped.write_text("(async function () {\n" + body + "\n})\n")
        r = subprocess.run(["node", "--check", str(wrapped)], capture_output=True, text=True)
        if r.returncode:
            err = [ln for ln in r.stderr.splitlines() if "Error" in ln]
            return None, f"{script.name}: syntax error: {(err or ['node --check failed'])[0].strip()}"
    r = subprocess.run(["node", str(HERE / "walk.mjs"), str(script)], capture_output=True, text=True)
    if r.returncode:
        return None, f"{script.name}: could not be read: {r.stderr.strip().splitlines()[-1:]}"
    return json.loads(r.stdout), None


def check(name):
    wf = HOME_DIR / "workflows" / name
    if not wf.is_dir():
        return [f"{name}: no folder {wf}"]
    problems = []
    stages_dir = wf / "stages"
    folders = sorted(p.name for p in stages_dir.iterdir() if p.is_dir()) if stages_dir.is_dir() else []

    root = wf / "CONTEXT.md"
    root_text = root.read_text() if root.exists() else ""
    if not root.exists():
        problems.append("CONTEXT.md: missing")
    table = []
    for ln in root_text.splitlines():
        cells = [c.strip().strip("`") for c in ln.strip().strip("|").split("|")] if ln.lstrip().startswith("|") else []
        if cells and STAGE.match(cells[0]):
            table.append(cells[0])
    for f in sorted(set(table) - set(folders)):
        problems.append(f"CONTEXT.md: stage {f} is in the pipeline table but stages/{f} is missing")
    for f in sorted(set(folders) - set(table)):
        problems.append(f"stages/{f}: not in the CONTEXT.md pipeline table")

    models, largest = {}, 0
    for f in folders:
        ctx = stages_dir / f / "CONTEXT.md"
        if not ctx.exists():
            problems.append(f"stages/{f}/CONTEXT.md: missing")
            continue
        text = ctx.read_text()
        largest = max(largest, len(text))
        sec = sections(text)
        for s in SECTIONS:
            if s not in sec:
                problems.append(f"stages/{f}/CONTEXT.md: no `## {s}` section")
        if "Human check" in sec and len(sec["Human check"]) != 1:
            problems.append(f"stages/{f}/CONTEXT.md: Human check has {len(sec['Human check'])} lines, not exactly one")
        models[f] = model_line(text)
        if models[f] is None:
            problems.append(f"stages/{f}/CONTEXT.md: no `Model: <model> <effort>` line")
        for shown, real in input_paths(sec.get("Inputs", [])):
            if not real.exists():
                problems.append(f"stages/{f}/CONTEXT.md: input {shown} does not exist")
    tokens = (len(root_text) + largest) // 4
    if tokens > TOKEN_CAP:
        problems.append(f"CONTEXT.md plus the largest stage CONTEXT.md is about {tokens} tokens, over {TOKEN_CAP}")

    script = wf / f"{name}.js"
    if not script.exists():
        problems.append(f"{name}.js: missing")
        return problems
    w, err = walk(script)
    if err:
        problems.append(err)
        return problems
    if w["metaError"]:
        problems.append(f"{name}.js: {w['metaError']}")
    else:
        titles = [p.get("title") for p in w["meta"].get("phases") or []]
        if titles != folders:
            problems.append(f"{name}.js: meta phase titles {titles} are not the stage folders {folders} in order")
    for b in w["banned"]:
        problems.append(f"{name}.js:{b['line']}: {b['name']} is not allowed in a workflow script")
    for a in w["agents"]:
        for k in ("schema", "label", "model", "effort"):
            if k not in a["keys"]:
                problems.append(f"{name}.js:{a['line']}: agent( call without {k}")
        want = models.get(a["phase"])
        if a["phase"] not in models:
            problems.append(f"{name}.js:{a['line']}: agent( call is in no stage phase ({a['phase']})")
        elif want and "model" in a["keys"] and "effort" in a["keys"] and (a["model"], a["effort"]) != want:
            problems.append(f"{name}.js:{a['line']}: model and effort {a['model']} {a['effort']} differ from "
                            f"stages/{a['phase']}/CONTEXT.md `Model: {want[0]} {want[1]}`")
    return problems


# ---------------------------------------------------------------- self checks

GOOD_ROOT = """# demo

Demo job.

## Pipeline
| Stage | Job | Input | Output | Human check |
|---|---|---|---|---|
| `01_find` | find items | the repo | items.md | items look right |
| `02_fix` | fix each item | items.md | fixes.md | fixes are small |

## How to start
`/demo`
"""

GOOD_STAGE = """# {stage}

Model: {model} {effort}

## Inputs
- `~/.claude/workflows/demo/CONTEXT.md`: the pipeline
- `claude-home/rules/x.md`: a rule
- `~/.claude/rules/live.md`: a live rule
- `~/.claude/state/<area>/notes.md`: a placeholder, filled at run time
- `<run>/01_find/output/items.md`: the items
- `{{repo}}/.workflow/runs/demo/x/01_find/output/items.md`: same, spelled another way

## Process
1. Do it.

## Outputs
- `<run>/{stage}/output/out.md`

## Human check
The output reads right.

## Do NOT load
- anything else
"""

GOOD_JS = """export const meta = {
  name: 'demo',
  description: 'Demo job',
  phases: [
    { title: '01_find', detail: 'find' },
    { title: '02_fix', detail: 'fix each' },
  ],
}
// a comment naming Date.now( and agent( is not code
for (const key of ['repo', 'runId']) {
  if (args == null || args[key] == null || args[key] === '') throw new Error(`missing arg: ${key}`)
}
const S = {type: 'object', properties: {summary: {type: 'string'}}, required: ['summary']}
phase('01_find')
const found = await agent(`Read the stage. Do not call Math.random( here. ${args.repo}`,
  {label: '01_find', model: 'haiku', effort: 'low', schema: S})
phase('02_fix')
const fixed = (await pipeline([1, 2], (item, _, i) => agent(`fix ${item} ${`nested ${i}`}`, {
  label: `02_fix ${i + 1}`,
  phase: '02_fix',
  model: 'sonnet',
  effort: 'medium',
  schema: S,
  isolation: 'worktree',
}))).filter(Boolean)
return {stages: [found, ...fixed]}
"""


def fixture(tmp, mutate=None):
    home = Path(tmp) / "claude-home"
    live = Path(tmp) / "live"
    wf = home / "workflows" / "demo"
    files = {
        wf / "CONTEXT.md": GOOD_ROOT,
        wf / "stages" / "01_find" / "CONTEXT.md": GOOD_STAGE.format(stage="01_find", model="haiku", effort="low"),
        wf / "stages" / "02_fix" / "CONTEXT.md": GOOD_STAGE.format(stage="02_fix", model="sonnet", effort="medium"),
        wf / "demo.js": GOOD_JS,
        home / "rules" / "x.md": "x\n",
        live / "rules" / "live.md": "x\n",
    }
    for p, body in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    if mutate:
        mutate(wf)
    return home, live


def edit(rel, old, new):
    def go(wf):
        p = wf / rel
        assert old in p.read_text(), (rel, old)
        p.write_text(p.read_text().replace(old, new, 1))
    return go


STAGE2 = "stages/02_fix/CONTEXT.md"
CASES = [
    # (name, mutation, expected problem text)
    ("syntax error", edit("demo.js", "return {", "return {{"), "demo.js: syntax error"),
    ("meta not a literal", edit("demo.js", "name: 'demo'", "name: NAME"), "demo.js: meta is not a literal"),
    ("meta with a call", edit("demo.js", "description: 'Demo job'", "description: String(1)"),
     "demo.js: meta is not a literal"),
    ("meta with interpolation", edit("demo.js", "description: 'Demo job'", "description: `Demo ${1}`"),
     "demo.js: meta is not a literal"),
    ("phase order", edit("demo.js", "{ title: '01_find', detail: 'find' },\n    { title: '02_fix', detail: 'fix each' },",
                         "{ title: '02_fix', detail: 'fix each' },\n    { title: '01_find', detail: 'find' },"),
     "meta phase titles ['02_fix', '01_find'] are not the stage folders ['01_find', '02_fix'] in order"),
    ("Date.now", edit("demo.js", "return {", "const t = Date.now()\nreturn {"), "Date.now( is not allowed"),
    ("Math.random", edit("demo.js", "return {", "const t = Math.random()\nreturn {"), "Math.random( is not allowed"),
    ("new Date()", edit("demo.js", "return {", "const t = new Date()\nreturn {"), "new Date() is not allowed"),
    ("import(", edit("demo.js", "return {", "const t = await import('x')\nreturn {"), "import( is not allowed"),
    ("banned call in ${}", edit("demo.js", "${args.repo}", "${Date.now()}"), "Date.now( is not allowed"),
    ("no schema", edit("demo.js", "effort: 'low', schema: S}", "effort: 'low'}"), "demo.js:15: agent( call without schema"),
    ("no label", edit("demo.js", "{label: '01_find', ", "{"), "demo.js:15: agent( call without label"),
    ("no model", edit("demo.js", "  model: 'sonnet',\n", ""), "demo.js:18: agent( call without model"),
    ("no effort", edit("demo.js", "  effort: 'medium',\n", ""), "demo.js:18: agent( call without effort"),
    ("Model line differs", edit(STAGE2, "Model: sonnet medium", "Model: opus medium"),
     "demo.js:18: model and effort sonnet medium differ from stages/02_fix/CONTEXT.md `Model: opus medium`"),
    ("no Model line", edit(STAGE2, "Model: sonnet medium\n", ""), "no `Model: <model> <effort>` line"),
    ("missing section", edit(STAGE2, "## Do NOT load", "## Never load"), "02_fix/CONTEXT.md: no `## Do NOT load` section"),
    ("two Human check lines", edit(STAGE2, "The output reads right.", "One.\nTwo."),
     "Human check has 2 lines, not exactly one"),
    ("no Human check line", edit(STAGE2, "The output reads right.\n", ""), "Human check has 0 lines, not exactly one"),
    ("input under claude-home missing", edit(STAGE2, "claude-home/rules/x.md", "claude-home/rules/gone.md"),
     "input claude-home/rules/gone.md does not exist"),
    ("input under ~/.claude missing", edit(STAGE2, "~/.claude/rules/live.md", "~/.claude/rules/gone.md"),
     "input ~/.claude/rules/gone.md does not exist"),
    ("workflow input resolved to the repo copy", edit(STAGE2, "workflows/demo/CONTEXT.md", "workflows/demo/GONE.md"),
     "input ~/.claude/workflows/demo/GONE.md does not exist"),
    ("over the token cap", edit(STAGE2, "1. Do it.", "1. " + "word " * 6500), "over 8000"),
    ("stage folder missing", lambda wf: shutil.rmtree(wf / "stages" / "02_fix"),
     "stage 02_fix is in the pipeline table but stages/02_fix is missing"),
    ("stage folder not in the table", edit("CONTEXT.md", "| `02_fix` |", "| `02_mend` |"),
     "stages/02_fix: not in the CONTEXT.md pipeline table"),
]


def fill(text, stage):
    """A template filled the way the builder fills it: follows line stripped, every {{...}} given a value."""
    text = text.split("\n", 1)[1] if text.startswith(("<!-- follows", "// follows")) else text
    for old, new in (("{{name}}", "demo"), ("01_{{stage}}", "01_find"), ("02_{{stage}}", "02_fix"),
                     ("NN_{{stage}}", stage), ("{{model}}", "sonnet"), ("{{effort}}", "medium"),
                     ("{{haiku|sonnet|opus}}", "sonnet"), ("{{low|medium|high}}", "medium"), ("{{named arg}}", "pr")):
        text = text.replace(old, new)
    return re.sub(r"\{\{[^}]*\}\}", "x", text)


def templates(tmp):
    """The builder's own templates, filled, must pass the check: a template change that breaks it shows here."""
    t = HERE / "templates"
    wf = Path(tmp) / "claude-home" / "workflows" / "demo"
    files = {wf / "CONTEXT.md": fill((t / "CONTEXT.md").read_text(), ""), wf / "demo.js": fill((t / "workflow.js").read_text(), "")}
    for s in ("01_find", "02_fix"):
        files[wf / "stages" / s / "CONTEXT.md"] = fill((t / "stage-CONTEXT.md").read_text(), s)
    for p, body in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    return wf.parents[1], Path(tmp) / "live"


def self_test():
    global HOME_DIR, LIVE
    failed = 0
    for name, make in (("good fixture", fixture), ("templates filled", templates)):
        with tempfile.TemporaryDirectory() as tmp:
            HOME_DIR, LIVE = make(tmp)
            got = check("demo")
        if got:
            failed += 1
            print(f"FAIL {name}: {got}")
    for name, mutate, want in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            HOME_DIR, LIVE = fixture(tmp, mutate)
            got = check("demo")
        if not any(want in g for g in got):
            failed += 1
            print(f"FAIL {name}: wanted {want!r}, got {got}")
    print(f"check.py self check: {len(CASES) + 2 - failed} of {len(CASES) + 2} pass")
    if not failed:
        print("check.py self check: ok")
    return 1 if failed else 0


def main(argv):
    if argv == ["--test"]:
        return self_test()
    if len(argv) != 1 or argv[0].startswith("-"):
        print(__doc__.strip())
        return 2
    problems = check(argv[0])
    for p in problems:
        print(p)
    if not problems:
        print("ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
