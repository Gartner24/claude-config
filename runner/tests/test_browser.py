"""Spec 0009: headless verify and test for `wf run`."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402
from test_run import RunCase  # noqa: E402

GIT_ID = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]
TEST_FIRST = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress\n- [ ] `/test a`\n- [ ] `/develop a`\n"


def git(repo, *args):
    return subprocess.run(["git", *GIT_ID, "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def branch_repo(repo, base="main"):
    """base with one commit, then work with two more and an uncommitted file; returns the base sha."""
    git(repo, "checkout", "-q", "-b", base)
    (repo / "a.txt").write_text("a")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    sha = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "-b", "work")
    for n in ("b", "c"):
        (repo / f"{n}.txt").write_text(n)
        git(repo, "add", f"{n}.txt")
        git(repo, "commit", "-qm", n)
    (repo / "d.txt").write_text("d")
    return sha


class TestBaseUnit(unittest.TestCase):
    # covers: AC-9 (main, master, neither)
    def test_base(self):
        for base in ("main", "master"):
            with tempfile.TemporaryDirectory() as d:
                repo = Path(d)
                git(repo, "init", "-q")
                sha = branch_repo(repo, base)
                self.assertEqual(run.test_base(str(repo)), sha)
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            git(repo, "init", "-q")
            branch_repo(repo, "trunk")
            self.assertIsNone(run.test_base(str(repo)))

    def test_prompt(self):
        self.assertEqual(run.unattended_prompt({}, False, None), run.UNATTENDED_PROMPT)
        self.assertEqual(run.unattended_prompt({}, False, "abc123"), run.UNATTENDED_PROMPT + (
            " For /test, the feature's changes are the files in git diff --name-only --diff-filter=ACMR abc123 plus "
            "the untracked files from git ls-files --others --exclude-standard; use that list as the changed files "
            "instead of uncommitted files only."))


class TestBaseRun(RunCase):
    # covers: AC-9 (only /test box calls, a retry reuses it), AC-10 (test_base in run.json)
    def test_run(self):
        sha = branch_repo(self.repo)
        (self.repo / "docs/scope/scope.md").write_text(TEST_FIRST)
        self.steps([{"tick": False, "rc": 1}, {}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = json.loads(next((self.state / "wf" / "runs").iterdir()).joinpath("run.json").read_text())
        self.assertEqual([(c["command"], c["test_base"], c["retry_of"]) for c in rec["calls"]],
                         [("/test a", sha, None), ("/test a", sha, 1), ("/develop a", None, None), ("/sync", None, None)])
        prompts = [self.argv(n)["argv"][self.argv(n)["argv"].index("--append-system-prompt") + 1] for n in (1, 2, 3, 4)]
        self.assertEqual(prompts[0], run.unattended_prompt({}, False, sha))
        self.assertEqual(prompts[1], prompts[0])
        self.assertEqual(prompts[2:], [run.UNATTENDED_PROMPT] * 2)


if __name__ == "__main__":
    unittest.main()
