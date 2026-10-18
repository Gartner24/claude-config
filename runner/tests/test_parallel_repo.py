"""Spec 0027: several features of one repo at once, each in its own worktree on its own spec branch."""
import datetime
import io
import shutil
import json
import os
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pr  # noqa: E402
import run  # noqa: E402
import test_pr  # noqa: E402
from test_park import GIT_ID  # noqa: E402
from test_pr import FakeRun  # noqa: E402
from test_run import WF, RunCase, summary  # noqa: E402

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
    # covers: AC-1 (parallel 1 to 8, spec 0052 AC-1, only with branches: per spec)
    def test_values(self):
        d = Path(tempfile.mkdtemp())
        c = types.SimpleNamespace(path=str(d), scope_dir="docs/scope")
        for text, want in ((ANSWERS, ({"branches": "per spec", "parallel": "2"}, None)),
                           ("## Standing answers\n- parallel: 2\n", (None, "AGENTS.md: parallel needs branches: per spec")),
                           ("## Standing answers\n- branches: per spec\n- parallel: 8\n",
                            ({"branches": "per spec", "parallel": "8"}, None))):
            (d / "AGENTS.md").write_text(text)
            self.assertEqual(run.read_answers(c), want)
        for bad in ("9", "0", "08", "x", "\uff15", "4.0"):
            (d / "AGENTS.md").write_text(f"## Standing answers\n- branches: per spec\n- parallel: {bad}\n")
            self.assertEqual(run.read_answers(c), (None, f"AGENTS.md:3: {bad} is not allowed for parallel"), bad)


class TestPaths(unittest.TestCase):
    # covers: AC-5 (globs of the Paths line, shared files left out; overlap by fnmatch either way or a folder
    # prefix; no Paths overlaps everything), AC-4 (clashes lets two worktrees of one repo run unless they overlap or
    # share a port)
    def test_overlap(self):
        self.assertEqual(pr.overlap(["runner/run.py"], ["runner/*.py"]), "runner/run.py")
        self.assertEqual(pr.overlap(["runner/tests/"], ["runner/tests/test_x.py"]), "runner/tests/")
        self.assertIsNone(pr.overlap(["runner/run.py"], ["scripts/x.py"]))
        self.assertEqual(pr.overlap(None, ["a"]), "*")
        # Spec 0052 AC-5: `Paths: none` touches no code, so it meets nothing, not even a spec with no Paths line.
        self.assertIsNone(pr.overlap([], None))
        self.assertIsNone(pr.overlap(["a"], []))
        d = Path(tempfile.mkdtemp())
        (d / "docs" / "specs").mkdir(parents=True)
        lines = ["- [ ] Spec: [0001](../specs/0001-a.md)"]
        for paths, want in (("none", []), ("`src/x.py`, `docs/scope/scope.md`", ["src/x.py"]), ("", None)):
            (d / "docs" / "specs" / "0001-a.md").write_text(f"# 0001\n\n**Status**: Accepted\n**Paths:** {paths}\n")
            self.assertEqual(pr.globs(str(d), "docs/scope", lines), want, paths)
        self.assertTrue(pr.shared("docs/scope/scope.md", "docs/scope"))
        self.assertTrue(pr.shared("docs/specs/0001-a/verify.md", "docs/scope"))
        self.assertFalse(pr.shared("docs/specs/0001-a/index.md", "docs/scope"))
        self.assertEqual(pr.hits(["x/y.py", "a.txt"], ["a.*"]), "a.txt")
        t = lambda g, port=None: {"tree": "/t", "key": "/r", "globs": g, "port": port, "path": "/t", "common": "/r/.git"}
        self.assertFalse(run.clashes(t(["a"]), t(["b"])))
        # Spec 0043 AC-2: overlapping or missing Paths no longer keep two worktrees apart; a shared port still does.
        self.assertFalse(run.clashes(t(["a"]), t(["a"])))
        self.assertTrue(run.clashes(t(["a"], 80), t(["b"], 80)))
        self.assertFalse(run.clashes(t(None), t(["b"])))
        # Two plain repos sharing a common dir still never run together.
        self.assertTrue(run.clashes({"path": "/a", "common": "/g", "port": None}, {"path": "/b", "common": "/g", "port": None}))


