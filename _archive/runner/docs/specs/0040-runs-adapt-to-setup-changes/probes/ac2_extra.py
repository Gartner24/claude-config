"""Verify driver for spec 0040 AC-2 paths the suite does not drive: a text block from an earlier run retaken once a
newer setup line exists; wf queue (no guard) keeps a denied_path park; a denial outside the guard's denies records
no denied_path."""
import json, sys, unittest
sys.path.insert(0, sys.argv.pop(1))
from test_swap_take import SwapTake, sha, STAMP  # noqa: E402

HOOK = "#!/bin/sh\n"


class V(SwapTake):
    def q(self):
        return json.loads((self.state / "wf" / "queue.json").read_text())

    def test_earlier_run_text_block(self):
        self.steps([{"tick": False, "json": {"result": "no\nBLOCKED: run ./install.sh live first"}}, {}, {}, {"tick": False}])
        self.wf("demo", "-y")
        park = self.q()["parks"][0]
        print("run 1 park:", park["reason"], "setup", park.get("setup"), "seen", park.get("setups_seen"))
        r = self.wf("demo", "-y")
        self.assertEqual(len(self.calls()), 1, "no newer setup: must stay parked\n" + r.stdout)
        self.ledger({str(self.live / "settings.json"): sha("{}")})
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        runs = sorted((self.state / "wf" / "runs").iterdir())
        log = (runs[-1] / "log.txt").read_text()
        print([l for l in log.splitlines() if "retaken" in l])
        self.assertIn("retaken 1. Loop: the setup changed", log)
        self.assertEqual(self.q()["parks"], [])

    def deny_park(self, target):
        (self.repo / "tools").mkdir()
        (self.repo / "tools" / "h.sh").write_text(HOOK)
        old = json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": f"bash {self.repo}/tools/h.sh"}]}]}})
        (self.live / "settings.json").write_text(old)
        self.steps([{"tick": False, "json": {"permission_denials": [
            {"tool_name": "Edit", "tool_use_id": "t1", "tool_input": {"file_path": target}}]}}, {}, {}])
        self.wf("demo", "-y")
        return self.q()["parks"][0]

    def test_queue_keeps_park(self):
        park = self.deny_park(str(self.repo / "tools" / "x.py"))
        print("park denied_path:", park.get("denied_path"))
        self.assertEqual(park.get("denied_path"), str(self.repo / "tools" / "x.py"))
        (self.live / "settings.json").write_text("{}")
        r = self.wf_queue()
        print(r.stdout)
        self.assertIn("parked: 1. Loop: denied", r.stdout)

    def wf_queue(self):
        import subprocess
        from test_run import WF
        return subprocess.run([sys.executable, str(WF), "queue", "demo"], capture_output=True, text=True, env=self.env)

    def test_no_path_outside_guard(self):
        park = self.deny_park(str(self.repo / "src" / "x.py"))
        print("outside guard park:", park["reason"], "denied_path" in park)
        self.assertNotIn("denied_path", park)


if __name__ == "__main__":
    unittest.main(argv=["x", "-v", "V.test_earlier_run_text_block", "V.test_queue_keeps_park", "V.test_no_path_outside_guard"])
