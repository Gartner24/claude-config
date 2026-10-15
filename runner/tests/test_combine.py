"""Spec 0043 AC-3: a parallel run's finished feature branches combined into one branch at the end."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import unittest  # noqa: E402
from test_parallel_repo import ANSWERS, RepoCase  # noqa: E402


def feature(x, shared=None):
    """One build call writing <x>.txt (and shared.txt when given), committing, ticking; then the sync call."""
    files = [[f"{x}.txt", f"{x}\n"]] + ([["shared.txt", shared]] if shared else [])
    return [{"tick": False, "sleep": 0, "write_file": files,
             "run": [["git", "add", "-A"], ["git", "commit", "-qm", f"wip {x}"]],
             "edit": [[f"- [ ] `/develop {x}`", f"- [x] `/develop {x}`"]]},
            {"tick": False, "edit": [[f"### {'ABC'.index(x.upper()) + 1}. {x.upper()} · auto",
                                      f"### {'ABC'.index(x.upper()) + 1}. {x.upper()} · done · auto"]]}]


# A jail stand in that runs the command it was given (the real bwrap needs namespaces), noting its argv.
BWRAP = f"""#!{sys.executable}
import json, os, subprocess, sys
a = sys.argv[1:]
json.dump(a, open(os.path.join(os.environ["FAKE_DIR"], "bwrap-argv.json"), "w"))
i = a.index("--chdir")
sys.exit(subprocess.run(a[i + 2:], cwd=a[i + 1]).returncode)
"""


class TestCombine(RepoCase):
    def setUp(self):
        super().setUp()
        self.fake("bwrap", BWRAP)
    def answers(self, suite=None):
        (self.repo / "AGENTS.md").write_text(ANSWERS + (f"- suite: {suite}\n" if suite else ""))
        self.git("commit", "-q", "--allow-empty", "-am", "answers")

    def combined(self):
        [b] = [b for b in self.git("branch", "--format=%(refname:short)").split("\n") if b.startswith("wf/combined-")]
        return b

    def show(self, branch, path):
        return self.git("show", f"{branch}:{path}")

    # covers: AC-3 (every finished branch merged into a new combined branch cut from the start branch; the start
    # branch and the feature branches are untouched)
    def test_clean(self):
        self.answers()
        self.steps({"feat-0001-a": feature("a"), "feat-0002-b": feature("b"), "feat-0003-c": feature("c")})
        r = self.wf("-y", "--jobs", "3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        b = self.combined()
        self.assertIn("combined: " + b + ": 3 merged, 0 left out", r.stdout)
        for x in "abc":
            self.assertEqual(self.show(b, f"{x}.txt"), x)
        self.assertEqual(self.git("rev-parse", "work"), self.git("merge-base", "work", b))
        self.assertEqual(self.git("log", "--format=%s", "-1", "feat/0001-a").startswith("feat:"), True)

    # covers: AC-3 (a same lines clash goes to one resolve call in the combined worktree; the suite, from the main
    # checkout's answers, runs jailed and passes; the merge is committed)
    def test_resolved(self):
        self.answers("{ read a; read c; } < shared.txt && [ \"$a$c\" = AC ]")
        (self.fakes / "combine.json").write_text(json.dumps({"write": [["shared.txt", "A\nC\n"]]}))
        self.steps({"feat-0001-a": feature("a", "A\n"), "feat-0002-b": feature("b"), "feat-0003-c": feature("c", "C\n")})
        r = self.wf("-y", "--jobs", "3")
        logs = "".join(p.read_text() for p in (self.state / "wf" / "runs").glob("wf-combined-*/log.txt"))
        self.assertEqual(r.returncode, 0, logs)
        b = self.combined()
        self.assertIn(": 3 merged, 0 left out", r.stdout)
        self.assertEqual(self.show(b, "shared.txt"), "A\nC")
        jail = json.loads((self.fakes / "bwrap-argv.json").read_text())
        self.assertIn("--unshare-net", jail)
        self.assertEqual(jail[-1], "{ read a; read c; } < shared.txt && [ \"$a$c\" = AC ]")
        [call] = [json.loads(p.read_text()) for p in self.fakes.glob("combine-argv-*.json")]
        self.assertIn("shared.txt", " ".join(call["argv"]))
        self.assertTrue(call["cwd"].endswith(b.replace("/", "-")), call["cwd"])

    # covers: AC-3 (markers left: that branch is aborted and left out with a combine_conflict question; the others
    # stay merged), and a red suite leaves it out too
    def test_left_out(self):
        for suite, combine in ((None, {"write": []}), ("false", {"write": [["shared.txt", "A\nC\n"]]})):
            with self.subTest(suite=suite):
                self.setUp()
                self.answers(suite)
                (self.fakes / "combine.json").write_text(json.dumps(combine))
                self.steps({"feat-0001-a": feature("a", "A\n"), "feat-0002-b": feature("b"),
                            "feat-0003-c": feature("c", "C\n")})
                r = self.wf("-y", "--jobs", "3")
                b = self.combined()
                logs = "".join(p.read_text() for p in (self.state / "wf" / "runs").glob("wf-combined-*/log.txt"))
                self.assertIn(": 2 merged, 1 left out", r.stdout + logs)
                self.assertEqual(self.show(b, "shared.txt"), "A")
                self.assertEqual(self.git("status", "--porcelain", cwd=self.trees / b.replace("/", "-")), "")
                q = json.loads((self.state / "wf" / "queue.json").read_text())
                [d] = [d for d in q["decisions"] if d.get("case") == "combine_conflict"]
                self.assertEqual(d["feature"], "3. C")
                self.assertIn("feat/0003-c left out of " + b, d["question"] + json.dumps(d))


    # covers: security review (validator bypass): a resolve call that also stages another file, or commits the merge
    # itself, leaves that branch out
    def test_resolve_contained(self):
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        resolved = ["shared.txt", "A\nC\n"]
        # (files the call writes, commands it runs, a file git ignores in the repo, why it is left out)
        cases = (([resolved, ["other.txt", "x\n"]], [["git", "add", "other.txt"]], None, "staged or added other files"),
                 ([resolved], [["git", "add", "shared.txt"], [*git, "commit", "-qm", "self"]], None,
                  "committed, merged or switched"),
                 # Security review: an edit hidden behind an index flag, or a file git ignores, is caught too.
                 ([resolved, ["a.txt", "evil\n"]], [["git", "update-index", "--assume-unchanged", "a.txt"]], None,
                  "hid an edit from git or added an ignored file"),
                 ([resolved, ["planted.txt", "x\n"]], [], "planted.txt", "hid an edit from git or added an ignored file"))
        for writes, run_, ignored, why in cases:
            with self.subTest(why=why, run=run_):
                self.setUp()
                self.answers()
                if ignored:
                    (self.repo / ".gitignore").write_text(ignored + "\n")
                    self.git("add", ".gitignore")
                    self.git("commit", "-qm", "ignore")
                (self.fakes / "combine.json").write_text(json.dumps({"write": writes, "run": run_}))
                self.steps({"feat-0001-a": feature("a", "A\n"), "feat-0002-b": feature("b"),
                            "feat-0003-c": feature("c", "C\n")})
                self.wf("-y", "--jobs", "3")
                logs = "".join(p.read_text() for p in (self.state / "wf" / "runs").glob("wf-combined-*/log.txt"))
                self.assertIn(f"combine: left out feat/0003-c: the resolve call {why}", logs)


class TestResolveUnit(unittest.TestCase):
    # covers: security review (fail open): unreadable standing answers never let a resolved clash be committed
    def test_unreadable_answers(self):
        import types
        import run
        r = run.Run.__new__(run.Run)
        r.c = types.SimpleNamespace(path="/nowhere", scope_dir="docs/scope")
        why = r.resolve("feat/x", ["a.txt"], run.Stop("answers_unreadable", "AGENTS.md:3: bad"), [])
        self.assertEqual(why, "the main checkout's standing answers cannot be read: AGENTS.md:3: bad")


    # covers: security review (validator bypass): the suite runs in a clean copy of the index, so an ignored file the
    # call edited in place never reaches it; the copy is gone afterwards
    def test_clean_suite(self):
        import subprocess
        import tempfile
        import types
        import run
        repo = Path(tempfile.mkdtemp()) / "t"
        repo.mkdir()
        g = lambda *a: subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                      check=True, capture_output=True)
        g("init", "-q")
        (repo / ".gitignore").write_text("cache.txt\n")
        (repo / "kept.txt").write_text("k\n")
        g("add", "-A")
        g("commit", "-qm", "base")
        (repo / "cache.txt").write_text("edited by the call\n")
        r = run.Run.__new__(run.Run)
        r.run_id = "t"
        seen = []
        r.jail_argv = lambda cmd, root: seen.append(root) or ["/bin/sh", "-c", cmd]
        run.wf.GIT = run.wf.GIT or "git"
        code, _ = r.clean_suite(str(repo), "test -e kept.txt && test ! -e cache.txt")
        self.assertEqual(code, 0)
        self.assertEqual(seen, [str(repo) + "-suite"])
        self.assertFalse(Path(seen[0]).exists())


if __name__ == "__main__":
    import unittest
    unittest.main()
