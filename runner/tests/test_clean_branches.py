"""Spec 0051: clean branches, PRs and commits. The self merge of a small, low risk, green PR, the merge now path, the
cleanup after a merge, the plan's docs PR, the settings check, size and age warnings and the allow list."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pr  # noqa: E402
import report  # noqa: E402
import run  # noqa: E402
import test_pr  # noqa: E402
from test_run import WF, RunCase  # noqa: E402

SHA = "a" * 40
# The PR fake, plus pr ready, the rulesets read, and a merge that lands the head's tree on its base like a squash.
FAKE_GH = test_pr.FAKE_GH.replace('if a[:2] == ["pr", "merge"]:\n', '''if a[:2] == ["pr", "merge"] and cfg.get("land"):
    import subprocess
    sha = a[a.index("--match-head-commit") + 1]
    o = cfg["land"]
    tree = subprocess.run(["git", "--git-dir", o, "rev-parse", sha + "^{tree}"], capture_output=True, text=True).stdout.strip()
    new = subprocess.run(["git", "--git-dir", o, "commit-tree", tree, "-p", "refs/heads/work", "-m", "squash"],
                         capture_output=True, text=True, env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x",
                                                              "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}).stdout.strip()
    subprocess.run(["git", "--git-dir", o, "update-ref", "refs/heads/work", new], check=True)
    say("")
if a[:2] == ["pr", "merge"]:
''', 1).replace('if a[:2] == ["pr", "edit"]:', 'if a[:2] == ["pr", "ready"]:\n    say("")\nif a[:2] == ["pr", "edit"]:', 1).replace(
    '    p = a[1]\n', '    p = a[1]\n    if p.endswith("/rulesets"):\n        say(cfg.get("rulesets", []))\n', 1)
SCOPE = """# Scope: x
**Autopilot:** allowed

