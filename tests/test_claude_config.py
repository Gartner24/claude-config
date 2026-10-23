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

from test_skill_scan import fake_bin, issue

REAL = Path(__file__).resolve().parents[1]
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
        # update --apply runs skill-scan (spec 0054); a fake skillspector keeps the real one out
        self.ss_bin, self.ss_data = fake_bin(self.tmp)
        self.env = {**os.environ, **ENV, "CLAUDE_CONFIG_REPO": str(self.repo), "CLAUDE_LIVE_DIR": str(self.live),
                    "FAKE_SS": str(self.ss_data), "PATH": f"{self.ss_bin}:{os.environ['PATH']}"}
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

    def install_mod(self):
        """A mod: upstream folder with no SKILL.md, live copy edited, entry and patch written by sync."""
        self.pinned = self.commit({"mods/m/a.txt": "one\ntwo\nthree\n", "LICENSE": "MIT License\nCopyright (c) Someone\n"})
        m = self.live / "skills" / "m"
        m.mkdir()
        (m / "a.txt").write_text("one\ntwo mine\nthree\n")
        base = self.tmp / "base_m"
        base.mkdir()
        (base / "a.txt").write_text("one\ntwo\nthree\n")
        self.manifest({"m": {"kind": "skill", "status": "downloaded", "source": str(self.up), "path": "mods/m",
                             "pinned": self.pinned, "base_hash": cc.folder_hash(base), "license": "MIT",
                             "publish": True, "patch": None, "fetch": "git", "install": "x", "framework": None}})
        r = self.tool("patches")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return m

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

    # covers: spec 0068 AC-6 (a mod at path "." with no SKILL.md is rebuilt from git archive of the whole repo)
    def test_rebuild_whole_repo_mod(self):
        self.pinned = self.commit({"hooks/a.ts": "one\ntwo\n", "README.md": "r\n"})
        base = self.tmp / "base_root"
        shutil.copytree(self.up, base, ignore=shutil.ignore_patterns(".git"))
        m = self.live / "skills" / "m"
        shutil.copytree(base, m)
        (m / "hooks" / "a.ts").write_text("one\ntwo mine\n")
        self.manifest({"m": {"kind": "skill", "status": "downloaded", "source": str(self.up), "path": ".",
                             "pinned": self.pinned, "base_hash": cc.folder_hash(base), "license": "MIT",
                             "publish": True, "patch": None, "fetch": "git", "install": "x", "framework": None}})
        self.assertEqual(self.tool("patches").returncode, 0)
        patch = (self.repo / "config" / "patches" / "m.patch").read_text()
        self.assertEqual([ln for ln in patch.splitlines() if ln.startswith("diff --git")],
                         ["diff --git a/hooks/a.ts b/hooks/a.ts"])
        before = cc.folder_hash(m)
        shutil.rmtree(m)
        r = self.tool("restore")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(cc.folder_hash(m), before)

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

    # covers: a first install (live missing, or an empty folder) installs upstream as is: no merge, no patch.
    # This used to read the missing folder as "every file deleted", install nothing and store a delete-all patch.
    def test_first_install(self):
        base = self.tmp / "base"
        base.mkdir()
        (base / "SKILL.md").write_text(SKILL)
        (base / "ref.md").write_text("ref\n")
        entry = {"kind": "skill", "status": "downloaded", "source": str(self.up), "path": "skills/s",
                 "pinned": self.pinned, "base_hash": cc.folder_hash(base), "license": "MIT",
                 "publish": True, "patch": None, "fetch": "git", "install": "x", "framework": None}
        s = self.live / "skills" / "s"
        for make_empty in (False, True):
            shutil.rmtree(s, ignore_errors=True)
            if make_empty:
                s.mkdir()
            self.manifest({"s": dict(entry)})
            r = self.tool("update", "--apply", "s")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual((s / "SKILL.md").read_text(), SKILL, make_empty)
            self.assertNotIn("(edited)", r.stdout)
            e = self.manifest()["entries"]["s"]
            self.assertEqual((e["status"], e["patch"]), ("downloaded", None))
            self.assertFalse((self.repo / "config" / "patches" / "s.patch").exists())

    # covers: spec 0054 AC-7 (the merged folder is scanned against the live copy before it installs, and
    # installs even with findings)
    def test_scan_before_install(self):
        s = self.install_edited()
        self.commit({"skills/s/SKILL.md": SKILL.replace("line 5\n", "line 5 up\n")})
        # the fake keys findings by folder name: the live s has none, any other folder (the merged one) has one
        cfg = json.loads((self.ss_data / "config.json").read_text())
        cfg["targets"] = {"s": {"issues": []}, "*": {"issues": [issue()]}}
        (self.ss_data / "config.json").write_text(json.dumps(cfg))
        r = self.tool("update", "--apply", "s")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("line 5 up", (s / "SKILL.md").read_text())
        out = r.stdout
        self.assertIn("s: skill scan, new serious findings (static):\n  s  HIGH Tainted flow (line N) @ scripts/a.py:7", out)
        self.assertLess(out.index("s: skill scan"), out.index("s: installed upstream"), out)
        scanned = [json.loads(x)["argv"][1] for x in (self.ss_data / "log").read_text().splitlines()]
        self.assertEqual(len(scanned), 2)
        self.assertIn(os.path.realpath(s), scanned)

    # covers: spec 0054 AC-7 (no skillspector: one line, installs anyway)
    def test_scan_missing_installs(self):
        s = self.install_edited()
        self.commit({"skills/s/SKILL.md": SKILL.replace("line 5\n", "line 5 up\n")})
        (self.ss_bin / "skillspector").unlink()
        self.env["PATH"] = f"{self.ss_bin}:{Path(sys.executable).parent}:/usr/bin"
        r = self.tool("update", "--apply", "s")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("s: skill scan: skill-scan: skillspector not found on PATH\n", r.stdout)
        self.assertIn("line 5 up", (s / "SKILL.md").read_text())

    # covers: AC-10 (conflict: exit 2, conflicts folder, live and manifest byte for byte unchanged)
    def test_conflict_then_resolved(self):
        self.install_edited()
        self.commit({"skills/s/SKILL.md": SKILL.replace("line 2\n", "line 2 up\n")})
        before = self.state()
        r = self.tool("update", "--apply", "s")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertEqual(self.state(), before)
        self.assertFalse((self.ss_data / "log").exists(), "a conflict installs nothing, so spec 0054 scans nothing")
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

    # an upstream folder replaced by a link (a rename) is reported, never a crash
    def test_renamed_to_link(self):
        self.install_edited()
        shutil.move(self.up / "skills" / "s", self.up / "skills" / "t")
        (self.up / "skills" / "s").symlink_to("t")
        self.git(self.up, "add", "-A")
        self.git(self.up, "commit", "-q", "-m", "rename")
        r = self.tool("update", "--plan")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("s: source not reached, nothing changes: skills/s is a link to t", r.stdout)

    def plain(self, status="downloaded", fetch="git", base_hash=None):
        """An unedited live skill at pinned with its manifest entry."""
        s = self.live / "skills" / "s"
        s.mkdir()
        (s / "SKILL.md").write_text(SKILL)
        (s / "ref.md").write_text("ref\n")
        pinned = None if status == "unpinned" else self.pinned
        self.manifest({"s": {"kind": "skill", "status": status, "source": str(self.up), "path": "skills/s",
                             "pinned": pinned, "base_hash": base_hash or (None if pinned is None else cc.folder_hash(s)),
                             "license": "MIT", "publish": True, "patch": None, "fetch": fetch, "install": "x",
                             "framework": None}})
        return s

    # covers: AC-10 (a downloaded entry is replaced with upstream now; pinned moves, no patch)
    def test_downloaded_replaced(self):
        s = self.plain()
        head = self.commit({"skills/s/SKILL.md": SKILL + "line 7\n", "skills/s/ref.md": None})
        r = self.tool("update", "--apply", "s")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((s / "SKILL.md").read_text(), SKILL + "line 7\n")
        self.assertFalse((s / "ref.md").exists())
        e = self.manifest()["entries"]["s"]
        self.assertEqual((e["pinned"], e["status"], e["patch"], e["base_hash"]), (head, "downloaded", None, cc.folder_hash(s)))

    # covers: AC-10 (an unpinned entry, on yes, is replaced and becomes downloaded)
    def test_unpinned_becomes_downloaded(self):
        s = self.plain(status="unpinned")
        (s / "SKILL.md").write_text("mine, no known base\n")
        head = self.commit({"skills/s/SKILL.md": SKILL + "line 7\n"})
        self.assertIn("s (unpinned): upstream", self.tool("update", "--plan").stdout)
        r = self.tool("update", "--apply", "s")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((s / "SKILL.md").read_text(), SKILL + "line 7\n")
        e = self.manifest()["entries"]["s"]
        self.assertEqual((e["pinned"], e["status"]), (head, "downloaded"))

    # covers: AC-10 (--apply refuses a fetch: manual entry; the plan lists it as update by hand)
    def test_manual_refused(self):
        self.plain(fetch="manual")
        self.commit({"skills/s/SKILL.md": SKILL + "line 7\n"})
        before = self.state()
        self.assertEqual(self.tool("update", "--apply", "s").returncode, 1)
        self.assertEqual(self.state(), before)
        self.assertIn("s: update by hand, not checked", self.tool("update", "--plan").stdout)

    # covers: AC-10 (the base fetched again by commit no longer hashes to base_hash: reported, nothing changes)
    def test_base_moved(self):
        self.plain(base_hash="0" * 64)
        self.commit({"skills/s/SKILL.md": SKILL + "line 7\n"})
        before = self.state()
        r = self.tool("update", "--apply", "s")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("no longer hashes to base_hash", r.stdout)
        self.assertEqual(self.state(), before)

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

    # covers: AC-9 (a skills folder with no SKILL.md is not a skill, so drift does not report it)
    def test_non_skill_folder(self):
        support = self.live / "skills" / "shared"
        support.mkdir()
        (support / "ref.md").write_text("ref\n")
        r = self.tool("drift")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "drift: none"), r.stdout + r.stderr)

    # covers: spec 0068 AC-6 (a folder with no SKILL.md but a manifest entry is checked, not "missing live";
    # one with no entry is still not a skill)
    def test_mod_folder_with_entry(self):
        m = self.install_mod()
        support = self.live / "skills" / "shared"
        support.mkdir()
        (support / "ref.md").write_text("ref\n")
        r = self.tool("drift")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "drift: none"), r.stdout + r.stderr)
        (m / "a.txt").write_text("one\ntwo\nthree\n")
        self.assertIn("m: your edit is no longer in it", self.tool("drift").stdout)

    # covers: AC-9 (settings compare after the sync transform: the home path swap and the ignored keys are not
    # drift, a real difference is, under kind setting)
    def test_settings(self):
        home = self.tmp / "home"
        home.mkdir()
        self.env["HOME"] = str(home)
        (self.repo / "config" / "drift-ignore.json").write_text(json.dumps(["skillOverrides.x"]))
        repo = {"model": "a", "hooks": {"Stop": cc.AUTHOR_HOME + "/.claude/hooks/h.sh"},
                "skillOverrides": {"x": "off", "y": "on"}}
        (self.repo / "claude-home" / "settings.json").write_text(json.dumps(repo))
        live = {"model": "a", "hooks": {"Stop": f"{home}/.claude/hooks/h.sh"}, "skillOverrides": {"x": "on", "y": "on"}}
        (self.live / "settings.json").write_text(json.dumps(live))
        r = self.tool("drift")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "drift: none"), r.stdout + r.stderr)
        live["model"] = "b"
        live["skillOverrides"]["y"] = "off"
        (self.live / "settings.json").write_text(json.dumps(live))
        r = self.tool("drift")
        self.assertEqual(r.returncode, 1)
        self.assertIn("setting:\n  settings.json: model: differs\n  settings.json: skillOverrides: differs", r.stdout)

    # covers: row 105 (a live settings.json hook command naming a missing file is drift, named by its path)
    def test_missing_hook_file(self):
        home = self.tmp / "home"
        (home / ".claude" / "hooks").mkdir(parents=True)
        (home / ".claude" / "hooks" / "here.sh").write_text("#!/bin/sh\n")
        self.env["HOME"] = str(home)
        cmds = ["bash ~/.claude/hooks/here.sh", "paplay /no/such.oga"]
        live = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": c} for c in cmds]}]}}
        (self.repo / "claude-home" / "settings.json").write_text(json.dumps(live))
        (self.live / "settings.json").write_text(json.dumps(live))
        r = self.tool("drift")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "drift: none"), r.stdout + r.stderr)
        live["hooks"]["Stop"][0]["hooks"].append({"type": "command", "command": "python3 $HOME/.claude/hooks/gone.py"})
        (self.repo / "claude-home" / "settings.json").write_text(json.dumps(live))
        (self.live / "settings.json").write_text(json.dumps(live))
        r = self.tool("drift")
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"hook:\n  {home}/.claude/hooks/gone.py: settings.json hook command names a missing file",
                      r.stdout)

    # covers: row 105 (hook-files on a live settings.json that does not parse says so and exits 2, not "missing")
    def test_hook_files_parse_error(self):
        (self.live / "settings.json").write_text("{not json")
        r = self.tool("hook-files")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("does not parse", r.stdout)
        self.assertNotIn("missing hook file", r.stdout)

    # covers: spec 0076 AC-6 (a workflow linked live is no drift; a real folder where the link belongs, a missing link
    # and a live only workflow are reported under kind workflow)
    def test_workflows(self):
        own = self.repo / "claude-home" / "workflows" / "w"
        own.mkdir(parents=True)
        (own / "CONTEXT.md").write_text("x\n")
        (self.live / "workflows").mkdir()
        (self.live / "workflows" / "w").symlink_to(own)
        r = self.tool("drift")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "drift: none"), r.stdout + r.stderr)
        (self.live / "workflows" / "w").unlink()
        r = self.tool("drift")
        self.assertIn("workflow:\n  w: missing live", r.stdout)
        (self.live / "workflows" / "w").mkdir()
        (self.live / "workflows" / "stray").mkdir()
        r = self.tool("drift")
        self.assertEqual(r.returncode, 1)
        self.assertIn("workflow:\n  stray: live only", r.stdout)
        self.assertIn("  w: in the repo, but live is not a link to it", r.stdout)

    # covers: spec 0076 AC-10 (drift and update --plan compare each template's follows commit with the icm-architect
    # pin: no entry, equal, moved; a template with no follows line is named too)
    def test_follows(self):
        t = self.repo / "claude-home" / "skills" / "workflow-builder" / "templates"
        t.mkdir(parents=True)
        (t / "CONTEXT.md").write_text("<!-- follows icm-architect aaa -->\n# x\n")
        (t / "workflow.js").write_text("// follows icm-architect aaa\nexport const meta = {}\n")
        none = "icm-architect not installed, templates not compared"
        for cmd in (("drift",), ("update", "--plan")):
            self.assertIn(none, self.tool(*cmd).stdout, cmd)
        entry = {"kind": "skill", "status": "downloaded", "source": "github:x/icm-architect", "path": ".",
                 "pinned": "aaa", "base_hash": None, "license": "MIT", "publish": True, "patch": None,
                 "fetch": "manual", "install": "x", "framework": None}
        self.manifest({"icm-architect": entry})
        for cmd in (("drift",), ("update", "--plan")):
            out = self.tool(*cmd).stdout
            self.assertNotIn("review workflow-builder templates", out, cmd)
            self.assertNotIn(none, out, cmd)
        self.manifest({"icm-architect": {**entry, "pinned": "bbb"}})
        want = "review workflow-builder templates: they follow icm-architect aaa, the pin is bbb"
        for cmd in (("drift",), ("update", "--plan")):
            self.assertIn(want, self.tool(*cmd).stdout, cmd)
        (t / "stage-CONTEXT.md").write_text("# no follows line\n")
        self.manifest({"icm-architect": entry})
        self.assertIn("they follow icm-architect (no follows line), the pin is aaa", self.tool("drift").stdout)

    # covers: AC-7 (the old override guard: a reinstall over an edited skill shows in drift)
    def test_override_lost(self):
        s = self.install_edited()
        self.assertEqual(self.tool("drift").returncode, 0, self.tool("drift").stdout)
        (s / "SKILL.md").write_text(SKILL)
        self.assertIn("s: your edit is no longer in it", self.tool("drift").stdout)


