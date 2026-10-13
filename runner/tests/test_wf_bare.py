"""Spec 0020 AC-1, AC-2, AC-6 to AC-8, AC-13: bare `wf`, the one command."""
import fcntl
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import finish  # noqa: E402
import run  # noqa: E402
from test_park import GIT_ID  # noqa: E402
from test_parallel import ParallelCase  # noqa: E402
from test_queue import DONE_A, ONE, TICK_A, park  # noqa: E402
from test_run import WF  # noqa: E402

LIVE = ONE + """
### 2. Setup
- [ ] Probe: `python3 docs/specs/0001-x/probes/p.py` · waits on you · live
Spec [0001](../specs/0001-x/index.md)
"""
PROBE = "import os, sys\nprint('probe ran')\nsys.exit(int(os.environ.get('PROBE_CODE', '0')))\n"


class BareCase(ParallelCase):
    def setUp(self):
        super().setUp()
        self.live = self.tmp / ".claude"
        self.live.mkdir()
        (self.live / "settings.json").write_text("{}")
        self.env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

    def bare(self, *args, stdin=None, env=None):
        cmd = [sys.executable, str(WF), *args]
        if stdin is None:
            return subprocess.run(cmd, capture_output=True, text=True, env=env or self.env, timeout=120,
                                  stdin=subprocess.DEVNULL)
        master, slave = os.openpty()
        p = subprocess.Popen(cmd, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             env=env or self.env)
        os.close(slave)
        os.write(master, stdin.encode())
        out, err = p.communicate(timeout=120)
        os.close(master)
        return subprocess.CompletedProcess(cmd, p.returncode, out, err)

    def committed(self, name, text):
        repo = self.make_repo(name, text)
        d = repo / "docs" / "specs" / "0001-x"
        (d / "probes").mkdir(parents=True)
        (d / "index.md").write_text("# spec\n")
        (d / "probes" / "p.py").write_text(PROBE)
        (repo / "src.py").write_text("x = 1\n")
        self.commit(repo)
        return repo

    def head(self, repo):
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    def write_queue(self, parks):
        p = self.state / "wf" / "queue.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"version": 1, "parks": parks, "decisions": []}))