### 1. A · auto
Spec [0001](../specs/0001-a/index.md)
- [x] (spec)
- [x] `/develop a`
- [x] `/check verify a`
- [x] `/test a`
"""
SUITE = "- suite: python3 -c pass\n"
GOOD = {"squashMergeAllowed": True, "mergeCommitAllowed": False, "rebaseMergeAllowed": False, "deleteBranchOnMerge": True}
RULES = [{"name": "main only through a PR", "enforcement": "active", "target": "branch"}]


class R(test_pr.FakeRun):
    """FakeRun with what the merge code reads: answers, gh, a run folder, the suite stand in and question extras."""
    def __init__(self, repo, start, gh, folder):
        super().__init__(repo, start)
        self.answers = {"branches": "per spec", "push": "draft pr"}
        self.gh, self.folder, self.run_id = gh, folder, "run-1"
        self.suites, self.extras, self.suite_code = [], [], 0
        self.repo["origin_url"] = test_pr.ORIGIN
        self.feature_named = lambda name: None

    def clean_suite(self, tree, suite, rev=None):
        self.suites.append((tree, suite, rev))
        return self.suite_code, ["ok"]

    def pr_ask(self, rec, case, detail, options=None, **extra):
        self.asked.append((case, detail))
        self.extras.append(extra)

    def entry_for(self, d):
        pass


class Case(test_pr.PrCase):
    def setUp(self):
        super().setUp()
        self.fake("gh", FAKE_GH)
        (self.repo / "docs" / "scope" / "scope.md").write_text(SCOPE)
        (self.repo / "AGENTS.md").write_text(test_pr.ANSWERS + SUITE)
        self.git("commit", "-qam", "plan")
        self.git("push", "-q", "origin", "work")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/work")
        (self.tmp / ".claude" / "private" / "pr.json").write_text(json.dumps({"acme/widgets": {"auto_merge": True}}))
        env = mock.patch.dict(os.environ, {"HOME": str(self.tmp), "FAKE_DIR": str(self.fakes),
                                           "XDG_STATE_HOME": str(self.state), "GIT_AUTHOR_NAME": "t",
                                           "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
                                           "GIT_COMMITTER_EMAIL": "t@example.invalid"})
        env.start()
        self.addCleanup(env.stop)
        folder = self.tmp / "runfolder"
        folder.mkdir()
        self.r = R(self.repo, "work", str(self.bin / "gh"), str(folder))

    def branch(self, files=None, name="feat/0001-a", push=True):
        """feat/0001-a off work with files {path: text} committed, pushed; its record (draft PR #7) saved."""
        base = self.git("rev-parse", "work")
        self.git("switch", "-qc", name)
        for path, text in (files or {"a.txt": "a\n"}).items():
            p = self.repo / path
            p.parent.mkdir(parents=True, exist_ok=True)
            if text is None:
                p.unlink()
            else:
                p.write_text(text)
        self.git("add", "-A")
        self.git("commit", "-qm", "feat: A (spec 0001)")
        head = self.git("rev-parse", "HEAD")
        if push:
            self.git("push", "-q", "origin", name)
        self.git("switch", "-q", "work")
        rec = {"repo": str(self.repo), "feature": "1. A", "spec": "0001", "branch": name, "base": "work",
               "base_sha": base, "stacked_on": None, "pr": "https://github.com/acme/widgets/pull/7", "number": 7,
               "state": "draft", "seen": [], "rounds": 0, "pushed_sha": head if push else None}
        self.r.q["prs"] = [rec]
        return rec, head

    def views(self, head, draft=True, checks=(), mergeable="MERGEABLE", **cfg):
        v = {"state": "OPEN", "isDraft": draft, "headRefOid": head, "mergeable": mergeable,
             "statusCheckRollup": list(checks), "reviewDecision": "REVIEW_REQUIRED", "url": "u"}
        self.gh({"views": [v, v, {**v, "state": "MERGED"}], "methods": GOOD, "rulesets": RULES, **cfg})

    def merges(self):
        return [c for c in self.gh_calls() if c[:2] == ["pr", "merge"]]


class TestAllowList(unittest.TestCase):
    MERGE = ["pr", "merge", "7", "--repo", "o/r", "--squash", "--delete-branch", "--match-head-commit", SHA]
    READY = ["pr", "ready", "7", "--repo", "o/r"]
    CREATE = ["pr", "create", "--repo", "o/r", "--base", "main", "--head", "docs/plan-20261015-0101", "--title",
              "docs(scope): plan updates 20261015-0101", "--body-file", "/tmp/wf-plan-x1.md"]

    # covers: AC-9 (the squash merge with --delete-branch and pr ready only with green, from merge_green and land_plan;
    # any other caller raises; --admin and --auto never; spec 0031's merge entry unchanged)
    def test_green_only(self):
        for args in (self.MERGE, self.READY):
            self.assertTrue(pr.allowed(args, green=True), args)
            for kw in ({}, {"merging": True}, {"plan": True}, {"posting": True}):
                with self.subTest(args=args[:2], kw=kw), self.assertRaises(pr.Refused):
                    pr.gh("/bin/false", *args, **kw)
        for bad in ([*self.MERGE, "--admin"], [*self.MERGE, "--auto"], [*self.MERGE[:5], "--admin", *self.MERGE[6:]],
                    [*self.MERGE[:5], "--merge", *self.MERGE[6:]], [*self.MERGE[:8], "HEAD"], [*self.READY, "--auto"],
                    ["pr", "ready", "x7", "--repo", "o/r"], [*self.MERGE[:5], "--auto", *self.MERGE[6:]]):
            with self.subTest(bad), self.assertRaises(pr.Refused):
                pr.gh("/bin/false", *bad, green=True)
        # Spec 0031's 8 item merge is still merge() only.
        old = ["pr", "merge", "7", "--repo", "o/r", "--squash", "--match-head-commit", SHA]
        self.assertTrue(pr.allowed(old, merging=True))
        self.assertFalse(pr.allowed(old, green=True))

    # covers: AC-9 (the docs PR create without --draft only with plan, only to a docs/plan-<stamp> head; the rulesets
    # GET of AC-10 and nothing else on that path)
    def test_plan_create_and_rulesets(self):
        self.assertTrue(pr.allowed(self.CREATE, plan=True))
        for kw in ({}, {"green": True}, {"merging": True}):
            with self.subTest(kw), self.assertRaises(pr.Refused):
                pr.gh("/bin/false", *self.CREATE, **kw)
        for bad in ([*self.CREATE, "--draft"], [*self.CREATE[:7], "feat/x", *self.CREATE[8:]],
                    [*self.CREATE[:11], "b.md"], [*self.CREATE, "--auto"]):
            with self.subTest(bad), self.assertRaises(pr.Refused):
                pr.gh("/bin/false", *bad, plan=True)
        self.assertTrue(pr.allowed(["api", "repos/o/r/rulesets"]))
        for bad in (["api", "-X", "POST", "repos/o/r/rulesets"], ["api", "repos/o/r/rulesets", "--method", "PUT"],
                    ["api", "repos/o/r/rulesets/1"]):
            with self.subTest(bad), self.assertRaises(pr.Refused):
                pr.gh("/bin/false", *bad, green=True)

    # covers: security review (parser differential): gh reads a "-" leading word anywhere as a flag, so every value
    # slot of the new entries refuses one, and a flag given twice refuses
    def test_value_slots(self):
        for args, kw in ((self.MERGE, {"green": True}), (self.READY, {"green": True}), (self.CREATE, {"plan": True})):
            self.assertTrue(pr.allowed(args, **kw))
            for i, x in enumerate(args):
                if i < 2 or x.startswith("--"):
                    continue
                for bad in ("--admin", "-F", "--auto=true", "-o/r"):
                    with self.subTest(args=args[:2], slot=i, bad=bad), self.assertRaises(pr.Refused):
                        pr.gh("/bin/false", *args[:i], bad, *args[i + 1:], **kw)
            for i, x in enumerate(args):
                if x.startswith("--"):
                    with self.subTest(args=args[:2], twice=x), self.assertRaises(pr.Refused):
                        pr.gh("/bin/false", *args[:i + 2], x, *args[i + 1:], **kw)


class TestPrivateSwitch(RunCase):
    # covers: AC-1 (the auto_merge switch lives where no call can write: ~/.claude/private is in SECRETS and a real
    # call's deny arguments cover ~/.claude/private/pr.json, in the Edit rules and the sandbox's denyWrite)
    def test_denied(self):
        self.assertIn("~/.claude/private", run.SECRETS)
        private = self.tmp / ".claude" / "private"
        private.mkdir(parents=True)
        (private / "pr.json").write_text("{}")
        (self.repo / "x.txt").write_text("x\n")
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@x", "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", "b"],
                       check=True, capture_output=True)
        self.steps([{"tick": False}])
        r = subprocess.run([sys.executable, str(WF), "run", "demo", "-y", "--max-calls", "1", "--max-wait", "0.0001"],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, env=self.env, timeout=60)
        self.assertTrue((self.fakes / "argv-1.json").exists(), r.stdout + r.stderr)
        a = self.argv(1)["argv"]
        rules = a[a.index("--disallowedTools") + 1].split(",")
        fs = json.loads(a[a.index("--settings") + 1])["sandbox"]["filesystem"]["denyWrite"]
        self.assertIn(str(private), fs)
        for rule in run.path_rules("Edit", str(private)):
            self.assertIn(rule, rules)
        # The folder rule is what covers pr.json inside it.
        self.assertIn(f"Edit(/{private}/**)", rules)