class TestWorkflowBuilderCheck(unittest.TestCase):
    # covers: spec 0076 AC-5 (check.py's self check runs in the suite: a good workflow and the filled templates pass,
    # each fixture's problem is reported)
    def test_self_check(self):
        r = subprocess.run([sys.executable, "-B", str(REAL / "claude-home" / "skills" / "workflow-builder" / "check.py"),
                            "--test"], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("check.py self check: ok", r.stdout)


class TestBuild(Case):
    # covers: AC-5, AC-6, AC-7, AC-8 happy path: an older pinned commit found by the history walk, a lock entry
    # edited after install pinned by its tree hash with a public patch, a cite only skill with nothing in the repo,
    # an untraceable one in the private store, and every live skill accounted for
    def test_build(self):
        self.git(self.up, "config", "uploadpack.allowFilter", "true")
        old = self.commit({"skills/a/SKILL.md": "---\ndescription: Does a. More.\n---\nA\n", "skills/b/SKILL.md": SKILL,
                           "skills/fig/SKILL.md": "fig\n", "LICENSE": "MIT\nPermission is hereby granted, free of charge\n"})
        tree_b = self.git(self.up, "rev-parse", f"{old}:skills/b")
        self.commit({"skills/a/SKILL.md": "---\ndescription: Does a. More.\n---\nA newer\n"})
        sk = self.live / "skills"
        for name, body in (("a", "---\ndescription: Does a. More.\n---\nA\n"), ("b", SKILL.replace("line 3", "mine")),
                           ("fig", "fig mine\n"), ("unknown", "who\n")):
            (sk / name).mkdir()
            (sk / name / "SKILL.md").write_text(body)
        own = self.repo / "claude-home" / "skills" / "own"
        own.mkdir()
        (own / "SKILL.md").write_text("own\n")
        (sk / "own").symlink_to(own)
        src = f"file://{self.up}"
        (self.repo / "docs" / "briefs").mkdir(parents=True)
        (self.repo / "docs" / "briefs" / "untraced-skills.md").write_text(
            f"# t\n\n## G\na\nSource: {src}, `skills/<name>/SKILL.md`. Confirmed.\nLicense: MIT (x).\n"
            f"Publish an edited copy: yes, keep the notice.\n\nfig\nSource: {src}, `skills/<name>/`.\nLicense: none.\n"
            f"Publish an edited copy: NO.\n\n## Formerly unclear\n- unknown: author UNKNOWN. Publish: no, cite only.\n")
        lock = self.tmp / "lock.json"
        lock.write_text(json.dumps({"skills": {"b": {"source": "x/y", "sourceType": "git", "sourceUrl": src,
                                                     "skillPath": "skills/b/SKILL.md", "skillFolderHash": tree_b}}}))
        self.manifest({})
        self.env.update(CLAUDE_CONFIG_LOCK=str(lock), XDG_CACHE_HOME=str(self.tmp / "cache"))
        r = self.tool("build")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("accounting: 0 skill(s)", r.stdout)
        e = self.manifest()["entries"]
        self.assertEqual((e["a"]["status"], e["a"]["pinned"], e["a"]["license"], e["a"]["description"]),
                         ("downloaded", old, "MIT", "Does a."))
        self.assertEqual((e["b"]["status"], e["b"]["pinned"], e["b"]["patch"]), ("edited", old, "config/patches/b.patch"))
        self.assertIn("+mine", (self.repo / "config" / "patches" / "b.patch").read_text())
        self.assertEqual((e["fig"]["status"], e["fig"]["publish"]), ("unpinned", False))
        self.assertEqual(sorted(p.name for p in (self.repo / "config" / "patches").iterdir()), ["b.patch"])
        self.assertTrue((self.live / "private" / "skills" / "fig" / "SKILL.md").exists())
        self.assertEqual((e["unknown"]["status"], e["unknown"]["install"]), ("source-unknown", None))
        self.assertTrue((self.live / "private" / "skills" / "unknown" / "SKILL.md").exists())
        self.assertNotIn("own", e)
        self.assertEqual(self.tool("drift").returncode, 0, self.tool("drift").stdout)
        notice = (self.repo / "docs" / "NOTICE.md").read_text()
        self.assertIn("Patched here: b.", notice)
        self.assertIn("SPDX-License-Identifier: MIT", notice)
        self.assertIn("Permission is hereby granted, free of charge", notice)
        not_redistributed = notice.split("## Not redistributed", 1)[1]
        self.assertIn("- fig:", not_redistributed)
        self.assertIn("- unknown: source unknown (unknown)", not_redistributed)
        self.assertNotIn("- a:", not_redistributed)

    # covers: review 2026-10-21 leftover (a source the main loop could not reach is reported once, not cloned again)
    def test_build_unreachable_reported_once(self):
        self.install_edited()
        lock = self.tmp / "lock.json"
        lock.write_text(json.dumps({"skills": {"s": {"source": "x/y", "sourceType": "git",
                                                     "sourceUrl": f"file://{self.up}", "skillPath": "skills/s/SKILL.md"}}}))
        shutil.rmtree(self.up)
        (self.repo / "docs").mkdir()
        self.env.update(CLAUDE_CONFIG_LOCK=str(lock), XDG_CACHE_HOME=str(self.tmp / "cache"))
        r = self.tool("build")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(r.stdout.count("not reached"), 1, r.stdout + r.stderr)

    # covers: spec 0068 AC-6 (a hand written edited entry whose live folder has no SKILL.md gets its license text
    # in the notice, and the entry is kept as it was)
    def test_mod_license_text(self):
        self.git(self.up, "config", "uploadpack.allowFilter", "true")
        self.install_mod()
        before = self.manifest()["entries"]["m"]
        (self.repo / "docs").mkdir()
        self.env.update(CLAUDE_CONFIG_LOCK=str(self.tmp / "nolock.json"), XDG_CACHE_HOME=str(self.tmp / "cache"))
        r = self.tool("build")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.manifest()["entries"]["m"], before)
        notice = (self.repo / "docs" / "NOTICE.md").read_text()
        self.assertIn("Patched here: m.", notice)
        self.assertIn("Copyright (c) Someone", notice)
        self.assertNotIn("license text not reached", notice)

    # covers: AC-8 (a skill holding a private name gets no manifest entry, goes to the private store, stays
    # installed untouched, and drift still accounts for it)
    def test_private_name_skill(self):
        s = self.live / "skills" / "secret"
        s.mkdir()
        (s / "SKILL.md").write_text("made for Zorblex\n")
        self.manifest({})
        (self.repo / "docs").mkdir()
        self.env.update(CLAUDE_CONFIG_LOCK=str(self.tmp / "nolock.json"), XDG_CACHE_HOME=str(self.tmp / "cache"))
        r = self.tool("build")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("secret: private name, copied to the private store only", r.stdout)
        self.assertNotIn("secret", self.manifest()["entries"])
        self.assertNotIn("zorblex", (self.repo / "config" / "manifest.json").read_text().lower())
        self.assertEqual((self.live / "private" / "skills" / "secret" / "SKILL.md").read_text(), "made for Zorblex\n")
        self.assertEqual((s / "SKILL.md").read_text(), "made for Zorblex\n")
        self.assertEqual(self.tool("drift").returncode, 0, self.tool("drift").stdout)

    # covers: AC-6 (the history walk passes over the commit that deleted the folder and finds the older match)
    def test_pin_past_deletion(self):
        old = self.commit({"skills/m/SKILL.md": "m\n"})
        self.commit({"skills/m/SKILL.md": None})
        self.commit({"skills/m/SKILL.md": "m newer\n"})
        live = self.tmp / "m"
        live.mkdir()
        (live / "SKILL.md").write_text("m\n")
        self.assertEqual(cc.pin(self.up, "skills/m", cc.folder_hash(live), None, self.tmp)[0], old)

    # covers: AC-6 (an Apache-2.0 patch opens with the changed files line, and still applies)
    def test_apache_header(self):
        s = self.install_edited()
        m = self.manifest()
        m["entries"]["s"]["license"] = "Apache-2.0"
        (self.repo / "config" / "manifest.json").write_text(json.dumps(m))
        (s / "ref.md").write_text("ref mine\n")
        self.assertEqual(self.tool("patches").returncode, 0)
        patch = (self.repo / "config" / "patches" / "s.patch").read_text()
        self.assertEqual(patch.splitlines()[0], "# Changed from upstream: SKILL.md, ref.md")
        shutil.rmtree(s)
        self.assertEqual(self.tool("restore").returncode, 0)
        self.assertEqual((s / "ref.md").read_text(), "ref mine\n")


