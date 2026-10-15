"""Spec 0044: questions, round two."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import context  # noqa: E402
import ntfy  # noqa: E402
import run  # noqa: E402
import telegram  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