class TestSmallSafe(Case):
    def check(self, files):
        _, head = self.branch(files, push=False)
        return pr.small_safe(self.r, None, "origin/work", head)

    # covers: AC-3 (a small change with none of the rules hit is small and low risk)
    def test_small(self):
        self.assertEqual(self.check({"a.txt": "a\n", "src/b.py": "def b():\n    return 1\n"}), (True, []))

    # covers: AC-3 (RISK_PATHS, whole path, case folded; the runner's own files and the scope folder)
    def test_risk_paths(self):
        for path in ("runner/pr.py", "src/Auth/login.py", "AGENTS.md", "pkg/AGENTS.md", ".github/workflows/ci.yml",
                     "docs/scope/scope.md", "config/.env.local", "db/Migrations/1.sql"):
            with self.subTest(path):
                self.setUp()
                ok, reasons = self.check({path: "x\n"})
                self.assertFalse(ok)
                self.assertEqual(reasons, [f"touches {path}"])

    # covers: AC-3 (over 200 lines or over 10 files is not small)
    def test_size(self):
        self.assertEqual(self.check({"a.txt": "x\n" * 201}), (False, ["201 lines"]))
        self.setUp()
        self.assertEqual(self.check({f"f{i}.txt": "x\n" for i in range(11)}), (False, ["11 files"]))

    # covers: AC-3 (a deleted test file or an added skip; a removed top level def, flag or env key)
    def test_tests_and_contracts(self):
        self.branch({"tests/test_x.py": "X = 1\n", "src/m.py": "def run_step():\n    pass\n",
                     "cli.py": 'p.add_argument("--max-calls")\nos.environ.get("WF_KEY")\n'}, name="seed")
        self.git("merge", "-q", "seed")
        self.git("push", "-q", "origin", "work")
        for files, why in (({"tests/test_x.py": None}, "deletes or skips a test"),
                           ({"t_test.py": "@unittest.skip('no')\n"}, "deletes or skips a test"),
                           ({"src/m.py": "def other():\n    pass\n"}, "removes def run_step"),
                           ({"cli.py": 'os.environ.get("WF_KEY")\n'}, "removes flag --max-calls"),
                           ({"cli.py": 'p.add_argument("--max-calls")\n'}, "removes env WF_KEY")):
            with self.subTest(why=why, files=files):
                got = self.check(files)
                self.git("branch", "-qD", "feat/0001-a")
                self.assertEqual(got, (False, [why]))
        # A def kept under the same name (a changed signature) is not removed.
        self.assertEqual(self.check({"src/m.py": "def run_step(x):\n    pass\n"}), (True, []))


class TestGreen(Case):
    def setUp(self):
        super().setUp()
        self.rec, self.head = self.branch()
        self.views(self.head)

    # covers: AC-4 (green: plan boxes ticked in the main checkout, main's suite on a tree of head, the scans, the
    # PR's checks SUCCESS, NEUTRAL or SKIPPED)
    def test_green(self):
        self.views(self.head, checks=[{"name": "ci", "conclusion": "SUCCESS"}, {"context": "x", "state": "SUCCESS"},
                                      {"name": "n", "conclusion": "NEUTRAL"}, {"name": "s", "conclusion": "SKIPPED"}])
        why = []
        self.assertTrue(pr.green(self.r, self.rec, self.head, why), why)
        self.assertEqual(self.r.suites, [(str(self.repo), "python3 -c pass", self.head)])

    # covers: AC-4 (the suite command is origin/<default>'s, never the branch's AGENTS.md, even with the branch
    # checked out)
    def test_suite_from_main(self):
        self.git("switch", "-q", "feat/0001-a")
        (self.repo / "AGENTS.md").write_text(test_pr.ANSWERS + "- suite: true\n")
        self.git("commit", "-qam", "trivial suite")
        self.rec["pushed_sha"] = self.head = self.git("rev-parse", "HEAD")
        self.git("push", "-q", "origin", "feat/0001-a")
        self.assertTrue(pr.green(self.r, self.rec, self.head))
        self.assertEqual([s for _, s, _ in self.r.suites], ["python3 -c pass"])

    # covers: AC-4 (not green: no suite answer on origin, a red suite, a box unticked or skipped, a failing or pending
    # check)
    def test_not_green(self):
        cases = []
        def no_suite():
            self.git("switch", "-q", "work")
            (self.repo / "AGENTS.md").write_text(test_pr.ANSWERS)
            self.git("commit", "-qam", "no suite")
            self.git("push", "-q", "origin", "work")
        cases.append((no_suite, "no suite answer on origin/work"))
        cases.append((lambda: setattr(self.r, "suite_code", 1), "main's suite failed: ok"))
        for box in ("- [x] `/test a`", "- [x] `/check verify a`"):
            cases.append((lambda box=box: (self.repo / "docs" / "scope" / "scope.md").write_text(
                SCOPE.replace(box, box.replace("[x]", "[ ]"))), "verify and test not ticked in the plan"))
        cases.append((lambda: (self.repo / "docs" / "scope" / "scope.md").write_text(
            SCOPE.replace("- [x] `/test a`", "- [x] `/test a` · skipped")), "verify and test not ticked in the plan"))
        cases.append((lambda: self.views(self.head, checks=[{"name": "ci", "conclusion": "FAILURE"}]), "check ci: failure"))
        cases.append((lambda: self.views(self.head, checks=[{"name": "ci", "status": "IN_PROGRESS", "conclusion": ""}]),
                      "check ci: pending"))
        for change, want in cases:
            with self.subTest(want):
                self.setUp()
                change()
                why = []
                self.assertFalse(pr.green(self.r, self.rec, self.head, why))
                self.assertEqual(why, [want])


