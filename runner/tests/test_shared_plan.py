"""Spec 0043 AC-4 to AC-6: one shared plan while features of one repo build in worktrees."""
import os
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pr  # noqa: E402
from test_parallel_repo import RepoCase, step  # noqa: E402

PLAN = """# Scope: x

## At a glance

| # | Feature | Status |
|---|---|---|
| 1 | A | planned |
| 2 | B | planned |

## Features

### 1. A · auto
- [ ] `/develop a`

### 2. B · auto
- [ ] `/develop b`

## Deferred
- later
"""


class FakeRun:
    def __init__(self, main, tree, feature):
        self.c = types.SimpleNamespace(path=str(tree), scope_dir="docs/scope")
        self.main, self.feature, self.notes = str(main), feature, []
        self.repo = {"tree": str(tree)}

    def note(self, text):
        self.notes.append(text)


class TestSplice(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.state = self.tmp / "state"
        self.enterContext(mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.state)}))
        self.main, self.trees = self.tmp / "main", []
        (self.main / "docs" / "scope").mkdir(parents=True)
        (self.main / "docs" / "scope" / "scope.md").write_text(PLAN)
        self.enterContext(mock.patch("run.key_of", lambda c: str(self.main)))

    def tree(self, name, feature):
        t = self.tmp / name
        (t / "docs" / "scope").mkdir(parents=True)
        (t / "docs" / "scope" / "scope.md").write_text("stale copy\n")
        return FakeRun(self.main, t, feature)

    def plan(self, where=None):
        return ((where or self.main) / "docs" / "scope" / "scope.md").read_text()

    # covers: AC-4 (only the feature's block and its At a glance row change in main; the rest stays)
    def test_block_and_row_only(self):
        t = PLAN.replace("| 1 | A | planned |", "| 1 | A | done |").replace("### 1. A · auto\n- [ ] `/develop a`",
                                                                           "### 1. A · done · auto\n- [x] `/develop a`")
        t = t.replace("| 2 | B | planned |", "| 2 | B | broken |").replace("- later", "- changed by A")
        m = pr.splice(PLAN, t, "1. A")
        self.assertIn("| 1 | A | done |", m)
        self.assertIn("### 1. A · done · auto\n- [x] `/develop a`", m)
        self.assertIn("| 2 | B | planned |", m)
        self.assertIn("- later", m)
        self.assertNotIn("changed by A", m)

    # covers: AC-4 (a child starts from main's plan, not its stale copy; a change outside its section is a note and is
    # not copied)
    def test_copy_in_and_note(self):
        r = self.tree("ta", "1. A")
        pr.plan_in(r)
        self.assertEqual(self.plan(Path(r.c.path)), PLAN)
        tree_file = Path(r.c.path) / "docs" / "scope" / "scope.md"
        tree_file.write_text(PLAN.replace("- [ ] `/develop a`", "- [x] `/develop a`").replace("- later", "- by A"))
        pr.plan_out(r, "1. A")
        self.assertIn("- [x] `/develop a`", self.plan())
        self.assertNotIn("- by A", self.plan())
        self.assertEqual(r.notes, ["1. A: its plan copy changed scope.md outside its own section; only its section was kept"])

    # covers: security review (path traversal): a worktree whose scope folder a call turned into a symlink gets no
    # plan written through it
    def test_symlinked_copy(self):
        r = self.tree("ta", "1. A")
        outside = self.tmp / "outside"
        outside.mkdir()
        scope = Path(r.c.path) / "docs" / "scope"
        (scope / "scope.md").unlink()
        scope.rmdir()
        scope.symlink_to(outside)
        pr.plan_in(r)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual(r.notes, ["plan copy skipped scope.md: not a plain file inside the worktree"])

    # covers: AC-4 (two children syncing at the same moment both land, under the lock)
    def test_two_at_once(self):
        ra, rb = self.tree("ta", "1. A"), self.tree("tb", "2. B")
        for r, x in ((ra, "a"), (rb, "b")):
            pr.plan_in(r)
            f = Path(r.c.path) / "docs" / "scope" / "scope.md"
            f.write_text(PLAN.replace(f"- [ ] `/develop {x}`", f"- [x] `/develop {x}`"))
        start = threading.Barrier(2)

        def go(r):
            start.wait()
            for _ in range(20):
                pr.plan_out(r, r.feature)
        threads = [threading.Thread(target=go, args=(r,)) for r in (ra, rb)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertIn("- [x] `/develop a`", self.plan())
        self.assertIn("- [x] `/develop b`", self.plan())


class TestSharedPlanRun(RepoCase):
    # covers: AC-4 (both features' ticks and status tags land in the main checkout's plan), AC-5 (no feature branch
    # carries a scope change), AC-6 (the plan is committed on the start branch, only the scope file; an unrelated edit
    # in the main checkout stays uncommitted)
    def test_run(self):
        (self.repo / "notes.txt").write_text("mine\n")
        self.git("add", "notes.txt")
        self.git("commit", "-qm", "notes")
        (self.repo / "notes.txt").write_text("mine, edited\n")
        self.steps({"feat-0001-a": step("a", sleep=0), "feat-0002-b": step("b", sleep=0),
                    "feat-0003-c": step("c", sleep=0)})
        r = self.wf("-y", "--jobs", "3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        plan = (self.repo / "docs" / "scope" / "scope.md").read_text()
        for n, x in ((1, "A"), (2, "B"), (3, "C")):
            self.assertIn(f"### {n}. {x} · done · auto", plan, r.stdout)
            self.assertIn(f"- [x] `/develop {x.lower()}`", plan)
        self.assertEqual(self.git("status", "--porcelain", "--", "docs/scope"), "")
        self.assertIn("docs(scope): ", self.git("log", "-1", "--format=%s"))
        self.assertEqual(self.git("status", "--porcelain", "--", "notes.txt"), "M notes.txt")
        base = self.git("rev-parse", "work~0")
        for b in ("feat/0001-a", "feat/0002-b", "feat/0003-c"):
            mb = self.git("merge-base", base, b)
            self.assertEqual(self.git("diff", "--name-only", mb, b, "--", "docs/scope"), "", b)
            self.assertIn(f"{b[-1]}.txt", self.git("diff", "--name-only", mb, b))


if __name__ == "__main__":
    unittest.main()
