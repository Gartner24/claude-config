import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / "claude-home/workflows/restructure-check"
JS = WF / "restructure-check.js"

SHA = "a" * 40
GOOD = {"repo": "/r", "runId": "1", "head": "refs/heads/feat/x", "headSha": SHA,
        "base": "b" * 40, "ownerChecked": True}

# Runs the real script body with stub agent/phase/log; agent returns null so a valid run ends after 01_capture.
RUNNER = """
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8').replace('export const meta', 'const meta');
const args = JSON.parse(process.argv[2]);
const prompts = [];
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
new AsyncFunction('args', 'agent', 'phase', 'log', src)(args, async (p) => { prompts.push(p); return null }, () => {}, () => {})
  .then(() => console.log(JSON.stringify({ ok: true, prompts })))
  .catch((e) => console.log(JSON.stringify({ ok: false, error: e.message })));
"""


def run(**over):
    args = {**GOOD, **over}
    args = {k: v for k, v in args.items() if v is not None}
    out = subprocess.run(["node", "-e", RUNNER, str(JS), json.dumps(args)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


class ArgRefusal(unittest.TestCase):
    def test_good_args_pass_and_capture_uses_pinned_sha(self):
        r = run()
        self.assertTrue(r["ok"], r)
        self.assertIn("head " + SHA, r["prompts"][1])
        self.assertIn("base " + GOOD["base"], r["prompts"][0])

    def test_pr_ref_passes(self):
        self.assertTrue(run(head="refs/restructure-check/pr-12")["ok"])

    def test_refuses_unverified_owner(self):
        self.assertFalse(run(ownerChecked=False)["ok"])
        self.assertFalse(run(ownerChecked=None)["ok"])

    def test_refuses_bad_head(self):
        for head in ["main", "origin/main", "refs/heads/../x", "refs/restructure-check/pr-x",
                     "refs/remotes/origin/x", "-x", "refs/heads/a b"]:
            self.assertFalse(run(head=head)["ok"], head)

    def test_refuses_bad_sha(self):
        for key in ["headSha", "base"]:
            for v in ["HEAD", "abc123", "A" * 40, "a" * 39, "a" * 41, "origin/main"]:
                self.assertFalse(run(**{key: v})["ok"], (key, v))

    def test_missing_arg(self):
        self.assertFalse(run(headSha=None)["ok"])


class SpecNumber(unittest.TestCase):
    def test_rule_is_stated_and_holds_for_every_real_spec(self):
        ctx = (WF / "stages/01_capture/CONTEXT.md").read_text()
        self.assertIn("first 4 digits", ctx)
        self.assertIn("never a fragment of `index`", ctx)
        bad = []
        tops = list((ROOT / "docs/specs").glob("[0-9][0-9][0-9][0-9]-*"))
        for p in tops:
            if re.match(r"^\d{4}$", p.name[:4]) is None:
                bad.append(p.name)
        self.assertEqual(bad, [], f"{len(bad)} spec names without a 4 digit prefix")
        self.assertGreater(len(tops), 0)


if __name__ == "__main__":
    unittest.main()