class TestMergeGreen(Case):
    # covers: AC-5 (small, low risk and green: gh pr ready for the draft, then the one squash merge with
    # --delete-branch at the tested head; state merged, the report line, AC-7 cleanup deletes the local branch)
    def test_self_merge(self):
        rec, head = self.branch()
        self.views(head)
        self.assertTrue(pr.merge_green(self.r, rec))
        calls = self.gh_calls()
        self.assertIn(["pr", "ready", "7", "--repo", "acme/widgets"], calls)
        self.assertEqual(self.merges(), [["pr", "merge", "7", "--repo", "acme/widgets", "--squash", "--delete-branch",
                                          "--match-head-commit", head]])
        self.assertLess(calls.index(["pr", "ready", "7", "--repo", "acme/widgets"]), calls.index(self.merges()[0]))
        self.assertEqual(rec["state"], "merged")
        self.assertIn("merged: 1. A: PR #7 (small and low risk)", self.r.notes)
        self.assertNotIn("feat/0001-a", self.git("branch", "--list"))

    # covers: AC-5 (the PR's head on GitHub must be the tested head, the state OPEN and mergeable MERGEABLE;
    # UNKNOWN is read again, at most 3 times; any other failure is a note and nothing merges)
    def test_view_refuses(self):
        rec, head = self.branch()
        for view, want in (({"headRefOid": "b" * 40}, "head bbbbbbb"), ({"state": "CLOSED"}, "closed"),
                           ({"mergeable": "CONFLICTING"}, "conflicting"), ({"mergeable": "UNKNOWN"}, "unknown")):
            with self.subTest(view):
                (self.fakes / "gh-views").unlink(missing_ok=True)
                (self.fakes / "gh-argv.jsonl").unlink(missing_ok=True)
                self.r.notes.clear()
                v = {"state": "OPEN", "isDraft": True, "headRefOid": head, "mergeable": "MERGEABLE",
                     "statusCheckRollup": []}
                self.gh({"views": [v, {**v, **view}], "methods": GOOD})
                with mock.patch.object(pr, "MERGEABLE_WAIT", 0):
                    self.assertIsNone(pr.merge_green(self.r, rec))
                self.assertEqual(self.merges(), [])
                self.assertEqual(rec["state"], "draft")
                self.assertEqual(len(self.r.notes), 1)
                self.assertIn(want, self.r.notes[0])
                if view.get("mergeable") == "UNKNOWN":
                    self.assertEqual(len([c for c in self.gh_calls() if c[:2] == ["pr", "view"]]), 1 + 3)

    # covers: AC-8 (green but not small and low risk: stays a draft, the report line, the merge_ready question with the
    # head it names, stored as asked_head)
    def test_needs_review(self):
        rec, head = self.branch({"runner/x.py": "x = 1\n"})
        self.views(head)
        pr.merge_green(self.r, rec)
        self.assertEqual(self.merges(), [])
        self.assertNotIn(["pr", "ready", "7", "--repo", "acme/widgets"], self.gh_calls())
        self.assertIn("next: run /review on PR #7 (touches runner/x.py), then answer merge now", self.r.notes)
        self.assertEqual(self.r.asked, [("merge_ready", f"PR #7 passed its checks but needs your review (touches "
                                                        f"runner/x.py). Merge it now? (head {head[:7]})")])
        self.assertEqual(self.r.extras[-1]["asked_head"], head)
        self.assertEqual(rec["asked_head"], head)

    # covers: AC-6 (a branch without origin/<default> gets it by a plain merge, never a rebase; then a fast forward
    # push and pushed_sha updated; the merged head is what is tested and merged)
    def test_up_to_date(self):
        rec, old = self.branch()
        (self.repo / "other.txt").write_text("main moved\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "main moves")
        self.git("push", "-q", "origin", "work")
        main = self.git("rev-parse", "work")
        v = {"state": "OPEN", "isDraft": False, "mergeable": "MERGEABLE", "statusCheckRollup": []}
        # GitHub shows the head after the update.
        self.gh({"views": [{**v, "headRefOid": "pending"}], "methods": GOOD})
        with mock.patch.object(pr, "mergeable", lambda r, rec, name: ({**v, "headRefOid": pr.tip(r, rec["branch"])}, None)):
            self.assertTrue(pr.merge_green(self.r, rec))
        new = self.merges()[0][-1]
        self.assertEqual(self.git("rev-parse", f"{new}^1"), old)
        self.assertEqual(self.git("rev-parse", f"{new}^2"), main)
        self.assertEqual(self.git("rev-parse", "feat/0001-a", repo=self.origin), new)
        self.assertEqual(rec["pushed_sha"], new)
        self.assertEqual(self.r.suites[-1][2], new)

    # covers: AC-6 (a clash aborts the merge and asks merge_conflict; nothing is pushed or merged), AC-13 (its row)
    def test_conflict(self):
        rec, old = self.branch()
        (self.repo / "a.txt").write_text("other\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "clash")
        self.git("push", "-q", "origin", "work")
        self.views(old)
        self.assertIsNone(pr.merge_green(self.r, rec))
        self.assertEqual([c for c, _ in self.r.asked], ["merge_conflict"])
        self.assertEqual(run.CASES["merge_conflict"][1], ("leave it for you", "try again at the next run"))
        self.assertEqual(self.merges(), [])
        self.assertEqual(self.git("rev-parse", "feat/0001-a", repo=self.origin), old)
        self.assertEqual(self.git("worktree", "list").count("\n"), 0)

    # covers: AC-5 (in an AC-1 repo publish opens the draft PR as before, then tries the self merge at once)
    def test_publish_merges(self):
        rec, head = self.branch(push=False)
        rec["state"] = "local"
        self.views(head)
        pr.publish(self.r, rec)
        self.assertEqual(self.git("rev-parse", "feat/0001-a", repo=self.origin), head)
        self.assertEqual(self.merges()[0][-1], head)
        self.assertEqual(rec["state"], "merged")

    # covers: AC-2 (an old record with combined: true is never published or merged)
    def test_combined(self):
        rec, head = self.branch()
        rec.update(combined=True, state="local")
        self.views(head)
        self.assertIsNone(pr.merge_green(self.r, rec))
        pr.publish(self.r, rec)
        (self.tmp / ".claude" / "private" / "pr.json").write_text(json.dumps({"acme/widgets": {"merge": True}}))
        pr.merge(self.r, rec)
        self.assertEqual([c for c in self.gh_calls() if c[:2] in (["pr", "merge"], ["pr", "create"], ["pr", "ready"])], [])


class TestMergeNow(Case):
    def ask(self, files=None):
        rec, head = self.branch(files or {"runner/x.py": "x = 1\n"})
        self.views(head)
        pr.merge_green(self.r, rec)
        [extra] = self.r.extras
        d = {"id": "abcd", "repo": rec["repo"], "feature": rec["feature"], "case": "merge_ready",
             "options": list(run.CASES["merge_ready"][1]), "answer": None, "pr": True, **extra}
        self.r.q["decisions"] = [d]
        (self.fakes / "gh-views").unlink()
        return rec, head, d

    # covers: AC-8 (merge now, exactly, from you: merged through merge_green at the asked head, green judged again,
    # small_safe not asked)
    def test_merge_now(self):
        rec, head, d = self.ask()
        d.update(answer="merge now", source="keyboard")
        pr.answer(self.r, d)
        self.assertEqual(self.merges(), [["pr", "merge", "7", "--repo", "acme/widgets", "--squash", "--delete-branch",
                                          "--match-head-commit", head]])
        self.assertEqual(len(self.r.suites), 2)
        self.assertIn("merged: 1. A: PR #7 (your merge now)", self.r.notes)

    # covers: AC-8 (a reply that is not an option, "later", or merge now from ntfy without a code merges nothing)
    def test_no_merge(self):
        for answer, extra in (("merge it", {"source": "keyboard"}), ("yes", {"source": "keyboard"}),
                              ("later", {"source": "keyboard"}), ("merge now", {})):
            with self.subTest(answer, **extra):
                self.setUp()
                rec, head, d = self.ask()
                d.update(answer=answer, **extra)
                pr.answer(self.r, d)
                self.assertEqual(self.merges(), [])
                self.assertEqual(rec["state"], "draft")

    # covers: AC-8 (a head that moved since the question asks again naming the new head; nothing merges)
    def test_head_moved(self):
        rec, head, d = self.ask()
        self.git("switch", "-q", "feat/0001-a")
        (self.repo / "runner" / "x.py").write_text("x = 2\n")
        self.git("commit", "-qam", "fix: more")
        new = self.git("rev-parse", "HEAD")
        self.git("push", "-q", "origin", "feat/0001-a")
        self.git("switch", "-q", "work")
        rec["pushed_sha"] = new
        self.r.asked.clear()
        d.update(answer="merge now", source="keyboard")
        pr.answer(self.r, d)
        self.assertEqual(self.merges(), [])
        [(case, detail)] = self.r.asked
        self.assertEqual(case, "merge_ready")
        self.assertIn(f"(head {new[:7]})", detail)
        self.assertEqual(self.r.extras[-1]["asked_head"], new)


class TestCleanup(Case):
    # covers: AC-7 (after a merge: prune, the clean worktree removed, the local branch deleted when its tip is the PR's
    # head)
    def test_merged(self):
        rec, head = self.branch()
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp)}):
            tree = run.tree_path(str(self.repo), rec["branch"])
        self.git("worktree", "add", "-q", tree, rec["branch"])
        rec.update(tree=tree, state="merged")
        self.gh({"view": {"state": "MERGED", "headRefOid": head}})
        self.assertEqual(pr.cleanup(self.r, rec), [])
        self.assertFalse(os.path.exists(tree))
        self.assertNotIn("feat/0001-a", self.git("branch", "--list"))

    # covers: AC-7 (a local tip with commits after the PR's head keeps the branch with a note; a dirty worktree stays)
    def test_kept(self):
        rec, head = self.branch()
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp)}):
            tree = run.tree_path(str(self.repo), rec["branch"])
        self.git("worktree", "add", "-q", tree, rec["branch"])
        Path(tree, "b.txt").write_text("more\n")
        self.git("add", "-A", repo=tree)
        self.git("commit", "-qm", "after the PR", repo=tree)
        rec.update(tree=tree, state="merged")
        self.gh({"view": {"state": "MERGED", "headRefOid": head}})
        Path(tree, "dirty.txt").write_text("x\n")
        self.assertEqual(pr.cleanup(self.r, rec), [f"left: {tree}: uncommitted changes",
                                                   "kept: feat/0001-a: commits after the PR"])
        self.assertTrue(os.path.isdir(tree))
        os.remove(os.path.join(tree, "dirty.txt"))
        self.r.notes.clear()
        self.assertEqual(pr.cleanup(self.r, rec), ["kept: feat/0001-a: commits after the PR"])
        self.assertIn("feat/0001-a", self.git("branch", "--list"))

    # covers: AC-7 (a closed PR's remote branch is deleted; the local one too when its tip is the PR head)
    def test_closed(self):
        rec, head = self.branch()
        rec["state"] = "closed"
        self.gh({"view": {"state": "CLOSED", "headRefOid": head}})
        self.assertIn("feat/0001-a", self.git("branch", "--list", repo=self.origin))
        self.assertEqual(pr.cleanup(self.r, rec), [])
        self.assertNotIn("feat/0001-a", self.git("branch", "--list", repo=self.origin))
        self.assertNotIn("feat/0001-a", self.git("branch", "--list"))

    # covers: AC-7 (a poll that finds the PR merged on GitHub cleans up)
    def test_poll(self):
        rec, head = self.branch()
        rec["state"] = "ready"
        self.gh({"view": {"state": "MERGED", "headRefOid": head, "isDraft": False}})
        pr.poll_one(self.r, rec)
        self.assertEqual(rec["state"], "merged")
        self.assertNotIn("feat/0001-a", self.git("branch", "--list"))


