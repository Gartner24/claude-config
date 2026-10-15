"""Verify driver for spec 0040 AC-1 paths the suite does not drive: a refused file mid wait keeps ntfy and logs it,
then a valid one switches."""
import re, sys, time, unittest
from pathlib import Path
sys.path.insert(0, sys.argv.pop(1))
from test_telegram import TestRunChannel, write_cfg  # noqa: E402
import test_run  # noqa: E402


class V(TestRunChannel):
    def logs(self):
        return "".join(p.read_text() for p in self.state.glob("wf/**/log.txt"))

    def test_kept_then_switched(self):
        self.bot.taps = ["{id} 2"]
        self.steps([test_run.ask(), {}, {}, {"tick": False}])
        p = self.start("demo", "-y", "--max-wait", "0.01", mode="fast")
        end = time.monotonic() + 20
        while not any(re.match(r"^[a-z0-9]{4}: ", m["message"]) for m in self.report_ntfy.messages):
            self.assertLess(time.monotonic(), end, "no question on ntfy")
            time.sleep(0.05)
        write_cfg(self.tmp / "config", chat_id="x")
        while "phone channel kept" not in self.logs():
            self.assertLess(time.monotonic(), end, "no kept line")
            time.sleep(0.05)
        self.assertEqual(self.bot.sent(), [], "nothing may go to the bot while the file is refused")
        time.sleep(0.05)
        write_cfg(self.tmp / "config")
        out, err = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 0, out + err)
        folder, rec = self.run_record()
        log = (folder / "log.txt").read_text()
        print("\n".join(l for l in log.splitlines() if "phone channel" in l))
        self.assertIn("phone channel kept: no_telegram: chat_id must be an integer", log)
        self.assertEqual(log.count("phone channel now Telegram"), 1, log)
        d = rec["decisions"][0]
        self.assertEqual((d["answer"], d["source"]), ("SQLite", "phone"))


if __name__ == "__main__":
    unittest.main(argv=["x", "-v"])
