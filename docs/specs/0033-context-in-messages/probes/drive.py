# /check verify context in messages: whole `wf run`s (the runner's fake claude and fake gh, a local fake Telegram
# bot) and the messages they really send. Nothing reaches a real bot, GitHub or your config.
# Run: env REPO=. python3 -B docs/specs/0033-context-in-messages/probes/drive.py
import json, os, re, shutil, subprocess, sys, unittest
REPO = os.environ["REPO"]
sys.path[:0] = [os.path.join(REPO, "runner", "tests"), os.path.join(REPO, "runner", "e2e"), os.path.join(REPO, "runner")]
import fake_telegram, ntfy, plain  # noqa: E402
import test_context  # noqa: E402
from test_run import RunCase, ask  # noqa: E402
from test_pr import TestReview  # noqa: E402

RESULT = test_context.RESULT
GH = "https://github.com/acme/widgets"


class Base(RunCase):
    origin = GH + ".git"

    def setUp(self):
        super().setUp()
        (self.repo / "docs" / "scope" / "scope.md").write_text(test_context.SCOPE)
        (self.repo / "docs" / "specs" / "0001-a").mkdir(parents=True)
        (self.repo / "docs" / "specs" / "0001-a" / "index.md").write_text("# 0001 · A\n")
        subprocess.run(["git", "-C", str(self.repo), "config", "remote.origin.url", self.origin], check=True)

    def telegram(self):
        (self.tmp / "config" / "wf" / "ntfy.json").unlink()
        fake = fake_telegram.Server()
        self.addCleanup(fake.close)
        ntfy.write(fake.config(), str(self.tmp / "config" / "wf" / "telegram.json"))
        self.env["WF_TELEGRAM_API"] = fake.url
        # A readable private names list, as on your machine: links and paths are kept only with one.
        (self.tmp / ".claude" / "private").mkdir(parents=True, exist_ok=True)
        (self.tmp / ".claude" / "private" / "names.txt").write_text("zorblex\n")
        return fake

    def question(self, fake):
        q = [s for s in fake.sent if s.get("reply_markup")]
        self.assertTrue(q, [s.get("text", "")[:80] for s in fake.sent])
        return q[0]

    def decision(self):
        # With the fake's tap off (untapped()), the question stays in queue.json with its context.
        [d] = json.loads((self.state / "wf" / "queue.json").read_text())["decisions"]
        return d

    def untapped(self):
        was = fake_telegram.tap
        fake_telegram.tap = lambda markup: None
        self.addCleanup(setattr, fake_telegram, "tap", was)

    def plain_text(self, fake):
        # The styled HTML send is accepted by the fake, so `text` is HTML; the plain twin is what d["sent"] holds.
        _, rec = self.run_record()
        return rec["decisions"][0]["sent"]