class TestLandPlan(Case):
    def plan_commit(self, path="docs/scope/scope.md", text=SCOPE + "\n- [x] more\n"):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        self.git("add", "-A")
        self.git("commit", "-qm", "docs(scope): 1. A")
        return self.git("rev-parse", "HEAD")

    # covers: AC-15 (plan only commits ahead of origin: pushed to docs/plan-<stamp>, a PR without --draft, the squash
    # merge at HEAD; then reset --keep to origin, whose plan is the same)
    def test_lands(self):
        head = self.plan_commit()
        self.gh({"land": str(self.origin)})
        self.assertTrue(pr.land_plan(self.r))
        [create] = [c for c in self.gh_calls() if c[:2] == ["pr", "create"]]
        self.assertNotIn("--draft", create)
        self.assertRegex(create[create.index("--head") + 1], r"^docs/plan-\d{8}-\d{4}$")
        self.assertEqual(self.merges(), [["pr", "merge", "7", "--repo", "acme/widgets", "--squash", "--delete-branch",
                                          "--match-head-commit", head]])
        self.assertEqual(self.git("rev-parse", "work"), self.git("rev-parse", "work", repo=self.origin))
        self.assertEqual(self.git("status", "--porcelain"), "")

    # covers: AC-15 (a commit touching a path outside the scope folder: nothing pushed, no PR, a note)
    def test_outside(self):
        self.plan_commit()
        self.plan_commit("src/code.py", "x = 1\n")
        before = self.git("rev-parse", "HEAD")
        self.assertIsNone(pr.land_plan(self.r))
        self.assertEqual(self.gh_calls(), [])
        self.assertEqual(self.r.notes, ["plan not landed: src/code.py is outside docs/scope"])
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertNotIn("docs/plan", self.git("branch", "--list", "-a", repo=self.origin))

    # covers: AC-15 (no commits ahead does nothing; origin's plan differs after the merge: the local commits stay)
    def test_nothing_and_differs(self):
        self.assertIsNone(pr.land_plan(self.r))
        self.assertEqual(self.gh_calls(), [])
        head = self.plan_commit()
        pr.land_plan(self.r)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.r.notes, ["plan landed in PR #7; origin's plan differs, the local commits stay"])


