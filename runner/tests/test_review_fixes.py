"""Review stack fixes of 2026-10-12 (docs/briefs/runner-review-stack-2026-10-12.md): one test per finding."""
import fcntl
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ntfy  # noqa: E402
import run  # noqa: E402
import wf  # noqa: E402
from test_browser import AppCase, VERIFY_FIRST, git  # noqa: E402
from test_park import limited  # noqa: E402
from test_queue import ONE, TICK_B, DONE_B, DecisionCase, QueueCase, decision  # noqa: E402
from test_run import WF, FakeNtfy, RunCase, ask, write_config  # noqa: E402

ARGS = SimpleNamespace(budget=1, call_timeout=60, max_calls=20, max_hours=8, max_wait=12, yes=True)


def quiet_git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=cwd, check=True,
                   capture_output=True)


class TestParkedResume(AppCase):
    # covers: spec 0011 AC-7 (H1: an answered Decision whose resume parks app_failed on the restart is not picked
    # again; it used to loop until --max-hours)
    def test_not_repicked(self):
        fake = FakeNtfy()
        self.addCleanup(fake.close)
        write_config(self.tmp / "config", fake.url, codes=[f"code{i:04d}" for i in range(5)])
        fake.replies = ["{id} 1"]
        broken = self.fakes / "broken"
        self.app("ok", f"[ -e {broken} ] && exit 3; exec python3 {self.app_py} {self.port} ok")
        self.steps([ask(run=[[sys.executable, "-c", f"open({str(broken)!r}, 'w')"]])])
        r = self.wf("demo", "-y", "--max-hours", "0.002", mode="fast")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn("parked: 1. A: app_failed: app exited 3", r.stdout)
        self.assertIn("queue done: ", r.stdout)
        self.assertEqual(len(list(self.fakes.glob("bwrap-*.json"))), 2)
        self.assertEqual(len(list(self.fakes.glob("argv-*.json"))), 1)
        q = json.loads((self.state / "wf" / "queue.json").read_text())
        self.assertEqual([(p["feature"], p["reason"]) for p in q["parks"]], [("1. A", "app_failed")])
        self.assertEqual([d["answer"] for d in q["decisions"]], ["Postgres (recommended)"])


class TestStaleUnqueued(DecisionCase):
    # covers: spec 0011 AC-13 (L9: an answered Decision whose feature lost `· auto` is stale, never resumed)
    def test_untagged(self):
        repo = self.make_repo("unq", ONE)
        self.commit(repo)
        i = self.open_one("unq")["id"]
        self.set_decision(answer="SQLite", source="phone", answered="2026-10-12T10:00:00+02:00")
        (repo / "docs/scope/scope.md").write_text(ONE.replace("### 1. A · auto", "### 1. A") +
                                                  "\n### 2. B · auto\n- [x] (spec)\n- [ ] `/develop b`\n")
        self.commit(repo)
        self.steps([TICK_B, DONE_B])
        r = self.wf("unq", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"  stale: {i} 1. A\n", r.stdout)
        self.assertNotIn("--resume", self.argv(1)["argv"])
        self.assertEqual(self.queue()["decisions"], [])


class TestPaid(unittest.TestCase):
    # covers: spec 0008 AC-7 (L6: _KEY, _PAT endings and the exact names; lookalikes kept)
    def test_names(self):
        for name in ("PGPASSWORD", "DATABASE_URL", "SENTRY_DSN", "STRIPE_KEY", "GITHUB_PAT", "ssh_key", "My_Secret"):
            self.assertTrue(run.paid(name), name)
        for name in ("PATH", "REDIS_URL", "MY_DATABASE_URL_HINT", "PATCH_LEVEL", "CLAUDE_CODE_OAUTH_TOKEN", "KEYTIMEOUT",
                     "LESSKEY"):
            self.assertFalse(run.paid(name), name)
        with mock.patch.dict(os.environ, {"DATABASE_URL": "postgres://x", "GITHUB_PAT": "p", "REDIS_URL": "r"}):
            env = run.call_env()
        self.assertEqual(("DATABASE_URL" in env, "GITHUB_PAT" in env, env.get("REDIS_URL")), (False, False, "r"))


