"""Spec 0018: the morning report at the end of every wf run, wf report, and the session start hook."""
import datetime
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ntfy  # noqa: E402
import report  # noqa: E402
from test_parallel import ParallelCase  # noqa: E402
from test_queue import DONE_B, ONE, TICK_A, DONE_A, TICK_B, TWO, QueueCase, blocked  # noqa: E402
from test_run import WF  # noqa: E402

# Feature 3 is not queued: its waiting boxes stay open for the live and yours lines.
WAITING = """
### 3. C · in-progress
- [x] (spec)
- [ ] Copy it: `cp a b` · waits on you · live
- [ ] Install: `./install.sh` · waits on you · live
- [ ] Check the phone · waits on you · later boxes go on

## Deferred
### 4. D
- [ ] Later thing · waits on you
"""
CFG = {"aliases": {}, "block": ["acme"], "server": "x", "topic": "t" * 32}


def rec(features, reason="queue_done", ended="2026-10-13T03:20:00+00:00", calls=()):
    return {"features": [{"feature": f, "outcome": o, "detail": d} for f, o, d in features],
            "stop_reason": reason, "ended": ended, "calls": list(calls)}


class Unit(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(subprocess.run, ["rm", "-rf", str(self.tmp)])
        env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.tmp / "state")})
        env.start()
        self.addCleanup(env.stop)
        (self.tmp / "state" / "wf" / "runs").mkdir(parents=True)

    def repo(self, name, scope="# Scope: x\n"):
        p = self.tmp / name
        (p / "docs" / "scope").mkdir(parents=True)
        (p / "docs" / "scope" / "scope.md").write_text(scope)
        return str(p)

    def source(self, path, r, folder="/f", code=None):
        return {"path": path, "name": os.path.basename(path), "folder": folder, "code": code, "rec": r}

    # covers: AC-2, AC-4 (head, items in AC-2 order, live counted per feature, the owed text without its tags,
    # Deferred skipped, next: wf; the phone body has the label and no park detail or run folder)
    def test_lines(self):
        p = self.repo("demo", "# Scope: x\n" + WAITING)
        calls = [{"cost_usd": 0.5, "tokens": {"input": 10, "output": 5, "cache_read": 0, "cache_write": 0}}]
        r = rec([("1. A", "blocked", "test park"), ("2. B", "feature_done", None), ("5. E", "waiting", "x")], calls=calls)
        full, body = report.render([self.source(p, r)], CFG)
        at = datetime.datetime.fromisoformat(r["ended"]).astimezone().strftime("%H:%M")
        self.assertEqual(full.splitlines(), [
            f"wf done {at}: 1 built, 1 stuck, 0 questions, 0.50 USD, 15 tokens", "built: 2. B",
            "stuck: 1. A: the step needs something only you can do: test park", "setup steps: 3. C: 2 step(s)",
            "for you: 3. C: Check the phone",
            "next: wf, then review and merge: demo", "run folder: /f"])
        label = ntfy.repo_label(CFG, p)
        self.assertEqual(body.splitlines(), full.splitlines()[:2] + ["stuck: 1. A: the step needs something only you can do"]
                         + full.splitlines()[3:5]
                         + [f"next: wf, then review and merge: {label}"])

    # covers: AC-2 (internal_error reads crash; distinct reasons in run order; question ids; stopped lines;
    # each repo suffix; no record, no end and not started rows)
    def test_status_and_rows(self):
        a, b, c, d, e = (self.repo(n) for n in "abcde")
        sources = [self.source(a, rec([("1. A", "decision_open", "k3x9")], reason="internal_error")),
                   self.source(b, rec([("1. B", "branch_changed", "moved")], reason="queue_done")),
                   self.source(c, None, folder=None, code=1), self.source(d, rec([], reason=None, ended=None)),
                   self.source(e, None, folder=None)]
        full, _ = report.render(sources, CFG)
        lines = full.splitlines()
        # Spec 0028 AC-13: reasons and prefixes in plain words.
        self.assertTrue(lines[0].startswith("wf stopped the build tool itself hit a bug, all queued work is done "),
                        lines[0])
        self.assertTrue(lines[0].endswith(": 0 built, 0 stuck, 1 questions, - USD, - tokens"), lines[0])
        self.assertEqual(lines[1:7], ["stopped: 1. B: the code was switched to another branch (b)",
                                      "question k3x9: 1. A (a)", "no record: c: exit 1 (c)", "did not finish: d (d)",
                                      "not started: e (e)", "next: wf"])

    # covers: AC-1, AC-2 (the parent's sources come from its summary rows: work rows only, folder - with a code is
    # no record, without one not started, a folder's run.json read for its features)
    def test_parent_rows(self):
        a, b, c = (self.repo(n) for n in ("ra", "rb", "rc"))
        folder = self.tmp / "state" / "wf" / "runs" / "rb-20261013-031000-1"
        folder.mkdir()
        (folder / "run.json").write_text(json.dumps(rec([("1. B", "feature_done", None)])))
        rows = [{"work": False, "name": "skipped"}, {"work": True, "path": a, "name": "ra", "folder": "-", "code": 5},
                {"work": True, "path": b, "name": "rb", "folder": str(folder), "code": 0},
                {"work": True, "path": c, "name": "rc", "folder": "-", "code": None}]
        with mock.patch.object(report, "send", return_value="sent") as send:
            report.end_of_parent(mock.Mock(ntfy=CFG), rows)
        self.assertEqual(send.call_count, 1)
        text = (self.tmp / "state" / "wf" / "report.txt").read_text().splitlines()
        self.assertEqual(text[1:], ["built: 1. B (rb)", "no record: ra: exit 5 (ra)", "not started: rc (rc)",
                                    "next: wf", f"run folder: {folder}"])

    # covers: AC-2 (next: wf, wf queue, review and merge, wf queue, in that order of precedence)
    def test_next(self):
        p = self.repo("demo")
        live = self.repo("live", "# Scope: x\n### 1. L\n- [ ] x · waits on you · live\n")
        cases = [([self.source(live, rec([]))], "next: wf"),
                 ([self.source(p, rec([("1. A", "blocked", None), ("2. B", "feature_done", None)]))], "next: wf"),
                 ([self.source(p, rec([("2. B", "feature_done", None)]))], "next: review and merge: demo"),
                 ([self.source(p, rec([]))], "next: wf")]
        for sources, line in cases:
            with self.subTest(line):
                self.assertEqual(report.render(sources, CFG)[0].splitlines()[-2], line)

    # covers: AC-4 (30 items: 12 lines, built lines dropped first, then others from the end, the more line before
    # next, under 1000 characters; a block list hit in one field replaces only that field)
    def test_cap_and_scrub(self):
        p = self.repo("demo")
        feats = [(f"{n}. Built", "feature_done", None) for n in range(15)]
        feats += [(f"{n}. Parked", "blocked", None) for n in range(15, 30)]
        feats[15] = ("15. Acme thing", "blocked", None)
        _, body = report.render([self.source(p, rec(feats))], CFG)
        lines = body.splitlines()
        self.assertEqual(len(lines), 12)
        self.assertLessEqual(len(body), 1000)
        why = "the step needs something only you can do"
        self.assertEqual(lines[1:10], [f"stuck: feature: {why}"] + [f"stuck: {n}. Parked: {why}" for n in range(16, 24)])
        self.assertEqual(lines[-2:], ["+21 more on the wf screen", "next: wf"])
        # Nine yours lines of about 130 characters fit the line cap but not the 1000 characters.
        boxes = "".join(f"- [ ] {n} " + "word " * 30 + "· waits on you\n" for n in range(9))
        q = self.repo("long", "# Scope: x\n### 1. A feature name that runs well past forty characters\n" + boxes)
        _, body = report.render([self.source(q, rec([]))], CFG)
        lines = body.splitlines()
        self.assertLessEqual(len(body), 1000)
        self.assertLessEqual(len(lines[1]), len("for you: ") + 40 + 2 + 80, lines[1])
        self.assertTrue(lines[1].endswith("..."), lines[1])
        self.assertEqual(lines[-2:], [f"+{9 - (len(lines) - 3)} more on the wf screen", "next: wf"])
        self.assertGreater(len(lines), 5)
        self.assertEqual(ntfy.scrub_field(CFG, "`/x` ~/y", 40, "step"), "step")
        self.assertEqual(ntfy.scrub_field(CFG, "fine words", 40, "step"), "fine words")

    # covers: AC-1, AC-3 (report.txt 0600 written atomically, report.seen removed, sent only on a message id; a
    # failing send only warns and records failed)
    def test_deliver(self):
        p = self.repo("demo")
        seen = self.tmp / "state" / "wf" / "report.seen"
        seen.write_text("")
        with mock.patch.object(ntfy.Topic, "post", return_value="m1") as post:
            self.assertEqual(report.deliver([self.source(p, rec([]))], CFG), "sent")
        body = post.call_args[0][0]
        self.assertEqual((body["title"], body["priority"], body["tags"], "actions" in body), ("wf report", 3, [], False))
        txt = self.tmp / "state" / "wf" / "report.txt"
        self.assertEqual(os.stat(txt).st_mode & 0o777, 0o600)
        self.assertFalse(seen.exists())
        with mock.patch.object(ntfy.Topic, "publish", return_value=None):
            self.assertEqual(report.deliver([self.source(p, rec([]))], CFG), "failed: no message id")
        with mock.patch.object(ntfy.Topic, "post", side_effect=OSError("refused")), \
                mock.patch.object(ntfy, "RETRY_GAP", 0.01), mock.patch("builtins.print") as out:
            self.assertEqual(report.deliver([self.source(p, rec([]))], CFG), "failed: refused")
        out.assert_called_once_with("warning: report: refused", flush=True)

    def hook(self, **env):
        out = subprocess.run([sys.executable, str(WF), "report", "--hook"], capture_output=True, text=True,
                             env={"PATH": os.environ["PATH"], "XDG_STATE_HOME": str(self.tmp / "state"), **env})
        self.assertEqual((out.returncode, out.stderr), (0, ""))
        return out.stdout

    def wf(self, *args):
        return subprocess.run([sys.executable, str(WF), "report", *args], capture_output=True, text=True,
                              env={"PATH": os.environ["PATH"], "XDG_STATE_HOME": str(self.tmp / "state")}).stdout

    # covers: AC-5, AC-6 (the hook shows an unseen report, nothing under WF_RUN or a held lock, nothing after
    # --seen, again after a newer report; wf report prints it or no report yet)
    def test_hook_and_seen(self):
        state = self.tmp / "state" / "wf"
        self.assertEqual((self.hook(), self.wf()), ("", "no report yet\n"))
        (state / "report.txt").write_text("wf done 03:20: x\nnext: wf\n")
        self.assertEqual(self.hook(), report.HOOK_HEAD + "\nwf done 03:20: x\nnext: wf\n")
        self.assertEqual(self.hook(WF_RUN="r"), "")
        (state / "locks").mkdir()
        lock = state / "locks" / "a.lock"
        holder = subprocess.Popen([sys.executable, "-c", "import fcntl, os, sys, time\n"
                                   "fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT)\nfcntl.flock(fd, fcntl.LOCK_EX)\n"
                                   "print('held', flush=True)\ntime.sleep(30)", str(lock)], stdout=subprocess.PIPE, text=True)
        self.addCleanup(holder.kill)
        holder.stdout.readline()
        self.assertEqual(self.hook(), "")
        holder.kill()
        holder.wait()
        holder.stdout.close()
        self.assertNotEqual(self.hook(), "")
        self.assertEqual(self.wf(), "wf done 03:20: x\nnext: wf\n")
        self.assertEqual(self.wf("--seen"), "")
        self.assertEqual(((state / "report.seen").read_text(), self.hook()), ("", ""))
        report.save("wf done 04:00: y\n")
        self.assertEqual(self.hook(), report.HOOK_HEAD + "\nwf done 04:00: y\n")

    # covers: AC-5, AC-6 (the killed run line for a dead pid folder newer than report.txt with no ended; never for
    # an ended record, a live pid, an older folder, or one report.seen names)
    def test_killed_line(self):
        state = self.tmp / "state" / "wf"
        report.save("old\n")
        dead = subprocess.Popen([sys.executable, "-c", ""])
        dead.wait()
        stamp = (datetime.datetime.now() + datetime.timedelta(minutes=1)).strftime("%Y%m%d-%H%M%S")
        name = f"my-repo-{stamp}-{dead.pid}"
        (state / "runs" / name).mkdir()
        line = f"wf run {name} ended without a record (killed or power loss), see its log.txt\n"
        self.assertEqual(self.hook(), report.HOOK_HEAD + "\nold\n" + line)
        (state / "runs" / name / "run.json").write_text(json.dumps({"ended": None}))
        self.assertEqual(self.wf(), "old\n" + line)
        (state / "runs" / name / "run.json").write_text(json.dumps({"ended": "x"}))
        self.assertEqual(self.wf(), "old\n")
        (state / "runs" / name / "run.json").unlink()
        live = f"my-repo-{stamp}-{os.getpid()}"
        os.rename(state / "runs" / name, state / "runs" / live)
        self.assertEqual(self.wf(), "old\n")
        os.rename(state / "runs" / live, state / "runs" / name)
        old = (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime("%Y%m%d-%H%M%S")
        os.rename(state / "runs" / name, state / "runs" / f"my-repo-{old}-{dead.pid}")
        self.assertEqual(self.wf(), "old\n")
        os.rename(state / "runs" / f"my-repo-{old}-{dead.pid}", state / "runs" / name)
        self.assertEqual(self.wf("--seen"), line)
        self.assertEqual(((state / "report.seen").read_text(), self.wf()), (name, "old\n"))

    # covers: AC-6 (the hook swallows its own errors: an unreadable report.txt still exits 0 with no output)
    def test_hook_swallows(self):
        (self.tmp / "state" / "wf" / "report.txt").mkdir()
        self.assertEqual(self.hook(), "")

    # covers: AC-8 (--parallel PASS needs both children "parent" and one report.txt naming both repos)
    def test_parallel_e2e_checks(self):
        spec = importlib.util.spec_from_file_location("e2e_run", Path(report.__file__).parent / "e2e" / "run.py")
        e2e = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(e2e)
        top = self.tmp / "top"
        call = {"started": "2026-10-13T03:00:00+00:00", "duration_s": 60}
        for name in ("one", "two"):
            (top / "state" / "wf" / "runs" / name).mkdir(parents=True)
        txt = top / "state" / "wf" / "report.txt"

        def check(reports, text):
            for name, rep in zip(("one", "two"), reports):
                (top / "state" / "wf" / "runs" / name / "run.json").write_text(json.dumps(
                    {"features": [{"outcome": "feature_done"}], "calls": [call], "report": rep}))
            if text is None:
                txt.unlink(missing_ok=True)
            else:
                txt.write_text(text)
            with mock.patch.object(e2e.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)):
                return e2e.parallel_failure(str(top), {})
        both = "built: 1. A (one)\nbuilt: 1. A (two)\n"
        self.assertIsNone(check(["parent", "parent"], both))
        self.assertEqual(check(["parent", "sent"], both), "run.json report ['parent', 'sent']")
        self.assertEqual(check(["parent", "parent"], None), "no report.txt")
        self.assertEqual(check(["parent", "parent"], "built: 1. A (one)\n"), "report.txt does not name both repos")


