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

    def test_closed_features_in_done_md_still_count_as_built(self):
        # spec 0072c AC-12: the split moves closed features to done.md; the open ones and the built count stay the same
        folder = Path(self.root, "here/docs/scope")
        text = (folder / "scope.md").read_text()
        start = text.index("### 4. Built")
        end = text.index("### 5. Half done")
        (folder / "done.md").write_text("# Closed\n\n" + text[start:end])
        (folder / "scope.md").write_text(text[:start] + text[end:])
        feats = {f["heading"].split(".")[0]: f["state"]
                 for r in run(self.root)["repos"] if r["name"] == "here" for f in r["features"]}
        self.assertEqual(feats, {k: f["state"] for k, f in self.feats.items()})
        self.assertEqual(feats["4"], "done")

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


def warnings(repo):
    r = subprocess.run([sys.executable, "-I", str(HERE / "plan.py"), "--warnings", repo], capture_output=True, text=True,
                       env={"PATH": os.environ["PATH"], "HOME": repo})
    return r.returncode, r.stdout.splitlines()


class Warnings(unittest.TestCase):
    # covers: spec 0073 AC-7 (plan.py --warnings prints the pane's warnings for one repo, exit 1 when any)
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def scope(self, name, text, base="docs/scope", file="scope.md"):
        d = self.root / name / base
        d.mkdir(parents=True, exist_ok=True)
        (d / file).write_text(text)
        return str(self.root / name)

    def test_near_miss_on_the_next_box_is_printed(self):
        repo = self.scope("here", SCOPE)
        self.assertEqual(warnings(repo), (1, ['"waits on" is not the marker here, end the box with " · waits on you": '
                                              'Ask someone, waits on Bob']))

    def test_near_miss_on_a_later_box_is_not(self):
        repo = self.scope("later", "### 1. F\n- [ ] Build it: `/develop f`\n- [ ] Ask someone, waits on Bob\n")
        self.assertEqual(warnings(repo), (0, []))

    def test_both_scope_folders_and_a_missing_epic(self):
        repo = self.scope("both", "# S\n\n- [epic](gone.md)\n- [epic](here.md)\n", file="index.md")
        self.scope("both", "### 1. F\n- [ ] Build it: `/develop f`\n", file="here.md")
        self.scope("both", "### 1. F\n- [ ] Build it: `/develop f`\n", base=".workflow/scope")
        self.assertEqual(warnings(repo), (1, ["both docs/scope and .workflow/scope exist, using docs/scope",
                                              "missing epic file gone.md"]))

    def test_hub_and_no_scope_print_nothing(self):
        hub = self.scope("hub", HUB)
        self.scope("hub", HUB, base=".workflow/scope")
        self.assertEqual(warnings(hub), (0, []))
        (self.root / "empty").mkdir()
        self.assertEqual(warnings(str(self.root / "empty")), (0, []))


if __name__ == "__main__":
    unittest.main()
