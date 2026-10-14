"""Spec 0017: bare `wf run` as a parent of single repo runs, side by side."""
import datetime
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_browser import AppCase  # noqa: E402
from test_park import GIT_ID  # noqa: E402
from test_queue import DONE_A, ONE, TICK_A, DecisionCase, QueueCase, park  # noqa: E402
from test_run import plan, run, summary  # noqa: E402

SLOW = {**TICK_A, "sleep": 3}
LOCK_HOLDER = """import fcntl, os, sys, time
fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)
fcntl.flock(fd, fcntl.LOCK_EX)
os.ftruncate(fd, 0)
os.write(fd, b"4242 2026-10-13T00:00:00+00:00\\n")
open(sys.argv[2], "w").write(str(os.getpid()))
time.sleep(60)
"""


def kill(pid):
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def at(iso):
    return datetime.datetime.fromisoformat(iso)


class ParallelCase(QueueCase):
    def trust(self, *paths):
        (self.tmp / "config" / "wf" / "allowed.json").write_text(json.dumps([str(p) for p in paths]))

    def assert_after(self, recs, first, second):
        """AC-2, AC-3: the second child confirmed only after the first child's run ended."""
        self.assertGreaterEqual(at(recs[second]["started"]), at(recs[first]["ended"]), recs)

    def slow_start(self, repo):
        """The first git command that repo's child runs sleeps 2 seconds, so its start checks are slow."""
        mark, real = self.fakes / "slow-git", shutil.which("git")
        (self.bin / "git").unlink()
        self.fake("git", f"""#!{sys.executable}
import os, sys, time
args = open(f"/proc/{{os.getppid()}}/cmdline").read().split("\\0")
if "-u" in args and {str(repo)!r} in args and not os.path.exists({str(mark)!r}):
    open({str(mark)!r}, "w").close()
    time.sleep(2)
os.execv({real!r}, ["git", *sys.argv[1:]])
""")