class TestEndOfRun(QueueCase):
    # covers: AC-1, AC-3 (a single repo run writes report.txt and records sent; the note is the phone body)
    def test_single(self):
        repo = self.make_repo("two", TWO + WAITING)
        self.commit(repo)
        self.steps([blocked(), TICK_B, DONE_B])
        r = self.wf("two", "-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        folder, record = self.run_record()
        self.assertEqual(record["report"], "sent")
        text = (self.state / "wf" / "report.txt").read_text().splitlines()
        # Spec 0021 AC-6: the park's open question with its recommended answer.
        self.assertRegex(text[3], r"^question [a-z0-9]{4}: 1\. A: the step needs something only you can do in 1\. A\. test park "
                                  r"\(recommended: done, go on\)$")
        self.assertEqual(text[1:3] + text[4:7], ["built: 2. B",
                                                 "stuck: 1. A: the step needs something only you can do: test park",
                                                 "setup steps: 3. C: 2 step(s)", "for you: 3. C: Check the phone", "next: wf, then review and merge: two"])
        self.assertEqual(text[-1], f"run folder: {folder}")
        notes = [p for p in self.report_ntfy.posts if p["title"] == "wf report"]
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["message"].splitlines()[2], "stuck: 1. A: the step needs something only you can do")

    # covers: AC-1 (internal_error still writes and sends); AC-3 (a failing POST warns, records failed, keeps the code)
    def test_crash_and_failed_send(self):
        self.steps([{}])
        r = self.wf("demo", "-y", mode="boom")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertEqual(self.run_record()[1]["report"], "sent")
        self.assertIn(" stopped the build tool itself hit a bug ", (self.state / "wf" / "report.txt").read_text().splitlines()[0])
        self.again()
        self.report_ntfy.fail_posts = 3
        r = self.wf("demo", "-y", mode="boom")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertTrue(self.run_record()[1]["report"].startswith("failed: "))
        self.assertIn("\nwarning: report: ", r.stdout)

    # covers: AC-1, AC-4 (a Ctrl C run still sends: the report ignores the run's stopped flag, so a failed first
    # POST is retried instead of giving up)
    def test_interrupted_sends(self):
        self.make_repo("one", ONE)
        self.steps([{"tick": False, "sleep": 60}])
        self.report_ntfy.fail_posts = 1
        p = self.start("one", "-y")
        self.wait_for(self.fakes / "argv-1.json", timeout=20)
        p.send_signal(2)
        out, err = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 130, out + err)
        self.assertEqual(self.run_record()[1]["report"], "sent")
        # The fake keeps the failed POST too: two posts means the retry went out after Ctrl C.
        self.assertEqual(len([p for p in self.report_ntfy.posts if p["title"] == "wf report"]), 2)
        self.assertTrue((self.state / "wf" / "report.txt").read_text().startswith("wf stopped you stopped the build "))