class TestLandPlanIsolated(Case):
    plan_commit = TestLandPlan.plan_commit

    # covers: security review (module shadowing): land_plan's names scan runs the checker with python -I, so a
    # PYTHONPATH holding a planted module cannot make a private name in the plan commits pass
    def test_planted_module(self):
        planted = self.tmp / "planted"
        planted.mkdir()
        (planted / "subprocess.py").write_text("import sys\nsys.exit(0)\n")
        self.plan_commit(text=SCOPE + "\nmade for Zorblex\n")
        self.gh({"land": str(self.origin)})
        with mock.patch.dict(os.environ, {"PYTHONPATH": str(planted)}):
            self.assertIsNone(pr.land_plan(self.r))
        self.assertEqual(self.gh_calls(), [])
        self.assertTrue(self.r.notes[0].startswith("plan not landed: private_names:"), self.r.notes)


class TestSettings(Case):
    # covers: AC-10 (at a run's start an AC-1 repo's settings and ruleset are read; a difference is one report line and
    # the self merge is off for the run; matching settings leave it on)
    def test_check(self):
        self.gh({"methods": {**GOOD, "mergeCommitAllowed": True}, "rulesets": []})
        self.assertTrue(pr.auto(self.r))
        pr.settings_check(self.r)
        self.assertEqual(self.r.notes, ["settings: acme/widgets: mergeCommitAllowed is true; no active ruleset "
                                        "'main only through a PR'; run bin/repo-settings.sh acme/widgets"])
        self.assertFalse(pr.auto(self.r))
        self.setUp()
        self.gh({"methods": GOOD, "rulesets": RULES})
        self.assertEqual(pr.settings_check(self.r), [])
        self.assertTrue(pr.auto(self.r))
        # Without auto_merge in pr.json nothing is read.
        (self.tmp / ".claude" / "private" / "pr.json").write_text("{}")
        (self.fakes / "gh-argv.jsonl").unlink()
        self.assertIsNone(pr.settings_check(self.r))
        self.assertFalse(pr.auto(self.r))
        self.assertEqual(self.gh_calls(), [])