class TestSameRepo(RepoCase):
    # covers: AC-2 (worktrees under wf-trees, the main checkout never switched), AC-3 (one child per feature, trusted
    # through the main checkout, records name the repo and the tree), AC-4 (2 at once; spec 0052 AC-5: C shares a.txt
    # with A, so it waits for A's child to exit and says so once), AC-7 (sibling Edit denies), AC-9 (rows named repo:
    # feature)
    def test_three_features(self):
        self.steps({"feat-0001-a": step("a", sleep=4), "feat-0002-b": step("b"), "feat-0003-c": step("c", sleep=0)})
        r = self.wf("-y", "--jobs", "3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([x for x in r.stdout.splitlines() if x.startswith("waits:")],
                         ["waits: 3. C: shares a.txt with 1. A"], r.stdout)
        self.assertEqual((self.repo / ".git" / "HEAD").read_text(), "ref: refs/heads/work\n")
        s = summary(r.stdout)
        # Spec 0051 AC-2: no combine child after the features, and no wf/combined-* branch; each keeps its own.
        self.assertEqual([x.split(": exit")[0] for x in s], ["  par: 1. A", "  par: 2. B", "  par: 3. C"])
        self.assertNotIn("wf/combined-", self.git("branch", "--format=%(refname:short)"))
        feats = self.by_feature()
        (ra, ea), (rb, eb), (rc, ec) = feats["1. A"], feats["2. B"], feats["3. C"]
        ca, cb, cc = ra["calls"][0], rb["calls"][0], rc["calls"][0]
        end = lambda c: at(c["started"]) + datetime.timedelta(seconds=c["duration_s"])
        # Times are kept to the second: B's call began well before A's 4 second call ended.
        self.assertLess(at(cb["started"]) + datetime.timedelta(seconds=1), end(ca), "A and B ran side by side")
        self.assertGreaterEqual(at(rc["started"]), end(ca) - datetime.timedelta(seconds=1), "C started before A ended")
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
        self.assertIn(f"Edit(/{self.repo / 'AGENTS.md'})", rules)
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
        # Security review (incomplete write guard): every sibling path is in both lists, as written and resolved.
        g = ra["repos"][0]["guard"]["siblings"]
        self.assertTrue(g)
        for p in g:
            self.assertIn(os.path.realpath(p), g)
            self.assertIn(p, fs)
            for rule in run.path_rules("Edit", p):
                self.assertIn(rule, rules)
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

    # covers: security review (stale state): a worktree added after a child's guard was built is in both deny lists
    # of that child's next call
    def test_new_tree_mid_run(self):
        extra = self.trees / "extra"
        first = step("a", sleep=0)
        first[0]["run"].append(["git", "worktree", "add", "-q", "-b", "extra", str(extra)])
        self.steps({"feat-0001-a": first, "feat-0002-b": step("b", sleep=0), "feat-0003-c": step("c", sleep=0)})
        r = self.wf("-y", "--jobs", "1")
        before = json.loads((self.fakes / "feat-0001-a-argv-1.json").read_text())["argv"]
        after = json.loads((self.fakes / "feat-0001-a-argv-2.json").read_text())["argv"]
        for argv, want in ((before, False), (after, True)):
            fs = json.loads(argv[argv.index("--settings") + 1])["sandbox"]["filesystem"]["denyWrite"]
            rules = argv[argv.index("--disallowedTools") + 1].split(",")
            self.assertEqual(str(extra) in fs, want, r.stdout)
            self.assertEqual(f"Edit(/{extra}/**)" in rules, want, r.stdout)

    # covers: spec 0043 AC-2 (A's call writes into B's Paths while B runs: a note, no question; both go on)
    def test_drift(self):
        self.steps({"feat-0001-a": step("a", sleep=1.5, extra_file="b.txt"), "feat-0002-b": step("b", sleep=4),
                    "feat-0003-c": step("c", sleep=0)})
        r = self.wf("-y", "--jobs", "2")
        q = json.loads((self.state / "wf" / "queue.json").read_text())
        self.assertEqual([d for d in q["decisions"] if d.get("case") == "paths_overlap"], [], r.stdout)
        ra, ea = self.by_feature()["1. A"]
        self.assertIn("1. A: b.txt is in the Paths of 2. B, which is building now", ra["notes"])
        self.assertEqual((ea["outcome"], self.by_feature()["2. B"][1]["outcome"]), ("feature_done", "feature_done"))

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
            # A worktree under wf-trees is trusted only while its main checkout is on the list.
            (self.tmp / "config" / "wf" / "allowed.json").write_text(json.dumps([]))
            self.assertIsNotNone(run.untrusted(str(tree)))


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


