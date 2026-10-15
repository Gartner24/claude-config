"""Spec 0045 verify scenarios V1 to V6: real wf run with the stub claude, plan shapes copied from features 46 and 47.
V6 scans RANGE, every commit this feature added on top of its planning commit 9ef7f1b."""
import subprocess
import sys
import unittest
from pathlib import Path

T = Path(__file__).resolve().parents[4] / "runner" / "tests"
sys.path.insert(0, str(T))
sys.path.insert(0, str(T.parent))
import pr  # noqa: E402
import run  # noqa: E402
from test_never_stop import NeverStopCase  # noqa: E402

RANGE = "9ef7f1b..HEAD"
HEAD = "# Scope: x\n**Autopilot:** allowed\n"
F46 = (HEAD + "### 1. Missed-skill detector · in-progress · auto\n- [x] Design it (spec): `/architect m`\n"
       "- [x] Build it: `/develop m`\n- [ ] Verify it: `/check verify m`\n- [ ] Test it: `/test m`\n"
       "- [x] Install it live: `./install.sh` · waits on you · live\n"
       "- [ ] After 3 days, run the report and write its verdict into verify.md · waits on you · later boxes go on\n"
       "- [ ] Sync docs: `/sync m`\n")
F47 = (HEAD + "### 1. Context monitor that fires · in-progress · auto\n- [x] Design it (spec): `/architect c`\n"
       "- [x] Build it: `/develop c`\n- [ ] Verify it: `/check verify c`\n- [ ] Test it: `/test c`\n"
       "- [ ] Install it live after the merge, from main (the first install ran without this branch) · waits on you "
       "· later boxes go on\n- [ ] Sync docs: `/sync c`\n")
BOX46 = "After 3 days, run the report and write its verdict into verify.md"
BOX47 = "Install it live after the merge, from main (the first install ran without this branch)"


def says(text, **extra):
    return {"json": {"result": text}, **extra}


class V(NeverStopCase):
    def commands(self):
        return [c["command"] for c in self.run_record()[1]["calls"]]

    # V1 (AC-1): feature 46 shape, AC-6 live, AC-7, AC-9 left to the 3 day box, the rest passed.
    def test_v1_f46_reaches_waiting_box(self):
        self.make_repo("c", F46)
        self.steps([says(f"AC-7 left\nLEFT TO BOX: {BOX46}\nCAN FAIL CHECKED: 4"), says("MUTATION CHECKED: 2"),
                    says("synced")])
        r = self.wf("c", "-y")
        p = self.prompt(1)
        print("\nV1 verify prompt boxes:", p[p.index("BEGIN BOXES"):p.index("END BOXES")].replace("\n", " | "))
        print("V1 calls:", self.commands(), "decisions:", self.queue()["decisions"], "rc:", r.returncode)
        self.assertIn(f"BEGIN BOXES-DATA-0\n{BOX46}\nEND BOXES-DATA-0", p)
        self.assertNotIn("Install it live", p[p.index("BEGIN BOXES"):])
        self.assertEqual([d["case"] for d in self.queue()["decisions"]], ["waiting"])
        self.assertEqual(self.commands()[:2], ["/check verify m", "/test m"])

    # V2 (AC-1): feature 47 shape, P1 and P2 both need a real claude -p, every check left: CAN FAIL 0 passes.
    def test_v2_f47_all_left_passes(self):
        self.make_repo("c", F47)
        self.steps([says(f"- **LEFT TO BOX:** {BOX47}\nCAN FAIL CHECKED: 0"), says("MUTATION CHECKED: 1"),
                    says("synced")])
        r = self.wf("c", "-y")
        print("\nV2 calls:", self.commands(), "decisions:", self.queue()["decisions"], "rc:", r.returncode)
        self.assertEqual([d["case"] for d in self.queue()["decisions"]], ["waiting"])
        self.assertEqual(self.commands()[:2], ["/check verify c", "/test c"])

    # V3 (AC-1 guard): a made up box name with CAN FAIL 0 still parks unchecked.
    def test_v3_made_up_box_parks(self):
        self.make_repo("c", F47)
        self.steps([says("LEFT TO BOX: some box I invented\nCAN FAIL CHECKED: 0")])
        r = self.wf("c", "-y")
        print("\nV3 rc:", r.returncode, "stdout tail:", r.stdout.strip().splitlines()[-3:])
        self.assertIn("unchecked", r.stdout)
        print("V3 calls:", self.commands())
        self.assertNotIn("/test c", self.commands())

    # V4 (AC-2): a verify that could not reach claude -p fails: question offers skip first with the fixed why.
    def test_v4_unreachable_skip_first(self):
        self.make_repo("c", F47)
        self.steps([says("UNREACHABLE: probe P1 needs a real claude -p\nVERIFY FAIL: develop", tick=False)])
        r = self.wf("c", "-y")
        [d] = self.queue()["decisions"]
        print("\nV4 case/options:", d["case"], d["options"], "\nV4 detail:", d["detail"], "\nV4 why:",
              d["context"].get("why"), "\nV4 stdout:", [l for l in r.stdout.splitlines() if "waiting:" in l or l.startswith("  ")])
        self.assertEqual((d["case"], d["options"]), ("verify_failed", ["skip", "try again"]))
        self.assertTrue(d["detail"].startswith("could not reach: probe P1 needs a real claude -p; "))
        self.assertEqual(d["context"]["why"], "a retry runs in the same sandbox, so it cannot reach this either")

    # V5 (AC-2 unchanged path): an ordinary failing verify still recommends try again.
    def test_v5_plain_failure_try_again(self):
        self.make_repo("c", F47)
        self.steps([says("AC-3 output wrong\nVERIFY FAIL: debug", tick=False), {"tick": False},
                    says("AC-3 output wrong\nVERIFY FAIL: develop", tick=False)])
        self.wf("c", "-y")
        [d] = self.queue()["decisions"]
        print("\nV5 case/options:", d["case"], d["options"], "detail:", d["detail"][:80])
        self.assertEqual(d["options"][0], "try again")


class VScan(unittest.TestCase):
    # V6 (AC-3): the real push scan over this branch's commits and diff, as pr.scans reads them.
    def test_v6_branch_scan_clean_and_strict(self):
        repo = str(T.parents[1])
        msgs = subprocess.run(["git", "-C", repo, "log", "--format=%H%n%B%x00", RANGE], capture_output=True,
                              text=True).stdout
        commits = [(f"commit {c.strip()[:12]}", c.strip().split("\n", 1)[1] if "\n" in c.strip() else "")
                   for c in msgs.split("\0") if c.strip()]
        diff = subprocess.run(["git", "-C", repo, "diff", RANGE], capture_output=True, text=True).stdout
        hits = pr.attribution_hits(commits, diff)
        whole = "Co-Authored-" + "By: Claude <x@example.invalid>"
        planted = diff.replace("\n+TRAILER = ", "\n+" + whole + "\n+TRAILER = ", 1)
        print("\nV6 branch hits:", hits, "commits:", len(commits), "diff lines:", diff.count("\n"),
              "\nV6 planted hits:", pr.attribution_hits(commits, planted))
        self.assertEqual(hits, [])
        self.assertEqual(len(pr.attribution_hits(commits, planted)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
