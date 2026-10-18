import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runner


class RunEntry(unittest.TestCase):
    def test_repo_name_reaches_the_pane_without_escape_codes(self):
        out = runner.run_entry({"repo": "/x/ev\x1b]0;owned\x07il", "feature": "f", "tree": ""})
        self.assertNotIn("\x1b", out["repo"])
        self.assertNotIn("\x07", out["repo"])


if __name__ == "__main__":
    unittest.main()
