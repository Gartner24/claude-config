"""bin/install.sh (spec 0020 AC-3, AC-4, spec 0035 AC-7, spec 0072): copied from the archived runner suite, which no
longer runs. A scratch repo holds a copy of the script; it stops at its own verify step, after every write."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHECKER = "#!/usr/bin/env python3\n# c\n"


class Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = repo = self.tmp / "repo"
        for d in ("claude-home/agents", "claude-home/rules", "claude-home/hooks", "claude-home/scripts", "scripts", "bin"):
            (repo / d).mkdir(parents=True)
        shutil.copy(REPO / "bin/install.sh", repo / "bin/install.sh")
        shutil.copy(REPO / "bin/claude-config.py", repo / "bin/claude-config.py")
        for f in ("hooks/block-destructive.sh", "hooks/review-stack-pre-push", "hooks/plain-panel.py",
                  "hooks/context-monitor.js", "hooks/handover-start.sh", "hooks/no-jjstack-bar.py", "hooks/skill-rules.py"):
            (repo / "claude-home" / f).write_text("#!/bin/sh\n")
        (repo / "scripts" / "private-names.py").write_text(CHECKER)
        (repo / "claude-home" / "settings.json").write_text("{}")
        (repo / "claude-home" / "CLAUDE.md").write_text("# r\n")
        subprocess.run(["git", "init", "-q", str(repo)], check=True, stdin=subprocess.DEVNULL)
        self.hooks = repo / ".git" / "hooks"
        self.hooks.mkdir(exist_ok=True)
        for h in self.hooks.iterdir():
            h.unlink()

    def install(self, name, staged=False, *args):
        home = self.tmp / f"home-{name}"
        live = home / ".claude"
        (live / "private").mkdir(parents=True, exist_ok=True)
        (live / "private" / "names.txt").write_text("x\n")
        (live / "settings.json").write_text('{"old": 1}')
        env = {**os.environ, "HOME": str(home), "CLAUDE_LIVE_DIR": str(live), "GIT_CONFIG_GLOBAL": "/dev/null"}
        env.pop("WF_STAGE", None)
        if staged:
            env["WF_STAGE"] = "1"
        r = subprocess.run(["bash", str(self.repo / "bin/install.sh"), *args], env=env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=120)
        return home, live, r


class TestInstallStage(Scratch):
    # covers: spec 0020 AC-3 (WF_STAGE=1 writes no bin link and no git hook; without it, as today)
    def test_stage(self):
        for staged in (True, False):
            home, live, r = self.install(f"stage-{staged}", staged)
            with self.subTest(staged=staged):
                self.assertEqual(("staged: bin links and git hooks left to wf" in r.stdout), staged, r.stdout + r.stderr)
                self.assertEqual((home / ".local" / "bin").exists(), not staged, r.stdout + r.stderr)
                self.assertEqual((self.hooks / "pre-commit").exists(), not staged, r.stdout + r.stderr)
                self.assertTrue((live / "rules").is_dir())
                self.assertTrue((live / "settings.json").exists(), r.stdout + r.stderr)
                # covers: spec 0035 AC-7 (the old settings are backed up under backups/settings/, never at the top)
                baks = list((live / "backups" / "settings").glob("settings.json.bak.*"))
                self.assertEqual([b.read_text() for b in baks], ['{"old": 1}'], r.stdout + r.stderr)
                self.assertEqual([p.name for p in live.glob("*.bak.*")], [])

    # covers: spec 0020 AC-4 (the hook replace rules of bin/install.sh: an up to date copy and a hand written hook are
    # left alone; an older copy, same second line, is refreshed; a missing hook is copied)
    def test_hooks_left_alone(self):
        (self.hooks / "pre-commit").write_text(CHECKER)
        (self.hooks / "pre-commit").chmod(0o755)
        (self.hooks / "commit-msg").write_text("#!/bin/sh\nexit 0\n")
        _, _, r = self.install("a")
        self.assertIn("pre-commit: up to date", r.stdout, r.stdout + r.stderr)
        self.assertIn("hook exists, not replaced: commit-msg", r.stdout, r.stdout + r.stderr)
        self.assertEqual((self.hooks / "commit-msg").read_text(), "#!/bin/sh\nexit 0\n")
        (self.hooks / "commit-msg").write_text("#!/usr/bin/env python3\n# c\nold\n")
        (self.hooks / "pre-commit").unlink()
        _, _, r = self.install("b")
        self.assertIn("commit-msg: refreshed", r.stdout, r.stdout + r.stderr)
        self.assertIn("pre-commit: copied", r.stdout, r.stdout + r.stderr)
        self.assertEqual((self.hooks / "commit-msg").read_text(), CHECKER)
        self.assertEqual((self.hooks / "pre-commit").read_text(), CHECKER)


class TestWorkflowLinks(Scratch):
    # covers: spec 0076 AC-6 (each claude-home/workflows/<name> is linked to ~/.claude/workflows/<name>; a real folder
    # already there is skipped and named, never replaced)
    def test_workflow_links(self):
        for name in ("a", "b"):
            (self.repo / "claude-home" / "workflows" / name).mkdir(parents=True)
        home = self.tmp / "home-wf"
        (home / ".claude" / "workflows" / "b").mkdir(parents=True)
        _, live, r = self.install("wf")
        link = live / "workflows" / "a"
        self.assertTrue(link.is_symlink(), r.stdout + r.stderr)
        self.assertEqual(link.resolve(), (self.repo / "claude-home" / "workflows" / "a").resolve())
        self.assertFalse((live / "workflows" / "b").is_symlink())
        self.assertIn("SKIP workflows/b (a real file is already there)", r.stdout)


class TestRulesOnDemand(Scratch):
    # covers: spec 0077 AC-6 (MAP.md is copied live), AC-7 (rules-on-demand/ and skill-rules.py are copied; a live file
    # in rules/ or rules-on-demand/ with no repo source moves to backups/rules/<date>/ and is named in the output)
    def test_moved_rules_stop_loading(self):
        (self.repo / "claude-home" / "rules" / "kept.md").write_text("kept\n")
        (self.repo / "claude-home" / "rules-on-demand").mkdir()
        (self.repo / "claude-home" / "rules-on-demand" / "moved.md").write_text("moved\n")
        (self.repo / "claude-home" / "MAP.md").write_text("map\n")
        live = self.tmp / "home-rules" / ".claude"
        for rel in ("rules/kept.md", "rules/moved.md", "rules-on-demand/stale.md"):
            (live / rel).parent.mkdir(parents=True, exist_ok=True)
            (live / rel).write_text("old\n")
        _, live, r = self.install("rules")
        out = r.stdout + r.stderr
        self.assertEqual((live / "rules" / "kept.md").read_text(), "kept\n", out)
        self.assertEqual((live / "rules-on-demand" / "moved.md").read_text(), "moved\n", out)
        self.assertEqual((live / "MAP.md").read_text(), "map\n", out)
        self.assertTrue((live / "hooks" / "skill-rules.py").exists(), out)
        self.assertFalse((live / "rules" / "moved.md").exists(), out)
        self.assertFalse((live / "rules-on-demand" / "stale.md").exists(), out)
        backups = sorted(str(p.relative_to(live / "backups" / "rules")) for p in (live / "backups" / "rules").rglob("*.md"))
        self.assertEqual([b.split("/", 1)[1] for b in backups], ["rules-on-demand/stale.md", "rules/moved.md"], out)
        self.assertIn("live only: rules/moved.md -> backups/rules/", r.stdout, out)
        self.assertIn("live only: rules-on-demand/stale.md -> backups/rules/", r.stdout, out)


    # covers: PR 205 review (a second same-day backup of the same path keeps the first one under a numbered name)
    def test_backup_not_overwritten(self):
        (self.repo / "claude-home" / "rules-on-demand").mkdir()
        live = self.tmp / "home-bak" / ".claude"
        for text in ("first\n", "second\n"):
            (live / "rules").mkdir(parents=True, exist_ok=True)
            (live / "rules" / "gone.md").write_text(text)
            self.install("bak")
        found = sorted(p.read_text() for p in (live / "backups" / "rules").rglob("gone.md*"))
        self.assertEqual(found, ["first\n", "second\n"])

    # covers: spec 0077 AC-1 live measure (verify sums live CLAUDE.md plus rules/*.md and fails over 20000, printing it)
    def test_live_size_check(self):
        _, _, r = self.install("small")
        self.assertIn("live always loaded text: 4 characters (limit 20000)", r.stdout, r.stdout + r.stderr)
        (self.repo / "claude-home" / "rules" / "big.md").write_text("x" * 20000)
        _, _, r = self.install("big")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("IS 20004 CHARACTERS", r.stderr)


class TestHookFiles(Scratch):
    # covers: row 105 (verify runs the hook file check last and exits non zero naming a settings.json hook command
    # whose file is missing after install; ~ and $HOME expand, an interpreter before the path is skipped, a command
    # that is no path and a hook under the live skills folder are left alone; every other self check still ran)
    def stub_verify(self):
        for f in ("scripts/gen-agent-index.py", "scripts/spec-paths.py", "scripts/fb-ask.py", "scripts/start-gates.py",
                  "scripts/design-check.py", "scripts/issue-reread.py", "scripts/review-isolated.py",
                  "claude-home/skills/design/scripts/test-ledger.sh", "claude-home/skills/design/scripts/build-ramp.mjs"):
            (self.repo / f).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / f).write_text("")

    def test_missing_hook_file(self):
        self.stub_verify()
        hooks = {"Stop": [{"hooks": [{"type": "command", "command": "bash ~/.claude/hooks/block-destructive.sh"},
                                     {"type": "command", "command": "node \"$HOME/.claude/hooks/context-monitor.js\""},
                                     {"type": "command", "command": "~/.claude/skills/jjstack/hooks/x.sh"},
                                     {"type": "command", "command": "paplay /no/such/sound.oga"}]}]}
        (self.repo / "claude-home" / "settings.json").write_text(json.dumps({"hooks": hooks}))
        _, _, r = self.install("ok")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("hook files: every settings.json hook command names a file that exists", r.stdout,
                      r.stdout + r.stderr)
        hooks["Stop"][0]["hooks"].append({"type": "command", "command": "~/.claude/hooks/gone.sh --x"})
        (self.repo / "claude-home" / "settings.json").write_text(json.dumps({"hooks": hooks}))
        home, _, r = self.install("gone")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(f"missing hook file: {home}/.claude/hooks/gone.sh", r.stderr, r.stdout + r.stderr)
        self.assertIn("HOOK FILES MISSING", r.stderr)
        self.assertIn("spec-paths: all self-checks passed", r.stdout)
        self.assertNotIn("sound.oga", r.stderr)
        self.assertNotIn("jjstack", r.stderr)


class TestDryRun(unittest.TestCase):
    # covers: spec 0020 AC-12, retired 2026-10-22 (the real install.sh --dry-run exits 0, no longer copies or links
    # the runner, and writes nothing under the home folder)
    def test_install_sh_dry_run_names_no_runner_copy(self):
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, tmp)
        home = tmp / "home"
        env = {**os.environ, "HOME": str(home), "CLAUDE_LIVE_DIR": str(tmp / "live")}
        r = subprocess.run(["bash", str(REPO / "bin/install.sh"), "--dry-run"], capture_output=True, text=True, env=env,
                           stdin=subprocess.DEVNULL, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("runner/*.py", r.stdout)
        self.assertNotIn(f"{home}/.local/bin/wf", r.stdout)
        self.assertFalse((home / ".local" / "share" / "wf").exists())
        self.assertFalse((tmp / "live").exists())


if __name__ == "__main__":
    unittest.main()
