"""tools/bin/docs-pr.sh (spec 0051 AC-11, spec 0026 AC-6, spec 0072 AC-3): copied from the archived runner suite, which no
longer runs. Every case runs a copy of the script inside a scratch repo whose origin carries tools/scripts/private-names.py and
_archive/runner, because the script reads its scanners from its repo's origin default branch."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FAKE_GH = f"""#!{sys.executable}
import json, os, subprocess, sys
d = os.environ["FAKE_DIR"]
a = sys.argv[1:]
open(os.path.join(d, "gh-argv.jsonl"), "a").write(json.dumps(a) + "\\n")
cfg = json.load(open(os.path.join(d, "gh.json")))
if a[:2] == ["pr", "create"]:
    print("https://github.com/acme/widgets/pull/7")
elif a[:2] == ["pr", "merge"] and cfg.get("land"):
    # a squash merge: the head's tree lands on the origin's work branch as one new commit
    o = cfg["land"]
    sha = a[a.index("--match-head-commit") + 1]
    if cfg.get("dirty"):
        open("docs/notes.md", "a").write("later work\\n")
    ref = "refs/heads/work" if cfg.get("land_other") else sha
    tree = subprocess.run(["git", "--git-dir", o, "rev-parse", ref + "^{{tree}}"], capture_output=True, text=True).stdout.strip()
    env = {{**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}}
    new = subprocess.run(["git", "--git-dir", o, "commit-tree", tree, "-p", "refs/heads/work", "-m", "squash"],
                         capture_output=True, text=True, env=env).stdout.strip()
    subprocess.run(["git", "--git-dir", o, "update-ref", "refs/heads/work", new], check=True)
