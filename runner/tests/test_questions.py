"""Spec 0039: questions while wf is off."""
import fcntl
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pr  # noqa: E402
import questions  # noqa: E402
import run  # noqa: E402
import telegram  # noqa: E402
from test_queue import DecisionCase, ONE, decision  # noqa: E402
from test_telegram import TelegramCase, msg_update  # noqa: E402
from test_wf_bare import BareCase  # noqa: E402


def write_queue(state, decisions):
    p = Path(state) / "wf" / "queue.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"version": 1, "parks": [], "decisions": decisions}))
    return p


class TestAnswer(TelegramCase):
    def setUp(self):
        super().setUp()
        self.state = self.tmp / "state"

    def queue(self):
        return json.loads((self.state / "wf" / "queue.json").read_text())["decisions"]

    # covers: AC-2, AC-3 (a number picks the label, source keyboard, the queue still loads; an answered one is not
    # answered twice; a label and free text parse as a Telegram reply)
    def test_answer(self):
        write_queue(self.state, [decision("/r/demo", "1. A"), decision("/r/demo", "2. B", did="cd34")])
        d = questions.answer("ab12", "2")
        self.assertEqual((d["answer"], d["source"]), ("SQLite", "keyboard"))
        self.assertIsNone(questions.answer("ab12", "1"))
        self.assertEqual(questions.answer("cd34", "use a file").get("answer"), "use a file")
        q = run.queue_transact()["decisions"]
        self.assertEqual([(x["answer"], x["source"]) for x in q], [("SQLite", "keyboard"), ("use a file", "keyboard")])
        self.assertTrue(all(x["answered"] for x in q))

    # covers: AC-4 (a keyboard answer is strong under ntfy; a phone one there is not without a code)
    def test_strong(self):
        r = mock.Mock(ntfy={"topic": "x"})
        self.assertTrue(pr.strong(r, {"source": "keyboard"}))
        self.assertFalse(pr.strong(r, {"source": "phone"}))

    # covers: AC-1, AC-2 (the section lists every open question oldest first with numbered options and the
    # recommended one; -y never asks; Enter skips; a typed answer is written; Ctrl C cancels with 130)
    def test_screen(self):
        write_queue(self.state, [decision("/r/demo", "1. A", asked="2026-10-12T10:00:00+02:00"),
                                 decision("/r/quux", "(run)", did="cd34", options=[], kind="prose"),
                                 decision("/r/demo", "2. B", did="ef56", answer="SQLite", source="phone")])
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("builtins.input", side_effect=AssertionError("asked")):
            self.assertIsNone(questions.screen(True))
        self.assertEqual(out.getvalue(), "questions:\n  cd34 quux: (run): Which storage engine?\n"
                         "    (no options, type your answer)\n  ab12 demo: 1. A: Which storage engine?\n"
                         "    1 Postgres (recommended) (recommended)\n    2 SQLite\n")
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("builtins.input", side_effect=["", "1"]):
            self.assertIsNone(questions.screen(False))
        self.assertIn("answered: ab12 Postgres (recommended) (keyboard)\n", out.getvalue())
        self.assertEqual([x["answer"] for x in self.queue()], ["Postgres (recommended)", None, "SQLite"])
        with redirect_stdout(io.StringIO()), mock.patch("builtins.input", side_effect=KeyboardInterrupt):
            self.assertEqual(questions.screen(False), 130)
        self.assertIsNone(self.queue()[1]["answer"])

    # covers: AC-5 (links from context and asked; read only: no state folder is made; an unreadable queue refuses)
    def test_command(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(questions.cmd_questions(), 0)
        self.assertEqual(out.getvalue(), "no open questions\n")
        self.assertFalse(self.state.exists())
        ctx = {"spec": "https://github.com/acme/demo/blob/work/docs/specs/0001-x/index.md",
               "issues": ["https://github.com/acme/demo/issues/3"], "pr": {"number": 7, "url": "https://github.com/acme/demo/pull/7"}}
        p = write_queue(self.state, [decision("/r/demo", "1. A", context=ctx)])
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(questions.cmd_questions(), 0)
        self.assertEqual(out.getvalue().splitlines()[3:], [
            f"  spec: {ctx['spec']}", "  issue: https://github.com/acme/demo/issues/3",
            "  PR: #7 https://github.com/acme/demo/pull/7", "  asked: 2026-10-12T09:00:00+02:00"])
        p.write_text("{")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(questions.cmd_questions(), 5)


class TestResume(DecisionCase):
    # covers: AC-3 (the next run resumes the call with the keyboard answer, as with a phone answer)
    def test_next_run_resumes(self):
        from test_queue import DONE_A, TICK_A
        repo = self.make_repo("later", ONE)
        self.commit(repo)
        d = self.open_one("later")
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": self.env["XDG_STATE_HOME"]}):
            self.assertEqual(questions.answer(d["id"], "2")["answer"], "SQLite")
        self.steps([TICK_A, DONE_A])
        r = self.wf("later", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"  resume: {d['id']} 1. A: Which storage engine?\n", r.stdout)
        self.assertEqual(self.argv(1)["argv"][:4], ["-p", run.ANSWERED + "SQLite", "--resume", "s-1"])


class TestBareScreen(BareCase):
    # covers: AC-1, AC-2 (bare `wf` at a terminal: the questions section first, the answer written before the plan,
    # which then shows it as a resume; cancelling the build prompt keeps the answer)
    def test_wf_screen(self):
        a = self.make_repo("ra", ONE)
        self.trust(a)
        write_queue(self.state, [decision(a, "1. A")])
        r = self.bare(stdin="2\nx\n")
        self.assertEqual(r.returncode, 130, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith("questions:\n  ab12 ra: 1. A: Which storage engine?\n"), r.stdout)
        self.assertIn("answered: ab12 SQLite (keyboard)", r.stdout)
        self.assertIn("resume: ab12 1. A", r.stdout)
        d = json.loads((self.state / "wf" / "queue.json").read_text())["decisions"][0]
        self.assertEqual((d["answer"], d["source"]), ("SQLite", "keyboard"))


class TestFetchCommand(TelegramCase):
    # covers: AC-6 (no telegram.json: exit 0, nothing made; a fetch saves updates silently; a held lock returns
    # without calling Telegram; a broken config exits 1 with one stderr line)
    def test_fetch(self):
        self.bot.updates = [msg_update(1, "ab12 1")]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(telegram.cmd_fetch(), 0)
        self.assertEqual((out.getvalue(), err.getvalue()), ("", ""))
        self.assertEqual([l["id"] for l in telegram.read_log()], ["u1"])
        fd = os.open(os.path.join(telegram.state_dir(), "telegram.lock"), os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            self.assertEqual(telegram.cmd_fetch(), 0)
        finally:
            os.close(fd)
        self.assertEqual(len(self.bot.sent("getUpdates")), 1)
        self.cfg_path.chmod(0o644)
        with redirect_stderr(err):
            self.assertEqual(telegram.cmd_fetch(), 1)
        self.assertEqual(len(err.getvalue().splitlines()), 1)
        self.cfg_path.unlink()
        os.rename(telegram.log_path(), str(self.tmp / "kept"))
        self.assertEqual(telegram.cmd_fetch(), 0)
        self.assertFalse(os.path.exists(telegram.log_path()))


class TestTimer(TelegramCase):
    def setUp(self):
        super().setUp()
        self.calls = []

        def fake(argv, **kw):
            self.calls.append(argv[2:])
            return subprocess.CompletedProcess(argv, self.code, "", "boom" if self.code else "")
        self.code = 0
        p = mock.patch.object(telegram.subprocess, "run", side_effect=fake)
        p.start()
        self.addCleanup(p.stop)
        self.units = self.tmp / "config" / "systemd" / "user"

    def timer(self, state, env=None):
        with mock.patch.dict(os.environ, env or {}), redirect_stdout(io.StringIO()) as out:
            return telegram.cmd_timer(state), out.getvalue()

    # covers: AC-7 (on writes both units with this state folder and enables the timer; off disables and removes
    # them; refusals under WF_RUN and without telegram.json; a failed systemctl exits 1)
    def test_on_off(self):
        self.assertEqual(self.timer("on")[0], 0)
        service = (self.units / "wf-telegram-fetch.service").read_text()
        self.assertIn(" telegram fetch\n", service)
        self.assertIn(f'Environment="XDG_STATE_HOME={self.tmp / "state"}"\n', service)
        self.assertIn("Type=oneshot\n", service)
        self.assertIn("OnUnitActiveSec=5min\n", (self.units / "wf-telegram-fetch.timer").read_text())
        self.assertEqual(self.calls, [["daemon-reload"], ["enable", "--now", "wf-telegram-fetch.timer"]])
        self.calls.clear()
        self.assertEqual(self.timer("off")[0], 0)
        self.assertEqual(self.calls, [["disable", "--now", "wf-telegram-fetch.timer"], ["daemon-reload"]])
        self.assertEqual(list(self.units.iterdir()), [])
        self.calls.clear()
        self.assertEqual(self.timer("on", {"WF_RUN": "x"})[0], 5)
        self.cfg_path.unlink()
        rc, out = self.timer("on")
        self.assertEqual(rc, 5)
        self.assertTrue(out.startswith("refused: no_telegram: "), out)
        self.assertEqual((self.calls, list(self.units.iterdir())), ([], []))
        self.code = 1
        self.assertEqual(self.timer("off"), (1, "systemctl: boom\n"))


if __name__ == "__main__":
    unittest.main()
