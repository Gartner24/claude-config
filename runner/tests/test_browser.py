"""Spec 0009: headless verify and test for `wf run`."""
import json
import os
import re
import shlex
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
TEST_FIRST = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n- [ ] `/test a`\n- [ ] `/develop a`\n"


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
            " For /test, the feature's changes are the files in git diff --relative --name-only --diff-filter=ACMR abc123 plus "
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

    # covers: AC-9 (neither main nor master: the /test prompt adds nothing), AC-10 (test_base null)
    def test_run_no_base(self):
        branch_repo(self.repo, "trunk")
        (self.repo / "docs/scope/scope.md").write_text(TEST_FIRST)
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = json.loads(next((self.state / "wf" / "runs").iterdir()).joinpath("run.json").read_text())
        self.assertEqual([(c["command"], c["test_base"]) for c in rec["calls"]][0], ("/test a", None))
        argv = self.argv(1)["argv"]
        self.assertEqual(argv[argv.index("--append-system-prompt") + 1], run.UNATTENDED_PROMPT)


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
json.dump({{"argv": sys.argv[1:], "env": dict(os.environ)}},
          open(os.path.join(d, "bwrap-%d.json" % (len(glob.glob(os.path.join(d, "bwrap-*.json"))) + 1)), "w"))
i = sys.argv.index("--chdir")
os.chdir(sys.argv[i + 1])
os.execv(sys.argv[i + 2], sys.argv[i + 2:])
"""
FAKE_NPX = f"""#!{sys.executable}
import json, os, sys
d = os.environ["FAKE_DIR"]
json.dump({{"argv": sys.argv[1:], "env": dict(os.environ), "cwd": os.getcwd()}}, open(os.path.join(d, "npx.json"), "w"))
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
VERIFY_FIRST = "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n- [ ] `/check verify a`\n"


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
        (self.bin / "env").symlink_to(shutil.which("env"))
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
        # Spec 0021: a park is a phone question; no test waits the 12 hour default for its reply.
        if "--max-wait" not in args:
            args = (*args, "--max-wait", "0.0001")
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
        # P10: npx starts in the state dir, never the repo or wf's own cwd.
        self.assertEqual(npx["cwd"], str(self.state / "wf"))
        self.assertTrue(cache.is_dir())
        self.assertEqual(run.mcp_cache(), os.path.join(run.state_dir(), "npm"))
        # Spec 0011 AC-6 dropped the answers from the plan; run.json keeps them.
        self.assertEqual(json.loads(next((self.state / "wf" / "runs").iterdir()).joinpath("run.json").read_text())
                         ["repos"][0]["answers"]["app url"], self.url)

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
    # covers: AC-3 step 3 (order, tmpfs for dirs, /dev/null for files, read only binds from the frozen
    # denyWrite list as listed, wf's folders hidden, missing paths skipped)
    def test_argv(self):
        with tempfile.TemporaryDirectory() as d:
            home, repo, state = Path(d, "home"), Path(d, "repo"), Path(d, "state", "wf")
            for p in (home / ".ssh", home / ".gnupg", home / ".npm", repo / ".claude", repo / ".git" / "hooks", state):
                p.mkdir(parents=True)
            (home / ".netrc").write_text("x")
            (repo / ".git" / "config").write_text("")
            (repo / "hooks").mkdir()
            r, h = str(repo), str(home)
            # Unsorted on purpose: the jail keeps the list's order. A missing path is skipped.
            deny = [f"{r}/.git/hooks", f"{r}/.claude", f"{r}/missing", f"{r}/hooks", f"{r}/.git/config"]
            ns = SimpleNamespace(c=SimpleNamespace(path=r), bwrap="/bin/bwrap",
                                 guard_settings={"sandbox": {"filesystem": {"denyWrite": deny}}},
                                 browser={"start": "npm run dev", "wf_dirs": [f"{d}/config/wf", str(state)]})
            with mock.patch.dict(os.environ, {"HOME": h}):
                argv = run.Run.jail_argv(ns)
            self.assertEqual(argv, [
                "/bin/bwrap", "--die-with-parent", "--unshare-pid", "--ro-bind", "/", "/", "--dev", "/dev",
                "--proc", "/proc", "--tmpfs", "/tmp", "--tmpfs", "/run",
                "--bind", r, r, "--bind", f"{h}/.npm", f"{h}/.npm",
                "--ro-bind", f"{r}/.git/hooks", f"{r}/.git/hooks", "--ro-bind", f"{r}/.claude", f"{r}/.claude",
                "--ro-bind", f"{r}/hooks", f"{r}/hooks", "--ro-bind", f"{r}/.git/config", f"{r}/.git/config",
                "--tmpfs", f"{h}/.ssh", "--ro-bind", "/dev/null", f"{h}/.netrc", "--tmpfs", f"{h}/.gnupg",
                "--tmpfs", str(state),
                "--chdir", r, "/bin/sh", "-c", "npm run dev"])


