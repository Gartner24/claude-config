"""Scratch verify driver for row 71 (spec 0051 AC-3, AC-4, AC-12, AC-16). argv[1] = runner dir to load."""
import json
import os
import sys
import unittest
from unittest import mock

RUNNER = sys.argv.pop(1)
sys.path.insert(0, os.path.join(RUNNER, "tests"))
sys.path.insert(0, RUNNER)
import pr  # noqa: E402
import run  # noqa: E402
import test_clean_branches as tc  # noqa: E402


def show(tag, **kw):
    print(f"== {tag}: " + json.dumps(kw, default=str), flush=True)


class V(tc.Case):
    def test_1_risk_patterns(self):
        out = {}
        for path in ("config/routing.md", "claude-home/skills/x/SKILL.md", "claude-home/agents/a.md", "package.json",
                     "web/package.json", ".githooks/pre-push", ".husky/pre-commit", "hooks/x.sh",
                     ".claude/hooks/x.sh", "src/hooks/useThing.ts", "src/config/x.py"):
            self.git("switch", "-q", "work")
            rec, head = self.branch({path: "x\n"}, name="feat/" + path.replace("/", "-").strip("."), push=False)
            out[path] = pr.small_safe(self.r, rec, "origin/work", head)
        show("risk", **out)

    def test_2_nocheck_wait(self):
        rec, head = self.branch()
        self.views(head, checks=())
        res = []
        for t in (1000.0, 1599.0, 1600.0):
            why = []
            with mock.patch.object(pr.time, "time", return_value=t):
                ok = pr.green(self.r, rec, head, why)
            res.append({"t": t, "green": ok, "why": why, "suites_so_far": len(self.r.suites),
                        "saved": (pr.find(self.r, rec["repo"], rec["feature"]) or {}).get("nocheck_since")})
        show("nocheck", steps=res)

    def test_3_failing_check_no_suite(self):
        rec, head = self.branch()
        self.views(head, checks=[{"name": "ci", "conclusion": "FAILURE"}])
        why = []
        ok = pr.green(self.r, rec, head, why)
        show("check-first", green=ok, why=why, suites=len(self.r.suites))

    def test_4_new_head_resets(self):
        rec, head = self.branch()
        rec["nocheck_since"] = ["b" * 40, 0.0]
        self.views(head, checks=())
        with mock.patch.object(pr.time, "time", return_value=5000.0):
            ok = pr.green(self.r, rec, head)
        show("reset", green=ok, since=rec.get("nocheck_since"), suites=len(self.r.suites))

    def test_5_merge_note(self):
        rec, head = self.branch({"docs/x.md": "a\n"})
        self.views(head, checks=())
        with mock.patch.object(pr.time, "time", return_value=1000.0):
            res = pr.merge_green(self.r, rec)
        show("note", result=res, notes=self.r.notes, merges=len(self.merges()), state=rec["state"])

    def test_6_age(self):
        old = "@" + str(int(run.time.time()) - 3 * 86400 - 60)
        with mock.patch.dict(os.environ, {"GIT_AUTHOR_DATE": old}):
            rec, _ = self.branch(push=False)
        self.on_work({"main.txt": "fresh\n"})
        self.merge_work(rec)
        a = pr.warnings(self.r, rec)
        self.setUp()
        rec, _ = self.branch(push=False)
        with mock.patch.dict(os.environ, {"GIT_COMMITTER_DATE": old, "GIT_AUTHOR_DATE": old}):
            self.on_work({"main.txt": "old\n"})
        self.merge_work(rec)
        b = pr.warnings(self.r, rec)
        show("age", own_3_days_merged_fresh_main=a, fresh_merged_old_main=b)

    def on_work(self, files):
        for path, text in files.items():
            (self.repo / path).write_text(text)
        self.git("add", "-A")
        self.git("commit", "-qm", "main moves")

    def merge_work(self, rec):
        self.git("switch", "-q", rec["branch"])
        self.git("merge", "-q", "--no-edit", "work")
        self.git("switch", "-q", "work")


if __name__ == "__main__":
    unittest.main(verbosity=0)
