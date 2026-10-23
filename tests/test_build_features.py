"""Spec 0074: the /build-features ready list (ready.py, AC-1, AC-2) and its Workflow script (build-features.js,
AC-5 to AC-8), against the real plan.py and the real script; gh and spec-paths are stubs on PATH."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "claude-home" / "skills" / "build-features"
PLAN = REPO / "claude-home" / "mods" / "chip-dash" / "plan.py"

SCOPE = """\
# Plan
**Workflow:** Beta (after `/develop`: `/check verify`, then `/test`).

### 1. Alpha one thing
Spec [0001](../specs/0001-a.md).
- [x] Design it: `/architect a`
- [ ] Build it: `/develop a`

### 2. Needs design first
Spec [0002](../specs/0002-b.md).
- [ ] Design it: `/architect b`

### 3. Tagged row · needs a decision
Spec [0003](../specs/0003-c.md).
- [ ] Build it: `/develop c`

### 5. No spec here
- [ ] Build it: `/develop e`

### 6. Already started
Spec [0006](../specs/0006-f.md).
- [ ] Build it: `/develop f`

### 7. Superseded spec
Spec [0007](../specs/0007-g.md).
- [ ] Build it: `/develop g`

### 8. Gold tier row · GA
Spec [0008](../specs/0008-h.md).
- [ ] Build it: `/develop h`

## Deferred
### 4. Later maybe
Spec [0004](../specs/0004-d.md).
- [ ] Build it: `/develop d`
"""

STUB_SPEC_PATHS = """\
#!/bin/sh
case "$2 $3" in
  "0001 0008") echo "overlap: a/** meets a/x"; exit 1 ;;
  "0001 0009") echo "overlap: a/** meets a/y"; exit 1 ;;
