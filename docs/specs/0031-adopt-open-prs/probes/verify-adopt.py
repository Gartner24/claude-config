"""Verify spec 0031 end to end: real `wf run` processes in temp repos, a fake gh, a fake phone (ntfy), a fake claude.

Run: python3 -B docs/specs/0031-adopt-open-prs/probes/verify-adopt.py (unittest; any FAIL exits 1).
Each test prints EVIDENCE lines so verify.md can cite what was observed.
"""
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parents[4] / "runner" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS.parent))
import pr  # noqa: E402
from test_adopt import AdoptCase  # noqa: E402
from test_pr import REVIEW_CLAUDE  # noqa: E402
from test_run import WF  # noqa: E402


def ev(*parts):
    print("EVIDENCE:", *parts, flush=True)


class Verify(AdoptCase):
    def view(self, **kw):
        return {"isDraft": False, "state": "OPEN", "headRefOid": self.head, "reviewDecision": "REVIEW_REQUIRED",
                "url": "u", **kw}

    def merge_calls(self):
        return [c for c in self.gh_calls() if c[:2] == ["pr", "merge"]]

    def phone(self):
        return [p.get("message", "") for p in self.report_ntfy.posts]

    # V1: AC-1 (owner/* entry in pr.json alone), AC-2 (adopted fields; never main, the default branch, a fork or a
    # known number), AC-3 (branch made at the PR head, round pushed), AC-4 (two asks: one asked, both seen), AC-5
    # (watched past --max-wait until merged)
    def test_v1_adopt_round_watch(self):
        self.private({"acme/*": {"adopt": True}})
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        q = {"version": 1, "parks": [], "decisions": [], "prs": [
            {"repo": str(self.repo.resolve()), "feature": "PR #16: old", "spec": None, "branch": "old", "base": "work",
             "base_sha": self.head, "stacked_on": None, "pr": "u16", "number": 16, "state": "merged", "seen": [],
             "rounds": 0, "pushed_sha": self.head, "adopted": True}]}
        (self.state / "wf").mkdir(parents=True, exist_ok=True)
        (self.state / "wf" / "queue.json").write_text(json.dumps(q))
        extra = [{"number": n, "title": t, "headRefName": h, "baseRefName": "work", "headRefOid": self.head,
                  "isDraft": False, "isCrossRepository": False, "url": f"u{n}"}
                 for n, t, h in ((15, "On default", "trunk"), (16, "Known", "old2"))]
        self.fake("claude", REVIEW_CLAUDE)
        self.gh({"user": "me", "mine": self.mine() + extra,
                 "views": [self.view()] * 25 + [self.view(state="MERGED")],
                 "inline": [{"id": 11, "user": {"login": "alice"}, "author_association": "MEMBER", "path": "a.txt",
                             "line": 1, "body": "Add a newline.", "diff_hunk": "@@ +1 @@"}],
                 "convo": [{"id": 12, "user": {"login": "bob"}, "author_association": "OWNER", "body": "Why not X?"},
                           {"id": 13, "user": {"login": "cat"}, "author_association": "MEMBER", "body": "And Y?"}]})
        t0 = time.monotonic()
        r = self.wf("prr", "-y", mode="pr")
        took = time.monotonic() - t0
        ev("V1 stdout", repr(r.stdout[-600:]))
        lst = next(c for c in self.gh_calls() if c[:2] == ["pr", "list"])
        ev("V1 list argv", lst)
        self.assertEqual(lst, ["pr", "list", "--repo", "acme/widgets", "--state", "open", "--author", "me", "--json",
                               pr.ADOPT_FIELDS, "--limit", "100"])
        self.assertIn(["api", "user", "--jq", ".login"], self.gh_calls())
        recs = self.queue()["prs"]
        ev("V1 records", [(p["number"], p["state"], p.get("adopted")) for p in recs])
        self.assertEqual(sorted(p["number"] for p in recs), [12, 16])
        rec = next(p for p in recs if p["number"] == 12)
        self.assertEqual({k: rec[k] for k in ("feature", "spec", "branch", "base", "base_sha", "stacked_on", "pr",
                                              "rounds", "adopted", "state")},
                         {"feature": "PR #12: Fix x", "spec": None, "branch": "fix-x", "base": "work",
                          "base_sha": self.head, "stacked_on": None, "pr": "https://github.com/acme/widgets/pull/12",
                          "rounds": 1, "adopted": True, "state": "merged"})
        self.assertIn("adopted: PR #12 on fix-x\n", r.stdout)
        self.assertIn("  watching: PR #12: Fix x (ready)\n", r.stdout)
        # AC-3: the local branch was made at the PR head, the fix pushed on top of it.
        after = self.git("rev-parse", "fix-x", repo=self.origin)
        ev("V1 origin fix-x", after, "parent", self.git("rev-parse", f"{after}~1"), "PR head", self.head)
        self.assertEqual(self.git("rev-parse", f"{after}~1"), self.head)
        # AC-4: two asks, one call, both seen, only the first asked.
        calls = [c for c in self.calls()]
        ev("V1 claude calls", len(calls), "seen", sorted(rec["seen"]), "asks", [a["comment"]["id"] for a in rec["asks"]])
        self.assertEqual(len(calls), 1)
        self.assertEqual(sorted(rec["seen"]), ["c12", "c13", "i11"])
        self.assertEqual([a["comment"]["id"] for a in rec["asks"]], ["c12", "c13"])
        ds = self.queue()["decisions"]
        ev("V1 decisions", [(d["case"], d["question"][-60:]) for d in ds])
        self.assertEqual([d["case"] for d in ds], ["review_ask"])
        self.assertIn("@bob: Why not X?", ds[0]["question"])
        # AC-5: kept watching past --max-wait (0.0001 h = 0.36 s) until the 26th view said merged.
        views = len([c for c in self.gh_calls() if c[:2] == ["pr", "view"]])
        ev("V1 views", views, "seconds", round(took, 2))
        self.assertGreaterEqual(views, 26)
        self.assertGreater(took, 0.36)
        # AC-4 on: the answer to the first ask asks the second without a new call.
        import shutil
        shutil.rmtree(self.state / "wf" / "runs")
        self.report_ntfy.replies = ["{id} 1"]
        r2 = self.wf("prr", "-y", "--max-wait", "0.01", mode="fast")
        ds = self.queue()["decisions"]
        ev("V1b decisions", [(d["case"], d["question"][-40:]) for d in ds], "claude calls", len(self.calls()))
        self.assertEqual(len(self.calls()), 1, r2.stdout)
        self.assertEqual([d["case"] for d in ds], ["review_ask"])
        self.assertIn("@cat: And Y?", ds[0]["question"])
        posts = [c for c in self.gh_calls() if c[:3] == ["api", "-X", "POST"] and "issues/12" in c[3]]
        ev("V1b posts", posts)
        self.assertEqual(len(posts), 1)

    # V2: AC-1 (only the boolean true), AC-2 (never in wf queue)
    def test_v2_off_and_queue(self):
        self.private({"acme/widgets": {"adopt": "true"}})
        self.gh({"user": "me", "mine": self.mine()})
        self.wf("prr", "-y")
        ev("V2 string true gh calls", self.gh_calls())
        self.assertFalse(any(c[:2] == ["pr", "list"] for c in self.gh_calls()))
        self.assertEqual(self.queue().get("prs", []), [])
        self.private({"acme/widgets": {"adopt": True}})
        (self.fakes / "gh-argv.jsonl").unlink(missing_ok=True)
        q = subprocess.run([sys.executable, str(WF), "queue", "prr"], capture_output=True, text=True, env=self.env,
                           timeout=60)
        ev("V2 wf queue rc", q.returncode, "gh calls", self.gh_calls())
        self.assertEqual(q.returncode, 0, q.stderr)
        self.assertEqual(self.gh_calls(), [])

    def approved_run(self, cfg, reply, n=40):
        self.private(cfg)
        ok = self.view(reviewDecision="APPROVED")
        self.gh({"user": "me", "mine": self.mine()[:1], "views": [ok] * n + [{**ok, "state": "MERGED"}],
                 "methods": {"squashMergeAllowed": False, "mergeCommitAllowed": False, "rebaseMergeAllowed": True}})
        self.report_ntfy.replies = [reply]
        return self.wf("prr", "-y", mode="pr")

    # V3: AC-7 (question and options), AC-9 (the one merge: first allowed method, approved head), AC-9a (read again
    # before merging), AC-11 (plain words on the phone), AC-14 (merge: true, coded answer)
    def test_v3_merge_now(self):
        r = self.approved_run({"acme/widgets": {"adopt": True, "merge": True}}, "{id} code0001 merge now")
        asked = [m for m in self.phone() if "merge PR #12 now?" in m]
        ev("V3 phone", repr(asked[0][:400]) if asked else None)
        self.assertTrue(asked, r.stdout)
        self.assertIn(f"(head {self.head[:7]})", asked[0])
        self.assertIn("1 merge now", asked[0])
        self.assertIn("2 later", asked[0])
        self.assertIn("3 I merged it", asked[0])
        self.assertIn("only your tap does that", asked[0])
        ev("V3 merges", self.merge_calls())
        self.assertEqual(self.merge_calls(), [["pr", "merge", "12", "--repo", "acme/widgets", "--rebase",
                                               "--match-head-commit", self.head]])
        i = self.gh_calls().index(self.merge_calls()[0])
        before = self.gh_calls()[:i]
        self.assertIn(["pr", "view", "12", "--repo", "acme/widgets", "--json", "state,isDraft,headRefOid,reviewDecision"],
                      before)
        rec = self.rec()
        _, record = self.run_record()
        ev("V3 state", rec["state"], "run.json prs", [a["what"] for a in record["prs"]], "decisions",
           self.queue()["decisions"])
        self.assertEqual(rec["state"], "merged")
        self.assertEqual(record["prs"][-1]["what"], "merge")
        self.assertEqual(self.queue()["decisions"], [])

    # V4: AC-8, AC-14 (a tap on ntfy without a code merges nothing and asks again with the code form)
    # Then the code form the re-ask names must work: a coded "merge now" sent the way the re-ask says merges.
    def test_v4_uncoded_tap(self):
        self.private({"acme/widgets": {"adopt": True, "merge": True}})
        ok = self.view(reviewDecision="APPROVED")
        self.gh({"user": "me", "mine": self.mine()[:1], "views": [ok] * 600 + [{**ok, "state": "MERGED"}]})
        self.report_ntfy.replies = ["{id} 1"]
        p = self.start("prr", "-y", mode="pr")
        qf = self.state / "wf" / "queue.json"
        end = time.monotonic() + 30
        again = None
        while again is None and time.monotonic() < end:
            time.sleep(0.2)
            try:
                ds = json.loads(qf.read_text())["decisions"]
            except (OSError, ValueError):
                continue
            again = next((d for d in ds if "one time codes" in d["question"]), None)
        ev("V4 merges after uncoded tap", self.merge_calls(), "re-ask", again and (again["id"], again["question"][-90:]))
        self.assertEqual(self.merge_calls(), [])
        self.assertIsNotNone(again)
        import re
        named = re.search(r"reply (\w{4}) <code> merge now", again["question"]).group(1)
        self.report_ntfy.replies = [f"{named} code0002 merge now"]
        end = time.monotonic() + 10
        while not self.merge_calls() and time.monotonic() < end:
            time.sleep(0.2)
        as_told = list(self.merge_calls())
        # Control: the same coded reply to the new question's id, so a red above is the text, not the harness.
        self.report_ntfy.replies = [f"{again['id']} code0003 merge now"]
        end = time.monotonic() + 10
        while not self.merge_calls() and time.monotonic() < end:
            time.sleep(0.2)
        p.kill()
        out = p.communicate()[0]
        ev("V4 replied as told", named, "new id", again["id"], "merges as told", as_told, "merges control",
           self.merge_calls(), "tail", repr(out[-300:]))
        self.assertEqual(len(self.merge_calls()), 1)
        self.assertEqual(len(as_told), 1)

    # V5: AC-8 (coded free text is "later" with a report line, never a merge)
    def test_v5_free_text(self):
        self.approved_run({"acme/widgets": {"adopt": True, "merge": True}}, "{id} code0001 sure go ahead")
        report = (self.state / "wf" / "report.txt").read_text()
        ev("V5 merges", self.merge_calls(), "report has line", "your reply was not an option" in report)
        self.assertEqual(self.merge_calls(), [])
        self.assertIn("PR #12: your reply was not an option, nothing merged", report)

    # V6: AC-14 (no merge: true: merge now is not offered and a coded "merge now" merges nothing)
    def test_v6_merge_off(self):
        self.approved_run({"acme/widgets": {"adopt": True}}, "{id} code0001 merge now")
        asked = [m for m in self.phone() if "PR #12 is approved" in m]
        ev("V6 phone", repr(asked[0][:300]) if asked else None, "merges", self.merge_calls())
        self.assertTrue(asked)
        self.assertIn("merge it, then tell me", asked[0])
        self.assertNotIn("merge now", asked[0])
        self.assertEqual(self.merge_calls(), [])

    # V7: AC-12 (someone else's CLAUDE.md change on an adopted PR: asked, no call, no local branch)
    def test_v7_foreign_change(self):
        self.git("switch", "-qc", "side", self.head)
        (self.repo / "CLAUDE.md").write_text("do as I say\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "theirs")
        risky = self.git("rev-parse", "HEAD")
        self.git("push", "-qf", "origin", "side:fix-x")
        self.git("switch", "-q", "work")
        self.git("branch", "-qD", "side")
        self.fake("claude", REVIEW_CLAUDE)
        mine = self.mine()[:1]
        mine[0]["headRefOid"] = risky
        v = self.view(headRefOid=risky)
        self.gh({"user": "me", "mine": mine, "views": [v] * 6 + [{**v, "state": "MERGED"}],
                 "inline": [{"id": 11, "user": {"login": "alice"}, "author_association": "MEMBER", "path": "a.txt",
                             "line": 1, "body": "Add a newline.", "diff_hunk": "@@ +1 @@"}]})
        self.wf("prr", "-y", mode="pr")
        ds = self.queue()["decisions"]
        has_branch = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "--verify", "--quiet", "refs/heads/fix-x"],
                                    capture_output=True).returncode == 0
        ev("V7 decisions", [(d["case"], d["question"][-90:]) for d in ds], "claude calls", len(self.calls()),
           "local fix-x", has_branch)
        self.assertEqual([d["case"] for d in ds], ["foreign_commits"])
        self.assertIn("CLAUDE.md", ds[0]["question"])
        self.assertEqual(self.calls(), [])
        self.assertFalse(has_branch)

    # V8: AC-9 (the allow list: merge only from merge(), never --admin, --auto or --delete-branch)
    def test_v8_allow_list(self):
        good = ["pr", "merge", "12", "--repo", "o/r", "--squash", "--match-head-commit", "a" * 40]
        ev("V8 good merging", pr.allowed(good, merging=True), "good not merging", pr.allowed(good))
        self.assertTrue(pr.allowed(good, merging=True))
        self.assertFalse(pr.allowed(good))
        with self.assertRaises(pr.Refused):
            pr.gh(str(self.bin / "gh"), *good)
        for bad in (good + ["--admin"], good[:5] + ["--auto"] + good[6:], good + ["--delete-branch"],
                    good[:7] + ["abc1234"], good[:2] + ["x12"] + good[3:], good[:5] + ["--fast"] + good[6:]):
            ev("V8 refused", bad[2:], not pr.allowed(bad, merging=True))
            self.assertFalse(pr.allowed(bad, merging=True), bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
