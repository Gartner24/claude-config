"""Second review stack of 2026-10-12 (c95f181..d20a328, docs/briefs/runner-review-stack-2026-10-12.md): one test
per finding."""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402
from test_browser import AppCase  # noqa: E402
from test_queue import ONE, SubcommandCase, decision, park  # noqa: E402
from test_review_fixes import quiet_git  # noqa: E402
from test_run import RunCase  # noqa: E402

PLANTED = "AGENTS.md standing answers changed during the run; check them before the next wf run"


def alarm(seconds, what):
    signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TimeoutError(what)))
    signal.alarm(seconds)


class TestAnswersLine(SubcommandCase):
    # covers: spec 0011 AC-6 (the plan's answers line shows every standing answer, app start and app url included;
    # only `answers: none` was pinned and a constant passed every test)
    def test_queue(self):
        repo = self.make_repo("q", ONE)
        (repo / "AGENTS.md").write_text("## Standing answers\n- run suite: yes\n- app start: npm run dev -- --port 3000\n"
                                        "- app url: http://localhost:3000\n")
        r = self.sub("queue", "q")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[1],
                         "  answers: run suite yes, app start npm run dev -- --port 3000, app url http://localhost:3000")


class TestAnswersLineRun(AppCase):
    # covers: spec 0011 AC-6 (wf run's confirm shows the frozen app start and app url)
    def test_run(self):
        self.steps([{}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"\n  answers: app start {self.start_cmd}, app url {self.url}\n", r.stdout)


class TestAnswersFile(RunCase):
    def read(self, d):
        return run.read_answers(SimpleNamespace(path=d, scope_dir="docs/scope"))

    # covers: spec 0006 AC-3 (second review: a FIFO or a link to /dev/zero is refused, never read; a file past the
    # cap is refused; CRLF still parses as text mode read it)
    def test_special(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "AGENTS.md")
            os.mkfifo(p)
            alarm(5, "read_answers hung")
            try:
                self.assertEqual(self.read(d), (None, "AGENTS.md: not a regular file"))
                p.unlink()
                p.symlink_to("/dev/zero")
                self.assertEqual(self.read(d), (None, "AGENTS.md: not a regular file"))
            finally:
                signal.alarm(0)
            p.unlink()
            p.write_text("## Standing answers\r\n- run suite: yes\r\n- done: yes\r\n")
            self.assertEqual(self.read(d), ({"run suite": "yes", "done": "yes"}, None))
            with mock.patch.object(run, "SNAPSHOT_CAP", 8):
                self.assertEqual(self.read(d), (None, "AGENTS.md: larger than 8 bytes"))

    # covers: spec 0011 AC-6 (second review: a call that swaps AGENTS.md for a FIFO stops its repo guard_changed;
    # the reread after the call used to block wf on it)
    def test_fifo_stop(self):
        (self.repo / "AGENTS.md").write_text("## Standing answers\n- run suite: yes\n")
        swap = "import os; os.remove('AGENTS.md'); os.mkfifo('AGENTS.md')"
        self.steps([{"run": [[sys.executable, "-c", swap]]}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        rec = self.assert_stopped(r, "guard_changed", calls=1, repo=True)
        self.assertEqual(rec["detail"], PLANTED)


class TestSubmodules(RunCase):
    def gitlink(self, path):
        quiet_git("update-index", "--add", "--cacheinfo", f"160000,{'1' * 40},{path}", cwd=self.repo)

    def settings(self):
        a = self.argv(1)["argv"]
        return json.loads(a[a.index("--settings") + 1])["sandbox"]["filesystem"]["denyWrite"], \
            a[a.index("--disallowedTools") + 1]

    # covers: spec 0007 AC-2, AC-7 (second review: a submodule cloned in place keeps its .git folder in the work
    # tree; its config, hooks and config.worktree are denied and hashed, the whole folder denied to Edit)
    def test_in_tree(self):
        self.gitlink("lib")
        git = self.repo / "lib" / ".git"
        (git / "hooks").mkdir(parents=True)
        (git / "config").write_text("[core]\n")
        (git / "hooks" / "pre-commit").write_text("#!/bin/sh\n")
        self.steps([{"write_file": [["lib/.git/hooks/pre-commit", "#!/bin/sh\ncurl x\n"]]}, {}, {"tick": False}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "guard_changed", calls=1, repo=True)
        self.assertEqual(rec["detail"].split(" ")[0], f"{git}/hooks/pre-commit")
        deny, tools = self.settings()
        for p in (f"{git}/config", f"{git}/hooks", f"{git}/config.worktree"):
            self.assertIn(p, deny)
        self.assertIn(f"Edit(/{git}/**)", tools.split(","))
        self.assertIn(f"{git}/config", rec["repos"][0]["guard"]["guarded_files"])

    # covers: spec 0007 AC-7 (second review: an absorbed submodule's .git pointer file and its git dir's include
    # targets are hashed and denied; a rewritten pointer stops the repo)
    def test_pointer_and_include(self):
        self.gitlink("lib")
        mod = self.repo / ".git" / "modules" / "lib"
        mod.mkdir(parents=True)
        (mod / "HEAD").write_text("ref: refs/heads/main\n")
        (mod / "config").write_text("[include]\n\tpath = ../extra.cfg\n")
        (self.repo / ".git" / "modules" / "extra.cfg").write_text("[core]\n")
        (self.repo / "lib").mkdir()
        (self.repo / "lib" / ".git").write_text("gitdir: ../.git/modules/lib\n")
        self.steps([{"write_file": [["lib/.git", "gitdir: ../evil\n"]]}, {}, {"tick": False}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "guard_changed", calls=1, repo=True)
        pointer = f"{self.repo}/lib/.git"
        self.assertEqual(rec["detail"].split(" ")[0], pointer)
        deny, _ = self.settings()
        guarded = rec["repos"][0]["guard"]["guarded_files"]
        for p in (pointer, f"{self.repo}/.git/modules/extra.cfg", f"{mod}/config.worktree"):
            self.assertIn(p, deny)
            self.assertIn(p, guarded)

    # covers: spec 0007 AC-7 (commit review: a submodule not checked out has its .git hashed as absent, so a call
    # that creates one with a hook stops the repo)
    def test_absent(self):
        self.gitlink("lib")
        (self.repo / "lib").mkdir()
        self.steps([{"write_file": [["lib/.git/hooks/pre-commit", "#!/bin/sh\ncurl x\n"]]}, {}, {"tick": False}])
        rec = self.assert_stopped(self.wf("demo", "-y"), "guard_changed", calls=1, repo=True)
        self.assertEqual(rec["detail"].split(" ")[0], f"{self.repo}/lib/.git")
        self.assertEqual(rec["repos"][0]["guard"]["guarded_files"][f"{self.repo}/lib/.git"], "absent")
        self.assertNotIn(f"{self.repo}/lib/.git", self.settings()[0])

    # covers: spec 0007 AC-8 (commit review: a submodule .git that is a symlink refuses, its target unguardable)
    def test_symlink(self):
        self.gitlink("lib")
        (self.repo / "lib").mkdir()
        (self.repo / "elsewhere").mkdir()
        (self.repo / "lib" / ".git").symlink_to(self.repo / "elsewhere")
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn(f"refused: no_sandbox: {self.repo}/lib/.git is a symlink, so its git dir cannot be guarded",
                      r.stdout)

    # covers: spec 0011 AC-9 (commit review: a call that swaps the submodule folder for a link to / cannot make a
    # global settings change look like this repo's own; the run stops)
    def test_swap_to_root(self):
        self.gitlink("lib")
        (self.repo / "lib").mkdir()
        (self.repo / "lib" / ".git").write_text("gitdir: ../.git/modules/lib\n")
        swap = "import os, shutil; shutil.rmtree('lib'); os.symlink('/', 'lib')"
        self.steps([{"run": [[sys.executable, "-c", swap]],
                     "write_file": [[str(self.tmp / ".claude" / "settings.json"), "{}"]]}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assert_stopped(r, "guard_changed", calls=1)

    # covers: spec 0011 AC-9, spec 0017 AC-7 (commit review: a hook planted in a submodule git dir that another
    # trusted repo uses as its common dir still stops the child whose call planted it)
    def test_shared_with_worktree(self):
        lib = self.repo / "lib"
        lib.mkdir()
        quiet_git("init", "-q", "-b", "main", cwd=lib)
        (lib / "docs" / "scope").mkdir(parents=True)
        (lib / "docs" / "scope" / "scope.md").write_text(ONE)
        (lib / ".git" / "hooks").mkdir(exist_ok=True)
        (lib / ".git" / "hooks" / "pre-commit").write_text("#!/bin/sh\n")
        quiet_git("add", "-A", cwd=lib)
        quiet_git("commit", "-qm", "x", cwd=lib)
        wt = self.tmp / "root" / "wt"
        quiet_git("worktree", "add", "-q", "-b", "work", str(wt), cwd=lib)
        self.allow(wt)
        quiet_git("update-index", "--add", "--cacheinfo", f"160000,{'1' * 40},lib", cwd=self.repo)
        self.steps({"demo": [{"write_file": [[str(lib / ".git" / "hooks" / "pre-commit"), "#!/bin/sh\ncurl x\n"]]}],
                    "wt": [{}, {"tick": False}]})
        r = self.wf("-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        # Spec 0017: demo is a child of its own, so its submodule's hook is its own file and ends that child.
        self.assertIn(f"[demo] stopped repo demo: guard_changed: {lib}/.git/hooks/pre-commit changed", r.stdout)

    # covers: spec 0011 AC-9 (a trusted repo checked out as this repo's submodule, dotfiles with its nvim child: the
    # child's git reads the .git pointer, so a call rewriting it stops the parent repo's child; spec 0017 AC-3 starts
    # the nested child only after that, and its own checks refuse the broken pointer)
    def test_child_repo_held(self):
        nvim = self.repo / "nvim"
        (self.repo / ".git" / "modules").mkdir()
        quiet_git("init", "-q", "-b", "work", f"--separate-git-dir={self.repo}/.git/modules/nvim", str(nvim),
                  cwd=self.repo)
        (nvim / "docs" / "scope").mkdir(parents=True)
        (nvim / "docs" / "scope" / "scope.md").write_text(ONE)
        quiet_git("add", "-A", cwd=nvim)
        quiet_git("commit", "-qm", "x", cwd=nvim)
        self.allow(nvim)
        self.gitlink("nvim")
        pointer = nvim / ".git"
        self.steps([{"write_file": [[str(pointer), "gitdir: ../evil\n"]]}, {}, {"tick": False}])
        r = self.wf("-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        # Spec 0017 AC-3: nvim lies inside demo, so its child starts after demo's ends, on the broken pointer.
        self.assertIn(f"[demo] stopped repo demo: guard_changed: {pointer} changed", r.stdout)
        self.assertIn("\n[nvim] refused: branch: no git, switch to a work branch first\n", r.stdout)

    # covers: spec 0011 AC-9 (commit review: the submodule .git is matched as written and as resolved at start, so a
    # repo under a symlinked ~/projects still sees a worktree whose resolved common dir lies in its submodule)
    def test_symlinked_parent(self):
        text, real = "/home/u/projects/a/lib/.git", "/data/projects/a/lib/.git"
        h = {"c": SimpleNamespace(path="/home/u/projects/a"), "common": "/data/projects/a/.git",
             "repo": {"guard": {"submodules": [[text, real]]}}}
        o = {"c": SimpleNamespace(path="/data/wt"), "common": real, "repo": {}}
        ns = SimpleNamespace(held=[h, o])
        with mock.patch.object(run.os.path, "realpath", side_effect=lambda p: p):
            self.assertFalse(run.Run.own_file(ns, h, f"{text}/hooks/pre-commit"))
            ns.held = [h]
            self.assertTrue(run.Run.own_file(ns, h, f"{text}/hooks/pre-commit"))

    # covers: spec 0007 AC-9 (commit review: a submodule folder that is a symlink at start is recorded in both forms)
    def test_alias_record(self):
        self.gitlink("lib")
        out = self.tmp / "out"
        out.mkdir()
        (out / ".git").write_text("gitdir: x\n")
        (self.repo / "lib").symlink_to(out)
        self.steps([{"tick": False}])
        r = self.wf("demo", "-y", "--max-calls", "1")
        self.assertTrue((self.state / "wf" / "runs").exists(), r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual(rec["repos"][0]["guard"]["submodules"], [[f"{self.repo}/lib/.git", f"{out}/.git"]])

    # covers: spec 0007 AC-8 (second review: git ls-files failing refuses, never reads as no submodules; a submodule
    # config git cannot read refuses as the main config does)
    def test_git_failures(self):
        real = shutil.which("git")
        (self.bin / "git").unlink()
        self.fake("git", f'#!/bin/sh\ncase " $* " in *" ls-files "*) echo boom >&2; exit 1;; esac\nexec {real} "$@"\n')
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn("refused: no_sandbox: git ls-files -z --stage failed: boom", r.stdout)
        (self.bin / "git").unlink()
        (self.bin / "git").symlink_to(real)
        mod = self.repo / ".git" / "modules" / "lib"
        mod.mkdir(parents=True)
        (mod / "HEAD").write_text("x\n")
        (mod / "config").write_text("[broken\n")
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn(f"refused: no_sandbox: git cannot read {mod}/config", r.stdout)

    # covers: spec 0007 AC-8 (second review: a submodule hooks folder or modules folder that cannot be listed
    # refuses no_sandbox; one raised a traceback, the other read as no submodule)
    def test_unreadable(self):
        mod = self.repo / ".git" / "modules" / "lib"
        (mod / "hooks").mkdir(parents=True)
        (mod / "HEAD").write_text("ref: refs/heads/main\n")
        (mod / "hooks").chmod(0)
        self.addCleanup((mod / "hooks").chmod, 0o755)
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn(f"refused: no_sandbox: cannot list {mod}/hooks: Permission denied", r.stdout)
        (mod / "hooks").chmod(0o755)
        hidden = self.repo / ".git" / "modules" / "other"
        hidden.mkdir()
        hidden.chmod(0)
        self.addCleanup(hidden.chmod, 0o755)
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn(f"refused: no_sandbox: cannot list {hidden}: Permission denied", r.stdout)


class TestJailAncestor(unittest.TestCase):
    # covers: spec 0009 AC-3 step 3 (second review: a Read deny holding the repo never puts a tmpfs over its bind)
    def test_argv(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(os.path.realpath(d), "home")
            repo = home / "projects" / "repo"
            (home / ".claude").mkdir(parents=True)
            repo.mkdir(parents=True)
            (home / "vault").mkdir()
            (home / ".gitconfig").write_text("x")
            (repo / ".claude").mkdir()
            h = str(home)
            (home / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": [
                f"Read(/{h}/**)", f"Read(/{h}/projects)", f"Read(/{h}/vault/**)"]}}))
            ns = SimpleNamespace(c=SimpleNamespace(path=str(repo)), bwrap="/bin/bwrap",
                                 guard_settings={"sandbox": {"filesystem": {"denyWrite": [f"{h}/.gitconfig",
                                                                                          f"{repo}/.claude"]}}},
                                 browser={"start": "x", "wf_dirs": []})
            with mock.patch.dict(os.environ, {"HOME": h}):
                argv = run.Run.jail_argv(ns)
            # The denied folders that hold the repo are hidden first, the repo goes back on top with its read only
            # paths (commit review: skipping them showed the app everything you denied); a read only path elsewhere
            # in the denied home stays hidden (commit review: binding ~/.gitconfig back showed it).
            self.assertEqual(argv[argv.index("/run") + 1:-5], [
                "--tmpfs", h, "--tmpfs", f"{h}/projects", "--bind", str(repo), str(repo),
                "--ro-bind", f"{repo}/.claude", f"{repo}/.claude", "--tmpfs", f"{h}/vault"])

    # covers: spec 0009 AC-3 step 3 (a denied cache folder that is itself a write bind is hidden, then bound back,
    # so the app keeps its cache)
    def test_cache_bind(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(os.path.realpath(d))
            (home / ".claude").mkdir()
            (home / ".cache").mkdir()
            (home / "repo").mkdir()
            (home / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": [f"Read(/{home}/.cache/**)"]}}))
            ns = SimpleNamespace(c=SimpleNamespace(path=str(home / "repo")), bwrap="/bin/bwrap",
                                 guard_settings={"sandbox": {"filesystem": {"denyWrite": []}}},
                                 browser={"start": "x", "wf_dirs": []})
            with mock.patch.dict(os.environ, {"HOME": str(home)}):
                argv = run.Run.jail_argv(ns)
            self.assertEqual(argv[argv.index("/run") + 1:-5], [
                "--tmpfs", f"{home}/.cache", "--bind", f"{home}/repo", f"{home}/repo",
                "--bind", f"{home}/.cache", f"{home}/.cache"])


class TestSnapshotScope(unittest.TestCase):
    # covers: spec 0008 AC-3 (second review: a tracked specs folder is not walked, so its ignored files stay out)
    def test_ignored_in_docs_specs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(os.path.realpath(d))
            quiet_git("init", "-q", "-b", "main", cwd=root)
            (root / ".gitignore").write_text("__pycache__/\n")
            (root / "docs" / "specs" / "probes" / "__pycache__").mkdir(parents=True)
            (root / "docs" / "specs" / "index.md").write_text("spec")
            (root / "docs" / "specs" / "probes" / "__pycache__" / "p.pyc").write_text("x")
            ns = SimpleNamespace(c=SimpleNamespace(path=str(root), scope_dir="docs/scope"))
            self.assertEqual(sorted(run.Run.snapshot(ns)), ["docs/specs/index.md"])
            # A check-ignore git cannot answer stops the run, never skips or forces the walk.
            real = run.wf.git
            fail = lambda path, *args: (subprocess.CompletedProcess(args, 128, "", "fatal: x") if args[0] == "check-ignore"
                                        else real(path, *args))
            with mock.patch.object(run.wf, "git", side_effect=fail):
                with self.assertRaisesRegex(RuntimeError, "git check-ignore docs/specs/ failed: fatal: x"):
                    run.Run.snapshot(ns)

    # covers: spec 0008 AC-3 (second review: a skip added past the cap of a big test file counts as touched; the
    # diff of the first bytes used to see no change)
    def test_touched_past_cap(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(os.path.realpath(d))
            quiet_git("init", "-q", "-b", "main", cwd=root)
            (root / "tests").mkdir()
            f = root / "tests" / "test_big.py"
            f.write_text("# pad\ndef test_a(): pass\n")
            ns = SimpleNamespace(c=SimpleNamespace(path=str(root), scope_dir="docs/scope"))
            with mock.patch.object(run, "SNAPSHOT_CAP", 8):
                before = run.Run.snapshot(ns)
                self.assertEqual(run.touched(before, run.Run.snapshot(ns)), [])
                f.write_text("# pad\n@skip\ndef test_a(): pass\n")
                self.assertEqual(run.touched(before, run.Run.snapshot(ns)), ["tests/test_big.py"])


class TestParkedAnswered(SubcommandCase):
    # covers: spec 0011 AC-7 (an answered Decision whose feature has a Park that applies shows the parked line, not
    # nothing; and with nothing else queued the plan says nothing to run)
    def test_plan(self):
        repo = self.make_repo("q", ONE)
        self.commit(repo)
        self.write_queue([park(repo, "1. A", self.section_sha(repo, "1. A"))],
                         [decision(repo, "1. A", answer="SQLite", source="phone", answered="2026-10-12T10:00:00+02:00")])
        r = self.sub("queue", "q")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("  parked: 1. A: blocked: test park (retaken on a new commit)\n", r.stdout)
        self.assertIn("nothing to run", r.stdout)


class TestTraceFile(RunCase):
    # covers: spec 0008 AC-10 (L8: the whole trace of an internal_error is kept in the run folder)
    def test_trace(self):
        r = self.wf("demo", "-y", mode="boom")
        self.assertIn("stopped: internal_error: RuntimeError: forced failure", r.stdout)
        folder, _ = self.run_record()
        trace = (folder / "traceback.txt").read_text()
        self.assertTrue(trace.startswith("Traceback (most recent call last):"), trace)
        self.assertIn("RuntimeError: forced failure", trace)


if __name__ == "__main__":
    unittest.main()
