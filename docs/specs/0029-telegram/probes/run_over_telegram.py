# /check verify telegram: a whole `wf run` (fake claude, the runner's own test fixture) asks over the fake Telegram
# bot, takes the tap, resumes the call with the answer and sends the morning report there. Nothing to ntfy.
import os, sys, unittest
REPO = os.environ["REPO"]
sys.path[:0] = [os.path.join(REPO, "runner", "tests"), os.path.join(REPO, "runner", "e2e"), os.path.join(REPO, "runner")]
import fake_telegram, ntfy  # noqa: E402
from test_run import RunCase, ask  # noqa: E402


class Telegram(RunCase):
    def test_run_over_telegram(self):
        os.unlink(self.ntfy_config) if isinstance(self.ntfy_config, str) else (self.tmp / "config" / "wf" / "ntfy.json").unlink()
        fake = fake_telegram.Server()
        self.addCleanup(fake.close)
        ntfy.write(fake.config(), str(self.tmp / "config" / "wf" / "telegram.json"))
        self.env["WF_TELEGRAM_API"] = fake.url
        posts_before = len(self.report_ntfy.posts) if hasattr(self.report_ntfy, "posts") else None
        self.steps([ask(), {}, {}, {"tick": False}])
        r = self.wf("demo", "-y", "--max-wait", "60", mode="fast")
        print("EXIT", r.returncode)
        print("STDOUT", r.stdout[-1500:])
        print("STDERR", r.stderr[-500:])
        folder, rec = self.run_record()
        d = rec["decisions"][0]
        print("DECISION", d["id"], d["answer"], d["source"], d["resumed_in"])
        q = [s for s in fake.sent if s.get("reply_markup")]
        print("QUESTION buttons", [b[0]["callback_data"] for b in q[0]["reply_markup"]["inline_keyboard"]] if q else None)
        print("SENT texts", [s.get("text", "<document>")[:60] for s in fake.sent])
        print("RESUME argv", self.argv(2)["argv"][:2])
        print("NTFY posts", posts_before, len(self.report_ntfy.posts) if hasattr(self.report_ntfy, "posts") else "n/a")
        self.assertEqual(r.returncode, 0)
        self.assertEqual((d["answer"], d["source"]), ("Postgres (recommended)", "phone"))
        self.assertEqual(self.argv(2)["argv"][1], "The user answered your DECISION NEEDED question: Postgres (recommended)")
        self.assertTrue(q and q[0]["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == f"{d['id']} 1")
        self.assertTrue(any(str(s.get("text", "")).startswith("wf ") and "built" in s.get("text", "") for s in fake.sent))


if __name__ == "__main__":
    unittest.main(verbosity=2)
