"""Spec 0054: scripts/skill-scan.py against a fake skillspector on PATH and a fake HOME; never the real ~/.claude."""
import contextlib
import datetime
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REAL = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("skill_scan", REAL / "scripts" / "skill-scan.py")
ss = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ss)

# The fake reads $FAKE_SS/config.json: {"version": ..., "targets": {folder name or "*": {"mode": ..., "issues": [...]}}}
# and logs one JSON line per call (argv, provider) to $FAKE_SS/log.
FAKE = r'''#!/usr/bin/env python3
import json, os, sys, time
d = os.environ["FAKE_SS"]
cfg = json.load(open(os.path.join(d, "config.json")))
if sys.argv[1:] == ["--version"]:
    print(cfg.get("version", "SkillSpector v2.12.0"))
    sys.exit(0)
with open(os.path.join(d, "log"), "a") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "provider": os.environ.get("SKILLSPECTOR_PROVIDER")}) + "\n")
t = cfg["targets"].get(os.path.basename(sys.argv[2]), cfg["targets"].get("*", {}))
mode = t.get("mode", "ok")
if mode == "hang":
    time.sleep(30)
if mode == "noreport":
    sys.exit(3)
out = sys.argv[sys.argv.index("-o") + 1]
with open(out, "w") as f:
    f.write("{\"issues\": [" if mode == "truncated" else json.dumps({"issues": t.get("issues", [])}))
'''


def fake_bin(tmp, version="SkillSpector v2.12.0", targets=None):
    """A bin folder holding the fake; returns (bin, data dir). PATH gets only it and python's folder."""
    b, d = tmp / "fakebin", tmp / "fakess"
    b.mkdir(exist_ok=True)
    d.mkdir(exist_ok=True)
    (b / "skillspector").write_text(FAKE.replace("/usr/bin/env python3", sys.executable))
    (b / "skillspector").chmod(0o755)
    (d / "config.json").write_text(json.dumps({"version": version, "targets": targets or {}}))
    return b, d


def issue(sev="HIGH", pattern="Tainted flow (line 12)", text="requests.post(url)", file="scripts/a.py", line=7):
    return {"severity": sev, "pattern": pattern, "finding": text, "location": {"file": file, "start_line": line}}


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        self.skills = self.home / ".claude" / "skills"
        self.skills.mkdir(parents=True)
        self.bin, self.data = fake_bin(self.tmp)
        env = mock.patch.dict(os.environ, {"HOME": str(self.home), "FAKE_SS": str(self.data),
                                           "PATH": f"{self.bin}:{Path(sys.executable).parent}"})
        env.start()
        self.addCleanup(env.stop)

    def config(self, **kw):
        cfg = json.loads((self.data / "config.json").read_text())
        cfg.update(kw)
        (self.data / "config.json").write_text(json.dumps(cfg))

    def target(self, name, **t):
        cfg = json.loads((self.data / "config.json").read_text())
        cfg["targets"][name] = t
        (self.data / "config.json").write_text(json.dumps(cfg))

    def skill(self, name, where=None):
        real = (where or self.tmp / "real") / name
        real.mkdir(parents=True)
        (real / "SKILL.md").write_text("x\n")
        (self.skills / name).symlink_to(real)
        return real

    def plugin(self, key, path):
        path.mkdir(parents=True, exist_ok=True)
        f = self.home / ".claude" / "plugins" / "installed_plugins.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(f.read_text()) if f.exists() else {"version": 2, "plugins": {}}
        data["plugins"][key] = [{"installPath": str(path)}]
        f.write_text(json.dumps(data))

    def log(self):
        f = self.data / "log"
        return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []

    def run_main(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ss.main(list(args))
        return code, out.getvalue()

    def reports(self, mode="static"):
        return self.home / ".claude" / "state" / "skillspector" / datetime.date.today().isoformat() / mode


class TestTargets(Case):
    # covers: AC-1 (realpath of a symlinked skill, plugin installPath, nested folder dropped)
    def test_realpath_and_nested(self):
        a = self.skill("a")
        p = self.home / ".claude" / "plugins" / "cache" / "m" / "p" / "1.0"
        self.plugin("p@m", p)
        self.skill("inner", where=p / "skills")
        code, out = self.run_main()
        self.assertEqual(code, 0, out)
        scanned = sorted(c["argv"][1] for c in self.log())
        self.assertEqual(scanned, sorted([str(a), str(p)]))
        self.assertIn("static: 2 targets", out)

    # covers: AC-13 (trusted pack and skills linked into it skipped and named; look alike and explicit path scanned)
    def test_trusted(self):
        pack = self.skill("gstack")
        self.skill("qa", where=pack)
        upgrade = self.skill("gstack-upgrade")
        other = self.skill("other")
        code, out = self.run_main()
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(c["argv"][1] for c in self.log()), sorted([str(upgrade), str(other)]))
        self.assertIn("skipped (trusted): gstack\n", out)
        (self.data / "log").unlink()
        code, out = self.run_main(str(self.skills / "gstack"))
        self.assertEqual([c["argv"][1] for c in self.log()], [str(pack)])
        self.assertNotIn("skipped", out)

    # covers: AC-13 (both passes scan the same filtered targets, one skip line)
    def test_trusted_both(self):
        self.skill("qa", where=self.skill("ui-ux-pro-max"))
        other = self.skill("other")
        code, out = self.run_main("both")
        self.assertEqual(code, 0, out)
        self.assertEqual([c["argv"][1] for c in self.log()], [str(other)] * 2)
        self.assertEqual(out.count("skipped (trusted): ui-ux-pro-max\n"), 1, out)

    # covers: AC-13, AC-7 (--against, the update hook, still scans an installed trusted pack)
    def test_trusted_against(self):
        pack = self.skill("gstack")
        cand = self.tmp / "cand" / "gstack"
        cand.mkdir(parents=True)
        code, out = self.run_main("--against", "gstack", str(cand))
        self.assertEqual((code, out.strip()), (0, "no new findings"))
        self.assertEqual(sorted(c["argv"][1] for c in self.log()), sorted([str(pack), str(cand)]))


