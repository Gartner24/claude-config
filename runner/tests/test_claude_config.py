"""Spec 0048: bin/claude-config.py on temp trees. Upstreams are local git repos, so nothing reaches the network;
the tool is run as a subprocess with CLAUDE_CONFIG_REPO and CLAUDE_LIVE_DIR, never against ~/.claude."""
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REAL = Path(__file__).resolve().parents[2]
TOOL = REAL / "bin" / "claude-config.py"
ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t",
       "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
SKILL = "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\n"

_spec = importlib.util.spec_from_file_location("claude_config", TOOL)
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo, self.live, self.up = self.tmp / "repo", self.tmp / "live", self.tmp / "up"
        for d in (self.repo / "scripts", self.repo / "config", self.repo / "claude-home" / "skills",
                  self.live / "skills", self.live / "private"):
            d.mkdir(parents=True)
        shutil.copy(REAL / "scripts" / "private-names.py", self.repo / "scripts" / "private-names.py")
        (self.live / "private" / "names.txt").write_text("zorblex\n")
        self.env = {**os.environ, **ENV, "CLAUDE_CONFIG_REPO": str(self.repo), "CLAUDE_LIVE_DIR": str(self.live)}
        self.up.mkdir()
        self.git(self.up, "init", "-q", "-b", "main")
        self.git(self.up, "config", "uploadpack.allowAnySHA1InWant", "true")
        self.pinned = self.commit({"skills/s/SKILL.md": SKILL, "skills/s/ref.md": "ref\n"})

    def git(self, cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, env={**os.environ, **ENV}, capture_output=True, text=True,
                              check=True).stdout.strip()

    def commit(self, files):
        for rel, body in files.items():
            p = self.up / rel
            if body is None:
                p.unlink()
                continue
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body)
        self.git(self.up, "add", "-A")
        self.git(self.up, "commit", "-q", "-m", "c")
        return self.git(self.up, "rev-parse", "HEAD")

    def tool(self, *args):
        return subprocess.run([sys.executable, "-B", str(TOOL), *args], env=self.env, capture_output=True, text=True)

    def install_edited(self, edit="line 2 mine\n", publish=True):
        """The live skill: upstream at pinned with line 2 edited, and its manifest entry and patch via sync."""
        s = self.live / "skills" / "s"
        s.mkdir()
        (s / "SKILL.md").write_text(SKILL.replace("line 2\n", edit))
        (s / "ref.md").write_text("ref\n")
        base = self.tmp / "base"
        (base).mkdir()
        (base / "SKILL.md").write_text(SKILL)
        (base / "ref.md").write_text("ref\n")
        self.manifest({"s": {"kind": "skill", "status": "downloaded", "source": str(self.up), "path": "skills/s",
                             "pinned": self.pinned, "base_hash": cc.folder_hash(base), "license": "MIT",
                             "publish": publish, "patch": None, "fetch": "git", "install": "x", "framework": None}})
        r = self.tool("patches")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return s

    def manifest(self, entries=None):
        p = self.repo / "config" / "manifest.json"
        if entries is None:
            return json.loads(p.read_text())
        p.write_text(json.dumps({"version": 1, "frameworks": {}, "entries": entries}))


class TestPatches(Case):
    # covers: AC-7 (an edit becomes a public patch, status edited), AC-8 publish: false goes private
    def test_patch_written(self):
        self.install_edited()
        e = self.manifest()["entries"]["s"]
        self.assertEqual((e["status"], e["patch"]), ("edited", "config/patches/s.patch"))
        patch = (self.repo / "config" / "patches" / "s.patch").read_text()
        self.assertIn("+line 2 mine", patch)
        self.assertIn("--- a/SKILL.md", patch)

    def test_private_patch(self):
        self.install_edited(publish=False)
        e = self.manifest()["entries"]["s"]
        self.assertEqual(e["patch"], "~/.claude/private/patches/s.patch")
        self.assertTrue((self.live / "private" / "patches" / "s.patch").exists())
        self.assertFalse((self.repo / "config" / "patches").exists())

    # covers: AC-8 (a patch holding a private name never enters the repo)
    def test_name_goes_private(self):
        self.install_edited(edit="line 2 Zorblex\n")
        self.assertEqual(self.manifest()["entries"]["s"]["patch"], "~/.claude/private/patches/s.patch")
        self.assertFalse((self.repo / "config" / "patches" / "s.patch").exists())


