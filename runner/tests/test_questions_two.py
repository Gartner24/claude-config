"""Spec 0044: questions, round two."""
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import context  # noqa: E402
import ntfy  # noqa: E402
import run  # noqa: E402
import telegram  # noqa: E402
from test_never_stop import NeverStopCase  # noqa: E402

CFG = {"block": [], "chat_id": 7, "aliases": {}, "token": "1"}
SPEC = "https://github.com/acme/widgets/blob/work/docs/specs/0031-adopt-open-prs/index.md"


def question(**ctx):
    return {"id": "ab12", "case": "waiting", "kind": "panel", "repo": "/w/widgets", "feature": "38. Adopt",
            "question": "38. Adopt needs one step only you can do: write the file", "learn": "L", "options": ["done", "skip"],
            "context": {"feature": "38. Adopt", "spec": SPEC, "repo_url": "https://github.com/acme/widgets",
                        "issues": ["https://github.com/acme/widgets/issues/4"], **ctx}}


def sent(d, names=("zzz",)):
    out = {}
    with mock.patch.object(ntfy, "private_names", return_value=list(names)), \
            mock.patch.object(telegram.Topic, "publish",
                              lambda self, m, *a, **k: out.update(plain=m, styled=k.get("styled")) or "1"):
        telegram.Topic(CFG, "widgets", "38. Adopt").ping(dict(d), lambda: False)
    return out


class TestLabels(unittest.TestCase):
    # covers: AC-1 (short tappable labels in the styled message, full addresses in the plain one, no from: line)
    def test_short_labels(self):
        m = sent(question(what="It writes the file."))
        self.assertIn(f'spec: <a href="{SPEC}">0031 adopt open prs</a>', m["styled"])
        self.assertIn('repo: <a href="https://github.com/acme/widgets">widgets</a>', m["styled"])
        self.assertIn('issue: <a href="https://github.com/acme/widgets/issues/4">#4</a>', m["styled"])
        self.assertIn(f"spec: {SPEC}", m["plain"])
        self.assertIn("repo: widgets https://github.com/acme/widgets", m["plain"])
        self.assertNotIn("from:", m["styled"] + m["plain"])

    # covers: AC-1 (a private repo's alias or hashed label gets no link that would name it)
    def test_private_label_unlinked(self):
        d = question(what="x.")
        d["repo"] = "/w/secret-cms"
        with mock.patch.object(ntfy, "private_names", return_value=["secret"]):
            label = ntfy.repo_label(CFG, "/w/secret-cms")
        self.assertNotIn("secret", label)
        m = sent(d, names=("secret",))
        self.assertNotIn("github.com/acme/widgets\"", m["styled"].split("spec:")[0])
        self.assertIn(f"repo: {label}\n", m["plain"])

    # covers: AC-1 (a flat spec file's label is its name without .md)
    def test_flat_spec_label(self):
        self.assertEqual(telegram.label("spec", "spec: ", "https://github.com/a/b/blob/m/docs/specs/0001-runner-stack.md"),
                         "0001 runner stack")


class TestFold(unittest.TestCase):
    # covers: AC-2 (the first sentence shows, the marker with it; the rest folds; the plain message is not folded)
    def test_fold(self):
        mark = run.EXPLAINED_UNVERIFIED
        m = sent(question(what=f"{mark} The check stopped. It changed a notes file. Keep it."))
        import html
        self.assertIn(f"<b>what this is:</b> {html.escape(mark)} The check stopped.\n<blockquote expandable>It changed a notes file. "
                      "Keep it.</blockquote>", m["styled"])
        self.assertIn(f"what this is: {mark} The check stopped. It changed a notes file. Keep it.", m["plain"])

    # covers: AC-2 (a first sentence over 300 characters is cut at a word and the rest folds)
    def test_long_first(self):
        m = sent(question(what="word " * 100 + "end. Next."))
        shown = m["styled"].split("<b>what this is:</b> ")[1].split("\n")[0]
        self.assertLessEqual(len(shown), context.FIRST_MAX)
        self.assertIn("<blockquote expandable>", m["styled"])
        self.assertIn("end. Next.</blockquote>", m["styled"])


