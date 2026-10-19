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


if __name__ == "__main__":
    unittest.main()
