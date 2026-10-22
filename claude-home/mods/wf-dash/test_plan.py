import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCOPE = """# Scope: here

### 1. Owed step
- [ ] Log in on the phone · waits on you

### 2. Ready one
- [ ] Build it: `/develop ready one` (spec [0007](../specs/0007-ready/index.md))

### 3. Needs design
- [x] Plan it: `/scope three`
- [ ] Design it: `/architect three`

### 4. Built · done
- [x] Build it: `/develop four`

### 5. Half done
- [x] Build it: `/develop five`
- [ ] Prove it: `/check verify five`

### 6. Ticked, no tag
- [x] Build it: `/develop six`

### 7. Escape \x1b]0;owned\x07 heading
- [ ] Test it: `/test seven`

### 8. Near miss
- [ ] Ask someone, waits on Bob

## Deferred

### 9. Later
- [ ] Build it: `/develop later`

<!--
### 10. Commented out
- [ ] Build it: `/develop ten`
-->
"""

HUB = """# Hub

## At a glance

| # | Thing | Status |
|---|---|---|
| 1 | Open thing | planned |
| 2 | Shut thing | done |
"""


def run(root):
    r = subprocess.run([sys.executable, "-I", str(HERE / "plan.py")], capture_output=True, text=True,
                       env={"PATH": os.environ["PATH"], "HOME": root, "WF_ROOTS": root})
    if r.returncode:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout)


class Plan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.root = str(root)
        here = root / "here"
        (here / "docs/scope").mkdir(parents=True)
        (here / "docs/scope/scope.md").write_text(SCOPE)
        (here / "docs/specs/0007-ready").mkdir(parents=True)
        (here / "docs/specs/0007-ready/index.md").write_text("# 0007\n\n**Status**: Accepted\n")
        hub = root / "hub/docs/scope"
        hub.mkdir(parents=True)
        (hub / "scope.md").write_text(HUB)
        # a linked worktree of here: left out, its repo's entry is the main checkout's
        wt = root / "wt"
        (wt / "docs/scope").mkdir(parents=True)
        (wt / "docs/scope/scope.md").write_text(SCOPE)
        gd = root / "here/.git/worktrees/wt"
        gd.mkdir(parents=True)
        (gd / "commondir").write_text("../..\n")
        (wt / ".git").write_text(f"gitdir: {gd}\n")
        self.out = run(self.root)
        self.repos = {r["name"]: r for r in self.out["repos"]}
        self.feats = {f["heading"].split(".")[0]: f for f in self.repos["here"]["features"]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_each_feature_gets_its_state(self):
        got = {k: f["state"] for k, f in self.feats.items()}
        self.assertEqual(got, {"1": "waits on you", "2": "ready to build", "3": "needs a design", "4": "done", "5": "in progress",
                               "6": "done (untagged)", "7": "in progress", "8": "in progress", "9": "ready to build"})

    def test_next_step_command_and_spec(self):
        f = self.feats["2"]
        self.assertEqual((f["command"], f["spec"], f["specStatus"], f["deferred"]), ("/develop ready one", "0007", "Accepted", False))
        self.assertEqual(self.feats["5"]["command"], "/check verify five")
        self.assertTrue(self.feats["9"]["deferred"])
        self.assertNotIn("10", self.feats)

    def test_escape_codes_never_reach_the_pane(self):
        self.assertNotIn("\x1b", self.feats["7"]["heading"])
        self.assertNotIn("\x07", self.feats["7"]["heading"])

    def test_a_near_miss_marker_is_warned_about(self):
        self.assertTrue(any("waits on Bob" in w for w in self.repos["here"]["warnings"]))

    def test_hub_lists_open_rows_and_worktree_is_left_out(self):
        self.assertEqual(self.repos["hub"]["rows"], ["1 | Open thing | planned"])
        self.assertTrue(self.repos["hub"]["hub"])
        self.assertNotIn("wt", self.repos)

    def test_a_broken_scope_is_listed_with_its_error(self):
        bad = Path(self.root, "bad/docs/scope")
        bad.mkdir(parents=True)
        (bad / "scope.md").mkdir()  # a folder where the file should be: reading it fails
        (bad / "index.md").write_text("[x](x.md)\n")
        os.chmod(bad / "index.md", 0)
        try:
            repos = {r["name"]: r for r in run(self.root)["repos"]}
        finally:
            os.chmod(bad / "index.md", 0o644)
        self.assertIn("error", repos["bad"])
        self.assertIn("here", repos)


if __name__ == "__main__":
    unittest.main()
