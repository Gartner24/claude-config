"""Spec 0015 AC-4: rule 11a, a ticked /check verify or /test box needs its proof line."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402
from test_ntfy import FakeNtfy, write_config  # noqa: E402
from test_park import VERIFY, fail  # noqa: E402
from test_run import RunCase, ask  # noqa: E402

TEST = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n- [ ] Test it: `/test a`\n"
DEVELOP = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n- [ ] `/develop a`\n"
MILESTONE = TEST + "   - [ ] m1 cases\n"


def says(text, **extra):
    return {"json": {"result": text}, **extra}


class TestUnchecked(RunCase):
    def done(self, scope, steps, *args):
        self.make_repo("c", scope)
        self.steps(steps)
        r = self.wf("c", "-y", *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return self.run_record()[1]

    # Spec 0021 F6: calls counts the one rerun the box gets by itself before it parks.
    def parked(self, scope, steps, name, calls=None):
        self.make_repo("c", scope)
        self.steps(steps)
        rec = self.assert_stopped(self.wf("c", "-y"), "unchecked", calls=calls)
        self.assertRegex(rec["detail"], rf"^.*`/(test|check verify) a` ticked without a valid {name} line; "
                                        r"untick it to rerun$")
        return rec

    # covers: AC-4 (a /test pass with its line goes on; marker and checked_n recorded)
    def test_test_line(self):
        rec = self.done(TEST, [says("all green\nMUTATION CHECKED: 3"), {}])
        self.assertEqual((rec["calls"][0]["marker"], rec["calls"][0]["checked_n"]), ("mutation_checked", 3))

    # covers: AC-4 (no line parks unchecked, the detail names the box, the park is recorded)
    def test_test_missing(self):
        rec = self.parked(TEST, [says("all green")], "MUTATION CHECKED", calls=2)
        self.assertEqual(rec["detail"], "Test it: `/test a` ticked without a valid MUTATION CHECKED line; "
                                        "untick it to rerun")
        self.assertEqual((rec["calls"][0]["marker"], rec["calls"][0]["checked_n"]), (None, None))
        q = json.loads((self.state / "wf" / "queue.json").read_text())
        self.assertEqual([p["reason"] for p in q["parks"]], ["unchecked"])
        self.assertIn("unchecked", run.RECORDED)

    # covers: AC-4 (a verify pass with its line goes on; without it parks)
    def test_verify(self):
        rec = self.done(VERIFY, [says("ok\nCAN FAIL CHECKED: 2"), says("ok\nMUTATION CHECKED: 1"), {}])
        self.assertEqual([(c["marker"], c["checked_n"]) for c in rec["calls"]],
                         [("can_fail_checked", 2), ("mutation_checked", 1), (None, None)])

    def test_verify_missing(self):
        self.parked(VERIFY, [says("ok\nMUTATION CHECKED: 4")], "CAN FAIL CHECKED", calls=2)

    # covers: AC-4 (a verify fail needs no line: the debug loop as before; the rerun after it needs its own)
    def test_debug_rerun(self):
        rec = self.parked(VERIFY, [fail(), {"tick": False}, says("fixed")], "CAN FAIL CHECKED", calls=4)
        self.assertEqual([c["kind"] for c in rec["calls"]], ["box", "debug", "box", "box"])
        self.assertEqual(rec["calls"][0]["marker"], "verify_fail_debug")

    # covers: AC-4 (ticking nothing is no_progress as before; /develop never needs a line)
    def test_earlier_rules(self):
        self.make_repo("c", TEST)
        self.steps([says("nothing", tick=False)])
        self.assert_stopped(self.wf("c", "-y"), "no_progress", calls=1)

    # covers: AC-4 (a ticked box that ends BLOCKED: is decided by the earlier rule and needs no line)
    def test_blocked_first(self):
        self.make_repo("c", TEST)
        self.steps([says("tried\n**BLOCKED:** sudo needed")])
        rec = self.assert_stopped(self.wf("c", "-y"), "blocked", calls=1)
        self.assertEqual((rec["detail"], rec["calls"][0]["marker"]), ("sudo needed", "blocked"))

    def test_develop(self):
        rec = self.done(DEVELOP, [says("built"), {}])
        self.assertEqual(rec["calls"][0]["marker"], None)

    # covers: AC-4 edges (bold line passes, a later line wins, verify 0 parks)
    def test_bold_and_zero(self):
        rec = self.done(TEST, [says("**MUTATION CHECKED:** 2"), {}])
        self.assertEqual(rec["calls"][0]["checked_n"], 2)

    def test_last_line_wins(self):
        rec = self.done(TEST, [says("> MUTATION CHECKED: 7\n- MUTATION CHECKED: 5"), {}])
        self.assertEqual(rec["calls"][0]["checked_n"], 5)

    def test_verify_zero(self):
        self.parked(VERIFY, [says("CAN FAIL CHECKED: 0")], "CAN FAIL CHECKED", calls=2)

    # covers: AC-4 (MUTATION CHECKED: 0 passes with no test file changed, parks when one changed)
    def test_mutation_zero(self):
        rec = self.done(TEST, [says("MUTATION CHECKED: 0", write_file=[["src/a.py", "x = 1\n"]]), {}])
        self.assertEqual(rec["calls"][0]["checked_n"], 0)

    def test_mutation_zero_test_changed(self):
        self.parked(TEST, [says("MUTATION CHECKED: 0", write_file=[["tests/test_a.py", "def test_a(): pass\n"]]),
                           says("MUTATION CHECKED: 0", write_file=[["tests/test_a.py", "def test_a(): 1\n"]])],
                    "MUTATION CHECKED", calls=2)

    # covers: AC-4 (a milestone tick alone is not the box's progress, so no line is asked)
    def test_milestone(self):
        rec = self.done(MILESTONE, [says("m1 done", tick=False, edit=[["- [ ] m1", "- [x] m1"]]),
                                    says("MUTATION CHECKED: 1"), {}])
        self.assertEqual([c["marker"] for c in rec["calls"]], [None, "mutation_checked", None])

    # covers: AC-4 (a resumed /test is judged by the resume's own result)
    def test_resume(self):
        ntfy = FakeNtfy()
        self.addCleanup(ntfy.close)
        write_config(self.tmp / "config", ntfy.url, codes=[f"code{i:04d}" for i in range(5)])
        ntfy.replies = ["{id} 1"]
        self.make_repo("c", TEST)
        self.steps([ask(), says("MUTATION CHECKED: 1"), {}])
        r = self.wf("c", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = self.run_record()[1]
        self.assertEqual(self.argv(2)["argv"][2:4], ["--resume", "s-1"])
        self.assertEqual(rec["calls"][1]["marker"], "mutation_checked")


class TestRuleFile(unittest.TestCase):
    # covers: AC-1 (the repo copy beats skill text, holds the AC-2, AC-3, AC-5 plus AC-7 and AC-9 sections,
    # and NOTICE.md lists it as authored)
    def test_rule_file(self):
        repo = Path(__file__).resolve().parents[2]
        text = (repo / "claude-home" / "rules" / "check-gates.md").read_text()
        self.assertEqual(text.splitlines()[0], "# Check gates (beats skill text)")
        for needle in ("CAN FAIL CHECKED: <n>", "MUTATION CHECKED: <n>", "**Paths:** none", "spec-paths --spec NNNN",
                       "Specs possibly stale", "## Agreed so far, do not ask again"):
            self.assertIn(needle, text)
        self.assertRegex((repo / "docs" / "NOTICE.md").read_text(), r"(?m)^\| `claude-home/rules/check-gates\.md` \|")


if __name__ == "__main__":
    unittest.main()
