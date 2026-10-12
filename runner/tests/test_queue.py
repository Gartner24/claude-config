"""Spec 0011: the build queue inside one repo, queue.json and park memory."""
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run  # noqa: E402
import wf  # noqa: E402
from test_park import GIT_ID  # noqa: E402
from test_run import WF, FakeNtfy, RunCase, ask, write_config  # noqa: E402

TWO = """# Scope: x
**Autopilot:** allowed

### 1. A · auto
- [x] Design it (spec): `/architect a`
- [ ] `/develop a`

### 2. B · auto
- [x] (spec)
- [ ] `/develop b`
"""
TICK_B = {"tick": False, "edit": [["- [ ] `/develop b`", "- [x] `/develop b`"]]}
DONE_B = {"tick": False, "edit": [["### 2. B · auto", "### 2. B · done · auto"]]}
TICK_A = {"tick": False, "edit": [["- [ ] `/develop a`", "- [x] `/develop a`"]]}
DONE_A = {"tick": False, "edit": [["### 1. A · auto", "### 1. A · done · auto"]]}


def blocked(text="test park", **extra):
    return {"tick": False, "json": {"result": f"Stuck.\nBLOCKED: {text}\n"}, **extra}


class QueueCase(RunCase):
    def commit(self, repo):
        subprocess.run(["git", *GIT_ID, "-C", str(repo), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", *GIT_ID, "-C", str(repo), "commit", "-qm", "x"], check=True, capture_output=True)

    def queue(self):
        p = self.state / "wf" / "queue.json"
        return json.loads(p.read_text()) if p.exists() else None

    def again(self):
        """A fresh run folder and call count; queue.json stays."""
        shutil.rmtree(self.state / "wf" / "runs", ignore_errors=True)
        for f in [self.fakes / "count", *self.calls()]:
            f.unlink(missing_ok=True)

    def section_sha(self, repo, name):
        _, feats = run.repo_features(str(repo), "docs/scope")
        return next(f.sha for f in feats if f.name == name)


class TestDoneWhen(QueueCase):
    # covers: AC-8, AC-9, AC-10, AC-18, AC-19 (the first parks blocked with a clean tree, the second still builds)
    def test_park_then_next(self):
        repo = self.make_repo("two", TWO)
        self.commit(repo)
        self.steps([blocked(), TICK_B, DONE_B])
        r = self.wf("two", "-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[:3], ["two on work, 0 changes", "  queued: 1. A", "  queued: 2. B"])
        self.assertIn("parked: 1. A: blocked: test park", lines)
        self.assertEqual(lines[-3:-1], ["done: 2. B", "queue done: 1 done, 1 parked, 0 open"])
        folder, rec = self.run_record()
        self.assertEqual([(e["n"], e["feature"], e["outcome"], e["detail"], e["calls"]) for e in rec["features"]],
                         [(1, "1. A", "blocked", "test park", [1]), (2, "2. B", "feature_done", None, [2, 3])])
        self.assertEqual([(c["command"], c["feature"]) for c in rec["calls"]],
                         [("/develop a", 1), ("/develop b", 2), ("/sync", 2)])
        q = self.queue()
        self.assertEqual(q["decisions"], [])
        park = q["parks"][0]
        self.assertEqual(sorted(park), ["cap", "detail", "feature", "parked_at", "reason", "repo", "run", "section_sha"])
        self.assertEqual((park["repo"], park["feature"], park["reason"], park["detail"], park["cap"], park["run"]),
                         (str(repo), "1. A", "blocked", "test park", None, str(folder)))
        self.assertEqual(park["section_sha"], self.section_sha(repo, "1. A"))
        self.assertEqual(os.stat(self.state / "wf" / "queue.json").st_mode & 0o777, 0o600)


class TestQueueRules(QueueCase):
    # covers: AC-2, AC-3 (only a tagged feature with every decision box ticked is queued, file order kept;
    # a box check is a skip in the plan, never a record)
    def test_rules(self):
        text = ("# Scope: x\n**Autopilot:** allowed\n"
                "### 1. No tag\n- [x] (spec)\n- [ ] `/develop a`\n"
                "### 2. Unticked spec · auto\n- [ ] Design it (spec): `/architect b`\n- [ ] `/develop b`\n"
                "### 3. Skipped spec · auto\n- [x] Design it (spec): `/architect c` · skipped\n- [ ] `/develop c`\n"
                "### 4. No decision box · auto\n- [ ] `/develop d`\n"
                "### 5. Gone · done · auto\n- [x] (spec)\n- [ ] `/develop e`\n"
                "### 6. Merge · auto-merge\n- [x] (spec)\n- [ ] `/develop f`\n"
                "### 7. Twin · auto\n- [x] (spec)\n- [ ] `/develop g`\n"
                "### 8. Valid · in-progress · auto\n- [x] Design it (spec): `/architect h`\n"
                "- [x] Data (spec)\n- [ ] `/develop h`\n"
                "### 7. Twin · in-progress · auto\n- [x] (spec)\n- [ ] `/develop i`\n"
                "### 9. Arch · auto\n- [x] (spec)\n- [ ] `/architect j`\n"
                "### 10. Later · auto\n- [x] (spec)\n- [ ] `/develop k`\n   - [ ] waits on the merge\n"
                "### 11. Owed · auto\n- [x] (spec)\n- [ ] phone check · waits on you\n"
                "### 12. Two specs · auto\n- [x] (spec)\n- [ ] Data (spec)\n- [ ] `/develop m`\n"
                "## Deferred\n### 13. Later still · auto\n- [x] (spec)\n- [ ] `/develop n`\n")
        self.make_repo("rules", text)
        r = self.wf("rules")
        self.assertEqual(r.returncode, 130, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[1:7], [
            "  skip: 7. Twin: ambiguous_feature", "  queued: 8. Valid", "  skip: 7. Twin: ambiguous_feature",
            "  skip: 9. Arch: manual_box", "  skip: 10. Later: waiting", "  skip: 11. Owed: waiting"])
        self.assertTrue(r.stdout.splitlines()[7].startswith("caps: "))
        self.assertIsNone(self.queue())


class TestSections(unittest.TestCase):
    # covers: AC-3 (a heading in a fence or a comment is not a section; a section ends at a level 1 to 3
    # heading; raw lines keep comments, so a comment edit changes the hash; the Deferred flag)
    def test_sections(self):
        text = ("# T\n### 1. A · auto\n- [x] (spec)\n```\n### not\n```\n<!-- note\n### hidden\n-->\n#### sub\n- [ ] `/x`\n"
                "## Deferred\n### 2. B\n- [ ] y\n# Top\n### 3. C\n")
        got = wf.sections(text)
        self.assertEqual([(h, d) for h, _, _, d in got], [("1. A · auto", False), ("2. B", True), ("3. C", True)])
        self.assertEqual(got[0][1], ["### 1. A · auto", "- [x] (spec)", "```", "### not", "```", "<!-- note",
                                     "### hidden", "-->", "#### sub", "- [ ] `/x`"])
        self.assertEqual(got[0][2][5:8], ["", "", ""])
        self.assertEqual(got[2][1], ["### 3. C", ""])
        a = run.Feature(*got[0])
        self.assertEqual((a.name, a.queued, a.next.command), ("1. A", True, "/x"))
        edited = run.Feature(*wf.sections(text.replace("<!-- note", "<!-- notes"))[0])
        self.assertNotEqual(edited.sha, a.sha)
        self.assertEqual(run.Feature(*wf.sections(text)[0]).sha, a.sha)
        self.assertFalse(run.Feature(*got[1]).queued)


class TestEpicSplit(QueueCase):
    # covers: AC-2, AC-3 (an epic split queues in load_scope order and hashes each file's sections alone)
    def test_split(self):
        repo = self.make_repo("big", "x")
        d = repo / "docs" / "scope"
        (d / "scope.md").unlink()
        (d / "index.md").write_text("# Scope: big\n**Autopilot:** allowed\n\n[two](two.md) [one](one.md)\n")
        (d / "one.md").write_text("### 1. One · auto\n- [x] (spec)\n- [ ] `/develop one`\n")
        (d / "two.md").write_text("### 2. Two · auto\n- [x] (spec)\n- [ ] `/develop two`\n")
        _, feats = run.repo_features(str(repo), "docs/scope")
        self.assertEqual([f.name for f in feats], ["2. Two", "1. One"])
        before = feats[1].sha
        (d / "two.md").write_text((d / "two.md").read_text() + "more\n")
        self.assertEqual(run.repo_features(str(repo), "docs/scope")[1][1].sha, before)
        r = self.wf("big")
        self.assertEqual(r.stdout.splitlines()[1:3], ["  queued: 2. Two", "  queued: 1. One"])


class TestSyncOwed(QueueCase):
    # covers: AC-2, AC-8 (every box ticked before /sync ran: the next run shows sync owed and runs only /sync)
    def test_sync_owed(self):
        self.make_repo("owed", "# Scope: x\n**Autopilot:** allowed\n### 1. A · auto\n- [x] (spec)\n- [x] `/develop a`\n"
                               "### 2. B\n- [ ] `/develop b`\n")
        self.steps([DONE_A])
        r = self.wf("owed", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("  sync owed: 1. A\n", r.stdout)
        _, rec = self.run_record()
        self.assertEqual([(c["command"], c["kind"]) for c in rec["calls"]], [("/sync", "sync")])
        self.assertEqual(rec["features"][0]["outcome"], "feature_done")


class TestFeatureBoundary(QueueCase):
    # covers: AC-8 (the feature ends when it has no open box; an earlier feature's open box is never run)
    def test_boundary(self):
        self.make_repo("edge", "# Scope: x\n**Autopilot:** allowed\n### 1. Early\n- [ ] `/develop early`\n"
                               "### 2. B · auto\n- [x] (spec)\n- [ ] `/develop b`\n")
        self.steps([TICK_B, DONE_B])
        r = self.wf("edge", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual([c["command"] for c in rec["calls"]], ["/develop b", "/sync"])
        self.assertIn("next: /sync", r.stdout)


class TestTreeRule(QueueCase):
    # covers: AC-7 (dirty with a park blocks the next feature; clean lets it start; dirty with no record lets
    # the first start; a failed git status reads dirty)
    def test_dirty_with_parks(self):
        repo = self.make_repo("tree", TWO)
        self.commit(repo)
        self.steps([blocked(write_file=[["notes.txt", "x"]])])
        r = self.wf("tree", "-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual(len(rec["calls"]), 1)
        self.assertEqual(r.stdout.splitlines()[-2], "queue done: 0 done, 1 parked, 0 open")
        self.again()
        r = self.wf("tree")
        self.assertEqual(r.stdout.splitlines()[1:3], ["  parked: 1. A: blocked: test park (wf unpark to retry)",
                                                      "  skip: 2. B: dirty with parks"])
        self.assertEqual(r.stdout.splitlines()[-1], "nothing to run")
        self.assertEqual(r.returncode, 6)
        self.commit(repo)
        self.assertFalse(run.dirty(str(repo)))
        self.steps([TICK_B, DONE_B])
        r = self.wf("tree", "-y")
        self.assertIn("done: 2. B", r.stdout)
        # A dirty tree with no record: the default fixture repo is never committed, and every other test starts there.
        self.assertTrue(run.dirty(str(self.repo)))
        self.assertTrue(run.dirty(str(self.tmp / "fakes")))
        self.assertTrue(run.dirty(str(self.tmp / "nowhere")))


class TestParkMemory(QueueCase):
    # covers: AC-3, AC-10, AC-19 (a park is skipped by the next run, a section edit clears it, nothing left exits 0)
    def test_edit_clears(self):
        repo = self.make_repo("mem", TWO)
        self.commit(repo)
        self.steps([blocked(), TICK_B, DONE_B])
        self.wf("mem", "-y")
        self.again()
        r = self.wf("mem", "-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[1:2], ["  parked: 1. A: blocked: test park (wf unpark to retry)"])
        self.assertEqual(self.calls(), [])
        scope = repo / "docs" / "scope" / "scope.md"
        scope.write_text(scope.read_text().replace("- [ ] `/develop a`", "- [ ] `/develop a` "))
        self.again()
        self.steps([TICK_A, DONE_A])
        r = self.wf("mem", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("  queued: 1. A\n", r.stdout)
        self.assertEqual(self.queue()["parks"], [])

    # covers: AC-3, AC-10 (a cap park records its cap and clears only with a higher value for that cap)
    def test_cap(self):
        self.make_repo("cap", TWO)
        self.steps([{"tick": False, "json": {"subtype": "error_max_budget_usd", "is_error": True}}, TICK_B, DONE_B])
        self.wf("cap", "-y", "--budget", "1")
        park = self.queue()["parks"][0]
        self.assertEqual((park["reason"], park["cap"]), ("budget", 1))
        self.again()
        r = self.wf("cap", "--budget", "1")
        self.assertIn("  parked: 1. A: budget: error_max_budget_usd (wf unpark to retry)\n", r.stdout)
        r = self.wf("cap", "--budget", "1.5")
        self.assertIn("  queued: 1. A\n", r.stdout)
        # The plan alone never deletes a record.
        self.assertEqual(len(self.queue()["parks"]), 1)

    # covers: AC-10 (call_error writes no record; the next run retries the feature)
    def test_call_error(self):
        self.make_repo("err", TWO)
        self.steps([{"tick": False, "rc": 1}, {"tick": False, "rc": 1}, TICK_B, DONE_B])
        r = self.wf("err", "-y")
        self.assertIn("parked: 1. A: call_error: ", r.stdout)
        self.assertEqual(r.returncode, 6)
        self.assertIsNone(self.queue())
        self.again()
        self.steps([TICK_A, DONE_A])
        r = self.wf("err", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("done: 1. A", r.stdout)


class TestCapsPerFeature(QueueCase):
    # covers: AC-16 (--max-calls and the two debug attempts count per feature)
    def test_max_calls(self):
        repo = self.make_repo("caps", TWO.replace("- [ ] `/develop a`", "- [ ] `/develop a`\n- [ ] `/test a`")
                              .replace("- [ ] `/develop b`", "- [ ] `/develop b`\n- [ ] `/test b`"))
        self.commit(repo)
        # The ticks would make the tree dirty, and dirty with a park blocks feature 2 (AC-7).
        subprocess.run(["git", "-C", str(repo), "update-index", "--assume-unchanged", "docs/scope/scope.md"], check=True)
        tick = lambda box: {"tick": False, "edit": [[f"- [ ] `{box}`", f"- [x] `{box}`"]]}
        self.steps([tick("/develop a"), tick("/test a"), tick("/develop b"), tick("/test b")])
        r = self.wf("caps", "-y", "--max-calls", "2")
        _, rec = self.run_record()
        self.assertEqual([(e["outcome"], e["counted"]) for e in rec["features"]], [("max_calls", 2)] * 2)
        self.assertIn("[2/2] caps: /test b", r.stdout)

    def test_debug(self):
        repo = self.make_repo("dbg", TWO.replace("/develop a", "/check verify a").replace("/develop b", "/check verify b"))
        self.commit(repo)
        fail = {"tick": False, "json": {"result": "VERIFY FAIL: debug"}}
        self.steps([fail, {"tick": False}] * 2 + [fail] + [fail, {"tick": False}] * 2 + [fail])
        r = self.wf("dbg", "-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        _, rec = self.run_record()
        self.assertEqual([(e["outcome"], e["debug_attempts"], len(e["calls"])) for e in rec["features"]],
                         [("verify_failed", 2, 5)] * 2)


class TestStateFile(QueueCase):
    # covers: AC-17 (a broken file refuses queue_unreadable and is never overwritten)
    def test_unreadable(self):
        p = self.state / "wf" / "queue.json"
        p.parent.mkdir(parents=True)
        park = {"repo": "/r", "feature": "1. A", "section_sha": "a" * 64, "reason": "blocked", "detail": None,
                "cap": None, "run": "/x", "parked_at": "t"}
        dec = {"id": "ab12", "repo": "/r", "feature": "1. A", "branch": "w", "session_id": "s", "call_kind": "box",
               "command": "/develop a", "box_text": None, "question": "q", "options": [], "kind": "prose", "multi": False,
               "sent": None, "pings": [], "acks": [], "asked": "t", "answer": None, "source": None, "answered": None,
               "ignored": 0, "run": "/x"}
        for name, text in [("not json", "{broken"), ("version 2", '{"version": 2, "parks": [], "decisions": []}'),
                           ("two parks", json.dumps({"version": 1, "parks": [park, park], "decisions": []})),
                           ("same id", json.dumps({"version": 1, "parks": [], "decisions": [
                               dec, {**dec, "feature": "2. B"}]})),
                           ("bad reason", json.dumps({"version": 1, "parks": [{**park, "reason": "call_error"}],
                                                      "decisions": []})),
                           ("bool cap", json.dumps({"version": 1, "parks": [{**park, "cap": True}], "decisions": []})),
                           ("bad id", json.dumps({"version": 1, "parks": [], "decisions": [{**dec, "id": "AB12"}]}))]:
            with self.subTest(name):
                p.write_text(text)
                r = self.wf("demo", "-y")
                self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
                self.assertIn(f"refused: queue_unreadable: {p}", r.stdout)
                self.assertEqual(p.read_text(), text)
                self.assertEqual(self.calls(), [])
        p.write_text(json.dumps({"version": 1, "parks": [park], "decisions": [dec]}))
        self.assertEqual(run.queue_problem(json.loads(p.read_text())), None)

    # covers: AC-17 (a failed write mid run stops internal_error, exit 6, the file as last written)
    def test_write_failure(self):
        self.make_repo("wfail", TWO)
        (self.state / "wf").mkdir(parents=True)
        (self.state / "wf" / "queue.json.tmp").mkdir()
        self.steps([blocked()])
        r = self.wf("wfail", "-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn("stopped: internal_error: ", r.stdout)
        _, rec = self.run_record()
        self.assertEqual((rec["stop_reason"], len(rec["calls"])), ("internal_error", 1))
        self.assertFalse((self.state / "wf" / "queue.json").exists())


ONE = "# Scope: x\n**Autopilot:** allowed\n\n### 1. A · auto\n- [x] (spec)\n- [ ] `/develop a`\n"


class DecisionCase(QueueCase):
    def setUp(self):
        super().setUp()
        self.ntfy = FakeNtfy()
        self.addCleanup(self.ntfy.close)
        write_config(self.tmp / "config", self.ntfy.url, codes=[f"code{i:04d}" for i in range(5)])

    def keep_queue(self, name):
        """A fake call step that copies queue.json to the fakes folder as it is during that call."""
        src, dst = self.state / "wf" / "queue.json", self.fakes / name
        return [sys.executable, "-c", f"import shutil; shutil.copy({str(src)!r}, {str(dst)!r})"]

    def set_decision(self, **fields):
        p = self.state / "wf" / "queue.json"
        q = json.loads(p.read_text())
        q["decisions"][0].update(fields)
        p.write_text(json.dumps(q))
        return q["decisions"][0]

    def open_one(self, repo_name):
        """A first run whose only feature asks and whose end wait runs out: the Decision stays open."""
        self.steps([ask()])
        r = self.wf(repo_name, "-y", "--max-wait", "0.0001", mode="fast")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.again()
        return self.queue()["decisions"][0]


class TestDecisionMoveOn(DecisionCase):
    # covers: AC-7, AC-11, AC-12, AC-13 (feature 1 asks and the run moves on; the reply comes during feature 2;
    # feature 1 resumes after it with its own session; the record leaves only after the resume is classified)
    def test_move_on(self):
        repo = self.make_repo("two", TWO)
        self.commit(repo)
        self.ntfy.replies = ["{id} 1"]
        self.steps([ask(), TICK_B, DONE_B, {**TICK_A, "run": [self.keep_queue("during-resume.json")]}, DONE_A])
        r = self.wf("two", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        folder, rec = self.run_record()
        d = rec["decisions"][0]
        i = d["id"]
        lines = r.stdout.splitlines()
        self.assertEqual(lines[lines.index(f"open: {i} 1. A") + 1:][:3], [
            "[1/20] two: /develop b -> success, 0.50 USD, 0.0m, next: /sync", f"answered: {i} Postgres (recommended) (phone)",
            "[2/20] two: /sync -> success, 0.50 USD, 0.0m, next: -"])
        self.assertIn(f"[2/20] two: /develop a (resume {i}) -> success, 0.50 USD, 0.0m, next: /sync", lines)
        self.assertEqual(lines[-2], "queue done: 2 done, 0 parked, 0 open")
        self.assertEqual(self.argv(4)["argv"][:4], ["-p", run.ANSWERED + "Postgres (recommended)", "--resume", "s-1"])
        self.assertEqual(self.argv(4)["argv"][4:], self.argv(1)["argv"][2:])
        self.assertEqual([(e["feature"], e["outcome"], e["calls"], e["counted"]) for e in rec["features"]],
                         [("1. A", "feature_done", [1, 4, 5], 3), ("2. B", "feature_done", [2, 3], 2)])
        self.assertEqual((d["call"], d["resumed_in"], d["source"], d["sent"]), (1, 4, "phone", self.ntfy.posts[0]["message"]))
        self.assertEqual([c["resumes"] for c in rec["calls"]], [[], [], [], [i], []])
        during = json.loads((self.fakes / "during-resume.json").read_text())["decisions"]
        self.assertEqual(len(during), 1)
        self.assertEqual({k: during[0][k] for k in ("id", "repo", "feature", "branch", "session_id", "call_kind", "command",
                                                     "box_text", "kind", "answer", "source", "run")},
                         {"id": i, "repo": str(repo), "feature": "1. A", "branch": "work", "session_id": "s-1",
                          "call_kind": "box", "command": "/develop a", "box_text": "`/develop a`", "kind": "panel",
                          "answer": "Postgres (recommended)", "source": "phone", "run": str(folder)})
        self.assertEqual(len(during[0]["pings"]), 1)
        self.assertEqual(len(during[0]["acks"]), 1)
        self.assertEqual(self.ntfy.posts[1]["message"], f"{i} accepted")
        self.assertEqual(self.queue()["decisions"], [])

    # covers: AC-11 (a first ping failing three times stops the run ping_failed; the record stays with sent null)
    def test_ping_failed(self):
        self.make_repo("pf", ONE)
        self.ntfy.fail_posts = 3
        self.steps([ask()])
        r = self.wf("pf", "-y", mode="fast")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn("stopped: ping_failed: ", r.stdout)
        d = self.queue()["decisions"][0]
        self.assertEqual((d["sent"], d["pings"], d["feature"]), (None, [], "1. A"))


class TestAcrossRuns(DecisionCase):
    # covers: AC-12, AC-13, AC-15 (an open Decision outlives its run; the next run's poll from its asked time
    # takes the reply, keeps the first of two, skips the ids in pings and acks, warns once on failed polls)
    def test_reply_next_run(self):
        repo = self.make_repo("later", ONE)
        self.commit(repo)
        d = self.open_one("later")
        i = d["id"]
        # A message listed in acks would be a rejected reply; it must not count.
        mid = self.ntfy.add(f"{i} 9")
        self.set_decision(acks=[mid])
        self.ntfy.replies = ["{id} 2", "{id} 1"]
        self.ntfy.fail_polls = 2
        self.steps([TICK_A, DONE_A])
        n = len(self.ntfy.polls)
        r = self.wf("later", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"  open: {i} 1. A: Which storage engine?\n", r.stdout)
        self.assertEqual(r.stdout.count("warning: ntfy poll failed"), 1)
        self.assertTrue(self.ntfy.polls[n].endswith(f"since={int(run.asked_at(d))}"), self.ntfy.polls[n])
        self.assertEqual(self.argv(1)["argv"][:4], ["-p", run.ANSWERED + "SQLite", "--resume", "s-1"])
        _, rec = self.run_record()
        e = rec["decisions"][0]
        self.assertEqual((e["id"], e["call"], e["resumed_in"], e["answer"], e["ignored"]), (i, None, 1, "SQLite", 1))
        self.assertEqual(self.queue()["decisions"], [])

    # covers: AC-13 (an answered Decision on another branch is dropped stale and the feature starts fresh)
    def test_stale_branch(self):
        repo = self.make_repo("st", ONE)
        self.commit(repo)
        i = self.open_one("st")["id"]
        self.set_decision(answer="x", source="phone", answered="t", branch="old")
        self.steps([TICK_A, DONE_A])
        r = self.wf("st", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[1:3], [f"  stale: {i} 1. A", "  queued: 1. A"])
        self.assertIn(f"\nstale: {i} 1. A\n", r.stdout)
        self.assertNotIn("--resume", self.argv(1)["argv"])
        self.assertEqual(self.queue()["decisions"], [])

    # covers: AC-13 (a resume still failing after its retry is dropped stale and parks call_error, unrecorded)
    def test_resume_fails(self):
        repo = self.make_repo("rf", ONE)
        self.commit(repo)
        i = self.open_one("rf")["id"]
        self.set_decision(answer="Postgres", source="phone", answered="t")
        self.steps([{"tick": False, "rc": 1}])
        r = self.wf("rf", "-y", mode="fast")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertEqual(len(self.calls()), 2)
        self.assertIn("--resume", self.argv(2)["argv"])
        self.assertIn(f"\nstale: {i} 1. A\nparked: 1. A: call_error: ", r.stdout)
        self.assertEqual(self.queue(), {"version": 1, "parks": [], "decisions": []})

    # covers: AC-13 (Ctrl C during a resume keeps the record for the next run)
    def test_interrupt_keeps(self):
        repo = self.make_repo("ik", ONE)
        self.commit(repo)
        i = self.open_one("ik")["id"]
        self.set_decision(answer="Postgres", source="phone", answered="t")
        self.steps([{"tick": False, "sleep": 60}])
        p = self.start("ik", "-y", mode="fast")
        self.wait_for(self.fakes / "argv-1.json")
        p.send_signal(subprocess.signal.SIGINT)
        out, err = p.communicate(timeout=30)
        self.assertEqual(p.returncode, 130, out + err)
        self.assertEqual([(d["id"], d["answer"]) for d in self.queue()["decisions"]], [(i, "Postgres")])

    # covers: AC-15 (the end wait polls until the reply comes, then resumes)
    def test_end_wait_polls(self):
        self.make_repo("ew", ONE)
        self.ntfy.hold_polls = 3
        self.ntfy.replies = ["{id} 1"]
        self.steps([ask(), TICK_A, DONE_A])
        r = self.wf("ew", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertGreaterEqual(len(self.ntfy.polls), 4)
        _, rec = self.run_record()
        self.assertEqual([c["resumes"] != [] for c in rec["calls"]], [False, True, False])


class TestReping(DecisionCase):
    # covers: AC-14 (every unanswered Decision is pinged again right after the confirm with its same id and body;
    # a failed re-ping warns and the run goes on, a null sent gets the body; the reply then resumes it)
    def test_reping(self):
        repo = self.make_repo("rp", ONE)
        self.commit(repo)
        d = self.open_one("rp")
        first = self.ntfy.posts[0]
        r = self.wf("rp", "-y", "--max-wait", "0.0001", mode="fast")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.ntfy.posts[-1], first)
        q = self.queue()["decisions"][0]
        self.assertEqual((q["id"], len(q["pings"]), q["sent"]), (d["id"], 2, d["sent"]))
        self.again()
        self.set_decision(sent=None)
        self.ntfy.fail_posts = 3
        r = self.wf("rp", "-y", "--max-wait", "0.0001", mode="fast")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn(f"warning: re-ping {d['id']} failed: ", r.stdout)
        self.assertIn("queue done: 0 done, 0 parked, 0 open", r.stdout)
        q = self.queue()["decisions"][0]
        self.assertEqual((len(q["pings"]), q["sent"]), (2, d["sent"]))
        self.again()
        self.ntfy.replies = ["{id} 1"]
        self.steps([TICK_A, DONE_A])
        r = self.wf("rp", "-y", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.argv(1)["argv"][:4], ["-p", run.ANSWERED + "Postgres (recommended)", "--resume", "s-1"])
        self.assertEqual(self.queue()["decisions"], [])


class TestAcrossRepos(QueueCase):
    def trust(self, *paths):
        (self.tmp / "config" / "wf" / "allowed.json").write_text(json.dumps([str(p) for p in paths]))

    def lock(self, repo):
        return self.state / "wf" / "locks" / (run.hashlib.sha1(str(repo).encode()).hexdigest() + ".lock")

    # covers: AC-1, AC-4, AC-6 (bare wf run takes the trust list in file order, once per real path; missing, hub and
    # unreadable scopes are skips; a missing or broken trust file refuses untrusted)
    def test_trust_list(self):
        a = self.make_repo("alpha", ONE)
        self.commit(a)
        hub = self.make_repo("hubrepo", "# Scope: hub\n\n| a | b |\n")
        bad = self.make_repo("bad", ONE)
        (bad / "docs" / "scope" / "scope.md").chmod(0)
        (self.tmp / "alias").symlink_to(a)
        self.trust(self.tmp / "gone", hub, bad, a, self.tmp / "alias")
        self.steps([TICK_A, DONE_A])
        r = self.wf("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[:2], [f"{self.tmp}/gone", "  skip: missing: no folder or no scope"])
        self.assertTrue(lines[2].startswith("hubrepo on work, "), lines[2])
        self.assertEqual(lines[3], "  skip: hub: hubrepo is a hub scope with no boxes of its own")
        self.assertEqual(lines[4:8], [str(bad), f"  skip: scope_unreadable: [Errno 13] Permission denied: "
                                                f"'{bad}/docs/scope/scope.md'", "alpha on work, 0 changes", "  queued: 1. A"])
        self.assertTrue(lines[8].startswith("caps: "))
        _, rec = self.run_record()
        self.assertEqual([(e["repo"], e["skip"] and e["skip"].split(":")[0]) for e in rec["repos"]],
                         [(f"{self.tmp}/gone", "missing"), (str(hub), "hub"), (str(bad), "scope_unreadable"), (str(a), None)])
        self.assertEqual([c["command"] for c in rec["calls"]], ["/develop a", "/sync"])
        self.assertIn("run folder: " + str(self.state / "wf" / "runs" / "queue-"), r.stdout)
        for text in (None, "{not json"):
            with self.subTest(text):
                p = self.tmp / "config" / "wf" / "allowed.json"
                if text is None:
                    p.unlink()
                else:
                    p.write_text(text)
                r = self.wf("-y")
                self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
                self.assertIn("refused: untrusted: ", r.stdout)

    # covers: AC-4, AC-5, AC-6 (in bare form a repo on main, one with Autopilot off and one locked show skip lines
    # and the fourth runs; every repo skipped by a refusal exits 5 with nothing to run; skips that are not refusals
    # exit per AC-19)
    def test_repo_checks(self):
        main = self.make_repo("onmain", ONE, head="ref: refs/heads/main\n")
        off = self.make_repo("apoff", ONE.replace("allowed", "off"))
        held = self.make_repo("held", ONE)
        good = self.make_repo("good", ONE)
        self.commit(good)
        self.lock(held).parent.mkdir(parents=True, mode=0o700)
        fd = os.open(self.lock(held), os.O_RDWR | os.O_CREAT, 0o600)
        self.addCleanup(os.close, fd)
        run.fcntl.flock(fd, run.fcntl.LOCK_EX)
        os.write(fd, b"4242 2026-10-11T09:00:00+02:00\n")
        self.trust(main, off, held, good)
        self.steps([TICK_A, DONE_A])
        r = self.wf("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[:8], [
            "onmain on main, 1 change", "  skip: branch: main, switch to a work branch first",
            "apoff on work, 1 change", "  skip: autopilot_off: Autopilot is off, the scope header needs **Autopilot:** allowed",
            "held on work, 1 change", "  skip: locked: 4242 2026-10-11T09:00:00+02:00",
            "good on work, 0 changes", "  queued: 1. A"])
        self.assertIn("done: 1. A", r.stdout)
        self.again()
        self.trust(main, off)
        r = self.wf("-y")
        self.assertEqual((r.returncode, r.stdout.splitlines()[-1]), (5, "nothing to run"), r.stdout + r.stderr)
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.state / "wf" / "runs").exists())
        self.trust(self.tmp / "gone", self.make_repo("hubrepo", "# Scope: hub\n\n| a | b |\n"))
        r = self.wf("-y")
        self.assertEqual((r.returncode, r.stdout.splitlines()[-1]), (0, "nothing to run"), r.stdout + r.stderr)

    # covers: AC-5, AC-9 (Autopilot turned off in repo A ends A only, its lock kept while repo B runs to done)
    def test_repo_stop(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(a, b)
        out = self.fakes / "lock-a"
        probe = (f"import fcntl, os\nfd = os.open({str(self.lock(a))!r}, os.O_RDWR)\ntry:\n"
                 f"    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n    r = 'free'\nexcept BlockingIOError:\n"
                 f"    r = 'held'\nopen({str(out)!r}, 'w').write(r)\n")
        self.steps([{"edit": [["**Autopilot:** allowed", "**Autopilot:** off"]]},
                    {**TICK_A, "run": [[sys.executable, "-c", probe]]}, DONE_A])
        r = self.wf("-y")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn("\nstopped repo ra: autopilot_off: Autopilot is now off\n", r.stdout)
        self.assertEqual(r.stdout.splitlines()[-2], "queue done: 1 done, 0 parked, 0 open")
        self.assertEqual(out.read_text(), "held")
        _, rec = self.run_record()
        self.assertEqual([(e["name"], e["ended"]) for e in rec["repos"]], [("ra", "autopilot_off"), ("rb", None)])
        self.assertEqual([(e["repo"], e["outcome"]) for e in rec["features"]],
                         [(str(a), "autopilot_off"), (str(b), "feature_done")])
        self.assertEqual([c["feature"] for c in rec["calls"]], [1, 2, 2])

    # covers: AC-9 (guard_changed scope: a repo's own settings end that repo, whether it is the one running or
    # another; ~/.claude settings and a git config two held worktrees share stop the run)
    def test_guard_scope(self):
        detail = " changed during the run; inspect or delete it before opening a session in this repo"
        with self.subTest("own file of the running repo"):
            a, b = self.make_repo("oa", ONE), self.make_repo("ob", ONE)
            self.trust(a, b)
            self.steps([{"write_file": [[".claude/settings.json", "{}"]]}, TICK_A, DONE_A])
            r = self.wf("-y")
            self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
            self.assertIn(f"\nstopped repo oa: guard_changed: {a}/.claude/settings.json{detail}\n", r.stdout)
            self.assertIn("done: 1. A", r.stdout)
            self.assertEqual(self.run_record()[1]["stop_reason"], "queue_done")
        with self.subTest("own file of another held repo"):
            self.again()
            a, b = self.make_repo("pa", ONE), self.make_repo("pb", ONE)
            self.trust(a, b)
            self.steps([{"write_file": [[f"{b}/.claude/settings.local.json", "{}"]]}, DONE_A])
            r = self.wf("-y")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn(f"\nstopped repo pb: guard_changed: {b}/.claude/settings.local.json{detail}\n", r.stdout)
            _, rec = self.run_record()
            self.assertEqual([(e["name"], e["ended"]) for e in rec["repos"]], [("pa", None), ("pb", "guard_changed")])
            self.assertEqual([(e["repo"], e["outcome"]) for e in rec["features"]], [(str(a), "feature_done")])
        with self.subTest("shared git common dir"):
            self.again()
            a = self.make_repo("wa", ONE)
            self.commit(a)
            w = self.tmp / "root" / "wb"
            subprocess.run(["git", *GIT_ID, "-C", str(a), "worktree", "add", "-q", "-b", "wtb", str(w)],
                           check=True, capture_output=True)
            self.trust(a, w)
            self.steps([{"write_file": [[".git/config", "{}"]]}, {}])
            r = self.wf("-y")
            self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
            self.assertIn(f"\nstopped: guard_changed: {a}/.git/config{detail}\n", r.stdout)
        with self.subTest("user settings"):
            self.again()
            a, b = self.make_repo("ua", ONE), self.make_repo("ub", ONE)
            self.trust(a, b)
            self.steps([{"write_file": [[f"{self.tmp}/.claude/settings.json", "{}"]]}, {}])
            r = self.wf("-y")
            self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
            self.assertIn(f"\nstopped: guard_changed: {self.tmp}/.claude/settings.json{detail}\n", r.stdout)
            self.assertEqual(len(self.run_record()[1]["calls"]), 1)


class TestNestedRepo(QueueCase):
    # covers: AC-9, spec 0007 AC-7 (the outer repo's last call rewrites a nested held repo's git config: the guard
    # check at the pick ends the nested repo before wf runs any git there)
    def test_no_git_after_write(self):
        outer = self.make_repo("outer", ONE.replace("- [ ] `/develop a`", "- [x] `/develop a`"))
        inner = self.make_repo("outer/inner", ONE)
        (self.tmp / "config" / "wf" / "allowed.json").write_text(json.dumps([str(outer), str(inner)]))
        log = self.fakes / "git-log"
        (self.bin / "git").unlink()
        self.fake("git", f'#!/bin/sh\necho "$@" >> {log}\nexec {shutil.which("git")} "$@"\n')
        mark = [sys.executable, "-c", f"open({str(log)!r}, 'a').write('WRITE\\n')"]
        config = (inner / ".git" / "config").read_text() + "# moved\n"
        self.steps([{**DONE_A, "write_file": [[f"{inner}/.git/config", config]], "run": [mark]}])
        r = self.wf("-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("  sync owed: 1. A\n", r.stdout)
        self.assertIn(f"\nstopped repo inner: guard_changed: {inner}/.git/config changed during the run; ", r.stdout)
        self.assertNotIn(f"-C {inner} ", log.read_text().split("WRITE\n", 1)[1])
        self.assertEqual(len(self.run_record()[1]["calls"]), 1)
        self.assertIn("done: 1. A", r.stdout)


class TestExit(QueueCase):
    # covers: AC-19 (nothing to run with no record exits 0; with an old park 6; a park left after the run 6)
    def test_codes(self):
        self.make_repo("plain", "# Scope: x\n**Autopilot:** allowed\n### 1. A\n- [ ] `/develop a`\n")
        r = self.wf("plain", "-y")
        self.assertEqual((r.returncode, r.stdout.splitlines()[-1]), (0, "nothing to run"))


def park(repo, feature, sha="a" * 64, **extra):
    return {"repo": str(repo), "feature": feature, "section_sha": sha, "reason": "blocked", "detail": "test park",
            "cap": None, "run": "/x", "parked_at": "2026-10-12T09:00:00+02:00", **extra}


def decision(repo, feature, did="ab12", **extra):
    return {"id": did, "repo": str(repo), "feature": feature, "branch": "work", "session_id": "s", "call_kind": "box",
            "command": "/develop c", "box_text": "`/develop c`", "question": "Which storage engine?",
            "options": ["Postgres (recommended)", "SQLite"], "kind": "panel", "multi": False, "sent": None,
            "pings": [], "acks": [], "asked": "2026-10-12T09:00:00+02:00", "answer": None, "source": None,
            "answered": None, "ignored": 0, "run": "/x", **extra}


class SubcommandCase(QueueCase):
    def sub(self, *args):
        return subprocess.run([sys.executable, str(WF), *args], capture_output=True, text=True, env=self.env, timeout=60)

    def write_queue(self, parks, decisions):
        p = self.state / "wf" / "queue.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"version": 1, "parks": parks, "decisions": decisions}))
        return p

    def hold(self, repo):
        lock = self.state / "wf" / "locks" / (run.hashlib.sha1(str(repo).encode()).hexdigest() + ".lock")
        lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        run.fcntl.flock(fd, run.fcntl.LOCK_EX)
        os.write(fd, b"4242 2026-10-11T09:00:00+02:00\n")
        return fd, lock


THREE = TWO + "\n### 3. C · auto\n- [x] (spec)\n- [ ] `/develop c`\n"


class TestQueueCommand(SubcommandCase):
    # covers: AC-20 (the plan with options and would clear, no call, no write, locks left free, no claude and no
    # ntfy config needed; a held lock is a skip line; a broken queue.json refuses)
    def test_plan(self):
        repo = self.make_repo("q", THREE)
        self.commit(repo)
        p = self.write_queue([park(repo, "1. A", self.section_sha(repo, "1. A")), park(repo, "2. B", "b" * 64)],
                             [decision(repo, "3. C")])
        before = p.read_text()
        (self.tmp / "config" / "wf" / "allowed.json").write_text(json.dumps([str(repo)]))
        (self.bin / "claude").unlink()
        self.ntfy_config.unlink()
        want = ["q on work, 0 changes", "  open: ab12 3. C: Which storage engine?", "    1 Postgres (recommended)",
                "    2 SQLite", "  parked: 1. A: blocked: test park (wf unpark to retry)", "  queued: 2. B",
                "  would clear: 2. B"]
        for args in (["q"], []):
            with self.subTest(args):
                r = self.sub("queue", *args)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                lines = r.stdout.splitlines()
                self.assertEqual(lines[:7], want)
                self.assertTrue(lines[7].startswith("caps: 20 USD/call"), lines[7])
                self.assertNotIn("nothing to run", r.stdout)
        self.assertEqual(p.read_text(), before)
        self.assertEqual(sorted(os.listdir(self.state / "wf")), ["queue.json", "queue.lock"])
        self.assertEqual(self.calls(), [])
        fd, lock = self.hold(repo)
        r = self.sub("queue", "q")
        os.close(fd)
        self.assertEqual((r.returncode, r.stdout.splitlines()[:2]),
                         (0, ["q on work, 0 changes", "  skip: locked: 4242 2026-10-11T09:00:00+02:00"]))
        # Tested and let go: wf queue never keeps a lock.
        self.sub("queue", "q")
        fd = os.open(lock, os.O_RDONLY)
        run.fcntl.flock(fd, run.fcntl.LOCK_EX | run.fcntl.LOCK_NB)
        os.close(fd)
        self.assertEqual(lock.read_text(), "4242 2026-10-11T09:00:00+02:00\n")
        p.write_text("{broken")
        r = self.sub("queue", "q")
        self.assertEqual(r.returncode, 5)
        self.assertIn("refused: queue_unreadable: ", r.stdout)

    # covers: AC-20 (a fresh state folder is never created; a higher cap shows the cap park as would clear)
    def test_no_state_and_cap(self):
        repo = self.make_repo("q", THREE)
        r = self.sub("queue", "q")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(self.state.exists())
        self.commit(repo)
        self.write_queue([park(repo, "1. A", self.section_sha(repo, "1. A"), reason="budget", cap=1)], [])
        self.assertIn("  parked: 1. A: budget: ", self.sub("queue", "q", "--budget", "1").stdout)
        self.assertIn("  would clear: 1. A\n", self.sub("queue", "q", "--budget", "2").stdout)


class TestUnpark(SubcommandCase):
    # covers: AC-21 (exact heading before substring, ambiguous exits 1, all records of the repo, other repos kept,
    # nothing parked, a held lock refuses)
    def test_unpark(self):
        repo = self.make_repo("q", THREE)
        other = park("/other", "Login")
        p = self.write_queue([park(repo, "Login"), park(repo, "Login page"), other],
                             [decision(repo, "Billing"), decision(repo, "Login page", "cd34")])
        r = self.sub("unpark", "q", "LOGIN")
        self.assertEqual((r.returncode, r.stdout), (0, "unparked: Login\n"), r.stderr)
        before = p.read_text()
        r = self.sub("unpark", "q", "i")
        self.assertEqual(r.returncode, 1)
        self.assertIn("  Login page\n  Billing\n", r.stderr)
        self.assertEqual(p.read_text(), before)
        r = self.sub("unpark", "q", "page")
        self.assertEqual((r.returncode, r.stdout), (0, "unparked: Login page\ndropped: cd34 Login page\n"), r.stderr)
        self.assertEqual(self.sub("unpark", "q", "nope").stdout, "nothing parked in q\n")
        fd, _ = self.hold(repo)
        r = self.sub("unpark", "q")
        os.close(fd)
        self.assertEqual(r.returncode, 5)
        self.assertIn("refused: locked: a wf run holds this repo: 4242 ", r.stdout)
        r = self.sub("unpark", "q")
        self.assertEqual((r.returncode, r.stdout), (0, "dropped: ab12 Billing\n"), r.stderr)
        self.assertEqual(self.sub("unpark", "q").stdout, "nothing parked in q\n")
        self.assertEqual(self.queue(), {"version": 1, "parks": [other], "decisions": []})
        self.assertEqual(self.sub("unpark", "nosuchrepo").returncode, 1)

    # covers: AC-21 (a dropped Decision is never resumed: its feature is queued fresh)
    def test_dropped_not_resumed(self):
        repo = self.make_repo("q", ONE)
        self.commit(repo)
        self.write_queue([], [decision(repo, "1. A", answer="1", source="phone", answered="2026-10-12T09:01:00+02:00")])
        self.assertIn("  resume: ab12 1. A: ", self.wf("q").stdout)
        self.sub("unpark", "q")
        self.assertIn("  queued: 1. A\n", self.wf("q").stdout)


if __name__ == "__main__":
    unittest.main()
