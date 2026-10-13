"""Spec 0021: never stop, a case for every stop."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402

ROWS = {*(f"F{n}" for n in range(1, 13)), *(f"R{n}" for n in range(1, 5)), *(f"U{n}" for n in range(1, 11))}


class TestCaseTable(unittest.TestCase):
    # covers: AC-1 (every reason in PARKS, REPO_STOPS, RUN_STOPS has exactly one row; every row of the spec is used)
    def test_every_reason_has_a_row(self):
        reasons = run.PARKS | run.REPO_STOPS | run.RUN_STOPS
        self.assertEqual(sorted(reasons - set(run.CASES)), [], "reasons with no case row")
        self.assertEqual(sorted(set(run.CASES) - reasons), ["branch"])
        self.assertEqual({row for row, _ in run.CASES.values()}, ROWS)

    # covers: AC-2 (a feature level row always asks, its options fit a phone button and the panel)
    def test_options(self):
        for reason, (row, options) in run.CASES.items():
            with self.subTest(reason):
                self.assertLessEqual(len(options), run.MAX_OPTIONS)
                self.assertTrue(all(0 < len(o) < 40 for o in options))
                self.assertEqual(len(set(options)), len(options))
                if reason in run.PARKS:
                    self.assertTrue(row.startswith("F") and len(options) >= 2)
        # Only R1, R4, U1, U3, U9 and U10 never ask.
        self.assertEqual(sorted(r for r, o in run.CASES.values() if not o), ["R1", "R4", "U1", "U10", "U3", "U9"])


if __name__ == "__main__":
    unittest.main()
