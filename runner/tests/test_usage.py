"""Spec 0022: usage limit planning."""
import datetime
import http.server
import io
import json
import os
import signal
import socket
import sys
import tempfile
import shutil
import threading
import time
import types
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402
import usage  # noqa: E402
import wf  # noqa: E402
import test_park  # noqa: E402
import test_run  # noqa: E402
from test_park import limited  # noqa: E402
from test_queue import DONE_A, ONE, TICK_A  # noqa: E402
from test_wf_bare import BareCase  # noqa: E402

TOKEN = "sk-ant-oat01-PLANTED-TOKEN-7f3e9c"
ANSWER = {"five_hour": {"utilization": 14.0, "resets_at": "2026-10-14T05:00:00.819794+00:00"},
          "seven_day": {"utilization": 89.0, "resets_at": "2026-10-14T22:00:00.819817+00:00"}}


def at(iso):
    return datetime.datetime.fromisoformat(iso)


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class StateCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.live = self.tmp / "claude"
        self.live.mkdir()
        env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.tmp / "state"), "CLAUDE_CONFIG_DIR": str(self.live)})
        env.start()
        self.addCleanup(env.stop)
        for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"):
            os.environ.pop(k, None)
        p = mock.patch.object(run, "claude_version", return_value="2.1.296")
        p.start()
        self.addCleanup(p.stop)
        usage._version.clear()

    def creds(self, token=TOKEN):
        (self.live / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {"accessToken": token}}))

    def state(self):
        return self.tmp / "state" / "wf"


