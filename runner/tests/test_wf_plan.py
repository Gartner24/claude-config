"""Spec 0060 AC-1, AC-4, AC-5, AC-7: `wf plan --json` and `wf answer`, the wf-dash dashboard's facts and answer action."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import auto  # noqa: E402
import wf  # noqa: E402
from test_queue import decision  # noqa: E402

SCOPE = """# Scope: one

**Source of truth:** scope
**Autopilot:** allowed

### 1. Building one · auto
- [ ] Build it: `/develop building one`

### 2. Waiting one
- [ ] Log in to the dashboard · waits on you

### 3. Local one
- [x] Build it: `/develop local one`
- [ ] Verify it: `/check verify local one`

### 4. Review one
- [x] Build it: `/develop review one`
- [ ] Verify it: `/check verify review one`

### 5. Tagged one · done
- [x] Build it: `/develop tagged one`

### 6. Dropped one · dropped
- [ ] Build it: `/develop dropped one`

### 7. Untagged one
- [x] Build it: `/develop untagged one`

### 8. Design one
- [ ] Design it: `/architect design one`
Spec [0007](../specs/0007-design-one.md) · Source: the owner.

### 9. Ready one
- [ ] Build it: `/develop ready one`
Spec [0099](../specs/0099-gone.md)

### 10. Mid one
- [x] Build it: `/develop mid one`
- [ ] Verify it: `/check verify mid one`
Spec [0008](../specs/0008-mid/index.md)
"""
OTHER = """# Scope: two

### 1. Built here
- [x] Build it: `/develop built here`
- [ ] Test it: `/test built here`
"""
HUB = """# Hub