class TestRestore(Case):
    # covers: AC-7 (a missing edited skill is rebuilt from upstream at pinned plus its patch, same hash)
    def test_rebuild(self):
        s = self.install_edited()
        before = cc.folder_hash(s)
        self.commit({"skills/s/SKILL.md": SKILL + "line 7\n"})  # upstream moved on; pinned must be used
        shutil.rmtree(s)
        r = self.tool("restore")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(cc.folder_hash(s), before)

    def test_installed_never_overwritten(self):
        s = self.install_edited()
        (s / "SKILL.md").write_text("mine only\n")
        self.assertEqual(self.tool("restore").returncode, 0)
        self.assertEqual((s / "SKILL.md").read_text(), "mine only\n")


class TestUpdate(Case):
    def state(self):
        s = self.live / "skills" / "s"
        return cc.folder_hash(s), (self.repo / "config" / "manifest.json").read_bytes()

    # covers: AC-10 (clean merge installs, moves pinned and base_hash, keeps your edit in the new patch)
    def test_clean(self):
        s = self.install_edited()
        head = self.commit({"skills/s/SKILL.md": SKILL.replace("line 5\n", "line 5 up\n"), "skills/s/new.md": "n\n"})
        plan = self.tool("update", "--plan")
        self.assertIn("s (edited): upstream", plan.stdout)
        self.assertIn("SKILL.md", plan.stdout)
        r = self.tool("update", "--apply", "s")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = (s / "SKILL.md").read_text()
        self.assertIn("line 2 mine", text)
        self.assertIn("line 5 up", text)
        self.assertTrue((s / "new.md").exists())
        e = self.manifest()["entries"]["s"]
        self.assertEqual((e["pinned"], e["status"]), (head, "edited"))
        self.assertIn("+line 2 mine", (self.repo / "config" / "patches" / "s.patch").read_text())
        self.assertNotIn("+line 5 up", (self.repo / "config" / "patches" / "s.patch").read_text())

    # covers: AC-10 (conflict: exit 2, conflicts folder, live and manifest byte for byte unchanged)
    def test_conflict_then_resolved(self):
        self.install_edited()
        self.commit({"skills/s/SKILL.md": SKILL.replace("line 2\n", "line 2 up\n")})
        before = self.state()
        r = self.tool("update", "--apply", "s")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertEqual(self.state(), before)
        conflict = self.live / "state" / "claude-config-conflicts" / "s" / "SKILL.md"
        self.assertIn("<<<<<<< mine", conflict.read_text())
        self.assertEqual(self.tool("update", "--apply", "s", "--resolved").returncode, 2)
        self.assertEqual(self.state(), before)
        conflict.write_text(SKILL.replace("line 2\n", "line 2 both\n"))
        r = self.tool("update", "--apply", "s", "--resolved")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("line 2 both", (self.live / "skills" / "s" / "SKILL.md").read_text())
        self.assertFalse(conflict.parent.exists())

    # covers: AC-10 (a source that is gone changes nothing, and the plan does not record a check)
    def test_unreachable(self):
        self.install_edited()
        before = self.state()
        shutil.rmtree(self.up)
        self.assertEqual(self.tool("update", "--apply", "s").returncode, 1)
        self.assertEqual(self.state(), before)
        r = self.tool("update", "--plan")
        self.assertIn("source not reached", r.stdout)
        self.assertFalse((self.live / "state" / "claude-config.json").exists())

    # covers: AC-11 (a plan that reached every source records the time)
    def test_plan_writes_state(self):
        self.install_edited()
        self.assertEqual(self.tool("update", "--plan").returncode, 0)
        self.assertIn("last_upstream_check", (self.live / "state" / "claude-config.json").read_text())

    # covers: AC-10 (a file upstream deleted is deleted when you did not edit it, a conflict when you did)
    def test_merge_deletes(self):
        base, mine, theirs, out = (self.tmp / n for n in ("b", "m", "t", "o"))
        for d in (base, mine, theirs):
            d.mkdir()
            (d / "a.md").write_text("a\n")
            (d / "b.md").write_text("b\n")
        (theirs / "a.md").unlink()
        (theirs / "b.md").unlink()
        (mine / "b.md").write_text("b mine\n")
        self.assertEqual(cc.merge(base, mine, theirs, out), ["b.md"])
        self.assertFalse((out / "a.md").exists())


