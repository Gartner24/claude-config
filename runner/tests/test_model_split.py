"""Spec 0055: search helpers on haiku, per model cost in call records, the run and week split, the 15% gate."""
import datetime
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import report  # noqa: E402
import run  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
USAGE = {"claude-opus-5-5[1m]": {"inputTokens": 228, "outputTokens": 68258, "costUSD": 8.06},
         "claude-haiku-5-5": {"inputTokens": 76, "outputTokens": 1055, "costUSD": 0.12}}


def call(started, models, cost=None):
    return {"started": started.isoformat(timespec="seconds"), "models": models,
            "cost_usd": cost if cost is not None else sum(v["cost_usd"] for v in (models or {}).values())}


def split(main, other):
    return {"claude-opus-5-5[1m]": {"cost_usd": main, "output_tokens": 1},
            "claude-haiku-5-5": {"cost_usd": other, "output_tokens": 1}}


class TestPins(unittest.TestCase):
    # covers: spec 0055 AC-1 (every agent pins a model; the haiku set is exactly the five read only helpers)
    def test_pins(self):
        files = sorted((REPO / "claude-home" / "agents").glob("*.md"))
        pins = {f.stem: re.search(r"^model:\s*(\S+)", f.read_text(), re.M) for f in files}
        missing = [n for n, m in pins.items() if not m]
        self.assertEqual(missing, [], f"{len(missing)} agents without a model line: {missing}")
        haiku = sorted(n for n, m in pins.items() if m and m.group(1) == "haiku")
        self.assertEqual(haiku, ["code-explorer", "doc-updater", "docs-lookup", "researcher", "scout"])

    # covers: spec 0055 AC-2 (the subagent model rule names haiku for read only search)
    def test_rule(self):
        text = " ".join((REPO / "claude-home" / "rules" / "lessons.md").read_text().split())
        self.assertIn("haiku for read only search and lookup helpers, sonnet for review and simple edits, "
                      "opus only for architecture and hard debugging", text)


class TestRecord(unittest.TestCase):
    # covers: spec 0055 AC-3 (models dict keyed as modelUsage returns it; absent or empty gives None)
    def test_models(self):
        self.assertEqual(run.model_costs(USAGE), {
            "claude-opus-5-5[1m]": {"cost_usd": 8.06, "output_tokens": 68258},
            "claude-haiku-5-5": {"cost_usd": 0.12, "output_tokens": 1055}})
        self.assertIsNone(run.model_costs(None))
        self.assertIsNone(run.model_costs({}))

    # covers: spec 0055 AC-3 (the main model is the largest cost key, the rest counts as non main)
    def test_split(self):
        per, other, total, used, skipped = run.split([{"models": split(1.0, 3.0), "cost_usd": 4.0}, {"models": None}])
        self.assertEqual((per, other, total, used, skipped),
                         ({"claude-opus-5-5[1m]": 1.0, "claude-haiku-5-5": 3.0}, 1.0, 4.0, 1, 1))
        # covers: spec 0055 AC-5 (the denominator is the call's own cost_usd, the model sum only when it is missing)
        self.assertEqual(run.split([{"models": split(1.0, 3.0), "cost_usd": 10.0},
                                    {"models": split(2.0, 0.5), "cost_usd": None}])[2], 12.5)


class TestReport(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.runs = os.path.join(tmp.name, "wf", "runs")
        env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": tmp.name})
        env.start()
        self.addCleanup(env.stop)
        self.now = datetime.datetime.now().astimezone()

    def write(self, name, calls):
        os.makedirs(os.path.join(self.runs, name))
        with open(os.path.join(self.runs, name, "run.json"), "w") as f:
            json.dump({"calls": calls}, f)

    # covers: spec 0055 AC-4 (one run line by model id with the non main share, unknown with no split)
    def test_run_line(self):
        recs = [{"calls": [{"models": split(3.0, 1.0), "cost_usd": 4.0}, {"models": None}]}]
        self.assertEqual(report.model_line(recs), ["models: claude-opus-5-5[1m] $3.00, claude-haiku-5-5 $1.00; non main 25%"])
        self.assertEqual(report.model_line([{"calls": [{"models": None}]}]), ["model split: unknown"])

    # covers: spec 0055 AC-5 (over 15% in the last 7 days prints the gate; older calls are left out)
    def test_week_gate(self):
        self.write("a", [call(self.now - datetime.timedelta(days=1), split(8.0, 2.0)),
                         call(self.now - datetime.timedelta(days=2), None, cost=5.0),
                         call(self.now - datetime.timedelta(days=9), split(1.0, 0.0))])
        self.assertEqual(report.week_line(), [
            "week: non main models 20% of $10.00 (upper bound for helper cost; 1 calls without a split skipped)",
            "consider a routing mod (spec 0055)"])

    # covers: spec 0055 AC-5 (under 15% prints no gate line)
    def test_week_under(self):
        self.write("a", [call(self.now - datetime.timedelta(days=1), split(9.0, 1.0))])
        self.assertEqual(report.week_line(), [
            "week: non main models 10% of $10.00 (upper bound for helper cost; 0 calls without a split skipped)"])

    # covers: spec 0055 AC-5 (only unsplit calls, or none, reads unknown, never 0%)
    def test_week_unknown(self):
        self.assertEqual(report.week_line(), ["week: unknown"])
        self.write("a", [call(self.now, None, cost=5.0)])
        self.assertEqual(report.week_line(), ["week: unknown"])


if __name__ == "__main__":
    unittest.main()
