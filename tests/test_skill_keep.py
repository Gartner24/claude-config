import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "scripts" / "skill-keep.py"

spec = importlib.util.spec_from_file_location("skill_keep", SCRIPT)
sk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sk)

KEEP_37 = [
    "design-gate", "impeccable", "rollover", "save-and-clear", "save-and-exit", "resume-from-clear",
    "sync", "architect", "design", "check", "test", "develop", "scope", "debug", "audit", "document",
    "auto", "review", "review-stack", "browse", "deep-research", "cro", "marketing-psychology",
    "high-end-visual-design", "minimalist-ui", "ui-ux-pro-max", "design-dna", "design-motion-principles",
    "assets", "brand-system", "animate", "animation-vocabulary", "review-animations", "gsap-scrolltrigger",
    "write", "polish", "new-site",
]


class Live:
    """A temp ~/.claude with skills, commands, plugins and settings."""

    def __init__(self, test, settings, skills=(), commands=()):
        self.tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        for s in skills:
            d = self.dir / "skills" / s
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"---\nname: {s}\n---\n")
        (self.dir / "commands").mkdir(exist_ok=True)
        for c in commands:
            (self.dir / "commands" / f"{c}.md").write_text("x\n")
        self.path = self.dir / "settings.json"
        self.path.write_text(json.dumps(settings, indent=2) + "\n")
        os.chmod(self.path, 0o640)
        self.keep = self.dir / "keep.txt"

    def run(self, keep, *args):
        self.keep.write_text("# comment\n\n" + "\n".join(keep) + "\n")
        out = io.StringIO()
        env = {**os.environ, "CLAUDE_LIVE_DIR": str(self.dir)}
        with mock.patch.dict(os.environ, env), mock.patch.object(sk, "KEEP", self.keep), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = sk.main(list(args))
        return code, out.getvalue().splitlines()

    def settings(self):
        return json.loads(self.path.read_text())

    def backups(self):
        d = self.dir / "backups" / "settings"
        return sorted(d.iterdir()) if d.is_dir() else []

    def plugin(self, folder, skills=0, commands=0):
        for i in range(skills):
            d = folder / "skills" / f"s{i}"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text("x\n")
        (folder / "commands").mkdir(parents=True, exist_ok=True)
        for i in range(commands):
            (folder / "commands" / f"c{i}.md").write_text("x\n")


class KeepListFile(unittest.TestCase):
    def test_real_list_is_the_37_names(self):
        self.assertEqual(sk.read_keep(), KEEP_37)

    def test_comments_and_blanks_ignored(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "k.txt"
            p.write_text("# a\n\n  alpha  \n#beta\nbeta\n")
            self.assertEqual(sk.read_keep(p), ["alpha", "beta"])

    def test_no_private_names(self):
        if not (Path.home() / ".claude" / "private" / "names.txt").is_file():
            self.skipTest("no names.txt")
        # covers: AC-9. Checks the one file: a whole repo check used to stop on sandbox masked
        # dotfiles, so asserting only on its output passed without ever reading the list.
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "scripts" / "private-names.py"), "check",
                            str(sk.KEEP)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)


