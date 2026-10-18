"""Spec 0058: our own status bar, ported from jjstack's statusline.sh."""
import http.server
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import statusbar  # noqa: E402

# The real refresh(), since every test patches the module's own.
REFRESH = statusbar.refresh
ANSI = re.compile(r"\033\[[0-9;]*m")
G, Y, R = "\033[42m\033[30m", "\033[43m\033[30m", "\033[41m\033[97m"


def plain(s):
    return ANSI.sub("", s)


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(subprocess.run, ["rm", "-rf", str(self.tmp)])
        env = mock.patch.dict(os.environ, {"HOME": str(self.tmp), "ANTHROPIC_BASE_URL": "",
                                           "CLAUDE_CODE_EFFORT_LEVEL": "", "CLAUDE_PROVIDER_LABEL": ""})
        env.start()
        self.addCleanup(env.stop)
        self.cache = self.tmp / "usage.json"
        for name, value in (("CACHE", str(self.cache)), ("USAGE_URL", "http://127.0.0.1:9/none")):
            p = mock.patch.object(statusbar, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.refreshed = []
        p = mock.patch.object(statusbar, "refresh", self.refreshed.append)
        p.start()
        self.addCleanup(p.stop)

    def login(self):
        p = self.tmp / ".claude" / ".credentials.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"claudeAiOauth": {"accessToken": "tok"}}))
        return p

    def settings(self, name, level):
        p = self.tmp / ".claude" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"effortLevel": level}))

    def repo(self):
        d = self.tmp / "proj"
        subprocess.run(["git", "init", "-q", "-b", "main", str(d)], check=True)
        return d


class TestProgress(Case):
    # covers: AC-1 (create_progress_bar: green under 70, yellow 70 to 89, red 90 and up; filled share rounds; the
    # label centred to the width; the percent truncated)
    def test_colors_and_fill(self):
        self.assertEqual(statusbar.progress(69.9, "5h", 5), "".join(
            f"{G if i < 5 else statusbar.DIM}{c}\033[0m" for i, c in enumerate("  5h   ")) + " 69%")
        self.assertTrue(statusbar.progress(70, "x").startswith(Y))
        self.assertTrue(statusbar.progress(89, "x").startswith(Y))
        self.assertTrue(statusbar.progress(90, "x").startswith(R))
        self.assertEqual(statusbar.progress(0, "context").count(G), 0)
        self.assertEqual(statusbar.progress(100, "context").count(R), 9)
        self.assertEqual(statusbar.progress(50, "context").count(G), 5)
        self.assertEqual(plain(statusbar.progress(3, "week", 5)), " week   3%")


class TestSegments(Case):
    # covers: AC-1 (model, effort and folder lead; context bar from used_percentage; no context, no bar)
    def test_head(self):
        out = statusbar.render({"model": {"display_name": "Opus"}, "cwd": "/a/b/proj",
                                "context_window": {"used_percentage": 42}})
        self.assertTrue(out.startswith("\033[36mOpus\033[0m \033[2m·\033[0m\033[2mauto\033[0m\033[2m | \033[0mproj"))
        self.assertEqual(plain(out), "Opus ·auto | proj |  context  42% | $?")
        self.assertEqual(plain(statusbar.render({"workspace": {"current_dir": "/x/y"}})), "unknown ·auto | y | $?")
        self.assertEqual(statusbar.render({"cwd": "/x/y"}, short=True), "y")

    # covers: AC-1 (effort: stdin, then the env, then settings.local.json, then settings.json, then auto; a color each)
    def test_effort_chain(self):
        self.settings("settings.json", "low")
        self.assertIn("\033[92mlow", statusbar.render({}))
        self.settings("settings.local.json", "medium")
        self.assertIn("\033[93mmedium", statusbar.render({}))
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_EFFORT_LEVEL": "xhigh"}):
            self.assertIn("\033[96mxhigh", statusbar.render({}))
            self.assertIn("\033[95mhigh", statusbar.render({"effort": {"level": "high"}}))
        self.assertIn("\033[2mmax", statusbar.render({"effort": {"level": "max"}}))
        (self.tmp / ".claude" / "settings.local.json").unlink()
        (self.tmp / ".claude" / "settings.json").write_text("{bad")
        self.assertIn("\033[2mauto", statusbar.render({}))

    # covers: AC-1 (render never raises into bar())
    def test_never_raises(self):
        self.assertEqual(statusbar.render({"model": "Opus"}), "")