class TestRealPathBinds(unittest.TestCase):
    # covers: AC-3 step 3 (findings 8: binds at the real path, each once; the symlink inside a write bind
    # rule), AC-3 step 5 (file_hash on a directory)
    def test_argv(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            home, repo, dots, cache = Path(d, "home"), Path(d, "repo"), Path(d, "dots"), Path(d, "cache")
            for p in (home, repo / ".claude", dots, cache):
                p.mkdir(parents=True)
            (dots / "gitconfig").write_text("")
            (home / ".gitconfig").symlink_to(dots / "gitconfig")
            (home / ".cache").symlink_to(cache)
            r, h = str(repo), str(home)
            deny = [f"{h}/.gitconfig", f"{r}/.claude", f"{r}/./.claude", f"{h}/missing"]
            ns = SimpleNamespace(c=SimpleNamespace(path=r), bwrap="/bin/bwrap",
                                 guard_settings={"sandbox": {"filesystem": {"denyWrite": deny}}},
                                 browser={"start": "x", "wf_dirs": []})
            with mock.patch.dict(os.environ, {"HOME": h}):
                argv = run.Run.jail_argv(ns)
            self.assertEqual(argv[14:-5], ["--bind", r, r, "--bind", str(cache), str(cache),
                                           "--ro-bind", f"{dots}/gitconfig", f"{dots}/gitconfig",
                                           "--ro-bind", f"{r}/.claude", f"{r}/.claude"])

    def test_symlink_in_bind(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            real, other = Path(d, "real", "repo"), Path(d, "other")
            for p in (real / "x", other / "tools"):
                p.mkdir(parents=True)
            Path(d, "projects").symlink_to(Path(d, "real"))
            (real / ".claude").symlink_to(other)
            (real / "lib").symlink_to(other)
            linked = f"{d}/projects/repo"
            for name, entry, binds, want in (
                ("entry is a link", f"{real}/.claude", [str(real)], f"{real}/.claude"),
                ("link above the entry", f"{real}/lib/tools", [str(real)], f"{real}/lib"),
                ("bind as written", f"{linked}/lib/tools", [linked], f"{linked}/lib"),
                ("bind at its real path", f"{real}/lib/tools", [linked], f"{real}/lib"),
                ("link above the bind", f"{linked}/x", [linked], None),
                ("outside every bind", f"{other}/tools", [str(real)], None),
                ("the bind itself", linked, [linked], None),
            ):
                with self.subTest(name):
                    self.assertEqual(run.symlink_in_bind(entry, binds), want)

    def test_file_hash_directory(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run.file_hash(d), "directory")
            Path(d, "loop").symlink_to(Path(d, "loop"))
            self.assertEqual(run.file_hash(str(Path(d, "loop"))), "unreadable")

    # covers: AC-3 step 5, findings 10 and 13 (a tree of folders passes, any file or symlink in it trips;
    # an absent guarded file that is now a symlink trips, dangling or not)
    def test_findings_10_13(self):
        def changed(build, guarded=False):
            with tempfile.TemporaryDirectory() as d:
                p = Path(d, "x")
                build(Path(d), p)
                g = {"guarded_files": {str(p): "absent"}, "absent_denied": []} if guarded else \
                    {"guarded_files": {}, "absent_denied": [str(p)]}
                return next(run.moved(g), (None, None))[1]

        def tree(extra=None):
            def build(d, p):
                (p / ".cc-writes" / "a").mkdir(parents=True)
                (d / "out").mkdir()
                (d / "out" / "f").write_text("")
                if extra:
                    extra(d, p / ".cc-writes" / "a")
            return build

        self.assertIsNone(changed(tree()))
        self.assertIsNone(changed(lambda d, p: p.write_text("")))
        self.assertIsNone(changed(lambda d, p: p.write_text(""), guarded=True))
        for name, extra in (("file top", lambda d, a: (a.parent.parent / "f").write_text("")),
                            ("file deep", lambda d, a: (a / "post-commit").write_text("")),
                            ("file deeper", lambda d, a: (a / "b" / "c").mkdir(parents=True) or (a / "b" / "c" / "f").write_text("")),
                            ("link to file", lambda d, a: (a / "l").symlink_to(d / "out" / "f")),
                            ("link to folder", lambda d, a: (a / "l").symlink_to(d / "out"))):
            with self.subTest(name):
                self.assertIn("appeared during the run", changed(tree(extra)))
        with self.subTest("unreadable folder"):
            self.assertIn("appeared during the run", changed(tree(lambda d, a: a.chmod(0))))
        with self.subTest("link to empty folder"):
            self.assertIn("appeared during the run", changed(lambda d, p: (d / "e").mkdir() or p.symlink_to(d / "e")))
        with self.subTest("non empty file"):
            self.assertIn("appeared during the run", changed(lambda d, p: p.write_text("x")))
        for name, build in (("dangling", lambda d, p: p.symlink_to(d / "nowhere")),
                            ("loop", lambda d, p: p.symlink_to(p)),
                            ("link to empty file", lambda d, p: (d / "e").write_text("") or p.symlink_to(d / "e"))):
            with self.subTest(name):
                self.assertIn("changed during the run", changed(build, guarded=True))


# The fake PATH holds only the fakes.
MKDIR = shutil.which("mkdir")


class TestFindings89(AppCase):
    # covers: AC-3 step 3 (the symlink park on start, no bwrap run), AC-3 step 5 (absent_denied recorded and
    # checked right after the app stops; empty placeholders pass; a guarded file turned folder stops)
    def test_park(self):
        (self.tmp / "other" / "tools").mkdir(parents=True)
        (self.tmp / "other" / "tools" / "h.sh").write_text("#!/bin/sh\n")
        cases = (("link", ".claude", f"{self.repo}/.claude"), ("under a link", "lib", f"{self.repo}/lib"))
        for name, link, detail in cases:
            with self.subTest(name):
                shutil.rmtree(self.state, ignore_errors=True)
                if name == "under a link":
                    (self.repo / ".claude").unlink()
                    (self.repo / ".claude").mkdir()
                    (self.repo / ".claude" / "settings.json").write_text(json.dumps({"hooks": {"Stop": [
                        {"hooks": [{"type": "command", "command": "./lib/tools/h.sh"}]}]}}))
                (self.repo / link).symlink_to(self.tmp / "other")
                rec = self.assert_stopped(self.wf("demo", "-y"), "app_failed", calls=0)
                self.assertEqual(rec["detail"], f"{detail} is a symlink inside a writable folder")
                self.assertEqual(list(self.fakes.glob("bwrap-*.json")), [])

    def test_linked_parent_starts(self):
        Path(self.tmp, "projects").symlink_to(self.tmp / "root")
        linked = self.tmp / "projects" / "demo"
        self.allow(linked)
        self.steps([{}, {"tick": False}])
        r = self.wf(str(linked), "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.fakes / "bwrap-1.json").exists())

    def test_hook_appears(self):
        self.app(None, f"{MKDIR} -p .git/hooks; echo 'curl evil' > .git/hooks/post-commit; exit 1")
        rec = self.assert_stopped(self.wf("demo", "-y"), "guard_changed", calls=0, repo=True)
        self.assertEqual(rec["detail"], f"{self.repo}/.git/hooks appeared during the run; "
                                        "inspect or delete it before opening a session in this repo")

    def test_placeholders_pass(self):
        self.app(None, f"{MKDIR} .git/hooks; : > .git/config.worktree; : > .claude; exec python3 {self.app_py} {self.port} ok")
        self.steps([{}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.repo / ".git" / "hooks").is_dir())
        self.assertEqual(self.run_record()[1]["repos"][0]["guard"]["absent_denied"], [f"{self.repo}/.claude", f"{self.repo}/.git/hooks",
                                                                                      f"{self.repo}/.git/info"])

    def test_dangling_target_recorded(self):
        (self.tmp / ".gitconfig").symlink_to(self.repo / "planted")
        self.steps([{}, {"tick": False}])
        self.wf("demo", "-y")
        self.assertIn(f"{self.repo}/planted", self.run_record()[1]["repos"][0]["guard"]["absent_denied"])

    def test_file_becomes_folder(self):
        (self.repo / ".git" / "hooks").mkdir()
        (self.repo / ".git" / "hooks" / "pre-push").write_text("#!/bin/sh\n")
        self.app(None, f"{shutil.which('rm')} .git/hooks/pre-push; {MKDIR} .git/hooks/pre-push; exit 1")
        rec = self.assert_stopped(self.wf("demo", "-y"), "guard_changed", calls=0, repo=True)
        self.assertIn(".git/hooks/pre-push changed during the run", rec["detail"])


class TestJailRun(AppCase):
    # covers: AC-3 step 3 through wf run (a linked worktree's pointer and a hook token script folder are read
    # only for the app, wf's folders hidden, no Claude login in the app's env)
    def test_worktree(self):
        demo = self.repo
        (demo / "scripts").mkdir()
        (demo / "scripts" / "h.sh").write_text("#!/bin/sh\n")
        (demo / ".claude").mkdir()
        (demo / ".claude" / "settings.json").write_text(json.dumps({"hooks": {"Stop": [
            {"hooks": [{"type": "command", "command": "./scripts/h.sh"}]}]}}))
        git(demo, "add", "-A")
        git(demo, "commit", "-qm", "base")
        wt = self.tmp / "root" / "wt"
        git(demo, "worktree", "add", "-q", "-b", "wt2", str(wt))
        self.allow(wt)
        self.env["CLAUDE_CODE_OAUTH_TOKEN"] = "secret-login"
        self.steps([{}, {"tick": False}])
        r = self.wf("wt", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        jail = json.loads((self.fakes / "bwrap-1.json").read_text())
        argv = jail["argv"]
        ro = [argv[i + 1] for i, a in enumerate(argv) if a == "--ro-bind" and argv[i + 1] not in ("/", "/dev/null")]
        for p in (wt / ".git", Path(os.path.realpath(wt / ".git")), wt / "scripts", wt / ".claude",
                  demo / ".git" / "config"):
            self.assertIn(str(p), ro)
        self.assertTrue(all(os.path.exists(p) for p in ro), ro)
        tmpfs = [argv[i + 1] for i, a in enumerate(argv) if a == "--tmpfs"]
        self.assertIn(str(self.tmp / "config" / "wf"), tmpfs)
        self.assertIn(str(self.state / "wf"), tmpfs)
        self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", jail["env"])
        self.assertEqual(jail["env"]["WF_RUN"], self.run_record()[0].name)
        self.assertEqual(self.argv(1)["env"]["CLAUDE_CODE_OAUTH_TOKEN"], "secret-login")


class TestGuardAfterApp(AppCase):
    # covers: AC-3 step 5 (the guarded file check right after each app stop wins over app_failed, a pending
    # decision and Ctrl C)
    def edit(self, then, first=""):
        self.app(None, f"{first}echo '# moved' >> {self.repo}/.git/config; {then}")

    def test_over_app_failed(self):
        self.edit("exit 1")
        rec = self.assert_stopped(self.wf("demo", "-y"), "guard_changed", calls=0, repo=True)
        self.assertIn(".git/config changed during the run", rec["detail"])

    def test_over_decision(self):
        fake = FakeNtfy()
        self.addCleanup(fake.close)
        write_config(self.tmp / "config", fake.url, codes=[f"code{i:04d}" for i in range(5)])
        self.edit(f"exec python3 {self.app_py} {self.port} ok")
        self.steps([ask()])
        self.assert_stopped(self.wf("demo", "-y", mode="fast"), "guard_changed", calls=1, repo=True)
        # The call's question is never pinged; only the repo stop's own (spec 0021 U5) is.
        self.assertEqual([p["message"].split("\n")[0][6:38] for p in fake.pings()], ["the setup changed during the build"[:32]])

    def test_over_ctrl_c(self):
        # Ctrl C while the app boots and ignores SIGTERM: only cleanup() stops it. An app that exits on the
        # SIGTERM is stopped by start_app, a stop during a call by the loop.
        # The trap comes before the edit the test waits on: a SIGTERM between the two used to end the shell.
        self.edit(f"exec {shutil.which('sleep')} 600", first="trap '' TERM; ")
        p = self.start("demo", "-y", grace=2)
        end = time.monotonic() + 30
        while "# moved" not in (self.repo / ".git" / "config").read_text():
            self.assertLess(time.monotonic(), end)
            time.sleep(0.05)
        p.send_signal(signal.SIGINT)
        out, err = p.communicate(timeout=30)
        self.assertIn("stopped: guard_changed", out, out + err)


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

    # covers: AC-3 step 5 (a question stops the app; spec 0011 AC-13: the resume starts a new one with its own log)
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
        self.assertEqual([c["app"] and c["app"]["logs"] for c in rec["calls"]], [["app-01.log"], ["app-02.log"], None])
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
                # Spec 0021 F12: the park asks retry or skip.
                q = json.loads((self.state / "wf" / "queue.json").read_text())
                self.assertEqual([(d["case"], d["options"]) for d in q["decisions"]], [("app_failed", ["retry", "skip"])])

    # covers: spec 0021 U7 (a busy port stops only the repo, with its question)
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
        q = json.loads((self.state / "wf" / "queue.json").read_text())
        self.assertEqual([(d["reason"], d["options"]) for d in q["decisions"] if d.get("level") == "repo"],
                         [("app_port_busy", ["retry", "stop this repo"])])


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


ATTACH = ("--browserUrl", "--browser-url", "-u", "--wsEndpoint", "--ws-endpoint", "-w", "--autoConnect",
          "--auto-connect", "--userDataDir", "--user-data-dir", "--channel")
CHROME_ARGS = ["--chromeArg=--webrtc-ip-handling-policy=disable_non_proxied_udp", "--chromeArg=--disable-quic"]


def check_mcp(text, cache, env, state, npx):
    """AC-5 on an MCP config as a call receives it; raises AssertionError on any way it could attach or leak."""
    server = json.loads(text)["mcpServers"]["chrome-devtools"]
    args = server["args"]
    # P10: npx in the repo ran a planted node_modules copy; env -C moves it to the state dir first.
    assert server["command"] == env and args[:3] == ["-C", state, npx], (server["command"], args[:3])
    assert all(a in args for a in ("--isolated", "--headless", "--proxyServer")), args
    assert len([a for a in args if re.fullmatch(r"chrome-devtools-mcp@\d+\.\d+\.\d+", a)]) == 1, args
    assert all(a in CHROME_ARGS for a in args if a.startswith("--chromeArg")), args
    assert server["env"] == {"npm_config_cache": cache}, server["env"]
    assert not any(a.split("=")[0] in ATTACH or "@latest" in a for a in args), args


class TestBrowserArgv(AppCase):
    # covers: AC-4, AC-5, AC-6, AC-7 (which calls get the browser and exactly what they get), AC-8 (prompt)
    def test_argv(self):
        (self.repo / "docs/scope/scope.md").write_text(
            "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n- [ ] `/develop a`\n- [ ] `/check verify a`\n"
            "- [ ] `/test a`\n")
        self.steps([{}, {"tick": False, "json": {"result": "VERIFY FAIL: debug"}}, {"tick": False}, {}, {},
                    {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        folder, rec = self.run_record()
        self.assertEqual([c["kind"] for c in rec["calls"]], ["box", "box", "debug", "box", "box", "sync"])
        shots = folder / "shots"
        self.assertTrue(shots.is_dir())
        npx, brave = os.path.realpath(self.bin / "npx"), os.path.realpath(self.bin / "brave")
        env, state = os.path.realpath(self.bin / "env"), str(self.state / "wf")
        cache = str(self.state / "wf" / "npm")
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.state)}):
            mcp = run.mcp_browser(env, npx, brave, cache)
        self.assertEqual(json.loads(mcp), {"mcpServers": {"chrome-devtools": {
            "type": "stdio", "command": env,
            "args": ["-C", state, npx, "-y", "chrome-devtools-mcp@1.10.1", "--isolated", "--headless", "--executablePath", brave,
                     "--proxyServer", "127.0.0.1:9", *CHROME_ARGS, "--no-usage-statistics", "--no-performance-crux"],
            "env": {"npm_config_cache": cache}}}})
        plain = self.argv(1)["argv"]
        for n in (1, 2, 3, 4, 5, 6):
            argv = self.argv(n)["argv"]
            opt = lambda k: argv[argv.index(k) + 1]
            browser = n in (2, 3, 4)
            with self.subTest(n=n):
                self.assertEqual(opt("--mcp-config"), mcp if browser else run.MCP_ALLOW)
                denied = opt("--disallowedTools").split(",")
                hooks = json.loads(opt("--settings"))["hooks"]["PreToolUse"]
                prompt = opt("--append-system-prompt")
                if not browser:
                    self.assertNotIn("--allowedTools", argv)
                    self.assertEqual((opt("--settings"), opt("--disallowedTools")),
                                     (plain[plain.index("--settings") + 1], plain[plain.index("--disallowedTools") + 1]))
                    self.assertNotIn("chrome-devtools", prompt)
                    continue
                check_mcp(opt("--mcp-config"), cache, env, state, npx)
                self.assertEqual(opt("--allowedTools").split(","), ["mcp__chrome-devtools__" + t for t in run.BROWSER_TOOLS])
                self.assertEqual(denied[-6:], ["mcp__chrome-devtools__" + t for t in (
                    "upload_file", "take_heapsnapshot", "performance_start_trace", "performance_stop_trace",
                    "performance_analyze_insight", "lighthouse_audit")])
                self.assertEqual(",".join(denied[:-6]), plain[plain.index("--disallowedTools") + 1])
                self.assertEqual(hooks[0], json.loads(plain[plain.index("--settings") + 1])["hooks"]["PreToolUse"][0])
                self.assertEqual(hooks[1], {"matcher": "mcp__chrome-devtools__.*", "hooks": [{
                    "type": "command", "timeout": 10,
                    "command": f"{shlex.quote(os.path.realpath(sys.executable))} -c {shlex.quote(run.BROWSER_GUARD)} "
                               f"{shlex.quote(self.url)} {shlex.quote(str(shots))} || exit 2"}]})
                self.assertTrue(prompt.endswith(
                    f" wf started the app at {self.url} and stops it after this step; do not start, stop or restart it. "
                    "Drive it with the chrome-devtools tools and open only that address; outside sites do not load. "
                    f"Save any file a browser tool writes under {shots}, or leave its path out. Anything you start from Bash runs in a "
                    "separate sandbox the browser cannot reach. If no chrome-devtools tool is available, end with "
                    "BLOCKED: browser tools unavailable. Otherwise end with BLOCKED only for a login, captcha, 2FA or "
                    "hardware."), prompt)

    # covers: AC-7, AC-8 (a state dir behind a symlink: hook and prompt both name the real shots path)
    def test_symlinked_state(self):
        self.state.mkdir()
        link = self.tmp / "statelink"
        link.symlink_to(self.state)
        self.env["XDG_STATE_HOME"] = str(link)
        self.steps([{}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        shots = str(self.run_record()[0] / "shots")
        argv = self.argv(1)["argv"]
        hook = json.loads(argv[argv.index("--settings") + 1])["hooks"]["PreToolUse"][1]["hooks"][0]["command"]
        self.assertEqual(shlex.split(hook)[-4], shots)
        self.assertIn(f"under {shots}, or leave", argv[argv.index("--append-system-prompt") + 1])

    def test_no_keys(self):
        (self.repo / "AGENTS.md").unlink()
        self.steps([{}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        argv = self.argv(1)["argv"]
        self.assertEqual(argv[argv.index("--mcp-config") + 1], run.MCP_ALLOW)
        self.assertEqual(argv[argv.index("--append-system-prompt") + 1], run.UNATTENDED_PROMPT)
        self.assertNotIn("--allowedTools", argv)

    # covers: AC-5 (the check rejects every way to attach, persist or leak)
    def test_check_rejects(self):
        cache = "/s/wf/npm"
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": "/s"}):
            good = json.loads(run.mcp_browser("/bin/env", "/bin/npx", "/bin/brave", cache))
        check = lambda text: check_mcp(text, cache, "/bin/env", "/s/wf", "/bin/npx")
        check(json.dumps(good))
        args = good["mcpServers"]["chrome-devtools"]["args"]
        bad = {
            "npx in the repo": {"command": "/bin/npx", "args": args[3:]},
            "no -C": {"args": args[2:]},
            "other dir": {"args": ["-C", "/repo", *args[2:]]},
            "browserUrl": {"args": [*args, "--browserUrl", "http://127.0.0.1:9222"]},
            "user data dir": {"args": [*args, "--user-data-dir=/home/x/.config/BraveSoftware"]},
            "third chromeArg": {"args": [*args, "--chromeArg=--no-sandbox"]},
            "latest": {"args": [a.replace("@1.10.1", "@latest") for a in args]},
            "old spelling": {"args": [a.replace("--webrtc", "--force-webrtc") for a in args]},
            "extra env": {"env": {"npm_config_cache": cache, "NODE_OPTIONS": "--require x"}},
            "home npm": {"env": {"npm_config_cache": os.path.expanduser("~/.npm")}},
            "no proxy": {"args": [a for a in args if a not in ("--proxyServer", "127.0.0.1:9")]},
        }
        for name, change in bad.items():
            with self.subTest(name):
                copy = json.loads(json.dumps(good))
                copy["mcpServers"]["chrome-devtools"].update(change)
                with self.assertRaises(AssertionError):
                    check(json.dumps(copy))


class TestBrowserGuard(unittest.TestCase):
    # covers: AC-7 (BROWSER_GUARD run directly, fails closed)
    def test_guard(self):
        with tempfile.TemporaryDirectory() as d:
            # Real paths: an allowed path must equal its own realpath.
            d = os.path.realpath(d)
            shots = Path(d, "shots")
            shots.mkdir()
            (shots / "esc").symlink_to(d)
            (shots / "sub").mkdir()
            Path(d, "into").symlink_to(shots)
            app = "http://localhost:3000"
            nav = lambda **i: json.dumps({"tool_name": "mcp__chrome-devtools__navigate_page", "tool_input": i})
            shot = lambda p: json.dumps({"tool_name": "mcp__chrome-devtools__take_screenshot", "tool_input": {"filePath": p}})
            cases = [
                ("app origin", nav(url="http://localhost:3000/x"), 0),
                ("upper case host", nav(url="HTTP://LOCALHOST:3000/"), 0),
                ("new_page", json.dumps({"tool_name": "mcp__chrome-devtools__new_page",
                                         "tool_input": {"url": "http://localhost:3000"}}), 0),
                ("evil suffix", nav(url="http://localhost:3000.evil.example/"), 2),
                ("backslash", nav(url="http://localhost:22\\@localhost:3000/"), 2),
                ("userinfo", nav(url="http://x@localhost:3000/"), 2),
                ("tab", nav(url="http://localhost:3000/\ta"), 2),
                ("space", nav(url="http://localhost:3000/ a"), 2),
                ("control", nav(url="http://localhost:3000/\x01"), 2),
                ("del", nav(url="http://localhost:3000/\x7f"), 2),
                ("other port", nav(url="http://localhost:3001/"), 2),
                ("file", nav(url="file:///etc/passwd"), 2),
                ("chrome", nav(url="chrome://settings"), 2),
                ("reload", nav(type="reload"), 0),
                ("back", nav(type="back"), 2),
                ("forward", nav(type="forward"), 2),
                ("url type no url", nav(type="url"), 2),
                ("path inside", shot(str(shots / "a.png")), 0),
                ("path outside", shot(os.path.join(d, "a.png")), 2),
                ("dot dot", shot(str(shots / ".." / "a.png")), 2),
                ("dot dot inside", shot(f"{shots}/sub/../a.png"), 2),
                ("dot dot ending inside", shot(f"{d}/x/../shots/a.png"), 2),
                ("relative", shot("shots/a.png"), 2),
                ("the shots dir", shot(str(shots)), 2),
                ("trailing slash", shot(f"{shots}/sub/"), 2),
                ("symlink", shot(str(shots / "esc" / "a.png")), 2),
                ("symlink into shots", shot(f"{d}/into/a.png"), 2),
                ("path not a string", json.dumps({"tool_name": "mcp__chrome-devtools__take_snapshot",
                                                  "tool_input": {"filePath": 1}}), 2),
                ("other tool", json.dumps({"tool_name": "Bash", "tool_input": {}}), 2),
                ("malformed", "{nope", 2),
                ("empty", "", 2),
            ]
            for name, stdin, code in cases:
                with self.subTest(name):
                    r = subprocess.run([sys.executable, "-c", run.BROWSER_GUARD, app, str(shots)], input=stdin,
                                       capture_output=True, text=True)
                    self.assertEqual(r.returncode, code, r.stderr)
                    if code:
                        self.assertIn("wf run: browser tool call refused", r.stderr)
            # The default port form matches an app url that names it.
            r = subprocess.run([sys.executable, "-c", run.BROWSER_GUARD, "http://localhost:80", str(shots)],
                               input=nav(url="http://localhost/"), capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