sys.exit(0)
"""


class DocsPr(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / ".claude" / "private").mkdir(parents=True)
        (self.tmp / ".claude" / "private" / "names.txt").write_text("zorblex\n")
        self.fakes = self.tmp / "fakes"
        self.fakes.mkdir()
        self.gh_bin = self.tmp / "gh"
        self.gh_bin.write_text(FAKE_GH)
        self.gh_bin.chmod(0o755)
        self.gh({})
        self.env = {**os.environ, "HOME": str(self.tmp), "GH": str(self.gh_bin), "FAKE_DIR": str(self.fakes),
                    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
        self.origin = self.tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(self.origin)], check=True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "work")
        (self.repo / "tools" / "bin").mkdir(parents=True)
        shutil.copy(REPO / "tools" / "bin" / "docs-pr.sh", self.repo / "tools" / "bin" / "docs-pr.sh")
        (self.repo / "tools" / "scripts").mkdir()
        shutil.copy(REPO / "tools" / "scripts" / "private-names.py", self.repo / "tools" / "scripts" / "private-names.py")
        shutil.copytree(REPO / "_archive" / "runner", self.repo / "_archive" / "runner",
                        ignore=shutil.ignore_patterns("tests", "__pycache__", "e2e", "docs"))
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "keep.md").write_text("k\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "base with the scanners")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "-q", "origin", "work")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/work")

    def git(self, *args, repo=None):
        r = subprocess.run(["git", "-C", str(repo or self.repo), *args], capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def gh(self, cfg):
        (self.fakes / "gh.json").write_text(json.dumps(cfg))

    def gh_calls(self):
        p = self.fakes / "gh-argv.jsonl"
        return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []

    def script(self, *args):
        return subprocess.run(["bash", str(self.repo / "tools" / "bin" / "docs-pr.sh"), *args], cwd=self.repo, capture_output=True,
                              text=True, env=self.env, timeout=120)

    def commit(self, path, text="x\n", message=None):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        self.git("add", "-A")
        self.git("commit", "-qm", message or f"docs: {path}")

    # covers: spec 0051 AC-11 (refusals, exit 2 and one line: tracked changes, nothing ahead of origin, a commit outside
    # docs/, not on the default branch; nothing is pushed)
    def test_refusals(self):
        r = self.script()
        self.assertEqual((r.returncode, r.stderr), (2, "docs-pr: no commit ahead of origin/work\n"))
        self.commit("docs/notes.md")
        (self.repo / "docs" / "notes.md").write_text("changed\n")
        r = self.script()
        self.assertEqual((r.returncode, r.stderr), (2, "docs-pr: the tree has tracked changes\n"))
        self.git("checkout", "--", "docs/notes.md")
        self.commit("src/x.py")
        r = self.script("notes")
        self.assertEqual((r.returncode, r.stderr), (2, "docs-pr: a commit touches src/x.py, outside docs/\n"))
        self.git("switch", "-qc", "other")
        self.assertEqual(self.script().stderr, "docs-pr: not on work\n")
        self.assertEqual(self.gh_calls(), [])
        self.assertNotIn("docs/", self.git("branch", "--list", "-a", repo=self.origin))

    # covers: spec 0051 AC-11 (docs only commits: a docs/<date>-<slug> branch pushed, the PR, the squash merge at HEAD,
    # then reset to origin whose docs match; the URL printed). It also covers spec 0072 AC-3: the scanners are read
    # from `_archive/runner` of origin's default branch, so a clean run reaches the merge.
    def test_lands(self):
        self.commit("docs/notes.md")
        head = self.git("rev-parse", "HEAD")
        self.gh({"land": str(self.origin)})
        r = self.script("notes")
        self.assertEqual((r.returncode, r.stdout), (0, "https://github.com/acme/widgets/pull/7\n"), r.stderr)
        [merge] = [c for c in self.gh_calls() if c[:2] == ["pr", "merge"]]
        self.assertEqual(merge[3:], ["--squash", "--delete-branch", "--match-head-commit", head])
        self.assertEqual(self.git("rev-parse", "work"), self.git("rev-parse", "work", repo=self.origin))
        self.assertEqual(self.git("symbolic-ref", "--short", "HEAD"), "work")

    # covers: spec 0072 AC-3 (the scanners come from origin's `_archive/runner`: when the default branch has no such
    # folder the script refuses before any PR)
    def test_scanners_missing_from_archive(self):
        self.git("rm", "-rq", "_archive/runner")
        self.git("commit", "-qm", "drop the runner")
        self.git("push", "-q", "origin", "work")
        self.commit("docs/notes.md")
        r = self.script("notes")
        self.assertEqual(r.returncode, 2, r.stderr)
        # git and tar print their own errors first; the script's line is the last one
        self.assertTrue(r.stderr.endswith("docs-pr: cannot read the scanners from origin/work\n"), r.stderr)
        self.assertEqual(self.gh_calls(), [])

    # covers: spec 0026 AC-6 (the attribution scan runs the archived pr.attribution_hits: a banned trailer in a commit
    # message stops the script before the push and the PR)
    def test_attribution_scan(self):
        self.commit("docs/notes.md", message="docs: notes\n\nCo-Authored-" + "By: Claude <noreply@anthropic.com>")
        r = self.script("notes")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("docs-pr: attribution scan hit", r.stderr)
        self.assertEqual(self.gh_calls(), [])

    # covers: spec 0051 AC-11 (the squash commit differs from the local commits: local default branch is still reset)
    def test_resyncs_diverged(self):
        self.commit("docs/notes.md")
        self.gh({"land": str(self.origin), "land_other": True})
        r = self.script("notes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.git("rev-parse", "work"), self.git("rev-parse", "work", repo=self.origin))

    # covers: spec 0051 AC-11 (a tree that went dirty during the merge is never reset away)
    def test_resync_keeps_dirty_tree(self):
        self.commit("docs/notes.md")
        self.gh({"land": str(self.origin), "land_other": True, "dirty": True})
        self.script("notes")
        self.assertIn("later work", (self.repo / "docs" / "notes.md").read_text())

    # covers: spec 0051 AC-11 (PR title is the newest commit subject, body lists every subject, no --fill)
    def test_title_and_body_from_commits(self):
        self.commit("docs/a.md")
        self.commit("docs/b.md")
        self.gh({"land": str(self.origin)})
        r = self.script("notes")
        self.assertEqual(r.returncode, 0, r.stderr)
        [create] = [c for c in self.gh_calls() if c[:2] == ["pr", "create"]]
        self.assertNotIn("--fill", create)
        self.assertEqual(create[create.index("--title") + 1], "docs: docs/b.md")
        self.assertEqual(create[create.index("--body") + 1], "- docs: docs/a.md\n- docs: docs/b.md")

    # covers: spec 0026 security review (module shadowing): the scanners run from origin's copy with python -I, so an
    # untracked module planted next to the tree's checker does not turn a private name hit into a pass
    def test_planted_checker(self):
        self.commit("docs/notes.md", "made for Zorblex\n")
        # Untracked, so the tree check does not see it; python's script folder would.
        (self.repo / "tools" / "scripts" / "subprocess.py").write_text("import sys\nsys.exit(0)\n")
        self.gh({"land": str(self.origin)})
        r = self.script()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("docs-pr: private names scan hit", r.stderr)
        self.assertEqual(self.gh_calls(), [])


if __name__ == "__main__":
    unittest.main()