class TestSteps(unittest.TestCase):
    # covers: AC-3 (an explained step only you can do with no steps says so; with steps, they are numbered)
    def test_none_given(self):
        m = sent(question(what="It writes the file."))
        self.assertIn(context.NO_STEPS_LINE, m["plain"])
        m = sent(question(what="It writes the file.", steps=["Open a terminal", "Run make"]))
        self.assertNotIn(context.NO_STEPS_LINE, m["plain"])
        self.assertIn("\n1. Open a terminal\n2. Run make", m["plain"])

    # covers: AC-3 (the explain prompt asks for one to six steps, and a check step when the box is ticked)
    def test_prompt(self):
        self.assertIn("one to six of them", run.EXPLAIN_PROMPT)
        self.assertIn("already done, give one STEP line saying how to check that it is done", run.EXPLAIN_PROMPT)


class TestDoIt(unittest.TestCase):
    # covers: AC-4, AC-5 (the do it for me answer and the note line reach both messages; every option stays in the
    # styled one)
    def test_message(self):
        d = question(what="It writes the file.")
        d["options"] = ["done", run.DO_IT, run.SKIP_IT]
        m = sent(d)
        for body in (m["plain"], m["styled"]):
            self.assertIn("\n1 done\n2 do it for me\n3 skip\nor reply with a note: it goes to the step as your "
                          "instruction\ntap a button", body)


class TestApproved(unittest.TestCase):
    # covers: AC-6 (the approved question's block shows the reviewers line on Telegram, styled and plain)
    def test_reviewers_on_telegram(self):
        d = question(reviewers="reviewers: your approver: approved · review bot: not yet")
        d.update(case="approved", question="your PR #3 was approved: 38. Adopt. Merge it now?",
                 options=["merge now", "later", "I merged it"])
        m = sent(d)
        for body in (m["plain"], m["styled"]):
            self.assertIn("reviewers: your approver: approved · review bot: not yet", body)


PHONE ="# Scope: m\n**Autopilot:** allowed\n### 1. M · auto\n- [x] (spec)\n- [ ] `/develop m`\n" \
        "- [ ] Check it on the phone: `/qa m`\n- [ ] `/test m`\n"
BOX = "Check it on the phone: `/qa m`"


