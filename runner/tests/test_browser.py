"""Spec 0009: headless verify and test for `wf run`."""
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402
from test_run import RUNNER, WRAPPER, FakeNtfy, RunCase, alive, ask, write_config  # noqa: E402

GIT_ID = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]
TEST_FIRST = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress\n- [ ] `/test a`\n- [ ] `/develop a`\n"


def git(repo, *args):
    return subprocess.run(["git", *GIT_ID, "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def branch_repo(repo, base="main"):
    """base with one commit, then work with two more and an uncommitted file; returns the base sha."""
    git(repo, "checkout", "-q", "-b", base)
    (repo / "a.txt").write_text("a")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    sha = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "-b", "work")
    for n in ("b", "c"):
        (repo / f"{n}.txt").write_text(n)
        git(repo, "add", f"{n}.txt")
        git(repo, "commit", "-qm", n)
    (repo / "d.txt").write_text("d")
    return sha


class TestBaseUnit(unittest.TestCase):
    # covers: AC-9 (main, master, neither)
    def test_base(self):
        for base in ("main", "master"):
            with tempfile.TemporaryDirectory() as d:
                repo = Path(d)
                git(repo, "init", "-q")
                sha = branch_repo(repo, base)
                self.assertEqual(run.test_base(str(repo)), sha)
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            git(repo, "init", "-q")
            branch_repo(repo, "trunk")
            self.assertIsNone(run.test_base(str(repo)))

    def test_prompt(self):
        self.assertEqual(run.unattended_prompt({}, False, None), run.UNATTENDED_PROMPT)
        self.assertEqual(run.unattended_prompt({}, False, "abc123"), run.UNATTENDED_PROMPT + (
            " For /test, the feature's changes are the files in git diff --name-only --diff-filter=ACMR abc123 plus "
            "the untracked files from git ls-files --others --exclude-standard; use that list as the changed files "
            "instead of uncommitted files only."))


class TestBaseRun(RunCase):
    # covers: AC-9 (only /test box calls, a retry reuses it), AC-10 (test_base in run.json)
    def test_run(self):
        sha = branch_repo(self.repo)
        (self.repo / "docs/scope/scope.md").write_text(TEST_FIRST)
        self.steps([{"tick": False, "rc": 1}, {}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = json.loads(next((self.state / "wf" / "runs").iterdir()).joinpath("run.json").read_text())
        self.assertEqual([(c["command"], c["test_base"], c["retry_of"]) for c in rec["calls"]],
                         [("/test a", sha, None), ("/test a", sha, 1), ("/develop a", None, None), ("/sync", None, None)])
        prompts = [self.argv(n)["argv"][self.argv(n)["argv"].index("--append-system-prompt") + 1] for n in (1, 2, 3, 4)]
        self.assertEqual(prompts[0], run.unattended_prompt({}, False, sha))
        self.assertEqual(prompts[1], prompts[0])
        self.assertEqual(prompts[2:], [run.UNATTENDED_PROMPT] * 2)


class TestAppKeys(unittest.TestCase):
    # covers: AC-1 (both keys, case and spaces kept, every refusal, the other keys unchanged)
    def answers(self, text):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "AGENTS.md").write_text("## Standing answers\n" + text)
            return run.read_answers(SimpleNamespace(path=d, scope_dir="docs/scope"))

    def test_keys(self):
        self.assertEqual(self.answers("- App Start: NODE_ENV=dev npm  run Dev\n- app url: http://localhost:3000/Home\n"
                                      "- Run Suite: YES\n- done: Ask\n"),
                         ({"run suite": "yes", "done": "ask", "app start": "NODE_ENV=dev npm  run Dev",
                           "app url": "http://localhost:3000/Home"}, None))
        for url in ("https://127.0.0.1:1", "http://[::1]:65535", "http://localhost:8080/a/b?c=d"):
            self.assertEqual(self.answers(f"- app start: x\n- app url: {url}\n")[0]["app url"], url)
        self.assertEqual(self.answers("- done: yes\n"), ({"done": "yes"}, None))

    def test_refusals(self):
        bad_url = "AGENTS.md:3: app url must be http(s)://localhost|127.0.0.1|[::1]:<port 1-65535>"
        cases = [
            ("start alone", "- app start: npm run dev\n", "AGENTS.md: app start and app url go together"),
            ("url alone", "- app url: http://localhost:3000\n", "AGENTS.md: app start and app url go together"),
            ("remote host", "- app start: x\n- app url: http://example.com:3000\n", bad_url),
            ("no port", "- app start: x\n- app url: http://localhost\n", bad_url),
            ("port 0", "- app start: x\n- app url: http://localhost:0\n", bad_url),
            ("port 70000", "- app start: x\n- app url: http://localhost:70000\n", bad_url),
            ("ftp", "- app start: x\n- app url: ftp://localhost:21\n", bad_url),
            ("space", "- app start: x\n- app url: http://localhost:3000 /x\n", bad_url),
            ("repeat", "- app start: x\n- app url: http://localhost:3000\n- App URL: http://localhost:3001\n",
             "AGENTS.md:4: app url set twice"),
        ]
        for name, text, detail in cases:
            with self.subTest(name):
                self.assertEqual(self.answers(text), (None, detail))


# Exec what follows --chdir, so the app really runs; the argv is kept for the tests.
FAKE_BWRAP = f"""#!{sys.executable}
import glob, json, os, sys
d = os.environ["FAKE_DIR"]
json.dump(sys.argv[1:], open(os.path.join(d, "bwrap-%d.json" % (len(glob.glob(os.path.join(d, "bwrap-*.json"))) + 1)), "w"))
i = sys.argv.index("--chdir")
os.chdir(sys.argv[i + 1])
os.execv(sys.argv[i + 2], sys.argv[i + 2:])
"""
FAKE_NPX = f"""#!{sys.executable}
import json, os, sys
d = os.environ["FAKE_DIR"]
json.dump({{"argv": sys.argv[1:], "env": dict(os.environ)}}, open(os.path.join(d, "npx.json"), "w"))
rc = int(open(os.path.join(d, "npx-rc")).read()) if os.path.exists(os.path.join(d, "npx-rc")) else 0
sys.stderr.write("npm ERR! boom\\nmore\\n" if rc else "")
sys.exit(rc)
"""
# argv: port, mode. ok serves 200; 500 serves 500; silent never listens; stubborn ignores SIGTERM;
# gen writes tests/generated_x.py while it runs and removes it on SIGTERM.
FIXTURE_APP = """import http.server, os, signal, sys, time
port, mode = int(sys.argv[1]), sys.argv[2]
print("booting", mode, flush=True)
if mode == "silent":
    time.sleep(600)
if mode == "stubborn":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
if mode == "gen":
    os.makedirs("tests", exist_ok=True)
    open("tests/generated_x.py", "w").write("x = 1\\n")
    def bye(s, f):
        os.remove("tests/generated_x.py")
        sys.exit(0)
    signal.signal(signal.SIGTERM, bye)
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(500 if mode == "500" else 200)
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", port), H).serve_forever()
"""
# WRAPPER plus a patchable APP_READY, so a never ready app parks in seconds.
BROWSER_WRAPPER = WRAPPER.replace("import ntfy, run, wf\n", "import ntfy, run, wf, os\n"
                                  "run.APP_READY = float(os.environ.get('WF_TEST_APP_READY', run.APP_READY))\n")
VERIFY_FIRST = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress\n- [ ] `/check verify a`\n"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class AppCase(RunCase):
    def setUp(self):
        super().setUp()
        self.fake("bwrap", FAKE_BWRAP)
        self.fake("npx", FAKE_NPX)
        self.fake("brave", "#!/bin/sh\n")
        self.app_py = self.tmp / "app.py"
        self.app_py.write_text(FIXTURE_APP)
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        (self.repo / "docs/scope/scope.md").write_text(VERIFY_FIRST)
        self.app("ok")

    def app(self, mode, start=None):
        self.start_cmd = start or f"python3 {self.app_py} {self.port} {mode}"
        (self.repo / "AGENTS.md").write_text(f"## Standing answers\n- app start: {self.start_cmd}\n- app url: {self.url}\n")

    def cmd(self, *args, grace=30, mode="-"):
        return [sys.executable, "-c", BROWSER_WRAPPER, str(RUNNER), str(grace), mode, "run", *args]

    def probe(self):
        """A fake claude step that fails unless the app answers during the call."""
        return [sys.executable, "-c", f"import urllib.request; urllib.request.urlopen({self.url!r}, timeout=2)"]

    def down(self):
        """A fake claude step that fails when the app still answers: the call before stopped it."""
        return [sys.executable, "-c", f"import urllib.request\ntry:\n urllib.request.urlopen({self.url!r}, timeout=2)\n"
                                      "except OSError: pass\nelse: raise SystemExit(1)"]

    def refused(self, r, detail):
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn(f"refused: no_browser: {detail}\n", r.stdout)
        self.assertEqual(list(self.fakes.glob("argv-*.json")), [])


class TestStart(AppCase):
    # covers: AC-2, AC-4 (MCP_CACHE place check, creation and npm_config_cache on the --version run)
    def test_ok(self):
        self.steps([{}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        npx = json.loads((self.fakes / "npx.json").read_text())
        cache = self.state / "wf" / "npm"
        self.assertEqual(npx["argv"], ["-y", "chrome-devtools-mcp@1.10.1", "--version"])
        self.assertEqual(npx["env"]["npm_config_cache"], str(cache))
        self.assertTrue(cache.is_dir())
        self.assertEqual(run.mcp_cache(), os.path.join(run.state_dir(), "npm"))
        self.assertIn(f"answers: app start {self.start_cmd}, app url {self.url}", r.stdout.splitlines()[0])

    def test_refusals(self):
        with self.subTest("no brave"):
            (self.bin / "brave").unlink()
            self.refused(self.wf("demo", "-y"), "brave")
            self.fake("brave", "#!/bin/sh\n")
        with self.subTest("mcp fails"):
            (self.fakes / "npx-rc").write_text("1")
            self.refused(self.wf("demo", "-y"), "mcp: npm ERR! boom")
            (self.fakes / "npx-rc").unlink()
        for name, state in (("state in repo", self.repo / "state"), ("state in cache", self.tmp / ".cache" / "s")):
            with self.subTest(name):
                env = self.env
                self.env = {**env, "XDG_STATE_HOME": str(state)}
                self.refused(self.wf("demo", "-y"), "state dir is writable by calls")
                self.assertFalse((state / "wf").exists())
                self.env = env
        self.assertFalse((self.state / "wf" / "locks").exists())

    def test_no_keys(self):
        (self.repo / "AGENTS.md").unlink()
        (self.bin / "brave").unlink()
        self.steps([{}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.fakes / "npx.json").exists())
        self.assertEqual(list(self.fakes.glob("bwrap-*.json")), [])
        _, rec = self.run_record()
        self.assertEqual([c["app"] for c in rec["calls"]], [None, None])


class TestJailArgv(unittest.TestCase):
    # covers: AC-3 step 3 (order, tmpfs for dirs, /dev/null for files, read only binds, missing paths skipped)
    def test_argv(self):
        with tempfile.TemporaryDirectory() as d:
            home, repo = Path(d, "home"), Path(d, "repo")
            for p in (home / ".ssh", home / ".gnupg", home / ".npm", repo / ".claude", repo / ".git" / "hooks"):
                p.mkdir(parents=True)
            (home / ".netrc").write_text("x")
            (repo / ".git" / "config").write_text("")
            ns = SimpleNamespace(c=SimpleNamespace(path=str(repo)), bwrap="/bin/bwrap", common=str(repo / ".git"),
                                 browser={"start": "npm run dev"})
            with mock.patch.dict(os.environ, {"HOME": str(home)}):
                argv = run.Run.jail_argv(ns)
            r, h = str(repo), str(home)
            self.assertEqual(argv, [
                "/bin/bwrap", "--die-with-parent", "--unshare-pid", "--ro-bind", "/", "/", "--dev", "/dev",
                "--proc", "/proc", "--tmpfs", "/tmp", "--tmpfs", "/run",
                "--bind", r, r, "--bind", f"{h}/.npm", f"{h}/.npm",
                "--ro-bind", f"{r}/.claude", f"{r}/.claude", "--ro-bind", f"{r}/.git/config", f"{r}/.git/config",
                "--ro-bind", f"{r}/.git/hooks", f"{r}/.git/hooks",
                "--tmpfs", f"{h}/.ssh", "--ro-bind", "/dev/null", f"{h}/.netrc", "--tmpfs", f"{h}/.gnupg",
                "--chdir", r, "/bin/sh", "-c", "npm run dev"])


class TestLifecycle(AppCase):
    # covers: AC-3 (ready before the call, stopped after, a retry keeps it), AC-10 (app in run.json)
    def test_retry_keeps_app(self):
        self.steps([{"tick": False, "rc": 1, "run": [self.probe()]}, {"run": [self.probe()]},
                    {"tick": False, "run": [self.down()]}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        folder, rec = self.run_record()
        a, b, s = rec["calls"]
        self.assertEqual(a["app"], b["app"])
        self.assertEqual((b["retry_of"], a["app"]["url"], a["app"]["logs"], s["app"]), (1, self.url, ["app-01.log"], None))
        self.assertIsNotNone(a["app"]["exit"])
        self.assertEqual(a["app"]["ready_s"], round(a["app"]["ready_s"], 1))
        self.assertEqual(len(list(self.fakes.glob("bwrap-*.json"))), 1)
        self.assertIn("booting ok", (folder / "app-01.log").read_text())
        self.assertIsNone(run.http_status(self.url))
        # Every call and the app carry WF_RUN; the run id is the run folder's name.
        self.assertEqual(self.argv(1)["env"]["WF_RUN"], folder.name)

    # covers: AC-3 (each verify or debug call starts a new app with a new log)
    def test_new_app_per_call(self):
        self.steps([{"tick": False, "json": {"result": "VERIFY FAIL: debug"}, "run": [self.probe()]},
                    {"tick": False, "run": [self.probe()]}, {"run": [self.probe()]}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual([(c["kind"], c["app"] and c["app"]["logs"]) for c in rec["calls"]],
                         [("box", ["app-01.log"]), ("debug", ["app-02.log"]), ("box", ["app-03.log"]), ("sync", None)])

    # covers: AC-3 step 5 (a decision wait stops the app, the resume restarts it with an -r1 log)
    def test_decision_restarts(self):
        fake = FakeNtfy()
        self.addCleanup(fake.close)
        write_config(self.tmp / "config", fake.url, codes=[f"code{i:04d}" for i in range(5)])
        fake.replies = ["{id} 2"]
        # The resume finds the app up again; the /sync call after it finds it down.
        self.steps([ask(run=[self.probe()]), {"run": [self.probe()]}, {"tick": False, "run": [self.down()]}])
        r = self.wf("demo", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual(rec["calls"][0]["app"]["logs"], ["app-01.log", "app-01-r1.log"])
        self.assertEqual(rec["calls"][0]["app"], rec["calls"][1]["app"])
        self.assertEqual(len(list(self.fakes.glob("bwrap-*.json"))), 2)

    # covers: AC-3 step 6 (Ctrl C stops a call and a stubborn app within one shared GRACE)
    def test_ctrl_c(self):
        # exec: the leader itself ignores SIGTERM, so only the shared GRACE ends it.
        self.app("stubborn", f"exec python3 {self.app_py} {self.port} stubborn")
        self.steps([{"sleep": 60, "ignore_int": True}])
        p = self.start("demo", "-y", grace=2)
        self.wait_for(self.fakes / "argv-1.json", timeout=30)
        t0 = time.monotonic()
        p.send_signal(signal.SIGINT)
        out, err = p.communicate(timeout=30)
        self.assertLess(time.monotonic() - t0, 3.5, out + err)
        self.assertIn("stopped: interrupted", out)
        self.assertIsNone(run.http_status(self.url))

    # covers: AC-3 step 6 (a process carrying WF_RUN that left the call's group is killed by the sweep)
    def test_sweep(self):
        leave = [sys.executable, "-c", "import os, subprocess, sys; p = subprocess.Popen([sys.executable, '-c', "
                 "'import time; time.sleep(300)'], start_new_session=True, stdout=subprocess.DEVNULL, "
                 "stderr=subprocess.DEVNULL); open(os.environ['FAKE_DIR'] + '/leftover', 'w').write(str(p.pid))"]
        # The /sync call checks the leftover is already gone: the sweep runs after each browser call, not only at exit.
        gone = [sys.executable, "-c", "import os; os.kill(int(open(os.environ['FAKE_DIR'] + '/leftover').read()), 0)"]
        self.steps([{"run": [leave]}, {"tick": False, "run": [[sys.executable, "-c", "import subprocess, sys; "
                                                               f"sys.exit(subprocess.run({gone!r}).returncode == 0)"]]}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        pid = int((self.fakes / "leftover").read_text())
        self.addCleanup(lambda: alive(pid) and os.kill(pid, signal.SIGKILL))
        self.assertFalse(alive(pid))


class TestAppFailures(AppCase):
    # covers: AC-3 step 4 (app_failed with detail and tail, no claude call), step 2 (app_port_busy)
    def test_failures(self):
        cases = [
            ("exits", "exit 1", None, r"app exited 1: $"),
            ("500 only", None, "500", rf"not ready at {self.url} after 1.5 s \(last status 500\): booting 500$"),
            ("never", None, "silent", rf"not ready at {self.url} after 1.5 s \(last status none\): booting silent$"),
        ]
        for name, start, mode, detail in cases:
            with self.subTest(name):
                shutil.rmtree(self.state, ignore_errors=True)
                self.app(mode, start)
                self.env["WF_TEST_APP_READY"] = "1.5"
                r = self.wf("demo", "-y")
                rec = self.assert_stopped(r, "app_failed", calls=0)
                self.assertRegex(rec["detail"], detail)
                self.assertEqual(list(self.fakes.glob("argv-*.json")), [])
                self.assertIsNone(run.http_status(self.url))

    def test_port_busy(self):
        server = subprocess.Popen([sys.executable, str(self.app_py), str(self.port), "ok"], stdout=subprocess.DEVNULL)
        self.addCleanup(lambda: (server.kill(), server.wait()))
        end = time.monotonic() + 10
        while run.http_status(self.url) is None:
            self.assertLess(time.monotonic(), end)
            time.sleep(0.05)
        rec = self.assert_stopped(self.wf("demo", "-y"), "app_port_busy", calls=0)
        self.assertEqual(rec["detail"], f"something already answers at {self.url}")
        self.assertEqual(list(self.fakes.glob("bwrap-*.json")), [])


class TestDebugOrder(AppCase):
    # covers: AC-3 step 1 (the debug snapshot comes before the app starts, the after one after it stops)
    def test_app_files_are_not_the_call(self):
        self.app("gen")
        self.steps([{"tick": False, "json": {"result": "VERIFY FAIL: debug"}}, {"tick": False}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.repo / "tests" / "generated_x.py").exists())
        _, rec = self.run_record()
        self.assertEqual(rec["calls"][1]["touched"], [])


if __name__ == "__main__":
    unittest.main()
