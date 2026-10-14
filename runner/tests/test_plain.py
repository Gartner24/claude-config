"""Spec 0028: plain words in phone questions and the morning report, learn lines, and the jargon check."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ntfy  # noqa: E402
import plain  # noqa: E402
import report  # noqa: E402
import run  # noqa: E402
from test_queue import DONE_A, ONE, TICK_A, DecisionCase, decision  # noqa: E402
from test_run import ask  # noqa: E402

CFG = {"aliases": {}, "block": [], "server": "https://x", "topic": "t" * 32}
FEATURE = "1. Login page"
# Details as the runner writes them; a reason code inside one is read as its plain words.
DETAILS = {"crash_loop": "call_error: exit 1 (also in 2. Sign up)", "max_calls": "8 calls made",
           "budget": "spent 2.00 USD", "debug_touched": "test files changed after verify_failed", "denied": "Edit src/app.py", "internal_error": "KeyError: 'x'",
           "decision_open": "ab12"}
SCOPE = """# Scope: demo
**Autopilot:** allowed

### 3. Phone setup · in-progress
- [x] (spec)
- [ ] Copy it: `cp a b` · waits on you · live
- [ ] Check the phone · waits on you · later boxes go on
"""


def detail(reason):
    return DETAILS.get(reason, "the login test still fails")


def case(reason, denied_at=None):
    """(question, options, learn) ask_case builds for reason, through the real method."""
    asked = {}
    r = SimpleNamespace(case_box=lambda: (None, ""), denied_at=denied_at, repo={"guard": {"never": []}},
                        c=SimpleNamespace(name="demo"), entry={"calls": []}, record={"calls": []}, feature=FEATURE, overlap_other=None,
                        ask=lambda q, o, **kw: asked.update(question=q, options=o, **kw) or asked)
    run.Run.ask_case(r, reason, detail(reason), True)
    return asked["question"], list(asked["options"]), asked.get("learn")


def ping_body(question, options, learn):
    d = {"id": "ab12", "question": question, "options": options, "kind": "panel" if options else "prose",
         "learn": learn}
    with mock.patch.object(ntfy.Topic, "publish", return_value="m1"):
        ntfy.Topic(CFG, "demo", FEATURE).ping(d, lambda: False)
    return d["sent"]


class TestTable(unittest.TestCase):
    # covers: AC-7, AC-15 (an entry for every case reason and the three outcomes, under the limits, itself plain)
    def test_plain(self):
        self.assertEqual(sorted(set(run.CASES) - set(plain.PLAIN)), [])
        for k in ("queue_done", "decision_open", "feature_done"):
            self.assertIn(k, plain.PLAIN)
        for reason, (words, learn) in plain.PLAIN.items():
            with self.subTest(reason):
                self.assertLess(len(words), 60)
                self.assertLess(len(learn), 300)
                self.assertEqual(plain.jargon(words + " " + learn), [])

    # covers: AC-7 (snake case, AC and spec numbers, listed words on word boundaries case folded, path tokens left out)
    def test_jargon(self):
        self.assertEqual(plain.jargon("verify_failed in AC-3 of spec 0021, the Sandbox and a traceback"),
                         ["AC-3", "sandbox", "spec 0021", "traceback", "verify_failed"])
        self.assertEqual(plain.jargon("see runner/run_x.py and https://a.b/c_d, caps and parking"), [])
        self.assertEqual(plain.jargon("Session ID and exit code"), ["exit code", "session id"])


class TestCorpus(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(subprocess.run, ["rm", "-rf", str(self.tmp)])
        env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.tmp / "state"), "HOME": str(self.tmp)})
        env.start()
        self.addCleanup(env.stop)
        (self.tmp / "state" / "wf" / "runs").mkdir(parents=True)

    def repo(self, name):
        p = self.tmp / name
        (p / "docs" / "scope").mkdir(parents=True)
        (p / "docs" / "scope" / "scope.md").write_text(SCOPE)
        return str(p)

    def texts(self):
        out = []
        for reason in run.CASES:
            q, options, learn = case(reason)
            self.assertTrue(learn, reason)
            out += [(f"case {reason}", q), (f"case {reason} learn", learn),
                    (f"ping {reason}", ping_body(q, options, learn))]
        q, options, learn = case("denied", denied_at="/repo/src/app.py")
        out += [("case denied path", q), ("ping denied path", ping_body(q, options, learn))]
        reasons = sorted(run.PARKS | run.REPO_STOPS | run.RUN_STOPS)
        a, b = self.repo("demo"), self.repo("shop")
        q = self.tmp / "state" / "wf" / "queue.json"
        q.write_text(json.dumps({"version": 1, "parks": [], "decisions": [
            decision(a, "4. Search", did="ab12", question="Which search engine should the site use?",
                     options=["The built in one (recommended)", "A hosted one"])]}))
        feats = [{"feature": f"{n}. Part {n}", "outcome": r, "detail": detail(r)} for n, r in enumerate(reasons, 5)]
        feats += [{"feature": "2. Sign up", "outcome": "feature_done", "detail": None},
                  {"feature": "4. Search", "outcome": "decision_open", "detail": "ab12"}]
        rec = {"features": feats, "stop_reason": "interrupted", "ended": "2026-10-13T03:20:00+00:00", "calls": [],
               "repos": [{"ended": "branch_changed"}]}
        for name, sources in (("one", [a]), ("two", [a, b])):
            srcs = [{"path": p, "name": os.path.basename(p), "folder": "/f", "code": None, "rec": rec} for p in sources]
            full, phone = report.render(srcs, CFG)
            out += [(f"report {name} full", full), (f"report {name} phone", phone)]
        return out

    # covers: AC-15 (every case question, learn line and ping, every report rendering: zero jargon hits)
    def test_no_jargon(self):
        hits = [f"{src}: {', '.join(h)}" for src, text in self.texts() for h in [plain.jargon(text)] if h]
        self.assertEqual(len(hits), 0, f"{len(hits)} texts with jargon:\n" + "\n".join(hits))


class TestLearnParts(unittest.TestCase):
    # covers: AC-9 (every LEARN: line after the question, joined and flattened, bold and bullets as OPTION; none: None)
    def test_read(self):
        text = ("LEARN: not this one\nDECISION NEEDED: Which engine?\nOPTION: A\nOPTION: B\n- **LEARN:** A database "
                "keeps data,\n  LEARN: like a filing cabinet.\n")
        self.assertEqual(run.read_decision(text), ("Which engine?", ["A", "B"], "A database keeps data, like a filing cabinet."))
        self.assertEqual(run.read_decision("DECISION NEEDED: q\nOPTION: a\n"), ("q", ["a"], None))

    # covers: AC-10 (the learn option's answer resumes with LEARN_PROMPT, any other with ANSWERED)
    def test_resume_prompt(self):
        self.assertEqual(run.resume_prompt("Learn this first"), run.LEARN_PROMPT)
        self.assertEqual(run.resume_prompt("SQLite"), run.ANSWERED + "SQLite")

    # covers: AC-11 (the learn line right after the question, one line, cut to 300, scrubbed; left out when empty)
    def test_ping(self):
        body = ping_body("Which engine?", ["A", "B"], "A database\nkeeps data. " + "more " * 80)
        lines = body.splitlines()
        self.assertEqual(lines[0], "ab12: Which engine?")
        self.assertTrue(lines[1].startswith("learn: A database keeps data. more more"), lines[1])
        self.assertLessEqual(len(lines[1]), len("learn: ") + 300)
        self.assertEqual(lines[2:], ["1 A", "2 B", "reply ab12 <n>"])
        self.assertEqual(ping_body("Which engine?", ["A"], None).splitlines()[1], "1 A")
        self.assertEqual(ping_body("Which engine?", ["A"], "see /home/x/secret.txt").splitlines()[1], "learn: see")

    # covers: AC-9 (a queue record without learn or jargon still loads; a wrong type does not)
    def test_old_record(self):
        q = {"version": 1, "parks": [], "decisions": [decision("/r", "1. A")]}
        self.assertIsNone(run.queue_problem(q))
        q["decisions"][0]["learn"] = 5
        self.assertIsNotNone(run.queue_problem(q))


class TestLearnFlow(DecisionCase):
    # covers: AC-10, AC-14, AC-11 (a call's question gets the learn option last; picking it resumes with LEARN_PROMPT;
    # the jargon in the model's text is recorded and logged, the question still asked; the ping carries the learn line)
    def test_learn(self):
        repo = self.make_repo("lf", ONE)
        self.commit(repo)
        text = ("DECISION NEEDED: Which verify_failed fix?\n" + "".join(f"OPTION: o{i}\n" for i in range(9)) +
                "LEARN: A fix is like a patch on a tyre.\n")
        self.ntfy.replies = ["{id} 9"]
        self.steps([ask(text), TICK_A, DONE_A])
        r = self.wf("lf", "-y", "--max-wait", "1", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        folder, rec = self.run_record()
        d = rec["decisions"][0]
        self.assertEqual(d["options"], [f"o{i}" for i in range(8)] + ["learn this first"])
        self.assertEqual((d["learn"], d["jargon"], d["answer"]),
                         ("A fix is like a patch on a tyre.", ["verify_failed"], "learn this first"))
        self.assertEqual(self.argv(2)["argv"][:2], ["-p", run.LEARN_PROMPT])
        self.assertIn("learn: A fix is like a patch on a tyre.", self.ntfy.posts[0]["message"])
        self.assertIn(f"jargon {d['id']}: verify_failed", (folder / "log.txt").read_text())


if __name__ == "__main__":
    unittest.main()
