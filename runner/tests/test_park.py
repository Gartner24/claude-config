"""Spec 0008: failure and park policy for `wf run`."""
import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402
from test_ntfy import FakeNtfy, write_config  # noqa: E402
from test_run import WF, RunCase, ask  # noqa: E402

VERIFY = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n- [ ] Verify it: `/check verify a`\n- [ ] `/test a`\n"
GIT_ID = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]


def fail(marker="debug", text="2 checks failed\n"):
    return {"tick": False, "json": {"result": f"{text}VERIFY FAIL: {marker}\n"}}


LIMIT_TEXT = "You've hit your session limit · resets 6:20am (America/Bogota)"


def limited(text=LIMIT_TEXT, **extra):
    return {"tick": False, "json": {"is_error": True, "result": text}, **extra}


class TestParkSets(unittest.TestCase):
    # covers: spec 0011 AC-9, AC-10 (three scopes, never two for one reason; the recorded set)
    def test_sets(self):
        self.assertEqual(run.PARKS & run.REPO_STOPS, frozenset())
        self.assertEqual(run.PARKS & run.RUN_STOPS, frozenset())
        self.assertEqual(run.REPO_STOPS & run.RUN_STOPS, frozenset())
        self.assertEqual(run.PARKS, {"verify_failed", "blocked", "denied", "debug_touched", "no_progress", "call_error",
                                     "call_timeout", "budget", "max_calls", "manual_box", "waiting",
                                     "no_command", "no_feature", "app_failed", "design_gate"})
        self.assertEqual(run.REPO_STOPS, {"branch_changed", "autopilot_off", "scope_unreadable"})
        self.assertEqual(run.RUN_STOPS, {"interrupted", "run_limit", "usage_limit", "spawn_failed", "guard_changed",
                                         "ping_failed", "internal_error", "app_port_busy"})
        self.assertEqual(run.PARKS - run.RECORDED, {"call_error", "manual_box", "waiting", "no_command", "no_feature"})


class TestParkPrint(RunCase):
    # covers: spec 0011 AC-18, AC-19 (feature_done exits 0, a park exits 6 with the queue done line,
    # interrupted exits 130 and the running feature's outcome says so)
    def test_values(self):
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.run_record()[1]["features"][0]["outcome"], "feature_done")
        for name, steps, reason in [("np", [{"tick": False}], "no_progress"), ("mc", [{}], "max_calls")]:
            self.fresh(name)
            self.steps(steps)
            r = self.wf(name, "-y", "--max-calls", "1")
            self.assert_stopped(r, reason)
        self.assertIn("parked: 1. A: max_calls: 1 calls made\nqueue done: 0 done, 1 parked, 0 open\n", r.stdout)
        self.fresh("int")
        self.steps([{"sleep": 30}])
        p = self.start("int", "-y")
        self.wait_for(self.fakes / "argv-1.json")
        p.send_signal(signal.SIGINT)
        out, _ = p.communicate(timeout=20)
        self.assertEqual(p.returncode, 130)
        self.assertIn("stopped: interrupted", out)
        self.assertEqual(self.run_record()[1]["features"][0]["outcome"], "interrupted")

    def fresh(self, name):
        shutil.rmtree(self.state, ignore_errors=True)
        for f in [self.fakes / "count", *self.fakes.glob("argv-*.json")]:
            f.unlink(missing_ok=True)
        self.make_repo(name, VERIFY.replace("Verify it: `/check verify a`", "Build it: `/develop a`"))


