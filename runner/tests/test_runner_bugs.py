"""Row 78: runner bugs found while conducting the runs of 2026-10-18 (brief leftovers-2026-10-18, Runner bugs)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pr  # noqa: E402
import run  # noqa: E402
import wf  # noqa: E402
from test_clean_branches import Case  # noqa: E402
from test_design import PASSING  # noqa: E402
from test_never_stop import NeverStopCase  # noqa: E402
from test_queue import DONE_A, ONE, TICK_A, DecisionCase  # noqa: E402
from test_run import ask  # noqa: E402
from test_shared_plan import PLAN  # noqa: E402

ID = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
      "GIT_COMMITTER_EMAIL": "t@example.invalid"}


def git(repo, *args, data=None):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=data is None or None,
                          input=data, env=ID).stdout


class GitRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "work")
        self.enterContext(mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.tmp / "state")}))

    def put(self, rel, text, commit=True):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        if commit:
            git(self.repo, "add", "-A")
            git(self.repo, "commit", "-qm", f"put {rel}")


class TestDesignAccept(GitRepo):
    def design_run(self):
        r = run.Run.__new__(run.Run)
        r.c, r.feature, r.entry, r.design_ok = SimpleNamespace(path=str(self.repo), scope_dir="docs/scope"), \
            "1. Loop", {}, set()
        r.files_changed = lambda: None
        return r

    # covers: bug 1 (accept as is holds in the next run, for the files as they were; a changed file asks again)
    def test_accept_persists(self):
        self.put("docs/scope/scope.md", "# Scope: x\n### 1. Loop · auto\n- [x] (spec)\n- [ ] `/sync`\n")
        self.put("index.html", "<p>x</p>\n")
        r = self.design_run()
        self.assertIn("index.html (no report)", r.design_check())
        r.apply_case({"case": "design_gate", "box_text": None}, "accept as is", SimpleNamespace(name="1. Loop"))
        self.assertIsNone(self.design_run().design_check())
        (self.repo / "index.html").write_text("<p>changed</p>\n")
        self.assertIn("index.html (no report)", self.design_run().design_check())

    # covers: bug 1 data model (design_ok may be absent; a bad record is refused, never read as an accept)
    def test_queue_validation(self):
        base = {"version": 1, "parks": [], "decisions": []}
        self.assertIsNone(run.queue_problem(base))
        good = {"repo": "/r", "feature": "1. A", "files": {"index.html": "ab"}}
        for value, want in (([good], None), ({}, "design_ok is not a list of records"),
                            ([{**good, "files": []}], "design_ok is not a list of records"),
                            ([{**good, "repo": 7}], "design_ok is not a list of records")):
            self.assertEqual(run.queue_problem({**base, "design_ok": value}), want, value)

    # covers: bug 7 (a file restored byte for byte with cp gets a new date, yet its passing report still covers it;
    # a real change after the report does not)
    def test_restored_file(self):
        self.put("index.html", "<p>x</p>\n")
        self.put(".design/audit-report.md", PASSING)
        later = os.stat(self.repo / ".design" / "audit-report.md").st_mtime_ns + 5 * 10 ** 9
        os.utime(self.repo / "index.html", ns=(later, later))
        self.assertEqual(run.design_problems(str(self.repo), ["index.html"])[1], [])
        (self.repo / "index.html").write_text("<p>edited after the report</p>\n")
        os.utime(self.repo / "index.html", ns=(later, later))
        self.assertEqual(run.design_problems(str(self.repo), ["index.html"])[1],
                         [{"path": "index.html", "problem": "older than the file"}])

    # covers: bug 7 (page and report in one commit, the report written a minute before it; a cp restore of the page
    # used to park it, since the commit time beat the report's own file date)
    def test_restored_same_commit(self):
        self.put("index.html", "<p>x</p>\n", commit=False)
        self.put(".design/audit-report.md", PASSING, commit=False)
        report = self.repo / ".design" / "audit-report.md"
        early = os.stat(report).st_mtime_ns - 60 * 10 ** 9
        os.utime(report, ns=(early, early))
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "page and report")
        later = os.stat(report).st_mtime_ns + 120 * 10 ** 9
        os.utime(self.repo / "index.html", ns=(later, later))
        self.assertEqual(run.design_problems(str(self.repo), ["index.html"])[1], [])
        report.write_text(PASSING + "\n")
        os.utime(report, ns=(early, early))
        self.assertEqual(run.design_problems(str(self.repo), ["index.html"])[1],
                         [{"path": "index.html", "problem": "older than the file"}])


class TestCopyTree(GitRepo):
    def tree(self, entries):
        """A tree object from (mode, path, text) entries, nested as written; git mktree keeps a duplicate name."""
        def mktree(items):
            lines = []
            for name, value in items.items():
                if isinstance(value, dict):
                    lines.append(f"040000 tree {mktree(value)}\t{name.split(chr(0))[0]}")
                else:
                    mode, text = value
                    sha = git(self.repo, "hash-object", "-w", "--stdin", data=text.encode()).decode().strip()
                    lines.append(f"{mode} blob {sha}\t{name.split(chr(0))[0]}")
            return git(self.repo, "mktree", "--missing", data="\n".join(lines).encode() + b"\n").decode().strip()
        return mktree(entries)

    # covers: bug 8 (a link chain whose written path stays inside but whose real path leaves the copy is refused)
    def test_link_chain(self):
        sha = self.tree({"d1": {"d2": {"y": ("120000", "../../e")}}, "x": ("120000", "d1/d2/y/../..")})
        dest = self.tmp / "clean"
        dest.mkdir()
        self.assertEqual(run.copy_tree(str(self.repo), sha, str(dest)), "a symlink leaves the clean copy: x")

    # covers: bug 8 (a file is never written through a folder an earlier link entry made)
    def test_parent_link(self):
        sha = self.tree({"b": {"x": ("100644", "x\n")}, "z": ("120000", "b"), "z\0": {"c": ("100644", "c\n")}})
        dest = self.tmp / "clean"
        dest.mkdir()
        self.assertEqual(run.copy_tree(str(self.repo), sha, str(dest)), "a path goes through a symlink: z/c")
        self.assertFalse((dest / "b" / "c").exists())


    # covers: bug 8 (a folder under a link chain that resolves outside is refused before any folder is made there)
    def test_no_folder_outside(self):
        sha = self.tree({"d1": {"d2": {"y": ("120000", "../../e")}}, "e": {"k": ("100644", "k\n")},
                         "x": ("120000", "d1/d2/y/../.."), "x\0": {"evil": {"f": ("100644", "f\n")}}})
        dest = self.tmp / "clean"
        dest.mkdir()
        self.assertEqual(run.copy_tree(str(self.repo), sha, str(dest)), "a path goes through a symlink: x/evil/f")
        self.assertFalse((self.tmp / "evil").exists())


class TestReusedBranch(GitRepo):
    def setUp(self):
        super().setUp()
        self.put("a.txt", "a\n")
        git(self.repo, "branch", "feat/0001-a")
        self.old = git(self.repo, "rev-parse", "work").strip()
        self.put("docs/specs/0063.md", "newer spec\n")

    # covers: bug 2 (a new record of a branch that already exists starts where it left its base, not at the base's
    # tip, so its squash never lays the old tree over main)
    def test_fork_point(self):
        self.assertEqual(pr.fork_point(str(self.repo), "work", "feat/0001-a"), self.old)
        self.assertEqual(pr.fork_point(str(self.repo), "work", "feat/0002-new"), git(self.repo, "rev-parse", "work").strip())

    # covers: bug 2 (a branch that does not start at its recorded base is never squashed onto it)
    def test_squash_refuses(self):
        git(self.repo, "switch", "-q", "feat/0001-a")
        self.put("b.txt", "b\n")
        self.put("c.txt", "c\n")
        head = git(self.repo, "rev-parse", "HEAD").strip()
        r = SimpleNamespace(c=SimpleNamespace(path=str(self.repo), scope_dir="docs/scope"), repo={}, asked=[])
        r.pr_ask = lambda rec, case, detail, *a, **k: r.asked.append(case)
        rec = {"feature": "1. A", "branch": "feat/0001-a", "base": "work", "base_sha": git(self.repo, "rev-parse", "work").strip()}
        self.assertIsNone(pr.squash(r, None, rec))
        self.assertEqual(r.asked, ["squash_failed"])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD").strip(), head)


class TestPublishReverts(Case):
    # covers: bug 2 (a PR whose diff against origin's default branch deletes a file main has asks, never pushes)
    def test_reverts_main(self):
        (self.repo / "docs" / "brief.md").write_text("main's brief\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "brief")
        self.git("push", "-q", "origin", "work")
        rec, head = self.branch({"docs/brief.md": None}, push=False)
        rec["state"] = "local"
        self.views(head)
        pr.publish(self.r, rec)
        self.assertEqual([c for c, _ in self.r.asked], ["pr_failed"])
        self.assertIn("would delete 1 file(s) that origin/work has: docs/brief.md", self.r.asked[0][1])
        self.assertEqual([c for c in self.gh_calls() if c[:2] == ["pr", "create"]], [])
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "feat/0001-a"), "")


class TestPlanFirst(GitRepo):
    # covers: bug 3 (a worktree child picks from main's plan, not its old branch's copy)
    def test_child_plans_from_main(self):
        main = self.tmp / "main"
        (main / "docs" / "scope").mkdir(parents=True)
        (main / "docs" / "scope" / "scope.md").write_text(PLAN.replace("### 1. A · auto\n",
                                                                         "### 1. A · auto\n- [x] (spec)\n"))
        tree = self.repo
        self.put("docs/scope/scope.md", "# Scope: old copy\n")
        r = run.Run.__new__(run.Run)
        r.args = SimpleNamespace(budget=1, call_timeout=1, max_calls=1, max_hours=1, max_wait=1)
        c = SimpleNamespace(path=str(tree), scope_dir="docs/scope", name="x", display_name=lambda: "x", warnings=[])
        h = {"c": c, "lock_fd": None}
        r.added, r.held, r.target, r.peek, r.warnings, r.record = [h], [h], str(tree), False, [], {"features": [], "notes": []}
        r.folder, r.again = None, set()
        r.use = lambda h: setattr(r, "c", h["c"])
        r.repo, r.branch, r.answers = {"repo": str(main), "tree": str(tree)}, "feat/0001-a", {"branches": "per spec"}
        with mock.patch.object(run, "key_of", lambda c: str(main)), mock.patch.object(pr, "watching", lambda r: False), \
                mock.patch.object(wf, "open_sessions", lambda p: 0), mock.patch("builtins.print") as out:
            r.plan()
        printed = [a[0] for a, _ in out.call_args_list if a]
        self.assertIn("  queued: 1. A", printed)


class TestLearnOnce(DecisionCase):
    # covers: bug 5 (a call's own "Learn this first" option is not shown twice)
    def test_learn_once(self):
        repo = self.make_repo("lo", ONE)
        self.commit(repo)
        self.ntfy.replies = ["{id} 1"]
        self.steps([ask("DECISION NEEDED: Which one?\nOPTION: A\nOPTION: B\nOPTION: Learn this first\n"), TICK_A, DONE_A])
        r = self.wf("lo", "-y", "--max-wait", "1", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual(rec["decisions"][0]["options"], ["A", "B", "learn this first"])


class TestAutoNotQueued(DecisionCase):
    # covers: bug 6 (a feature tagged auto without a ticked (spec) box says why it is not queued)
    def test_warning(self):
        self.make_repo("nq", "# Scope: x\n**Autopilot:** allowed\n### 1. Fix things · auto\n"
                             "- [x] Decide it: `/architect x`\n- [ ] `/debug x`\n")
        r = self.wf("nq")
        self.assertIn("warning: 1. Fix things: tagged auto, not queued: needs a ticked (spec) box", r.stdout)


class TestVerifyRetry(GitRepo):
    # covers: retry line under the PR #77 leftovers (try again on a verify FAIL: develop runs the build step first,
    # told what verify found, then verify again; a FAIL: debug retry stays as it was)
    def test_build_first(self):
        self.put("docs/scope/scope.md", "# Scope: x\n### 1. A · auto\n- [x] (spec)\n- [x] Build it: `/develop a`\n"
                                        "- [ ] `/check verify a`\n")
        [f] = run.repo_features(str(self.repo), "docs/scope")[1]
        self.assertEqual(run.build_command(f, "AC-3 missing"),
                         "/develop a -- the last /check verify found specced code missing or not applied:\nAC-3 missing")
        r = run.Run.__new__(run.Run)
        r.c, r.args = SimpleNamespace(path=str(self.repo), name="x", scope_dir="docs/scope"), SimpleNamespace()
        r.record, r.again, r.answers, r.repo, r.head0 = {"features": []}, set(), {}, {}, {}
        r.branch, r.folder, r.app, r.allow_once = "work", None, None, []
        r.branch_off = r.take_case = lambda *a: "try again"
        r.apply_case = lambda d, opt, f: f
        calls = []
        r.loop = lambda kind, box, command, *a: calls.append((kind, command.split("\n")[0]))
        outcomes = []
        for d in ({"case": "verify_failed", "build": True, "detail": "AC-3 missing", "box_text": None},
                  {"case": "verify_failed", "detail": "2 debug attempts made", "box_text": None}):
            # A resumed feature reuses its entry (spec 0011 AC-18), so each retry gets a fresh record.
            r.record = {"features": []}
            r.run_feature(f, d)
            outcomes += [e["outcome"] for e in r.record["features"]]
        self.assertEqual(outcomes, [None, None])
        self.assertEqual(calls, [("debug", "/develop a -- the last /check verify found specced code missing or not "
                                           "applied:"), ("box", "/check verify a")])


class TestVerifyRetryRun(NeverStopCase):
    # covers: retry line (a FAIL: develop question carries the build flag; try again runs /develop, then verify)
    def test_try_again_builds(self):
        self.make_repo("c", "# Scope: x\n**Autopilot:** allowed\n### 1. A · in-progress · auto\n- [x] (spec)\n"
                            "- [x] Build it: `/develop a`\n- [ ] Verify it: `/check verify a`\n")
        self.reply("{id} 1")
        self.steps([{"tick": False, "json": {"result": "AC-3 is not built\nVERIFY FAIL: develop"}}, {"tick": False},
                    {"json": {"result": "CAN FAIL CHECKED: 1"}}])
        self.wf("c", "-y", "--max-wait", "0.01", mode="fast")
        self.assertEqual(self.argv(2)["argv"][1].split("\n")[0],
                         "/develop a -- the last /check verify found specced code missing or not applied:")
        self.assertIn("AC-3 is not built", self.argv(2)["argv"][1])
        self.assertEqual(self.argv(3)["argv"][1], "/check verify a")


if __name__ == "__main__":
    unittest.main()
