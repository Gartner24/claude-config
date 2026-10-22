"""scripts/fb-ask.py (spec 0023 AC-13, spec 0053 AC-8): copied from the archived runner suite, which no longer runs."""
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestFbAsk(unittest.TestCase):
    # covers: spec 0023 AC-13 (fb-ask --test passes: fake proxy, temp repos, every reason)
    def test_fb_ask(self):
        r = subprocess.run([sys.executable, str(REPO / "scripts" / "fb-ask.py"), "--test"], capture_output=True,
                           text=True, stdin=subprocess.DEVNULL, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # covers: spec 0053 AC-8 (the rule file stays at most 8 lines and names every local limit; AGENTS.md shows --local)
    def test_local_rule_and_docs(self):
        rule = (REPO / "claude-home" / "rules" / "cheap-worker.md").read_text().splitlines()
        self.assertLessEqual(len(rule), 8)
        local = [l for l in rule if "only with `--local`" in l]
        self.assertEqual(len(local), 1, rule)
        for part in ("2 minutes", "6 words a second", "30,000 characters", "600000 ms"):
            self.assertIn(part, local[0])
        agents = [l for l in (REPO / "AGENTS.md").read_text().splitlines() if l.startswith("fb-ask <task>")]
        self.assertEqual(len(agents), 1)
        self.assertIn("[--local]", agents[0])


if __name__ == "__main__":
    unittest.main()
