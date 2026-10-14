"""Spec 0033: context and links in every message, the labeled question name, blocked steps, the write deny route."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import context  # noqa: E402
import run  # noqa: E402
import telegram  # noqa: E402
from test_run import RunCase, ask  # noqa: E402

CFG = {"block": ["zorblex"], "chat_id": 7}
RESULT = ("I compared both engines on the schema in docs/specs/0001-a/index.md and both fit.\n"
          "DECISION NEEDED: Which storage engine?\nOPTION: Postgres\nOPTION: SQLite\n"
          "LEARN: a database keeps data, like a filing cabinet.\nWHY: Postgres already runs on your server.")
SCOPE = """# Scope: demo
**Autopilot:** allowed

### 1. Loop · auto
Spec [0001](../specs/0001-a/index.md)
Source: acme/widgets#4
- [x] (spec)
- [ ] Build it: `/develop loop`
"""


class TestUnit(unittest.TestCase):
    # covers: AC-1, AC-3 (did is the text above the marker, why and steps after it)
    def test_from_call(self):
        c = context.from_call(RESULT, run.DECISION)
        self.assertTrue(c["did"].startswith("I compared both engines"))
        self.assertEqual(c["why"], "Postgres already runs on your server.")
        c = context.from_call("tried it\nBLOCKED: needs sudo\nSTEP: 1. Open a terminal in ~/x\nSTEP: run `make`",
                              run.BLOCKED)
        self.assertEqual(c["steps"], ["Open a terminal in ~/x", "run `make`"])
        self.assertEqual(context.from_call("no marker", run.BLOCKED), {})

    # covers: AC-4 (from block: scrubbed call text, runner links kept, a blocked link dropped, did cut to fit)
    def test_telegram_block(self):
        d = {"context": {"repo": "demo", "feature": "1. Loop", "spec": "https://github.com/acme/widgets/blob/work/a.md",
                         "step": "Build it `/develop loop`", "did": "read `secret.py` then x " * 60,
                         "issues": ["https://github.com/acme/widgets/issues/4",
                                    "https://github.com/zorblex/x/issues/1"],
                         "pr": {"number": 7, "url": "https://github.com/acme/widgets/pull/7"}, "why": "it is faster"}}
        block = context.telegram_block(CFG, d, 4000)
        self.assertIn("\nspec: https://github.com/acme/widgets/blob/work/a.md\n", block)
        self.assertIn("\nissue: https://github.com/acme/widgets/issues/4\n", block)
        self.assertNotIn("zorblex", block)
        self.assertIn("\nPR: #7 https://github.com/acme/widgets/pull/7\n", block)
        self.assertIn("\nwhy recommended: it is faster", block)
        self.assertNotIn("secret.py", block)
        small = context.telegram_block(CFG, d, 400)
        self.assertLessEqual(len(small), 400)
        self.assertIn("why recommended: it is faster", small)

    # covers: AC-5 (the swipe reply finds the labeled first line and the old one; typed replies unchanged)
    def test_swipe(self):
        for first in (context.label("w8d0") + ":\nShip it?", "w8d0: Ship it?"):
            u = {"update_id": 5, "message": {"chat": {"id": 7}, "from": {"id": 7}, "text": "2", "date": 1,
                                             "reply_to_message": {"from": {"is_bot": True}, "text": first}}}
            line, _, hint = telegram.entry(CFG, u)
            self.assertEqual((line["message"], hint), ("w8d0 2", False))

    # covers: AC-7 (a path inside the repo named with a deny word; outside the repo or no deny word is not)
    def test_denied_in_text(self):
        import tempfile
        repo = Path(tempfile.mkdtemp()).resolve()
        (repo / "runner").mkdir()
        self.assertEqual(context.denied_in_text(str(repo), "runner/ is write-denied, apply the fix in a session"),
                         str(repo / "runner"))
        self.assertIsNone(context.denied_in_text(str(repo), "needs /etc/sudoers, permission denied"))
        self.assertIsNone(context.denied_in_text(str(repo), "runner/ needs a review"))


class TestRun(RunCase):
    def setUp(self):
        super().setUp()
        (self.repo / "docs" / "scope" / "scope.md").write_text(SCOPE)
        (self.repo / "docs" / "specs" / "0001-a").mkdir(parents=True)
        (self.repo / "docs" / "specs" / "0001-a" / "index.md").write_text("# 0001 · A\n")
        subprocess.run(["git", "-C", str(self.repo), "config", "remote.origin.url",
                        "https://github.com/acme/widgets.git"], check=True)

    def decision(self):
        [d] = json.loads((self.state / "wf" / "queue.json").read_text())["decisions"]
        return d

    # covers: AC-1, AC-2, AC-3, AC-8 (a call's question carries its context: spec link from the remote, step, did,
    # issue, why; ntfy gets the short from line and why, no links)
    def test_question_context(self):
        self.steps([ask(RESULT)])
        self.wf("demo", "-y")
        c = self.decision()["context"]
        self.assertEqual(c["spec"], "https://github.com/acme/widgets/blob/work/docs/specs/0001-a/index.md")
        self.assertEqual(c["step"], "Build it: `/develop loop`")
        self.assertEqual(c["issues"], ["https://github.com/acme/widgets/issues/4"])
        self.assertEqual(c["why"], "Postgres already runs on your server.")
        self.assertTrue(c["did"].startswith("I compared"))
        msg = self.report_ntfy.pings()[0]["message"]
        self.assertIn("\nwhy: Postgres already runs on your server.\n", msg)
        self.assertNotIn("https://", msg)

    # covers: AC-6 (a block's STEP lines become the question's numbered steps)
    def test_blocked_steps(self):
        self.steps([{"tick": False, "json": {"result": "BLOCKED: needs a login\nSTEP: Open a terminal\n"
                                                       "STEP: 2. Run gh auth login and pick GitHub.com"}}])
        self.wf("demo", "-y")
        d = self.decision()
        self.assertEqual(d["case"], "blocked")
        self.assertEqual(d["context"]["steps"], ["Open a terminal", "Run gh auth login and pick GitHub.com"])
        self.assertIn("\n1. Open a terminal\n2. Run gh auth login and pick GitHub.com\n",
                      self.report_ntfy.pings()[0]["message"])

    # covers: AC-7 (a block caused by the run's own write deny is F1 with the path, not F2)
    def test_write_deny_is_f1(self):
        (self.repo / "runner").mkdir()
        self.steps([{"tick": False, "json": {"result": "BLOCKED: runner/ is write-denied; apply the fix in an "
                                                       "interactive session"}}])
        self.wf("demo", "-y")
        d = self.decision()
        self.assertEqual((d["case"], d["allow"]), ("denied", str(self.repo.resolve() / "runner")))
        self.assertEqual(d["options"][:2], ["allow once", "always"])


if __name__ == "__main__":
    unittest.main()
