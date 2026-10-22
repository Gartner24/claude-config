"""Spec 0014: runner resilience (outage waits, crash loop, tokens and cost, timeout unconfirmed boxes, live log,
a /sync box, skip ahead, the end to end fixture)."""
import json
import os
import shutil
import stat
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_browser import AppCase  # noqa: E402
from test_ntfy import FakeNtfy, write_config  # noqa: E402
from test_run import RUNNER, SCOPE, WF, RunCase, ask, before_brief, run, wf, without_brief_gaps  # noqa: E402

# Runs wf with a fake boot clock that each nap moves forward, so waits take no real time; FAKE_NAP acts in a nap.
WRAP = """import os, signal, sys
sys.path.insert(0, sys.argv[1])
import ntfy, run, wf
ntfy.RETRY_GAP = ntfy.POLL_EVERY = 0.05
d = os.environ["FAKE_DIR"]
shift = [0.0]
real = ntfy.boottime
ntfy.boottime = lambda: real() + shift[0]
def nap(self, seconds):
    open(os.path.join(d, "slept"), "a").write("%g\\n" % seconds)
    shift[0] += seconds
    act = os.environ.get("FAKE_NAP")
    if act == "autopilot_off":
        p = os.environ["FAKE_SCOPE"]
        open(p, "w").write(open(p).read().replace("**Autopilot:** allowed", "**Autopilot:** off"))
    elif act == "sigint":
        os.kill(os.getpid(), signal.SIGINT)
run.Run.nap = nap
sys.exit(wf.main(sys.argv[2:]))
"""

# A failed call the way Claude Code reports a 5xx (P3: api_error_status).
OUT = {"tick": False, "rc": 1, "json": {"is_error": True, "subtype": "success", "result": "boom", "api_error_status": 529}}
FAIL = {"tick": False, "rc": 1, "json": {"is_error": True, "subtype": "success", "result": "boom"}}
DENIED = {"tick": False, "json": {"permission_denials": [
    {"tool_name": "Bash", "tool_input": {"command": "rm -rf build"}, "tool_use_id": "t1"}]}}


def feature(n, name, *boxes):
    return f"### {n}. {name} · auto\n- [x] (spec)\n" + "".join(f"- [ ] {b}\n" for b in boxes) + "\n"


HEAD = "# Scope: x\n**Autopilot:** allowed\n\n"