class TestRunEnds(Case):
    # covers: AC-10 (wf run checks the settings at its start: one report line), AC-15 (and lands the plan only commits
    # at its end through the docs PR)
    def test_run(self):
        (self.repo / "docs" / "scope" / "scope.md").write_text(SCOPE.replace("- [x] `/develop a`", "- [ ] `/develop a`"))
        self.git("commit", "-qam", "docs(scope): reopen")
        self.gh({"methods": {**GOOD, "deleteBranchOnMerge": False}, "rulesets": RULES, "land": str(self.origin)})
        self.steps([{"tick": False}])
        r = self.wf("prr", "-y", "--max-calls", "1")
        report_text = (self.state / "wf" / "report.txt").read_text()
        self.assertIn("settings: acme/widgets: deleteBranchOnMerge is false; run bin/repo-settings.sh acme/widgets",
                      report_text, r.stdout + r.stderr)
        self.assertIn("plan landed: PR #7, 1 commits", report_text, r.stdout + r.stderr)
        self.assertEqual(self.git("rev-parse", "work"), self.git("rev-parse", "work", repo=self.origin))


class TestWarnings(Case):
    # covers: AC-12 (over 400 lines and a first commit older than 2 days: the PR body and the built: line warn)
    def test_large_and_old(self):
        old = "@" + str(int(run.time.time()) - 3 * 86400 - 60)
        with mock.patch.dict(os.environ, {"GIT_COMMITTER_DATE": old, "GIT_AUTHOR_DATE": old}):
            rec, head = self.branch({"a.txt": "x\n" * 401}, push=False)
        want = ["large: 401 lines changed (over 400)", "old: branch 3 days (over 2)"]
        self.assertEqual(pr.warnings(self.r, rec), want)
        rec["state"] = "local"
        (self.tmp / ".claude" / "private" / "pr.json").write_text("{}")
        pr.publish(self.r, rec)
        [create] = [c for c in self.gh_calls() if c[:2] == ["pr", "create"]]
        body = Path(create[create.index("--body-file") + 1]).read_text()
        self.assertTrue(body.endswith("\n".join(want)), body)
        line = report.item_line({"kind": "built", "name": "prr", "feature": "1. A", "pr": {},
                                 "built": {"commits": 1, "files": 1, "warn": want}}, False, False, {})
        self.assertIn("1 files; large: 401 lines changed (over 400); old: branch 3 days (over 2); next:", line)
        self.setUp()
        rec, _ = self.branch()
        self.assertEqual(pr.warnings(self.r, rec), [])


BIN = Path(__file__).resolve().parent.parent.parent / "bin"
# gh for bin/repo-settings.sh: reads answer from settings.json by API path (the --jq result), writes are logged.
SETTINGS_GH = f"""#!{sys.executable}
import json, os, sys
d = os.environ["FAKE_DIR"]
a = sys.argv[1:]
open(os.path.join(d, "gh-argv.jsonl"), "a").write(json.dumps(a) + "\\n")
cfg = json.load(open(os.path.join(d, "settings.json")))
if "-X" in a:
    print("{{}}")
elif a[1].endswith("/rulesets"):
    print(cfg.get("id", ""))
elif "/rulesets/" in a[1]:
    print(cfg["shape"])
else:
    print(cfg["repo"][a[3].lstrip(".")])
"""
REPO_OK = {"allow_squash_merge": "true", "allow_merge_commit": "false", "allow_rebase_merge": "false",
           "delete_branch_on_merge": "true", "squash_merge_commit_title": "PR_TITLE",
           "squash_merge_commit_message": "PR_BODY"}
SHAPE_OK = "active branch ~DEFAULT_BRANCH deletion,non_fast_forward,pull_request 0 0"