class TestRefusals(BareCase):
    # covers: AC-1 (WF_RUN and no terminal without -y refuse with exit 5, nothing changed)
    def test_refusals(self):
        r = self.bare("-y", env={**self.env, "WF_RUN": "x"})
        self.assertEqual(r.returncode, 5)
        self.assertTrue(r.stdout.startswith("refused: unattended: "), r.stdout)
        r = self.bare()
        self.assertEqual(r.returncode, 5)
        self.assertTrue(r.stdout.startswith("refused: no_tty: "), r.stdout)
        self.assertFalse((self.state / "wf").exists())

    # covers: AC-2 (nothing due: the report, then nothing to do, report.seen, exit 0)
    def test_nothing_to_do(self):
        a = self.make_repo("ra", "# Scope: x\n**Autopilot:** allowed\n\n### 1. A · done\n- [x] `/develop a`\n")
        self.trust(a)
        (self.state / "wf").mkdir(parents=True)
        (self.state / "wf" / "report.txt").write_text("wf done 09:00: 1 built\nnext: wf\n")
        r = self.bare("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout, "report:\n  wf done 09:00: 1 built\n  next: wf\nnothing to do\n")
        self.assertTrue((self.state / "wf" / "report.seen").exists())
        r = self.bare("-y")
        self.assertEqual(r.stdout, "nothing to do\n")


class TestScreen(BareCase):
    # covers: AC-2, AC-13 (the sections in order, every queued feature numbered; --only 2 builds rb alone, ra stays
    # queued; a held repo is a running line, exit 0)
    def test_order_and_only(self):
        a, b, c = self.make_repo("ra", ONE), self.make_repo("rb", ONE), self.make_repo("rc", ONE)
        self.trust(a, b, c)
        (self.state / "wf" / "locks").mkdir(parents=True)
        (self.state / "wf" / "report.txt").write_text("wf done 09:00\n")
        fd, _ = run.lock_file(str(self.state / "wf" / "locks" / (run.hashlib.sha1(str(c).encode()).hexdigest() + ".lock")),
                              what="wf run rc")
        self.addCleanup(os.close, fd)
        self.steps({"rb": [TICK_A, DONE_A]})
        r = self.bare("--only", "2", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = r.stdout
        heads = [x for x in out.splitlines() if x and not x.startswith(" ")]
        self.assertEqual(heads[:3], ["report:", "build:", "running:"])
        self.assertIn("  1. ra: 1. A\n  2. rb: 1. A\n", out)
        self.assertIn(f"running:\n  rc: {os.getpid()} ", out)
        self.assertNotIn("[ra]", out)
        self.assertIn("[rb] done: 1. A", out)
        self.assertIn("### 1. A · auto", (a / "docs" / "scope" / "scope.md").read_text())
        self.assertEqual(sorted(self.run_records()), ["rb"])

    # covers: AC-13 (at a terminal: a number off the list or other text cancels with nothing changed; a pick builds
    # only that feature)
    def test_prompt(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(a, b)
        for answer in ("3\n", "y\n", "1-x\n"):
            r = self.bare(stdin=answer)
            self.assertEqual(r.returncode, 130, r.stdout + r.stderr)
            self.assertIn("Enter for all, numbers to pick (1 2 4 or 1-3,5), anything else cancels: ", r.stdout)
            self.assertFalse((self.state / "wf" / "report.seen").exists())
            self.assertFalse((self.state / "wf" / "runs").exists())
        self.steps({"ra": [TICK_A, DONE_A]})
        r = self.bare(stdin="1\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sorted(self.run_records()), ["ra"])

    # covers: AC-13 (a pick inside one repo: its child builds only the picked feature, the other stays queued)
    def test_pick_in_repo(self):
        from test_queue import TWO
        a = self.make_repo("ra", TWO)
        self.trust(a)
        self.steps({"ra": [TICK_A, DONE_A, {"tick": True}]})
        r = self.bare("--only", "1", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("  1. ra: 1. A\n  2. ra: 2. B\n", r.stdout)
        self.assertEqual([e["feature"] for e in self.run_records()["ra"]["features"]], ["1. A"])
        self.assertIn("- [ ] `/develop b`", (a / "docs" / "scope" / "scope.md").read_text())

    # covers: AC-13 (number parsing)
    def test_picks(self):
        self.assertEqual(finish.picks("1 2 4", 5), [1, 2, 4])
        self.assertEqual(finish.picks("1-3,5", 5), [1, 2, 3, 5])
        for bad in ("6", "0", "3-1", "a", "", "1,,x"):
            self.assertIsNone(finish.picks(bad, 5), bad)


class TestRetakes(BareCase):
    # covers: AC-6 (a commit outside scope and verify.md retakes; one touching only them does not; no head: the
    # committer time; setup and claude signals; unknown never retakes; caps left to applies)
    def test_rules(self):
        repo = self.committed("rr", ONE)
        h0 = self.head(repo)
        base = park(repo, "1. A", head=h0, parked_at="2026-01-01T00:00:00+00:00")
        (repo / "docs" / "scope" / "scope.md").write_text(ONE + "\n")
        (repo / "docs" / "specs" / "0001-x" / "verify.md").write_text("v\n")
        self.commit(repo)
        with mock.patch.dict(os.environ, {"PATH": os.environ["PATH"]}):
            self.assertIsNone(run.what_changed(base, None, None))
            (repo / "src.py").write_text("x = 2\n")
            self.commit(repo)
            self.assertEqual(run.what_changed(base, None, None), "a new commit")
            old = {**base, "head": None}
            self.assertEqual(run.what_changed(old, None, None), "a new commit")
            self.assertIsNone(run.what_changed({**old, "parked_at": "2999-01-01T00:00:00+00:00"}, None, None))
        denied = {**base, "reason": "denied", "setup": "20261013-010000", "claude": "2.1.296"}
        self.assertEqual(run.what_changed(denied, "20261013-020000", "2.1.296"), "setup 20261013-020000")
        self.assertEqual(run.what_changed(denied, "20261013-010000", "2.1.300"), "claude 2.1.296 -> 2.1.300")
        self.assertIsNone(run.what_changed(denied, "20261013-010000", "2.1.296"))
        self.assertIsNone(run.what_changed({**denied, "setup": None, "claude": None}, "20261013-020000", "2.1.300"))
        self.assertIsNone(run.what_changed(denied, None, None))
        timeout = {**denied, "reason": "call_timeout", "cap": 60}
        self.assertIsNone(run.what_changed(timeout, "20261013-020000", "2.1.300"))
        self.assertEqual(run.retaken_on(timeout), "a higher --call-timeout")
        self.assertEqual(run.retaken_on({**timeout, "cap": None}), "a setup change or a new Claude Code version")
        self.assertEqual(run.retaken_on(base), "a new commit")
        # A record written before the new fields still loads; a bad one does not.
        q = {"version": 1, "parks": [park(repo, "1. A")], "decisions": []}
        self.assertIsNone(run.queue_problem(q))
        q["parks"][0]["head"] = 3
        self.assertEqual(run.queue_problem(q), "parks[0] has a bad head, setup or claude")

    # covers: AC-6, AC-2 (a park whose cause changed is taken back under queue.lock and built; one kept says what
    # would take it back)
    def test_screen_and_drop(self):
        repo = self.committed("rr", ONE + "\n### 2. B · auto\n- [x] (spec)\n- [ ] `/develop b`\n")
        self.trust(repo)
        h0 = self.head(repo)
        (repo / "src.py").write_text("x = 2\n")
        self.commit(repo)
        sha = lambda n: self.section_sha(repo, n)
        self.write_queue([park(repo, "1. A", sha("1. A"), head=h0),
                          park(repo, "2. B", sha("2. B"), head=self.head(repo))])
        self.steps({"rr": [TICK_A, DONE_A]})
        r = self.bare("-y", "--only", "1")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn("retake:\n  rr: 1. A: blocked (a new commit)\n", r.stdout)
        self.assertIn("parked:\n  rr: 2. B: blocked: retaken on a new commit\n", r.stdout)
        self.assertIn("  1. rr: 1. A\n", r.stdout)
        self.assertIn("[rr] done: 1. A", r.stdout)
        self.assertEqual([p["feature"] for p in self.queue()["parks"]], ["2. B"])


class TestSetupAndChecks(BareCase):
    # covers: AC-3, AC-8 (a held swap lock: setup and checks hold its one line and are skipped, builds still go)
    def test_held_swap_lock(self):
        repo = self.committed("rs", ONE + "\n### 2. Copy\n- [ ] Copy: `cp rules/a.md ~/.claude/rules/a.md` · waits on you · live\n")
        (repo / "rules").mkdir()
        (repo / "rules" / "a.md").write_text("new\n")
        self.commit(repo)
        self.trust(repo)
        (self.state / "wf").mkdir(parents=True, exist_ok=True)
        fd = os.open(self.state / "wf" / "swap.lock", os.O_RDWR | os.O_CREAT)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.write(fd, b"4242 2026-10-13T01:00:00+00:00 wf setup swap\n")
        self.steps({"rs": [TICK_A, DONE_A]})
        r = self.bare("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("setup:\n  setup update already in progress, pid 4242 since 2026-10-13T01:00:00+00:00\n", r.stdout)
        self.assertIn("[rs] done: 1. A", r.stdout)
        self.assertFalse((self.live / "rules" / "a.md").exists())

    # covers: AC-8 (checks run beside the build, prefixed [check], recorded, ticked, committed; the live dir is byte
    # equal before and after)
    def test_checks_beside(self):
        repo = self.committed("rc", LIVE)
        self.trust(repo)
        self.env["CLAUDE_CONFIG_DIR"] = str(self.live)
        before = {p: p.read_bytes() for p in self.live.rglob("*") if p.is_file()}
        self.steps({"rc": [TICK_A, DONE_A]})
        r = self.bare("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[check] probe ran", r.stdout)
        self.assertIn("[check] check: rc: python3 docs/specs/0001-x/probes/p.py", r.stdout)
        self.assertIn("[rc] done: 1. A", r.stdout)
        self.assertIn("`python3 docs/specs/0001-x/probes/p.py` PASS",
                      (repo / "docs" / "specs" / "0001-x" / "verify.md").read_text())
        self.assertIn("- [x] Probe:", (repo / "docs" / "scope" / "scope.md").read_text())
        log = subprocess.run(["git", "-C", str(repo), "log", "--format=%s"], capture_output=True, text=True).stdout
        self.assertIn("chore(wf):", log)
        self.assertEqual({p: p.read_bytes() for p in self.live.rglob("*") if p.is_file()}, before)

    # covers: AC-3, AC-8 (a failed install: live dir untouched, checks skipped, the build still starts, exit 1)
    def test_failed_install(self):
        repo = self.committed("ri", LIVE + "- [ ] Install: `./install.sh` · waits on you · live\n")
        (repo / "install.sh").write_text("#!/bin/sh\nexit 4\n")
        (repo / "install.sh").chmod(0o755)
        self.commit(repo)
        self.trust(repo)
        self.env["CLAUDE_CONFIG_DIR"] = str(self.live)
        self.steps({"ri": [TICK_A, DONE_A]})
        r = self.bare("-y")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("probe ran", r.stdout)
        self.assertIn("[ri] done: 1. A", r.stdout)
        self.assertRegex(r.stdout, r"FAIL: ri: \./install\.sh \(log \S+step-01\.log\)")
        self.assertIn("FAIL: ri: python3 docs/specs/0001-x/probes/p.py (not run)", r.stdout)


class TestSignals(BareCase):
    # covers: AC-8 (Ctrl C reaches the running check's group beside the builds; nothing is recorded for it)
    def test_ctrl_c_check(self):
        repo = self.committed("rc", LIVE)
        probe = repo / "docs" / "specs" / "0001-x" / "probes" / "p.py"
        probe.write_text(f"import time\nopen({str(self.fakes / 'probe-started')!r}, 'w').close()\ntime.sleep(60)\n")
        self.commit(repo)
        self.trust(repo)
        self.steps({"rc": [{**TICK_A, "sleep": 60}, DONE_A]})
        p = subprocess.Popen([sys.executable, str(WF), "-y"], env=self.env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.addCleanup(lambda: p.poll() is None and p.kill())
        self.wait_for(self.fakes / "probe-started", 30)
        self.wait_for(self.fakes / "rc-argv-1.json", 30)
        p.send_signal(subprocess.signal.SIGINT)
        out = p.communicate(timeout=90)[0]
        self.assertEqual(p.returncode, 130, out)
        self.assertNotIn("p.py` ", (repo / "docs" / "specs" / "0001-x" / "verify.md").read_text()
                         if (repo / "docs" / "specs" / "0001-x" / "verify.md").exists() else "")
        self.assertIn("- [ ] Probe:", (repo / "docs" / "scope" / "scope.md").read_text())


class TestCommitRetry(BareCase):
    # covers: AC-8 (a held index.lock is retried 3 times, 2 s apart, then the uncommitted line)
    def test_index_lock(self):
        repo = self.committed("rl", ONE)
        (repo / "x.md").write_text("x\n")
        (repo / ".git" / "index.lock").write_text("")
        c = mock.Mock(path=str(repo))
        c.name = "rl"
        out = io.StringIO()
        with mock.patch("time.sleep") as sleep, redirect_stdout(out), \
                mock.patch.dict(os.environ, {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}):
            self.assertFalse(finish.commit(c, [str(repo / "x.md")], 1))
        self.assertEqual([x.args for x in sleep.call_args_list], [(2,)] * 3)
        self.assertTrue(out.getvalue().startswith("edits left uncommitted in rl: "), out.getvalue())


if __name__ == "__main__":
    unittest.main()