class TestDrift(Case):
    # covers: AC-9 (no drift exits 0; a live only skill, a missing link and a changed source-unknown exit 1)
    def test_drift(self):
        own = self.repo / "claude-home" / "skills" / "mine"
        own.mkdir()
        (own / "SKILL.md").write_text("x\n")
        (self.live / "skills" / "mine").symlink_to(own)
        r = self.tool("drift")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "drift: none"), r.stdout + r.stderr)
        stray = self.live / "skills" / "stray"
        stray.mkdir()
        (stray / "SKILL.md").write_text("y\n")
        r = self.tool("drift")
        self.assertEqual(r.returncode, 1)
        self.assertIn("stray: live only", r.stdout)
        self.manifest({"stray": {"kind": "skill", "status": "source-unknown", "base_hash": cc.folder_hash(stray),
                                 "license": "unknown", "publish": False}})
        self.assertEqual(self.tool("drift").returncode, 0)
        (stray / "SKILL.md").write_text("changed\n")
        self.assertIn("stray: changed since its base hash", self.tool("drift").stdout)

    # covers: AC-7 (the old override guard: a reinstall over an edited skill shows in drift)
    def test_override_lost(self):
        s = self.install_edited()
        self.assertEqual(self.tool("drift").returncode, 0, self.tool("drift").stdout)
        (s / "SKILL.md").write_text(SKILL)
        self.assertIn("s: your edit is no longer in it", self.tool("drift").stdout)


class TestReminder(unittest.TestCase):
    _spec = importlib.util.spec_from_file_location("reminder", REAL / "claude-home" / "hooks" / "claude-config-reminder.py")
    hook = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(hook)

    # covers: AC-11 (8 days prints the line, 6 days prints nothing, missing prints the line)
    def test_days(self):
        now = datetime.datetime(2026, 10, 15, tzinfo=datetime.timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "claude-config.json"
            self.assertIn("run /claude-config update", self.hook.line(state, now))
            for days, shown in ((8, True), (6, False), (7, True)):
                state.write_text(json.dumps({"last_upstream_check": (now - datetime.timedelta(days=days)).isoformat()}))
                self.assertEqual(self.hook.line(state, now) is not None, shown, days)
            self.assertEqual(self.hook.line(state.with_name("x"), now)[:13], "claude-config")

    # covers: AC-11 (the registration is in the repo settings, and the sync transform keeps it)
    def test_sync_keeps_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "private").mkdir()
            (Path(tmp) / "private" / "names.txt").write_text("zorblex\n")
            out = Path(tmp) / "out.json"
            r = subprocess.run([sys.executable, str(REAL / "scripts" / "private-names.py"), "strip-settings",
                                str(REAL / "claude-home" / "settings.json"), str(out), str(Path(tmp) / "frag.json")],
                               env={**os.environ, "CLAUDE_LIVE_DIR": tmp}, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            starts = json.dumps(json.loads(out.read_text())["hooks"]["SessionStart"])
            self.assertIn("hooks/claude-config-reminder.py", starts)


if __name__ == "__main__":
    unittest.main()