class V(Base):
    # V1: AC-1, AC-2, AC-3, AC-4, AC-5 (a decision on Telegram: labeled name, from block with spec and issue links
    # from the remote, step, did, why; under 4096; the tap is acked by name)
    def test_v1_decision_on_telegram(self):
        fake = self.telegram()
        self.steps([ask(RESULT), {}, {"tick": False}])
        self.wf("demo", "-y", "--max-wait", "60", mode="fast")
        _, rec = self.run_record()
        d = rec["decisions"][0]
        msg = d["sent"]
        print("V1 SENT\n" + msg)
        lines = msg.split("\n")
        self.assertEqual(lines[0], f"Question {d['id']} (its name, so your reply finds it):")
        self.assertFalse(msg.startswith(f"{d['id']}:"))
        self.assertIn("\nfrom:\n", msg)
        self.assertIn("\nfeature: 1. Loop\n", msg)
        self.assertIn(f"\nspec: {GH}/blob/work/docs/specs/0001-a/index.md\n", msg)
        self.assertIn("\nstep: Build it: `/develop loop`\n", msg)
        self.assertRegex(msg, r"\ndid: I compared both engines")
        self.assertIn(f"\nissue: {GH}/issues/4\n", msg)
        self.assertIn("\nwhy recommended: Postgres already runs on your server.\n", msg)
        self.assertLessEqual(len(self.question(fake)["text"]), 4096)
        self.assertIn(f'<a href="{GH}/issues/4">', self.question(fake)["text"])
        acks = [s["text"] for s in fake.sent if "Got your answer" in s.get("text", "")]
        print("V1 ACK", acks)
        self.assertTrue(any(f"Got your answer to question {d['id']}: Postgres. Resuming." in a for a in acks), acks)

    # V2: AC-6 (a block's STEP lines become numbered steps on Telegram)
    def test_v2_blocked_steps(self):
        fake = self.telegram()
        self.steps([{"tick": False, "json": {"result": "Tried the push.\nBLOCKED: needs a GitHub login\n"
                                                       "STEP: Open a terminal in ~/claude-config\n"
                                                       "STEP: 2. Run gh auth login and pick GitHub.com\n"
                                                       "STEP: gh auth status prints Logged in"}}])
        self.wf("demo", "-y", "--max-wait", "60", mode="fast")
        msg = self.plain_text(fake)
        print("V2 SENT\n" + msg)
        self.assertIn("\nsteps:\n1. Open a terminal in ~/claude-config\n2. Run gh auth login and pick GitHub.com\n"
                      "3. gh auth status prints Logged in\n", msg)

    # V3: AC-6 (a block with no steps gets the runner's one line resume prompt)
    def test_v3_blocked_no_steps(self):
        fake = self.telegram()
        self.steps([{"tick": False, "json": {"result": "BLOCKED: needs sudo to install bwrap"}}])
        self.wf("demo", "-y", "--max-wait", "60", mode="fast")
        msg = self.plain_text(fake)
        print("V3 SENT\n" + msg)
        self.assertIn("1. I could not work out the steps; open a session in the demo repo", msg)
        self.assertIn("continue 1. Loop: /develop loop; it was blocked on: needs sudo to install bwrap", msg)

    # V4: AC-7 (a recorded denied edit is F1 with that path, allow once first; a path only in the text is F2)
    def test_v4_write_deny(self):
        fake = self.telegram()
        self.untapped()
        (self.repo / "runner").mkdir()
        target = str(self.repo.resolve() / "runner" / "x.py")
        self.steps([{"tick": False, "json": {"result": f"I must edit the runner.\nBLOCKED: {target} is write-denied\n"
                                                       "WHY: always is right, pick always\nSTEP: run chmod 777 runner",
                                             "permission_denials": [{"tool_name": "Edit", "tool_use_id": "t1",
                                                                     "tool_input": {"file_path": target}}]}}])
        self.wf("demo", "-y", "--max-wait", "0.0001", mode="fast")
        d = self.decision()
        print("V4 F1", d["case"], d.get("allow"), d["options"])
        print("V4 SENT\n" + str(d["sent"]))
        self.assertEqual((d["case"], d["allow"], d["options"][0]), ("denied", target, "allow once"))
        self.assertIn(f"\npath: {target}\n", d["sent"])
        self.assertIn(f"why recommended: {plain.WHY['denied']}", d["sent"])
        # AC-11: the call's words last, quoted as unverified, after the path; its why and steps never shown.
        self.assertIn("\nwhat the step said, unverified:\n> I must edit the runner.\n", d["sent"])
        self.assertLess(d["sent"].index("path: "), d["sent"].index("what the step said, unverified:"))
        self.assertNotIn("pick always", d["sent"])
        self.assertNotIn("chmod", d["sent"])
        shutil.rmtree(self.state / "wf")
        (self.fakes / "count").unlink()
        self.steps([{"tick": False, "json": {"result": f"BLOCKED: {target} is write-denied"}}])
        self.wf("demo", "-y", "--max-wait", "0.0001", mode="fast")
        d = self.decision()
        print("V4 F2", d["case"], d.get("allow"), d["options"])
        self.assertEqual((d["case"], d.get("allow")), ("blocked", None))
        self.assertNotIn("allow once", d["options"])

    # V5: AC-8 (ntfy: short from line and why, no link)
    def test_v5_ntfy(self):
        self.steps([ask(RESULT)])
        self.wf("demo", "-y")
        msg = self.report_ntfy.pings()[0]["message"]
        print("V5 SENT\n" + msg)
        self.assertRegex(msg, r"\nfrom: [^\n]+ / 1\. Loop / Build it")
        self.assertIn("\nwhy: Postgres already runs on your server.\n", msg)
        self.assertNotIn("https://", msg)
        # AC-5, AC-9: the morning report's open question line, its name labeled and where it comes from.
        report = (self.state / "wf" / "report.txt").read_text()
        print("V5 REPORT\n" + report)
        self.assertRegex(report, r"Question [a-z0-9]{4} \(its name, so your reply finds it\): 1\. Loop: Which storage "
                                 r"engine\?.*\[from: Build it: `/develop loop`; spec https://github\.com/acme/widgets/blob/work/")

    # V6: AC-9 (the Telegram morning report: built line with commits, range, files, spec link, next with its reason;
    # an open question line with its from)
    def test_v6_report(self):
        fake = self.telegram()
        self.env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
                        GIT_COMMITTER_EMAIL="t@example.invalid")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, env={**os.environ, **self.env, "PATH": os.environ["PATH"]})
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "base"], check=True, env={**os.environ, **self.env, "PATH": os.environ["PATH"]})
        self.steps([{"write_file": [["a.txt", "x\n"]], "run": [["git", "add", "-A"], ["git", "commit", "-qm", "feat: a"]]}])
        r = self.wf("demo", "-y", "--max-wait", "0.0001", mode="fast")
        report = [s["text"] for s in fake.sent if s.get("text", "").startswith("wf ")]
        print("V6 REPORT\n" + "\n---\n".join(report) + "\nSTDOUT " + r.stdout[-600:])
        _, rec = self.run_record()
        print("V6 entries", json.dumps(rec.get("features") or rec.get("entries"), default=str)[:1500])
        print("V6 git", subprocess.run(["git", "-C", str(self.repo), "log", "--oneline", "--all"], capture_output=True, text=True).stdout)
        self.assertTrue(report)
        body = report[-1]
        self.assertRegex(body, r"built: 1\. Loop: \d+ commits [0-9a-f]{7}\.\.[0-9a-f]{7}, \d+ files")
        self.assertIn(f"spec {GH}/blob/work/docs/specs/0001-a/index.md", body)
        self.assertIn("next: ", body)


