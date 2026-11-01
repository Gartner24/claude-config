import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import facts


def repo(d):
    subprocess.run(["git", "init", "-q", "-b", "main", d], check=True)
    Path(d, "t.txt").write_text("x\n")
    subprocess.run(["git", "-C", d, "add", "t.txt"], check=True)
    subprocess.run(["git", "-C", d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"], check=True)
    Path(d, "a.txt").write_text("x\n")


class GitFacts(unittest.TestCase):
    def test_repo_filter_is_never_run(self):
        with tempfile.TemporaryDirectory() as d:
            repo(d)
            marker = Path(d, "ran")
            subprocess.run(["git", "-C", d, "config", "filter.evil.clean", f"touch {marker}; cat"], check=True)
            Path(d, ".gitattributes").write_text("* filter=evil\n")
            # a changed tracked file: status re-reads it through its clean filter
            Path(d, "t.txt").write_text("y\n")
            g = facts.git(d)
            self.assertFalse(marker.exists())
            self.assertEqual(g, {"branch": "main", "changes": None, "staged": None, "modified": None, "untracked": None})

    def test_plain_repo_counts(self):
        with tempfile.TemporaryDirectory() as d:
            repo(d)
            g = facts.git(d)
            self.assertEqual((g["branch"], g["changes"], g["untracked"]), ("main", 1, 1))


class Alone(unittest.TestCase):
    def test_runs_with_no_runner_beside_it(self):
        # it used to import the runner's wf.py through a path four folders up; the runner is retired
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as alone:
            repo(d)
            script = Path(alone, "facts.py")
            script.write_text(Path(facts.__file__).read_text())
            r = subprocess.run([sys.executable, "-I", str(script), d], capture_output=True, text=True,
                               env={"PATH": os.environ["PATH"], "ANTHROPIC_BASE_URL": "https://user@llm.example:8443/v1"})
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual((out["git"]["branch"], out["git"]["untracked"], out["via"]), ("main", 1, "llm.example"))
            self.assertEqual(set(out), {"folder", "git", "via"})


class Profile(unittest.TestCase):
    # covers: spec 0081 AC-9 (the name from state/profile.json under CLAUDE_LIVE_DIR is printed; no key when the file
    # is missing)
    def test_profile_name(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as live:
            env = {"PATH": os.environ["PATH"], "CLAUDE_LIVE_DIR": live}
            run = lambda: json.loads(subprocess.run([sys.executable, "-I", facts.__file__, d], capture_output=True,
                                                    text=True, env=env, check=True).stdout)
            self.assertNotIn("profile", run())
            Path(live, "state").mkdir()
            Path(live, "state", "profile.json").write_text(json.dumps({"name": "creator", "owner": False}))
            self.assertEqual(run()["profile"], "creator")


if __name__ == "__main__":
    unittest.main()