class TestVerifyLoop(RunCase):
    # covers: AC-2 (two debug calls, then park; the debug command, its kind and the 1500 character tail)
    def test_two_attempts(self):
        self.make_repo("v", VERIFY)
        long = "x" * 1990 + "\n\x1b[31mred\x1b[0m line\n"
        self.steps([fail(text=long), {"tick": False}, fail(), {"tick": False}, fail()])
        r = self.wf("v", "-y")
        rec = self.assert_stopped(r, "verify_failed", calls=5)
        self.assertEqual(rec["detail"], "2 debug attempts made")
        self.assertEqual(rec["features"][0]["debug_attempts"], 2)
        self.assertEqual([c["kind"] for c in rec["calls"]], ["box", "debug", "box", "debug", "box"])
        self.assertEqual([c["marker"] for c in rec["calls"]],
                         ["verify_fail_debug", None, "verify_fail_debug", None, "verify_fail_debug"])
        self.assertEqual([c["box_text"] for c in rec["calls"]][:2], ["Verify it: `/check verify a`", None])
        result = long + "VERIFY FAIL: debug\n"
        want = "/debug a -- the last /check verify failed:\n" + "\n".join(
            l.replace("\x1b", "") for l in result[-1500:].split("\n"))
        self.assertEqual(self.argv(2)["argv"][1], want)
        self.assertEqual(rec["calls"][1]["command"], want)
        self.assertIn("next: /debug a -- the last /check verify failed:", r.stdout)
        self.assertNotIn("xxxxxxxxxx\n", r.stdout)

    # covers: AC-2 (develop parks at once with the marker line and 5 lines before it; any other value is develop)
    def test_develop(self):
        for marker in ("develop", "maybe"):
            with self.subTest(marker):
                shutil.rmtree(self.state, ignore_errors=True)
                (self.fakes / "count").unlink(missing_ok=True)
                self.make_repo("v" + marker, VERIFY)
                text = "intro\n" + "".join(f"line {i}\n\n" for i in range(1, 7))
                self.steps([fail(marker, text)])
                rec = self.assert_stopped(self.wf("v" + marker, "-y"), "verify_failed", calls=1)
                self.assertEqual(rec["detail"], f"line 2 line 3 line 4 line 5 line 6 VERIFY FAIL: {marker}")
                self.assertEqual((rec["calls"][0]["marker"], rec["features"][0]["debug_attempts"]),
                                 ("verify_fail_develop", 0))

    # covers: AC-2 (a verify box with no arguments; a marker on another command is ignored)
    def test_bare_and_other(self):
        self.make_repo("bare", "# Scope: x\n**Autopilot:** allowed\n### 1. A · auto\n- [x] (spec)\n- [ ] `/check verify`\n- [ ] `/test a`\n")
        self.steps([fail(text=""), {"tick": False}, {}])
        self.wf("bare", "-y", "--max-calls", "2")
        self.assertEqual(self.argv(2)["argv"][1], "/debug -- the last /check verify failed:\nVERIFY FAIL: debug\n")
        self.make_repo("dev", "# Scope: x\n**Autopilot:** allowed\n### 1. A · auto\n- [x] (spec)\n- [ ] `/develop a`\n- [ ] `/test a`\n")
        shutil.rmtree(self.state)
        (self.fakes / "count").unlink()
        self.steps([{"json": {"result": "VERIFY FAIL: develop"}}])
        r = self.wf("dev", "-y", "--max-calls", "1")
        rec = self.assert_stopped(r, "max_calls")
        self.assertIsNone(rec["calls"][0]["marker"])