class TestRepoSettings(RunCase):
    def script(self, *args, **cfg):
        (self.fakes / "settings.json").write_text(json.dumps({"repo": REPO_OK, "id": "5", "shape": SHAPE_OK, **cfg}))
        (self.fakes / "gh-argv.jsonl").unlink(missing_ok=True)
        self.fake("gh", SETTINGS_GH)
        return subprocess.run(["bash", str(BIN / "repo-settings.sh"), *args], capture_output=True, text=True,
                              env={**os.environ, "GH": str(self.bin / "gh"), "FAKE_DIR": str(self.fakes)}, timeout=60)

    def writes(self):
        p = self.fakes / "gh-argv.jsonl"
        return [x for x in map(json.loads, p.read_text().splitlines()) if "-X" in x] if p.exists() else []

    # covers: AC-10 (bad arguments refuse with exit 2; --check only reads: 0 when all match, 1 and one line per
    # difference otherwise, the ruleset's rules and bypass included)
    def test_check(self):
        for args in ((), ("--check",), ("o/r", "p/q"), ("--force", "o/r"), ("not a repo",)):
            with self.subTest(args):
                self.assertEqual(self.script(*args).returncode, 2)
        r = self.script("--check", "o/r")
        self.assertEqual((r.returncode, r.stdout), (0, ""), r.stderr)
        r = self.script("--check", "o/r", repo={**REPO_OK, "allow_merge_commit": "true"},
                        shape=SHAPE_OK.replace(" 0 0", " 0 1"))
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout.splitlines(), ["allow_merge_commit is true, wants false",
                                                 f"ruleset 'main only through a PR' is: {SHAPE_OK[:-1]}1; wants: {SHAPE_OK}"])
        r = self.script("--check", "o/r", id="")
        self.assertEqual((r.returncode, r.stdout), (1, "no ruleset named 'main only through a PR'\n"))
        self.assertEqual(self.writes(), [])

    # covers: AC-10 (without --check: the six settings by one PATCH, the ruleset created when missing, else updated)
    def test_set(self):
        r = self.script("o/r", id="")
        [patch, post] = self.writes()
        self.assertEqual(patch[:4], ["api", "-X", "PATCH", "repos/o/r"])
        self.assertEqual(patch[4:], ["-F", "allow_squash_merge=true", "-F", "allow_merge_commit=false", "-F",
                                     "allow_rebase_merge=false", "-F", "delete_branch_on_merge=true", "-f",
                                     "squash_merge_commit_title=PR_TITLE", "-f", "squash_merge_commit_message=PR_BODY"])
        self.assertEqual(post, ["api", "-X", "POST", "repos/o/r/rulesets", "--input", "-"])
        self.assertEqual(r.returncode, 1, "the fake still has no ruleset, so the closing check says so")
        r = self.script("o/r")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.writes()[1], ["api", "-X", "PUT", "repos/o/r/rulesets/5", "--input", "-"])


class TestDocsPr(Case):
    def script(self, *args):
        return subprocess.run(["bash", str(BIN / "docs-pr.sh"), *args], cwd=self.repo, capture_output=True, text=True,
                              env={**os.environ, "GH": str(self.bin / "gh")}, timeout=60)

    def commit(self, path, text="x\n"):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        self.git("add", "-A")
        self.git("commit", "-qm", f"docs: {path}")

    # covers: AC-11 (refusals, exit 2 and one line: tracked changes, nothing ahead of origin, a commit outside docs/,
    # not on the default branch; nothing is pushed)
    def test_refusals(self):
        r = self.script()
        self.assertEqual((r.returncode, r.stderr), (2, "docs-pr: no commit ahead of origin/work\n"))
        self.commit("docs/notes.md")
        (self.repo / "docs" / "notes.md").write_text("changed\n")
        r = self.script()
        self.assertEqual((r.returncode, r.stderr), (2, "docs-pr: the tree has tracked changes\n"))
        self.git("checkout", "--", "docs/notes.md")
        self.commit("src/x.py")
        r = self.script("notes")
        self.assertEqual((r.returncode, r.stderr), (2, "docs-pr: a commit touches src/x.py, outside docs/\n"))
        self.git("switch", "-qc", "other")
        self.assertEqual(self.script().stderr, "docs-pr: not on work\n")
        self.assertEqual(self.gh_calls(), [])
        self.assertNotIn("docs/", self.git("branch", "--list", "-a", repo=self.origin))

    # covers: AC-11 (docs only commits: a docs/<date>-<slug> branch pushed, the PR, the squash merge at HEAD, then
    # reset to origin whose docs match; the URL printed)
    def test_lands(self):
        self.commit("docs/notes.md")
        head = self.git("rev-parse", "HEAD")
        self.gh({"land": str(self.origin)})
        r = self.script("notes")
        self.assertEqual((r.returncode, r.stdout), (0, "https://github.com/acme/widgets/pull/7\n"), r.stderr)
        [merge] = [c for c in self.gh_calls() if c[:2] == ["pr", "merge"]]
        self.assertEqual(merge[3:], ["--squash", "--delete-branch", "--match-head-commit", head])
        self.assertEqual(self.git("rev-parse", "work"), self.git("rev-parse", "work", repo=self.origin))
        self.assertEqual(self.git("symbolic-ref", "--short", "HEAD"), "work")

    # covers: security review (module shadowing): the scanners run from the script repo's origin copy with python
    # -I, so an untracked module planted next to the tree's checker does not turn a private name hit into a pass
    def test_planted_checker(self):
        import shutil
        top = BIN.parent
        (self.repo / "bin").mkdir()
        shutil.copy(BIN / "docs-pr.sh", self.repo / "bin" / "docs-pr.sh")
        (self.repo / "scripts").mkdir()
        shutil.copy(top / "scripts" / "private-names.py", self.repo / "scripts" / "private-names.py")
        shutil.copytree(top / "runner", self.repo / "runner", ignore=shutil.ignore_patterns("tests", "__pycache__", "e2e"))
        self.git("add", "-A")
        self.git("commit", "-qm", "tools")
        self.git("push", "-q", "origin", "work")
        self.commit("docs/notes.md", "made for Zorblex\n")
        # Untracked, so the tree check does not see it; python's script folder would.
        (self.repo / "scripts" / "subprocess.py").write_text("import sys\nsys.exit(0)\n")
        self.gh({"land": str(self.origin)})
        r = subprocess.run(["bash", str(self.repo / "bin" / "docs-pr.sh")], cwd=self.repo, capture_output=True,
                           text=True, env={**os.environ, "GH": str(self.bin / "gh")}, timeout=60)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("docs-pr: private names scan hit", r.stderr)
        self.assertEqual(self.gh_calls(), [])


if __name__ == "__main__":
    unittest.main()