class TestCommands(Case):
    # covers: AC-2 (static has --no-llm and no provider; llm drops it and sets claude_cli)
    def test_static_and_llm(self):
        a = self.skill("a")
        self.assertEqual(self.run_main("both")[0], 0)
        static, llm = self.log()
        self.assertEqual(static["argv"][:5], ["scan", str(a), "--format", "json", "-o"])
        self.assertIn("--no-llm", static["argv"])
        self.assertIsNone(static["provider"])
        self.assertNotIn("--no-llm", llm["argv"])
        self.assertEqual(llm["provider"], "claude_cli")
        self.assertTrue(any(self.reports("llm").glob("*.json")))


class TestPin(Case):
    # covers: AC-3 (wrong version or no skillspector exits 2 with one line, scans nothing)
    def test_wrong_version(self):
        self.skill("a")
        self.config(version="SkillSpector v2.11.0")
        code, out = self.run_main()
        self.assertEqual(code, 2)
        self.assertEqual(len(out.strip().splitlines()), 1)
        self.assertIn("v2.12.0 needed", out)
        self.assertEqual(self.log(), [])

    def test_missing(self):
        (self.bin / "skillspector").unlink()
        code, out = self.run_main()
        self.assertEqual((code, out.strip()), (2, "skill-scan: skillspector not found on PATH"))


class TestResume(Case):
    # covers: AC-4 (done targets skipped the same day, a truncated report scanned again)
    def test_skip_and_rescan(self):
        self.skill("a")
        self.skill("b")
        self.assertEqual(self.run_main()[0], 0)
        self.assertEqual(len(self.log()), 2)
        bad = next(f for f in self.reports().glob("*.json") if f.name.endswith("__b.json"))
        bad.write_text('{"issues": [')
        self.assertEqual(self.run_main()[0], 0)
        calls = self.log()
        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[2]["argv"][1].endswith("/b"))

    # covers: AC-4 (a timeout and a missing report are FAIL, exit 1, and leave no report behind)
    def test_timeout_and_no_report(self):
        self.skill("slow")
        self.skill("broken")
        self.target("slow", mode="hang")
        self.target("broken", mode="noreport")
        with mock.patch.dict(ss.TIMEOUT, {"static": 1}):
            code, out = self.run_main()
        self.assertEqual(code, 1, out)
        self.assertIn("timeout after 1 s", out)
        self.assertIn("exit 3, no readable report", out)
        self.assertEqual(list(self.reports().iterdir()), [])

    def test_truncated_is_fail(self):
        self.skill("a")
        self.target("a", mode="truncated")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("FAIL static", out)