class TestDebugGuard(RunCase):
    def setUp(self):
        super().setUp()
        self.v = self.make_repo("g", "# Scope: x\n**Autopilot:** allowed\n### 1. A · auto\n- [x] (spec)\n- [ ] `/develop a`\n"
                                     "- [ ] Verify it: `/check verify a`\n- [ ] `/test a`\n")
        (self.v / "docs" / "specs").mkdir()
        (self.v / "docs" / "specs" / "x.md").write_text("# spec\n")
        (self.v / "tests").mkdir()
        (self.v / "tests" / "test_a.py").write_text("import unittest\n\ndef test_a():\n    pass\n\ndef test_b():\n    pass\n")
        subprocess.run(["git", *GIT_ID, "-C", str(self.v), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", *GIT_ID, "-C", str(self.v), "commit", "-qm", "base"], check=True, capture_output=True)

    def run_debug(self, debug_step, earlier=None):
        self.steps([earlier or {}, fail(), {"tick": False, **debug_step}, {}])
        return self.wf("g", "-y", "--max-calls", "4")

    # covers: AC-3 (each forbidden change parks debug_touched naming the path)
    def test_parks(self):
        cases = [
            ("spec edit", {"write_file": [["docs/specs/x.md", "# changed\n"]]}, "docs/specs/x.md"),
            ("spec added", {"write_file": [["docs/specs/new.md", "x\n"]]}, "docs/specs/new.md"),
            ("test deleted", {"rm": ["tests/test_a.py"]}, "tests/test_a.py"),
            ("skip added", {"write_file": [["tests/test_a.py", "import unittest\n\n@unittest.skip('x')\ndef test_a():\n"
                                                               "    pass\n\ndef test_b():\n    pass\n"]]}, "tests/test_a.py"),
            ("test removed", {"write_file": [["tests/test_a.py", "def test_a():\n    pass\n"]]}, "tests/test_a.py"),
            ("new skipped file", {"write_file": [["tests/test_n.py", "import pytest\npytest.skip('x')\n"]]},
             "tests/test_n.py"),
            ("committed spec edit", {"write_file": [["docs/specs/x.md", "# c\n"]],
                                     "run": [["git", *GIT_ID, "commit", "-qam", "x"]]}, "docs/specs/x.md"),
        ]
        for name, step, path in cases:
            with self.subTest(name):
                shutil.rmtree(self.state, ignore_errors=True)
                (self.fakes / "count").unlink(missing_ok=True)
                subprocess.run(["git", "-C", str(self.v), "reset", "-q", "--hard", "HEAD"], check=True)
                subprocess.run(["git", "-C", str(self.v), "clean", "-qfd"], check=True)
                rec = self.assert_stopped(self.run_debug(step), "debug_touched", calls=3)
                self.assertEqual(rec["detail"], path)
                self.assertEqual(rec["calls"][2]["touched"], [path])
                self.assertEqual([c["touched"] for c in rec["calls"][:2]], [None, None])

    # covers: AC-3 (a rename inside one file plus a new test passes; earlier calls' verify.md and tests do not trip it)
    def test_passes(self):
        step = {"write_file": [["tests/test_a.py", "def test_a():\n    pass\n\ndef test_c():\n    pass\n"],
                               ["tests/test_new.py", "def test_x():\n    pass\n"]]}
        earlier = {"write_file": [["docs/specs/x/verify.md", "- [ ] check\n"], ["tests/test_old.py", "def test_o(): pass\n"]]}
        rec = self.assert_stopped(self.run_debug(step, earlier), "max_calls", calls=4)
        self.assertEqual(rec["calls"][2]["touched"], [])
        self.assertEqual(rec["calls"][3]["command"], "/check verify a")


class TestTouched(unittest.TestCase):
    # covers: AC-3 (test file patterns, definition counts, skip markers, deletions)
    def test_patterns(self):
        for rel, want in [("tests/a.py", True), ("src/__tests__/a.js", True), ("spec/a_spec.rb", True),
                          ("test_x.py", True), ("x_test.go", True), ("a.test.ts", True), ("a.spec.js", True),
                          ("docs/specs/x.md", False), ("src/contest.py", False), ("latest.py", False)]:
            self.assertIs(run.is_test_file(rel), want, rel)
        t = lambda text: ("h", text)
        before = {"tests/test_a.py": t("it('a', x)\nit('b', y)\n"), "x.test.js": t("test('a')\n")}
        self.assertEqual(run.touched(before, {"tests/test_a.py": t("it('a', x)\nxit('b', y)\n"),
                                              "x.test.js": t("test('a')\n")}), ["tests/test_a.py"])
        self.assertEqual(run.touched(before, {"tests/test_a.py": t("it('a', x)\nit('c', y)\n"),
                                              "x.test.js": t("test('a')\ntest('b')\n")}), [])
        self.assertEqual(run.touched(before, {"tests/test_a.py": t("it('a', x)\nit('b', y)\n")}), ["x.test.js"])


class TestBlocked(RunCase):
    # covers: AC-4 (BLOCKED parks with its text and wins over DECISION NEEDED, which then records nothing)
    def test_blocked(self):
        result = "Need a package.\nDECISION NEEDED: which one?\nOPTION: a\n**BLOCKED:** sudo pacman -S stow\n"
        self.steps([{"tick": False, "json": {"result": result}}])
        r = self.wf("demo", "-y")
        rec = self.assert_stopped(r, "blocked", calls=1)
        self.assertEqual(rec["detail"], "sudo pacman -S stow")
        self.assertEqual((rec["calls"][0]["marker"], rec["calls"][0]["decision"], rec["decisions"]), ("blocked", None, []))
        self.assertIn("parked: 1. Loop: blocked: sudo pacman -S stow", r.stdout)


DENIALS = [{"tool_name": "AskUserQuestion", "tool_use_id": "toolu_ask", "tool_input": {"questions": []}},
           {"tool_name": "Bash", "tool_use_id": "toolu_bash", "tool_input": {"command": "sudo pacman -S stow"}}]


class TestDenials(RunCase):
    def transcript(self, sid="s-1"):
        cc = self.tmp / "cc"
        self.env["CLAUDE_CONFIG_DIR"] = str(cc)
        d = cc / "projects" / "-x"
        d.mkdir(parents=True, exist_ok=True)
        lines = [{"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "toolu_bash"}]}},
                 {"type": "user", "toolUseResult": "Error: PreToolUse:Bash hook error: \x1b[1mno sudo\x1b[0m"},
                 {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "toolu_ask"}]}}]
        lines[1]["message"] = {"content": [{"type": "tool_result", "tool_use_id": "toolu_bash"}]}
        (d / f"{sid}.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\nnot json\n")

    # covers: AC-5 (records with reasons, park denied on the first non AskUserQuestion denial)
    def test_park(self):
        self.transcript()
        self.steps([{"tick": False, "json": {"permission_denials": DENIALS}}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "denied", calls=1)
        self.assertEqual(rec["calls"][0]["denials"], [
            {"tool": "AskUserQuestion", "input": '{"questions": []}', "reason": None},
            {"tool": "Bash", "input": "sudo pacman -S stow", "reason": "Error: PreToolUse:Bash hook error: [1mno sudo[0m"}])
        self.assertEqual(rec["detail"], "Bash: Error: PreToolUse:Bash hook error: [1mno sudo[0m")

    # covers: AC-5 (no transcript: null reason, the input is the detail; only AskUserQuestion: it is the detail;
    # a call that progressed keeps going)
    def test_fallbacks(self):
        self.steps([{"tick": False, "json": {"permission_denials": DENIALS[1:]}}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "denied", calls=1)
        self.assertEqual(rec["detail"], "Bash: sudo pacman -S stow")
        self.assertIsNone(rec["calls"][0]["denials"][0]["reason"])
        shutil.rmtree(self.state)
        (self.fakes / "count").unlink()
        self.steps([{"tick": False, "json": {"permission_denials": DENIALS[:1]}}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "denied", calls=1)
        self.assertEqual(rec["detail"], 'AskUserQuestion: {"questions": []}')
        shutil.rmtree(self.state)
        (self.fakes / "count").unlink()
        self.steps([{"json": {"permission_denials": DENIALS}}, {}, {"tick": False}])
        self.assertEqual(self.wf("demo", "-y").returncode, 0)

    # covers: AC-5 (an unsafe session id is never globbed; a long input is cut to 200)
    def test_unit(self):
        self.assertIsNone(run.denial_reason("../x", "toolu_bash"))
        got = run.denials({"session_id": "s", "permission_denials": [
            {"tool_name": "Bash", "tool_input": {"command": "y" * 300}}, "junk"]})
        self.assertEqual((len(got), len(got[0]["input"]), got[0]["reason"]), (1, 200, None))
        self.assertEqual(run.denials({"permission_denials": "junk"}), [])


class TestRetry(RunCase):
    # covers: AC-6 (one failure then success continues; error_max_turns parks with no retry)
    def test_retry(self):
        self.steps([{"tick": False, "json": {"is_error": True}}, {}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual([(c["command"], c["retry_of"]) for c in rec["calls"]],
                         [("/develop loop", None), ("/develop loop", 1), ("/test loop", None), ("/sync", None)])
        self.assertIn("[1/20] demo: /develop loop -> success, 0.50 USD, 0.0m, next: retry", r.stdout)
        shutil.rmtree(self.state)
        (self.fakes / "count").unlink()
        self.steps([{"tick": False, "json": {"subtype": "error_max_turns", "is_error": True}}])
        self.assert_stopped(self.wf("demo", "-y"), "call_error", calls=1)

    # covers: AC-6 (a failure clears only on a call that does not fail: fail, ok, fail, ok runs on)
    def test_flag_clears(self):
        self.make_repo("four", "# Scope: x\n**Autopilot:** allowed\n### 1. A · auto\n- [x] (spec)\n- [ ] `/develop a`\n- [ ] `/test a`\n")
        self.steps([{"tick": False, "rc": 1}, {}, {"tick": False, "rc": 1}, {}, {"tick": False}])
        r = self.wf("four", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # covers: AC-6 (the rule 7 guard runs before the retry: a branch change stops, no rerun)
    def test_guard_before_retry(self):
        self.steps([{"tick": False, "rc": 1, "head": "ref: refs/heads/other\n"}])
        self.assert_stopped(self.wf("demo", "-y"), "branch_changed", calls=1)

    # covers: AC-6 (a failed resume reruns as --resume with the same session id and prompt)
    def test_resume_retry(self):
        ntfy = FakeNtfy()
        self.addCleanup(ntfy.close)
        write_config(self.tmp / "config", ntfy.url, codes=[f"code{i:04d}" for i in range(5)])
        ntfy.replies = ["{id} 1"]
        self.steps([ask(), {"tick": False, "rc": 1}, {}, {}, {"tick": False}])
        r = self.wf("demo", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.argv(2)["argv"][:4], self.argv(3)["argv"][:4])
        self.assertEqual(self.argv(3)["argv"][2:4], ["--resume", "s-1"])
        _, rec = self.run_record()
        self.assertEqual([c["retry_of"] for c in rec["calls"]][:3], [None, None, 2])


class TestPaidEnv(RunCase):
    # covers: AC-7 (paid keys and cloud switches gone from every call, the login token and PATH kept)
    def test_env(self):
        gone = ["GEMINI_API_KEY", "AWS_SECRET_ACCESS_KEY", "MY_SECRET_THING", "ANTHROPIC_API_KEY", "HF_TOKEN",
                "AWS_ACCESS_KEY_ID", "CLAUDE_CODE_USE_BEDROCK", "DB_PASSWORD", "openai_api_key", "X_API_TOKEN",
                "GOOGLE_APPLICATION_CREDENTIALS", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_USE_VERTEX",
                "CLAUDE_CODE_USE_FOUNDRY", "S3_ACCESS_KEY", "APP_SECRET"]
        for k in gone:
            self.env[k] = "x"
        self.env["CLAUDE_CODE_OAUTH_TOKEN"] = "login"
        self.env["TOKENIZER"] = "keep"
        ntfy = FakeNtfy()
        self.addCleanup(ntfy.close)
        write_config(self.tmp / "config", ntfy.url, codes=[f"code{i:04d}" for i in range(5)])
        ntfy.replies = ["{id} 1"]
        self.steps([ask(), {}, {"tick": False}])
        self.wf("demo", "-y", "--max-calls", "2", mode="fast")
        for n in (1, 2):
            env = self.argv(n)["env"]
            self.assertEqual([k for k in gone if k in env], [])
            self.assertEqual((env["CLAUDE_CODE_OAUTH_TOKEN"], env["TOKENIZER"], env["PATH"]),
                             ("login", "keep", str(self.bin)))
        self.assertEqual(self.argv(2)["argv"][2], "--resume")


class TestLimit(RunCase):
    def mode(self, at, scale=100000):
        return f"limit|{at}|{scale}"

    def slept(self):
        p = self.fakes / "slept"
        return p.read_text().split() if p.exists() else []

    def fresh(self):
        shutil.rmtree(self.state, ignore_errors=True)
        for f in ("count", "slept"):
            (self.fakes / f).unlink(missing_ok=True)

    # covers: AC-8 (sleeps to 2 minutes after the reset, reruns the same command, not counted, record)
    def test_wait_and_rerun(self):
        self.steps([limited(), {}, {}, {"tick": False}])
        r = self.wf("demo", "-y", "--max-calls", "3", mode=self.mode("2026-10-12T06:00:00-05:00"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.slept(), ["1320"])
        _, rec = self.run_record()
        self.assertEqual([(c["seq"], c["command"], c["limited"]) for c in rec["calls"]],
                         [(1, "/develop loop", True), (2, "/develop loop", False), (3, "/test loop", False),
                          (4, "/sync", False)])
        lw = rec["limit_wait"]
        self.assertEqual(sorted(lw), ["reset", "resumed", "started", "waited_s"])
        self.assertEqual(lw["reset"], "2026-10-12T06:20:00-05:00")
        self.assertIsNotNone(lw["resumed"])
        self.assertEqual(rec["limit_waited_s"], lw["waited_s"])
        self.assertIn("[1/3] demo: /develop loop -> usage_limit", r.stdout)
        self.assertIn("[1/3] demo: /develop loop -> success", r.stdout)
        self.assertIn("waiting: usage limit, resets 2026-10-12T06:20-05:00, sleeping 22m", r.stdout)
        self.assertEqual(sorted(p.name for p in self.run_record()[0].iterdir() if p.suffix == ".json"),
                         ["call-01.json", "call-02.json", "call-03.json", "call-04.json", "run.json"])

    # covers: AC-8 (only a failed call is a limit; budget wins; stderr is read; one minute past sleeps 2 minutes)
    def test_detection(self):
        self.steps([{"json": {"result": "we hit the rate_limit"}}, {}, {"tick": False}])
        self.assertEqual(self.wf("demo", "-y", mode=self.mode("2026-10-12T06:00:00-05:00")).returncode, 0)
        self.assertEqual(self.slept(), [])
        self.fresh()
        self.steps([limited(json={"is_error": True, "subtype": "error_max_budget_usd", "result": LIMIT_TEXT})])
        self.assert_stopped(self.wf("demo", "-y", mode=self.mode("2026-10-12T06:00:00-05:00")), "budget")
        self.fresh()
        self.steps([{"tick": False, "rc": 1, "raw": "", "stderr": LIMIT_TEXT + "\n"}, {"tick": False}])
        self.wf("demo", "-y", "--max-calls", "1", mode=self.mode("2026-10-12T06:21:00-05:00"))
        self.assertEqual(self.slept(), ["120"])

    # covers: AC-8 (a second limit, a far reset, no reset, an unknown zone: stop usage_limit, no further sleep)
    def test_stops(self):
        at = self.mode("2026-10-12T06:00:00-05:00")
        self.steps([limited(), limited()])
        rec = self.assert_stopped(self.wf("demo", "-y", mode=at), "usage_limit", calls=2)
        self.assertEqual(self.slept(), ["1320"])
        self.assertIn("hit your session limit", rec["detail"])
        for name, step, mode, detail in [
                ("far", limited(), self.mode("2026-10-12T23:00:00-05:00"), "resets 2026-10-13T06:20-05:00, more than 6h away"),
                ("none", limited("usage limit reached"), at, "no readable reset: "),
                ("zone", limited("hit your limit, resets 6am (Mars/Base)"), at, "no readable reset: ")]:
            with self.subTest(name):
                self.fresh()
                self.steps([step])
                rec = self.assert_stopped(self.wf("demo", "-y", mode=mode), "usage_limit", calls=1)
                self.assertTrue(rec["detail"].startswith(detail), rec["detail"])
                self.assertEqual(self.slept(), [])
                self.assertIsNone(rec["limit_wait"])

    def start_sleeping(self):
        self.steps([limited(), {}])
        p = self.start("demo", "-y", mode=self.mode("2026-10-12T06:00:00-05:00", 132))
        self.wait_for(self.fakes / "slept")
        time.sleep(0.5)
        return p

    # covers: AC-8 (Autopilot set off during the sleep stops before the rerun)
    def test_autopilot_off_during_sleep(self):
        p = self.start_sleeping()
        scope = self.repo / "docs/scope/scope.md"
        scope.write_text(scope.read_text().replace("**Autopilot:** allowed", "**Autopilot:** off"))
        out, err = p.communicate(timeout=30)
        self.assertEqual(p.returncode, 6, out + err)
        _, rec = self.run_record()
        self.assertEqual((rec["repos"][0]["ended"], len(rec["calls"])), ("autopilot_off", 1))
        self.assertGreater(rec["limit_waited_s"], 9)

    # covers: AC-8 (Ctrl C during the sleep stops interrupted at once)
    def test_sigint_during_sleep(self):
        p = self.start_sleeping()
        t = time.monotonic()
        p.send_signal(signal.SIGINT)
        out, err = p.communicate(timeout=20)
        self.assertLess(time.monotonic() - t, 3)
        self.assertEqual(p.returncode, 130, out + err)
        _, rec = self.run_record()
        self.assertEqual((rec["stop_reason"], len(rec["calls"]), rec["limit_wait"]["resumed"]), ("interrupted", 1, None))

    # covers: AC-8 (the sleep does not count toward --max-hours)
    def test_max_hours(self):
        self.steps([limited(), {}, {}, {"tick": False}])
        r = self.wf("demo", "-y", "--max-hours", "0.0003", mode=self.mode("2026-10-12T06:00:00-05:00", 1320 / 1.5))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertGreater(self.run_record()[1]["limit_waited_s"], 1.4)


class TestParseReset(unittest.TestCase):
    # covers: AC-8 (12 hour clock, minutes optional, next occurrence, 2 minute grace, bad values)
    def test_cases(self):
        at = datetime.datetime(2026, 10, 12, 6, 0, tzinfo=ZoneInfo("America/Bogota"))
        bog = lambda d, h, m: datetime.datetime(2026, 10, d, h, m, tzinfo=ZoneInfo("America/Bogota"))
        for text, want in [("resets 6:20am (America/Bogota)", bog(12, 6, 20)),
                           ("Resets 12am (America/Bogota)", bog(13, 0, 0)),
                           ("resets 12:30 PM (America/Bogota)", bog(12, 12, 30)),
                           ("resets 5:59am (America/Bogota)", bog(12, 5, 59)),
                           ("resets 5:57am (America/Bogota)", bog(13, 5, 57)),
                           ("resets 13am (America/Bogota)", None), ("resets 6:61am (America/Bogota)", None),
                           ("resets 6am (Not/AZone)", None), ("resets 6am (../../etc/passwd)", None),
                           ("resets soon", None)]:
            with self.subTest(text):
                self.assertEqual(run.parse_reset(text, at), want)
        madrid = run.parse_reset("resets 2pm (Europe/Madrid)", at)
        self.assertEqual(madrid - at, datetime.timedelta(hours=1))


class TestTrust(RunCase):
    # covers: AC-9 (wf allow adds the real path once, 0600 in a 0700 folder under XDG_CONFIG_HOME)
    def test_allow(self):
        p = self.tmp / "config" / "wf" / "allowed.json"
        p.unlink()
        (self.tmp / "link").symlink_to(self.repo)
        for _ in range(2):
            r = subprocess.run([sys.executable, str(WF), "allow", str(self.tmp / "link")], capture_output=True,
                               text=True, env=self.env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout, f"allowed: {self.repo}\n")
        self.assertEqual(json.loads(p.read_text()), [str(self.repo)])
        self.assertEqual((os.stat(p).st_mode & 0o777, os.stat(p.parent).st_mode & 0o777), (0o600, 0o700))
        r = subprocess.run([sys.executable, str(WF), "allow", "nothing-like-this"], capture_output=True, text=True,
                           env=self.env)
        self.assertEqual(r.returncode, 1)
        p.write_text("{broken")
        r = subprocess.run([sys.executable, str(WF), "allow", "demo"], capture_output=True, text=True, env=self.env)
        self.assertEqual((r.returncode, p.read_text()), (1, "{broken"))

    # covers: AC-9 (not listed, missing, broken, not a list of strings: refused untrusted, exit 5, no lock, no run)
    def test_refusals(self):
        p = self.tmp / "config" / "wf" / "allowed.json"
        for name, text, detail in [("unlisted", '["/elsewhere"]', f"{self.repo} is not listed, run wf allow "),
                                   ("missing", None, f"{p} is missing, run wf allow <repo>"),
                                   ("broken", "{broken", f"{p} is not a JSON list of paths"),
                                   ("numbers", "[1, 2]", f"{p} is not a JSON list of paths")]:
            with self.subTest(name):
                if text is None:
                    p.unlink(missing_ok=True)
                else:
                    p.write_text(text)
                r = self.wf("demo", "-y")
                self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
                self.assertIn(f"refused: untrusted: {detail}", r.stdout)
                self.assertEqual(self.calls(), [])
                self.assertFalse((self.state / "wf" / "locks").exists())
                self.assertFalse((self.state / "wf" / "runs").exists())


class TestRecord(RunCase):
    # covers: AC-10 (run.json and call fields after a mixed run: retry, verify fail, debug, done)
    def test_fields(self):
        self.make_repo("mix", VERIFY)
        self.steps([{"tick": False, "rc": 1}, fail(), {"tick": False}, {}, {}, {"tick": False}])
        r = self.wf("mix", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual((rec["features"][0]["outcome"], rec["features"][0]["debug_attempts"], rec["limit_wait"],
                          rec["limit_waited_s"]), ("feature_done", 1, None, 0))
        self.assertEqual([(c["seq"], c["kind"], c["marker"], c["limited"], c["retry_of"], c["touched"], c["denials"])
                          for c in rec["calls"]],
                         [(1, "box", None, False, None, None, []), (2, "box", "verify_fail_debug", False, 1, None, []),
                          (3, "debug", None, False, None, [], []), (4, "box", None, False, None, None, []),
                          (5, "box", None, False, None, None, []), (6, "sync", None, False, None, None, [])])


if __name__ == "__main__":
    unittest.main()