class TestPlugins(Case):
    # covers: AC-5 (one kind plugin entry per installed plugin with its source, version, license and install line;
    # patches and restore pass over it, restore names the reinstall command once it is gone; SKILLS.md lists it)
    def test_plugin_entry(self):
        folder = self.live / "plugins" / "cache" / "mk" / "p1" / "1.2.0"
        (folder / ".claude-plugin").mkdir(parents=True)
        (folder / ".claude-plugin" / "plugin.json").write_text(json.dumps({"description": "Does p1. More."}))
        (folder / "LICENSE").write_text("MIT\nPermission is hereby granted, free of charge\n")
        (self.live / "plugins" / "known_marketplaces.json").write_text(
            json.dumps({"mk": {"source": {"source": "github", "repo": "o/mk"}}}))
        plugins = self.live / "plugins" / "installed_plugins.json"
        plugins.write_text(json.dumps({"version": 2, "plugins": {"p1@mk": [
            {"installPath": str(folder), "version": "1.2.0", "gitCommitSha": "abc123"}]}}))
        self.manifest({})
        (self.repo / "docs").mkdir()
        self.env.update(CLAUDE_CONFIG_LOCK=str(self.tmp / "nolock.json"), XDG_CACHE_HOME=str(self.tmp / "cache"))
        r = self.tool("build")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("p1@mk", (self.repo / "docs" / "NOTICE.md").read_text())
        e = self.manifest()["entries"]["p1@mk"]
        self.assertEqual({k: e[k] for k in ("kind", "status", "source", "pinned", "license", "publish", "fetch",
                                              "install", "description")},
                         {"kind": "plugin", "status": "downloaded", "source": "github:o/mk", "pinned": "abc123",
                          "license": "MIT", "publish": False, "fetch": "manual",
                          "install": "claude plugin install p1@mk", "description": "Does p1."})
        self.assertEqual(self.tool("patches").returncode, 0)
        r = self.tool("restore")
        self.assertEqual((r.returncode, r.stdout), (0, ""), r.stderr)
        plugins.write_text(json.dumps({"version": 2, "plugins": {}}))
        self.assertIn("p1@mk: missing; reinstall with: claude plugin install p1@mk", self.tool("restore").stdout)
        shutil.copy(REAL / "scripts" / "asciify.py", self.repo / "scripts" / "asciify.py")
        r = self.tool("docs")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("| `p1@mk` | o/mk | abc123 | MIT | Does p1. |",
                      (self.repo / "docs" / "guides" / "SKILLS.md").read_text())

    # a running session drops .in_use/<pid> in the plugin folder; it used to make 10 of 12 base_hash values stale
    def test_in_use_marker_not_hashed(self):
        folder = self.live / "plugins" / "cache" / "mk" / "p1" / "1.2.0"
        folder.mkdir(parents=True)
        (folder / "plugin.md").write_text("p1\n")
        before = cc.folder_hash(folder)
        (folder / ".in_use").mkdir()
        (folder / ".in_use" / "4242").write_text('{"pid": 4242}\n')
        self.assertEqual(cc.folder_hash(folder), before)


class TestDescription(unittest.TestCase):
    # covers: spec 0048 AC-5 and AC-13 (a folded `>` description is read whole, not as the bare `>`)
    def test_folded(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "SKILL.md").write_text("---\nname: x\ndescription: >\n  Does one thing. Then\n  more.\n"
                                           "argument-hint: y\n---\nbody\n")
            self.assertEqual(cc.description(d), "Does one thing.")
            Path(d, "SKILL.md").write_text("---\ndescription: Plain line. Second.\n---\n")
            self.assertEqual(cc.description(d), "Plain line.")


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
