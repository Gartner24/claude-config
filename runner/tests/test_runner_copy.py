import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RUNNER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RUNNER))

import finish  # noqa: E402
import run  # noqa: E402


# covers: spec 0020 AC-12 (runner copy outside the repo, links, prune, deny)
class TestRunnerCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        self.repo = self.tmp / "repo"
        (self.repo / "runner" / "tests").mkdir(parents=True)
        (self.repo / "runner" / "wf.py").write_text("print('wf')\n")
        (self.repo / "runner" / "run.py").write_text("x = 1\n")
        (self.repo / "runner" / "tests" / "test_x.py").write_text("")
        self.share = self.home / ".local" / "share" / "wf"
        self.bin = self.home / ".local" / "bin"

    def tearDown(self):
        subprocess.run(["rm", "-rf", str(self.tmp)])

    def install(self, dry=False):
        with mock.patch("sys.stdout"):
            return finish.install_runner(str(self.repo), str(self.home), dry)

    def test_copy_and_links(self):
        fp = self.install()
        dst = self.share / fp
        self.assertEqual(sorted(os.listdir(dst)), ["run.py", "wf.py"])
        for name in ("wf", "next"):
            self.assertEqual(os.path.realpath(self.bin / name), str(dst / "wf.py"))
        self.assertFalse(any(str(self.repo) in os.path.realpath(self.bin / n) for n in ("wf", "next")))

    def test_same_files_same_folder_change_makes_new(self):
        fp = self.install()
        self.assertEqual(self.install(), fp)
        self.assertEqual(os.listdir(self.share), [fp])
        (self.repo / "runner" / "run.py").write_text("x = 2\n")
        fp2 = self.install()
        self.assertNotEqual(fp2, fp)
        self.assertEqual(sorted(os.listdir(self.share)), sorted([fp, fp2]))
        self.assertEqual(os.path.realpath(self.bin / "wf"), str(self.share / fp2 / "wf.py"))

    # covers: spec 0026 AC-6 (the copy carries scripts/private-names.py, which joins the fingerprint)
    def test_carries_checker(self):
        fp = self.install()
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts" / "private-names.py").write_text("# checker\n")
        fp2 = self.install()
        self.assertNotEqual(fp2, fp)
        self.assertEqual((self.share / fp2 / "private-names.py").read_text(), "# checker\n")
        self.assertEqual(sorted(os.listdir(self.share / fp2)), ["private-names.py", "run.py", "wf.py"])

    def test_fingerprint_frames_name_and_bytes(self):
        # Unframed, run.py "x = 1\n" + wf.py "print('wf')\n" hashes like one run.py holding both.
        a = finish.runner_fp(str(self.repo / "runner"))
        (self.repo / "runner" / "wf.py").unlink()
        (self.repo / "runner" / "run.py").write_text("x = 1\nwf.pyprint('wf')\n")
        self.assertNotEqual(finish.runner_fp(str(self.repo / "runner")), a)

    def test_prune_old_unlinked_keeps_linked(self):
        fp = self.install()
        old = self.share / "aaaaaaaaaaaa"
        kept = self.share / "bbbbbbbbbbbb"
        for d in (old, kept):
            d.mkdir()
            (d / "wf.py").write_text("")
        (self.bin / "other").symlink_to(kept / "wf.py")
        week = 8 * 86400
        for d in (old, kept, self.share / fp):
            t = d.stat().st_mtime - week
            os.utime(d, (t, t))
        self.install()
        self.assertEqual(sorted(os.listdir(self.share)), sorted([fp, "bbbbbbbbbbbb"]))

    def test_recent_unlinked_kept(self):
        fp = self.install()
        recent = self.share / "cccccccccccc"
        recent.mkdir()
        self.install()
        self.assertEqual(sorted(os.listdir(self.share)), sorted([fp, "cccccccccccc"]))

    def test_dry_changes_nothing(self):
        self.install(dry=True)
        self.assertFalse(self.home.exists())

    def test_real_file_skipped(self):
        self.bin.mkdir(parents=True)
        (self.bin / "wf").write_text("mine")
        self.install()
        self.assertEqual((self.bin / "wf").read_text(), "mine")
        self.assertTrue((self.bin / "next").is_symlink())

    def test_deny_has_no_repo_path(self):
        self.install()
        settings = {"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": f"{self.bin}/wf report --hook"}]}]}}
        with mock.patch.dict(os.environ, {"HOME": str(self.home), "PATH": str(self.bin)}):
            tokens = run.hook_tokens([settings], str(self.repo))
            deny = run.deny_paths(str(self.repo), f"{self.repo}/.git", tokens)
        self.assertEqual([d for d in deny if d.startswith(str(self.repo / "runner"))], [])
        self.assertIn(str(self.share), deny)

    def test_install_sh_dry_run_names_copy(self):
        real = RUNNER.parent
        env = {**os.environ, "HOME": str(self.home), "CLAUDE_LIVE_DIR": str(self.tmp / "live")}
        r = subprocess.run(["bash", str(real / "bin/install.sh"), "--dry-run"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        # the runner is retired live (2026-10-22): install no longer copies or links it
        self.assertNotIn("runner/*.py", r.stdout)
        self.assertNotIn(f"{self.bin}/wf", r.stdout)
        self.assertFalse(self.share.exists())


if __name__ == "__main__":
    unittest.main()
