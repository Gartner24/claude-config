"""Spec 0021: never stop, a case for every stop."""
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402
from test_park import GIT_ID, VERIFY  # noqa: E402
from test_run import RunCase, ask  # noqa: E402

ROWS = {*(f"F{n}" for n in range(1, 13)), *(f"R{n}" for n in range(1, 5)), *(f"U{n}" for n in range(1, 11))}

TWO = """# Scope: two
**Autopilot:** allowed

### 1. A · in-progress · auto
- [x] Design it (spec): `/architect a`
- [ ] Build it: `/develop a`
- [ ] Test it: `/test a`

### 2. B · in-progress · auto
- [x] Design it (spec): `/architect b`
- [ ] Build it: `/develop b`
"""
B_DONE = {"tick": False, "edit": [["- [ ] Build it: `/develop b`", "- [x] Build it: `/develop b`"]]}
BLOCKED = {"tick": False, "json": {"result": "BLOCKED: sudo pacman -S stow"}}


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


class NeverStopCase(RunCase):
    def queue(self):
        p = self.state / "wf" / "queue.json"
        return json.loads(p.read_text()) if p.exists() else {"parks": [], "decisions": []}

    def prompt(self, n):
        a = self.argv(n)["argv"]
        return a[a.index("--append-system-prompt") + 1]

    def settings(self, n):
        a = self.argv(n)["argv"]
        return json.loads(a[a.index("--settings") + 1])

    def denied(self, n):
        a = self.argv(n)["argv"]
        return a[a.index("--disallowedTools") + 1].split(",")

    def reply(self, *texts):
        self.report_ntfy.replies = list(texts)


