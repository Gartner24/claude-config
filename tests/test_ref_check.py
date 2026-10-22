"""scripts/ref-check.py (spec 0072 AC-1): its self check runs in the suite, so a break in the move detector shows."""
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestRefCheck(unittest.TestCase):
    # covers: spec 0072 AC-1 (every pointer kind recorded, a moved file reported, a stale pointer beside a fixed one kept)
    def test_self_check(self):
        r = subprocess.run([sys.executable, "-B", str(REPO / "scripts" / "ref-check.py"), "--test"], capture_output=True,
                           text=True, stdin=subprocess.DEVNULL, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ref-check self check: ok", r.stdout)


if __name__ == "__main__":
    unittest.main()
