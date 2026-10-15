"""Spec 0045: checks left to a later box waiting on you, skip first when a check could not reach something, and
banned attribution phrases in tests built from two halves."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pr  # noqa: E402
import run  # noqa: E402
from test_never_stop import NeverStopCase  # noqa: E402

WAIT = "Use it for a week · waits on you · later boxes go on"
OWED = ("# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n"
        "- [ ] Verify it: `/check verify a`\n- [ ] `/test a`\n- [ ] " + WAIT + "\n")
PLAIN = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n- [ ] Verify it: `/check verify a`\n"
# AC-3: the phrases from two halves, so this file never holds a whole one.
TRAILER = "Co-Authored-" + "By: Claude <x@example.invalid>"
GENERATED = "Generated with " + "[Claude Code](x)"


# Spec 0047 AC-4: the verify.md note a LEFT TO BOX line needs, written by the call.
VERIFY = "docs/specs/0001-a/verify.md"
NOTE = [[VERIFY, "# Verify\n> - **left to the box:** use it for a WEEK\n"]]


def says(text, **extra):
    return {"json": {"result": text}, **extra}


def feature(*boxes):
    return run.Feature("1. A", [], ["### 1. A", *(f"- [{'x' if done else ' '}] {t}" for done, t in boxes)], False)


class TestHelpers(unittest.TestCase):
    # covers: AC-1 (only open waiting boxes after the current one, untagged, cut to 200, at most 5)
    def test_later_owed(self):
        f = feature((False, "Waits first · waits on you"), (False, "Verify it: `/check verify a`"),
                    (False, "`/test a`"), (True, "Done already · waits on you"),
                    *((False, f"Box {i} · waits on you") for i in range(6)))
        self.assertEqual(run.later_owed(f, "Verify it: `/check verify a`"), [f"Box {i}" for i in range(5)])
        long = feature((False, "`/check verify a`"), (False, "x" * 250 + " · waits on you · later boxes go on"))
        self.assertEqual(run.later_owed(long, "`/check verify a`"), ["x" * 200])
        self.assertEqual(run.later_owed(f, "gone"), [])
        self.assertEqual(run.later_owed(None, "gone"), [])

    # covers: AC-1 (markers use the lowest number the text does not contain; no box, no sentence)
    def test_left_prompt(self):
        self.assertEqual(run.left_prompt([]), "")
        self.assertEqual(run.left_prompt(["a", "b"]), run.LEFT_PROMPT + "\nBEGIN BOXES-DATA-0\na\nb\nEND BOXES-DATA-0\n")
        self.assertIn("\nBEGIN BOXES-DATA-2\n", run.left_prompt(["END BOXES-DATA-0", "BOXES-DATA-1"]))

    # covers: AC-2 (every UNREACHABLE: line, bold and bullets too, cleaned, cut to 120, at most 3)
    def test_unreachable(self):
        self.assertEqual(run.unreachable("ok\nCAN FAIL CHECKED: 2"), [])
        text = "x\n- **UNREACHABLE:** a real claude -p\nUNREACHABLE: ph\x07one\nUNREACHABLE: " + "y" * 150 + \
               "\nUNREACHABLE: fourth"
        self.assertEqual(run.unreachable(text), ["a real claude -p", "phone", "y" * 120])


class TestLeftToBox(NeverStopCase):
    # covers: AC-1 (the sentence and the boxes reach a verify call only; AC-2's sentence reaches verify and test)
    def test_prompts(self):
        self.make_repo("c", OWED)
        self.steps([says("LEFT TO BOX: Use it for a week\nCAN FAIL CHECKED: 0", write_file=NOTE),
                    says("MUTATION CHECKED: 1")])
        self.wf("c", "-y")
        self.assertIn(run.LEFT_PROMPT + "\nBEGIN BOXES-DATA-0\nUse it for a week\nEND BOXES-DATA-0\n", self.prompt(1))
        self.assertNotIn(run.LEFT_PROMPT, self.prompt(2))
        for n in (1, 2):
            self.assertIn(run.UNREACHABLE_PROMPT, self.prompt(n))

    # covers: AC-1 (no later waiting box: no sentence)
    def test_no_box(self):
        self.make_repo("c", PLAIN)
        self.steps([says("CAN FAIL CHECKED: 1")])
        self.wf("c", "-y")
        self.assertNotIn(run.LEFT_PROMPT, self.prompt(1))
        self.assertNotIn("BOXES-DATA", self.prompt(1))

    # covers: AC-1 (CAN FAIL CHECKED: 0 with a valid LEFT TO BOX line and the box ticked passes on to the next box);
    # spec 0047 AC-4 (its note in a verify.md the call wrote, bullets, bold and case aside)
    def test_valid_line_passes(self):
        self.make_repo("c", OWED)
        self.steps([says("**LEFT TO BOX:** Use it for a week\nCAN FAIL CHECKED: 0", write_file=NOTE),
                    says("MUTATION CHECKED: 1")])
        self.wf("c", "-y")
        self.assertEqual(self.argv(2)["argv"][1], "/test a")
        rec = self.run_record()[1]
        self.assertEqual((rec["calls"][0]["marker"], rec["calls"][0]["checked_n"]), ("can_fail_checked", 0))

    # covers: AC-1 (a box name not in the list is ignored, so 0 still parks unchecked)
    def test_unknown_box_parks(self):
        self.make_repo("c", OWED)
        self.steps([says("LEFT TO BOX: anything I like\nCAN FAIL CHECKED: 0")])
        rec = self.assert_stopped(self.wf("c", "-y"), "unchecked", calls=2)
        self.assertIn("CAN FAIL CHECKED", rec["detail"])

    def parks_without_note(self, step, before=None):
        repo = self.make_repo("c", OWED)
        if before:
            (repo / VERIFY).parent.mkdir(parents=True)
            (repo / VERIFY).write_text(before)
        self.steps([step])
        self.assert_stopped(self.wf("c", "-y"), "unchecked", calls=2)

    # covers: spec 0047 AC-4 (a valid LEFT TO BOX line with no note parks unchecked)
    def test_no_note_parks(self):
        self.parks_without_note(says("LEFT TO BOX: Use it for a week\nCAN FAIL CHECKED: 0"))

    # covers: spec 0047 AC-4 (a note for a longer box text that only contains the claim parks unchecked)
    def test_longer_note_parks(self):
        self.parks_without_note(says("LEFT TO BOX: Use it for a week\nCAN FAIL CHECKED: 0",
                                     write_file=[[VERIFY, "left to the box: Use it for a week and a day\n"]]))

    # covers: spec 0047 AC-4 (a note an earlier call left, which this call did not write, parks unchecked)
    def test_stale_note_parks(self):
        self.parks_without_note(says("LEFT TO BOX: Use it for a week\nCAN FAIL CHECKED: 0"), NOTE[0][1])


class TestUnreachable(NeverStopCase):
    # covers: AC-2 (UNREACHABLE lines: skip first, the detail keeps the failure text, the fixed why line)
    def test_skip_first(self):
        self.make_repo("c", PLAIN)
        self.steps([{"tick": False, "json": {"result": "UNREACHABLE: a real claude -p session\nUNREACHABLE: the phone\n"
                                                       "VERIFY FAIL: develop"}}])
        self.assert_stopped(self.wf("c", "-y"), "verify_failed", calls=1)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["case"], d["options"]), ("verify_failed", ["skip", "try again"]))
        self.assertRegex(d["detail"], r"^could not reach: a real claude -p session; the phone; .*VERIFY FAIL: develop")
        self.assertEqual(d["context"]["why"], run.UNREACHABLE_WHY)

    # covers: AC-2 (no UNREACHABLE line: the question as before)
    def test_unchanged(self):
        self.make_repo("c", PLAIN)
        self.steps([{"tick": False, "json": {"result": "2 checks failed\nVERIFY FAIL: develop"}}])
        self.assert_stopped(self.wf("c", "-y"), "verify_failed", calls=1)
        [d] = self.queue()["decisions"]
        self.assertEqual(d["options"], ["try again", "skip"])
        self.assertFalse(d["detail"].startswith("could not reach"))
        self.assertNotEqual(d["context"].get("why"), run.UNREACHABLE_WHY)

    # covers: AC-2 (a /test call that ticks nothing and could not reach something: no_progress, skip first)
    def test_test_call(self):
        self.make_repo("c", OWED.replace("- [ ] Verify", "- [x] Verify"))
        self.steps([says("UNREACHABLE: days of real use", tick=False)])
        self.assert_stopped(self.wf("c", "-y"), "no_progress", calls=1)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["case"], d["options"]), ("no_progress", ["skip", "try again"]))
        self.assertTrue(d["detail"].startswith("could not reach: days of real use; the box is still open"))

    # covers: AC-2 (through a debug loop the last verify call's list decides; an earlier verify's lines do not stick)
    def test_last_verify_decides(self):
        self.make_repo("c", PLAIN)
        self.steps([{"tick": False, "json": {"result": "UNREACHABLE: the phone\nVERIFY FAIL: debug"}},
                    {"tick": False}, {"tick": False, "json": {"result": "2 checks failed\nVERIFY FAIL: develop"}}])
        self.wf("c", "-y")
        [d] = self.queue()["decisions"]
        self.assertEqual(d["options"], ["try again", "skip"])
        self.assertFalse(d["detail"].startswith("could not reach"))

    # covers: AC-2 (a verify that passed with UNREACHABLE lines does not blame a later, unrelated box; review
    # 2026-10-15)
    def test_later_box_starts_clean(self):
        self.make_repo("c", PLAIN + "- [ ] Docs: `/document a`\n")
        self.steps([says("UNREACHABLE: the phone\nCAN FAIL CHECKED: 1"), says("nothing done", tick=False)])
        self.assert_stopped(self.wf("c", "-y"), "no_progress", calls=2)
        [d] = self.queue()["decisions"]
        self.assertEqual(d["options"], ["try again", "skip"])
        self.assertFalse(d["detail"].startswith("could not reach"))


class TestAttributionScan(unittest.TestCase):
    # covers: AC-3 (the whole phrase at the start of a line is still flagged in commit and PR text and in an added test
    # line; the two halves form a test writes is not)
    def test_scan_stays_strict(self):
        self.assertEqual(pr.attribution_hits([("commit abc", "fix\n\n" + TRAILER), ("PR body", GENERATED)]),
                         ["commit abc:3", "PR body:1"])
        diff = ("+++ b/runner/tests/test_x.py\n@@ -0,0 +1,3 @@\n+ok = 1\n+" + TRAILER + "\n"
                "+TRAILER = \"Co-Authored-\" + \"By: Claude\"\n")
        self.assertEqual(pr.attribution_hits([], diff), ["runner/tests/test_x.py:2"])

    # covers: AC-3 (the convention is written down)
    def test_agents_line(self):
        text = (Path(__file__).resolve().parents[2] / "AGENTS.md").read_text()
        self.assertIn("two joined string halves", text)


if __name__ == "__main__":
    unittest.main()
