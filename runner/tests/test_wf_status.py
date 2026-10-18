import io
import json
import os
import re
import sys
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auto  # noqa: E402
import run  # noqa: E402
import wf  # noqa: E402
from test_auto import AutoCase  # noqa: E402
from test_queue import decision  # noqa: E402

SID = "0a73f089-5127-4347-998d-3a7c8adf3ac9"
ANSI = re.compile(r"\033\[[0-9;]*m")


class TestStatus(AutoCase):
    def status(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = wf.main(["status", "--json"])
        self.assertEqual(code, 0)
        return json.loads(out.getvalue())

    def active(self, *entries):
        p = Path(run.active_path())
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(list(entries)))

    def runs(self, *names):
        for n in names:
            (self.tmp / "state" / "wf" / "runs" / n).mkdir(parents=True)

    # covers: spec 0059 AC-1 (a missing or broken file is null, never an empty list)
    def test_unreadable_is_null(self):
        self.assertEqual(self.status(), {"running": None, "parked": [], "questions": []})
        self.active()
        Path(run.state_dir(), "queue.json").write_text("not json")
        self.assertEqual(self.status(), {"running": [], "parked": None, "questions": None})
        Path(run.active_path()).write_text("{broken")
        self.assertIsNone(self.status()["running"])

    # covers: spec 0059 AC-1 (running: only entries whose lock is held, each with its own run folder as id, never the
    # folder of an earlier run of the same tree; parked and questions from the unanswered decisions)
    def test_running_parked_questions(self):
        tree = self.tmp / "trees" / "feat-0001-a"
        tree.mkdir(parents=True)
        mine = f"feat-0001-a-20261018-010203-{os.getpid()}"
        self.runs("feat-0001-a-20261018-090000-1", mine, "feat-0001-ab-20261018-090000-" + str(os.getpid()))
        (self.tmp / "state" / "wf" / "locks").mkdir(parents=True)
        fd, _ = run.repo_lock(str(tree), what="wf run feat-0001-a")
        self.addCleanup(os.close, fd)
        self.active({"repo": str(self.folder), "feature": "1. A", "tree": str(tree)},
                    {"repo": str(self.other), "feature": "2. Stale", "tree": str(self.tmp / "trees" / "gone")})
        self.queue(decision(self.folder, "1. A", did="ab12", parked=True),
                   decision(self.other, "3. B", did="cd34"),
                   decision(self.other, "4. C", did="ef56", answer="SQLite"))
        self.assertEqual(self.status(), {
            "running": [{"id": mine, "repo": "work", "feature": "1. A"}],
            "parked": [{"id": "ab12", "repo": "work", "feature": "1. A"}],
            "questions": [{"id": "ab12", "repo": "work", "feature": "1. A", "title": "Which storage engine?"},
                          {"id": "cd34", "repo": "other", "feature": "3. B", "title": "Which storage engine?"}]})

    # covers: spec 0059 AC-1 (read only: nothing is created under the runner's state)
    def test_read_only(self):
        self.status()
        self.assertFalse((self.tmp / "state" / "wf").exists())


class TestShortBar(AutoCase):
    def setUp(self):
        super().setUp()
        env = mock.patch.dict(os.environ, {"ANTHROPIC_BASE_URL": "", "CLAUDE_CODE_EFFORT_LEVEL": ""})
        env.start()
        self.addCleanup(env.stop)
        self.dash = self.tmp / "state" / "wf-dash"

    def bar(self, sid=SID, **extra):
        data = {"session_id": sid, "workspace": {"current_dir": str(self.folder)}, "model": {"display_name": "Opus"},
                **extra}
        code, out = self.cli("bar", stdin=json.dumps(data))
        self.assertEqual(code, 0)
        return ANSI.sub("", out)

    def mark(self, age=0):
        self.dash.mkdir(parents=True, exist_ok=True)
        m = self.dash / SID
        m.touch()
        os.utime(m, (time.time() - age, time.time() - age))

    # covers: spec 0059 AC-4 (short only while this session's marker is under 15 s old; the AUTO segment stays; a
    # second chat without the mod, and an old marker, keep the full bar)
    def test_short_only_beside_a_live_band(self):
        full = self.bar()
        self.assertIn("Opus", full)
        self.mark()
        self.assertEqual(self.bar(), "work\n")
        self.assertEqual(self.bar(sid="another-session"), full)
        self.on()
        self.assertEqual(self.bar(), "work AUTO idle, 0 question(s)\n")
        self.mark(age=16)
        self.assertIn("Opus", self.bar())

    # covers: spec 0059 AC-4 (seen is still updated with the short bar)
    def test_short_bar_marks_the_chat_seen(self):
        self.on()
        key = auto.chat(auto.load(), str(self.folder))[0]
        auto.change(lambda s: s["chats"][key].update(seen="2000-01-01T00:00:00+00:00"))
        self.mark()
        self.assertEqual(self.bar(), "work AUTO idle, 0 question(s)\n")
        self.assertGreater(auto.secs(auto.chat(auto.load(), str(self.folder))[1].get("seen")), time.time() - 60)

    # covers: spec 0059 AC-2 (the effort comes only from .effort.level, written next to the marker when present and
    # changed; an env var alone writes nothing; a bad session id or level never names a file)
    def test_effort_handover(self):
        effort = self.dash / f"{SID}.effort"
        self.mark()
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_EFFORT_LEVEL": "high"}):
            self.bar()
        self.assertFalse(effort.exists())
        self.bar(effort={"level": "medium"})
        self.assertEqual(effort.read_text(), "medium")
        os.utime(effort, (1, 1))
        self.bar(effort={"level": "medium"})
        self.assertEqual(effort.stat().st_mtime, 1)
        self.bar(effort={"level": "xhigh"})
        self.assertEqual(effort.read_text(), "xhigh")
        self.bar(effort={"level": "../x"})
        self.bar(sid="../x", effort={"level": "low"})
        self.assertEqual(effort.read_text(), "xhigh")
        self.assertEqual(sorted(p.name for p in self.dash.iterdir()), [SID, f"{SID}.effort"])

    # covers: spec 0059 AC-5 (no mod folder: the bar writes no effort file and creates no folder)
    def test_no_mod_no_effort_file(self):
        self.bar(effort={"level": "medium"})
        self.assertFalse(self.dash.exists())


if __name__ == "__main__":
    unittest.main()
