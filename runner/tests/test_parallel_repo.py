"""Spec 0027: several features of one repo at once, each in its own worktree on its own spec branch."""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pr  # noqa: E402
import run  # noqa: E402
from test_park import GIT_ID  # noqa: E402
from test_pr import FakeRun  # noqa: E402
from test_run import RunCase, summary  # noqa: E402

SCOPE = "# Scope: x\n**Autopilot:** allowed\n" + "".join(
    f"\n### {n}. {x} · auto\nSpec [000{n}](../specs/000{n}-{x.lower()}/index.md)\n- [x] (spec)\n- [ ] `/develop {x.lower()}`\n"
    for n, x in ((1, "A"), (2, "B"), (3, "C")))
SPEC = "# 000{n}\n\n**Status**: Accepted\n**Paths:** {paths}\n\n## What you're agreeing to\n- {x}.\n"
ANSWERS = "## Standing answers\n- branches: per spec\n- parallel: 2\n"


def step(x, sleep=2, extra_file=None):
    files = [[f"{x}.txt", f"{x}\n"]] + ([[extra_file, "drift\n"]] if extra_file else [])
    return [{"tick": False, "sleep": sleep, "write_file": files,
             "run": [["git", "add", "-A"], ["git", "commit", "-qm", f"wip {x}"]],
             "edit": [[f"- [ ] `/develop {x}`", f"- [x] `/develop {x}`"]]},
            {"tick": False, "edit": [[f"### {'ABC'.index(x.upper()) + 1}. {x.upper()} · auto",
                                      f"### {'ABC'.index(x.upper()) + 1}. {x.upper()} · done · auto"]]}]


def at(iso):
    return datetime.datetime.fromisoformat(iso)