# The worktree child is a fresh wf.py, so the test wrapper's short poll gap never reaches it; this does.
SITE = f"""import sys
sys.path.insert(0, {str(WF.parent)!r})
import ntfy, pr
ntfy.RETRY_GAP = ntfy.POLL_EVERY = 0.05
pr.POLL_GAP = 0.05
"""


class TestRoundInTree(test_pr.PrCase):
    # covers: AC-8 (a review round of a parallel repo's PR runs in that feature's worktree, never the main checkout;
    # the merged PR's clean worktree is removed)
    def test_round_in_tree(self):
        (self.repo / "AGENTS.md").write_text(test_pr.ANSWERS + "- parallel: 2\n")
        self.git("commit", "-qam", "parallel")
        self.git("push", "-q", "origin", "work")
        site = self.tmp / "site"
        site.mkdir()
        (site / "sitecustomize.py").write_text(SITE)
        self.env["PYTHONPATH"] = str(site)
        test_pr.TestReview.ready(self)
        self.fake("claude", test_pr.REVIEW_CLAUDE.replace(
            'if prompt.startswith("Review comments on"):\n',
            'if prompt.startswith("Review comments on"):\n    open(os.path.join(d, "review-cwd.txt"), "w").write(os.getcwd())\n', 1))
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp)}):
            tree = run.tree_path(str(self.repo), "feat/0001-a")
        self.assertEqual(self.rec()["tree"], tree)
        before = self.git("rev-parse", "feat/0001-a", repo=self.origin)
        r = self.wf("prr", "-y", mode="pr")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertEqual((self.fakes / "review-cwd.txt").read_text(), tree)
        self.assertNotEqual(self.git("rev-parse", "feat/0001-a", repo=self.origin), before)
        self.assertEqual(self.rec()["state"], "merged")
        self.assertEqual((self.repo / ".git" / "HEAD").read_text(), "ref: refs/heads/work\n")
        self.assertNotIn(tree, self.git("worktree", "list"))


