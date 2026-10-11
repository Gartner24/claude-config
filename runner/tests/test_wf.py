import subprocess
import sys
import unittest
from pathlib import Path

WF = Path(__file__).resolve().parent.parent / "wf.py"


def run(*args):
    return subprocess.run([sys.executable, str(WF), *args], capture_output=True, text=True)


class TestEntry(unittest.TestCase):
    def test_help_exits_zero(self):
        r = run("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("usage: wf", r.stdout)

    def test_no_command_prints_usage_and_fails(self):
        r = run()
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage: wf", r.stderr)

    def test_unknown_command_fails(self):
        self.assertNotEqual(run("bogus").returncode, 0)


if __name__ == "__main__":
    unittest.main()
