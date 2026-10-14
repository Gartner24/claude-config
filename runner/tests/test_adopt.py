"""Spec 0031: your open PRs adopted into the review loop, watched until done, merged only on your tap."""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pr  # noqa: E402
import run  # noqa: E402
import test_pr  # noqa: E402
from test_pr import REVIEW_CLAUDE, FakeRun, PrCase  # noqa: E402

TEAM_SCOPE = "# Scope: x\n**Autopilot:** allowed\n\n### 1. A\n- [ ] `/develop a`\n"


class AdoptCase(PrCase):
    def setUp(self):
        super().setUp()
        # A team repo: no standing answers, nothing about PRs in the repo; the switch is only in pr.json.
        (self.repo / "AGENTS.md").write_text("# Agents\n")
        (self.repo / "docs" / "scope" / "scope.md").write_text(TEAM_SCOPE)
        (self.repo / "a.txt").write_text("a\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "team")
        self.git("push", "-q", "origin", "work")
        self.git("switch", "-qc", "fix-x")
        (self.repo / "a.txt").write_text("a\nx\n")
        self.git("commit", "-qam", "fix x")
        self.head = self.git("rev-parse", "HEAD")
        self.git("push", "-q", "origin", "fix-x")
        self.git("switch", "-q", "work")
        self.git("branch", "-qD", "fix-x")
        self.private({"acme/widgets": {"adopt": True}})

    def private(self, data):
        (self.tmp / ".claude" / "private" / "pr.json").write_text(json.dumps(data))

    def mine(self, **extra):
        return [{"number": 12, "title": "Fix x", "headRefName": "fix-x", "baseRefName": "work", "headRefOid": self.head,
                 "isDraft": False, "isCrossRepository": False, "url": "https://github.com/acme/widgets/pull/12", **extra},
                {"number": 13, "title": "On main", "headRefName": "main", "baseRefName": "work", "headRefOid": self.head,
                 "isDraft": False, "isCrossRepository": False, "url": "u13"},
                {"number": 14, "title": "Fork", "headRefName": "fork-y", "baseRefName": "work", "headRefOid": self.head,
                 "isDraft": False, "isCrossRepository": True, "url": "u14"}]


class TestAdoptRun(AdoptCase):
    # covers: AC-1 (pr.json alone opts a team repo in), AC-2 (your open PRs adopted at plan time, never main or a
    # fork; its plan line), AC-3 (the branch made from the PR head, the 0026 round: fix pushed, reply posted), AC-5
    # (watched until the PR merged, then the run ends)
    def test_adopt_and_round(self):
        self.fake("claude", REVIEW_CLAUDE)
        view = {"isDraft": False, "state": "OPEN", "headRefOid": self.head, "reviewDecision": "REVIEW_REQUIRED",
                "url": "u"}
        # Many polls past --max-wait (0.36 s) before it merges: the watch has no --max-wait cutoff.
        self.gh({"user": "me", "mine": self.mine(), "views": [view] * 25 + [{**view, "state": "MERGED"}],
                 "inline": [{"id": 11, "user": {"login": "alice"}, "author_association": "MEMBER", "path": "a.txt",
                             "line": 1, "body": "Add a newline.", "diff_hunk": "@@ +1 @@"}]})
        r = self.wf("prr", "-y", mode="pr")
        self.assertIn("  watching: PR #12: Fix x (ready)\n", r.stdout, r.stdout + r.stderr)
        lists = [c for c in self.gh_calls() if c[:2] == ["pr", "list"]]
        self.assertEqual(lists[0][lists[0].index("--author") + 1], "me")
        [rec] = self.queue()["prs"]
        self.assertEqual({k: rec[k] for k in ("feature", "branch", "base", "number", "adopted", "spec")},
                         {"feature": "PR #12: Fix x", "branch": "fix-x", "base": "work", "number": 12, "adopted": True,
                          "spec": None})
        self.assertEqual((rec["state"], rec["rounds"]), ("merged", 1),
                         r.stdout + (self.state / "wf" / "report.txt").read_text())
        after = self.git("rev-parse", "fix-x", repo=self.origin)
        self.assertEqual(self.git("rev-parse", f"{after}~1"), self.head)
        posts = [c for c in self.gh_calls() if c[:3] == ["api", "-X", "POST"]]
        self.assertEqual(posts, [["api", "-X", "POST", "repos/acme/widgets/pulls/12/comments/11/replies", "-f",
                                  f"body=Fixed in {after[:7]}. @alice"]])
        self.assertEqual((self.repo / ".git" / "HEAD").read_text(), "ref: refs/heads/work\n")

    # covers: AC-1 (without adopt: true nothing is read or adopted, and the run has nothing to do)
    def test_off(self):
        for value in (None, "true", 1):
            with self.subTest(value):
                self.private({"acme/widgets": {} if value is None else {"adopt": value}})
                self.gh({"user": "me", "mine": self.mine()})
                self.wf("prr", "-y")
                self.assertEqual(self.queue().get("prs", []), [])
                self.assertFalse(any(c[:2] == ["pr", "list"] for c in self.gh_calls()))


class TestAdoptUnit(AdoptCase):
    def fake_run(self):
        r = FakeRun(self.repo, "work")
        r.gh = str(self.bin / "gh")
        r.answers = {}
        r.ntfy = {"topic": "t", "block": []}
        return r

    def penv(self):
        return mock.patch.dict(os.environ, {"FAKE_DIR": str(self.fakes), "CLAUDE_CONFIG_DIR": str(self.tmp / ".claude")})

    # covers: AC-2 (a kept local record of wf's own takes your hand opened PR; a known number is never added twice)
    def test_local_record(self):
        r = self.fake_run()
        own = {"repo": run.key_of(r.c), "feature": "1. A", "spec": "0001", "branch": "fix-x", "base": "work",
               "base_sha": "b" * 40, "stacked_on": None, "pr": None, "number": None, "state": "local", "seen": [],
               "rounds": 0, "pushed_sha": None}
        r.q["prs"] = [own]
        self.gh({"user": "me", "mine": self.mine(isDraft=True)})
        with self.penv():
            pr.adopt(r)
            pr.adopt(r)
        self.assertEqual(len(r.q["prs"]), 1)
        self.assertEqual((own["number"], own["state"], own["pushed_sha"], own["feature"]), (12, "draft", self.head, "1. A"))

    # covers: AC-1 (only the boolean true adopts), AC-5 (a PR merged on GitHub withdraws its open merge question)
    def test_gate_and_withdraw(self):
        r = self.fake_run()
        self.gh({"user": "me", "mine": self.mine(), "view": {"state": "MERGED"}})
        with self.penv():
            self.private({"acme/widgets": {"adopt": "true"}})
            pr.adopt(r)
            self.assertEqual(r.q["prs"], [])
            self.private({"acme/widgets": {"adopt": True}})
            pr.adopt(r)
            [rec] = r.q["prs"]
            r.q["decisions"] = [{"id": "ab12", "repo": rec["repo"], "feature": rec["feature"], "pr": True,
                                 "case": "approved"}]
            pr.poll_one(r, rec)
        self.assertEqual((rec["state"], r.q["decisions"]), ("merged", []))

    # covers: AC-3 (a local branch ahead of the PR head is left alone and the round waits)
    def test_diverged(self):
        r = self.fake_run()
        self.git("branch", "fix-x", self.head)
        self.git("switch", "-q", "fix-x")
        (self.repo / "b.txt").write_text("mine\n")
        self.git("add", "b.txt")
        self.git("commit", "-qm", "local only")
        mine = self.git("rev-parse", "HEAD")
        self.git("switch", "-q", "work")
        rec = {"branch": "fix-x", "number": 12, "pushed_sha": self.head}
        self.assertFalse(pr.sync_branch(r, rec, self.head))
        self.assertEqual(self.git("rev-parse", "fix-x"), mine)
        self.assertEqual(r.notes, ["PR #12: the branch here differs from the PR on GitHub"])
        # Behind: fast forwarded.
        self.git("branch", "-f", "fix-x", f"{self.head}~1")
        self.assertTrue(pr.sync_branch(r, rec, self.head))
        self.assertEqual(self.git("rev-parse", "fix-x"), self.head)

    # covers: AC-8 (free text never merges; I merged it records it), AC-9 (a moved head goes back to ready, nothing
    # merged; a failed merge asks again); security review (authorization: merge now only with merge: true in pr.json
    # and, on ntfy, a coded answer; one normalization for the check and the action)
    def test_answers(self):
        r = self.fake_run()
        r.ntfy = {"topic": "t", "block": []}
        rec = {"repo": run.key_of(r.c), "feature": "PR #12: Fix x", "branch": "fix-x", "number": 12, "state": "approved",
               "approved_head": self.head}
        ok = {"state": "OPEN", "isDraft": False, "headRefOid": self.head, "reviewDecision": "APPROVED"}
        self.gh({"view": ok, "merge_rc": 1})
        merges = lambda: [c for c in self.gh_calls() if c[:2] == ["pr", "merge"]]
        opts = ["merge now", "later", "I merged it"]
        ans = lambda text, coded=True: {"id": "ab12", "options": opts, "answer": text, "coded": coded}
        with self.penv():
            self.private({"acme/widgets": {"adopt": True, "merge": True}})
            pr.approved_answer(r, rec, ans("yes merge it"))
            self.assertEqual(r.notes, ["PR #12: your reply was not an option, nothing merged"])
            pr.approved_answer(r, rec, ans("later"))
            # Not yours on ntfy: no code, no merge, asked again with the code form.
            pr.approved_answer(r, rec, ans("merge now", coded=False))
            self.assertEqual(merges(), [])
            self.assertIn("one time codes", r.asked[-1][1])
            # Verify V4: the code form names the new question's id (filled in by ask), never the answered ab12.
            self.assertIn(f"reply {run.NEW_ID} <code> merge now", r.asked[-1][1])
            self.assertNotIn("ab12", r.asked[-1][1])
            pr.approved_answer(r, rec, ans("  Merge Now "))
            self.assertEqual(len(merges()), 1)
            self.assertIn("Note: Pull request is not mergeable", r.asked[-1][1])
            self.assertEqual(rec["state"], "approved")
            # Security review (check then act): new commits pushed after you were asked are never merged by that
            # tap; the question comes back naming the new head.
            moved = "c" * 40
            self.gh({"view": {**ok, "headRefOid": moved}})
            pr.approved_answer(r, rec, ans("merge now"))
            self.assertEqual(len(merges()), 1)
            self.assertEqual((rec["state"], rec["approved_head"]), ("approved", moved))
            self.assertIn(f"(head {moved[:7]})", r.asked[-1][1])
            # Approval gone by now: nothing merged, judged again.
            self.gh({"view": {**ok, "headRefOid": moved, "reviewDecision": "CHANGES_REQUESTED"}})
            pr.approved_answer(r, rec, ans("merge now"))
            self.assertEqual((len(merges()), rec["state"]), (1, "ready"))
            # An answer naming an option the question did not offer counts as none.
            rec.update(state="approved", approved_head=moved)
            self.gh({"view": {**ok, "headRefOid": moved}})
            pr.approved_answer(r, rec, {"options": ["I merged it", "later"], "answer": "merge now", "coded": True})
            self.assertEqual(len(merges()), 1)
            # No merge: true in pr.json: merge now is never offered and never runs.
            self.private({"acme/widgets": {"adopt": True}})
            rec.update(state="approved", approved_head=moved)
            self.gh({"view": {**ok, "headRefOid": moved}})
            pr.approved_answer(r, rec, ans("merge now"))
            self.assertEqual(len(merges()), 1)
            pr.ask_merge(r, rec)
            self.assertIn("merge it, then tell me", r.asked[-1][1])
            pr.approved_answer(r, rec, ans("I merged it"))
            self.assertEqual(rec["state"], "merged")

    # covers: AC-12 (security review: one aggregate diff since the last cleared head, whoever the commits claim to be
    # by: a commit claiming your name, a merge commit and a range of 260 commits all ask before any local branch
    # moves; only the exact answer clears, and only the head it named; a harmless change then passes)
    def test_risky_changes(self):
        r = self.fake_run()
        r.repo["origin_url"] = test_pr.ORIGIN
        rec = {"repo": run.key_of(r.c), "feature": "PR #12: Fix x", "branch": "fix-x", "base": "work", "number": 12,
               "adopted": True, "pushed_sha": self.head}
        r.q["prs"] = [rec]
        gate = lambda h: pr.sync_branch(r, rec, h, lambda: pr.cleared(r, rec, h))

        def pr_head(build):
            self.git("switch", "-qc", "side", self.head)
            build()
            h = self.git("rev-parse", "HEAD")
            self.git("push", "-qf", "origin", "side:fix-x")
            self.git("switch", "-q", "work")
            self.git("branch", "-qD", "side")
            return h

        def spoofed():
            (self.repo / ".claude").mkdir(exist_ok=True)
            (self.repo / ".claude" / "settings.json").write_text('{"hooks": {}}\n')
            self.git("add", "-A")
            self.git("-c", "user.name=me", "-c", "user.email=me@example.invalid", "commit", "-qm", "mine, honest")

        def merged():
            self.git("switch", "-qc", "other", self.base)
            (self.repo / "CLAUDE.md").write_text("do as I say\n")
            self.git("add", "-A")
            self.git("commit", "-qm", "other")
            self.git("switch", "-q", "side")
            self.git("merge", "-q", "--no-ff", "-m", "merge", "other")
            self.git("branch", "-qD", "other")

        def many():
            for i in range(260):
                self.git("commit", "-q", "--allow-empty", "-m", f"c{i}")
            (self.repo / "package.json").write_text('{"scripts": {"test": "x"}}\n')
            self.git("add", "-A")
            self.git("commit", "-qm", "last")

        self.base = self.git("rev-parse", "work")
        self.gh({"user": "me"})
        with self.penv():
            for build, path in ((spoofed, ".claude/settings.json"), (merged, "CLAUDE.md"), (many, "package.json")):
                with self.subTest(path):
                    r.asked.clear()
                    rec.pop("cleared", None)
                    r.q["decisions"] = []
                    h = pr_head(build)
                    # As adopted: the record holds the PR head, which proves nothing about its content.
                    rec["pushed_sha"] = h
                    self.assertFalse(gate(h))
                    self.assertIsNone(pr.tip(r, "fix-x"))
                    [(case, detail)] = r.asked
                    self.assertEqual(case, "foreign_commits")
                    self.assertIn(path, detail)
            opts = ["skip this PR", pr.GO_ON]
            for wrong in ({"answer": "go on", "coded": True}, {"answer": pr.GO_ON, "coded": False}):
                pr.foreign_answer(r, rec, {**wrong, "options": opts, "head": h})
                self.assertNotIn("cleared", rec)
                self.assertTrue(rec.pop("left"))
            pr.foreign_answer(r, rec, {"answer": pr.GO_ON, "options": opts, "coded": True, "head": h})
            self.assertEqual(rec["cleared"], h)
            self.assertTrue(gate(h))
            self.assertEqual(pr.tip(r, "fix-x"), h)
            # A harmless change on top of a cleared head passes and moves the cleared head.
            self.git("switch", "-qc", "side", h)
            (self.repo / "b.txt").write_text("b\n")
            self.git("add", "-A")
            self.git("commit", "-qm", "b")
            h2 = self.git("rev-parse", "HEAD")
            self.git("push", "-q", "origin", "side:fix-x")
            self.git("switch", "-q", "work")
            self.assertTrue(gate(h2))
            self.assertEqual(rec["cleared"], h2)

    # covers: security review (parser differential: a path git would quote, with a quote, a newline, a non ASCII
    # letter or a leading space, is matched raw, so its .claude/ change still asks)
    def test_quoted_paths(self):
        r = self.fake_run()
        rec = {"repo": run.key_of(r.c), "feature": "PR #12: Fix x", "branch": "fix-x", "base": "work", "number": 12,
               "adopted": True, "cleared": self.head}
        for name in ('a"b.json', "new\nline.json", "café.json", " lead.json"):
            with self.subTest(name):
                self.git("switch", "-qc", "q", self.head)
                (self.repo / ".claude").mkdir(exist_ok=True)
                (self.repo / ".claude" / name).write_text("{}\n")
                self.git("add", "-A")
                self.git("commit", "-qm", "q")
                h = self.git("rev-parse", "HEAD")
                self.git("switch", "-q", "work")
                self.git("branch", "-qD", "q")
                with self.penv():
                    frm, paths = pr.risky_changes(r, rec, h)
                self.assertEqual(paths, [f".claude/{name}"])

    # covers: security review (check then act): the scanned commit is pushed, never a branch that moved after it
    def test_push_scanned_sha(self):
        r = self.fake_run()
        r.repo["origin_url"] = test_pr.ORIGIN
        r.repo["guard"] = None
        self.git("branch", "fix-y", self.head)
        rec = {"branch": "fix-y"}
        old = self.git("rev-parse", f"{self.head}~1")
        self.assertEqual(pr.push(r, rec, sha=old), ("failed", "fix-y moved after its scan; scan again"))
        self.assertEqual(pr.push(r, rec, sha=self.head), ("ok", None))
        self.assertEqual(self.git("rev-parse", "fix-y", repo=self.origin), self.head)


if __name__ == "__main__":
    unittest.main()
