"""Spec 0025 AC-4, the unanswered path: rb's guard_changed question stays in queue.json, the morning report lists it,
the next bare wf starts rb's child, which waits on the same question, and an answer then builds rb.
Run: python3 -B docs/specs/0025-guard-baseline-between-repos/probes/ac4_overnight.py Ac4.test_unanswered_then_next_wf"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "runner" / "tests"))
from test_parallel import TestPlanBaseline  # noqa: E402


class Ac4(TestPlanBaseline):
    def test_unanswered_then_next_wf(self):
        self.steps(self.change())
        r = self.wf("-y", "--jobs", "1", "--max-wait", "0.0001")
        print(r.stdout)
        self.asked(r, f"{self.hook} changed after the plan, before this repo started")
        [d] = self.queue()["decisions"]
        self.assertEqual((d["reason"], d["level"]), ("guard_changed", "repo"))
        self.assertIn(f"question {d['id']}: (repo): ", (self.state / "wf" / "report.txt").read_text())
        self.assertFalse((self.fakes / "rb-argv-1.json").exists())
        self.again()
        (self.fakes / "rb-count").unlink(missing_ok=True)
        self.reply("{id} 1")
        r = self.wf("-y", "--jobs", "1", "--max-wait", "0.01")
        print(r.stdout)
        self.assertIn(f"  open: {d['id']} (repo): ", r.stdout)
        self.assertNotIn("stopped repo rb: guard_changed", r.stdout)
        self.assertIn(f"answered: {d['id']} rb: accept the new setup and go on", r.stdout)
        self.assertIn("\n[rb] done: 1. A\n", r.stdout)
        self.assertEqual(self.queue()["decisions"], [])
        self.assertEqual(self.baselines(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