class TestSideBySide(ParallelCase):
    # covers: AC-1, AC-4 (one child per repo with work after the jobs line; the second starts only after the first
    # printed its run folder line; their calls overlap; every child line carries its prefix; one summary)
    def test_two_repos(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(a, b)
        self.slow_start(a)
        self.steps({"ra": [SLOW, DONE_A], "rb": [SLOW, DONE_A]})
        r = self.wf("-y", "--budget", "3", "--call-timeout", "9", "--max-calls", "7", "--max-hours", "2", "--max-wait", "5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = plan(r.stdout)
        self.assertEqual(lines[lines.index("jobs: 2 at once") - 1][:5], "caps:")
        folder = next(i for i, x in enumerate(lines) if x.startswith("[ra] run folder: "))
        first_b = next(i for i, x in enumerate(lines) if x.startswith("[rb] "))
        self.assertGreater(first_b, folder, r.stdout)
        body = lines[lines.index("jobs: 2 at once") + 1:lines.index("summary:")]
        self.assertEqual([x for x in body if not x.startswith(("[ra] ", "[rb] "))], [])
        recs = self.run_records()
        for rec in recs.values():
            self.assertEqual(rec["caps"], {"budget_usd": 3, "call_timeout_min": 9, "max_calls": 7, "max_hours": 2,
                                           "max_wait_h": 5})
        ca, cb = recs["ra"]["calls"][0], recs["rb"]["calls"][0]
        self.assertLess(at(cb["started"]), at(ca["started"]) + datetime.timedelta(seconds=ca["duration_s"]), recs)
        self.assertLess(at(ca["started"]), at(cb["started"]) + datetime.timedelta(seconds=cb["duration_s"]), recs)
        fa = lines[folder][len("[ra] run folder: "):]
        s = summary(r.stdout)
        self.assertEqual(s[0], f"  ra: exit 0, done: 1. A | run folder: {fa}")
        self.assertTrue(s[1].startswith("  rb: exit 0, done: 1. A | run folder: " + str(self.state / "wf" / "runs" / "rb-")))
        self.assertEqual(len(s), 2)

    # covers: AC-4 (lines reach the terminal while the child still runs, not when it exits)
    def test_streaming(self):
        a = self.make_repo("ra", ONE)
        self.trust(a)
        self.steps({"ra": [{**TICK_A, "sleep": 5}, DONE_A]})
        p = self.start("-y")
        seen = []
        while not seen or not seen[-1].startswith("[ra] run folder: "):
            line = p.stdout.readline()
            self.assertNotEqual(line, "", seen)
            seen.append(line.rstrip("\n"))
        self.assertIsNone(p.poll())
        self.assertFalse(any(x.startswith("[ra] [1/20]") for x in seen))
        out, err = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 0, out + err)
        self.assertTrue(out.startswith("[ra] [1/20] ra: /develop a -> success"), out)


class TestJobs(ParallelCase):
    # covers: AC-2 (--jobs 1 runs the repos one after the other; a bad value is a usage error; a target run takes
    # the flag and prints no jobs line, no prefix and no summary)
    def test_one_at_a_time(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(a, b)
        self.steps({"ra": [SLOW, DONE_A], "rb": [TICK_A, DONE_A]})
        r = self.wf("-y", "--jobs", "1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("\njobs: 1 at once\n", r.stdout)
        self.assert_after(self.run_records(), "ra", "rb")

    def test_bad_values(self):
        for v in ("0", "1.5", "x", "-1"):
            with self.subTest(v):
                r = self.wf("-y", "--jobs", v)
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn("--jobs", r.stderr)
        self.steps([{}])
        r = self.wf("demo", "-y", "--jobs", "3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("jobs:", r.stdout)
        self.assertNotIn("summary:", r.stdout)
        self.assertNotIn("[demo] ", r.stdout)


class TestNeverTogether(ParallelCase):
    # covers: AC-3 (a linked worktree sharing the git common dir, and a repo nested in another, each wait for the
    # other's child to end)
    def test_common_dir_and_nested(self):
        with self.subTest("shared git common dir"):
            a = self.make_repo("wa", ONE)
            self.commit(a)
            w = self.tmp / "root" / "wb"
            subprocess.run(["git", *GIT_ID, "-C", str(a), "worktree", "add", "-q", "-b", "wtb", str(w)],
                           check=True, capture_output=True)
            self.trust(a, w)
            self.steps({"wa": [SLOW, DONE_A], "wb": [TICK_A, DONE_A]})
            r = self.wf("-y")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("\njobs: 2 at once\n", r.stdout)
            self.assert_after(self.run_records(), "wa", "wb")
        with self.subTest("nested"):
            self.again()
            outer = self.make_repo("outer", ONE)
            inner = self.make_repo("outer/inner", ONE)
            self.trust(inner, outer)
            self.steps({"inner": [SLOW, DONE_A], "outer": [TICK_A, DONE_A]})
            r = self.wf("-y")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assert_after(self.run_records(), "inner", "outer")

    def test_clashes(self):
        base = {"port": None, "common": None}
        self.assertTrue(run.clashes({**base, "path": "/r/a"}, {**base, "path": "/r/a/b"}))
        self.assertTrue(run.clashes({**base, "path": "/r/a/b"}, {**base, "path": "/r/a"}))
        self.assertFalse(run.clashes({**base, "path": "/r/a"}, {**base, "path": "/r/ab"}))
        self.assertTrue(run.clashes({**base, "path": "/a", "port": 80}, {**base, "path": "/b", "port": 80}))
        self.assertFalse(run.clashes({**base, "path": "/a", "port": 80}, {**base, "path": "/b", "port": 8080}))
        self.assertTrue(run.clashes({**base, "path": "/a", "common": "/g"}, {**base, "path": "/b", "common": "/g"}))
        self.assertEqual([run.app_port(u) for u in ("http://localhost", "https://127.0.0.1", "http://[::1]:3000")],
                         [80, 443, 3000])


class TestPortClash(AppCase):
    # covers: AC-3 (two repos whose app url names the same port run one after the other)
    def test_same_port(self):
        other = self.make_repo("other", ONE)
        (other / "AGENTS.md").write_text((self.repo / "AGENTS.md").read_text())
        (self.repo / "docs/scope/scope.md").write_text(ONE)
        self.steps({"demo": [SLOW, DONE_A], "other": [TICK_A, DONE_A]})
        r = self.wf("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        recs = self.run_records()
        self.assertGreaterEqual(at(recs["other"]["started"]), at(recs["demo"]["ended"]), recs)


class TestDecisions(DecisionCase, ParallelCase):
    # covers: AC-1 (a repo holding only an unanswered decision has work: its child re-pings it)
    def test_open_only(self):
        repo = self.make_repo("rp", ONE)
        self.commit(repo)
        d = self.open_one("rp")
        first = self.ntfy.posts[0]
        self.trust(repo)
        r = self.wf("-y", "--max-wait", "0.0001")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        lines = plan(r.stdout)
        self.assertIn(f"  open: {d['id']} 1. A: Which storage engine?", lines)
        self.assertIn("jobs: 1 at once", lines)
        self.assertEqual(self.ntfy.pings()[-1], first)
        self.assertEqual(len(self.queue()["decisions"][0]["pings"]), 2)
        self.assertTrue(summary(r.stdout)[0].startswith("  rp: exit 6, "), r.stdout)

    # covers: AC-7 (two children with one open decision each and one phone reply per decision each resume their own)
    def test_each_resumes_own(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        for repo in (a, b):
            self.commit(repo)
            self.open_one(repo.name)
        ids = {Path(d["repo"]).name: d["id"] for d in self.queue()["decisions"]}
        self.ntfy.add(f"{ids['ra']} 1")
        self.ntfy.add(f"{ids['rb']} 2")
        self.trust(a, b)
        self.steps({"ra": [TICK_A, DONE_A], "rb": [TICK_A, DONE_A]})
        r = self.wf("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for name, answer in (("ra", "Postgres (recommended)"), ("rb", "SQLite")):
            argv = json.loads((self.fakes / f"{name}-argv-1.json").read_text())["argv"]
            self.assertEqual(argv[:4], ["-p", run.ANSWERED + answer, "--resume", "s-1"], name)
            self.assertEqual([e["id"] for e in self.run_records()[name]["decisions"]], [ids[name]])
        self.assertEqual(self.queue()["decisions"], [])


class TestExitAndSummary(ParallelCase):
    # covers: AC-1, AC-6 (another process takes a repo's lock after the parent let it go: that child is refused
    # locked), spec 0020 AC-7 (the parent counts it as a running skip, not as exit 6)
    def test_locked_child(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(a, b)
        lock = self.state / "wf" / "locks" / (run.hashlib.sha1(str(b).encode()).hexdigest() + ".lock")
        pid_file = self.fakes / "holder.pid"
        self.addCleanup(lambda: pid_file.exists() and kill(int(pid_file.read_text())))
        # Without WF_RUN, so the sweep at the end of ra's run leaves the holder alive.
        grab = [sys.executable, "-c", "import os, subprocess, sys, time\n"
                f"subprocess.Popen([sys.executable, '-c', {LOCK_HOLDER!r}, {str(lock)!r}, {str(pid_file)!r}], "
                "start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, "
                "stderr=subprocess.DEVNULL, env={k: v for k, v in os.environ.items() if k != 'WF_RUN'})\n"
                f"while not os.path.exists({str(pid_file)!r}):\n    time.sleep(0.05)\n"]
        self.steps({"ra": [{**TICK_A, "run": [grab]}, DONE_A], "rb": [TICK_A, DONE_A]})
        r = self.wf("-y", "--jobs", "1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("\n[rb] refused: locked: another wf run holds this repo: pid 4242 since 2026-10-13T00:00:00+00:00\n",
                      r.stdout)
        s = summary(r.stdout)
        self.assertTrue(s[0].startswith("  ra: exit 0, done: 1. A | run folder: "), s)
        self.assertEqual(s[1], "  rb: skipped: running: another wf run holds this repo: pid 4242 since "
                               "2026-10-13T00:00:00+00:00")
        self.assertNotIn("no record", (self.state / "wf" / "report.txt").read_text())

    # covers: AC-4, AC-6 (a skipped repo shows skipped: and leaves the code 0; two repos with one name get
    # <parent>/<name> prefixes)
    def test_skip_and_names(self):
        main = self.make_repo("onmain", ONE, head="ref: refs/heads/main\n")
        x, y = self.make_repo("x/same", ONE), self.make_repo("y/same", ONE)
        self.trust(main, x, y)
        r = self.wf("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("\n[x/same] done: 1. A\n", r.stdout)
        self.assertIn("\n[y/same] done: 1. A\n", r.stdout)
        s = summary(r.stdout)
        # Spec 0021 R1: a repo on main builds on the feat/ branch its child makes.
        self.assertTrue(s[0].startswith("  onmain: exit 0, done: 1. A | run folder: "), s)
        self.assertIn("\n[onmain] branch: feat/a from main\n", r.stdout)
        self.assertTrue(s[1].startswith("  x/same: exit 0, done: 1. A | run folder: "), s)
        self.assertTrue(s[2].startswith("  y/same: exit 0, done: 1. A | run folder: "), s)

    # covers: AC-1, AC-6 (a repo whose plan shows only a park has no work: no child, nothing to run in the summary,
    # and the parent code comes from the children alone)
    def test_parked_only(self):
        rp, rb = self.make_repo("rp", ONE), self.make_repo("rb", ONE)
        self.commit(rp)
        p = self.state / "wf" / "queue.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"version": 1, "parks": [park(rp, "1. A", self.section_sha(rp, "1. A"))],
                                 "decisions": []}))
        self.trust(rp, rb)
        self.steps({"rb": [TICK_A, DONE_A]})
        r = self.wf("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("  parked: 1. A: blocked: test park (retaken on a new commit)", plan(r.stdout))
        self.assertIn("jobs: 1 at once", plan(r.stdout))
        self.assertNotIn("[rp] ", r.stdout)
        self.assertFalse((self.fakes / "rp-argv-1.json").exists())
        s = summary(r.stdout)
        self.assertEqual(s[0], "  rp: nothing to run")
        self.assertTrue(s[1].startswith("  rb: exit 0, done: 1. A | run folder: "), s)


class TestSignals(ParallelCase):
    # covers: AC-5, AC-6 (SIGINT to the parent reaches both children as their Ctrl C; the parent exits 130)
    def test_sigint_reaches_both(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(a, b)
        long = {"tick": False, "sleep": 60}
        self.steps({"ra": [long], "rb": [long]})
        p = self.start("-y")
        self.wait_for(self.fakes / "ra-argv-1.json", timeout=20)
        self.wait_for(self.fakes / "rb-argv-1.json", timeout=20)
        p.send_signal(signal.SIGINT)
        out, err = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 130, out + err)
        self.assertEqual((self.fakes / "signals").read_text(), "INT\nINT\n")
        s = summary(out)
        self.assertTrue(all(x.split(": ", 1)[1].startswith("exit 130, stopped: interrupted") for x in s), s)
        self.assertEqual({n: rec["stop_reason"] for n, rec in self.run_records().items()},
                         {"ra": "interrupted", "rb": "interrupted"})

    # covers: AC-5, AC-6 (after a SIGTERM no child starts, even when a slot frees while another child still runs:
    # with --jobs 2, ra ends at once, rb finishes its call first, and rc stays not started)
    def test_not_started(self):
        a, b, c = self.make_repo("ra", ONE), self.make_repo("rb", ONE), self.make_repo("rc", ONE)
        self.trust(a, b, c)
        self.steps({"ra": [{"tick": False, "sleep": 60}], "rb": [{"tick": False, "sleep": 4, "ignore_int": True}],
                    "rc": [TICK_A, DONE_A]})
        p = self.start("-y", "--jobs", "2")
        self.wait_for(self.fakes / "ra-argv-1.json", timeout=20)
        self.wait_for(self.fakes / "rb-argv-1.json", timeout=20)
        p.send_signal(signal.SIGTERM)
        out, err = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 130, out + err)
        self.assertEqual(summary(out)[2], "  rc: not started")
        self.assertFalse((self.fakes / "rc-argv-1.json").exists())


class TestPlanBaseline(ParallelCase):
    """Spec 0025: a child started later checks its guard against the plan's, not its own start."""

    def setUp(self):
        super().setUp()
        self.a, self.b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(self.a, self.b)
        # A hook script every repo's guard hashes, from ~/.claude/settings.json; ra's calls may write its folder
        # (spec 0021 AC-7), so only rb sees the change, and only through the plan's baseline.
        hooks = self.tmp / "hooks"
        hooks.mkdir()
        self.hook = hooks / "h.sh"
        self.hook.write_text("#!/bin/sh\n")
        (self.tmp / ".claude").mkdir()
        (self.tmp / ".claude" / "settings.json").write_text(json.dumps({"hooks": {"PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": str(self.hook)}]}]}}))
        (self.tmp / "config" / "wf" / "allow.json").write_text(json.dumps({str(self.a): [str(hooks)]}))

    def baselines(self):
        d = self.state / "wf" / "baselines"
        return sorted(d.iterdir()) if d.exists() else []

    def change(self, *more):
        return {"ra": [{**TICK_A, "write_file": [[str(self.hook), "#!/bin/sh\necho changed\n"], *more]}, DONE_A],
                "rb": [TICK_A, DONE_A]}

    def asked(self, r, detail):
        self.assertIn(f"\n[rb] stopped repo rb: guard_changed: {detail}\n", r.stdout)

    # covers: AC-2, AC-3, AC-4 (ra's call changes a hook both guards hash: rb asks naming it before any call;
    # accept builds rb), AC-1 (the baseline files are gone after a normal end)
    def test_change_asks_then_accept(self):
        self.steps(self.change())
        self.reply("{id} 1")
        r = self.wf("-y", "--jobs", "1", "--max-wait", "0.01")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.asked(r, f"{self.hook} changed after the plan, before this repo started")
        self.assertRegex(r.stdout, r"\n\[rb\] answered: [a-z0-9]{4} rb: accept the new setup and go on\n")
        self.assertIn("\n[rb] done: 1. A\n", r.stdout)
        recs = self.run_records()
        self.assertEqual([e["outcome"] for e in recs["rb"]["features"]], ["feature_done"])
        self.assertEqual(self.queue()["decisions"], [])
        self.assertEqual(self.baselines(), [])

    # covers: AC-3 (no call in rb while it asks), AC-4 (stop this repo ends rb; ra's result is untouched and the
    # summary lists both)
    def test_stop_this_repo(self):
        self.steps(self.change())
        self.reply("{id} 2")
        r = self.wf("-y", "--jobs", "1", "--max-wait", "0.01")
        self.asked(r, f"{self.hook} changed after the plan, before this repo started")
        self.assertRegex(r.stdout, r"\n\[rb\] answered: [a-z0-9]{4} rb: stop this repo\n")
        self.assertFalse((self.fakes / "rb-argv-1.json").exists())
        recs = self.run_records()
        self.assertEqual(([e["outcome"] for e in recs["ra"]["features"]], recs["rb"]["features"]), (["feature_done"], []))
        self.assertEqual(recs["rb"]["repos"][0]["ended"], "guard_changed")
        s = summary(r.stdout)
        self.assertTrue(s[0].startswith("  ra: exit 0, done: 1. A | run folder: "), s)
        self.assertTrue(s[1].startswith("  rb: exit "), s)
        self.assertEqual(len(s), 2)

    # covers: AC-2, AC-5 (the same change as a swap wf wrote to swaps.jsonl asks nothing and prints nothing more)
    def test_swap_asks_nothing(self):
        new = "#!/bin/sh\necho changed\n"
        line = json.dumps({"stamp": "20261013-000000", "files": {str(self.hook): hashlib.sha256(new.encode()).hexdigest()}})
        self.steps(self.change([str(self.state / "wf" / "swaps.jsonl"), line + "\n"]))
        r = self.wf("-y", "--jobs", "1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("guard_changed", r.stdout)
        self.assertIn("\n[rb] done: 1. A\n", r.stdout)
        self.assertIsNone(self.queue())

    # covers: AC-2 (standing answers changed between the plan and rb's start ask)
    def test_answers_changed(self):
        self.steps({"ra": [{**TICK_A, "write_file": [[str(self.b / "AGENTS.md"), "## Standing answers\n- run suite: yes\n"]]},
                           DONE_A], "rb": [TICK_A, DONE_A]})
        r = self.wf("-y", "--jobs", "1")
        self.asked(r, "standing answers changed after the plan")
        self.assertFalse((self.fakes / "rb-argv-1.json").exists())

    # covers: AC-1 (wf run <repo> without the flag behaves as before: no plan check, no question), AC-2 (a missing
    # baseline file is one change)
    def test_no_flag_and_missing(self):
        self.hook.write_text("#!/bin/sh\necho changed before\n")
        self.steps({"rb": [TICK_A, DONE_A]})
        r = self.wf("rb", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("guard_changed", r.stdout)
        self.again()
        (self.fakes / "rb-count").unlink()
        (self.b / "docs/scope/scope.md").write_text(ONE)
        r = self.wf("rb", "-y", "--plan-guard", str(self.tmp / "gone.json"))
        self.assertIn(f"stopped repo rb: guard_changed: plan baseline unreadable: {self.tmp / 'gone.json'}\n", r.stdout)

    # covers: AC-1 (the file exists, 0600 in a 0700 folder, while a child runs; gone after SIGINT)
    def test_files_and_sigint(self):
        self.steps({"ra": [{"tick": False, "sleep": 60}], "rb": [TICK_A, DONE_A]})
        p = self.start("-y", "--jobs", "1")
        self.wait_for(self.fakes / "ra-argv-1.json", timeout=20)
        [f] = self.baselines()
        self.assertEqual((f.stat().st_mode & 0o777, f.parent.stat().st_mode & 0o777), (0o600, 0o700))
        self.assertEqual(f.name, f"{p.pid}-{hashlib.sha1(str(self.a).encode()).hexdigest()}.json")
        data = json.loads(f.read_text())
        self.assertEqual(sorted(data), ["absent_denied", "answers", "guarded_files"])
        self.assertIn(str(self.hook), data["guarded_files"])
        p.send_signal(signal.SIGINT)
        out, err = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 130, out + err)
        self.assertEqual(self.baselines(), [])

    def reply(self, *texts):
        self.report_ntfy.replies = list(texts)


if __name__ == "__main__":
    unittest.main()
