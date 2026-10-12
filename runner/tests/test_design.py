"""Spec 0010: design enforcement in `wf run`."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402
from test_run import RunCase  # noqa: E402

GIT_ID = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]
UI = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n- [ ] `/develop a`\n- [ ] Verify it: `/check verify a`\n"
PASSING = "# Design audit\n\nverdict: PASS WITH FINDINGS\n"


def git(repo, *args):
    subprocess.run(["git", *GIT_ID, "-C", str(repo), *args], check=True, capture_output=True)


def report(text, at="."):
    return [os.path.join(at, ".design", "audit-report.md"), text]


class TestFrontendRule(unittest.TestCase):
    # covers: AC-2 (the spec's rule scenario)
    def test_rule(self):
        for p in ("a.tsx", "styles/x.scss", "src/components/b.ts", "src/ui/c.ts", "app/page.tsx", "X.CSS",
                  "web/pages/d.mjs"):
            self.assertTrue(run.is_frontend(p), p)
        for p in ("app/models.ts", "src/lib/d.ts", "x.test.tsx", ".design/e.html", "dist/app.css", "vendor.min.css",
                  "README.md", "lib/ui.ts", "tests/components/a.tsx", "node_modules/x/pages/a.js", "a/build/b.css",
                  "x/src/ui/c.ts"):
            self.assertFalse(run.is_frontend(p), p)


class TestVerdict(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def verdict(self, text):
        p = self.tmp / "r.md"
        p.write_text(text)
        return run.report_verdict(p)

    # covers: AC-4 (last line wins, case, bold, the template line, a note in brackets, unreadable)
    def test_verdicts(self):
        for text, want in [("x\nverdict: FAIL\n", "FAIL"), ("**verdict:** stop\n", "STOP"), ("no line\n", "no verdict"),
                           ("verdict: PASS | PASS WITH FINDINGS | FAIL | STOP\n", "no verdict"),
                           ("verdict: pass (2 should fix)\n", "PASS"), ("verdict: FAIL\nverdict: PASS\n", "PASS"),
                           ("  Verdict: pass with findings\n", "PASS WITH FINDINGS"),
                           ("verdict: FAIL\nverdict: PASS (a | b)\n", "FAIL"), ("verdict: PASSED\n", "no verdict"),
                           (b"verdict: PASS\n\xff\n", "PASS")]:
            with self.subTest(text):
                p = self.tmp / "r.md"
                p.write_bytes(text if isinstance(text, bytes) else text.encode())
                self.assertEqual(run.report_verdict(p), want)
        self.assertEqual(run.report_verdict(self.tmp / "absent.md"), "no verdict")
        self.assertEqual(run.report_verdict(self.tmp), "no verdict")


class TestCandidates(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)

    def put(self, rel, text, ns):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        os.utime(p, ns=(ns, ns))

    # covers: AC-3 (candidates from the file's folder up to the repo root, never above; problems in order)
    def test_candidates(self):
        self.put("apps/web/src/a.tsx", "", 100)
        self.put("apps/admin/b.tsx", "", 100)
        self.put("apps/web/src/.design/audit-report.md", "verdict: FAIL\n", 200)
        self.put(".design/audit-report.md", PASSING, 200)
        reports, problems = run.design_problems(str(self.repo), ["apps/web/src/a.tsx"])
        self.assertEqual((reports, problems), ({".design/audit-report.md": "PASS WITH FINDINGS",
                                               "apps/web/src/.design/audit-report.md": "FAIL"}, []))
        os.remove(self.repo / ".design" / "audit-report.md")
        self.put("apps/web/.design/audit-report.md", PASSING, 200)
        reports, problems = run.design_problems(str(self.repo), ["apps/admin/b.tsx", "apps/web/src/a.tsx"])
        self.assertEqual(problems, [{"path": "apps/admin/b.tsx", "problem": "no report"}])
        self.assertEqual(list(reports), ["apps/web/.design/audit-report.md", "apps/web/src/.design/audit-report.md"])
        # A report above the repo root is never read.
        inner = self.repo / "inner"
        self.put("inner/c.tsx", "", 100)
        _, problems = run.design_problems(str(inner), ["c.tsx"])
        self.assertEqual(problems, [{"path": "c.tsx", "problem": "no report"}])

    # covers: AC-3 (older passing report, the nearest candidate's verdict, equal mtime counts as fresh)
    def test_problems(self):
        self.put("a/x.tsx", "", 300)
        self.put("a/.design/audit-report.md", "verdict: STOP\n", 400)
        self.put(".design/audit-report.md", "nothing\n", 400)
        self.assertEqual(run.design_problems(str(self.repo), ["a/x.tsx"])[1], [{"path": "a/x.tsx", "problem": "verdict STOP"}])
        self.put("a/.design/audit-report.md", "x\n", 400)
        self.assertEqual(run.design_problems(str(self.repo), ["a/x.tsx"])[1], [{"path": "a/x.tsx", "problem": "no verdict"}])
        self.put(".design/audit-report.md", PASSING, 299)
        self.assertEqual(run.design_problems(str(self.repo), ["a/x.tsx"])[1],
                         [{"path": "a/x.tsx", "problem": "older than the file"}])
        self.put(".design/audit-report.md", PASSING, 300)
        self.assertEqual(run.design_problems(str(self.repo), ["a/x.tsx"])[1], [])


class TestChanged(RunCase):
    # covers: AC-1 (committed and uncommitted changes since the merge base count, main's own changes, deletions,
    # symlinks and non frontend files do not; with no main or master every frontend file counts and base is None)
    def test_base(self):
        r = self.make_repo("b", UI)
        (r / "old.tsx").write_text("x")
        (r / "gone.tsx").write_text("x")
        git(r, "checkout", "-qb", "main")
        git(r, "add", "-A")
        git(r, "commit", "-qm", "base")
        git(r, "checkout", "-qb", "work")
        (r / "committed.tsx").write_text("x")
        os.remove(r / "gone.tsx")
        git(r, "add", "-A")
        git(r, "commit", "-qm", "work")
        (r / "old.tsx").write_text("y")
        (r / "new.css").write_text("y")
        (r / "notes.py").write_text("y")
        os.symlink("old.tsx", r / "link.tsx")
        base, changed = run.frontend_changed(str(r))
        sha = subprocess.run(["git", "-C", str(r), "rev-parse", "main"], capture_output=True, text=True).stdout.strip()
        self.assertEqual((base, changed), (sha, ["committed.tsx", "new.css", "old.tsx"]))
        git(r, "checkout", "-q", "main")
        git(r, "branch", "-qm", "main", "trunk")
        git(r, "checkout", "-q", "work")
        self.assertEqual(run.frontend_changed(str(r)), (None, ["committed.tsx", "new.css", "old.tsx"]))

    # covers: AC-1 (a git failure raises; an empty list would let /sync run unchecked)
    def test_git_failure(self):
        plain = self.tmp / "not-a-repo"
        plain.mkdir()
        (plain / "a.tsx").write_text("x")
        with self.assertRaises(RuntimeError):
            run.frontend_changed(str(plain))


class TestCheck(RunCase):
    def setUp(self):
        super().setUp()
        self.r = self.make_repo("ui", UI)

    # covers: AC-3, AC-7 (no UI changed: /sync runs, design.changed is [])
    def test_no_ui(self):
        self.steps([{"write_file": [["a.py", "x"]]}, {}, {"tick": False}])
        r = self.wf("ui", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = self.run_record()[1]
        self.assertEqual(rec["design"], {"base": None, "changed": [], "reports": {}, "problems": []})
        self.assertEqual(rec["calls"][-1]["kind"], "sync")

    # covers: AC-3, AC-7, AC-8 (no report parks design_gate, no sync call, exit 6, the detail and the record)
    def test_missing(self):
        self.steps([{"write_file": [["src/components/Nav.tsx", "x"]]}, {}, {"tick": False}])
        r = self.wf("ui", "-y")
        rec = self.assert_stopped(r, "design_gate", calls=2)
        # assert_stopped reads run.PARKS, so dropping design_gate from it passed; AC-8 pinned literally.
        self.assertEqual(rec["stop_reason"], "queue_done")
        self.assertIn("parked: 1. A: design_gate: 1 frontend file(s)", r.stdout)
        self.assertEqual(rec["detail"], "1 frontend file(s) not covered by a passing design-gate report: "
                                        "src/components/Nav.tsx (no report)")
        self.assertEqual(rec["design"], {"base": None, "changed": ["src/components/Nav.tsx"], "reports": {},
                                         "problems": [{"path": "src/components/Nav.tsx", "problem": "no report"}]})
        self.assertNotIn("sync", [c["kind"] for c in rec["calls"]])
        self.assertFalse((self.fakes / "argv-3.json").exists())

    # covers: AC-3, AC-4 (a later passing report lets the run reach /sync)
    def test_passing(self):
        self.steps([{"write_file": [["src/components/Nav.tsx", "x"]]}, {"write_file": [report(PASSING)]},
                    {"tick": False}])
        r = self.wf("ui", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = self.run_record()[1]
        self.assertEqual([c["kind"] for c in rec["calls"]], ["box", "box", "sync"])
        self.assertEqual(rec["design"]["reports"], {".design/audit-report.md": "PASS WITH FINDINGS"})
        self.assertEqual(rec["design"]["problems"], [])

    # covers: AC-3 (a passing report, then the .tsx edited again, parks older than the file)
    def test_stale(self):
        self.r.joinpath("docs/scope/scope.md").write_text(UI + "- [ ] `/develop b`\n")
        self.steps([{"write_file": [["a.tsx", "x"]]}, {"write_file": [report(PASSING)]},
                    {"write_file": [["a.tsx", "y"]]}])
        rec = self.assert_stopped(self.wf("ui", "-y"), "design_gate", calls=3)
        self.assertEqual(rec["design"]["problems"], [{"path": "a.tsx", "problem": "older than the file"}])

    # covers: AC-1, AC-3 (a rerun whose next box leads straight to /sync parks again; 6 files list the first 5)
    def test_rerun(self):
        files = [[f"p{i}.css", "x"] for i in range(6)]
        self.steps([{"write_file": files}, {}])
        rec = self.assert_stopped(self.wf("ui", "-y"), "design_gate", calls=2)
        self.assertEqual(rec["detail"], "6 frontend file(s) not covered by a passing design-gate report: "
                         + ", ".join(f"p{i}.css (no report)" for i in range(5)))
        shutil.rmtree(self.state)
        (self.fakes / "count").unlink()
        self.r.joinpath("docs/scope/scope.md").write_text(UI.replace("- [ ] `/develop", "- [x] `/develop"))
        self.steps([{}])
        rec = self.assert_stopped(self.wf("ui", "-y"), "design_gate", calls=1)
        self.assertEqual(len(rec["design"]["problems"]), 6)

    # covers: AC-3 (the check runs only when rule 14 picks /sync: a VERIFY FAIL: debug on the last box runs the
    # debug call first, and a retried sync call does not rerun it)
    def test_order(self):
        self.steps([{"write_file": [["a.tsx", "x"]]},
                    {"tick": False, "json": {"result": "VERIFY FAIL: debug"}},
                    {"tick": False, "write_file": [report(PASSING)]}, {},
                    {"tick": False, "rc": 1, "write_file": [["a.tsx", "z"]]}, {"tick": False}])
        r = self.wf("ui", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = self.run_record()[1]
        self.assertEqual([c["kind"] for c in rec["calls"]], ["box", "box", "debug", "box", "sync", "sync"])
        self.assertEqual(rec["calls"][5]["retry_of"], 5)
        # Recorded once, before the first sync call: the file the failed sync rewrote was not checked again.
        self.assertEqual(rec["design"]["problems"], [])

    # covers: AC-3 (a guarded git config changed by the last box call stops the run before wf's git reads it)
    def test_guard_before_check(self):
        self.steps([{"write_file": [["a.tsx", "x"]]}, {"write_file": [[".git/config", "{}"]]}, {"tick": False}])
        rec = self.assert_stopped(self.wf("ui", "-y"), "guard_changed", calls=2)
        self.assertIsNone(rec["design"])


class TestCallArgs(RunCase):
    # covers: AC-5, AC-6 (every call and resume carries both prompt lines and both skill denies, not design-gate)
    def test_argv(self):
        self.steps([{}])
        self.wf("demo", "-y", "--max-calls", "1")
        argv = self.argv(1)["argv"]
        denied = argv[argv.index("--disallowedTools") + 1].split(",")
        self.assertIn("Skill(design)", denied)
        self.assertIn("Skill(brand-system)", denied)
        self.assertFalse([d for d in denied if "design-gate" in d])
        prompt = argv[argv.index("--append-system-prompt") + 1]
        self.assertIn("end with BLOCKED: no locked design for <what>. Never invoke the design or brand-system skills.",
                      prompt)
        self.assertIn("invoke the design-gate skill", prompt)
        self.assertIn(".tsx", prompt)
        self.assertIn("components or pages folder or under src/ui/", prompt)

    # covers: AC-5 (a BLOCKED: no locked design line parks blocked with that text)
    def test_blocked(self):
        self.steps([{"tick": False, "json": {"result": "Nothing built.\nBLOCKED: no locked design for the pricing page"}}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "blocked", calls=1)
        self.assertEqual(rec["detail"], "no locked design for the pricing page")
        self.assertIsNone(rec["design"])


if __name__ == "__main__":
    unittest.main()