class TestLimitThenRepoStop(QueueCase):
    # covers: spec 0011 AC-9 (M1: a limit rerun ended by a repo stop no longer leaks into the next repo's feature,
    # which used to die on an unset value and end the run internal_error)
    def test_next_repo_runs(self):
        a = self.repo
        b = self.make_repo("beta", ONE)
        self.steps([limited(write_file=[[".claude/settings.json", "{}"]]), {}, {"tick": False}])
        r = self.wf("-y", mode="limit|2026-10-12T06:00:00-05:00|100000")
        # AC-19: a stopped repo is left for you, so not 0.
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual([(e["repo"], e["ended"]) for e in rec["repos"]], [(str(a), "guard_changed"), (str(b), None)])
        self.assertEqual([(e["repo"], e["outcome"]) for e in rec["features"]],
                         [(str(a), "guard_changed"), (str(b), "feature_done")])
        self.assertEqual(rec["stop_reason"], "queue_done")


class TestAppStopRepoStop(AppCase):
    # covers: spec 0011 AC-9 (M2: a guard change found when the feature's app stops ends only that repo; the stop
    # sat outside the try and used to end every repo)
    def test_other_repo_runs(self):
        plant = "import os; os.makedirs('.claude', exist_ok=True); open('.claude/settings.json', 'w').write('{}')"
        self.app("ok", f'python3 -c "{plant}"; exec python3 {self.app_py} {self.port} ok')
        # Only /sync is owed there, so one call is enough under --max-calls 1.
        other = self.make_repo("other", ONE.replace("- [ ] `/develop a`", "- [x] `/develop a`"))
        self.steps([{"tick": False, "rc": 1}, {"tick": False}])
        r = self.wf("-y", "--max-calls", "1")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn("stopped repo demo: guard_changed: ", r.stdout)
        _, rec = self.run_record()
        self.assertEqual([(e["repo"], e["outcome"]) for e in rec["features"]],
                         [(str(self.repo), "guard_changed"), (str(other), "feature_done")])
        self.assertEqual(rec["repos"][0]["ended"], "guard_changed")
        self.assertEqual(rec["stop_reason"], "queue_done")