class TestFeatureQuestions(NeverStopCase):
    def setUp(self):
        super().setUp()
        self.two = self.make_repo("two", TWO)
        # Clean, so spec 0011's dirty tree rule does not hold feature B back behind A's park.
        for argv in (["add", "-A"], ["commit", "-qm", "base"]):
            subprocess.run(["git", *GIT_ID, "-C", str(self.two), *argv], check=True, capture_output=True)

    # covers: AC-2 (a park opens its question, options recommended first, pinged; every other feature goes on)
    def test_park_asks_and_the_queue_goes_on(self):
        self.steps([BLOCKED, B_DONE, {"tick": False}])
        r = self.wf("two", "-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn("parked: 1. A: blocked: sudo pacman -S stow", r.stdout)
        self.assertIn("done: 2. B", r.stdout)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["feature"], d["case"], d["options"], d["answer"]), ("1. A", "blocked", ["done, go on", "skip"], None))
        self.assertEqual((d["detail"], d["box_text"], d["command"]), ("sudo pacman -S stow", "Build it: `/develop a`", "/develop a"))
        self.assertIn(f"waiting: {d['id']} blocked: sudo pacman -S stow\n  1 done, go on\n  2 skip\n", r.stdout)
        self.assertIn(f"{d['id']}: blocked: sudo pacman -S stow\n1 done, go on\n2 skip", self.report_ntfy.pings()[0]["message"])
        # The recorded park stays, so wf can still take it back by its cause (spec 0020 AC-6).
        self.assertEqual([p["reason"] for p in self.queue()["parks"]], ["blocked"])

    # covers: AC-3 (done, go on: the feature runs again from its open box, the answer passed into the call)
    def test_done_go_on_resumes(self):
        self.reply("{id} 1")
        self.steps([BLOCKED, B_DONE, {"tick": False}, {}, {}, {"tick": False}])
        r = self.wf("two", "-y", "--max-wait", "0.01", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("answered: ", r.stdout)
        self.assertEqual([self.argv(n)["argv"][1] for n in (4, 5, 6)], ["/develop a", "/test a", "/sync"])
        self.assertIn(run.HINT_PROMPT.format("the user did what you asked for: sudo pacman -S stow"), self.prompt(4))
        self.assertNotIn("The user's answer", self.prompt(2))
        self.assertEqual(self.queue(), {"version": 1, "parks": [], "decisions": []})

    # covers: AC-3 (the answer clears the park with its question, so a question the rerun asks is not held by it)
    def test_answer_clears_the_park(self):
        self.reply("{id} 1")
        self.steps([BLOCKED, B_DONE, {"tick": False}, ask()])
        r = self.wf("two", "-y", "--max-wait", "0.002", mode="fast")
        q = self.queue()
        self.assertEqual(q["parks"], [], r.stdout)
        self.assertEqual([(d["feature"], d.get("case")) for d in q["decisions"]], [("1. A", None)])

    # covers: AC-3 (skip: the feature is skipped for this run only, no park and no question left)
    def test_skip(self):
        self.reply("{id} 2")
        self.steps([BLOCKED, B_DONE, {"tick": False}])
        r = self.wf("two", "-y", "--max-wait", "0.01", mode="fast")
        self.assertIn("skipped: 1. A: ", r.stdout)
        self.assertEqual(self.queue(), {"version": 1, "parks": [], "decisions": []})
        _, rec = self.run_record()
        # Spec 0011 AC-18: the answer reuses the feature's entry of this run.
        self.assertEqual([e["outcome"] for e in rec["features"]], ["skipped", "feature_done"])
        self.assertEqual(len(rec["calls"]), 3)

    # covers: AC-3 (an answer that is no option is a hint for the recommended option)
    def test_free_text_is_a_hint(self):
        self.reply("{id} code0001 use port 9000")
        self.steps([BLOCKED, B_DONE, {"tick": False}, {}, {}, {"tick": False}])
        r = self.wf("two", "-y", "--max-wait", "0.01", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(run.HINT_PROMPT.format("use port 9000"), self.prompt(4))

    # covers: AC-2, spec 0011 AC-3 (a question goes with its park once the park's cause changed: the feature
    # section was edited, so the next run starts it fresh)
    def test_question_goes_with_its_park(self):
        self.steps([BLOCKED, B_DONE, {"tick": False}])
        self.wf("two", "-y")
        scope = self.two / "docs/scope/scope.md"
        scope.write_text(scope.read_text().replace("- [ ] Test it: `/test a`", "- [ ] Test it well: `/test a`"))
        self.steps([{}, {}, {"tick": False}])
        (self.fakes / "count").unlink()
        for f in self.fakes.glob("argv-*.json"):
            f.unlink()
        r = self.wf("two", "-y")
        self.assertIn("stale: ", r.stdout)
        self.assertEqual(self.argv(1)["argv"][1], "/develop a")
        self.assertEqual(self.queue()["decisions"], [])


class TestRows(NeverStopCase):
    # covers: F8 (give it more doubles that cap for the feature, the rerun keeps its count)
    def test_give_it_more(self):
        self.reply("{id} 1")
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("demo", "-y", "--max-calls", "1", "--max-wait", "0.002", mode="fast")
        self.assertIn("parked: 1. Loop: max_calls: 1 calls made", r.stdout)
        self.assertIn("[2/2] demo: /test loop -> success", r.stdout)
        self.assertIn("parked: 1. Loop: max_calls: 2 calls made", r.stdout)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["case"], d["options"]), ("max_calls", ["give it more", "skip"]))

    # covers: F9 (a crashed call is retried once by itself, then asked)
    def test_call_error(self):
        self.steps([{"tick": False, "rc": 1}])
        r = self.wf("demo", "-y")
        self.assertEqual(len(self.calls()), 2)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["case"], d["options"]), ("call_error", ["retry", "skip"]))
        self.assertEqual(self.queue()["parks"], [], r.stdout)

    # covers: F6 (a box ticked without its proof line reruns once by itself, open again, the line asked for)
    def test_unchecked_reruns_once(self):
        self.make_repo("v", VERIFY)
        self.steps([{"json": {"result": "ok"}}, {}, {}, {"tick": False}])
        r = self.wf("v", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([self.argv(n)["argv"][1] for n in (1, 2, 3)], ["/check verify a", "/check verify a", "/test a"])
        self.assertIn(run.HINT_PROMPT.format(run.UNCHECKED_HINT), self.prompt(2))
        self.assertNotIn(run.UNCHECKED_HINT, self.prompt(3))
        self.assertEqual(self.queue()["decisions"], [])

    # covers: F6 (still missing after the rerun: asked)
    def test_unchecked_then_asks(self):
        self.make_repo("v", VERIFY)
        self.steps([{"json": {"result": "ok"}}])
        r = self.wf("v", "-y")
        self.assertEqual(len(self.calls()), 2)
        self.assertIn("parked: 1. A: unchecked", r.stdout)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["case"], d["options"]), ("unchecked", ["try again", "skip"]))

    # covers: F10 (a box only you can do is asked; done ticks it and the feature goes on)
    def test_human_box_done(self):
        self.make_repo("m", "# Scope: m\n**Autopilot:** allowed\n### 1. M · auto\n- [x] (spec)\n- [ ] `/develop m`\n"
                            "- [ ] Check it on the phone: `/qa m`\n- [ ] `/test m`\n")
        self.reply("{id} 1")
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("m", "-y", "--max-wait", "0.01", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("parked: 1. M: manual_box: /qa m runs only with you", r.stdout)
        self.assertIn("- [x] Check it on the phone: `/qa m`\n", (self.tmp / "root/m/docs/scope/scope.md").read_text())
        self.assertEqual([self.argv(n)["argv"][1] for n in (2, 3)], ["/test m", "/sync"])

    # covers: F10 (a live step is left to wf: no question)
    def test_live_box_not_asked(self):
        self.make_repo("l", "# Scope: l\n**Autopilot:** allowed\n### 1. L · auto\n- [x] (spec)\n- [ ] `/develop l`\n"
                            "- [ ] Copy it: `cp a b` · waits on you · live\n- [ ] `/test l`\n")
        self.steps([{}])
        r = self.wf("l", "-y")
        self.assertIn("parked: 1. L: waiting", r.stdout)
        self.assertNotIn("\nwaiting: ", r.stdout)
        self.assertEqual(self.queue()["decisions"], [])

    # covers: F11 (a box with no command: skip the box ticks it `· skipped` and the feature goes on)
    def test_skip_the_box(self):
        self.make_repo("n", "# Scope: n\n**Autopilot:** allowed\n### 1. N · auto\n- [x] (spec)\n- [ ] `/develop n`\n"
                            "- [ ] Think about it\n- [ ] `/test n`\n")
        self.reply("{id} 1")
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("n", "-y", "--max-wait", "0.01", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("- [x] Think about it · skipped\n", (self.tmp / "root/n/docs/scope/scope.md").read_text())

    # covers: F5 (undo them and try again passes the touched files into the rerun)
    def test_undo_hint(self):
        r = run.Run.__new__(run.Run)
        r.c, r.feature, r.hint, r.more, r.design_ok = SimpleNamespace(path=str(self.repo), scope_dir="docs/scope"), \
            "1. Loop", None, {}, set()
        f = r.apply_case({"case": "debug_touched", "detail": "tests/test_a.py", "box_text": None},
                         "undo them and try again", SimpleNamespace(name="1. Loop"))
        self.assertEqual(f.name, "1. Loop")
        self.assertEqual(r.hint, "first undo your edits to these test or spec files: tests/test_a.py")
        # F7: accept as is lets the feature's /sync run without a passing design report.
        r.apply_case({"case": "design_gate", "box_text": None}, "accept as is", SimpleNamespace(name="1. Loop"))
        self.assertEqual(r.design_ok, {(str(self.repo), "1. Loop")})

    # covers: F7 (accept as is: that feature's /sync goes on without a passing design report)
    def test_accept_as_is(self):
        (self.repo / "index.html").write_text("<p>x</p>\n")
        r = run.Run.__new__(run.Run)
        r.c, r.feature, r.entry, r.design_ok = SimpleNamespace(path=str(self.repo)), "1. Loop", {}, set()
        r.files_changed = lambda: None
        self.assertIn("index.html (no report)", r.design_check())
        r.design_ok.add((str(self.repo), "1. Loop"))
        self.assertIsNone(r.design_check())


class TestAllow(NeverStopCase):
    def setUp(self):
        super().setUp()
        rules = self.tmp / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "a.md").write_text("a\n")
        self.target = str(rules / "x.md")

    def deny(self, path):
        return {"tick": False, "json": {"permission_denials": [
            {"tool_name": "Write", "tool_use_id": "t1", "tool_input": {"file_path": path, "content": "x"}}]}}

    # covers: F1, AC-3 (allow once: the step runs again with that path writable, only that path)
    def test_allow_once(self):
        self.reply("{id} 1")
        self.steps([self.deny(self.target), {}, {}, {"tick": False}])
        r = self.wf("demo", "-y", "--max-wait", "0.01", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"waiting: ", r.stdout)
        self.assertIn(f"allow {self.target} for demo? ", r.stdout)
        rules = str(self.tmp / ".claude" / "rules")
        fs = self.settings(1)["sandbox"]["filesystem"]
        self.assertIn(rules, fs["denyWrite"])
        fs = self.settings(2)["sandbox"]["filesystem"]
        self.assertIn(self.target, fs["allowWrite"])
        self.assertNotIn(rules, fs["denyWrite"])
        self.assertIn(rules + "/a.md", fs["denyWrite"])
        self.assertNotIn(f"Edit(/{rules}/**)", self.denied(2))
        self.assertIn(f"Edit(/{rules}/a.md)", self.denied(2))
        self.assertIn(f"Edit(/{rules}/**)", self.denied(1))

    # covers: F1, AC-7 (always writes the standing permission line, and the run does not stop for it)
    def test_always(self):
        self.reply("{id} 2")
        self.steps([self.deny(self.target), {}, {}, {"tick": False}])
        r = self.wf("demo", "-y", "--max-wait", "0.01", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((self.repo / "AGENTS.md").read_text(),
                         "## Standing answers\n\n- allow writes: ~/.claude/rules/x.md\n")
        self.assertIn(self.target, self.settings(3)["sandbox"]["filesystem"]["allowWrite"])

    # covers: F1 (a secret is never offered: no allow options)
    def test_secret_never_offered(self):
        self.steps([self.deny(str(self.tmp / ".ssh" / "id_x"))])
        r = self.wf("demo", "-y")
        self.assertEqual(len(self.queue()["decisions"]), 1, r.stdout + r.stderr)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["options"], d["allow"]), (["try again", "skip"], None))