class TestVerdict(Case):
    # covers: AC-5 (baseline hides known findings, noise paths hidden, a new HIGH prints file:line, exit 1,
    # and a plugin version change plus a line shift keeps a known finding hidden)
    def test_baseline(self):
        p1 = self.home / ".claude" / "plugins" / "cache" / "m" / "p" / "1.0"
        self.plugin("p@m", p1)
        self.target("1.0", issues=[issue(), issue(file=".venv/lib/x.py"), issue(sev="MEDIUM")])
        code, out = self.run_main("--accept")
        self.assertEqual(code, 0, out)
        self.assertIn("static: baseline holds 1 findings", out)
        # the plugin moves to 2.0 and its known finding shifts lines; one real new finding appears
        shutil.rmtree(self.home / ".claude" / "plugins" / "cache")
        p2 = p1.with_name("2.0")
        self.plugin("p@m", p2)
        self.target("2.0", issues=[issue(pattern="Tainted flow (line 40)", line=35),
                                   issue(file=".venv/lib/y.py", text="eval(x)"),
                                   issue(sev="CRITICAL", pattern="Exfil", text="curl evil", file="run.sh", line=3)])
        code, out = self.run_main()
        self.assertEqual(code, 1, out)
        lines = [x for x in out.splitlines() if "@" in x]
        self.assertEqual(lines, ["p@m  CRITICAL Exfil @ run.sh:3: curl evil"])
        self.assertIn("1 new serious findings", out)

    def test_baseline_per_pass(self):
        self.skill("a")
        self.target("a", issues=[issue()])
        self.assertEqual(self.run_main("static", "--accept")[0], 0)
        self.assertEqual(self.run_main("static")[0], 0)
        code, out = self.run_main("llm")
        self.assertEqual(code, 1, out)
        self.assertIn("a  HIGH", out)

    # covers: security review 2026-10-18 (the noise file patterns match only the last path part)
    def test_noise_anchored(self):
        self.skill("a")
        hidden = ["tests/x.py", "a/CHANGELOG.md", "src/x.test.ts", "pkg/y_test.go", "test_z.py", "node_modules/q.js"]
        shown = ["hooks/latest_hook.sh", "contest_x/run.sh", "bin/CHANGELOG/run.sh", "my.test.d/run.sh"]
        self.target("a", issues=[issue(file=f, text=f"curl {f}") for f in hidden + shown])
        code, out = self.run_main()
        self.assertEqual(code, 1, out)
        self.assertEqual(sorted(x.split(" @ ")[1].split(":")[0] for x in out.splitlines() if " @ " in x), sorted(shown))

    # covers: security review 2026-10-18 (the same finding in a second file is new; an old four part entry still hides it)
    def test_same_text_other_file(self):
        self.skill("a")
        self.target("a", issues=[issue()])
        self.assertEqual(self.run_main("--accept")[0], 0)
        self.target("a", issues=[issue(), issue(file="hooks/b.py")])
        shutil.rmtree(self.reports())  # same day: the first report would be reused
        code, out = self.run_main()
        self.assertEqual(code, 1, out)
        self.assertEqual([x for x in out.splitlines() if " @ " in x],
                         ["a  HIGH Tainted flow (line N) @ hooks/b.py:7: requests.post(url)"])
        bf = self.home / ".claude" / "state" / "skillspector" / "baseline.json"
        bf.write_text(json.dumps({"static": [k[:4] for k in json.loads(bf.read_text())["static"]]}))
        self.assertEqual(self.run_main()[0], 0)
        # an accept drops the old four part entries for file keys
        self.assertEqual(self.run_main("--accept")[0], 0)
        self.assertEqual({len(k) for k in json.loads(bf.read_text())["static"]}, {5})


class TestAgainst(Case):
    # covers: AC-6 (the candidate's added finding prints; a skill not installed counts every finding)
    def test_added(self):
        live = self.skill("s")
        cand = self.tmp / "cand" / "s"
        cand.mkdir(parents=True)
        self.target("s", issues=[issue()])
        # both folders are named s, so the fake gives them the same findings: nothing added
        code, out = self.run_main("--against", "s", str(cand))
        self.assertEqual((code, out.strip()), (0, "no new findings"))
        shutil.rmtree(live)
        code, out = self.run_main("--against", "s", str(cand))
        self.assertEqual(code, 1, out)
        self.assertIn("s  HIGH Tainted flow (line N) @ scripts/a.py:7", out)

    # covers: AC-6 (a failed side prints scan failed, never no new findings)
    def test_failed_candidate(self):
        self.skill("s")
        cand = self.tmp / "cand" / "bad"
        cand.mkdir(parents=True)
        self.target("bad", mode="noreport")
        code, out = self.run_main("--against", "s", str(cand))
        self.assertEqual(code, 1)
        self.assertIn("scan failed: candidate", out)
        self.assertNotIn("no new findings", out)


class TestPrivate(Case):
    # covers: AC-9 (reports and the baseline land under ~/.claude/state/skillspector only)
    def test_paths(self):
        self.skill("a")
        self.target("a", issues=[issue()])
        self.run_main("--accept")
        state = self.home / ".claude" / "state" / "skillspector"
        written = {p for p in self.tmp.rglob("*.json") if "fakess" not in p.parts}
        self.assertTrue(written)
        self.assertTrue(all(state in p.parents for p in written), written)


if __name__ == "__main__":
    unittest.main()
