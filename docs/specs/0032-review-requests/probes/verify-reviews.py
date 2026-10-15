"""Verify spec 0032 end to end: real `wf run` processes in temp repos, a fake gh, a fake phone (ntfy), a fake claude,
plus the reviews module driven directly where a step needs several answers in one place.

Run: python3 -B docs/specs/0032-review-requests/probes/verify-reviews.py (unittest; any FAIL exits 1).
Each test prints EVIDENCE lines so verify.md can cite what was observed.
"""
import json
import os
import re
import shutil
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parents[4] / "runner" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS.parent))
import plain  # noqa: E402
import pr  # noqa: E402
import reviews  # noqa: E402
import run  # noqa: E402
import test_reviews  # noqa: E402
from test_reviews import CODE_REVIEW_CLAUDE, ReviewCase  # noqa: E402


def ev(*parts):
    print("EVIDENCE:", *parts, flush=True)


class Verify(ReviewCase):
    def keep_alive(self, n=40):
        """An adopted PR #12 the run watches until its view says merged, so the run stays to take phone answers."""
        view = {"isDraft": False, "state": "OPEN", "headRefOid": self.head, "reviewDecision": "REVIEW_REQUIRED",
                "url": "u"}
        return [view] * n + [{**view, "state": "MERGED"}]

    def phone(self):
        return [m["message"] for m in self.report_ntfy.messages]

    def posts(self):
        return [c for c in self.gh_calls() if c[:3] == ["api", "-X", "POST"]]

    def first_run(self, reply="{id} 1"):
        self.fake("claude", CODE_REVIEW_CLAUDE)
        self.env["PLANTED_SECRET"] = "s3cr3t"
        self.private({"acme/widgets": {"review_requests": True, "adopt": True}})
        self.gh({"user": "me", "mine": self.mine()[:1], "requests": [{"number": 5}], "byn": {"5": self.view5},
                 "views": self.keep_alive()})
        self.report_ntfy.replies = [reply]
        return self.wf("prr", "-y", mode="pr")

    # V1: AC-1 (pr.json alone), AC-2 (search and view argv, record), AC-3 (question), AC-4 (fetch, data folder, isolated
    # call), AC-5 (prompt, DRAFT lines only), AC-6 (draft to the phone before the question), AC-10 (no park, no stop)
    def test_v1_request_to_draft(self):
        r = self.first_run()
        out = r.stdout + r.stderr
        ev("V1 rc", r.returncode, "tail", repr(out[-300:]))
        calls = self.gh_calls()
        search = [c for c in calls if c[:2] == ["search", "prs"]]
        ev("V1 search argv", search[0] if search else None)
        self.assertEqual(search[0], ["search", "prs", "--review-requested=@me", "--state", "open", "--repo",
                                     "acme/widgets", "--json", "number,title,author,url", "--limit", "30"])
        view = [c for c in calls if c[:3] == ["pr", "view", "5"]]
        ev("V1 view argv", view[0] if view else None)
        self.assertEqual(view[0], ["pr", "view", "5", "--repo", "acme/widgets", "--json", reviews.VIEW])
        [rec] = self.queue()["reviews"]
        ev("V1 record", {k: rec[k] for k in ("feature", "author", "size", "state", "head", "base", "url")})
        self.assertEqual((rec["feature"], rec["author"], rec["size"], rec["head"], rec["base"]),
                         ("review PR #5: Add z", "carol", [1, 0, 4], self.pr_head, self.base))
        asked = [m for m in self.phone() if "PR #5 Add z by carol" in m]
        ev("V1 request on phone", repr(asked[0][:500]) if asked else None)
        self.assertTrue(asked, out)
        # AC-3 asks with the link; spec 0033 AC-8 (later) keeps links off ntfy, a public server, so the link is in the
        # question wf stores and prints, and off the ntfy message.
        printed = [x for x in r.stdout.splitlines() if "PR #5 Add z by carol" in x]
        ev("V1 request printed", printed)
        self.assertIn("+1 -0 in 4 files https://github.com/acme/widgets/pull/5", printed[0])
        self.assertIn("+1 -0 in 4 files", asked[0])
        self.assertNotIn("https://", asked[0])
        self.assertIn("1 draft a review", asked[0])
        self.assertIn("2 skip", asked[0])
        # AC-4: fetched into refs/wf/review/5, never checked out.
        ref = self.git("rev-parse", "refs/wf/review/5")
        branch = self.git("symbolic-ref", "--short", "HEAD")
        ev("V1 fetched ref", ref, "PR head", self.pr_head, "repo branch", branch,
           "PR files in repo", (self.repo / "CLAUDE.md").exists())
        self.assertEqual((ref, branch), (self.pr_head, "work"))
        self.assertFalse((self.repo / "CLAUDE.md").exists())
        cr = json.loads((self.fakes / "code-review.json").read_text())
        folder, _ = self.run_record()
        folder = os.path.join(folder, "review-5")
        argv = cr["argv"]
        g = json.loads(argv[argv.index("--settings") + 1])
        ev("V1 call cwd", cr["cwd"], "files", cr["files"], "tools", argv[argv.index("--tools") + 1],
           "sources", argv[argv.index("--setting-sources") + 1], "restricted", "--restricted" in argv,
           "mcp", argv[argv.index("--mcp-config") + 1], "hooks off", g.get("disableAllHooks"), "hooks key", "hooks" in g,
           "allowWrite", g["sandbox"]["filesystem"]["allowWrite"], "net", g["sandbox"]["network"]["allowedDomains"],
           "env keys", sorted(cr["env"]))
        test_reviews.TestReviewRun.assert_isolated(self, cr, folder)
        self.assertIn(os.path.realpath(self.repo / ".git"), g["sandbox"]["filesystem"]["denyWrite"])
        prompt = argv[argv.index("-p") + 1]
        ev("V1 prompt head", repr(prompt[:160]))
        self.assertTrue(prompt.startswith(f"/code-review PR #5 ({self.base[:12]}...{self.pr_head[:12]})"))
        self.assertIn("never run /review, /review-stack or /code-review ultra".casefold(), prompt.casefold())
        self.assertRegex(prompt, r"BEGIN PR-DATA-\d+\ntitle: Add z\nauthor: carol\n")
        # AC-5, AC-6: only DRAFT lines kept; the draft (a shortened ntfy view) sent before the question.
        md = (Path(folder).parent / "review-5.md").read_text()
        ev("V1 review-5.md", repr(md))
        self.assertIn("verdict: approve", md)
        self.assertIn("- a.txt:2 Name this constant.", md)
        self.assertNotIn("other.txt", md)
        self.assertNotIn("notes", md)
        msgs = self.phone()
        di = next(i for i, m in enumerate(msgs) if m.startswith("draft review of PR #5"))
        qi = next(i for i, m in enumerate(msgs) if "post this review of PR #5?" in m)
        ev("V1 draft msg", repr(msgs[di][:400]), "index", di, "question", repr(msgs[qi][:400]), "index", qi)
        self.assertLess(di, qi)
        self.assertIn("full draft in the run folder", msgs[di])
        self.assertIn("shortened view", msgs[di])
        self.assertIn("verdict: approve, 1 line comments", msgs[qi])
        for i, o in enumerate(("post as my review", "edit first", "don't post"), 1):
            self.assertIn(f"{i} {o}", msgs[qi])
        self.assertEqual(self.posts(), [])
        _, record = self.run_record()
        ev("V1 parks", record.get("parks"), "stopped", record.get("stopped"))
        self.assertFalse(record.get("stopped"))

    # V1b: AC-8, AC-8a, AC-9 (next run, your coded tap posts exactly the shown draft through the one allowed call)
    def test_v1b_post(self):
        self.first_run()
        shutil.rmtree(self.state / "wf" / "runs")
        self.report_ntfy.replies = ["{id} code0001 post as my review"]
        self.gh({"user": "me", "requests": [{"number": 5}], "byn": {"5": self.view5}, "views": self.keep_alive(3)})
        r = self.wf("prr", "-y", mode="pr")
        ev("V1b posts", self.posts(), "tail", repr((r.stdout + r.stderr)[-200:]))
        [post] = self.posts()
        self.assertEqual(post[:5], ["api", "-X", "POST", "repos/acme/widgets/pulls/5/reviews", "--input"])
        i = self.gh_calls().index(post)
        self.assertIn(["pr", "view", "5", "--repo", "acme/widgets", "--json", "state"], self.gh_calls()[:i])
        body = json.loads(Path(post[5]).read_text())
        ev("V1b body", body, "input in run folder", str(self.state) in post[5])
        self.assertEqual(body, {"commit_id": self.pr_head, "event": "APPROVE", "body": "Small and fine.",
                                "comments": [{"path": "a.txt", "line": 2, "side": "RIGHT",
                                              "body": "Name this constant."}]})
        [rv] = self.queue()["reviews"]
        _, record = self.run_record()
        ev("V1b state", rv["state"], "run.json prs", record.get("prs"))
        self.assertEqual(rv["state"], "posted")
        self.assertEqual([(p["what"], p["number"], p["event"]) for p in record["prs"] if p["what"] == "review"],
                         [("review", 5, "APPROVE")])

    # V2: AC-1 (only the boolean true turns it on; nothing in the repo does)
    def test_v2_off(self):
        self.private({"acme/widgets": {"review_requests": "true", "adopt": True}})
        (self.repo / "AGENTS.md").write_text("# Agents\n- review_requests: true\n")
        self.gh({"user": "me", "mine": self.mine()[:1], "requests": [{"number": 5}], "byn": {"5": self.view5},
                 "views": self.keep_alive(2)})
        self.wf("prr", "-y", mode="pr")
        ev("V2 search calls", [c for c in self.gh_calls() if c[:1] == ["search"]], "reviews",
           self.queue().get("reviews"))
        self.assertFalse(any(c[:2] == ["search", "prs"] for c in self.gh_calls()))
        self.assertFalse(self.queue().get("reviews"))

    # V3: AC-3 (skip sets skipped, no call, no other question)
    def test_v3_skip(self):
        self.first_run("{id} 2")
        [rec] = self.queue()["reviews"]
        ev("V3 state", rec["state"], "code-review call", (self.fakes / "code-review.json").exists(), "decisions",
           [d["case"] for d in self.queue()["decisions"]])
        self.assertEqual(rec["state"], "skipped")
        self.assertFalse((self.fakes / "code-review.json").exists())
        self.assertFalse(any(d["case"].startswith("review") for d in self.queue()["decisions"]))

    # V4: AC-2 (own and draft PRs never asked; a failed read is a report line), AC-3 (no longer asked: gone, withdrawn)
    def test_v4_skips_and_gone(self):
        self.private({"acme/widgets": {"review_requests": True, "adopt": True}})
        own = {**self.view5, "number": 6, "author": {"login": "me"}}
        drft = {**self.view5, "number": 7, "isDraft": True}
        self.gh({"user": "me", "mine": self.mine()[:1], "requests": [{"number": 6}, {"number": 7}, {"number": 5}],
                 "byn": {"5": self.view5, "6": own, "7": drft}, "views": self.keep_alive(2)})
        self.wf("prr", "-y", mode="pr")
        recs = self.queue()["reviews"]
        asked = [d for d in self.queue()["decisions"] if d["case"] == "review_request"]
        ev("V4 records", [(x["number"], x["state"]) for x in recs], "asked", [d["feature"] for d in asked])
        self.assertEqual([x["number"] for x in recs], [5])
        self.assertEqual([d["feature"] for d in asked], ["review PR #5: Add z"])
        shutil.rmtree(self.state / "wf" / "runs")
        self.gh({"user": "me", "mine": self.mine()[:1], "requests": [], "views": self.keep_alive(2)})
        self.wf("prr", "-y", mode="pr")
        ev("V4 after gone", [(x["number"], x["state"]) for x in self.queue()["reviews"]], "decisions",
           [d["case"] for d in self.queue()["decisions"]])
        self.assertEqual(self.queue()["reviews"][0]["state"], "gone")
        self.assertFalse(any(d["case"] == "review_request" for d in self.queue()["decisions"]))
        shutil.rmtree(self.state / "wf" / "runs")
        (self.state / "wf" / "queue.json").unlink()
        self.gh({"user": "me", "mine": self.mine()[:1], "requests": "not json", "views": self.keep_alive(2)})
        r = self.wf("prr", "-y", mode="pr")
        report = (self.state / "wf" / "report.txt").read_text()
        line = [x for x in report.splitlines() if "review requests not read" in x]
        _, rj = self.run_record()
        ev("V4 failed read line", line, "rc", r.returncode, "run.json notes", rj.get("notes"), "search calls",
           len([c for c in self.gh_calls() if c[:2] == ["search", "prs"]]), "report", repr(report[:600]))
        self.assertEqual(len(line), 1)

    # V5: AC-7 (edit first asks review_edit; your text replaces the summary, the draft is sent again and asked again;
    # free text to review_draft also replaces it and never posts)
    def test_v5_edit(self):
        r = self.fake_run()
        with self.penv():
            self.gh({"user": "me", "requests": [{"number": 5}], "byn": {"5": self.view5}, "view": {"state": "OPEN"}})
            reviews.poll(r)
            [rec] = r.q["reviews"]
            reviews.answer(r, {"case": "review_request", "feature": rec["feature"], "answer": "draft a review",
                               "options": ["draft a review", "skip"]})
            rec = r.q["reviews"][0]
            sent0 = len([m for m in self.phone() if m.startswith("draft review of PR #5")])
            base = {"id": "ab12", "feature": rec["feature"], "coded": True}
            reviews.answer(r, {**base, "case": "review_draft", "answer": "edit first", "hash": rec["shown"],
                               "options": ["post as my review", "edit first", "don't post"]})
            ev("V5 after edit first", r.asked[-1])
            self.assertEqual(r.asked[-1], ("review_edit", "reply with the text that replaces the summary"))
            self.assertEqual(run.CASES["review_edit"][1], ())
            reviews.answer(r, {**base, "case": "review_edit", "answer": "Please rename the constant.", "options": []})
            rec = r.q["reviews"][0]
            sent1 = [m for m in self.phone() if m.startswith("draft review of PR #5")]
            ev("V5 summary", rec["draft"]["summary"], "drafts sent", sent0, "->", len(sent1), "asked", r.asked[-1][0])
            self.assertEqual(rec["draft"]["summary"], "Please rename the constant.")
            self.assertEqual(len(sent1), sent0 + 1)
            self.assertIn("Please rename the constant.", sent1[-1])
            self.assertEqual(r.asked[-1][0], "review_draft")
            reviews.answer(r, {**base, "case": "review_draft", "answer": "post it, looks fine", "hash": rec["shown"],
                               "options": ["post as my review", "edit first", "don't post"]})
            ev("V5 free text summary", r.q["reviews"][0]["draft"]["summary"], "posts", self.posts())
            self.assertEqual(r.q["reviews"][0]["draft"]["summary"], "post it, looks fine")
            self.assertEqual(self.posts(), [])

    # V6: AC-8a (an uncoded ntfy tap on post posts nothing and asks again with the code form naming the NEW question's
    # id; the reply sent as told posts once)
    def test_v6_uncoded_tap(self):
        self.first_run()
        shutil.rmtree(self.state / "wf" / "runs")
        self.gh({"user": "me", "requests": [{"number": 5}], "byn": {"5": self.view5}, "views": self.keep_alive(600)})
        self.report_ntfy.replies = ["{id} 1"]
        p = self.start("prr", "-y", mode="pr")
        qf = self.state / "wf" / "queue.json"
        end, again = time.monotonic() + 30, None
        while again is None and time.monotonic() < end:
            time.sleep(0.2)
            try:
                ds = json.loads(qf.read_text())["decisions"]
            except (OSError, ValueError):
                continue
            again = next((d for d in ds if d["case"] == "review_draft" and "one time codes" in d["question"]), None)
        ev("V6 posts after uncoded tap", self.posts(), "re-ask", again and (again["id"], again["question"][-120:]))
        self.assertEqual(self.posts(), [])
        self.assertIsNotNone(again)
        named = re.search(r"reply (\w{4}) <code> post as my review", again["question"]).group(1)
        self.report_ntfy.replies = [f"{named} code0002 post as my review"]
        end = time.monotonic() + 15
        while not self.posts() and time.monotonic() < end:
            time.sleep(0.2)
        p.kill()
        p.communicate()
        ev("V6 named", named, "new id", again["id"], "posts as told", self.posts())
        self.assertEqual(named, again["id"])
        self.assertEqual(len(self.posts()), 1)

    # V7: AC-8 (attribution scan blocks the post and asks again naming it; a closed PR is not posted to), AC-8a (an
    # answer about another draft never posts), AC-8b (secrets, home paths, private names, lines outside the diff dropped)
    def test_v7_scans_and_drops(self):
        r = self.fake_run()
        r.lines = ["DRAFT COMMENT: a.txt:2 Name this constant.",
                   "DRAFT COMMENT: a.txt:2 token ghp_" + "b" * 36,
                   f"DRAFT COMMENT: a.txt:2 see {os.path.expanduser('~')}/.ssh/id_rsa",
                   "DRAFT COMMENT: a.txt:2 for Zorblex",
                   "DRAFT COMMENT: a.txt:99 off the diff",
                   "DRAFT SUMMARY: api_key = abcdef123456", "DRAFT VERDICT: request changes"]
        with self.penv():
            self.gh({"user": "me", "requests": [{"number": 5}], "byn": {"5": self.view5}, "view": {"state": "OPEN"}})
            reviews.poll(r)
            [rec] = r.q["reviews"]
            reviews.answer(r, {"case": "review_request", "feature": rec["feature"], "answer": "draft a review",
                               "options": ["draft a review", "skip"]})
            rec = r.q["reviews"][0]
            dr = rec["draft"]
            sent = [m for m in self.phone() if m.startswith("draft review of PR #5")][-1]
            ev("V7 draft", dr, "phone", repr(sent[:300]))
            self.assertEqual(dr["comments"], [{"path": "a.txt", "line": 2, "body": "Name this constant."}])
            self.assertEqual((dr["summary"], dr["dropped"]), (reviews.NO_SUMMARY, 4))
            self.assertIn("4 drafted line(s) dropped", sent)
            self.assertNotIn("ghp_", json.dumps(r.q) + "".join(self.phone()))
            ans = {"id": "ab12", "case": "review_draft", "feature": rec["feature"], "coded": True,
                   "options": ["post as my review", "edit first", "don't post"], "answer": "post as my review"}
            reviews.answer(r, {**ans, "hash": "f" * 64})
            ev("V7 stale hash posts", self.posts(), "asked", r.asked[-1][1][-70:])
            self.assertEqual(self.posts(), [])
            self.assertIn("changed since you saw it", r.asked[-1][1])
            rec = r.q["reviews"][0]
            rec["draft"]["summary"] = "ok\nGenerated with Claude Code"
            rec["shown"] = reviews.digest(rec["draft"])
            reviews.answer(r, {**ans, "hash": rec["shown"]})
            ev("V7 attribution posts", self.posts(), "asked", r.asked[-1][1][-90:])
            self.assertEqual(self.posts(), [])
            self.assertIn("edit first", r.asked[-1][1])
            rec["draft"]["summary"] = "fine"
            rec["shown"] = reviews.digest(rec["draft"])
            self.gh({"view": {"state": "CLOSED"}})
            reviews.answer(r, {**ans, "hash": rec["shown"]})
            ev("V7 closed PR posts", self.posts(), "state", r.q["reviews"][0]["state"])
            self.assertEqual(self.posts(), [])
            self.assertEqual(r.q["reviews"][0]["state"], "gone")

    # V8: AC-6 (Telegram: the exact draft as posted, through telegram.send_report which splits or attaches), AC-8a
    def test_v8_telegram_body(self):
        rec = {"number": 5, "draft": {"verdict": "comment", "summary": "S " * 3000,
                                      "comments": [{"path": "dir/a.txt", "line": 2, "body": "x" * 800}], "dropped": 0}}
        r = self.fake_run()
        r.ntfy = {"chat_id": 5, "block": []}
        r.q["reviews"] = [{**rec, "repo": run.key_of(r.c), "feature": "f"}]
        got = []
        import telegram
        with mock.patch.object(telegram, "send_report", lambda cfg, body: got.append(body) or True):
            reviews.send_draft(r, r.q["reviews"][0])
        ev("V8 telegram body len", len(got[0]) if got else None, "has full comment", got and ("x" * 800) in got[0])
        self.assertEqual(len(got), 1)
        self.assertIn("summary: " + ("S " * 3000).strip(), got[0])
        self.assertIn("dir/a.txt:2 " + "x" * 800, got[0])
        self.assertNotIn("shortened view", got[0])

    # V9: AC-9 (allow list: the search shape; the post only with posting=True; gh pr review refused)
    def test_v9_allow_list(self):
        search = ["search", "prs", "--review-requested=@me", "--state", "open", "--repo", "o/r", "--json",
                  reviews.FIELDS, "--limit", "30"]
        post = ["api", "-X", "POST", "repos/o/r/pulls/5/reviews", "--input", "/run/review-5.json"]
        ev("V9 search", pr.allowed(search), "post", pr.allowed(post), "post posting", pr.allowed(post, posting=True),
           "pr review", pr.allowed(["pr", "review", "5", "--approve"], posting=True))
        self.assertTrue(pr.allowed(search))
        self.assertFalse(pr.allowed(post))
        self.assertTrue(pr.allowed(post, posting=True))
        with self.assertRaises(pr.Refused):
            pr.gh(str(self.bin / "gh"), *post)
        for bad in (["pr", "review", "5", "--approve"], [*search[:2], "--review-requested=bob", *search[3:]],
                    [*post[:3], "repos/o/r/pulls/5/merge", *post[4:]], [*post[:4], "-f", "event=APPROVE"]):
            self.assertFalse(pr.allowed(bad, posting=True), bad)

    # V10: AC-10, AC-11 (rows P13 to P15 in the case tables; plain words rows)
    def test_v10_tables(self):
        rows = {c: run.CASES.get(c) for c in reviews.CASES}
        ev("V10 CASES", rows, "PR_CASES", [c for c in reviews.CASES if c in run.PR_CASES],
           "PLAIN", {c: plain.PLAIN.get(c) for c in reviews.CASES})
        self.assertEqual(rows, {"review_request": ("P13", ("draft a review", "skip")),
                                "review_draft": ("P14", ("post as my review", "edit first", "don't post")),
                                "review_edit": ("P15", ())})
        self.assertTrue(all(c in run.PR_CASES for c in reviews.CASES))
        self.assertTrue(all(plain.PLAIN.get(c) for c in reviews.CASES))


if __name__ == "__main__":
    unittest.main(verbosity=2)
