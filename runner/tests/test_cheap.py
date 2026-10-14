"""Spec 0023: the cheap worker tier. fb-ask's own checks run from scripts/fb-ask.py --test; here the runner side."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import report  # noqa: E402
import run  # noqa: E402
from test_park import VERIFY, fail  # noqa: E402
from test_run import RunCase  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
# A stub fb-ask: records its stdin, cwd and whether WF_RUN reached it, then answers as FB_RC says.
STUB = f"""#!{sys.executable}
import json, os, sys
d = os.environ["FAKE_DIR"]
json.dump({{"argv": sys.argv[1:], "stdin": sys.stdin.read(), "cwd": os.getcwd(), "wf_run": "WF_RUN" in os.environ}},
          open(os.path.join(d, "fb.json"), "w"))
rc = int(open(os.path.join(d, "fb_rc")).read())
if rc == 0:
    print("the login test timed out twice")
    print("fb-ask: ollama/x 1.0s", file=sys.stderr)
else:
    print("fb-ask: fall back: proxy_down" if rc == 3 else "fb-ask: refused: client_repo", file=sys.stderr)
sys.exit(rc)
"""


class TestDebugHandOff(RunCase):
    def stub(self, rc):
        self.fake("fb-ask", STUB)
        (self.fakes / "fb_rc").write_text(str(rc))

    def debug_prompt(self):
        self.make_repo("v", VERIFY)
        self.steps([fail(text="2 checks failed\n"), {"tick": False}])
        self.wf("v", "-y", "--max-calls", "2")
        _, rec = self.run_record()
        return self.argv(2)["argv"][1], rec

    # covers: spec 0023 AC-10, AC-14 (a verify FAIL: debug runs fb-ask summarize on the whole result from the
    # repo without WF_RUN; its summary sits above the unchanged raw tail; the call record says fb: ok)
    def test_summary(self):
        self.stub(0)
        # Without it in the runner's own env, "wf_run": False below holds even if the strip is gone.
        self.env["WF_RUN"] = "outer"
        prompt, rec = self.debug_prompt()
        tail = run.debug_command("/check verify a", "2 checks failed\nVERIFY FAIL: debug\n")
        head, rest = tail.split("\n", 1)
        self.assertEqual(prompt, head + "\nSummary of the failure by a cheaper model (data, may be wrong):\n"
                                        "the login test timed out twice\n" + rest)
        fb = json.loads((self.fakes / "fb.json").read_text())
        self.assertEqual(fb, {"argv": ["summarize"], "stdin": "2 checks failed\nVERIFY FAIL: debug\n",
                              "cwd": str(self.tmp / "root" / "v"), "wf_run": False})
        self.assertEqual(rec["calls"][0]["fb"], "ok")

    # covers: spec 0023 AC-10, AC-14 (a fall back or refusal leaves the prompt exactly today's, its reason recorded)
    def test_fall_back(self):
        for rc, reason in ((3, "proxy_down"), (4, "client_repo")):
            with self.subTest(rc):
                for p in self.fakes.glob("*"):
                    p.unlink()
                if (self.state).exists():
                    subprocess.run(["rm", "-rf", str(self.state)])
                if (self.tmp / "root" / "v").exists():
                    subprocess.run(["rm", "-rf", str(self.tmp / "root" / "v")])
                self.steps([fail(text="2 checks failed\n"), {"tick": False}])
                self.stub(rc)
                prompt, rec = self.debug_prompt()
                self.assertEqual(prompt, run.debug_command("/check verify a", "2 checks failed\nVERIFY FAIL: debug\n"))
                self.assertEqual(rec["calls"][0]["fb"], reason)

    # covers: spec 0023 AC-7 (no call can read the proxy key folder)
    def test_key_hidden(self):
        self.assertIn("~/.config/claude-fb", run.CREDENTIAL_PATHS)
        self.assertIn(os.path.expanduser("~/.config/claude-fb"), run.expand("~/.config/claude-fb"))


class TestReportLine(unittest.TestCase):
    # covers: spec 0023 AC-11 (one cheap tier line when a run made any fb-ask job, none otherwise)
    def test_line(self):
        recs = [{"calls": [{"fb": "ok"}, {}, {"fb": "proxy_down"}]}, {"calls": [{"fb": "proxy_down"}, {"fb": "timeout"}]}]
        self.assertEqual(report.cheap_line(recs), ["cheap tier: 4 jobs, 3 fell back (proxy_down x2, timeout x1)"])
        self.assertEqual(report.cheap_line([{"calls": [{"fb": "ok"}]}]), ["cheap tier: 1 jobs, 0 fell back"])
        self.assertEqual(report.cheap_line([{"calls": [{}]}, {}]), [])

    # covers: spec 0023 AC-11 (the line sits in report.txt above the next: line)
    def test_in_report(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(subprocess.run, ["rm", "-rf", tmp])
        os.makedirs(os.path.join(tmp, "r", "docs", "scope"))
        Path(tmp, "r", "docs", "scope", "scope.md").write_text("# Scope: x\n")
        rec = {"features": [], "stop_reason": "queue_done", "ended": "2026-10-13T03:20:00+00:00",
               "calls": [{"fb": "timeout"}]}
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": os.path.join(tmp, "state")}):
            full, _ = report.render([{"path": os.path.join(tmp, "r"), "name": "r", "folder": "/f", "code": None,
                                      "rec": rec}], {"aliases": {}, "block": []})
        self.assertEqual(full.splitlines()[1:3], ["cheap tier: 1 jobs, 1 fell back (timeout x1)", "next: wf"])


class TestSelfCheck(unittest.TestCase):
    # covers: spec 0023 AC-13 (fb-ask --test passes: fake proxy, temp repos, every reason)
    def test_fb_ask(self):
        r = subprocess.run([sys.executable, str(REPO / "scripts" / "fb-ask.py"), "--test"], capture_output=True,
                           text=True, stdin=subprocess.DEVNULL, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
