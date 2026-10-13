"""Spec 0019: `wf finish` runs the live setup steps waiting on you."""
import fcntl
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RUNNER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RUNNER))
import finish  # noqa: E402
import wf  # noqa: E402

WF = RUNNER / "wf.py"
SCOPE = """# Scope: r

**Autopilot:** allowed

### 1. One · in-progress · auto
- [ ] Copy: `cp rules/a.md ~/.claude/rules/a.md` · waits on you · live
- [ ] Install: `./install.sh` · waits on you · live
- [ ] Probe: `python3 docs/specs/0001-x/probes/p.py` · waits on you · live
- [ ] Phone check · waits on you
Spec [0001](../specs/0001-x/index.md)

### 2. Two · auto
- [ ] Install again: `./install.sh` · live · waits on you
- [ ] Probe b: `python3 docs/specs/0002-y/probes/q.py` · waits on you · live
- [ ] Bad: `rm -rf x` · waits on you · live
- [ ] Half: `./install.sh` then check `!` · waits on you · live
- [ ] No tag: `./install.sh` · live
Spec [0002](../specs/0002-y/index.md)

### 3. Old · done
- [ ] Copy old: `cp rules/a.md ~/.claude/rules/a.md` · waits on you · live

## Deferred

### 4. Later
- [ ] Copy later: `cp rules/a.md ~/.claude/rules/a.md` · waits on you · live
"""
INSTALL = """#!/bin/sh
echo installing >> "$CLAUDE_LIVE_DIR/install.count"
echo "install done"
"""
PROBE = """import os, sys
here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, "ran"), "a").write("x")
code = int(open(os.path.join(here, "code")).read()) if os.path.exists(os.path.join(here, "code")) else 0
print("first line")
print("  boom: \\x1b[31mred\\x1b[0m  ")
print("")
sys.exit(code)
"""


class FinishCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        self.live = self.home / ".claude"
        (self.live / "rules").mkdir(parents=True)
        (self.live / "agents").mkdir()
        (self.live / "agents" / "link.md").symlink_to("/nowhere")
        (self.live / "settings.json").write_text('{"autoMode": {}}')
        (self.live / "rules" / "a.md").write_text("old\n")
        self.state = self.tmp / "state"
        (self.tmp / "config" / "wf").mkdir(parents=True)
        bin_ = self.tmp / "bin"
        bin_.mkdir()
        claude = bin_ / "claude"
        claude.write_text("#!/bin/sh\necho '2.1.296 (Claude Code)'\n")
        claude.chmod(0o755)
        self.env = {**os.environ, "HOME": str(self.home), "CLAUDE_LIVE_DIR": str(self.live),
                    "XDG_STATE_HOME": str(self.state), "XDG_CONFIG_HOME": str(self.tmp / "config"),
                    "PATH": f"{bin_}:{os.environ['PATH']}", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": "/dev/null"}
        self.env.pop("WF_RUN", None)
        self.repo = self.make_repo("r")
        self.trust(self.repo)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def git(self, repo, *args):
        return subprocess.run(["git", "-C", str(repo), *args], env=self.env, capture_output=True, text=True, check=True)

    def make_repo(self, name, scope=SCOPE, branch="feat"):
        repo = self.tmp / name
        (repo / "docs" / "scope").mkdir(parents=True)
        (repo / "docs" / "scope" / "scope.md").write_text(scope)
        (repo / "rules").mkdir()
        (repo / "rules" / "a.md").write_text("new\n")
        (repo / "install.sh").write_text(INSTALL)
        (repo / "install.sh").chmod(0o755)
        for spec, probe in (("0001-x", "p.py"), ("0002-y", "q.py")):
            d = repo / "docs" / "specs" / spec
            (d / "probes").mkdir(parents=True)
            (d / "index.md").write_text("# spec\n")
            (d / "probes" / probe).write_text(PROBE)
        (repo / "docs" / "specs" / "0001-x" / "verify.md").write_text("# Verify\n\nold notes\n")
        subprocess.run(["git", "init", "-q", "-b", branch, str(repo)], env=self.env, check=True)
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-qm", "init")
        return repo

    def trust(self, *paths):
        (self.tmp / "config" / "wf" / "allowed.json").write_text(json.dumps([str(p) for p in paths]))

    def wf(self, *args, stdin=subprocess.DEVNULL, env=None):
        return subprocess.run([sys.executable, "-B", str(WF), "finish", *args], env=env or self.env,
                              stdin=stdin, capture_output=True, text=True, timeout=120)

    def verify(self, spec):
        return (self.repo / "docs" / "specs" / spec / "verify.md").read_text()

    def scope(self):
        return (self.repo / "docs" / "scope" / "scope.md").read_text()

    def probe_dir(self, spec):
        return self.repo / "docs" / "specs" / spec / "probes"


class TestHappyPath(FinishCase):
    # covers: AC-3 to AC-8 (plan, phases, once per repo install, backups, verify.md lines, ticks, one commit)
    def test_all_steps(self):
        (self.repo / "docs" / "notes.md").write_text("unrelated, uncommitted\n")
        r = self.wf("-y")
        out = r.stdout
        self.assertEqual(r.returncode, 0, out + r.stderr)
        self.assertIn("copy: r: 1. One: cp rules/a.md ~/.claude/rules/a.md", out)
        self.assertIn("install: r: 1. One, 2. Two: ./install.sh", out)
        self.assertIn("check: r: 1. One: python3 docs/specs/0001-x/probes/p.py", out)
        self.assertIn("yours: r: 2. Two: Bad: `rm -rf x` · waits on you · live (not a live step: rm -rf x)", out)
        self.assertIn("(not a live step: !)", out)
        self.assertIn("No tag: `./install.sh` · live (live needs waits on you)", out)
        self.assertNotIn("Copy old", out)
        self.assertNotIn("Copy later", out)
        self.assertNotIn("Phone check", out)
        # phases in order, copy before install before checks
        self.assertLess(out.index("copy: r: cp"), out.index("install: r: ./install.sh"))
        self.assertLess(out.index("install: r: ./install.sh"), out.index("check: r: python3"))
        self.assertEqual((self.live / "rules" / "a.md").read_text(), "new\n")
        self.assertEqual((self.live / "install.count").read_text(), "installing\n")
        self.assertIn("install done", out)
        folder = Path(next(l for l in out.splitlines() if l.startswith("backups and logs: "))[18:])
        self.assertEqual((folder / "claude" / "rules" / "a.md").read_text(), "old\n")
        self.assertTrue((folder / "claude" / "agents" / "link.md").is_symlink())
        self.assertEqual((folder / "claude" / "settings.json").read_text(), '{"autoMode": {}}')
        self.assertIn("boom", (folder / "step-02.log").read_text())
        v1 = self.verify("0001-x")
        self.assertTrue(v1.startswith("# Verify\n\nold notes\n\n## Live runs (wf finish)\n\n"), v1)
        self.assertRegex(v1, r"- \d{4}-\d\d-\d\d, Claude Code 2\.1\.296: `python3 docs/specs/0001-x/probes/p\.py` PASS\n$")
        self.assertIn("## Live runs (wf finish)\n\n- ", self.verify("0002-y"))
        scope = self.scope()
        for t in ("Copy:", "Install:", "Probe:", "Install again:", "Probe b:"):
            self.assertIn(f"- [x] {t}", scope)
        for t in ("Bad:", "Half:", "No tag:", "Phone check", "Copy old:", "Copy later:"):
            self.assertIn(f"- [ ] {t}", scope)
        log = self.git(self.repo, "log", "-1", "--format=%s", "--name-only").stdout.split()
        self.assertEqual(log[:5], ["chore(wf):", "wf", "finish", "ran", "4"])
        self.assertEqual(sorted(log[7:]), ["docs/scope/scope.md", "docs/specs/0001-x/verify.md",
                                           "docs/specs/0002-y/verify.md"])
        self.assertIn("notes.md", self.git(self.repo, "status", "--porcelain").stdout)
        self.assertEqual(out.splitlines()[-1], "next: wf run")
        self.assertIn("PASS: r: ./install.sh", out)
        self.assertTrue((self.state / "wf" / "report.seen").exists())

    # covers: AC-5 (a second run appends under the existing heading, before a later heading)
    def test_heading_in_middle(self):
        (self.repo / "docs" / "specs" / "0001-x" / "verify.md").write_text(
            "# V\n\n## Live runs (wf finish)\n\n- old line\n\n## Later\n\ntext\n")
        self.assertEqual(self.wf("-y").returncode, 0)
        v = self.verify("0001-x")
        self.assertRegex(v, r"- old line\n- \S+, Claude Code 2\.1\.296: `python3 docs/specs/0001-x/probes/p\.py` PASS\n\n## Later\n")


class TestFailures(FinishCase):
    # covers: AC-4, AC-8 (a failed copy stops before the installs and checks)
    def test_failed_copy(self):
        shutil.rmtree(self.live / "rules")
        (self.live / "rules").write_text("a file where a folder goes")
        r = self.wf("-y")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertFalse((self.live / "install.count").exists())
        self.assertFalse((self.probe_dir("0001-x") / "ran").exists())
        self.assertIn("FAIL: r: cp rules/a.md ~/.claude/rules/a.md", r.stdout)
        self.assertIn("FAIL: r: ./install.sh (not run)", r.stdout)
        self.assertNotIn("- [x]", self.scope())
        self.assertEqual(r.stdout.splitlines()[-1], "next: fix the FAIL lines, then wf finish")

    # covers: AC-4, AC-5, AC-6 (a failed probe is recorded, the next probe still runs, its box stays open)
    def test_failed_probe(self):
        (self.probe_dir("0001-x") / "code").write_text("3")
        r = self.wf("-y")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertRegex(self.verify("0001-x"), r"`python3 docs/specs/0001-x/probes/p\.py` FAIL \(exit 3\): boom: \[31mred\[0m\n")
        self.assertRegex(self.verify("0002-y"), r"q\.py` PASS\n")
        self.assertIn("- [ ] Probe: ", self.scope())
        self.assertIn("- [x] Probe b: ", self.scope())
        self.assertIn("- [x] Install: ", self.scope())

    # covers: AC-6 (a box edited between the plan and the tick is not ticked)
    def test_box_changed(self):
        scope = self.repo / "docs" / "scope" / "scope.md"
        (self.repo / "install.sh").write_text(INSTALL + f"sed -i 's/^- \\[ \\] Probe b:/- [ ] Probe B:/' {scope}\n")
        r = self.wf("-y")
        self.assertIn("box changed, not ticked: Probe b:", r.stdout)
        self.assertIn("- [ ] Probe B:", self.scope())
        self.assertIn("- [x] Probe:", self.scope())

    # covers: AC-4, AC-8 (Ctrl C stops the running step's group, runs nothing further, keeps what passed)
    def test_ctrl_c(self):
        (self.probe_dir("0001-x") / "p.py").write_text(
            "import os, time\nopen(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ran'), 'w')\n"
            "time.sleep(60)\n")
        p = subprocess.Popen([sys.executable, "-B", str(WF), "finish", "-y"], env=self.env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        marker = self.probe_dir("0001-x") / "ran"
        for _ in range(200):
            if marker.exists():
                break
            time.sleep(0.1)
        p.send_signal(signal.SIGINT)
        out = p.communicate(timeout=60)[0]
        self.assertEqual(p.returncode, 130, out)
        self.assertFalse((self.probe_dir("0002-y") / "ran").exists())
        self.assertIn("- [x] Copy:", self.scope())
        self.assertIn("- [ ] Probe:", self.scope())
        self.assertNotIn("p.py", self.verify("0001-x").split("old notes")[1])
        self.assertFalse((self.state / "wf" / "report.seen").exists())


class TestRefusals(FinishCase):
    # covers: AC-3 (WF_RUN, no terminal, untrusted, held lock)
    def test_unattended(self):
        r = self.wf("-y", env={**self.env, "WF_RUN": "x"})
        self.assertEqual((r.returncode, r.stdout.split(":")[0:2]), (5, ["refused", " unattended"]))

    def test_no_tty(self):
        r = self.wf()
        self.assertEqual(r.returncode, 5)
        self.assertTrue(r.stdout.startswith("refused: no_tty: "), r.stdout)

    # covers: AC-3 (at a terminal: anything but an empty line cancels, an empty line runs)
    def test_confirm(self):
        import pty
        for answer, code in ((b"no\n", 130), (b"\n", 0)):
            master, slave = pty.openpty()
            try:
                os.write(master, answer)
                r = self.wf(stdin=slave)
            finally:
                os.close(master)
                os.close(slave)
            self.assertEqual(r.returncode, code, r.stdout)
            self.assertEqual((self.live / "install.count").exists(), code == 0)

    def test_untrusted(self):
        self.trust()
        r = self.wf(str(self.repo), "-y")
        self.assertEqual(r.returncode, 5)
        self.assertTrue(r.stdout.startswith("refused: untrusted: "), r.stdout)
        self.assertFalse((self.live / "install.count").exists())

    def test_locked(self):
        locks = self.state / "wf" / "locks"
        locks.mkdir(parents=True)
        fd = os.open(locks / (hashlib.sha1(b"/elsewhere").hexdigest() + ".lock"), os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            os.write(fd, b"4242 2026-10-13T00:00:00\n")
            r = self.wf("-y")
        finally:
            os.close(fd)
        self.assertEqual(r.returncode, 5)
        self.assertEqual(r.stdout.strip(), "refused: locked: a wf run is going: 4242 2026-10-13T00:00:00")
        self.assertEqual((self.live / "rules" / "a.md").read_text(), "old\n")

    # covers: AC-3 (a missing trusted repo is skipped), AC-7 (main leaves the edits uncommitted)
    def test_missing_and_main(self):
        main = self.make_repo("m", branch="main")
        self.trust(self.tmp / "gone", main)
        r = self.wf("-y")
        self.assertIn(f"skipped: {self.tmp / 'gone'}: no folder or no scope", r.stdout)
        self.assertIn("edits left uncommitted on main", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(self.git(main, "log", "--format=%s").stdout.strip(), "init")
        self.assertIn("- [x] Copy:", (main / "docs" / "scope" / "scope.md").read_text())

    # covers: AC-3 (no live step: says so, report.seen, exit 0)
    def test_no_live_steps(self):
        (self.repo / "docs" / "scope" / "scope.md").write_text("# Scope: r\n\n### 1. A\n- [ ] Phone · waits on you\n")
        r = self.wf("-y")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "no live steps"))
        self.assertTrue((self.state / "wf" / "report.seen").exists())


class TestShapes(FinishCase):
    # covers: AC-2 (only the four shapes run)
    def test_shapes(self):
        root = str(self.repo.resolve())
        (self.repo / "settings.json").write_text("{}")
        (self.repo / "private").mkdir()
        (self.repo / "private" / "n.txt").write_text("x")
        (self.repo / "link.md").symlink_to(self.repo / "rules" / "a.md")
        (self.repo / "runner" / "e2e").mkdir(parents=True)
        (self.repo / "runner" / "e2e" / "run.py").write_text("")
        good = {"cp rules/a.md ~/.claude/rules/a.md": "copy", "./install.sh": "install",
                "python3 runner/e2e/run.py": "check", "python3 runner/e2e/run.py --parallel": "check",
                "python3 docs/specs/0001-x/probes/p.py": "check"}
        bad = ["rm -rf x", "cp -f rules/a.md ~/.claude/rules/a.md", "cp rules/a.md ~/.claude/rules/b.md",
               "cp rules/a.md ~/.claude/a.md", "cp settings.json ~/.claude/settings.json",
               "cp private/n.txt ~/.claude/private/n.txt", "cp link.md ~/.claude/link.md",
               "cp ../x ~/.claude/x", "python3 docs/specs/0001-x/probes/p.py --fast",
               "bash docs/specs/0001-x/probes/p.py", "python3 docs/specs/0001-x/probes/missing.py",
               "python3 runner/e2e/run.py --other", "install.sh", "./install.sh -y", "bash ./install.sh", "!",
               "cp 'unclosed"]
        env = os.environ.copy()
        os.environ.update(CLAUDE_LIVE_DIR=str(self.live), HOME=str(self.home))
        try:
            for span, phase in good.items():
                self.assertEqual((finish.shape(root, span) or [None])[0], phase, span)
            for span in bad:
                self.assertIsNone(finish.shape(root, span), span)
            self.assertEqual(finish.not_live(root, []), "no command in backticks")
            self.assertEqual(finish.not_live(root, ["./install.sh", "!"]), "not a live step: !")
            self.assertEqual(finish.not_live(root, ["./install.sh", "./install.sh"]), "not a live step: ./install.sh")
            self.assertIsNone(finish.not_live(root, ["./install.sh"]))
        finally:
            os.environ.clear()
            os.environ.update(env)

    # covers: AC-1 (wf run treats a live box as any waiting box)
    def test_wf_run_waits(self):
        nb = wf.pick_next(wf.parse_text(SCOPE))
        self.assertEqual(nb.owed, "Copy: `cp rules/a.md ~/.claude/rules/a.md` · live")
        self.assertTrue(wf.LIVE.search("x · live · waits on you"))
        self.assertFalse(wf.LIVE.search("x · lively"))


if __name__ == "__main__":
    unittest.main()
