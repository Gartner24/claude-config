"""Spec 0061: the runner's history, baselines and proposals, the hook line, and the improve-my-system extract."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import insights  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "runner" / "wf.py"
EXTRACT = ROOT / "claude-home" / "skills" / "improve-my-system" / "extract.py"
EDIT = {"tool": "Edit", "input": json.dumps({"file_path": "/r/.env", "old_string": "x" * 300})[:200], "reason": None}
BASH = {"tool": "Bash", "input": "curl https://secret.example/token", "reason": None}


def call(command, duration=10, cost=0.5, denials=(), retry_of=None):
    return {"command": command, "duration_s": duration, "cost_usd": cost, "denials": list(denials), "retry_of": retry_of}


def record(i, calls, outcomes=(), ended=True):
    feats = [{"feature": f"f{n}", "outcome": o, "calls": [len(calls)]} for n, o in enumerate(outcomes)]
    return {"ended": f"2026-10-{i + 1:02d}T03:00:00+00:00" if ended else None, "stop_reason": "queue_done",
            "cost_usd": 1.0, "calls": calls, "features": feats}


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(subprocess.run, ["rm", "-rf", str(self.tmp)])
        self.env = {"XDG_STATE_HOME": str(self.tmp / "state"), "CLAUDE_CONFIG_DIR": str(self.tmp / "home" / ".claude"),
                    "HOME": str(self.tmp / "home")}
        p = mock.patch.dict(os.environ, self.env)
        p.start()
        self.addCleanup(p.stop)
        self.runs = self.tmp / "state" / "wf" / "runs"
        self.runs.mkdir(parents=True)
        self.ins = self.tmp / "state" / "wf" / "insights"

    def put(self, i, rec, name=None):
        name = name or f"repo-202610{i + 1:02d}-030000-{1000 + i}"
        (self.runs / name).mkdir(exist_ok=True)
        (self.runs / name / "run.json").write_text(rec if isinstance(rec, str) else json.dumps(rec))
        return name

    def update(self):
        with redirect_stdout(io.StringIO()):
            return insights.update()

    def history(self):
        return [json.loads(l) for l in (self.ins / "history.jsonl").read_text().splitlines()]

    def inbox(self):
        return insights.inbox_ids((self.ins / "inbox.md").read_text()) if (self.ins / "inbox.md").exists() else []

    def hook(self):
        out = subprocess.run([sys.executable, "-B", str(WF), "report", "--hook"], capture_output=True, text=True,
                             env={"PATH": os.environ["PATH"], **self.env})
        self.assertEqual((out.returncode, out.stderr), (0, ""))
        return out.stdout


class Reader(Case):
    def twelve(self):
        """Runs 0 and 1 fall out of the 10 run window. In the window: the Edit denial in runs 2, 5, 8 (HOT), Bash in
        runs 3, 4 (not HOT), a verify_failed park in 6, 7, 9 (HOT), a /develop call_timeout in 9, 10, 11 (HOT)."""
        names = []
        for i in range(12):
            calls = [call("/develop x", duration=10 * (i + 1), cost=None if i == 11 else 0.1 * i),
                     call("/check verify x", denials=[EDIT] if i in (0, 1, 2, 5, 8) else [BASH] if i in (3, 4) else [])]
            outcomes = ["verify_failed"] if i in (0, 1, 6, 7, 9) else []
            if i in (9, 10, 11):
                calls.append(call("/develop y\nmore", duration=None, cost=None, retry_of=1))
                outcomes.append("call_timeout")
            names.append(self.put(i, record(i, calls, outcomes)))
        return names

    # covers: AC-2, AC-3, AC-4 (12 runs: only the last 10 count; HOT at 3 runs; median, p90, nulls skipped; one
    # proposal per HOT finding citing its run ids, the tool and path only)
    def test_twelve_runs(self):
        names = self.twelve()
        r = self.update()
        self.assertEqual((r["history"], r["scanned"], r["window"], r["added"]), (12, 12, 10, 3))
        hot = {k: v for k, v in r["counts"].items() if len(v) >= insights.HOT}
        self.assertEqual(hot, {("denied", "Edit `/r/.env`"): [names[2], names[5], names[8]],
                               ("park", "verify_failed"): [names[6], names[7], names[9]],
                               ("park", "call_timeout"): names[9:], ("timeout", "/develop"): names[9:]})
        self.assertEqual(len(r["counts"][("denied", "Bash")]), 2)
        # /develop over runs 2..11: durations 30..120 (p90 is the 9th of 10), costs 0.2..1.0 with run 11's null skipped.
        self.assertEqual(r["stats"]["/develop"]["duration_s"], (75.0, 110))
        self.assertAlmostEqual(r["stats"]["/develop"]["cost_usd"][0], 0.6)
        h = self.history()
        self.assertEqual((h[11]["retries"], h[11]["timeouts"], h[2]["denials"]), (1, ["/develop"], ["Edit `/r/.env`"]))
        text = (self.ins / "inbox.md").read_text()
        self.assertEqual(text.count("\n- ["), 3)
        self.assertIn(f"Edit `/r/.env` was denied in 3 of the last 10 runs ({names[2]}, {names[5]}, {names[8]};", text)
        self.assertNotIn("curl", text)

    # covers: AC-4 (at most 3 new per run, the 4th next run; a finding already proposed never again, even after the
    # inbox is emptied by hand)
    def test_cap_and_never_twice(self):
        self.twelve()
        first = self.update()
        self.assertEqual((first["added"], len(self.inbox())), (3, 3))
        self.assertEqual((self.update()["added"], len(self.inbox())), (1, 4))
        self.assertEqual(self.update()["added"], 0)
        (self.ins / "inbox.md").write_text("")
        self.assertEqual((self.update()["added"], self.inbox()), (0, []))

    # covers: AC-2 (a running run is not appended, and is once it ends; a pruned run stays; a corrupt one is counted)
    def test_running_pruned_corrupt(self):
        name = self.put(0, record(0, [call("/develop")], ended=False))
        self.put(1, "{not json", name="repo-20261002-030000-9")
        r = self.update()
        self.assertEqual((r["history"], r["corrupt"]), (0, 1))
        self.put(0, record(0, [call("/develop")]), name=name)
        self.assertEqual(self.update()["scanned"], 1)
        subprocess.run(["rm", "-rf", str(self.runs / name)], check=True)
        r = self.update()
        self.assertEqual((r["history"], r["scanned"], [s["run"] for s in self.history()]), (1, 0, [name]))

    # covers: AC-8 (with fixture runs and a fake ~/.claude, every new or changed file is under insights/)
    def test_writes_only_insights(self):
        self.twelve()
        claude = self.tmp / "home" / ".claude"
        (claude / "usage-data").mkdir(parents=True)
        (claude / "usage-data" / "report.html").write_text("<p>x</p>")
        (claude / "settings.json").write_text("{}")

        def files():
            return {p: (p.stat().st_mtime_ns, p.stat().st_size) for p in self.tmp.rglob("*") if p.is_file()}
        before = files()
        with redirect_stdout(io.StringIO()):
            insights.cmd_insights(mock.Mock(seen=False))
            insights.cmd_insights(mock.Mock(seen=True))
        changed = [p for p, v in files().items() if before.get(p) != v]
        self.assertTrue(changed)
        self.assertEqual([p for p in changed if self.ins not in p.parents], [])

    # covers: AC-5 (a failing reader prints one warning line and returns)
    def test_end_of_run_swallows(self):
        out = io.StringIO()
        with mock.patch.object(insights, "update", side_effect=OSError("disk full")), redirect_stdout(out):
            insights.end_of_run()
        self.assertEqual(out.getvalue(), "warning: insights: disk full\n")

    # covers: AC-7 (report.html text, tags and scripts stripped, cut to 4,000 characters; absent, no section)
    def test_usage_report(self):
        out = subprocess.run([sys.executable, "-B", str(WF), "insights"], capture_output=True, text=True,
                             env={"PATH": os.environ["PATH"], **self.env})
        self.assertNotIn("from /insights", out.stdout)
        d = self.tmp / "home" / ".claude" / "usage-data"
        d.mkdir(parents=True)
        (d / "report.html").write_text("<style>a{}</style><h1>Top &amp; tools</h1><script>evil()</script>" + "w " * 3000)
        text = insights.usage_report()
        self.assertTrue(text.startswith("Top & tools w w"))
        self.assertEqual(len(text), insights.REPORT_MAX)
        self.assertNotIn("evil", text)
        out = subprocess.run([sys.executable, "-B", str(WF), "insights"], capture_output=True, text=True,
                             env={"PATH": os.environ["PATH"], **self.env})
        self.assertIn("from /insights (data):\nTop & tools", out.stdout)
        self.assertFalse((self.ins / "inbox.md").exists())

    # covers: AC-6 (the hook line appears, goes after --seen, comes back for a new proposal; never the text)
    def test_hook_line(self):
        self.assertEqual(self.hook(), "")
        for i in range(3):
            self.put(i, record(i, [call("/develop", denials=[EDIT])], ["blocked"]))
        self.update()
        path = self.ins / "inbox.md"
        self.assertEqual(self.hook(), f"wf proposals: 2 new ({path})\n")
        # Silent while a run holds a repo lock, as the report line is.
        (self.tmp / "state" / "wf" / "locks").mkdir()
        holder = subprocess.Popen([sys.executable, "-c", "import fcntl, os, sys, time\n"
                                   "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT)\nfcntl.flock(fd, fcntl.LOCK_EX)\n"
                                   "print('held', flush=True)\ntime.sleep(30)", str(self.tmp / "state" / "wf" / "locks" / "a.lock")],
                                  stdout=subprocess.PIPE, text=True)
        self.addCleanup(holder.kill)
        holder.stdout.readline()
        self.assertEqual(self.hook(), "")
        holder.kill()
        holder.wait()
        holder.stdout.close()
        self.assertEqual(self.hook(), f"wf proposals: 2 new ({path})\n")
        subprocess.run([sys.executable, "-B", str(WF), "insights", "--seen"], check=True, env={**os.environ})
        self.assertEqual(self.hook(), "")
        for i in range(3, 6):
            self.put(i, record(i, [call("/develop")], ["no_progress"]))
        self.update()
        self.assertEqual(self.hook(), f"wf proposals: 1 new ({path})\n")


class Extract(Case):
    def setUp(self):
        super().setUp()
        self.claude = self.tmp / "home" / ".claude"
        (self.claude / "private").mkdir(parents=True)
        (self.claude / "private" / "names.txt").write_text("# private\nAcmeCorp ==> client\n")
        self.mine, self.other = "/work/mine", "/work/theirs"
        (self.claude / "private" / "history-allow.txt").write_text(self.mine + "\n")
        for path in (self.mine, self.other):
            folder = self.claude / "projects" / path.replace("/", "-")
            (folder / "s1" / "subagents").mkdir(parents=True)
            lines = [{"type": "user", "timestamp": "2026-10-16T10:00:00Z", "message": {"role": "user", "content":
                      "no, stop it: acmecorp key sk-ant-abcdefghijklmnop mail me@example.com hex " + "ab12" * 10}},
                     {"type": "user", "isMeta": True, "message": {"content": "skill body"}},
                     {"type": "user", "message": {"content": [{"type": "tool_result", "content": "result text"}]}},
                     {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Edit", "input": {}}]}}]
            (folder / "s1.jsonl").write_text("".join(json.dumps(l) + "\n" for l in lines))
            (folder / "s1" / "subagents" / "a.jsonl").write_text(json.dumps(
                {"type": "user", "message": {"content": "subagent words"}}) + "\n")

    def extract(self, *args):
        return subprocess.run([sys.executable, "-B", str(EXTRACT), *args], capture_output=True, text=True,
                              env={"PATH": os.environ["PATH"], **self.env})

    # covers: AC-9 (names, keys, emails and hex runs never reach the extract; a project off the list and subagent
    # files are skipped; tool results and meta lines are not your words)
    def test_redacts_and_skips(self):
        out = self.extract()
        self.assertEqual(out.returncode, 0, out.stderr)
        files = list((self.tmp / "home" / "claude-improve" / "extract").iterdir())
        self.assertEqual([f.name for f in files], ["project-01.jsonl"])
        text = files[0].read_text()
        for bad in ("acmecorp", "AcmeCorp", "sk-ant", "me@example.com", "ab12ab12", "subagent words", "skill body",
                    "result text", "theirs"):
            self.assertNotIn(bad, text)
        row = json.loads(text)
        self.assertEqual((row["project"], row["date"], row["tools"]), (self.mine, "2026-10-16", ["Edit"]))
        self.assertEqual(row["messages"], ["no, stop it: [REDACTED] key [REDACTED] mail [REDACTED] hex [REDACTED]"])

    # covers: AC-9 (only sessions changed since the last report.md are read)
    def test_since_last_report(self):
        folder = self.claude / "projects" / self.mine.replace("/", "-")
        os.utime(folder / "s1.jsonl", (1000, 1000))
        (folder / "s2.jsonl").write_text(json.dumps({"type": "user", "message": {"content": "newer words"}}) + "\n")
        report = self.tmp / "home" / "claude-improve" / "report.md"
        report.parent.mkdir(parents=True)
        report.write_text("last week\n")
        os.utime(report, (2000, 2000))
        self.assertEqual(self.extract().returncode, 0)
        rows = [json.loads(l) for l in (report.parent / "extract" / "project-01.jsonl").read_text().splitlines()]
        self.assertEqual([(r["session"], r["messages"]) for r in rows], [("s2", ["newer words"])])

    # covers: AC-9 (fails closed with no allow list or no names list, and when ~/claude-improve is in a git repo)
    def test_refuses(self):
        (self.tmp / "home" / ".git").mkdir()
        self.assertIn("inside a git repo", self.extract().stderr)
        (self.tmp / "home" / ".git").rmdir()
        (self.claude / "private" / "names.txt").unlink()
        self.assertEqual(self.extract().returncode, 1)
        (self.claude / "private" / "history-allow.txt").unlink()
        self.assertIn("history-allow.txt is missing", self.extract().stderr)
        self.assertFalse((self.tmp / "home" / "claude-improve" / "extract").exists())

    # covers: AC-9 (up to 3 findings into the runner inbox, redacted, never twice, counted by the hook)
    def test_propose(self):
        out = self.extract("--propose", "one AcmeCorp", "two", "three", "four")
        self.assertEqual(out.stdout, f"propose: 3 added to {self.ins / 'inbox.md'}\n")
        text = (self.ins / "inbox.md").read_text()
        self.assertNotIn("AcmeCorp", text)
        self.assertNotIn("four", text)
        self.assertEqual(self.extract("--propose", "two").stdout, f"propose: 0 added to {self.ins / 'inbox.md'}\n")
        self.assertEqual(self.hook(), f"wf proposals: 3 new ({self.ins / 'inbox.md'})\n")


if __name__ == "__main__":
    unittest.main()