class Overrides(unittest.TestCase):
    def test_write(self):
        live = Live(self, {"model": "x", "skillOverrides": {"gone": "name-only", "kept": "name-only",
                                                      "already": "name-only", "frozen": "off",
                                                      "typed": "user-invocable-only"},
                     "theme": "dark"},
                    skills=["kept", "already", "frozen", "typed", "fresh", "free"], commands=["cmd"])
        code, out = live.run(["kept", "free", "typed"])
        self.assertEqual(code, 0)
        s = live.settings()
        self.assertEqual(list(s), ["model", "skillOverrides", "theme"])
        self.assertEqual(s["model"], "x")
        self.assertEqual(s["theme"], "dark")
        self.assertEqual(s["skillOverrides"], {"gone": "name-only", "already": "name-only",
                                               "frozen": "off", "typed": "user-invocable-only",
                                               "cmd": "name-only", "fresh": "name-only"})
        self.assertEqual(list(s["skillOverrides"])[-2:], ["cmd", "fresh"])
        self.assertIn("described: kept", out)
        self.assertIn("name-only: fresh", out)
        self.assertIn("name-only: cmd", out)
        self.assertNotIn("name-only: free", out)
        self.assertEqual(out[-1], "next: run tools/bin/sync.sh now, before any tools/bin/install.sh")

    def test_no_overrides_key_appended_last(self):
        live = Live(self, {"a": 1, "b": 2}, skills=["x"])
        live.run([])
        self.assertEqual(list(live.settings()), ["a", "b", "skillOverrides"])

    def test_dry_run_writes_nothing(self):
        live = Live(self, {"skillOverrides": {"kept": "name-only", "frozen": "off"}},
                    skills=["kept", "frozen", "other"])
        before = live.path.read_text()
        code, out = live.run(["kept", "frozen"], "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(live.path.read_text(), before)
        self.assertEqual(live.backups(), [])
        self.assertEqual(out[:3], ["kept as off: frozen", "described: kept", "name-only: other"])
        self.assertNotIn("next: run tools/bin/sync.sh now, before any tools/bin/install.sh", out)

    def test_backup_mode_and_format(self):
        live = Live(self, {"skillOverrides": {}, "note": "café"}, skills=["x"])
        before = live.path.read_text()
        live.run([])
        baks = live.backups()
        self.assertEqual(len(baks), 1)
        self.assertRegex(baks[0].name, r"^settings\.json\.bak\.\d{8}-\d{6}$")
        self.assertEqual(baks[0].read_text(), before)
        self.assertEqual(live.path.stat().st_mode & 0o777, 0o640)
        text = live.path.read_text()
        self.assertTrue(text.endswith("}\n"))
        self.assertIn("café", text)
        self.assertEqual(text, json.dumps(live.settings(), indent=2, ensure_ascii=False) + "\n")

    def test_bad_settings_exit_1_unchanged(self):
        live = Live(self, {}, skills=["x"])
        live.path.write_text("{not json")
        code, _ = live.run([])
        self.assertEqual(code, 1)
        self.assertEqual(live.path.read_text(), "{not json")
        self.assertEqual(live.backups(), [])

    def test_missing_settings_exit_1(self):
        live = Live(self, {}, skills=["x"])
        live.path.unlink()
        code, _ = live.run([])
        self.assertEqual(code, 1)
        self.assertFalse(live.path.exists())

    def test_folder_without_skill_md_ignored(self):
        live = Live(self, {}, skills=["real"])
        (live.dir / "skills" / "loose").mkdir()
        live.run([])
        self.assertEqual(live.settings()["skillOverrides"], {"real": "name-only"})

    def test_linked_skill_followed(self):
        live = Live(self, {}, skills=[])
        target = live.dir / "elsewhere" / "linked"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("x\n")
        (live.dir / "skills").mkdir(exist_ok=True)
        (live.dir / "skills" / "linked").symlink_to(target)
        live.run([])
        self.assertEqual(live.settings()["skillOverrides"], {"linked": "name-only"})


class Report(unittest.TestCase):
    def test_every_plugin_reported(self):
        live = Live(self, {"enabledPlugins": {"on@m": True, "off@m": False, "gone@m": True,
                                       "unlisted@m": "yes"}},
                    skills=["mine", "kept"])
        on = live.dir / "plugins" / "cache" / "on"
        live.plugin(on, skills=2, commands=1)
        offp = live.dir / "plugins" / "cache" / "off"
        live.plugin(offp, skills=5)
        unlisted = live.dir / "plugins" / "cache" / "unlisted"
        live.plugin(unlisted, skills=1)
        reg = {"version": 2, "plugins": {
            "on@m": [{"installPath": str(on)}],
            "off@m": [{"installPath": str(offp)}],
            "gone@m": [{"installPath": str(live.dir / "nope")}],
            "unlisted@m": [{"installPath": str(unlisted)}],
            "bare@m": [],
        }}
        (live.dir / "plugins" / "installed_plugins.json").write_text(json.dumps(reg))
        sentry = live.dir / "skills" / "sentry-pack"
        live.plugin(sentry, skills=3)
        (sentry / ".claude-plugin").mkdir()
        (sentry / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "sentry-skills"}))
        code, out = live.run(["kept", "absent"])
        self.assertEqual(code, 0)
        self.assertNotIn("sentry-pack", live.settings()["skillOverrides"])
        self.assertNotIn("s0", live.settings()["skillOverrides"])
        i = out.index("described: 1 own skills")
        self.assertEqual(out[i + 1:i + 9], [
            "plugin on@m: 2 skills, 1 commands (not controlled)",
            "plugin off@m: off",
            "plugin gone@m: folder missing",
            "plugin unlisted@m: off",
            "plugin bare@m: folder missing",
            "plugin sentry-skills: 3 skills, 0 commands (not controlled)",
            "total described: 6",
            "warning: kept skill not installed: absent",
        ])


if __name__ == "__main__":
    unittest.main()