## At a glance
| # | Item | Repos | Status |
|---|---|---|---|
| 1 | Plan the site | one | planned |
| 2 | Old thing | one | done |
"""


def git(*args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], check=True, capture_output=True)


class PlanCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.root = self.tmp / "projects"
        self.state = self.tmp / "state"
        env = mock.patch.dict(os.environ, {"WF_ROOTS": str(self.root), "XDG_STATE_HOME": str(self.state)})
        env.start()
        self.addCleanup(env.stop)
        # the suite itself may run inside a wf run call; patch.dict puts it back
        os.environ.pop("WF_RUN", None)
        (self.state / "wf").mkdir(parents=True)

    def repo(self, name, scope, answers=None, scope_file="scope.md"):
        r = self.root / name
        (r / "docs" / "scope").mkdir(parents=True)
        (r / "docs" / "scope" / scope_file).write_text(scope)
        if answers:
            (r / "AGENTS.md").write_text("# x\n\n## Standing answers\n\n" + answers + "\n")
        return r

    def queue(self, prs=(), decisions=()):
        (self.state / "wf" / "queue.json").write_text(json.dumps({"version": 1, "parks": [], "decisions": list(decisions), "prs": list(prs)}))

    def plan(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(wf.main(["plan", "--json"]), 0)
        return json.loads(out.getvalue())


def rec(repo, feature, state, number=None):
    return {"repo": str(repo), "feature": feature, "spec": None, "branch": "feat/x", "base": "main", "base_sha": "a" * 40,
            "stacked_on": None, "pr": None, "number": number, "state": state, "seen": [], "rounds": 0, "pushed_sha": None}


class TestPlan(PlanCase):
    # covers: AC-1 (every state, first match wins: building from a running active.json entry, waits on you, to publish
    # and in review from the PR records, the done and dropped tags, done untagged, needs a design, ready to build, in
    # progress; spec number from the heading block and its Status, unknown for a missing spec file; next box text)
    def test_every_state(self):
        r = self.repo("one", SCOPE, "- branches: per spec")
        (r / "docs" / "specs").mkdir()
        (r / "docs" / "specs" / "0007-design-one.md").write_text("# 0007\n\n**Status**: Proposed\n")
        (r / "docs" / "specs" / "0008-mid").mkdir()
        (r / "docs" / "specs" / "0008-mid" / "index.md").write_text("# 0008\n\n**Status**: Accepted\n")
        self.queue(prs=[rec(r, "3. Local one", "local"), rec(r, "4. Review one", "draft", 12)])
        (self.state / "wf" / "active.json").write_text(json.dumps([{"repo": str(r), "tree": str(r), "feature": "1. Building one · auto"}]))
        with mock.patch.object(auto, "entry_running", return_value=True), mock.patch.object(auto, "run_id", return_value=None):
            got = self.plan()
        (one,) = got["repos"]
        feats = {f["heading"]: f for f in one["features"]}
        self.assertEqual({h: f["state"] for h, f in feats.items()}, {
            "1. Building one": "building", "2. Waiting one": "waits on you", "3. Local one": "to publish",
            "4. Review one": "in review", "5. Tagged one": "done", "6. Dropped one": "dropped",
            "7. Untagged one": "done (untagged)", "8. Design one": "needs a design", "9. Ready one": "ready to build",
            "10. Mid one": "in progress"})
        self.assertEqual((feats["4. Review one"]["pr"], feats["4. Review one"]["prState"]), (12, "draft"))
        self.assertEqual((feats["8. Design one"]["spec"], feats["8. Design one"]["specStatus"]), ("0007", "Proposed"))
        self.assertEqual((feats["9. Ready one"]["spec"], feats["9. Ready one"]["specStatus"]), ("0099", "unknown"))
        self.assertEqual(feats["10. Mid one"]["specStatus"], "Accepted")
        self.assertEqual(feats["10. Mid one"]["command"], "/check verify mid one")
        self.assertEqual(feats["2. Waiting one"]["next"], "Log in to the dashboard · waits on you")
        # a per spec repo whose queue was read: no record is a fact, not unknown
        self.assertIsNone(feats["10. Mid one"]["review"])
        self.assertEqual([r["feature"] for r in got["runs"]], ["1. Building one · auto"])

    # covers: AC-1 (a repo without branches: per spec writes no PR records, so past its build it says in review:
    # unknown, never not in review; before its build it says nothing)
    def test_review_unknown_without_records(self):
        self.repo("two", OTHER + "\n### 2. Not built\n- [ ] Build it: `/develop not built`\n")
        self.queue()
        feats = {f["heading"]: f for f in self.plan()["repos"][0]["features"]}
        self.assertEqual((feats["1. Built here"]["state"], feats["1. Built here"]["review"]), ("in progress", "unknown"))
        self.assertIsNone(feats["2. Not built"]["review"])

    # covers: AC-1 (a scope that fails is listed with its error and the others still show; a hub lists its open At a
    # glance rows as written; the epic split's warnings show)
    def test_broken_scope_hub_and_warnings(self):
        self.repo("good", OTHER)
        bad = self.repo("bad", OTHER)
        (bad / "docs" / "scope" / "scope.md").chmod(0)
        self.addCleanup((bad / "docs" / "scope" / "scope.md").chmod, 0o644)
        self.repo("hub", HUB)
        self.repo("split", "# Scope: split\n\n- [one](one.md)\n- [gone](gone.md)\n", scope_file="index.md")
        (self.root / "split" / "docs" / "scope" / "one.md").write_text("### 1. Epic feature\n- [ ] Build it: `/develop epic`\n")
        self.queue()
        repos = {r["name"]: r for r in self.plan()["repos"]}
        self.assertIn("Permission denied", repos["bad"]["error"])
        self.assertEqual(repos["good"]["features"][0]["heading"], "1. Built here")
        self.assertEqual(repos["hub"]["rows"], ["1 | Plan the site | one | planned"])
        self.assertEqual([f["heading"] for f in repos["split"]["features"]], ["1. Epic feature"])
        self.assertIn("missing epic file gone.md", repos["split"]["warnings"])

    # covers: AC-1 (two worktrees of one repo give one entry, the plan checkout's)
    def test_worktrees_merge(self):
        r = self.repo("one", OTHER)
        git("-C", str(r), "init", "-q", "-b", "main")
        git("-C", str(r), "add", "-A")
        git("-C", str(r), "commit", "-qm", "x")
        git("-C", str(r), "worktree", "add", "-q", str(self.root / "one-wt1"), "-b", "a")
        git("-C", str(r), "worktree", "add", "-q", str(self.root / "one-wt2"), "-b", "b")
        self.queue()
        self.assertEqual([x["path"] for x in self.plan()["repos"]], [str(r)])

    # covers: AC-1 (an unreadable queue is a warning and unknown runs of questions, never an empty list)
    def test_unreadable_queue(self):
        self.repo("two", OTHER)
        (self.state / "wf" / "queue.json").write_text("not json")
        got = self.plan()
        self.assertIsNone(got["questions"])
        self.assertTrue(any("could not read the runner's queue" in w for w in got["warnings"]))
        self.assertEqual(got["repos"][0]["features"][0]["review"], "unknown")

    # covers: AC-1 (control characters in file text never reach the dashboard)
    def test_clean(self):
        self.repo("two", "### 1. Evil\x1b]0;x\x07 one\n- [ ] Build it: `/develop \x1b[2Jx`\n")
        self.queue()
        f = self.plan()["repos"][0]["features"][0]
        self.assertNotIn("\x1b", json.dumps(f))
        # json.dumps writes ESC as \u001b, so the line above alone could never fail: check the values themselves
        for k in ("heading", "next", "command"):
            self.assertFalse(any(ord(ch) < 32 for ch in f[k]), (k, f[k]))


class TestRunDetail(PlanCase):
    # covers: AC-4 (the step running now from log.txt, steps so far, cost and start from run.json)
    def test_run_detail(self):
        folder = self.state / "wf" / "runs" / "one-20261018-100000-42"
        folder.mkdir(parents=True)
        (folder / "run.json").write_text(json.dumps({"started": "2026-10-18T10:00:00-05:00", "cost_usd": 1.5, "calls": [
            {"command": "/develop x", "started": "2026-10-18T10:00:00-05:00", "duration_s": 120, "cost_usd": 1.5, "exit_code": 0, "is_error": False}]}))
        (folder / "log.txt").write_text("10:00 call 1 box one: /develop x, transcript t1\n10:02 end 1 ok\n"
                                        "10:02 call 2 box one: /check verify x\x1b[2J, transcript t2\n")
        d = wf.run_detail(str(folder))
        self.assertEqual((d["step"], d["calls"], d["cost"], d["startedAt"]), ("/check verify x[2J", 1, 1.5, "2026-10-18T10:00:00-05:00"))
        self.assertEqual(d["steps"], [{"command": "/develop x", "started": "2026-10-18T10:00:00-05:00", "minutes": 2.0, "cost": 1.5, "ok": True}])
        self.assertEqual(wf.run_detail(None)["step"], None)
        # a step that ended is not the one running now
        with open(folder / "log.txt", "a") as f:
            f.write("10:05 end 2 ok\n")
        self.assertIsNone(wf.run_detail(str(folder))["step"])


class TestAnswer(PlanCase):
    def answer(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = wf.main(["answer", *args])
        return rc, out.getvalue().strip()

    # covers: AC-5 (wf answer picks an option by number and writes it as a keyboard answer; a wrong option, an
    # answered id and an unknown id change nothing)
    def test_answer(self):
        self.queue(decisions=[decision("/r/demo", "1. A"), decision("/r/demo", "2. B", did="cd34", options=[], kind="prose")])
        self.assertEqual(self.answer("ab12", "3"), (2, "wrong option: 3, pick 1 to 2"))
        self.assertEqual(self.answer("ab12", "use sqlite"), (2, "wrong option: use sqlite, pick 1 to 2"))
        self.assertEqual(self.answer("cd34", "1"), (2, "this question takes no option number"))
        self.assertEqual(self.answer("zz99", "1"), (1, "no question zz99"))
        q = json.loads((self.state / "wf" / "queue.json").read_text())["decisions"]
        self.assertEqual([d["answer"] for d in q], [None, None])
        self.assertEqual(self.answer("ab12", "2"), (0, "answered: ab12 SQLite (keyboard)"))
        q = json.loads((self.state / "wf" / "queue.json").read_text())["decisions"]
        self.assertEqual((q[0]["answer"], q[0]["source"]), ("SQLite", "keyboard"))
        self.assertEqual(self.answer("ab12", "1"), (1, "already answered: ab12"))

    # covers: AC-5 (an unattended wf run call never answers as you)
    def test_refused_under_wf_run(self):
        self.queue(decisions=[decision("/r/demo", "1. A")])
        with mock.patch.dict(os.environ, {"WF_RUN": "1"}):
            self.assertEqual(self.answer("ab12", "2"), (5, "refused: user_only"))
        self.assertIsNone(json.loads((self.state / "wf" / "queue.json").read_text())["decisions"][0]["answer"])


if __name__ == "__main__":
    unittest.main()