class Case(RunCase):
    def wfx(self, *args, nap=None, extra=None):
        env = {**self.env, **(extra or {})}
        if nap:
            env.update(FAKE_NAP=nap, FAKE_SCOPE=str(self.repo / "docs/scope/scope.md"))
        # Spec 0021: a park is a phone question; no test waits the 12 hour default for its reply.
        if "--max-wait" not in args:
            args = (*args, "--max-wait", "0.0001")
        return subprocess.run([sys.executable, "-c", WRAP, str(RUNNER), "run", *args], capture_output=True, text=True,
                              env=env, timeout=120)

    def slept(self):
        p = self.fakes / "slept"
        return [float(x) for x in p.read_text().split()] if p.exists() else []

    def scope(self, text):
        (self.repo / "docs/scope/scope.md").write_text(text)

    def queue(self):
        p = self.state / "wf" / "queue.json"
        return json.loads(p.read_text()) if p.exists() else {"parks": [], "decisions": []}

    def commit(self, repo=None):
        """A clean tree, so a park does not hold the next feature back (spec 0011 AC-7 dirty tree rule)."""
        for args in (["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
            subprocess.run(["git", "-C", str(repo or self.repo), *args], check=True, capture_output=True)

    def fresh(self):
        """A new run folder and call count; queue.json stays."""
        shutil.rmtree(self.state / "wf" / "runs")
        for p in self.calls():
            p.unlink()
        (self.fakes / "count").unlink(missing_ok=True)


class TestOutage(Case):
    # covers: spec 0014 AC-1 (backoff 1 then 2 minutes, not counted, retry flag untouched, a later failure still retried)
    def test_backoff(self):
        self.steps([OUT, OUT, FAIL, {}, {}, {"tick": False}])
        r = self.wfx("demo", "-y", "--max-calls", "4")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual([c["outage"] for c in rec["calls"]], [True, True, False, False, False, False])
        self.assertEqual([w["minutes"] for w in rec["outage_waits"]], [1, 2])
        self.assertEqual(self.slept(), [15] * 12)
        # The plain failure after the outages still gets its one retry (spec 0008 AC-6).
        self.assertEqual([c["retry_of"] for c in rec["calls"]], [None, None, None, 3, None, None])
        self.assertEqual(rec["features"][0]["counted"], 4)
        self.assertEqual([c["command"] for c in rec["calls"]], ["/develop loop"] * 4 + ["/test loop", "/sync"])
        self.assertIn("[1/4] demo: /develop loop -> api_outage, 0.50 USD, 0.0m, next: outage wait", r.stdout)
        self.assertIn("waiting: API outage, sleeping 2m", r.stdout)
        self.assertEqual(rec["outage_waited_s"], 180)
        self.assertEqual(rec["outage_waits"][0]["error"], "success; boom")

    # covers: spec 0014 AC-1 as amended by spec 0021 U4 (failures until the cap stop the repo api_outage before the
    # wait that would pass the 12 hour wait cap)
    def test_cap(self):
        self.steps([OUT])
        rec = self.assert_stopped(self.wfx("demo", "-y"), "api_outage", calls=28)
        self.assertEqual([w["minutes"] for w in rec["outage_waits"]], [1, 2, 4, 8, 16] + [30] * 22)
        self.assertEqual(rec["detail"], "success; boom")
        self.assertEqual(rec["features"][0]["counted"], 0)
        # Spec 0021 U4: past the cap the repo asks.
        self.assertEqual([(d["reason"], d["options"]) for d in self.queue()["decisions"] if d.get("level") == "repo"],
                         [("api_outage", ["keep waiting", "stop this repo"])])

    # covers: spec 0014 AC-1 (`API Error: Connection error` in stderr with no JSON is an outage)
    def test_connection_error(self):
        self.steps([{"tick": False, "rc": 1, "raw": "", "stderr": "API Error: Connection error.\n"}, {}, {},
                    {"tick": False}])
        r = self.wfx("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual([c["outage"] for c in rec["calls"]], [True, False, False, False])
        self.assertEqual([w["minutes"] for w in rec["outage_waits"]], [1])

    # covers: spec 0014 AC-1 (a successful result naming an outage is not one; a usage limit text wins)
    def test_not_outage(self):
        self.steps([{"json": {"result": "fixed the overloaded_error handling"}}, {}, {"tick": False}])
        r = self.wfx("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual((rec["outage_waits"], [c["outage"] for c in rec["calls"]]), ([], [False] * 3))
        shutil.rmtree(self.state)
        self.scope(SCOPE)
        self.steps([{"tick": False, "rc": 1, "json": {"is_error": True, "result": "usage limit reached, overloaded_error",
                                                      "api_error_status": 529}}, {}, {}, {"tick": False}])
        # Spec 0021 U3: the limit sleeps and the call runs again.
        (self.fakes / "count").unlink(missing_ok=True)
        r = self.wfx("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual((rec["calls"][0]["limited"], rec["calls"][0]["outage"], rec["outage_waits"]), (True, False, []))

    # covers: spec 0014 AC-1 (Autopilot off during a wait stops the repo autopilot_off; Ctrl C stops interrupted)
    def test_wait_stops(self):
        self.steps([OUT])
        rec = self.assert_stopped(self.wfx("demo", "-y", nap="autopilot_off"), "autopilot_off", calls=1)
        self.assertEqual(len(rec["outage_waits"]), 1)
        shutil.rmtree(self.state)
        self.scope(SCOPE)
        (self.fakes / "count").unlink(missing_ok=True)
        rec = self.assert_stopped(self.wfx("demo", "-y", nap="sigint"), "interrupted", code=130, calls=1)
        self.assertEqual(self.slept()[-1], 15)

    # covers: spec 0014 AC-1 (the outage wait is subtracted from --max-hours)
    def test_max_hours(self):
        self.steps([OUT, {}, {}, {"tick": False}])
        r = self.wfx("demo", "-y", "--max-hours", "0.01")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.run_record()[1]["outage_waited_s"], 60)


class TestOutageApp(AppCase):
    # covers: spec 0014 AC-1 (the app is stopped before the outage wait and the rerun starts a new one)
    def test_restart(self):
        out = {**OUT, "run": [self.probe()]}
        self.steps([out, {"run": [self.probe()]}, {"tick": False, "run": [self.down()]}])
        r = self.wf("demo", "-y", mode="limit|2026-10-13T10:00:00+00:00|100000")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        a, b, _ = rec["calls"]
        self.assertEqual((a["outage"], a["app"]["logs"], b["app"]["logs"]), (True, ["app-01.log"], ["app-02.log"]))
        self.assertIsNotNone(a["app"]["exit"])
        self.assertEqual(b["retry_of"], None)


class TestCrashLoop(Case):
    THREE = HEAD + feature(1, "A", "`/develop a`") + feature(2, "B", "`/develop b`") + feature(3, "C", "`/develop c`")

    # covers: spec 0014 AC-2 (two features in a row parking denied the same way stop the run after the second park)
    def test_stop(self):
        self.scope(self.THREE)
        self.commit()
        self.steps([DENIED])
        r = self.wf("demo", "-y")
        self.assert_stopped(r, "crash_loop", calls=2)
        # Spec 0021 U6: only that repo stops, with its question.
        self.assertIn("stopped repo demo: crash_loop: denied: Bash: rm -rf build (also in 1. A)\n", r.stdout)
        self.assertEqual([p["feature"] for p in self.queue()["parks"]], ["1. A", "2. B"])
        log = (self.run_record()[0] / "log.txt").read_text()
        self.assertIn(" stop demo crash_loop: denied: Bash: rm -rf build (also in 1. A)\n", log)

    # covers: spec 0014 AC-2 (a different outcome between breaks the chain; two timeouts never count)
    def test_no_stop(self):
        self.scope(self.THREE)
        self.commit()
        # B's box is ticked and committed, so C may still start beside A's park.
        b_done = self.THREE.replace("- [ ] `/develop b`", "- [x] `/develop b`")
        commit = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "b"]
        self.steps([DENIED, {"tick": False, "write_file": [["docs/scope/scope.md", b_done]], "run": [commit]},
                    {"tick": False}, DENIED])
        rec = self.assert_stopped(self.wf("demo", "-y"), "denied", calls=4)
        self.assertEqual([e["outcome"] for e in rec["features"]], ["denied", "feature_done", "denied"])
        shutil.rmtree(self.state)
        (self.fakes / "count").unlink(missing_ok=True)
        self.scope(self.THREE)
        self.commit()
        self.steps([{"sleep": 30}])
        rec = self.assert_stopped(self.wf("demo", "-y", "--call-timeout", "0.01"), "call_timeout", calls=3)
        self.assertEqual([e["outcome"] for e in rec["features"]], ["call_timeout"] * 3)

    # covers: spec 0014 AC-2, spec 0017 (a bare wf run's children each see one repo, so the same park in two repos
    # is no crash loop; a detail differing in its first 60 characters breaks the chain)
    def test_repos_and_key(self):
        self.make_repo("other", HEAD + feature(1, "X", "`/develop x`"))
        self.steps([DENIED])
        r = self.wf("-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertNotIn("crash_loop", r.stdout)
        self.assertEqual({n: [e["outcome"] for e in rec["features"]] for n, rec in self.run_records().items()},
                         {"demo": ["denied"], "other": ["denied"]})
        shutil.rmtree(self.state)
        (self.fakes / "count").unlink(missing_ok=True)
        self.scope(HEAD + feature(1, "A", "`/develop a`") + feature(2, "B", "`/develop b`"))
        self.commit()
        long = "x" * 60
        self.steps([{"tick": False, "json": {"permission_denials": [
            {"tool_name": "Bash", "tool_input": {"command": long + " one"}, "tool_use_id": "t1"}]}},
            {"tick": False, "json": {"permission_denials": [
                {"tool_name": "Bash", "tool_input": {"command": long + " two"}, "tool_use_id": "t1"}]}}])
        # Same first 60 characters of "Bash: xxx..." though the commands differ: still a crash loop.
        rec = self.assert_stopped(self.wf("demo", "-y"), "crash_loop", calls=2)
        shutil.rmtree(self.state)
        (self.fakes / "count").unlink(missing_ok=True)
        self.steps([{"tick": False, "json": {"permission_denials": [
            {"tool_name": "Bash", "tool_input": {"command": "one " + long}, "tool_use_id": "t1"}]}},
            {"tick": False, "json": {"permission_denials": [
                {"tool_name": "Bash", "tool_input": {"command": "two " + long}, "tool_use_id": "t1"}]}}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "denied", calls=2)


class TestTokens(Case):
    # covers: spec 0014 AC-3 (per call tokens, feature and run sums, usage_partial, the spent line)
    def test_sums(self):
        u1 = {"input_tokens": 1000, "output_tokens": 200, "cache_read_input_tokens": 3000,
              "cache_creation_input_tokens": 300}
        u2 = {"input_tokens": 10, "output_tokens": 27, "cache_read_input_tokens": 30}
        # Spec 0055 AC-3: a split call carries models, keyed as modelUsage returns them.
        mu = {"claude-opus-5-5[1m]": {"outputTokens": 200, "costUSD": 0.7}, "claude-haiku-5-5": {"outputTokens": 9, "costUSD": 0.03}}
        self.steps([{"json": {"usage": u1, "total_cost_usd": 0.73, "modelUsage": mu}},
                    {"json": {"usage": u2}, "drop": ["total_cost_usd"]}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual(rec["calls"][0]["models"], {"claude-opus-5-5[1m]": {"cost_usd": 0.7, "output_tokens": 200},
                                                     "claude-haiku-5-5": {"cost_usd": 0.03, "output_tokens": 9}})
        self.assertIsNone(rec["calls"][1]["models"])
        self.assertEqual([c["tokens"] for c in rec["calls"]], [
            {"input": 1000, "output": 200, "cache_read": 3000, "cache_write": 300},
            {"input": 10, "output": 27, "cache_read": 30, "cache_write": None}, None])
        want = {"cost_usd": 1.23, "tokens": {"input": 1010, "output": 227, "cache_read": 3030, "cache_write": 300},
                "usage_partial": True}
        self.assertEqual({k: rec[k] for k in want}, want)
        self.assertEqual({k: rec["features"][0][k] for k in want}, want)
        self.assertEqual(r.stdout.splitlines()[-2], "spent: 1.23+ USD, 4567+ tokens")

    # covers: spec 0014 AC-3 (nothing known prints - for both; everything known has no +; a stop path prints it too)
    def test_unknown_and_full(self):
        self.steps([{"drop": ["total_cost_usd"]}, {"drop": ["total_cost_usd"]}, {"tick": False, "drop": ["total_cost_usd"]}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.stdout.splitlines()[-2], "spent: - USD, - tokens")
        self.assertEqual({k: self.run_record()[1][k] for k in ("cost_usd", "tokens", "usage_partial")},
                         {"cost_usd": None, "tokens": None, "usage_partial": True})
        shutil.rmtree(self.state)
        self.scope(SCOPE)
        (self.fakes / "count").unlink(missing_ok=True)
        u = {"input_tokens": 1, "output_tokens": 2, "cache_read_input_tokens": 3, "cache_creation_input_tokens": 4}
        self.steps([{"json": {"usage": u}}])
        r = self.wf("demo", "-y", mode="boom")
        self.assertIn("stopped repo demo: internal_error", r.stdout)
        self.assertEqual(r.stdout.splitlines()[-2], "spent: - USD, - tokens")
        shutil.rmtree(self.state)
        self.scope(SCOPE)
        (self.fakes / "count").unlink(missing_ok=True)
        self.steps([{"json": {"usage": u}}, {"json": {"usage": u}}, {"tick": False, "json": {"usage": u}}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.stdout.splitlines()[-2], "spent: 1.50 USD, 30 tokens")


class TestTimeout(Case):
    TICKED = SCOPE.replace("- [ ] Build it", "- [x] Build it")

    # covers: spec 0014 AC-4 (the boxes a timed out call ticked are named, the park has no cap, a larger
    # --call-timeout keeps it, unticking clears it; a timeout that ticked nothing keeps its cap)
    def test_unconfirmed(self):
        self.steps([{"write_file": [["docs/scope/scope.md", self.TICKED]], "sleep": 30, "tick": False}])
        rec = self.assert_stopped(self.wf("demo", "-y", "--call-timeout", "0.01"), "call_timeout", calls=1)
        detail = "still running after 0.01m; ticked before the timeout, recheck: Build it: `/develop loop`"
        self.assertEqual(rec["detail"], detail)
        self.assertEqual(rec["calls"][0]["unconfirmed"], ["Build it: `/develop loop`"])
        park = self.queue()["parks"][0]
        self.assertEqual((park["reason"], park["detail"], park["cap"]), ("call_timeout", detail, None))
        self.fresh()
        self.steps([{}, {"tick": False}])
        r = self.wf("demo", "-y", "--call-timeout", "60")
        self.assertIn("  parked: 1. Loop: call_timeout: still running after 0.01m; ticked before", r.stdout)
        self.assertEqual(self.calls(), [])
        # Unticking the box and ticking it again restores the section: the park holds.
        self.scope(SCOPE)
        self.scope(self.TICKED)
        self.assertEqual(self.wf("demo", "-y").returncode, 6)
        self.assertEqual(self.calls(), [])
        self.scope(SCOPE)
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.calls()), 3)

    def test_nothing_ticked(self):
        self.steps([{"sleep": 30}])
        rec = self.assert_stopped(self.wf("demo", "-y", "--call-timeout", "0.01"), "call_timeout", calls=1)
        self.assertEqual((rec["detail"], rec["calls"][0]["unconfirmed"]), ("still running after 0.01m", []))
        self.assertEqual(self.queue()["parks"][0]["cap"], 0.01)


class TestLiveLog(Case):
    # covers: spec 0014 AC-6 (a retry gets its own session id; log.txt events with the transcript path, mode 0600)
    def test_log(self):
        config = self.tmp / "claude-home"
        self.steps([FAIL, {}, {"tick": False, "json": {"result": "ok"}}, {"tick": False}])
        r = self.wfx("demo", "-y", extra={"CLAUDE_CONFIG_DIR": str(config)})
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        ids = [self.argv(n)["argv"][5] for n in (1, 2, 3)]
        self.assertEqual(len(set(ids)), 3)
        for i in ids:
            self.assertEqual(str(uuid.UUID(i, version=4)), i)
        folder, rec = self.run_record()
        log = folder / "log.txt"
        self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o600)
        events = without_brief_gaps([line.split(" ", 1)[1] for line in log.read_text().splitlines()])
        self.assertEqual(events, [
            "start demo",
            f"call 1 demo 1. Loop: /develop loop, transcript {config}/projects/*/{ids[0]}.jsonl",
            "end 1 success, 0.50 USD, 0.0m",
            f"call 2 demo 1. Loop: /develop loop, transcript {config}/projects/*/{ids[1]}.jsonl",
            "end 2 success, 0.50 USD, 0.0m",
            f"call 3 demo 1. Loop: /test loop, transcript {config}/projects/*/{ids[2]}.jsonl",
            "end 3 success, 0.50 USD, 0.0m",
            "park 1. Loop: no_progress: the box is still open: Test it: `/test loop`",
            # Spec 0042 AC-5: the question's plain account, one isolated call logged as one short line.
            next(e for e in events if e.startswith("call 1001 demo 1. Loop: explain, transcript ")),
            # Spec 0021 F4: the park's question, then the end wait for its reply.
            f"decision {rec['decisions'][0]['id']} 1. Loop", "wait answers",
            "done"])
        # The JSON's session id replaces the one wf gave.
        self.assertEqual(rec["calls"][0]["session_id"], "s-1")

    # covers: spec 0014 AC-6 (the outage and limit wait lines)
    def test_wait_lines(self):
        self.steps([OUT, {}, {}, {"tick": False}])
        self.wfx("demo", "-y")
        events = [line.split(" ", 1)[1] for line in (self.run_record()[0] / "log.txt").read_text().splitlines()]
        self.assertIn("wait outage 1m: success; boom", events)


class TestSyncBox(Case):
    # covers: spec 0014 AC-7 (b) (a sync box runs last with its box text and the prompt line, and passes only ticked)
    def test_runs_last(self):
        self.scope(HEAD + feature(1, "A", "Build it: `/develop a`", "Test it: `/test a`", "Sync docs: `/sync a`"))
        self.steps([{}, {}, {}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("  queued: 1. A", r.stdout)
        _, rec = self.run_record()
        self.assertEqual([(c["kind"], c["command"], c["box_text"]) for c in rec["calls"]], [
            ("box", "/develop a", "Build it: `/develop a`"), ("box", "/test a", "Test it: `/test a`"),
            ("sync", "/sync a", "Sync docs: `/sync a`")])
        self.assertEqual(rec["features"][0]["outcome"], "feature_done")
        prompt = lambda n: before_brief(self.argv(n)["argv"][self.argv(n)["argv"].index("--append-system-prompt") + 1])
        self.assertTrue(prompt(3).endswith(run.SYNC_BOX_PROMPT))
        self.assertFalse(prompt(2).endswith(run.SYNC_BOX_PROMPT))
        self.assertEqual(run.SYNC_BOX_PROMPT, " This call runs the feature's /sync box; when /sync is done, tick that box.")
        # No automatic /sync after it, and a finished feature is not in the next plan.
        self.fresh()
        r = self.wf("demo", "-y")
        self.assertNotIn("1. A", r.stdout)
        self.assertEqual(self.calls(), [])

    # covers: spec 0014 AC-7 (b) (a sync box call that asks keeps its box text on the Decision and its resume)
    def test_decision(self):
        fake = FakeNtfy()
        self.addCleanup(fake.close)
        write_config(self.tmp / "config", fake.url, codes=[f"code{i:04d}" for i in range(5)])
        self.scope(HEAD + feature(1, "A", "`/develop a`", "Sync docs: `/sync a`"))
        self.steps([{}, ask(), {}])
        r = self.wf("demo", "-y", "--max-wait", "0.0001", mode="fast")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        d = self.queue()["decisions"][0]
        self.assertEqual((d["call_kind"], d["command"], d["box_text"]), ("sync", "/sync a", "Sync docs: `/sync a`"))
        self.fresh()
        fake.replies = [f"{d['id']} 1"]
        r = self.wf("demo", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        c = self.run_record()[1]["calls"][0]
        self.assertEqual((c["kind"], c["box_text"], c["resumes"]), ("sync", "Sync docs: `/sync a`", [d["id"]]))
        self.assertTrue(before_brief(self.argv(1)["argv"][self.argv(1)["argv"].index("--append-system-prompt") + 1])
                        .endswith(run.SYNC_BOX_PROMPT))

    def test_unticked(self):
        self.scope(HEAD + feature(1, "A", "`/develop a`", "`/sync a`"))
        self.steps([{}, {"tick": False}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "no_progress", calls=2)
        self.assertEqual(rec["detail"], "the box is still open: `/sync a`")

    # covers: spec 0014 AC-7 (a sync box second of four runs last; no sync box keeps the automatic /sync)
    def test_order(self):
        self.scope(HEAD + feature(1, "A", "`/develop a`", "`/sync a`", "`/test a`", "`/check verify a`"))
        tick = lambda c: {"tick": False, "edit": [[f"- [ ] `{c}`", f"- [x] `{c}`"]]}
        self.steps([tick("/develop a"), tick("/test a"), tick("/check verify a"), tick("/sync a")])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([c["command"] for c in self.run_record()[1]["calls"]],
                         ["/develop a", "/test a", "/check verify a", "/sync a"])
        self.assertIn("next: /sync a", r.stdout)

    # covers: spec 0014 AC-7 (c), (d) (a sync box ticked by hand turns off the automatic /sync mid run too)
    def test_ticked_sync_box(self):
        self.scope(HEAD + "### 1. A · auto\n- [x] (spec)\n- [ ] `/develop a`\n- [x] `/sync a`\n")
        self.steps([{}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual(([c["command"] for c in rec["calls"]], rec["features"][0]["outcome"]),
                         (["/develop a"], "feature_done"))

    # covers: spec 0014 AC-7 (c) (every box ticked with a ticked sync box: nothing to run, not sync owed)
    def test_finished(self):
        self.scope(HEAD + "### 1. A · auto\n- [x] (spec)\n- [x] `/develop a`\n- [x] `/sync a`\n")
        r = self.wf("demo", "-y")
        self.assertNotIn("sync owed", r.stdout)
        self.assertIn("nothing to run", r.stdout)
        self.assertEqual(self.calls(), [])


class TestSkipAhead(Case):
    WAIT = "Copy the rule file live · waits on you · later boxes go on"

    # covers: spec 0014 AC-7 (a), AC-8 (the tagged box is passed, then the feature waits; after you tick it, /sync)
    def test_skip(self):
        self.scope(HEAD + feature(1, "A", "`/develop a`", self.WAIT, "`/test a`"))
        self.steps([{"tick": False, "edit": [["- [ ] `/develop a`", "- [x] `/develop a`"]]},
                    {"tick": False, "edit": [["- [ ] `/test a`", "- [x] `/test a`"]]}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "waiting", calls=2)
        self.assertEqual(rec["detail"], "Copy the rule file live · later boxes go on")
        self.assertEqual([c["command"] for c in rec["calls"]], ["/develop a", "/test a"])
        self.assertEqual(self.queue()["parks"], [])
        self.fresh()
        r = self.wf("demo", "-y")
        # Spec 0021 F10: the box only you can do is asked; done ticks it, and ticking it yourself drops the question.
        # Spec 0042 AC-1: in plain words, no tags.
        self.assertRegex(r.stdout, r"\n  open: [a-z0-9]{4} 1\. A: 1\. A needs one step only you can do: Copy the rule file live\n")
        self.assertEqual(self.calls(), [])
        self.fresh()
        self.scope((self.repo / "docs/scope/scope.md").read_text().replace("- [ ] Copy", "- [x] Copy"))
        self.steps([{"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([c["command"] for c in self.run_record()[1]["calls"]], ["/sync"])

    # covers: spec 0014 AC-8, spec 0012 (an untagged waiting box still stops the feature)
    def test_untagged(self):
        self.scope(HEAD + feature(1, "A", "`/develop a`", "Copy it · waits on you", "`/test a`"))
        self.steps([{"tick": False, "edit": [["- [ ] `/develop a`", "- [x] `/develop a`"]]}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "waiting", calls=1)
        self.assertEqual(rec["detail"], "waits on you: Copy it")

    # covers: spec 0014 AC-8 (next launches the box after a tagged one, refuses an untagged one, warns on a near miss)
    def test_next(self):
        def nxt():
            return subprocess.run([sys.executable, str(WF), "next", str(self.repo), "-y"], capture_output=True, text=True,
                                  env=self.env, timeout=30, stdin=subprocess.DEVNULL)
        self.scope(HEAD + feature(1, "A", self.WAIT, "`/test a`"))
        r = nxt()
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("claude '/test a'", r.stdout)
        self.scope(HEAD + feature(1, "A", "Copy it · waits on you", "`/test a`"))
        self.assertEqual(nxt().returncode, 3)
        # A tagged box with nothing after it in its feature stops as today.
        self.scope(HEAD + feature(1, "A", self.WAIT) + feature(2, "B", "`/test b`"))
        r = nxt()
        self.assertEqual(r.returncode, 3)
        self.assertIn("waits on you: Copy the rule file live · later boxes go on", r.stdout)
        self.scope(HEAD + feature(1, "A", "Copy it · waits on you · later boxes go on.", "`/test a`"))
        r = nxt()
        self.assertEqual(r.returncode, 3)
        self.assertIn('warning: "later boxes go on" is not the tag here, end the box with " · later boxes go on": '
                      'Copy it · waits on you · later boxes go on.', r.stdout)

    # covers: spec 0014 AC-8 (sub boxes are passed over with their box; the tag never counts on a note box)
    def test_pick(self):
        boxes = wf.parse_text("### A\n- [ ] Copy · waits on you · later boxes go on\n  - [ ] step one\n- [ ] `/test a`\n")
        self.assertEqual(wf.pick_next(boxes).command, "/test a")
        self.assertEqual(run.run_next(boxes).command, "/test a")
        boxes = wf.parse_text("### A\n- [ ] `/develop a`\n  - [ ] check · waits on you · later boxes go on\n"
                              "- [ ] `/test a`\n")
        nb = run.run_next(boxes)
        self.assertEqual((nb.command, run.box_refusal(nb)[0]), ("/develop a", "waiting"))
        self.assertEqual(wf.pick_next(boxes).command, "/develop a")


class TestFixture(Case):
    FAKE_WF = f"""#!{sys.executable}
import glob, json, os, sys
mode = open(os.path.join(os.environ["FAKE_DIR"], "wf-mode")).read()
open(os.path.join(os.environ["FAKE_DIR"], "wf-calls"), "a").write(" ".join(sys.argv[1:]) + "\\n")
if sys.argv[1] == "allow":
    sys.exit(0)
if mode == "fail":
    sys.exit(6)
repo = sys.argv[2]
scope = os.path.join(repo, "docs", "scope", "scope.md")
open(scope, "w").write(open(scope).read().replace("- [ ] ", "- [x] "))
open(os.path.join(repo, "calc.py"), "w").write("def add(a, b):\\n    return a + b\\n")
open(os.path.join(repo, "test_calc.py"), "w").write(
    "import unittest, calc\\nclass T(unittest.TestCase):\\n    def test_add(self):\\n        self.assertEqual(calc.add(2, 3), 5)\\n")
folder = os.path.join(os.environ["XDG_STATE_HOME"], "wf", "runs", "x")
os.makedirs(folder)
report = "failed: x" if mode == "unsent" else "sent"
json.dump({{"features": [{{"outcome": "feature_done"}}], "report": report}}, open(os.path.join(folder, "run.json"), "w"))
if mode != "no-report-txt":
    open(os.path.join(os.environ["XDG_STATE_HOME"], "wf", "report.txt"), "w").write("wf done 03:20\\n")
"""

    def e2e(self, mode):
        self.fake("wf", self.FAKE_WF)
        (self.fakes / "wf-mode").write_text(mode)
        tmp = self.tmp / "t"
        tmp.mkdir(exist_ok=True)
        env = {**self.env, "PATH": f"{self.bin}:{os.environ['PATH']}", "TMPDIR": str(tmp)}
        r = subprocess.run([sys.executable, str(RUNNER / "e2e" / "run.py")], capture_output=True, text=True, env=env,
                           timeout=60)
        return r, sorted(tmp.iterdir())

    # covers: spec 0014 AC-5 (PASS deletes the temp folders; FAIL names the check and keeps them)
    def test_run(self):
        r, left = self.e2e("pass")
        self.assertEqual((r.returncode, r.stdout), (0, "PASS\n"), r.stderr)
        self.assertEqual(left, [])
        calls = (self.fakes / "wf-calls").read_text().splitlines()
        self.assertTrue(calls[0].startswith("allow ") and calls[1].endswith(" -y --max-calls 10 --max-hours 1 --max-wait 0.25"), calls)
        r, left = self.e2e("fail")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(len(left), 1)
        self.assertEqual(r.stdout.splitlines(), ["FAIL: wf exit 6"] + [f"kept: {left[0] / n}" for n in ("repo", "state", "config")])
        cfg = left[0] / "config" / "wf" / "telegram.json"
        # The silent fake bot's config, never a copy of yours (no message reaches your phone).
        self.assertEqual(stat.S_IMODE(cfg.stat().st_mode), 0o600)
        self.assertEqual(json.loads(cfg.read_text())["chat_id"], 4242)
        self.assertFalse((left[0] / "config" / "wf" / "ntfy.json").exists())
        self.assertEqual(subprocess.run(["git", "-C", str(left[0] / "repo"), "branch", "--show-current"],
                                        capture_output=True, text=True).stdout, "wf-e2e\n")

    # covers: spec 0018 AC-8 (PASS needs report.txt in the temp state folder and "report": "sent" in run.json)
    def test_report_checks(self):
        for mode, line in (("unsent", "FAIL: run.json report 'failed: x'"), ("no-report-txt", "FAIL: no report.txt")):
            with self.subTest(mode):
                r, left = self.e2e(mode)
                self.assertEqual((r.returncode, r.stdout.splitlines()[0]), (1, line), r.stdout + r.stderr)
                shutil.rmtree(left[-1])

    # covers: spec 0014 AC-5 (the fixture scope parses with wf queue as one queued feature)
    def test_fixture_queues(self):
        repo = self.tmp / "root" / "fixture"
        shutil.copytree(RUNNER / "e2e" / "fixture", repo)
        subprocess.run(["git", "init", "-q", "-b", "wf-e2e", str(repo)], check=True)
        self.allow(repo)
        r = subprocess.run([sys.executable, str(WF), "queue", str(repo)], capture_output=True, text=True, env=self.env,
                           timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([l for l in r.stdout.splitlines() if l.startswith("  ") and ": " in l
                          and not l.startswith(("  answers", "  guard"))], ["  queued: 1. Add function"])
        self.assertIn("  answers: run suite yes, done yes", r.stdout)