class TestParent(ParallelCase):
    # covers: AC-1, AC-2 (children record parent and send nothing; the parent sends one note naming both repos)
    def test_one_note(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(a, b)
        self.steps({"ra": [TICK_A, DONE_A], "rb": [TICK_A, DONE_A]})
        r = self.wf("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual({n: x["report"] for n, x in self.run_records().items()}, {"ra": "parent", "rb": "parent"})
        notes = [p for p in self.report_ntfy.posts if p["title"] == "wf report"]
        self.assertEqual(len(notes), 1)
        # The labels as the run saw them: its HOME holds no private names list (spec 0021 AC-8).
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp)}):
            la, lb = (ntfy.repo_label(json.loads((self.tmp / "config" / "wf" / "ntfy.json").read_text()), str(x))
                      for x in (a, b))
        self.assertEqual(notes[0]["message"].splitlines()[1:], [f"built: 1. A ({la})", f"built: 1. A ({lb})",
                                                                f"next: review and merge: {la}, {lb}"])
        self.assertTrue(notes[0]["message"].startswith("wf done "))
        text = (self.state / "wf" / "report.txt").read_text()
        self.assertIn("built: 1. A (ra)\nbuilt: 1. A (rb)\n", text)


if __name__ == "__main__":
    unittest.main()