class TestGitPaths(unittest.TestCase):
    def repo(self, d):
        root = Path(d)
        root.mkdir(exist_ok=True)
        quiet_git("init", "-q", "-b", "main", cwd=root)
        (root / "top.txt").write_text("x")
        quiet_git("add", "-A", cwd=root)
        quiet_git("commit", "-qm", "base", cwd=root)
        quiet_git("checkout", "-q", "-b", "work", cwd=root)
        return root

    # covers: spec 0010 AC-1 (M3: a scope repo in a subfolder of a git repo keeps its committed frontend files)
    def test_subfolder(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.repo(os.path.realpath(d))
            sub = root / "app"
            (sub / "src" / "components").mkdir(parents=True)
            (sub / "src" / "components" / "Nav.tsx").write_text("x")
            quiet_git("add", "-A", cwd=root)
            quiet_git("commit", "-qm", "nav", cwd=root)
            self.assertEqual(run.frontend_changed(str(sub))[1], ["src/components/Nav.tsx"])

    # covers: spec 0008 AC-3 (M4: a git failure raises instead of reading as an empty tree that hides every edit)
    def test_snapshot_git_fails(self):
        with tempfile.TemporaryDirectory() as d:
            ns = SimpleNamespace(c=SimpleNamespace(path=d, scope_dir="docs/scope"))
            with self.assertRaises(RuntimeError):
                run.Run.snapshot(ns)

    # covers: spec 0008 AC-3 (M13: specs under an ignored .workflow/ are in the snapshot)
    def test_workflow_specs(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.repo(os.path.realpath(d))
            (root / ".gitignore").write_text(".workflow/\n")
            (root / ".workflow" / "specs" / "0001-x").mkdir(parents=True)
            (root / ".workflow" / "specs" / "0001-x" / "index.md").write_text("spec")
            (root / "tests").mkdir()
            (root / "tests" / "test_a.py").write_text("def test_a(): pass\n")
            ns = SimpleNamespace(c=SimpleNamespace(path=str(root), scope_dir=".workflow/scope"))
            self.assertEqual(sorted(run.Run.snapshot(ns)), [".workflow/specs/0001-x/index.md", "tests/test_a.py"])

    # covers: spec 0008 AC-3 (commit review: an edit past the text cap, same size, still changes the hash)
    def test_past_cap(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.repo(os.path.realpath(d))
            (root / "tests").mkdir()
            f = root / "tests" / "test_big.py"
            f.write_text("# pad\n" + "x" * 40)
            ns = SimpleNamespace(c=SimpleNamespace(path=str(root), scope_dir="docs/scope"))
            with mock.patch.object(run, "SNAPSHOT_CAP", 8):
                before = run.Run.snapshot(ns)["tests/test_big.py"]
                f.write_text("# pad\n" + "x" * 39 + "y")
                after = run.Run.snapshot(ns)["tests/test_big.py"]
            self.assertEqual(before[1], "# pad\nxx")
            self.assertNotEqual(before[0], after[0])

    # covers: spec 0008 AC-3 (commit review: a huge sparse file is never read past the cap, so the snapshot ends fast)
    def test_sparse(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.repo(os.path.realpath(d))
            (root / "tests").mkdir()
            with open(root / "tests" / "test_huge.py", "wb") as f:
                f.truncate(4 << 40)
            ns = SimpleNamespace(c=SimpleNamespace(path=str(root), scope_dir="docs/scope"))
            signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TimeoutError("snapshot read the whole file")))
            signal.alarm(5)
            try:
                t0 = time.monotonic()
                snap = run.Run.snapshot(ns)
            finally:
                signal.alarm(0)
            self.assertLess(time.monotonic() - t0, 3)
            self.assertEqual(len(snap["tests/test_huge.py"][1]), run.SNAPSHOT_CAP)

    # covers: spec 0008 AC-3 (commit review: a specs folder pointing out of the repo is not walked; a link to
    # /dev/zero and a FIFO are never read, so the snapshot neither hangs nor fills memory)
    def test_workflow_specs_hostile(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.repo(os.path.realpath(d) + "/r")
            outside = Path(d, "outside")
            outside.mkdir()
            (outside / "secret.md").write_text("x")
            (root / ".gitignore").write_text(".workflow/\n")
            (root / ".workflow").mkdir()
            (root / ".workflow" / "specs").symlink_to(outside)
            ns = SimpleNamespace(c=SimpleNamespace(path=str(root), scope_dir=".workflow/scope"))
            self.assertEqual(run.Run.snapshot(ns), {})
            (root / ".workflow" / "specs").unlink()
            (root / ".workflow" / "specs").mkdir()
            (root / ".workflow" / "specs" / "zero.md").symlink_to("/dev/zero")
            os.mkfifo(root / ".workflow" / "specs" / "pipe.md")
            signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TimeoutError("snapshot hung")))
            signal.alarm(10)
            try:
                snap = run.Run.snapshot(ns)
            finally:
                signal.alarm(0)
            self.assertEqual(sorted(snap), [".workflow/specs/pipe.md", ".workflow/specs/zero.md"])
            self.assertEqual(snap[".workflow/specs/zero.md"][0], run.hashlib.sha256(b"symlink:/dev/zero").hexdigest())
            self.assertEqual(snap[".workflow/specs/pipe.md"][0], run.hashlib.sha256(b"special file").hexdigest())


class TestFreezeRefusals(RunCase):
    refused = staticmethod(lambda self, r, detail: (self.assertEqual(r.returncode, 5, r.stdout + r.stderr),
                                                    self.assertIn(f"refused: no_sandbox: {detail}", r.stdout)))

    # covers: spec 0007 AC-8 (M5: git remote -v failing refuses instead of denying only the forges)
    def test_remote_fails(self):
        real = os.path.realpath(subprocess.run(["sh", "-c", "command -v git"], capture_output=True, text=True).stdout.strip())
        (self.bin / "git").unlink()
        self.fake("git", f'#!/bin/sh\ncase " $* " in *" remote "*) echo boom >&2; exit 1;; esac\nexec {real} "$@"\n')
        self.refused(self, self.wf("demo", "-y"), "git remote -v failed: boom")

    # covers: spec 0007 AC-7 (M11: a hooks folder that cannot be listed, or a settings file that cannot be read,
    # refuses instead of reading as no hooks)
    def test_unreadable(self):
        hooks = self.repo / ".git" / "hooks"
        hooks.mkdir()
        hooks.chmod(0)
        self.addCleanup(hooks.chmod, 0o755)
        self.refused(self, self.wf("demo", "-y"), f"cannot list {hooks}: Permission denied")
        hooks.chmod(0o755)
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / "settings.json").write_text("{broken")
        self.refused(self, self.wf("demo", "-y"), f"{self.repo}/.claude/settings.json cannot be read as settings")


