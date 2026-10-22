"""claude-home/skills/improve-my-system/extract.py (spec 0061 AC-9): copied from the archived runner suite, which no
longer runs. The runner's own `wf report --hook` line is runner only and stays in the archive."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EXTRACT = Path(__file__).resolve().parents[1] / "claude-home" / "skills" / "improve-my-system" / "extract.py"


class Extract(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.env = {"XDG_STATE_HOME": str(self.tmp / "state"), "CLAUDE_CONFIG_DIR": str(self.tmp / "home" / ".claude"),
                    "HOME": str(self.tmp / "home")}
        self.ins = self.tmp / "state" / "wf" / "insights"
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

    # covers: AC-9 (up to 3 findings into the inbox, redacted, never twice)
    def test_propose(self):
        out = self.extract("--propose", "one AcmeCorp", "two", "three", "four")
        self.assertEqual(out.stdout, f"propose: 3 added to {self.ins / 'inbox.md'}\n")
        text = (self.ins / "inbox.md").read_text()
        self.assertNotIn("AcmeCorp", text)
        self.assertNotIn("four", text)
        self.assertEqual(self.extract("--propose", "two").stdout, f"propose: 0 added to {self.ins / 'inbox.md'}\n")


if __name__ == "__main__":
    unittest.main()