class RepoCase(RunCase):
    def setUp(self):
        super().setUp()
        self.env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
                        GIT_COMMITTER_EMAIL="t@example.invalid")
        self.repo = self.make_repo("par", SCOPE)
        # AGENTS.md and the scope file are on two Paths lines and still never count (AC-5).
        for n, x, paths in ((1, "a", "`a.txt`, `AGENTS.md`"), (2, "b", "`b.txt`, `docs/scope/scope.md`, `AGENTS.md`"),
                            (3, "c", getattr(self, "c_paths", "`a.txt`"))):
            d = self.repo / "docs" / "specs" / f"000{n}-{x}"
            d.mkdir(parents=True)
            (d / "index.md").write_text(SPEC.format(n=n, paths=paths, x=x))
        (self.repo / "AGENTS.md").write_text(ANSWERS)
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        (self.tmp / "config" / "wf" / "allowed.json").write_text(json.dumps([str(self.repo)]))
        self.trees = self.tmp / ".local" / "share" / "wf-trees" / f"par-{run.hashlib.sha1(str(self.repo).encode()).hexdigest()[:6]}"

    def git(self, *args, cwd=None):
        r = subprocess.run(["git", *GIT_ID, "-C", str(cwd or self.repo), *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def records(self):
        return {p.name: json.loads((p / "run.json").read_text()) for p in sorted((self.state / "wf" / "runs").iterdir())}

    def by_feature(self):
        out = {}
        for rec in self.records().values():
            for e in rec["features"]:
                out[e["feature"]] = (rec, e)
        return out


class TestAnswer(unittest.TestCase):
    # covers: AC-1 (parallel 1 to 4, only with branches: per spec)
    def test_values(self):
        d = Path(tempfile.mkdtemp())
        c = types.SimpleNamespace(path=str(d), scope_dir="docs/scope")
        for text, want in ((ANSWERS, ({"branches": "per spec", "parallel": "2"}, None)),
                           ("## Standing answers\n- parallel: 2\n", (None, "AGENTS.md: parallel needs branches: per spec")),
                           ("## Standing answers\n- branches: per spec\n- parallel: 5\n",
                            (None, "AGENTS.md:3: 5 is not allowed for parallel"))):
            (d / "AGENTS.md").write_text(text)
            self.assertEqual(run.read_answers(c), want)


class TestPaths(unittest.TestCase):
    # covers: AC-5 (globs of the Paths line, shared files left out; overlap by fnmatch either way or a folder
    # prefix; no Paths overlaps everything), AC-4 (clashes lets two worktrees of one repo run unless they overlap or
    # share a port)
    def test_overlap(self):
        self.assertEqual(pr.overlap(["runner/run.py"], ["runner/*.py"]), "runner/run.py")
        self.assertEqual(pr.overlap(["runner/tests/"], ["runner/tests/test_x.py"]), "runner/tests/")
        self.assertIsNone(pr.overlap(["runner/run.py"], ["scripts/x.py"]))
        self.assertEqual(pr.overlap(None, ["a"]), "*")
        self.assertTrue(pr.shared("docs/scope/scope.md", "docs/scope"))
        self.assertTrue(pr.shared("docs/specs/0001-a/verify.md", "docs/scope"))
        self.assertFalse(pr.shared("docs/specs/0001-a/index.md", "docs/scope"))
        self.assertEqual(pr.hits(["x/y.py", "a.txt"], ["a.*"]), "a.txt")
        t = lambda g, port=None: {"tree": "/t", "key": "/r", "globs": g, "port": port, "path": "/t", "common": "/r/.git"}
        self.assertFalse(run.clashes(t(["a"]), t(["b"])))
        self.assertTrue(run.clashes(t(["a"]), t(["a"])))
        self.assertTrue(run.clashes(t(["a"], 80), t(["b"], 80)))
        self.assertTrue(run.clashes(t(None), t(["b"])))
        # Two plain repos sharing a common dir still never run together.
        self.assertTrue(run.clashes({"path": "/a", "common": "/g", "port": None}, {"path": "/b", "common": "/g", "port": None}))


class TestSameRepo(RepoCase):
    # covers: AC-2 (worktrees under wf-trees, the main checkout never switched), AC-3 (one child per feature, trusted
    # through the main checkout, records name the repo and the tree), AC-4 (2 at once, C waits for A), AC-5 (the
    # waits plan line), AC-7 (sibling Edit denies), AC-9 (rows named repo: feature)
    def test_three_features(self):
        self.steps({"feat-0001-a": step("a", sleep=4), "feat-0002-b": step("b"), "feat-0003-c": step("c", sleep=0)})
        r = self.wf("-y", "--jobs", "3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("  waits: 3. C: shares a.txt with 1. A\n", r.stdout)
        self.assertEqual((self.repo / ".git" / "HEAD").read_text(), "ref: refs/heads/work\n")
        s = summary(r.stdout)
        self.assertEqual([x.split(": exit")[0] for x in s], ["  par: 1. A", "  par: 2. B", "  par: 3. C"])
        feats = self.by_feature()
        (ra, ea), (rb, eb), (rc, ec) = feats["1. A"], feats["2. B"], feats["3. C"]
        ca, cb, cc = ra["calls"][0], rb["calls"][0], rc["calls"][0]
        end = lambda c: at(c["started"]) + datetime.timedelta(seconds=c["duration_s"])
        # Times are kept to the second: B's call began well before A's 4 second call ended.
        self.assertLess(at(cb["started"]) + datetime.timedelta(seconds=1), end(ca), "A and B ran side by side")
        self.assertGreaterEqual(at(rc["started"]), at(ra["ended"]), "C started after A's child ended")
        for e, rec, x in ((ea, ra, "a"), (eb, rb, "b"), (ec, rc, "c")):
            self.assertEqual(e["repo"], str(self.repo))
            self.assertEqual(e["tree"], str(self.trees / f"feat-000{'abc'.index(x) + 1}-{x}"))
            self.assertEqual(rec["repos"][0]["repo"], str(self.repo))
            self.assertEqual(e["outcome"], "feature_done")
        for n, x in ((1, "a"), (2, "b"), (3, "c")):
            changed = self.git("diff", "--name-only", f"work...feat/000{n}-{x}").split("\n")
            self.assertIn(f"{x}.txt", changed)
            self.assertFalse([f for f in changed if f.endswith(".txt") and f != f"{x}.txt"], changed)
        denied = json.loads((self.fakes / "feat-0001-a-argv-1.json").read_text())["argv"]
        rules = denied[denied.index("--disallowedTools") + 1].split(",")
        self.assertIn(f"Edit(/{self.repo}/**)", rules)
        self.assertIn(f"Edit(/{self.trees / 'feat-0002-b'}/**)", rules)
        self.assertNotIn(f"Edit(/{self.trees / 'feat-0001-a'}/**)", rules)
        # Security review: the sandbox denies the main checkout (carved around its .git, which commits need), every
        # sibling worktree, their admin folders and other spec branches' refs; its own stay writable.
        fs = json.loads(denied[denied.index("--settings") + 1])["sandbox"]["filesystem"]["denyWrite"]
        admin = self.repo / ".git" / "worktrees"
        self.assertIn(str(self.repo / "AGENTS.md"), fs)
        self.assertNotIn(str(self.repo), fs)
        self.assertIn(str(self.trees / "feat-0002-b"), fs)
        self.assertIn(str(admin / "feat-0002-b"), fs)
        self.assertNotIn(str(admin / "feat-0001-a"), fs)
        self.assertIn(str(self.repo / ".git" / "refs" / "heads" / "work"), fs)
        self.assertNotIn(str(self.repo / ".git" / "refs" / "heads" / "feat" / "0001-a"), fs)
        self.assertIn(f"Edit(/{admin / 'feat-0002-b'}/**)", rules)
        self.assertEqual(json.loads((self.state / "wf" / "active.json").read_text()), [])

    # covers: security review (spec 0025 with 0027): a worktree child's own pointer file changed after the parent
    # made the worktree, before the child started, asks guard_changed; its baseline is its own, never skipped
    def test_tree_baseline(self):
        b = self.trees / "feat-0002-b"
        first = step("a", sleep=0)
        first[0]["write_file"].append([str(b / ".git"), f"gitdir: {self.repo}/.git/worktrees/feat-0002-b\n\n"])
        self.steps({"feat-0001-a": first, "feat-0002-b": step("b", sleep=0), "feat-0003-c": step("c", sleep=0)})
        r = self.wf("-y", "--jobs", "1")
        q = json.loads((self.state / "wf" / "queue.json").read_text())
        [d] = [d for d in q["decisions"] if d.get("reason") == "guard_changed"]
        self.assertIn(f"{b}/.git changed after the plan, before this repo started", d["question"], r.stdout)
        self.assertFalse((self.fakes / "feat-0002-b-argv-1.json").exists(), "B made no call")

    # covers: AC-6 (A's call writes into B's Paths while B runs: A asks paths_overlap, wait recommended; B goes on)
    def test_drift(self):
        self.steps({"feat-0001-a": step("a", sleep=1.5, extra_file="b.txt"), "feat-0002-b": step("b", sleep=4),
                    "feat-0003-c": step("c", sleep=0)})
        r = self.wf("-y", "--jobs", "2")
        q = json.loads((self.state / "wf" / "queue.json").read_text())
        [d] = [d for d in q["decisions"] if d.get("case") == "paths_overlap"]
        self.assertEqual((d["feature"], d["options"][0], d["other"], d["tree"]),
                         ("1. A", "wait for the other, then go on", "2. B", str(self.trees / "feat-0001-a")), r.stdout)
        self.assertEqual(self.by_feature()["2. B"][1]["outcome"], "feature_done")

    # covers: security review: when the parent cannot build a worktree's guard (an unreadable config.worktree) and a
    # call repairs it before that child starts, the child's own files the plan never hashed still ask
    def test_tree_guard_unbuilt(self):
        b = self.trees / "feat-0002-b"
        self.git("worktree", "add", "-q", "-b", "feat/0002-b", str(b))
        bad = self.repo / ".git" / "worktrees" / "feat-0002-b" / "config.worktree"
        bad.write_text("[broken\n")
        first = step("a", sleep=0)
        first[0]["rm"] = [str(bad)]
        self.steps({"feat-0001-a": first, "feat-0002-b": step("b", sleep=0), "feat-0003-c": step("c", sleep=0)})
        r = self.wf("-y", "--jobs", "1")
        q = json.loads((self.state / "wf" / "queue.json").read_text())
        [d] = [d for d in q["decisions"] if d.get("reason") == "guard_changed"]
        self.assertIn(f"{b}/.git changed after the plan, before this repo started", d["question"], r.stdout)
        self.assertFalse((self.fakes / "feat-0002-b-argv-1.json").exists(), "B made no call")

    # covers: security review (AC-7 siblings as written and resolved)
    def test_siblings_resolved(self):
        link = self.tmp / "link"
        link.symlink_to(self.repo)
        tree = self.trees / "feat-x"
        self.git("worktree", "add", "-q", "-b", "feat/x", str(tree))
        git = str(self.repo / ".git")
        trees, parts = run.tree_siblings(str(tree), str(link), git, f"{git}/worktrees/feat-x")
        self.assertEqual(trees, [str(link), str(self.repo)])
        self.assertIn(f"{git}/refs/heads/work", parts)
        self.assertNotIn(f"{git}/refs/heads/feat/x", parts)
        c = types.SimpleNamespace(path=str(tree), key=str(link))
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.tmp / "state")}):
            rules = run.Run.sibling_denies(types.SimpleNamespace(repo={"tree": str(tree)}, c=c))
        self.assertIn(f"Edit(/{link}/**)", rules)
        self.assertIn(f"Edit(/{self.repo}/**)", rules)
        self.assertFalse([x for x in rules if "feat-x" in x], rules)

    # covers: AC-3 (a worktree of a trusted repo is trusted; one elsewhere is not)
    def test_trust(self):
        tree = self.trees / "feat-x"
        self.git("worktree", "add", "-q", "-b", "feat/x", str(tree))
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp), "XDG_CONFIG_HOME": str(self.tmp / "config")}):
            self.assertEqual(run.tree_main(str(tree)), str(self.repo))
            self.assertIsNone(run.untrusted(str(tree)))
            other = self.tmp / "elsewhere"
            self.git("worktree", "add", "-q", "-b", "feat/y", str(other))
            self.assertIsNone(run.tree_main(str(other)))
            self.assertIsNotNone(run.untrusted(str(other)))


