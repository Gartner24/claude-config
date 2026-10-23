"""tools/bin/repo-settings.sh (spec 0051 AC-10): copied from the archived runner suite, which no longer runs."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "tools" / "bin"
# gh for tools/bin/repo-settings.sh: reads answer from settings.json by API path (the --jq result), writes are logged.
SETTINGS_GH = f"""#!{sys.executable}
import json, os, sys
d = os.environ["FAKE_DIR"]
a = sys.argv[1:]
open(os.path.join(d, "gh-argv.jsonl"), "a").write(json.dumps(a) + "\\n")
cfg = json.load(open(os.path.join(d, "settings.json")))
if "-X" in a:
    print("{{}}")
elif a[1].endswith("/rulesets"):
    lists = sum(1 for l in open(os.path.join(d, "gh-argv.jsonl")) if json.loads(l)[1].endswith("/rulesets"))
    print(cfg.get("id", "") if lists >= cfg.get("listed_at", 0) else "")
elif "/rulesets/" in a[1]:
    print(cfg["shape"])
else:
    print(cfg["repo"][a[3].lstrip(".")])
"""
REPO_OK = {"allow_squash_merge": "true", "allow_merge_commit": "false", "allow_rebase_merge": "false",
           "delete_branch_on_merge": "true", "squash_merge_commit_title": "PR_TITLE",
           "squash_merge_commit_message": "PR_BODY"}
SHAPE_OK = "active branch ~DEFAULT_BRANCH deletion,non_fast_forward,pull_request 0 0"


class TestRepoSettings(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.fakes = self.tmp / "fakes"
        self.fakes.mkdir()
        self.gh_bin = self.tmp / "gh"
        self.gh_bin.write_text(SETTINGS_GH)
        self.gh_bin.chmod(0o755)

    def script(self, *args, **cfg):
        (self.fakes / "settings.json").write_text(json.dumps({"repo": REPO_OK, "id": "5", "shape": SHAPE_OK, **cfg}))
        (self.fakes / "gh-argv.jsonl").unlink(missing_ok=True)
        return subprocess.run(["bash", str(BIN / "repo-settings.sh"), *args], capture_output=True, text=True,
                              env={**os.environ, "GH": str(self.gh_bin), "FAKE_DIR": str(self.fakes), "RS_SLEEP": "0"},
                              timeout=60)

    def writes(self):
        p = self.fakes / "gh-argv.jsonl"
        return [x for x in map(json.loads, p.read_text().splitlines()) if "-X" in x] if p.exists() else []

    # covers: AC-10 (bad arguments refuse with exit 2; --check only reads: 0 when all match, 1 and one line per
    # difference otherwise, the ruleset's rules and bypass included)
    def test_check(self):
        for args in ((), ("--check",), ("o/r", "p/q"), ("--force", "o/r"), ("not a repo",)):
            with self.subTest(args):
                self.assertEqual(self.script(*args).returncode, 2)
        r = self.script("--check", "o/r")
        self.assertEqual((r.returncode, r.stdout), (0, ""), r.stderr)
        r = self.script("--check", "o/r", repo={**REPO_OK, "allow_merge_commit": "true"},
                        shape=SHAPE_OK.replace(" 0 0", " 0 1"))
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout.splitlines(), ["allow_merge_commit is true, wants false",
                                                 f"ruleset 'main only through a PR' is: {SHAPE_OK[:-1]}1; wants: {SHAPE_OK}"])
        r = self.script("--check", "o/r", id="")
        self.assertEqual((r.returncode, r.stdout), (1, "no ruleset named 'main only through a PR'\n"))
        self.assertEqual(self.writes(), [])

    # covers: AC-10 (without --check: the six settings by one PATCH, the ruleset created when missing, else updated)
    def test_set(self):
        r = self.script("o/r", id="")
        [patch, post] = self.writes()
        self.assertEqual(patch[:4], ["api", "-X", "PATCH", "repos/o/r"])
        self.assertEqual(patch[4:], ["-F", "allow_squash_merge=true", "-F", "allow_merge_commit=false", "-F",
                                     "allow_rebase_merge=false", "-F", "delete_branch_on_merge=true", "-f",
                                     "squash_merge_commit_title=PR_TITLE", "-f", "squash_merge_commit_message=PR_BODY"])
        self.assertEqual(post, ["api", "-X", "POST", "repos/o/r/rulesets", "--input", "-"])
        self.assertEqual(r.returncode, 1, "the fake never lists the ruleset, so the closing check says so")
        r = self.script("o/r")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.writes()[1], ["api", "-X", "PUT", "repos/o/r/rulesets/5", "--input", "-"])

    # covers: AC-10 (first run: the new ruleset is not listed right after the POST, so the closing check retries)
    def test_first_run(self):
        r = self.script("o/r", listed_at=3)  # list 1 is the pre-check, 2 the first closing read, 3 the retry
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[-1], "repo-settings: o/r set")
        self.assertEqual(self.writes()[1][:3], ["api", "-X", "POST"])


if __name__ == "__main__":
    unittest.main()