class TestGit(Case):
    # covers: AC-1, AC-5 (branch and the staged, modified and untracked counts from one git status; clean)
    def test_clean_and_dirty(self):
        d = self.repo()
        self.assertEqual(statusbar.git(str(d)), "main clean")
        for n in ("a", "b", "c"):
            (d / n).write_text("1")
        subprocess.run(["git", "-C", str(d), "add", "a", "b"], check=True)
        subprocess.run(["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
                       check=True)
        (d / "a").write_text("2")
        (d / "b").write_text("2")
        subprocess.run(["git", "-C", str(d), "add", "b"], check=True)
        (d / "b").write_text("3")
        (d / "d").write_text("1")
        self.assertEqual(statusbar.git(str(d)), "main +1 ~2 ?2")
        self.assertIn("main +1 ~2 ?2", plain(statusbar.render({"cwd": str(d)})))
        # the script counts every untracked file (ls-files --others), not one line per new folder
        (d / "new").mkdir()
        for n in ("x", "y", "z"):
            (d / "new" / n).write_text("1")
        self.assertEqual(statusbar.git(str(d)), "main +1 ~2 ?5")
        # the script prints the short commit id on a detached HEAD, as `rev-parse --short` does
        subprocess.run(["git", "-C", str(d), "checkout", "-q", "--detach"], check=True)
        sha = subprocess.run(["git", "-C", str(d), "rev-parse", "--short", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
        self.assertEqual(statusbar.git(str(d)), f"{sha} +1 ~2 ?5")

    # covers: AC-1 (from a subfolder the script counted only untracked files below it; staged and modified stay
    # repo wide)
    def test_subfolder(self):
        d = self.repo()
        (d / "s" / "t").mkdir(parents=True)
        for p in ("out", "s/in", "s/t/deep"):
            (d / p).write_text("1")
        self.assertEqual(statusbar.git(str(d)), "main ?3")
        self.assertEqual(statusbar.git(str(d / "s")), "main ?2")
        self.assertEqual(statusbar.git(str(d / "s" / "t")), "main ?1")

    # covers: AC-1 (git quotes accented or quoted names without -z, so these folders once showed "clean")
    def test_quoted_names(self):
        d = self.repo()
        for f in ("\u00e9d", 'q"d'):
            (d / f).mkdir()
            for n in ("a", "b"):
                (d / f / n).write_text("1")
            self.assertEqual(statusbar.git(str(d / f)), "main ?2")
        # a rename's old path comes as its own -z field and must not count as a row
        g = ["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(g + ["add", "-A"], check=True)
        subprocess.run(g + ["commit", "-qm", "a"], check=True)
        subprocess.run(g + ["mv", "q\"d/a", "q\"d/c"], check=True)
        self.assertEqual(statusbar.git(str(d)), "main +1")
        # a working tree only rename (git add -N) is " R": its old path once counted as +1 ~1 of its own
        subprocess.run(g + ["commit", "-qm", "b"], check=True)
        os.rename(d / "q\"d" / "b", d / "q\"d" / "e")
        subprocess.run(g + ["add", "-N", "q\"d/e"], check=True)
        self.assertEqual(statusbar.git(str(d)), "main ~1")

    # covers: AC-1 (a both modified conflict counts once staged and twice modified, as the script's two diffs do)
    def test_conflict(self):
        d = self.repo()
        g = ["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@t"]
        (d / "f").write_text("a")
        subprocess.run(g + ["add", "f"], check=True)
        subprocess.run(g + ["commit", "-qm", "a"], check=True)
        subprocess.run(g + ["checkout", "-qb", "o"], check=True)
        (d / "f").write_text("b")
        subprocess.run(g + ["commit", "-qam", "b"], check=True)
        subprocess.run(g + ["checkout", "-q", "main"], check=True)
        (d / "f").write_text("c")
        subprocess.run(g + ["commit", "-qam", "c"], check=True)
        subprocess.run(g + ["merge", "-q", "o"], capture_output=True)
        self.assertEqual(statusbar.git(str(d)), "main +1 ~2")

    # covers: AC-3 (not a repo, or a failed git call: no git segment, never "clean")
    def test_failed_git(self):
        (self.tmp / "plain").mkdir()
        self.assertEqual(statusbar.git(str(self.tmp / "plain")), "")
        self.assertEqual(plain(statusbar.render({"cwd": str(self.tmp / "plain")})), "unknown ·auto | plain | $?")

    # covers: AC-5 (git runs once, with porcelain v1 and -b; a timeout drops the segment inside the budget)
    def test_one_call_and_timeout(self):
        bin_ = self.tmp / "bin"
        bin_.mkdir()
        log = self.tmp / "git.log"
        (bin_ / "git").write_text(f"#!/bin/sh\necho \"$@\" >> {log}\nsleep \"${{FAKE_SLEEP:-0}}\"\n"
                                  "printf '## dev...origin/dev [ahead 1]\\0 M x\\0'\n")
        (bin_ / "git").chmod(0o755)
        with mock.patch.dict(os.environ, {"PATH": f"{bin_}:{os.environ['PATH']}"}):
            self.assertEqual(statusbar.git("/w"), "dev ~1")
            self.assertEqual(log.read_text(), "-C /w status --porcelain=v1 -b -z --untracked-files=all\n")
            with mock.patch.dict(os.environ, {"FAKE_SLEEP": "3"}):
                t0 = time.monotonic()
                self.assertEqual(statusbar.git("/w"), "")
                self.assertLess(time.monotonic() - t0, 2)


class TestUsage(Case):
    # covers: AC-1, AC-3 (through a provider: via <host> or its label, no usage)
    def test_provider(self):
        self.login()
        with mock.patch.dict(os.environ, {"ANTHROPIC_BASE_URL": "http://u:p@fb.local:4000/v1"}):
            self.assertEqual(statusbar.usage({}), ["\033[95mvia fb.local\033[0m"])
            with mock.patch.dict(os.environ, {"CLAUDE_PROVIDER_LABEL": "claude-fb"}):
                self.assertEqual(statusbar.usage({}), ["\033[95mvia claude-fb\033[0m"])
        with mock.patch.dict(os.environ, {"ANTHROPIC_BASE_URL": "https://api.anthropic.com"}):
            self.assertEqual(len(statusbar.usage({})), 2)
        self.assertEqual(self.refreshed, [str(self.tmp / ".claude" / ".credentials.json")])

    # covers: AC-1 (a fresh cache: the 5 hour and weekly bars, no refresh)
    def test_fresh_cache(self):
        self.login()
        self.cache.write_text(json.dumps({"five_hour": {"utilization": 75.6}, "seven_day": {"utilization": 91}}))
        five, week = statusbar.usage({})
        self.assertEqual((five, week), (statusbar.progress(75, "5h", 5), statusbar.progress(91, "week", 5)))
        self.assertEqual(self.refreshed, [])

    # covers: AC-1 (a cache older than 300 s: refresh started, old value shown)
    def test_stale_cache(self):
        self.login()
        self.cache.write_text(json.dumps({"five_hour": {"utilization": 10}, "seven_day": {"utilization": 20}}))
        old = time.time() - 301
        os.utime(self.cache, (old, old))
        self.assertEqual([plain(s) for s in statusbar.usage({})], ["  5h    10%", " week   20%"])
        self.assertEqual(len(self.refreshed), 1)
        os.utime(self.cache, (old + 2, old + 2))
        statusbar.usage({})
        self.assertEqual(len(self.refreshed), 1)

    # covers: AC-3 (an unreadable cache or figure shows 5h ? and wk ?, never 0%)
    def test_unknown(self):
        self.login()
        unknown = ["\033[2m5h ?\033[0m", "\033[2mwk ?\033[0m"]
        self.assertEqual(statusbar.usage({}), unknown)
        self.cache.write_text("{bad")
        self.assertEqual(statusbar.usage({}), unknown)
        self.cache.write_text(json.dumps({"five_hour": {"utilization": None}, "seven_day": 3}))
        self.assertEqual(statusbar.usage({}), unknown)
        self.cache.write_text(json.dumps({"five_hour": {"utilization": 0}}))
        self.assertEqual([plain(s) for s in statusbar.usage({})], ["  5h    0%", "wk ?"])

    # covers: AC-1 (no login: the session cost, green under 1, yellow from 1, magenta from 5; no cost read, $?)
    def test_cost(self):
        self.assertEqual(statusbar.usage({"cost": {"total_cost_usd": 0.5}}), ["\033[92m$0.50\033[0m"])
        self.assertEqual(statusbar.usage({"cost": {"total_cost_usd": 1}}), ["\033[93m$1.00\033[0m"])
        self.assertEqual(statusbar.usage({"cost": {"total_cost_usd": 5.004}}), ["\033[95m$5.00\033[0m"])
        self.assertEqual(statusbar.usage({}), ["\033[2m$?\033[0m"])
        self.assertEqual(self.refreshed, [])


class Usage(http.server.BaseHTTPRequestHandler):
    seen = []

    def do_GET(self):
        Usage.seen.append(self.headers["Authorization"])
        body = json.dumps({"five_hour": {"utilization": 33}}).encode()
        self.send_response(200 if self.path == "/ok" else 500)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class TestRefresh(Case):
    # covers: AC-1 (the detached refresh sends the login token and writes the cache whole; a failed call keeps the
    # old cache)
    def test_refresh(self):
        server = http.server.HTTPServer(("127.0.0.1", 0), Usage)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        creds = str(self.login())
        url = f"http://127.0.0.1:{server.server_port}"
        self.cache.write_text("old")
        p = subprocess.run([sys.executable, "-c", statusbar.REFRESH, creds, str(self.cache), url + "/fail"],
                           capture_output=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(self.cache.read_text(), "old")
        subprocess.run([sys.executable, "-c", statusbar.REFRESH, creds, str(self.cache), url + "/ok"], check=True)
        self.assertEqual(json.loads(self.cache.read_text()), {"five_hour": {"utilization": 33}})
        self.assertEqual(Usage.seen, ["Bearer tok", "Bearer tok"])
        self.assertFalse(Path(str(self.cache) + ".tmp").exists())

    # covers: AC-1 (refresh() starts the detached call and never waits for it)
    def test_detached(self):
        with mock.patch("subprocess.Popen") as popen:
            REFRESH("c")
        argv = popen.call_args.args[0]
        self.assertEqual(argv[1:], ["-c", statusbar.REFRESH, "c", str(self.cache), statusbar.USAGE_URL])
        self.assertTrue(popen.call_args.kwargs["start_new_session"])


if __name__ == "__main__":
    unittest.main()