class TestNtfyServer(unittest.TestCase):
    # covers: spec 0005 AC-1 (M6: a server URL urllib cannot split refuses no_ntfy, never a traceback)
    def test_bad_url(self):
        with tempfile.TemporaryDirectory() as d:
            write_config(d, "https://[x")
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": d}):
                with self.assertRaisesRegex(ntfy.Invalid, "server must start with https://"):
                    ntfy.load()


class TestHidden(unittest.TestCase):
    # covers: spec 0009 AC-3 step 3 (M7: more secret files and your own Read denies are hidden; M10: each at its
    # real path, so a symlinked ~/.ssh no longer fails bwrap)
    def test_argv(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            home, repo, dots = Path(d, "home"), Path(d, "repo"), Path(d, "dots")
            for p in (home / ".claude", home / "vault", repo, dots / "ssh"):
                p.mkdir(parents=True)
            (home / ".ssh").symlink_to(dots / "ssh")
            (home / ".npmrc").write_text("x")
            (home / "secret.env").write_text("x")
            h = str(home)
            (home / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": [
                f"Read(/{h}/secret.env)", f"Read(/{h}/vault/**)", "Read(**/*.pem)", f"Edit(/{h}/other)",
                f"Read(/{h}/missing)"]}}))
            ns = SimpleNamespace(c=SimpleNamespace(path=str(repo)), bwrap="/bin/bwrap",
                                 guard_settings={"sandbox": {"filesystem": {"denyWrite": []}}},
                                 browser={"start": "x", "wf_dirs": []})
            with mock.patch.dict(os.environ, {"HOME": h}):
                argv = run.Run.jail_argv(ns)
            self.assertEqual(argv[argv.index(str(repo)) + 2:-5], [
                "--tmpfs", f"{dots}/ssh", "--ro-bind", "/dev/null", f"{h}/.npmrc",
                "--ro-bind", "/dev/null", f"{h}/secret.env", "--tmpfs", f"{h}/vault"])


