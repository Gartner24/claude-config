"""Spec 0043 AC-7: the parallel suite command."""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fast  # noqa: E402

CASES = '''import os
import unittest


class TestA(unittest.TestCase):
    def test_ok(self):
        self.assertTrue(True)

    def test_state_is_own(self):
        self.assertIn("wf-fast-", os.environ["XDG_STATE_HOME"])


class TestB(unittest.TestCase):
    def test_broken(self):
        self.assertEqual(1, 2, "BROKEN-MARKER")
'''


class TestFast(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        with open(os.path.join(self.dir, "test_sample.py"), "w") as f:
            f.write(CASES)
        self.enterContext(mock.patch.object(fast, "HERE", self.dir))
        sys.modules.pop("test_sample", None)

    def main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = fast.main(list(argv))
        return code, out.getvalue()

    # covers: AC-7 (every test in its own process; a failure exits non zero and prints that test's output and a count)
    def test_failure_reported(self):
        code, out = self.main()
        self.assertEqual(code, 1)
        self.assertIn("=== test_sample.TestB.test_broken ===", out)
        self.assertIn("BROKEN-MARKER", out)
        self.assertIn("Ran 3 tests", out)
        self.assertIn("1 failed", out)
        self.assertNotIn("test_state_is_own ===", out)

    # covers: AC-7 (a test that hangs fails with a timeout line instead of holding the run)
    def test_hang(self):
        with open(os.path.join(self.dir, "test_sample.py"), "a") as f:
            f.write("\n\nclass TestC(unittest.TestCase):\n    def test_hang(self):\n        import time\n        time.sleep(30)\n")
        with mock.patch.object(fast, "TIMEOUT", 1):
            code, out = self.main("test_sample.TestC")
        self.assertEqual(code, 1)
        self.assertIn("=== test_sample.TestC.test_hang ===\ntimed out after 1 s", out)

    # covers: AC-7 (`fast.py module.Class` runs only that part)
    def test_only_part(self):
        code, out = self.main("test_sample.TestA")
        self.assertEqual(code, 0)
        self.assertIn("Ran 2 tests", out)
        self.assertTrue(out.rstrip().endswith("OK"), out)


if __name__ == "__main__":
    unittest.main()
