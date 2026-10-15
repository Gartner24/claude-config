"""Spec 0020 AC-3, AC-4: staged setup, the ordered swap with its journal and ledger, crash finish, swap lock."""
import fcntl
import hashlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

RUNNER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RUNNER))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import finish  # noqa: E402
import run  # noqa: E402
import wf  # noqa: E402
from test_finish import FinishCase  # noqa: E402

STAMP = "20261013-020304"


def sha(b):
    return hashlib.sha256(b).hexdigest()


class TestStagedFinish(FinishCase):
    # covers: AC-3 (stage built, install into it with WF_STAGE), AC-4 (ledger, journal done, stage deleted, no asides)
    def test_ledger_and_journal(self):
        (self.repo / "install.sh").write_text('#!/bin/sh\necho "$WF_STAGE" > "$CLAUDE_LIVE_DIR/install.count"\n')
        r = self.wf("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        live = self.live.resolve()
        self.assertEqual((self.live / "install.count").read_text(), "1\n")
        lines = [json.loads(l) for l in (self.state / "wf" / "swaps.jsonl").read_text().splitlines()]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["files"], {f"{live}/rules/a.md": sha(b"new\n"), f"{live}/install.count": sha(b"1\n")})
        self.assertEqual(oct(os.stat(self.state / "wf" / "swaps.jsonl").st_mode & 0o777), "0o600")
        folder = self.state / "wf" / "finish" / lines[0]["stamp"]
        journal = json.loads((folder / "swap.json").read_text())
        self.assertTrue(journal["done"])
        self.assertFalse((folder / "stage").exists())
        self.assertEqual((folder / "claude" / "rules" / "a.md").read_text(), "old\n")
        self.assertEqual([p for p in self.live.rglob("*") if ".wf-swap-" in p.name], [])

    # covers: AC-3 (a failed install: live dir untouched, stage kept, checks skipped, the failed step and its log named)
    def test_failed_install(self):
        (self.repo / "install.sh").write_text('#!/bin/sh\necho x > "$CLAUDE_LIVE_DIR/install.count"\nexit 3\n')
        r = self.wf("-y")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertFalse((self.live / "install.count").exists())
        self.assertEqual((self.live / "rules" / "a.md").read_text(), "old\n")
        self.assertFalse((self.probe_dir("0001-x") / "ran").exists())
        self.assertFalse((self.state / "wf" / "swaps.jsonl").exists())
        stage = next((self.state / "wf" / "finish").glob("*/stage"))
        self.assertEqual((stage / "install.count").read_text(), "x\n")
        self.assertRegex(r.stdout, r"FAIL: r: \./install\.sh \(log \S+/step-01\.log\)")
        self.assertNotIn("- [x]", self.scope())

    # covers: AC-3, AC-9 (a held swap lock skips setup and checks with the one line; two finishes never overlap)
    def test_swap_lock_held(self):
        (self.state / "wf").mkdir(parents=True)
        fd = os.open(self.state / "wf" / "swap.lock", os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            os.write(fd, b"4242 2026-10-13T01:00:00+00:00 wf setup swap\n")
            r = self.wf("-y")
        finally:
            os.close(fd)
        self.assertIn("setup update already in progress, pid 4242 since 2026-10-13T01:00:00+00:00", r.stdout)
        self.assertEqual((self.live / "rules" / "a.md").read_text(), "old\n")
        self.assertFalse((self.probe_dir("0001-x") / "ran").exists())

    # covers: AC-3 (at most the 3 newest stage folders are kept)
    def test_stage_prune(self):
        for n in range(5):
            (self.state / "wf" / "finish" / f"2026010{n}-000000" / "stage").mkdir(parents=True)
        self.assertEqual(self.wf("-y").returncode, 0)
        kept = sorted(p.parent.name for p in (self.state / "wf" / "finish").glob("*/stage"))
        self.assertEqual(kept, ["20260102-000000", "20260103-000000", "20260104-000000"])


class TestShapeConfigDir(FinishCase):
    # covers: AC-3 (a copy box's `~/.claude/` names the live dir, $CLAUDE_CONFIG_DIR when set)
    def test_copy_into_config_dir(self):
        conf = self.tmp / "conf"
        conf.mkdir()
        with mock.patch.dict(os.environ, {"HOME": str(self.home), "CLAUDE_CONFIG_DIR": str(conf)}):
            phase, fields = finish.shape(str(self.repo.resolve()), "cp rules/a.md ~/.claude/rules/a.md")
        self.assertEqual((phase, fields["dst"]), ("copy", str(conf.resolve() / "rules" / "a.md")))


class SwapUnit(unittest.TestCase):
    """swap() and recover() in process, on a temp home, live dir, state and repo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.home = self.tmp / "home"
        self.live = self.home / ".claude"
        (self.live / "rules").mkdir(parents=True)
        (self.live / "rules" / "a.md").write_text("old\n")
        (self.live / "settings.json").write_text("{}")
        self.state = self.tmp / "state"
        env = {"HOME": str(self.home), "XDG_STATE_HOME": str(self.state), "CLAUDE_CONFIG_DIR": str(self.live)}
        p = mock.patch.dict(os.environ, env)
        p.start()
        self.addCleanup(p.stop)
        self.repo = self.tmp / "repo"
        (self.repo / "runner").mkdir(parents=True)
        (self.repo / "runner" / "wf.py").write_text("print('wf')\n")
        (self.repo / "runner" / "run.py").write_text("x = 1\n")
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts" / "private-names.py").write_text("#!/usr/bin/env python3\n# checker v2\n")
        (self.repo / "scripts" / "spec-paths.py").write_text("print()\n")
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True, stdin=subprocess.DEVNULL)
        self.hooks = self.repo / ".git" / "hooks"
        self.hooks.mkdir(exist_ok=True)
        for h in self.hooks.iterdir():
            h.unlink()
        self.folder = self.state / "wf" / "finish" / STAMP
        self.stage = self.folder / "stage"
        self.stage.mkdir(parents=True)
        (self.stage / "rules").mkdir()
        (self.stage / "rules" / "a.md").write_text("new\n")
        (self.stage / "rules" / "same.md").write_text("same\n")
        (self.live / "rules" / "same.md").write_text("same\n")
        (self.stage / "settings.json").write_text('{"a": 1}')
        (self.stage / "settings.local.json").write_text("{}")
        (self.stage / "private").mkdir()
        (self.stage / "private" / "names.txt").write_text("x\n")
        self.c = mock.Mock(path=str(self.repo))

    def swap(self):
        done = []
        real = os.replace

        def replace(a, b):
            blocked = signal.pthread_sigmask(signal.SIG_BLOCK, [])
            done.append((b, signal.SIGINT in blocked and signal.SIGTERM in blocked and signal.SIGHUP in blocked))
            real(a, b)

        with mock.patch("os.replace", replace), redirect_stdout(io.StringIO()):
            finish.swap(str(self.folder), STAMP, str(self.stage), [self.c])
        return done

    # covers: AC-4 (changed set, rename order with settings.json last, signals blocked, ledger names hooks, runner
    # copy files and links by content, mtime and prune, nothing deleted)
    def test_order_and_ledger(self):
        (self.live / "rules" / "only-live.md").write_text("keep\n")
        done = self.swap()
        fp = finish.runner_fp(str(self.repo / "runner"))
        share, bin_ = self.home / ".local" / "share" / "wf", self.home / ".local" / "bin"
        live = str(self.live)
        self.assertEqual([d for d, _ in done], [
            str(share / fp), str(bin_ / "wf"), str(bin_ / "next"), str(bin_ / "spec-paths"),
            str(self.hooks / "pre-commit"), str(self.hooks / "commit-msg"), f"{live}/private/names.txt",
            f"{live}/rules/a.md", f"{live}/settings.local.json", f"{live}/settings.json"])
        self.assertTrue(all(b for _, b in done))
        self.assertEqual(signal.SIGINT in signal.pthread_sigmask(signal.SIG_BLOCK, []), False)
        self.assertEqual((self.live / "rules" / "a.md").read_text(), "new\n")
        self.assertEqual((self.live / "rules" / "only-live.md").read_text(), "keep\n")
        self.assertEqual(os.path.realpath(bin_ / "wf"), str(share / fp / "wf.py"))
        self.assertEqual(oct((self.hooks / "pre-commit").stat().st_mode & 0o777), "0o755")
        self.assertFalse((self.hooks / "pre-commit").is_symlink())
        files = run.ledger()[0][1]
        wf_sha = sha(b"print('wf')\n")
        self.assertEqual(files[str(bin_ / "wf")], wf_sha)
        self.assertEqual(files[str(share / fp / "wf.py")], wf_sha)
        self.assertEqual(files[str(share / fp / "run.py")], sha(b"x = 1\n"))
        self.assertEqual(files[str(self.hooks / "commit-msg")], sha((self.repo / "scripts" / "private-names.py").read_bytes()))
        self.assertNotIn(f"{live}/rules/same.md", files)
        self.assertTrue(json.loads((self.folder / "swap.json").read_text())["done"])
        # AC-5: a run holding the repo accepts the new hook copies.
        self.assertEqual(run.accepted_by(str(self.hooks / "pre-commit"), run.ledger()), STAMP)
        self.assertEqual((self.folder / "claude" / "rules" / "a.md").read_text(), "old\n")

    # covers: AC-4 (the hook replace rules of install.sh: an up to date copy and a hand written hook are left alone)
    def test_hooks_left_alone(self):
        checker = self.repo / "scripts" / "private-names.py"
        shutil.copy(checker, self.hooks / "pre-commit")
        (self.hooks / "pre-commit").chmod(0o755)
        (self.hooks / "commit-msg").write_text("#!/bin/sh\nexit 0\n")
        done = [d for d, _ in self.swap()]
        self.assertNotIn(str(self.hooks / "pre-commit"), done)
        self.assertNotIn(str(self.hooks / "commit-msg"), done)
        self.assertEqual((self.hooks / "commit-msg").read_text(), "#!/bin/sh\nexit 0\n")
        # An older copy (same second line) is refreshed; no names list means no hooks at all.
        (self.hooks / "commit-msg").write_text("#!/usr/bin/env python3\n# checker v2\nold\n")
        self.assertIn(str(self.hooks / "commit-msg"), [d for d, _ in self.swap()])
        (self.stage / "private" / "names.txt").unlink()
        (self.hooks / "pre-commit").unlink()
        self.assertNotIn(str(self.hooks / "pre-commit"), [d for d, _ in self.swap()])

    def journal(self, stamp, renames, done=False):
        d = self.state / "wf" / "finish" / stamp
        d.mkdir(parents=True, exist_ok=True)
        (d / "swap.json").write_text(json.dumps({"renames": renames, "done": done}))
        return d

    # covers: AC-4 (an interrupted swap with a ledger line is finished forward; without one it is dropped; a stray
    # aside and one of a done journal are deleted)
    def test_recover(self):
        a = self.live / "rules" / f"a.md.wf-swap-{STAMP}"
        a.write_text("new\n")
        s = self.live / f"settings.json.wf-swap-{STAMP}"
        s.write_text('{"b": 2}')
        self.journal(STAMP, [[str(a), str(self.live / "rules" / "a.md")], [str(s), str(self.live / "settings.json")]])
        (self.state / "wf" / "swaps.jsonl").write_text(json.dumps({"stamp": STAMP, "pid": 1, "at": "x", "files": {}}) + "\n")
        b = self.live / "rules" / "b.md.wf-swap-20261013-030000"
        b.write_text("b")
        self.journal("20261013-030000", [[str(b), str(self.live / "rules" / "b.md")]])
        stray = self.live / "rules" / "c.md.wf-swap-20261013-040000"
        stray.write_text("c")
        old = self.live / "rules" / "d.md.wf-swap-20261013-050000"
        old.write_text("d")
        self.journal("20261013-050000", [[str(old), str(self.live / "rules" / "d.md")]], done=True)
        out = io.StringIO()
        with redirect_stdout(out):
            finish.recover()
        self.assertEqual((self.live / "rules" / "a.md").read_text(), "new\n")
        self.assertEqual((self.live / "settings.json").read_text(), '{"b": 2}')
        self.assertFalse((self.live / "rules" / "b.md").exists())
        self.assertEqual([p.name for p in self.live.rglob("*") if ".wf-swap-" in p.name], [])
        self.assertIn(f"finished an interrupted swap from {STAMP}", out.getvalue())
        self.assertIn("dropped an interrupted swap from 20261013-030000", out.getvalue())
        for stamp in (STAMP, "20261013-030000"):
            self.assertTrue(json.loads((self.state / "wf" / "finish" / stamp / "swap.json").read_text())["done"])

    # covers: AC-4 (a held swap lock leaves an interrupted journal to its holder)
    def test_recover_held(self):
        a = self.live / "rules" / f"a.md.wf-swap-{STAMP}"
        a.write_text("new\n")
        self.journal(STAMP, [[str(a), str(self.live / "rules" / "a.md")]])
        fd, _ = run.lock_file(str(self.state / "wf" / "swap.lock"), what="wf setup swap")
        try:
            with redirect_stdout(io.StringIO()):
                finish.recover()
        finally:
            os.close(fd)
        self.assertTrue(a.exists())


class TestInstallStage(unittest.TestCase):
    """AC-3: install.sh with WF_STAGE=1 writes no bin link and no git hook; without it, as today. A scratch repo with
    a copy of install.sh, as scripts/private-names.py tests it: it stops at its own verify step, after every write."""

    def test_stage(self):
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, tmp)
        repo = tmp / "repo"
        for d in ("live/agents", "live/rules", "live/hooks", "live/scripts", "scripts", "runner"):
            (repo / d).mkdir(parents=True)
        shutil.copy(RUNNER.parent / "install.sh", repo / "install.sh")
        shutil.copy(RUNNER / "finish.py", repo / "runner" / "finish.py")
        for f in ("run.py", "wf.py", "ntfy.py", "report.py", "telegram.py", "plain.py", "context.py"):
            shutil.copy(RUNNER / f, repo / "runner" / f)
        for f in ("hooks/block-destructive.sh", "hooks/review-stack-pre-push", "hooks/plain-panel.py", "scripts/chroma-reaper.sh"):
            (repo / "live" / f).write_text("#!/bin/sh\n")
        (repo / "scripts" / "private-names.py").write_text("#!/usr/bin/env python3\n# c\n")
        (repo / "live" / "settings.json").write_text("{}")
        (repo / "live" / "CLAUDE.md").write_text("# r\n")
        subprocess.run(["git", "init", "-q", str(repo)], check=True, stdin=subprocess.DEVNULL)
        hooks = repo / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        for h in hooks.iterdir():
            h.unlink()
        for staged in (True, False):
            home = tmp / f"home-{staged}"
            live = home / ".claude"
            (live / "private").mkdir(parents=True)
            (live / "private" / "names.txt").write_text("x\n")
            (live / "settings.json").write_text('{"old": 1}')
            env ={**os.environ, "HOME": str(home), "CLAUDE_LIVE_DIR": str(live), "GIT_CONFIG_GLOBAL": "/dev/null"}
            env.pop("WF_STAGE", None)
            if staged:
                env["WF_STAGE"] = "1"
            r = subprocess.run(["bash", str(repo / "install.sh")], env=env, capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, timeout=120)
            with self.subTest(staged=staged):
                self.assertEqual(("staged: bin links and git hooks left to wf" in r.stdout), staged, r.stdout + r.stderr)
                self.assertEqual((home / ".local" / "bin").exists(), not staged, r.stdout + r.stderr)
                self.assertEqual((hooks / "pre-commit").exists(), not staged, r.stdout + r.stderr)
                self.assertTrue((live / "rules").is_dir())
                self.assertTrue((live / "settings.json").exists(), r.stdout + r.stderr)
                # covers: spec 0035 AC-7 (the old settings are backed up under backups/settings/, never at the top)
                baks = list((live / "backups" / "settings").glob("settings.json.bak.*"))
                self.assertEqual([b.read_text() for b in baks], ['{"old": 1}'], r.stdout + r.stderr)
                self.assertEqual([p.name for p in live.glob("*.bak.*")], [])


if __name__ == "__main__":
    unittest.main()