class TestStanding(NeverStopCase):
    def setUp(self):
        super().setUp()
        (self.tmp / ".claude").mkdir()
        self.settings_file = self.tmp / ".claude" / "settings.json"
        self.settings_file.write_text("{}")

    # covers: AC-7 (an allowed path is writable for every call and the guard takes a call's own change to it;
    # a secret inside it stays denied)
    def test_allowed_change_is_taken(self):
        (self.repo / "AGENTS.md").write_text("## Standing answers\n- allow writes: ~/.claude\n")
        self.steps([{"write_file": [[str(self.settings_file), '{"x": 1}']]}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        fs = self.settings(1)["sandbox"]["filesystem"]
        self.assertIn(str(self.tmp / ".claude"), fs["allowWrite"])
        self.assertIn(str(self.tmp / ".claude" / "private"), fs["denyWrite"])
        self.assertNotIn(str(self.settings_file), fs["denyWrite"])

    # covers: AC-7 (without the line the same change still stops)
    def test_without_line_stops(self):
        self.steps([{"write_file": [[str(self.settings_file), '{"x": 1}']]}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertIn("guard_changed", r.stdout)

    # covers: AC-7 (a secret path in the line is refused with a warning)
    def test_secret_line_warns(self):
        (self.repo / "AGENTS.md").write_text("## Standing answers\n- allow writes: ~/.ssh, runner/\n")
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertIn("warning: demo: allow writes: ~/.ssh is a secret path, refused", r.stdout)
        self.assertEqual(run.allow_paths(str(self.repo), "~/.ssh, runner/")[0], [str(self.repo / "runner")])

    # covers: AC-7 (the baseline moves only on the run's own call: a change after it still stops)
    def test_between_calls(self):
        inside, outside = self.tmp / ".claude" / "a.json", self.tmp / "b.json"
        for p in (inside, outside):
            p.write_text("1")
        h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        r = run.Run.__new__(run.Run)
        r.repo = {"guard": {"guarded_files": {str(inside): h(inside), str(outside): h(outside)}, "absent_denied": [],
                            "allowed": [str(self.tmp / ".claude")]}}
        for p in (inside, outside):
            p.write_text("2")
        r.accept_allowed()
        self.assertEqual([p for p, _ in run.moved(r.repo["guard"])], [str(outside)])
        inside.write_text("3")
        self.assertEqual([p for p, _ in run.moved(r.repo["guard"])], [str(inside), str(outside)])

    # covers: AC-7 (carve opens only the allowed path inside a denied folder)
    def test_carve(self):
        d = self.tmp / "d"
        (d / "sub").mkdir(parents=True)
        (d / "keep").write_text("")
        (d / "sub" / "open").write_text("")
        (d / "sub" / "shut").write_text("")
        got = run.carve([str(d), str(self.tmp / "other")], [str(d / "sub" / "open")])
        self.assertEqual(got, [str(d / "keep"), str(d / "sub" / "shut"), str(self.tmp / "other")])
        self.assertEqual(run.carve([str(d / "keep")], [str(d)]), [])


if __name__ == "__main__":
    unittest.main()
