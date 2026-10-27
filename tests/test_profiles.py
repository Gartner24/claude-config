"""Spec 0081 PR A: profile files, install from core plus a profile, the overwrite check, sync routing, the profile
command. Scratch repos and temp live trees only, never ~/.claude."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_install


class Scratch(test_install.Scratch):
    def setUp(self):
        super().setUp()
        # the verify step's other self checks are not under test here
        test_install.TestHookFiles.stub_verify(self)

REPO = Path(__file__).resolve().parents[1]


def load_tool(repo, live):
    """claude-config.py imported against a repo and a live tree (it reads both at import)."""
    old = {k: os.environ.get(k) for k in ("CLAUDE_CONFIG_REPO", "CLAUDE_LIVE_DIR")}
    os.environ.update(CLAUDE_CONFIG_REPO=str(repo), CLAUDE_LIVE_DIR=str(live))
    try:
        spec = importlib.util.spec_from_file_location("claude_config_tool", REPO / "tools/bin/claude-config.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class TestProfileFiles(unittest.TestCase):
    # covers: AC-1 (every profile in the repo is valid), AC-13 (engineer owns all, creator does not)
    def test_repo_profiles_valid(self):
        tool = load_tool(REPO, Path(tempfile.gettempdir()) / "no-live")
        self.assertIn("engineer", tool.profile_names())
        self.assertIn("creator", tool.profile_names())
        for name in tool.profile_names():
            with self.subTest(profile=name):
                self.assertEqual(tool.profile_problems(name), [])
        eng, cre = tool.load_profile("engineer"), tool.load_profile("creator")
        self.assertEqual((eng["owner"], eng["editable"]), (True, ["**"]))
        self.assertEqual((cre["owner"], cre["skills"], cre["rules"], cre["hooks_off"]),
                         (False, eng["skills"], eng["rules"], []))

    # covers: AC-3 (skillOverrides moved out of the core settings into engineer; engineer lists every core rule, so
    # its rules/ is byte for byte the core's)
    def test_engineer_is_today(self):
        tool = load_tool(REPO, Path(tempfile.gettempdir()) / "no-live")
        core = json.loads((REPO / "claude-home/settings.json").read_text())
        self.assertNotIn("skillOverrides", core)
        eng = tool.load_profile("engineer")
        self.assertEqual(sorted(eng["rules"]), sorted(p.name for p in (REPO / "claude-home/rules").glob("*.md")))
        self.assertEqual(eng["hooks_off"], [])
        self.assertEqual(list((REPO / "profiles/engineer/rules").glob("*.md")), [])

    # covers: AC-1 (the validator names each broken field)
    def test_validator(self):
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "claude-home/rules").mkdir(parents=True)
        (tmp / "claude-home/hooks").mkdir()
        (tmp / "claude-home/rules/a.md").write_text("a\n")
        (tmp / "claude-home/hooks/h.py").write_text("")
        (tmp / "claude-home/hooks/profile-lock.py").write_text("")
        good = {"name": "p", "description": "d", "owner": False, "base": "", "skills": {"s": "on"}, "rules": ["a.md"],
                "hooks_off": ["h.py"], "editable": []}
        bad = [({"name": "q"}, "not the folder name"), ({"rules": ["b.md"]}, "rule b.md"),
               ({"skills": {"s": "off"}}, "skill s"), ({"base": "gone"}, "base gone"),
               ({"hooks_off": ["profile-lock.py"]}, "hooks_off profile-lock.py"), ({"hooks_off": ["x.sh"]}, "hooks_off x.sh"),
               ({"owner": "yes"}, "owner missing or not bool")]
        tool = load_tool(tmp, tmp / "live")
        (tmp / "profiles/p").mkdir(parents=True)
        (tmp / "profiles/p/profile.json").write_text(json.dumps(good))
        self.assertEqual(tool.profile_problems("p"), [])
        for over, word in bad:
            with self.subTest(over=over):
                (tmp / "profiles/p/profile.json").write_text(json.dumps({**good, **over}))
                self.assertTrue(any(word in p for p in tool.profile_problems("p")), tool.profile_problems("p"))
        p = dict(good)
        del p["editable"]
        (tmp / "profiles/p/profile.json").write_text(json.dumps(p))
        self.assertIn("p: editable missing or not list", tool.profile_problems("p"))


class TestInstallProfile(Scratch):
    def setUp(self):
        super().setUp()
        rules = self.repo / "claude-home" / "rules"
        (rules / "a.md").write_text("a\n")
        (rules / "b.md").write_text("b\n")
        (rules / "ecc" / "py").mkdir(parents=True)
        (rules / "ecc" / "py" / "index.md").write_text("ecc\n")
        hooks = {"Stop": [{"hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/skill-rules.py"},
                                     {"type": "command", "command": "bash ~/.claude/hooks/block-destructive.sh"}]},
                          {"hooks": [{"type": "command", "command": "~/.claude/hooks/live-tick.py"}]}]}
        (self.repo / "claude-home" / "settings.json").write_text(json.dumps({"hooks": hooks, "x": "/home/santiago/y"}))
        self.profile()
        self.profile("creator", owner=False, rules=["a.md"], skills={"design": "on", "figma-use": "name-only"},
                     hooks_off=["live-tick.py", "block-destructive.sh"])
        (self.repo / "profiles" / "creator" / "rules" / "own.md").write_text("own\n")

    def run_install(self, home, *args):
        live = home / ".claude"
        env = {**os.environ, "HOME": str(home), "CLAUDE_LIVE_DIR": str(live), "GIT_CONFIG_GLOBAL": "/dev/null"}
        env.pop("WF_STAGE", None)
        return live, subprocess.run(["bash", str(self.repo / "tools/bin/install.sh"), *args], env=env,
                                    capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)

    # covers: AC-2 (rules: listed core files, subfolders whole, the profile's own; skillOverrides from skills; hooks_off
    # removed, empty groups dropped; CLAUDE.md always installed; state written with repo), AC-4 (state picks the next)
    def test_creator_build(self):
        home = self.tmp / "h"
        (home / ".claude").mkdir(parents=True)
        (home / ".claude" / "CLAUDE.md").write_text("# old\n")
        live, r = self.run_install(home, "--profile", "creator", "--accept-overwrite")
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, out)
        self.assertIn("profile: creator (from --profile)", r.stdout)
        self.assertEqual(sorted(p.relative_to(live / "rules").as_posix() for p in (live / "rules").rglob("*") if p.is_file()),
                         ["a.md", "ecc/py/index.md", "own.md"], out)
        s = json.loads((live / "settings.json").read_text())
        self.assertEqual(s["skillOverrides"], {"design": "on", "figma-use": "name-only"})
        self.assertEqual(s["hooks"], {"Stop": [{"hooks": [{"type": "command",
                                                            "command": "python3 ~/.claude/hooks/skill-rules.py"}]}]})
        self.assertEqual(s["x"], f"{home}/y")
        self.assertEqual((live / "CLAUDE.md").read_text(), "# r\n")
        state = json.loads((live / "state" / "profile.json").read_text())
        self.assertEqual((state["name"], state["owner"], state["repo"]), ("creator", False, str(self.repo)))
        self.assertEqual(list((live / "state").glob("*.tmp")), [])
        # AC-4: no --profile uses the state file
        live, r = self.run_install(home, "--accept-overwrite")
        self.assertIn("profile: creator (from state/profile.json)", r.stdout, r.stdout + r.stderr)
        # AC-4: no state file, engineer, and it says so
        _, r = self.run_install(self.tmp / "h2")
        self.assertIn("profile: engineer (from default)", r.stdout, r.stdout + r.stderr)

    # covers: AC-2 (an unknown profile exits 2 naming the known ones, before anything is written)
    def test_unknown_profile(self):
        live, r = self.run_install(self.tmp / "h", "--profile", "nobody")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("unknown profile: nobody; known: creator, engineer", r.stderr)
        self.assertFalse(live.exists())
        live, r = self.run_install(self.tmp / "h", "--profile")
        self.assertEqual((r.returncode, r.stderr.strip()), (2, "install.sh: --profile needs a name"))
        self.assertFalse(live.exists())

    # covers: AC-2 (a required hook missing from the repo stops the build before anything is written live; PR 239 review)
    def test_missing_hook_writes_nothing(self):
        home = self.tmp / "h"
        (home / ".claude" / "rules").mkdir(parents=True)
        (home / ".claude" / "rules" / "old.md").write_text("old\n")
        (self.repo / "claude-home" / "hooks" / "plain-panel.py").unlink()
        live, r = self.run_install(home, "--accept-overwrite")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("claude-home/hooks/plain-panel.py is missing", r.stderr)
        self.assertEqual(sorted(p.relative_to(live).as_posix() for p in live.rglob("*")), ["rules", "rules/old.md"])

    # covers: AC-5 (a second install lists nothing and exits 0; a live edit and a live only rule are listed, nothing is
    # written and it exits 3; a dry run lists and writes nothing; --accept-overwrite writes)
    def test_overwrite_check(self):
        home = self.tmp / "h"
        live, r = self.run_install(home)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        live, r = self.run_install(home)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("overwrite: changed", r.stdout)
        self.assertNotIn("overwrite: lost", r.stdout)
        (live / "rules" / "a.md").write_text("a\nmine\n")
        (live / "rules" / "extra.md").write_text("x\n")
        s = json.loads((live / "settings.json").read_text())
        s["x"] = "z"
        (live / "settings.json").write_text(json.dumps(s))
        before = {p: p.read_bytes() for p in live.rglob("*") if p.is_file()}
        for args, code in (((), 3), (("--dry-run",), 0)):
            with self.subTest(args=args):
                _, r = self.run_install(home, *args)
                self.assertEqual(r.returncode, code, r.stdout + r.stderr)
                self.assertIn("overwrite: changed rules/a.md +1/-0", r.stdout)
                self.assertIn("overwrite: changed settings.json +1/-1", r.stdout)
                self.assertIn("overwrite: lost rules/extra.md", r.stdout)
                self.assertEqual({p: p.read_bytes() for p in live.rglob("*") if p.is_file()}, before)
        _, r = self.run_install(home, "--accept-overwrite")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((live / "rules" / "a.md").read_text(), "a\n")
        self.assertFalse((live / "rules" / "extra.md").exists())


class TestSyncProfile(Scratch):
    def setUp(self):
        super().setUp()
        shutil.copy(REPO / "tools/bin/sync.sh", self.repo / "tools/bin/sync.sh")
        shutil.copy(REPO / "tools/scripts/private-names.py", self.repo / "tools/scripts/private-names.py")
        (self.repo / "claude-home" / "rules" / "core.md").write_text("core\n")
        (self.repo / "claude-home" / "rules" / "unlisted.md").write_text("unlisted\n")
        self.profile(rules=["core.md"], skills={"a": "on"})
        (self.repo / "profiles" / "engineer" / "rules" / "own.md").write_text("own\n")
        self.profile("creator", owner=False, rules=["core.md"])
        self.live = self.tmp / "live"
        for d in ("agents", "rules", "hooks", "scripts", "private", "state"):
            (self.live / d).mkdir(parents=True)
        (self.live / "private" / "names.txt").write_text("zorblexq\n")
        (self.live / "CLAUDE.md").write_text("# r\n")
        (self.live / "settings.json").write_text(json.dumps({"skillOverrides": {"a": "name-only", "b": "on"}, "k": 1}))
        (self.live / "settings.local.json").write_text("{}")
        (self.live / "rules" / "core.md").write_text("core edited\n")
        (self.live / "rules" / "own.md").write_text("own edited\n")
        (self.live / "rules" / "new.md").write_text("new\n")
        for f in ("hooks/block-destructive.sh", "hooks/review-stack-pre-push", "hooks/plain-panel.py"):
            (self.live / f).write_text("#!/bin/sh\n")

    def sync(self, active):
        (self.live / "state" / "profile.json").write_text(json.dumps({"name": active}))
        env = {**os.environ, "CLAUDE_LIVE_DIR": str(self.live), "GIT_CONFIG_GLOBAL": "/dev/null"}
        return subprocess.run(["bash", str(self.repo / "tools/bin/sync.sh")], env=env, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=120)

    def tree(self):
        return {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file() and ".git" not in p.parts}

    # covers: AC-6 (an owner false profile copies nothing and says why, exit 0)
    def test_not_owner(self):
        before = self.tree()
        r = self.sync("creator")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.strip(), "sync: creator is not an owner profile; changes reach the repo through a PR")
        self.assertEqual(self.tree(), before)
        self.assertFalse((self.live / "private" / "settings.json").exists())

    # covers: PR 239 review (an active profile that cannot be read fails the sync loudly, never a silent exit 0)
    def test_unreadable_profile(self):
        (self.repo / "profiles" / "engineer" / "profile.json").write_text("{not json")
        before = self.tree()
        r = self.sync("engineer")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("sync refused: the active profile could not be read", r.stderr)
        self.assertEqual(self.tree(), before)

    # covers: AC-6 (owner: skillOverrides into the profile, not the core settings; a core rule back to the core, the
    # profile's own rule back to its folder; a new live rule to the core and the profile's list)
    def test_owner(self):
        r = self.sync("engineer")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        p = json.loads((self.repo / "profiles" / "engineer" / "profile.json").read_text())
        self.assertEqual(p["skills"], {"a": "name-only", "b": "on"})
        self.assertEqual(p["rules"], ["core.md", "new.md"])
        self.assertEqual(json.loads((self.repo / "claude-home" / "settings.json").read_text()), {"k": 1})
        rules = self.repo / "claude-home" / "rules"
        self.assertEqual((rules / "core.md").read_text(), "core edited\n")
        self.assertEqual((rules / "new.md").read_text(), "new\n")
        self.assertFalse((rules / "own.md").exists())
        self.assertEqual((self.repo / "profiles" / "engineer" / "rules" / "own.md").read_text(), "own edited\n")
        self.assertNotIn("unlisted.md", r.stdout)


class TestProfileCommand(Scratch):
    def tool(self, *args, live=None):
        live = live or self.tmp / "home-cmd" / ".claude"
        env = {**os.environ, "HOME": str(live.parent), "CLAUDE_LIVE_DIR": str(live), "GIT_CONFIG_GLOBAL": "/dev/null",
               "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        env.pop("WF_STAGE", None)
        return subprocess.run([sys.executable, str(self.repo / "tools/bin/claude-config.py"), *args], env=env,
                              capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)

    # covers: AC-7 (profile <name> installs and says open a new chat; profile lists, the active one marked)
    def test_switch_and_list(self):
        self.profile("creator", owner=False, description="for videos")
        r = self.tool("profile", "creator")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.rstrip().endswith("profile creator active: open a new chat"), r.stdout)
        r = self.tool("profile")
        self.assertEqual(r.stdout.splitlines(), ["* creator: for videos", "  engineer: d"])
        self.assertEqual(self.tool("profile", "nobody").returncode, 2)

    # covers: AC-8 (update refuses a dirty repo naming the file; a clean one pulls fast forward and reinstalls the
    # active profile, never another)
    def test_update(self):
        git = lambda *a, cwd=self.repo: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True,
                                                       env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null",
                                                            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                                            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
        self.profile("creator", owner=False)
        git("add", "-A")
        git("commit", "-q", "-m", "start")
        origin = self.tmp / "origin.git"
        git("init", "-q", "--bare", str(origin), cwd=self.tmp)
        git("remote", "add", "origin", str(origin))
        git("push", "-q", "-u", "origin", "HEAD")
        other = self.tmp / "other"
        git("clone", "-q", str(origin), str(other), cwd=self.tmp)
        (other / "claude-home" / "rules").mkdir(parents=True, exist_ok=True)
        (other / "claude-home" / "rules" / "pulled.md").write_text("pulled\n")
        git("add", "-A", cwd=other)
        git("commit", "-q", "-m", "more", cwd=other)
        git("push", "-q", "origin", "HEAD", cwd=other)
        self.assertEqual(self.tool("profile", "creator").returncode, 0)
        (self.repo / "dirty.txt").write_text("x\n")
        r = self.tool("profile", "update")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("?? dirty.txt", r.stdout)
        self.assertFalse((self.repo / "claude-home" / "rules" / "pulled.md").exists())
        (self.repo / "dirty.txt").unlink()
        r = self.tool("profile", "update")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.repo / "claude-home" / "rules" / "pulled.md").exists())
        self.assertIn("profile: creator (from --profile)", r.stdout)


HOOK = REPO / "claude-home" / "hooks" / "profile-lock.py"


class TestLockHook(unittest.TestCase):
    # covers: AC-14 (the self check: allowed outside, editable, denied core and own shared profile, owner, links)
    def test_self_check(self):
        r = subprocess.run([sys.executable, str(HOOK), "--test"], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("profile-lock: all self-checks passed", r.stdout)

    # covers: AC-10 (wired on the four file tools in settings like the other core hooks, copied by install)
    def test_wired(self):
        pre = json.loads((REPO / "claude-home/settings.json").read_text())["hooks"]["PreToolUse"]
        groups = [g for g in pre if any("hooks/profile-lock.py" in c["command"] for c in g["hooks"])]
        self.assertEqual([g["matcher"] for g in groups], ["Edit|Write|MultiEdit|NotebookEdit"])
        tool = load_tool(REPO, Path(tempfile.gettempdir()) / "no-live")
        self.assertIn("hooks/profile-lock.py", tool.COPIED_FILES)
        self.assertIn("hooks/profile-lock.py", (REPO / "tools/bin/install.sh").read_text())
        self.assertIn("hooks/profile-lock.py", (REPO / "tools/bin/sync.sh").read_text())

    # covers: AC-13 (creator's edit list is the spec's, engineer may edit everything)
    def test_creator_editable(self):
        cre = json.loads((REPO / "profiles/creator/profile.json").read_text())
        skills = ["design", "assets", "brand-system", "nano-banana", "video-to-website", "voice-dna", "content-ops",
                  "anti-ai-writing", "watch-reels"]
        patches = ["high-end-visual-design", "minimalist-ui", "industrial-brutalist-ui"]
        self.assertEqual(cre["editable"], [f"claude-home/skills/{s}/**" for s in skills]
                         + [f"tools/config/patches/{p}.patch" for p in patches] + ["profiles/custom-*/**"])
        self.assertEqual(cre["owner"], False)


class TestCustomProfile(Scratch):
    def setUp(self):
        super().setUp()
        (self.repo / "claude-home" / "hooks" / "profile-lock.py").write_text(HOOK.read_text())
        self.profile("creator", owner=False, editable=["claude-home/skills/design/**", "profiles/custom-*/**"])
        self.live = self.tmp / "home-c" / ".claude"

    def tool(self, *args):
        env = {**os.environ, "HOME": str(self.live.parent), "CLAUDE_LIVE_DIR": str(self.live), "GIT_CONFIG_GLOBAL": "/dev/null"}
        env.pop("WF_STAGE", None)
        return subprocess.run([sys.executable, str(self.repo / "tools/bin/claude-config.py"), *args], env=env,
                              capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)

    def write(self, rel):
        data = {"tool_name": "Write", "tool_input": {"file_path": str(self.repo / rel)}}
        return subprocess.run([sys.executable, str(self.live / "hooks" / "profile-lock.py")], input=json.dumps(data),
                              capture_output=True, text=True, env={**os.environ, "CLAUDE_LIVE_DIR": str(self.live)})

    # covers: AC-10 (as creator, core denied, an editable skill allowed), AC-11 (its own shared folder denied with the
    # custom hint), AC-12 (custom copy: name, base, owner, edit list, switched; its rules writable, its profile.json
    # not; a bad or taken name exits 2; a copy made from a custom profile records it as base)
    def test_custom_flow(self):
        self.assertEqual(self.tool("profile", "creator").returncode, 0)
        r = self.write("tools/bin/install.sh")
        self.assertEqual((r.returncode, r.stderr.strip()),
                         (2, "locked core (profile creator): ask the owner to change tools/bin/install.sh"))
        self.assertEqual(self.write("claude-home/skills/design/SKILL.md").returncode, 0)
        r = self.write("profiles/creator/rules/x.md")
        self.assertEqual(r.returncode, 2)
        self.assertIn("creator is shared. Make the person's own copy now", r.stderr)
        r = self.tool("profile", "custom", "ana")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("profile custom-ana active: open a new chat", r.stdout)
        p = json.loads((self.repo / "profiles/custom-ana/profile.json").read_text())
        self.assertEqual((p["name"], p["base"], p["owner"]), ("custom-ana", "creator", True))
        self.assertEqual(p["editable"], ["claude-home/skills/design/**", "profiles/custom-*/**",
                                         "profiles/custom-ana/rules/**"])
        self.assertEqual(json.loads((self.live / "state/profile.json").read_text())["name"], "custom-ana")
        self.assertEqual(self.write("profiles/custom-ana/rules/x.md").returncode, 0)
        self.assertEqual(self.write("profiles/custom-ana/profile.json").returncode, 2)
        self.assertEqual(self.write("tools/bin/install.sh").returncode, 2)
        for bad in ("Ana", "a" * 31, "ana"):
            with self.subTest(bad=bad):
                self.assertEqual(self.tool("profile", "custom", bad).returncode, 2)
        self.assertEqual(self.tool("profile", "custom", "bo").returncode, 0)
        self.assertEqual(json.loads((self.repo / "profiles/custom-bo/profile.json").read_text())["base"], "custom-ana")


class TestPortableShell(unittest.TestCase):
    # covers: AC-9b (no GNU only construct in the shell this spec adds or changes; the lines listed are older and
    # row 119 removes them)
    KNOWN = {
        ("tools/bin/install.sh", '    [ -L "$dst" ] && [ "$(readlink -f "$dst")" = "$(readlink -f "$src")" ] \\'),
        ("tools/bin/install.sh", '      [ "$(readlink -f "$dst")" = "$(readlink -f "$checker")" ] && act=refreshed'),
    }
    GNU = re.compile(r"find .*-printf|readlink -f|sed -i(\s|$)|\$\{\w+\^\^\}|declare -A|(^|[\s;(])timeout\s")

    def test_no_gnu_only(self):
        hits = []
        for rel in ("tools/bin/install.sh", "tools/bin/sync.sh"):
            for line in (REPO / rel).read_text().splitlines():
                if self.GNU.search(line) and (rel, line) not in self.KNOWN:
                    hits.append(f"{rel}: {line.strip()}")
        self.assertEqual(hits, [], "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