class TestLimit(RepoCase):
    c_paths = "`c.txt`"

    def test_limit(self):
        """AC-4: with parallel: 2 a third disjoint feature starts only once one of the first two ended."""
        self.steps({"feat-0001-a": step("a"), "feat-0002-b": step("b"), "feat-0003-c": step("c", sleep=0)})
        r = self.wf("-y", "--jobs", "3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("waits: 3. C", r.stdout)
        feats = self.by_feature()
        first_end = min(at(feats["1. A"][0]["ended"]), at(feats["2. B"][0]["ended"]))
        self.assertGreaterEqual(at(feats["3. C"][0]["started"]), first_end)


class TestCleanup(RepoCase):
    # covers: AC-8 (a merged PR's clean worktree is removed, never with --force; a dirty one is kept with a line;
    # a feature that built nothing loses its worktree)
    def test_remove(self):
        r = FakeRun(self.repo, "work")
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp)}):
            tree = run.tree_path(str(self.repo), "feat/0001-a")
            self.git("worktree", "add", "-q", "-b", "feat/0001-a", tree)
            base = self.git("rev-parse", "work")
            rec = {"repo": str(self.repo), "feature": "1. A", "spec": "0001", "branch": "feat/0001-a", "base": "work",
                   "base_sha": base, "stacked_on": None, "pr": None, "number": 7, "state": "merged", "seen": [],
                   "rounds": 0, "pushed_sha": None, "tree": tree}
            r.q["prs"] = [rec]
            Path(tree, "x.txt").write_text("dirty\n")
            self.assertEqual(pr.remove_tree(r, rec), f"kept {tree}: uncommitted changes")
            self.assertTrue(os.path.isdir(tree))
            os.remove(os.path.join(tree, "x.txt"))
            self.assertIsNone(pr.remove_tree(r, rec))
            self.assertFalse(os.path.exists(tree))
            self.assertNotIn(tree, self.git("worktree", "list"))
            # Built nothing (still building, no commit past its base): removed too.
            tree2 = run.tree_path(str(self.repo), "feat/0002-b")
            self.git("worktree", "add", "-q", "-b", "feat/0002-b", tree2)
            rec2 = {**rec, "feature": "2. B", "branch": "feat/0002-b", "state": "building", "tree": tree2}
            r.q["prs"] = [rec2]
            self.assertIsNone(pr.remove_tree(r, rec2))
            self.assertFalse(os.path.exists(tree2))


if __name__ == "__main__":
    unittest.main()