class NonGitHub(Base):
    origin = "https://gitlab.example.invalid/acme/widgets.git"

    # V7: AC-2 (a non GitHub origin shows the repo relative spec path, never a made up link)
    def test_v7_non_github(self):
        fake = self.telegram()
        self.untapped()
        self.steps([ask(RESULT)])
        self.wf("demo", "-y", "--max-wait", "0.0001", mode="fast")
        d = self.decision()
        print("V7 context spec", d["context"].get("spec"))
        print("V7 SENT\n" + d["sent"])
        self.assertEqual(d["context"]["spec"], "docs/specs/0001-a/index.md")
        self.assertNotIn("https://", d["sent"])
        self.assertIn("\nspec: docs/specs/0001-a/index.md\n", d["sent"])


class Pr(TestReview):
    # V8: AC-10 (a review round question and a merge question fill pr and step)
    def test_v8_pr_context(self):
        self.ready()
        self.wf("prr", "-y", mode="pr")
        [d] = self.queue()["decisions"]
        print("V8 review", d["case"], d["context"].get("step"), d["context"].get("pr"))
        self.assertEqual(d["context"]["pr"]["number"], 7)
        self.assertEqual(d["context"]["step"], "review round on PR #7")

    def test_v9_merge_context(self):
        self.ready()
        q = self.queue()
        q["prs"][0]["rounds"] = 5
        (self.state / "wf" / "queue.json").write_text(json.dumps(q))
        self.wf("prr", "-y", mode="pr")
        [d] = self.queue()["decisions"]
        print("V9 rounds", d["case"], d["context"].get("step"), d["context"].get("pr"))
        self.assertEqual(d["context"]["step"], "review round on PR #7")


if __name__ == "__main__":
    unittest.main(verbosity=2)