class TestRead(StateCase):
    # covers: AC-1 (one GET with the status line's headers; every path: success, HTTP 401, timeout, bad JSON; the
    # token in no output and no file of the state folder)
    def test_token_never_leaves(self):
        self.creds()
        seen = []

        def ok(req, timeout):
            seen.append((req.full_url, dict(req.header_items()), timeout))
            return Reply(json.dumps(ANSWER).encode())

        def denied(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized " + req.get_header("Authorization"), {}, None)

        def slow(req, timeout):
            raise socket.timeout("timed out with " + req.get_header("Authorization"))

        def junk(req, timeout):
            return Reply(b"not json " + req.get_header("Authorization").encode())

        out, err = io.StringIO(), io.StringIO()
        results = []
        with redirect_stdout(out), redirect_stderr(err):
            for fake in (ok, denied, slow, junk):
                (self.state() / "usage.json").unlink(missing_ok=True)
                with mock.patch.object(usage.urllib.request, "urlopen", fake):
                    results.append(usage.read())
                print(results[-1])
        u = results[0]
        self.assertEqual((u["five_hour"]["used"], u["seven_day"]["used"]), (14.0, 89.0))
        self.assertEqual(u["seven_day"]["resets_at"], at("2026-10-14T22:00:00.819817+00:00"))
        self.assertEqual(results[1:], [(None, "usage service: 401"), (None, "usage service: TimeoutError"),
                                       (None, "usage answer unreadable")])
        url, headers, timeout = seen[0]
        self.assertEqual((url, timeout), (usage.URL, 5))
        self.assertEqual(headers, {"Authorization": f"Bearer {TOKEN}", "Anthropic-beta": "oauth-2025-04-20",
                                   "Anthropic-version": "2023-06-01", "Accept": "application/json",
                                   "User-agent": "claude-code/2.1.296"})
        self.assertNotIn(TOKEN, out.getvalue() + err.getvalue())
        hits = [p for p in self.state().rglob("*") if p.is_file() and TOKEN.encode() in p.read_bytes()]
        self.assertEqual(hits, [])
        self.assertTrue((self.state() / "usage.jsonl").exists())

    # covers: AC-1 (not a subscription login: no token, an API key, a base URL off anthropic.com)
    def test_not_login(self):
        with mock.patch.object(usage.urllib.request, "urlopen", side_effect=AssertionError("no request")):
            self.assertEqual(usage.read(), (None, "not a subscription login"))
            self.creds()
            for k, v in (("ANTHROPIC_API_KEY", "x"), ("ANTHROPIC_BASE_URL", "https://proxy.example.com"),
                         ("ANTHROPIC_BASE_URL", "https://anthropic.com.evil.example")):
                with self.subTest(v), mock.patch.dict(os.environ, {k: v}):
                    self.assertEqual(usage.read(), (None, "not a subscription login"))
        with mock.patch.dict(os.environ, {"ANTHROPIC_BASE_URL": "https://api.anthropic.com"}), \
                mock.patch.object(usage.urllib.request, "urlopen", return_value=Reply(json.dumps(ANSWER).encode())):
            self.assertIsInstance(usage.read(), dict)

    # covers: AC-1 (a null utilization reads 0 with no reset), AC-2 (60 s cache shared, 0600 files, one sample per
    # new read, newest 2000 lines kept)
    def test_cache_and_samples(self):
        self.creds()
        answer = {**ANSWER, "five_hour": {"utilization": None, "resets_at": None}}
        calls = []
        fake = lambda req, timeout: calls.append(1) or Reply(json.dumps(answer).encode())
        with mock.patch.object(usage.urllib.request, "urlopen", fake):
            u = usage.read()
            self.assertEqual(u["five_hour"], {"used": 0.0, "resets_at": None})
            self.assertEqual(usage.read(), u)
            self.assertEqual(len(calls), 1)
            for name in ("usage.json", "usage.jsonl"):
                self.assertEqual((self.state() / name).stat().st_mode & 0o777, 0o600)
            line = json.loads((self.state() / "usage.jsonl").read_text())
            self.assertEqual(sorted(line), ["at", "five_hour", "five_hour_resets_at", "seven_day", "seven_day_resets_at"])
            cache = json.loads((self.state() / "usage.json").read_text())
            cache["at_epoch"] -= 61
            (self.state() / "usage.json").write_text(json.dumps(cache))
            (self.state() / "usage.jsonl").write_text("{}\n" * 2005)
            usage.read()
            self.assertEqual(len(calls), 2)
            self.assertEqual(len((self.state() / "usage.jsonl").read_text().splitlines()), 2000)


def call(command, cost, dur=60, kind="box", started="2026-10-13T10:00:00+00:00", **extra):
    return {"kind": kind, "command": command, "cost_usd": cost, "duration_s": dur, "started": started,
            "tokens": {"input": 1, "output": 2, "cache_read": 3, "cache_write": 4}, "limited": False, "outage": False,
            **extra}


class TestEstimates(StateCase):
    # covers: AC-3 (per kind key medians; limited, outage and null values left out; under 3 samples the all calls
    # median; none at all is None), read from the run folders
    def test_estimates(self):
        calls = [call("/develop a", 1.0), call("/develop b", 3.0), call("/develop c", 2.0),
                 call("/check verify a", 0.5), call("/sync", 0.2, kind="sync"), call("/debug x", 9.0, kind="debug"),
                 call("/develop d", 50.0, limited=True), call("/develop e", 50.0, outage=True), call("/develop f", None)]
        folder = self.state() / "runs" / "r-1"
        folder.mkdir(parents=True)
        (folder / "run.json").write_text(json.dumps({"calls": calls}))
        est = usage.estimates()
        self.assertEqual(sorted(est["keys"]), ["/check verify", "/debug", "/develop", "/sync"])
        self.assertEqual((est["keys"]["/develop"]["cost_usd"], est["keys"]["/develop"]["n"]), (2.0, 4))
        self.assertEqual(est["keys"]["/develop"]["tokens"], 10)
        self.assertEqual(usage.estimate(est, "/develop")["cost_usd"], 2.0)
        self.assertEqual(usage.estimate(est, "/check verify"), est["all"])
        self.assertEqual(usage.estimate(est, "/test"), est["all"])
        self.assertEqual(est["all"]["cost_usd"], 1.5)
        self.assertIsNone(usage.estimates([])["all"])


class TestRatios(unittest.TestCase):
    # covers: AC-4 (the rise between samples with the same reset over the dollars of calls ended between them; pairs
    # with no call skipped; a reset between two samples skipped; under 1 USD unknown; only the last 14 days)
    def test_ratios(self):
        r5, rw = "2026-10-13T15:00:00+00:00", "2026-10-18T00:00:00+00:00"
        line = lambda t, a, b, r=r5: {"at": t, "five_hour": a, "five_hour_resets_at": r, "seven_day": b,
                                      "seven_day_resets_at": rw}
        lines = [line("2026-10-13T10:00:00+00:00", 10, 50), line("2026-10-13T11:00:00+00:00", 20, 52),
                 line("2026-10-13T12:00:00+00:00", 25, 53),
                 line("2026-10-13T13:00:00+00:00", 1, 54, "2026-10-13T20:00:00+00:00"),
                 line("2026-09-01T10:00:00+00:00", 0, 0)]
        calls = [call("/develop", 2.0, 60, started="2026-10-13T10:30:00+00:00"),
                 call("/develop", 5.0, 60, started="2026-10-13T12:30:00+00:00")]
        r = usage.ratios(calls, lines, at("2026-10-14T00:00:00+00:00"))
        self.assertEqual(r, {"five_hour": 10 / 2.0, "seven_day": (2 + 1) / (2.0 + 5.0)})
        self.assertEqual(usage.ratios([call("/develop", 0.5, started="2026-10-13T10:30:00+00:00")], lines,
                                      at("2026-10-14T00:00:00+00:00")), {"five_hour": None, "seven_day": None})


def feature(text):
    return run.Feature(*wf.sections(text)[0])


FEAT = feature("### 1. A · auto\n- [x] (spec)\n- [ ] `/develop a`\n- [ ] `/test a`\n- [ ] Sync: `/sync a`\n")
EST = {"keys": {"/develop": {"cost_usd": 4.0, "duration_s": 600, "tokens": 1, "n": 5},
                "/test": {"cost_usd": 2.0, "duration_s": 300, "tokens": 1, "n": 5},
                "/sync": {"cost_usd": 1.0, "duration_s": 100, "tokens": 1, "n": 5}},
       "all": {"cost_usd": 3.0, "duration_s": 200, "tokens": 1, "n": 15}}


def account(five, week, five_at="2026-10-14T05:00:00+00:00", week_at="2026-10-16T22:00:00+00:00"):
    return {"five_hour": {"used": five, "resets_at": at(five_at)}, "seven_day": {"used": week, "resets_at": at(week_at)}}


class TestPlan(unittest.TestCase):
    # covers: AC-5 (a feature is its open boxes plus one /sync; repos add up, the duration is the largest repo),
    # AC-6 (fits; does not fit the week; 5h nearly used; never refuses), AC-7 (the lines)
    def test_feature_cost(self):
        self.assertEqual(usage.feature_cost(FEAT, EST), (4.0 + 2.0 + 1.0, 1000, 4.0))

    def test_outcomes(self):
        ratio = {"five_hour": 2.0, "seven_day": 1.0}
        picked = [("/r1", FEAT), ("/r2", FEAT)]
        p = usage.plan(picked, account(10, 20), EST, ratio)
        self.assertIsNone(p["start"])
        self.assertEqual(p["week"], [7.0, 7.0])
        self.assertEqual(p["lines"][1:], ["need: ~28% of a 5h window, ~14% of the week, ~0.3h (from 15 past calls)",
                                          "fits, starts now"])
        self.assertTrue(p["lines"][0].startswith("now: 5h 10% (resets "))
        # Week: 100 - 80 - 10 reserve = 10 left, the run needs 14: starts 2 minutes after the weekly reset.
        p = usage.plan(picked, account(10, 80), EST, ratio)
        self.assertEqual(p["start"], at("2026-10-16T22:02:00+00:00"))
        self.assertEqual(p["lines"][-2:], [f"does not fit the week: starts at {usage.at_text(p['start'])}", "fits now: 1-1"])
        self.assertEqual(usage.plan(picked, account(10, 89), EST, ratio)["lines"][-1], "fits now: none")
        # The first call (4 USD, 8% of 5h) does not fit the 5h window: starts after its reset.
        p = usage.plan(picked, account(95, 20), EST, ratio)
        self.assertEqual(p["start"], at("2026-10-14T05:02:00+00:00"))
        self.assertEqual(p["lines"][-1], f"5h window nearly used: starts at {usage.at_text(p['start'])}")

    def test_five_hour_checks_each_repo(self):
        # This used to check only the first picked feature: a second repo's 8% first call ran on 6% left.
        ratio = {"five_hour": 2.0, "seven_day": 1.0}
        small = feature("### 2. B · auto\n- [x] (spec)\n- [ ] `/test b`\n- [ ] Sync: `/sync b`\n")
        p = usage.plan([("/r1", small), ("/r2", FEAT)], account(94, 20), EST, ratio)
        self.assertEqual(p["start"], at("2026-10-14T05:02:00+00:00"))
        self.assertEqual(p["lines"][-1], f"5h window nearly used: starts at {usage.at_text(p['start'])}")
        # A later feature in the same repo is not a first call: it waits for its turn, the run starts now.
        p = usage.plan([("/r1", small), ("/r1", FEAT)], account(94, 20), EST, ratio)
        self.assertIsNone(p["start"])
        self.assertEqual(p["lines"][-1], "fits, starts now")

    def test_unknown(self):
        ratio = {"five_hour": 2.0, "seven_day": 1.0}
        for u, est, r, why in (((None, "usage service: 503"), EST, ratio, "usage service: 503"),
                               (account(1, 1), {"keys": {}, "all": None}, ratio, "no past calls"),
                               (account(1, 1), EST, {"five_hour": None, "seven_day": 1.0}, "no usage samples yet")):
            with self.subTest(why):
                p = usage.plan([("/r", FEAT)], u, est, r)
                self.assertIsNone(p["start"])
                self.assertEqual(p["lines"][-1], f"unknown ({why}), starts now")


class ScreenCase(BareCase):
    """Bare `wf` with a seeded usage cache, past run records and samples, so the fit is known without a request."""

    def seed(self, week_used, five_used=10.0, week_in=3.0, five_in=3.0):
        now = time.time()
        reset = lambda s: datetime.datetime.fromtimestamp(now + s - 120, datetime.timezone.utc).isoformat()
        s = self.state / "wf"
        (s / "runs" / "old-1").mkdir(parents=True, exist_ok=True)
        today = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        calls = [call("/develop a", 4.0, 60, started=(today - datetime.timedelta(minutes=50)).isoformat())]
        (s / "runs" / "old-1" / "run.json").write_text(json.dumps({"calls": [*(call(c, 4.0, 600, kind=k) for c, k in
                                                                                (("/develop a", "box"),) * 3 + (("/sync", "sync"),) * 3), *calls]}))
        line = lambda m, a, b: {"at": (today - datetime.timedelta(minutes=m)).isoformat(), "five_hour": a,
                                "five_hour_resets_at": "x", "seven_day": b, "seven_day_resets_at": "y"}
        (s / "usage.jsonl").write_text(json.dumps(line(60, 10, 10)) + "\n" + json.dumps(line(40, 14, 14)) + "\n")
        (s / "usage.json").write_text(json.dumps({"at_epoch": now, "five_hour": {"used": five_used, "resets_at": reset(five_in)},
                                                  "seven_day": {"used": week_used, "resets_at": reset(week_in)}}))
        (s / "usage.json").chmod(0o600)

    def repos(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(a, b)
        self.steps({"ra": [TICK_A, DONE_A], "rb": [TICK_A, DONE_A]})
        return a, b


class TestScreen(ScreenCase):
    # covers: AC-7 (the usage section after build, a week percent on each numbered line), AC-8 (-y keeps the start
    # time), AC-9 (only the builds wait, the wait line, then the builds; exit code as spec 0020 gives)
    def test_waits_with_yes(self):
        self.repos()
        (self.state / "wf").mkdir(parents=True)
        # Each feature: 4 + 4 USD at 1 point per USD = 8% of the week; 2 repos need 16, 100 - 75 - 10 = 15 left.
        self.seed(75.0)
        t = time.time()
        r = self.bare("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = r.stdout
        self.assertIn("  1. ra: 1. A ~8% week\n  2. rb: 1. A ~8% week\nusage:\n  now: 5h 10% (resets ", out)
        self.assertIn("  need: ~16% of a 5h window, ~16% of the week, ~0.3h (from 7 past calls)\n", out)
        self.assertRegex(out, r"  does not fit the week: starts at \w{3} \d\d:\d\d\n  fits now: 1-1\n")
        self.assertRegex(out, r"\nwaiting for the usage reset: builds start at \w{3} \d\d:\d\d, Ctrl C cancels\n")
        self.assertGreaterEqual(min(at(rec["started"]).timestamp() for rec in self.run_records().values() if "started" in rec), t + 2)
        self.assertLess(out.index("waiting for the usage reset"), out.index("[ra] "))

    # covers: AC-7, AC-8 (unknown starts now, never refuses)
    def test_unknown_starts_now(self):
        self.repos()
        r = self.bare("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("usage:\n  unknown (not a subscription login), starts now\n", r.stdout)
        self.assertNotIn("waiting for the usage reset", r.stdout)

    # covers: AC-8 (at the prompt: now starts at once; numbers pick, the usage lines print again, the pick fits and
    # starts now with no second prompt)
    def test_prompt(self):
        self.repos()
        (self.state / "wf").mkdir(parents=True)
        self.seed(75.0, week_in=600)
        r = self.bare(stdin="now\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(r.stdout, r"Enter waits and starts at \w{3} \d\d:\d\d, numbers to pick \(1 2 4 or 1-3,5\), now "
                                   r"starts at once, anything else cancels: ")
        self.assertNotIn("waiting for the usage reset", r.stdout)
        self.assertEqual(sorted(self.run_records()), ["old", "ra", "rb"])
        import shutil as sh
        sh.rmtree(self.state / "wf" / "runs")
        for repo in ("ra", "rb"):
            (self.tmp / "root" / repo / "docs/scope/scope.md").write_text(ONE)
            (self.fakes / f"{repo}-count").unlink(missing_ok=True)
        self.seed(75.0, week_in=600)
        r = self.bare(stdin="1\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.count("usage:\n"), 2)
        self.assertIn("  fits, starts now\n", r.stdout)
        self.assertNotIn("waiting for the usage reset", r.stdout)
        self.assertEqual(sorted(self.run_records()), ["old", "ra"])

    # covers: AC-9 (Ctrl C during the wait starts no child: every repo not started, exit 130)
    def test_ctrl_c_during_wait(self):
        self.repos()
        (self.state / "wf").mkdir(parents=True)
        self.seed(75.0, week_in=600)
        p = subprocess_start(self, "-y")
        out = ""
        while "waiting for the usage reset" not in out:
            line = p.stdout.readline()
            self.assertNotEqual(line, "", out)
            out += line
        p.send_signal(signal.SIGINT)
        rest, err = p.communicate(timeout=30)
        self.assertEqual(p.returncode, 130, out + rest + err)
        self.assertIn("summary:\n  ra: not started\n  rb: not started\n", rest)
        self.assertFalse((self.fakes / "ra-argv-1.json").exists())


class TestScreenMore(ScreenCase):
    # covers: AC-6, AC-7, AC-9 (5h window nearly used through the real screen: the now line, the start line, the
    # wait, then both repos build)
    def test_five_hour_nearly_used(self):
        self.repos()
        (self.state / "wf").mkdir(parents=True)
        self.seed(20.0, five_used=99.0, five_in=3.0, week_in=600)
        r = self.bare("-y")
        out = r.stdout
        self.assertEqual(r.returncode, 0, out + r.stderr)
        self.assertRegex(out, r"  now: 5h 99% \(resets \w{3} \d\d:\d\d\), week 20% \(resets \w{3} \d\d:\d\d\)\n")
        self.assertRegex(out, r"  5h window nearly used: starts at \w{3} \d\d:\d\d\n")
        self.assertIn("waiting for the usage reset", out)
        self.assertEqual(sorted(self.run_records()), ["old", "ra", "rb"])

    # covers: AC-8 (a pick that still does not fit prints the lines again, keeps its start time, one prompt only)
    def test_pick_still_does_not_fit(self):
        self.repos()
        (self.state / "wf").mkdir(parents=True)
        self.seed(85.0, week_in=4)
        r = self.bare(stdin="1\n")
        out = r.stdout
        self.assertEqual(r.returncode, 0, out + r.stderr)
        self.assertEqual(out.count("usage:\n"), 2)
        self.assertEqual(out.count("Enter waits"), 1)
        self.assertEqual(out.count("does not fit the week"), 2)
        self.assertIn("waiting for the usage reset", out)
        self.assertEqual(sorted(self.run_records()), ["old", "ra"])

    # covers: AC-8 (anything else at the prompt cancels: exit 130, no build)
    def test_cancel(self):
        self.repos()
        (self.state / "wf").mkdir(parents=True)
        self.seed(85.0, week_in=600)
        r = self.bare(stdin="x\n")
        self.assertEqual(r.returncode, 130, r.stdout + r.stderr)
        self.assertEqual(sorted(self.run_records()), ["old"])

    # covers: AC-9 (the report is marked seen before the builds wait, not after)
    def test_report_seen_before_wait(self):
        self.repos()
        (self.state / "wf").mkdir(parents=True)
        (self.state / "wf" / "report.txt").write_text("wf report: last night\n")
        self.seed(85.0, week_in=600)
        p = subprocess_start(self, "-y")
        out = ""
        while "waiting for the usage reset" not in out:
            line = p.stdout.readline()
            self.assertNotEqual(line, "", out)
            out += line
        seen = (self.state / "wf" / "report.seen").exists()
        p.send_signal(signal.SIGINT)
        p.communicate(timeout=30)
        self.assertTrue(seen)
        self.assertEqual(p.returncode, 130)


# A real wf run child cannot take a mock: this sitecustomize sends the usage URL to a local fake server.
SITE = '''import os, urllib.request
_orig = urllib.request.urlopen
def urlopen(req, *a, **kw):
    if getattr(req, "full_url", None) == "https://api.anthropic.com/api/oauth/usage" and os.environ.get("V_URL"):
        req.full_url = os.environ["V_URL"]
    return _orig(req, *a, **kw)
urllib.request.urlopen = urlopen
'''


class TestChildSampling(test_run.RunCase):
    # covers: AC-2 (a wf run child reads usage at its start and after each call; a failed read warns once; a good
    # read is cached, so one request and one sample)
    def usage_server(self, code):
        hits = []

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(1)
                self.send_response(code)
                self.end_headers()
                self.wfile.write(json.dumps(ANSWER).encode())

            def log_message(self, *a):
                pass

        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        site = self.tmp / "site"
        site.mkdir()
        (site / "sitecustomize.py").write_text(SITE)
        (self.tmp / ".claude").mkdir(exist_ok=True)
        (self.tmp / ".claude" / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {"accessToken": TOKEN}}))
        self.env.update(PYTHONPATH=str(site), V_URL=f"http://127.0.0.1:{srv.server_address[1]}/api/oauth/usage")
        return hits

    def test_failed_read(self):
        hits = self.usage_server(503)
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        _, rec = self.run_record()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(hits), 1 + len(rec["calls"]))
        self.assertEqual(r.stdout.count("warning: usage not read: usage service: 503"), 1)

    def test_cached_read(self):
        hits = self.usage_server(200)
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(hits), 1)
        self.assertEqual(len((self.state / "wf" / "usage.jsonl").read_text().splitlines()), 1)
        self.assertNotIn("warning: usage", r.stdout)


def subprocess_start(case, *args):
    import subprocess
    from test_run import WF
    p = subprocess.Popen([sys.executable, str(WF), *args], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, env=case.env)
    case.addCleanup(lambda: p.poll() is None and p.kill())
    return p


class TestLimitAccount(test_park.TestLimit):
    # covers: AC-10 (no reset in the text, or an earlier one, sleeps to the reset of a full window from your account;
    # a window not full keeps the text's reset; a failed read keeps the 30 minutes)
    def account(self, week_used, week_reset):
        s = self.state / "wf"
        s.mkdir(parents=True, exist_ok=True)
        (s / "usage.json").write_text(json.dumps({"at_epoch": time.time(), "five_hour": {"used": 5, "resets_at": None},
                                                  "seven_day": {"used": week_used, "resets_at": week_reset}}))

    def test_account_reset(self):
        at_ = self.mode("2026-10-12T06:00:00-05:00")
        for name, step, used, slept in (("weekly text", limited("You've hit your weekly limit"), 100, "259320"),
                                        ("earlier text", limited(), 99.5, "259320"),
                                        ("not full", limited(), 60, "1320")):
            with self.subTest(name):
                self.fresh()
                self.account(used, "2026-10-15T06:00:00-05:00")
                self.steps([step, {}, {}, {"tick": False}])
                r = self.wf("demo", "-y", mode=at_)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertEqual(self.slept(), [slept])
        self.fresh()
        self.steps([limited("usage limit reached"), {}, {}, {"tick": False}])
        r = self.wf("demo", "-y", mode=at_)
        self.assertEqual(self.slept(), ["1920"])

    # covers: AC-10 (a full 5h window, both full takes the latest reset, a full window earlier than the text and a
    # window at 98 keep the text's reset)
    def test_which_window(self):
        at_ = self.mode("2026-10-12T06:00:00-05:00")
        for name, acct, slept in (("5h full later", (100, "2026-10-12T09:00:00-05:00", 50, None), "10920"),
                                  ("both full", (99, "2026-10-12T09:00:00-05:00", 100, "2026-10-15T06:00:00-05:00"), "259320"),
                                  ("full earlier than text", (100, "2026-10-12T06:10:00-05:00", 10, None), "1320"),
                                  ("98 not full", (98, "2026-10-12T09:00:00-05:00", 10, None), "1320")):
            with self.subTest(name):
                self.fresh()
                five, five_at, week, week_at = acct
                s = self.state / "wf"
                s.mkdir(parents=True, exist_ok=True)
                (s / "usage.json").write_text(json.dumps({"at_epoch": time.time(),
                                                          "five_hour": {"used": five, "resets_at": five_at},
                                                          "seven_day": {"used": week, "resets_at": week_at}}))
                self.steps([limited(), {}, {}, {"tick": False}])
                r = self.wf("demo", "-y", mode=at_)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertEqual(self.slept(), [slept])

    # only the AC-10 test of this class runs here
    test_wait_and_rerun = test_detection = test_stops = None
    test_autopilot_off_during_sleep = test_sigint_during_sleep = test_max_hours = None


if __name__ == "__main__":
    unittest.main()