class TestSubmoduleHooks(RunCase):
    # covers: spec 0007 AC-2, AC-7 (M8: a submodule's config and hooks are denied to calls and guarded)
    def test_planted_hook(self):
        mod = self.repo / ".git" / "modules" / "lib"
        (mod / "hooks").mkdir(parents=True)
        (mod / "HEAD").write_text("ref: refs/heads/main\n")
        (mod / "config").write_text("[core]\n")
        (mod / "hooks" / "pre-commit").write_text("#!/bin/sh\n")
        # A new hook file is stopped by denyWrite (no sandbox in the fake); an existing one is hashed.
        self.steps([{"write_file": [[".git/modules/lib/hooks/pre-commit", "#!/bin/sh\ncurl x\n"]]}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        rec = self.assert_stopped(r, "guard_changed", calls=1, repo=True)
        self.assertEqual(rec["detail"].split(" ")[0], f"{mod}/hooks/pre-commit")
        a = self.argv(1)["argv"]
        deny = json.loads(a[a.index("--settings") + 1])["sandbox"]["filesystem"]["denyWrite"]
        self.assertEqual(deny[-2:], [f"{mod}/config", f"{mod}/hooks"])
        self.assertIn(f"{mod}/hooks/pre-commit", rec["repos"][0]["guard"]["guarded_files"])
        self.assertIn(f"{mod}/config", rec["repos"][0]["guard"]["guarded_files"])


class TestDesignPerFeature(QueueCase):
    # covers: spec 0010 AC-7, spec 0011 FeatureEntry (M12: each feature keeps its own design record)
    def test_two_features(self):
        two = ONE + "\n### 2. B · auto\n- [x] (spec)\n- [ ] `/develop b`\n"
        self.make_repo("two", two)
        self.steps([{}, {"tick": False}, {}, {"tick": False}])
        r = self.wf("two", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        empty = {"base": None, "changed": [], "reports": {}, "problems": []}
        self.assertEqual([e["design"] for e in rec["features"]], [empty, empty])
        self.assertNotIn("design", rec)


class TestMutantSurvivors(unittest.TestCase):
    # covers: spec 0009 AC-1 (0.0.0.0 is not a local app address)
    def test_app_url(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "AGENTS.md").write_text("## Standing answers\n- app start: x\n- app url: http://0.0.0.0:3000\n")
            self.assertIsNone(run.read_answers(SimpleNamespace(path=d, scope_dir="docs/scope"))[0])

    # covers: spec 0009 AC-3 (a sibling folder sharing a prefix is not under it)
    def test_under(self):
        self.assertTrue(run.under("/a/b", ["/a/b"]))
        self.assertTrue(run.under("/a/b/c", ["/a/b/"]))
        self.assertFalse(run.under("/a/bc", ["/a/b"]))

    # covers: spec 0008 AC-9 (a repo reached through a symlink is trusted by its real path)
    def test_untrusted_alias(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            Path(d, "repo").mkdir()
            Path(d, "alias").symlink_to(Path(d, "repo"))
            Path(d, "wf").mkdir()
            Path(d, "wf", "allowed.json").write_text(json.dumps([f"{d}/repo"]))
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": d}):
                self.assertIsNone(run.untrusted(f"{d}/alias"))
                self.assertIn("is not listed", run.untrusted(d))


class TestPlanLock(unittest.TestCase):
    # covers: spec 0011 AC-5 (L1: a repo skipped scope_unreadable at the plan lets its lock go)
    def test_released(self):
        with tempfile.TemporaryDirectory() as d:
            lock = Path(d, "x.lock")
            fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX)
            c = SimpleNamespace(path=d, name="x", scope_dir="docs/scope", warnings=[], display_name=lambda: "x")
            with mock.patch.object(wf, "head_branch", return_value="work"), \
                    mock.patch.dict(os.environ, {"XDG_STATE_HOME": d}):
                r = run.Run(None, ARGS)
                h = r.add(c)
                h["lock_fd"] = fd
                with mock.patch.object(run, "repo_features", side_effect=OSError("gone")), redirect_stdout(io.StringIO()):
                    r.plan()
            self.assertIsNone(h["lock_fd"])
            other = os.open(lock, os.O_RDWR)
            fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.close(other)


class TestReplyId(DecisionCase):
    # covers: spec 0011 AC-12 (L2: the reply that answered a record is stored and skipped when read again)
    def test_reply(self):
        repo = self.make_repo("rid", ONE)
        self.commit(repo)
        i = self.open_one("rid")["id"]
        mid = self.ntfy.add(f"{i} 2")
        self.steps([{"tick": False, "edit": [["- [ ] `/develop a`", "- [x] `/develop a`"]],
                     "run": [self.keep_queue("during")]}, {"tick": False}])
        r = self.wf("rid", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        during = json.loads((self.fakes / "during").read_text())["decisions"][0]
        self.assertEqual((during["answer"], during["reply"]), ("SQLite", mid))
        _, rec = self.run_record()
        self.assertEqual(rec["decisions"][0]["ignored"], 0)

    # covers: spec 0011 AC-12 (L2: a stored reply read again from an older cursor is not counted ignored)
    def test_reread(self):
        repo = self.make_repo("rr", ONE + "\n### 2. B · auto\n- [x] (spec)\n- [ ] `/develop b`\n")
        self.commit(repo)
        mid = self.ntfy.add("cd34 1")
        p = self.state / "wf" / "queue.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        old = decision(repo, "1. A", did="ab12", asked="2026-10-12T08:00:00+02:00", command="/develop a",
                       box_text="`/develop a`")
        done = decision(repo, "2. B", did="cd34", command="/develop b", box_text="`/develop b`", answer="SQLite",
                        source="phone", answered="2026-10-12T09:05:00+02:00", reply=mid)
        p.write_text(json.dumps({"version": 1, "parks": [], "decisions": [old, done]}))
        self.steps([{"tick": False, "edit": [["- [ ] `/develop b`", "- [x] `/develop b`"]]}, {"tick": False}])
        r = self.wf("rr", "-y", "--max-wait", "0.0001", mode="fast")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual([(e["id"], e["ignored"]) for e in rec["decisions"]], [("cd34", 0)])


class TestOwedMarkerOnly(unittest.TestCase):
    # covers: spec 0012 AC-1 (L4: a box that is only the marker is still owed to you)
    def test_marker_only(self):
        nb = wf.pick_next(wf.parse_text("### 1. A\n- [ ] · waits on you\n"))
        self.assertEqual((nb.owed, nb.waiting), ("· waits on you", True))
        self.assertEqual(run.box_refusal(nb)[0], "waiting")


class TestAllowRace(RunCase):
    # covers: spec 0008 AC-9 (L5: a write never touches another writer's temp file, and wf allow waits for the lock)
    def test_temp_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "allowed.json")
            Path(d, "allowed.json.tmp").write_text("other writer")
            ntfy.write(["/x"], str(p))
            self.assertEqual(json.loads(p.read_text()), ["/x"])
            self.assertEqual(Path(d, "allowed.json.tmp").read_text(), "other writer")
            self.assertEqual(sorted(os.listdir(d)), ["allowed.json", "allowed.json.tmp"])
            self.assertEqual(os.stat(p).st_mode & 0o777, 0o600)

    def test_lock(self):
        lock = self.tmp / "config" / "wf" / "allowed.json.lock"
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        repo = self.make_repo("late", ONE)
        (self.tmp / "config" / "wf" / "allowed.json").write_text("[]")
        p = subprocess.Popen([sys.executable, str(WF), "allow", str(repo)], env=self.env, stdout=subprocess.PIPE, text=True)
        time.sleep(1)
        self.assertIsNone(p.poll())
        os.close(fd)
        out, _ = p.communicate(timeout=30)
        self.assertEqual(p.returncode, 0, out)
        self.assertEqual(json.loads((self.tmp / "config" / "wf" / "allowed.json").read_text()), [str(repo)])


class TestSmallFixes(RunCase):
    # covers: wf run --help (L3: --max-wait is the run's end wait budget)
    def test_help(self):
        r = subprocess.run([sys.executable, str(WF), "run", "--help"], capture_output=True, text=True)
        self.assertIn("hours the run waits at its end for your phone replies", " ".join(r.stdout.split()))

    # covers: L7 (a hung git returns a failure in time instead of stalling the run)
    def test_git_timeout(self):
        self.fake("slowgit", "#!/bin/sh\nsleep 10\n")
        with mock.patch.object(wf, "GIT", str(self.bin / "slowgit")), mock.patch.object(wf, "GIT_TIMEOUT", 0.5):
            t0 = time.monotonic()
            r = wf.git(str(self.tmp), "status")
        self.assertLess(time.monotonic() - t0, 5)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (124, "", "timed out after 0.5 s"))

    # covers: spec 0008 AC-10 (L8: internal_error keeps one detail line and prints the trace to stderr)
    def test_traceback(self):
        r = self.wf("demo", "-y", mode="boom")
        self.assertIn("stopped: internal_error: RuntimeError: forced failure", r.stdout)
        self.assertIn("Traceback (most recent call last):", r.stderr)
        self.assertIn("RuntimeError: forced failure", r.stderr)

    # covers: spec 0007 AC-3 (L11: an IPv6 remote keeps its whole address)
    def test_url_host(self):
        for url, host in (("ssh://git@[::1]:22/x.git", "::1"), ("https://[fe80::1]/x", "fe80::1"),
                          ("git@[2001:db8::1]:x.git", "2001:db8::1"), ("ssh://git@host:22/x", "host"),
                          # git's [user@host:port]:path form (commit review): the host alone, never user@host:port.
                          ("[git@git.corp.example:2222]:team/repo.git", "git.corp.example"),
                          ("[git.corp.example:2222]:x.git", "git.corp.example"), ("[git@::1]:x.git", "::1"),
                          ("git@github.com:x/y.git", "github.com"), ("/local/path", None)):
            self.assertEqual(run.url_host(url), host, url)

    # covers: spec 0006 AC-6 (L13: a lone open milestone under a ticked parent is the last box)
    def test_last_box_milestone(self):
        c = SimpleNamespace(path=str(self.repo), scope_dir="docs/scope", name="x", warnings=[])
        with mock.patch.object(wf, "head_branch", return_value="work"):
            r = run.Run(c, ARGS)
        r.feature = "1. A"
        scope = self.repo / "docs" / "scope" / "scope.md"
        head = "# Scope: x\n**Autopilot:** allowed\n### 1. A · auto\n- [x] (spec)\n- [x] `/develop a`\n   - [ ] m1\n"
        for text, want in ((head, True), (head + "   - [ ] m2\n", False), (head + "- [ ] `/test a`\n", False)):
            scope.write_text(text)
            self.assertIs(r.last_box(), want, text)

    # covers: spec 0011 AC-12 (L13: a failed ack prints a warning instead of failing silently)
    def test_ack_warning(self):
        fake = FakeNtfy()
        self.addCleanup(fake.close)
        write_config(self.tmp / "config", fake.url, codes=[f"code{i:04d}" for i in range(5)])
        p = self.state / "wf" / "queue.json"
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({"version": 1, "parks": [], "decisions": [decision(self.repo, "1. Loop")]}))
        fake.add("ab12 1")
        fake.fail_posts = 10
        env = {"XDG_STATE_HOME": str(self.state), "XDG_CONFIG_HOME": str(self.tmp / "config")}
        with mock.patch.dict(os.environ, env), mock.patch.object(ntfy, "RETRY_GAP", 0.01):
            r = run.Run(None, ARGS)
            r.ntfy = ntfy.load()
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertTrue(r.poll())
        self.assertIn("answered: ab12 Postgres (recommended) (phone)\nwarning: ack ab12 failed: ", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
