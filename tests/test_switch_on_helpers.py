"""Spec 0073 AC-14: the switch-on helpers' self checks run in the suite, so a break in one shows."""
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestSwitchOnHelpers(unittest.TestCase):
    # covers: spec 0073 AC-1 to AC-6, AC-8 to AC-12 (each script's --test), AC-4 (spec-paths --test covers --overlap)
    def test_self_checks(self):
        for name in ("start-gates", "spec-paths", "design-check", "issue-reread", "review-isolated"):
            with self.subTest(name=name):
                r = subprocess.run([sys.executable, "-B", str(REPO / "scripts" / f"{name}.py"), "--test"],
                                   capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=300)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn(f"{name} self checks: all passed", r.stdout)


if __name__ == "__main__":
    unittest.main()