class TestDenyNotNarrowed(RunCase):
    # covers: security review (control regression): a plain single repo run's Edit denies and sandbox denyWrite
    # hold every entry they held at 779dfc6, before this release
    BASE = "779dfc6"

    def deny_lists(self, wf_py):
        shutil.rmtree(self.state, ignore_errors=True)
        # The fake counts its calls in this folder too.
        shutil.rmtree(self.fakes)
        self.fakes.mkdir()
        self.steps([{"tick": False}])
        r = subprocess.run([sys.executable, str(wf_py), "run", "demo", "-y", "--max-calls", "1", "--max-wait", "0.0001"],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, env=self.env, timeout=60)
        self.assertTrue((self.fakes / "argv-1.json").exists(), r.stdout + r.stderr)
        a = self.argv(1)["argv"]
        fs = json.loads(a[a.index("--settings") + 1])["sandbox"]["filesystem"]["denyWrite"]
        return set(a[a.index("--disallowedTools") + 1].split(",")), set(fs), r

    def test_against_base(self):
        top = WF.parent.parent
        if subprocess.run(["git", "-C", str(top), "cat-file", "-e", self.BASE + "^{commit}"],
                          capture_output=True).returncode:
            self.skipTest(f"{self.BASE} is not in this checkout")
        old = self.tmp / "old"
        old.mkdir()
        tar = subprocess.run(["git", "-C", str(top), "archive", self.BASE, "runner"], capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", str(old)], input=tar.stdout, check=True)
        (self.repo / "x.txt").write_text("x\n")
        subprocess.run(["git", *GIT_ID, "-C", str(self.repo), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", *GIT_ID, "-C", str(self.repo), "commit", "-qm", "base"], check=True, capture_output=True)
        old_rules, old_fs, r1 = self.deny_lists(old / "runner" / "wf.py")
        new_rules, new_fs, r2 = self.deny_lists(WF)
        self.assertGreater(len([x for x in old_rules if x.startswith("Edit(")]), 10, r1.stdout)
        self.assertGreater(len(old_fs), 5, r1.stdout)
        self.assertEqual(sorted(old_rules - new_rules), [], r2.stdout)
        self.assertEqual(sorted(old_fs - new_fs), [], r2.stdout)


def meminfo(path, gb):
    # Every field the brake could read, MemFree far from MemAvailable, so reading the wrong one shows.
    kb = int(gb * 1024 * 1024)
    path.write_text(f"MemTotal:       67108864 kB\nMemFree:          {kb * 4} kB\nMemAvailable:   {kb} kB\n"
                    "Buffers:          100000 kB\nCached:          2000000 kB\n")


def row(feature, globs, key="/r"):
    return {"tree": f"/t/{feature}", "key": key, "feature": feature, "globs": globs, "port": None,
            "path": f"/t/{feature}", "common": f"{key}/.git", "limit": 8}


class TestBrakes(unittest.TestCase):
    # covers: spec 0052 AC-2 (MemAvailable, not MemFree, under 4.5 GB holds), AC-3 (five hour use at 80 holds, a failed
    # read never brakes and says so once), AC-6 (the new child's share of the cores)
    def test_free_memory(self):
        d = Path(tempfile.mkdtemp())
        meminfo(d / "m", 4.0)
        self.assertAlmostEqual(run.free_gb(str(d / "m")), 4.0)
        self.assertIsNone(run.free_gb(str(d / "missing")))

    def test_brake(self):
        d = Path(tempfile.mkdtemp())
        r = types.SimpleNamespace()
        u = lambda used: {"five_hour": {"used": used, "resets_at": None}, "seven_day": {"used": 99.0, "resets_at": None}}
        with mock.patch.dict(os.environ, {"WF_MEMINFO": str(d / "m")}), mock.patch("usage.read", return_value=u(50.0)):
            meminfo(d / "m", 4.0)
            self.assertEqual(run.brake(r), ("memory", "4.0 GB free, needs 4.5"))
            meminfo(d / "m", 5.0)
            # A seven day use of 99 never brakes: there is no weekly brake.
            self.assertIsNone(run.brake(r))
        with mock.patch.dict(os.environ, {"WF_MEMINFO": str(d / "m")}), mock.patch("usage.read", return_value=u(85.0)):
            self.assertEqual(run.brake(r), ("5 hour use", "85%, needs under 80"))
        with mock.patch.dict(os.environ, {"WF_MEMINFO": str(d / "m")}), mock.patch("usage.read", return_value=u(80.0)):
            self.assertEqual(run.brake(r)[0], "5 hour use")
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"WF_MEMINFO": str(d / "m")}), \
                mock.patch("usage.read", return_value=(None, "usage service: 500")), mock.patch("sys.stdout", out):
            self.assertIsNone(run.brake(r))
            self.assertIsNone(run.brake(r))
        self.assertEqual(out.getvalue(), "usage unknown, not braking\n")

    def test_cores(self):
        with mock.patch("os.cpu_count", return_value=20):
            self.assertEqual(run.cores([]), 20)
            self.assertEqual(run.cores([{}] * 3), 5)
            self.assertEqual(run.cores([{}] * 4), 4)
            self.assertEqual(run.cores([{}] * 11), 2)
        with mock.patch("os.cpu_count", return_value=None):
            self.assertEqual(run.cores([{}]), 2)

    def test_fast_suite_workers(self):
        import fast
        with mock.patch.dict(os.environ, {"WF_CORES": "3"}):
            self.assertEqual(fast.workers(), 3)
        with mock.patch.dict(os.environ, {"WF_CORES": ""}), mock.patch("os.cpu_count", return_value=20):
            self.assertEqual(fast.workers(), 20)


class TestPick(unittest.TestCase):
    # covers: spec 0052 AC-5 (8 rows of one repo: an overlapping pair never runs together, no Paths runs alone,
    # `Paths: none` runs with anything, other repos are never tested for overlap)
    def test_eight(self):
        jobs = [row("p1", ["src/a.py"]), row("p2", ["src/*.py"]), row("nopaths", None), row("none", []),
                row("d1", ["d1/"]), row("d2", ["d2/"]), row("d3", ["d3/"]), row("d4", ["d4/"])]
        waiting, running, together = list(jobs), [], []
        # Start greedily, then end the oldest child, until every row ran.
        while waiting or running:
            j = run.pick(waiting, running)
            if j:
                waiting.remove(j)
                running.append(j)
                together.append({k["feature"] for k in running})
                continue
            running.pop(0)
        self.assertFalse([t for t in together if {"p1", "p2"} <= t], together)
        self.assertFalse([t for t in together if "nopaths" in t and t - {"nopaths", "none"}], together)
        self.assertTrue([t for t in together if "none" in t and len(t) > 2], together)
        self.assertEqual(run.shares(jobs[1], [jobs[0]]), "p2: shares src/*.py with p1")
        self.assertEqual(run.shares(jobs[0], [jobs[2]]), "p1: shares * with nopaths")
        self.assertIsNone(run.shares(jobs[3], [jobs[2]]))
        # Another repo's worktree with the same Paths is not this repo's sibling.
        self.assertIsNone(run.shares(row("q", ["src/a.py"], key="/other"), [jobs[0]]))


class TestGitRetry(unittest.TestCase):
    # covers: spec 0052 AC-7 (only a lock git refused to create is retried, 5 times, then it fails as before)
    def fake(self, errors):
        calls = []

        def go(argv, **kw):
            calls.append(argv)
            err = errors[len(calls) - 1] if len(calls) <= len(errors) else ""
            return subprocess.CompletedProcess(argv, 128 if err else 0, "", err)
        return calls, go

    def test_retry(self):
        import wf
        busy = "fatal: Unable to create '/r/.git/worktrees/a/index.lock': File exists."
        for errors, want_calls, want_code in (([busy, busy], 3, 0), (["error: cannot lock ref 'refs/heads/x'"], 1, 128),
                                              ([busy] * 9, 6, 128), (["fatal: not a git repository"], 1, 128)):
            calls, go = self.fake(errors)
            with mock.patch("subprocess.run", go), mock.patch("time.sleep") as nap:
                r = wf.git("/r", "commit", "-m", "x")
            self.assertEqual((len(calls), r.returncode), (want_calls, want_code), errors)
            self.assertEqual(nap.call_count, want_calls - 1)


class TestBrakeRun(RepoCase):
    # covers: spec 0052 AC-2, AC-3, AC-4 (a held start with no child running is tried again every POLL, says why once
    # per value, and starts once the line is cleared), AC-6 (each child and its calls get WF_CORES)
    def held(self, hold, clear, want):
        hold()
        p = self.start("-y")
        time.sleep(1.5)
        self.assertIsNone(p.poll())
        self.assertEqual(list(self.fakes.glob("*argv-*.json")), [])
        clear()
        out, err = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 0, out + err)
        lines = out.splitlines()
        waits = [x for x in lines if x.startswith("waits:") and "shares" not in x]
        self.assertEqual(waits, [want], out)
        first = next(i for i, x in enumerate(lines) if x.startswith("[par: "))
        self.assertLess(lines.index(want), first, out)
        return out

    def test_memory(self):
        m = Path(self.env["WF_MEMINFO"])
        self.steps({"feat-0001-a": step("a", sleep=3), "feat-0002-b": step("b"), "feat-0003-c": step("c", sleep=0)})
        self.held(lambda: meminfo(m, 4.0), lambda: meminfo(m, 5.0), "waits: memory 4.0 GB free, needs 4.5, 0 min so far")
        n = os.cpu_count() or 4
        env = lambda f: json.loads((self.fakes / f"{f}-argv-1.json").read_text())["env"]
        self.assertEqual(env("feat-0001-a")["WF_CORES"], str(max(2, n)))
        self.assertEqual(env("feat-0002-b")["WF_CORES"], str(max(2, n // 2)))

    def test_usage(self):
        cache = self.state / "wf" / "usage.json"
        cache.parent.mkdir(parents=True, exist_ok=True)

        def use(used):
            cache.write_text(json.dumps({"at_epoch": time.time(), "five_hour": {"used": used, "resets_at": None},
                                         "seven_day": {"used": 10, "resets_at": None}}))
        self.steps({"feat-0001-a": step("a", sleep=0), "feat-0002-b": step("b", sleep=0), "feat-0003-c": step("c", sleep=0)})
        out = self.held(lambda: use(85), lambda: use(50), "waits: 5 hour use 85%, needs under 80, 0 min so far")
        self.assertNotIn("usage unknown", out)


if __name__ == "__main__":
    unittest.main()