esac
echo "no overlap"
"""


def sh(*argv, cwd):
    subprocess.run(argv, cwd=cwd, check=True, capture_output=True)


class TestReady(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.repo = t / "repo"
        (self.repo / "docs" / "scope").mkdir(parents=True)
        (self.repo / "docs" / "specs").mkdir()
        (self.repo / "docs" / "scope" / "scope.md").write_text(SCOPE)
        for n, status in (("0001-a", "Proposed"), ("0002-b", "Proposed"), ("0003-c", "Accepted"), ("0004-d", "Proposed"),
                          ("0006-f", "In Progress"), ("0007-g", "Superseded"), ("0008-h", "Accepted")):
            (self.repo / "docs" / "specs" / f"{n}.md").write_text(f"# {n}\n\n**Status**: {status}\n")
        sh("git", "init", "-q", "-b", "main", cwd=self.repo)
        sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init", cwd=self.repo)
        sh("git", "branch", "feat/0006-already-started", cwd=self.repo)
        self.bin = t / "bin"
        self.bin.mkdir()
        self.stub("spec-paths", STUB_SPEC_PATHS)
        self.gh('[{"number": 5, "headRefName": "wip"}, {"number": 9, "headRefName": "feat/0009-other"}]')

    def tearDown(self):
        self.tmp.cleanup()

    def stub(self, name, body):
        p = self.bin / name
        p.write_text(body)
        p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def gh(self, out, code=0):
        self.stub("gh", f"#!/bin/sh\necho '{out}' >&{2 if code else 1}\nexit {code}\n")

    def ready(self):
        env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}", "WF_ROOTS": str(self.repo)}
        r = subprocess.run([sys.executable, "-B", str(SKILL / "ready.py"), "--plan", str(PLAN)], cwd=self.repo,
                           capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    # covers: spec 0074 AC-1 (ready only: not needs a design, not tagged needs a decision, not deferred, spec status
    # Proposed/In Progress/Accepted; row number; no spec listed as not offered; tier from tag, else the header)
    def test_ready_list(self):
        out = self.ready()
        rows = {r["row"]: r for r in out["rows"]}
        self.assertEqual(sorted(rows), [1, 5, 6, 8])
        self.assertTrue(rows[1]["offered"])
        self.assertEqual(rows[1]["label"], "row 1 Alpha one thing")
        self.assertEqual((rows[1]["tier"], rows[8]["tier"]), ("Beta", "GA"))
        self.assertEqual(rows[5]["reason"], "no spec, not offered")
        self.assertEqual(out["base"], "main")

    # covers: spec 0074 AC-2 (own branch already exists: already in progress; a pair whose Paths meet; an open PR of
    # another spec that meets; a PR branch with no spec number)
    def test_clashes(self):
        out = self.ready()
        rows = {r["row"]: r for r in out["rows"]}
        self.assertFalse(rows[6]["offered"])
        self.assertEqual(rows[6]["reason"], "already in progress: feat/0006-already-started")
        self.assertEqual(out["pairs"], [{"rows": [1, 8], "text": "overlap: a/** meets a/x"}])
        self.assertIn("may clash with PR #9: overlap: a/** meets a/y", rows[1]["notes"])
        self.assertIn("may clash with PR #5, branch has no spec number", rows[8]["notes"])
        self.assertNotIn("may clash with PR #9: overlap: a/** meets a/y", rows[8]["notes"])

    # covers: spec 0074 AC-2 (an open PR of the row's own spec is already in progress)
    def test_own_pr_in_progress(self):
        self.gh('[{"number": 12, "headRefName": "fix/0001-alpha"}]')
        rows = {r["row"]: r for r in self.ready()["rows"]}
        self.assertEqual(rows[1]["reason"], "already in progress: PR #12")

    # a failed PR list is said on each row, never read as no open PRs
    def test_pr_list_failed(self):
        self.gh("boom", 1)
        out = self.ready()
        self.assertEqual(out["prError"], "boom")
        self.assertIn("open PRs not checked: boom", out["rows"][0]["notes"])


class TestReadyEpic(unittest.TestCase):
    # covers: spec 0074 AC-1 (a tag in a nested epic file is seen; a heading found in no scope file is not offered)
    def test_nested_epic_and_unfound_heading(self):
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t) / "repo"
            (repo / "docs" / "scope" / "epics").mkdir(parents=True)
            (repo / "docs" / "specs").mkdir()
            (repo / "docs" / "scope" / "index.md").write_text("# Plan\n**Workflow:** Beta\n\n- [Epic](epics/a.md)\n")
            (repo / "docs" / "scope" / "epics" / "a.md").write_text(
                "### 1. Tagged nested · needs a decision\nSpec [0001](../../specs/0001-a.md).\n- [ ] Build it: `/develop a`\n\n"
                "### 2. Nested ok · GA\nSpec [0002](../../specs/0002-b.md).\n- [ ] Build it: `/develop b`\n\n"
                "### 3. Commented <!-- note -->\nSpec [0003](../../specs/0003-c.md).\n- [ ] Build it: `/develop c`\n")
            for n in ("0001-a", "0002-b", "0003-c"):
                (repo / "docs" / "specs" / f"{n}.md").write_text(f"# {n}\n\n**Status**: Proposed\n")
            sh("git", "init", "-q", "-b", "main", cwd=repo)
            sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "i", cwd=repo)
            bin_ = Path(t) / "bin"
            bin_.mkdir()
            for name, body in (("gh", "#!/bin/sh\necho '[]'\n"), ("spec-paths", "#!/bin/sh\nexit 0\n")):
                (bin_ / name).write_text(body)
                (bin_ / name).chmod(0o755)
            env = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "WF_ROOTS": str(repo)}
            r = subprocess.run([sys.executable, "-B", str(SKILL / "ready.py"), "--plan", str(PLAN)], cwd=repo,
                               capture_output=True, text=True, env=env, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            rows = {x["row"]: x for x in json.loads(r.stdout)["rows"]}
            self.assertNotIn(1, rows)
            self.assertEqual((rows[2]["offered"], rows[2]["tier"]), (True, "GA"))
            self.assertEqual((rows[3]["offered"], rows[3]["reason"]), (False, "heading not found in scope files"))


HARNESS = textwrap.dedent("""\
    import { readFileSync } from 'node:fs'
    const src = readFileSync(process.argv[1], 'utf8').replace('export const meta', 'const meta')
    const input = JSON.parse(process.argv[2])
    const calls = []
    const agent = async (prompt, opts) => {
      calls.push({ prompt, opts })
      const r = input.answers[calls.length - 1]
      return r === undefined ? null : r
    }
    const parallel = async thunks => Promise.all(thunks.map(t => t().catch(() => null)))
    const run = new (Object.getPrototypeOf(async function () {}).constructor)('args', 'agent', 'parallel', 'phase', 'log', src)
    try {
      const result = await run(input.args, agent, parallel, () => {}, () => {})
      console.log(JSON.stringify({ result, calls }))
    } catch (e) {
      console.log(JSON.stringify({ error: e.message }))
    }
    """)


def row(n, **kw):
    return {"row": n, "feature": f"{n}. Thing number {n}", "spec": f"{n:04d}", "model": "sonnet", "effort": "medium",
            "cores": 4, "tier": "Beta", "base": "main", **kw}


class TestScript(unittest.TestCase):
    def run_script(self, args, answers=()):
        r = subprocess.run(["node", "--input-type=module", "-e", HARNESS, str(SKILL / "build-features.js"),
                            json.dumps({"args": args, "answers": list(answers)})],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    # covers: spec 0074 AC-5 (one worktree agent per row with its model, effort and label; run id in the prompt),
    # AC-6 (step file before each step, the tier chain, branch, draft PR)
    def test_one_agent_per_row(self):
        out = self.run_script({"runId": "20261022-1", "rows": [row(1), row(2, model="opus", effort="high", tier="Alpha")]})
        a, b = out["calls"]
        self.assertEqual({k: a["opts"][k] for k in ("isolation", "model", "effort", "label")},
                         {"isolation": "worktree", "model": "sonnet", "effort": "medium", "label": "row 1 · Thing number 1"})
        self.assertEqual((b["opts"]["model"], b["opts"]["effort"]), ("opus", "high"))
        p = a["prompt"]
        for step in ("develop", "verify", "test", "pr"):
            self.assertIn(f"printf {step} > ~/.claude/state/build-features/20261022-1/row-1.step", p)
        self.assertIn("/check verify Thing number 1", p)
        self.assertIn("/test Thing number 1", p)
        self.assertIn("gh pr create --draft", p)
        self.assertIn("'feat/0001-thing-number-1'", p)
        self.assertNotIn("/test Thing number 2", b["prompt"])

    # covers: spec 0074 AC-6 (a GA agent never runs /review; the merge loop does, once)
    def test_ga_agent_does_not_review(self):
        p = self.run_script({"runId": "r1", "rows": [row(1, tier="GA")]})["calls"][0]["prompt"]
        self.assertNotIn("/review", p)
        self.assertIn("/document pr", p)

    # covers: spec 0074 AC-8 (the row and branch come from the args; an agent that returned nothing is failed)
    def test_results(self):
        lie = {"row": 7, "status": "pr", "branch": "main", "pr_url": "u", "step": "pr", "reason": ""}
        out = self.run_script({"runId": "r1", "rows": [row(1), row(2, feature="2. Fix the thing")]}, [lie])
        self.assertEqual(out["result"][0], {**lie, "row": 1, "branch": "feat/0001-thing-number-1"})
        self.assertEqual(out["result"][1]["status"], "failed")
        self.assertEqual(out["result"][1]["branch"], "fix/0002-fix-the-thing")

    def test_bad_args_refused(self):
        self.assertEqual(self.run_script({"runId": "r1", "rows": [row(1, effort="max")]})["error"],
                         'bad arg: rows[].effort ("max")')
        self.assertEqual(self.run_script({"runId": "r1", "rows": [row(1, base="-x")]})["error"], 'bad arg: rows[].base ("-x")')
        self.assertEqual(self.run_script({"runId": "a b", "rows": [row(1)]})["error"], "bad arg: runId")


if __name__ == "__main__":
    unittest.main()