class TestDoItRun(NeverStopCase):
    def setUp(self):
        super().setUp()
        self.make_repo("m", PHONE)

    def run_m(self):
        return self.wf("m", "-y", "--max-wait", "0.01", mode="fast")

    # covers: AC-4 (do it for me runs the box's own call with DO_IT_PROMPT; its tick ends the question)
    def test_do_it_ticks(self):
        self.reply("{id} code0001 do it for me")
        self.steps([{}, {}, {}, {"tick": False}])
        r = self.run_m()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("answered: ", r.stdout)
        self.assertEqual([self.argv(n)["argv"][1] for n in (2, 3, 4)],
                         [run.DO_IT_PROMPT.format(BOX), "/test m", "/sync"])
        self.assertIn("- [x] Check it on the phone", (self.tmp / "root/m/docs/scope/scope.md").read_text())

    # covers: AC-4 (the offer is done, do it for me, skip; BLOCKED asks again, without do it for me)
    def test_blocked_asks_again(self):
        self.reply("{id} code0001 do it for me")
        self.steps([{}, {"tick": False, "json": {"result": "BLOCKED: it needs your phone"}}])
        r = self.run_m()
        self.assertEqual(self.argv(2)["argv"][1], run.DO_IT_PROMPT.format(BOX), r.stdout)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["case"], d["detail"]), ("blocked", "it needs your phone"))
        self.assertNotIn(run.DO_IT, d["options"])
        self.assertIn("- [ ] Check it on the phone", (self.tmp / "root/m/docs/scope/scope.md").read_text())

    # covers: AC-4 (one try per box per run: a try that leaves the box open asks again without do it for me)
    def test_one_try(self):
        # The try changes nothing; try again on that question reaches the box, asked again with no second try.
        self.reply("{id} code0001 do it for me")
        self.steps([{}, {"tick": False}])
        fake, done = self.report_ntfy, threading.Event()

        def later():
            # try again on the no progress question, then skip on the box's question, so the run ends by itself.
            seen = 1
            for words, answer in (("changed nothing", "{id} 1"), ("needs one step", "{id} 2")):
                while not done.is_set():
                    at = next((i for i, p in enumerate(fake.pings()) if i >= seen and words in p["message"]), None)
                    if at is not None:
                        seen = at + 1
                        break
                    time.sleep(0.05)
                fake.replies = [answer]
        threading.Thread(target=later, daemon=True).start()
        self.addCleanup(done.set)
        r = self.wf("m", "-y", "--max-wait", "0.015", mode="fast")
        self.assertEqual(len(self.calls()), 2, r.stdout + r.stderr)
        third = [p["message"] for p in fake.pings() if "needs one step" in p["message"]][-1]
        self.assertIn("needs one step only you can do", third, r.stdout)
        self.assertIn("\n1 done\n2 skip", third)
        self.assertNotIn(run.DO_IT, third)

    # covers: AC-4 security review (an ntfy tap without your one time code runs no call; the box asks again)
    def test_weak_tap(self):
        self.reply("{id} 2")
        self.steps([{}])
        r = self.run_m()
        self.assertEqual(len(self.calls()), 1, r.stdout + r.stderr)
        self.assertIn("answered: ", r.stdout)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["case"], d["answer"]), ("manual_box", None))
        self.assertIn(run.DO_IT, d["options"])

    # covers: AC-5 (a strong typed note runs the try with the note as its hint)
    def test_strong_note(self):
        self.reply("{id} code0001 use the spare phone")
        self.steps([{}, {}, {}, {"tick": False}])
        r = self.run_m()
        self.assertEqual(self.argv(2)["argv"][1], run.DO_IT_PROMPT.format(BOX), r.stdout + r.stderr)
        self.assertIn(run.HINT_PROMPT.format("use the spare phone"), self.prompt(2))

    # covers: AC-5 (a note anyone could post on ntfy, with no one time code, runs nothing; the question stays)
    def test_weak_note(self):
        self.reply("{id} use the spare phone")
        self.steps([{}])
        r = self.run_m()
        self.assertEqual(len(self.calls()), 1, r.stdout + r.stderr)
        [d] = self.queue()["decisions"]
        self.assertEqual((d["case"], d["answer"]), ("manual_box", None))


class TestHome(NeverStopCase):
    # covers: AC-7 (the home folder joins the write list only; the login, startup and key places and every known repo's
    # git config, hooks and info are never writable and denied in the sandbox and as Edit rules)
    def test_home_open_risky_shut(self):
        other = self.make_repo("other", PHONE)
        self.steps([{"tick": False}])
        self.wf("demo", "-y", "--max-calls", "1")
        a = self.argv(1)["argv"]
        fs = json.loads(a[a.index("--settings") + 1])["sandbox"]["filesystem"]
        denied = set(a[a.index("--disallowedTools") + 1].split(","))
        g = self.run_record()[1]["repos"][0]["guard"]
        home = str(self.tmp)
        self.assertIn(home, fs["allowWrite"])
        self.assertNotIn(home, g["allowed"])
        for p in (f"{home}/.config/systemd", f"{home}/.config/autostart", f"{home}/.zlogin", f"{home}/.config/fish",
                  f"{home}/.local/share/keyrings", f"{home}/.mozilla", f"{home}/.cargo/credentials.toml",
                  f"{other}/.git/config", f"{other}/.git/hooks", f"{other}/.git/info"):
            with self.subTest(p):
                self.assertIn(p, g["never"])
                self.assertIn(p, fs["denyWrite"])
                self.assertTrue({f"Edit(/{p})", f"Edit(/{p}/**)"} & denied)


if __name__ == "__main__":
    unittest.main()
