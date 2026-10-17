"""Scratch verify driver for spec 0051: real runner functions on real git repos, a fake gh (github.com unreachable)."""
import json
import os
import subprocess
import sys
import time
import unittest

T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "runner", "tests")
sys.path.insert(0, T)
sys.path.insert(0, os.path.dirname(T))
import pr  # noqa: E402
import run  # noqa: E402
import test_clean_branches as tc  # noqa: E402


def show(tag, **kw):
    print(f"== {tag}: " + json.dumps(kw, default=str), flush=True)


class V(tc.Case):
    def test_ac1_switch(self):
        rec, head = self.branch()
        on = pr.auto(self.r)
        (self.tmp / ".claude" / "private" / "pr.json").write_text(json.dumps({"acme/widgets": {}}))
        off = pr.auto(self.r)
        deny = run.never_writable(str(self.repo), None)
        show("AC-1", auto_with_flag=on, auto_without_flag=off,
             private_denied=any(os.path.expanduser("~/.claude/private") == p for p in deny))

    def test_ac2_combined(self):
        rec, head = self.branch()
        rec["combined"] = True
        self.views(head)
        res = pr.merge_green(self.r, rec)
        show("AC-2", merge_green=res, merges=self.merges(), state=rec["state"])

    def test_ac3_small_safe(self):
        out = {}
        for name, files in {"docs": {"docs/x.md": "a\n"}, "big": {"big.txt": "l\n" * 250},
                            "risky": {"runner/x.py": "x = 1\n"}, "auth": {"src/AuthForm.ts": "x\n"},
                            "many": {f"f{i}.txt": "a\n" for i in range(11)}}.items():
            self.git("switch", "-q", "work")
            rec, head = self.branch(files, name=f"feat/{name}", push=False)
            out[name] = pr.small_safe(self.r, rec, "origin/work", head)
        self.git("switch", "-q", "work")
        (self.repo / "lib.py").write_text("def keep():\n    pass\n\n\ndef run_step():\n    pass\n")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_lib.py").write_text("x = 1\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "lib")
        self.git("push", "-q", "origin", "work")
        rec, head = self.branch({"lib.py": "def keep():\n    pass\n"}, name="feat/rmdef", push=False)
        out["rmdef"] = pr.small_safe(self.r, rec, "origin/work", head)
        self.git("switch", "-q", "work")
        rec, head = self.branch({"tests/test_lib.py": None}, name="feat/rmtest", push=False)
        out["rmtest"] = pr.small_safe(self.r, rec, "origin/work", head)
        show("AC-3", **out)

    def test_ac4_green(self):
        rec, head = self.branch({"docs/x.md": "a\n", "AGENTS.md": tc.test_pr.ANSWERS + "- suite: true\n"})
        self.views(head, checks=[{"name": "ci", "conclusion": "SUCCESS"}])
        why = []
        ok = pr.green(self.r, rec, head, why)
        suites = list(self.r.suites)
        self.views(head, checks=[{"name": "ci", "conclusion": "FAILURE"}])
        why2 = []
        bad = pr.green(self.r, rec, head, why2)
        (self.repo / "docs" / "scope" / "scope.md").write_text(tc.SCOPE.replace("- [x] `/test a`", "- [ ] `/test a`"))
        why3 = []
        unticked = pr.green(self.r, rec, head, why3)
        show("AC-4", green=ok, suite_run=suites, failing_check=(bad, why2), unticked=(unticked, why3))

    def test_ac5_ac6_self_merge(self):
        rec, head = self.branch({"docs/x.md": "a\n"})
        (self.repo / "docs" / "other.md").write_text("main moved\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "main moves")
        self.git("push", "-q", "origin", "work")
        self.git("reset", "-q", "--hard", "HEAD~1")
        new = None
        # The fake PR head follows the branch after the update push.
        self.r.notes.clear()
        tip = lambda: self.git("rev-parse", f"refs/heads/{rec['branch']}")
        orig = pr.up_to_date

        def spy(r, rec_, default):
            res = orig(r, rec_, default)
            self.views(tip(), checks=[{"name": "ci", "conclusion": "SUCCESS"}], land=str(self.origin))
            return res
        pr.up_to_date = spy
        try:
            res = pr.merge_green(self.r, rec)
        finally:
            pr.up_to_date = orig
        parents = subprocess.run(["git", "--git-dir", str(self.origin), "log", "-1", "--format=%P %s",
                                  "refs/heads/feat/0001-a"], capture_output=True, text=True).stdout.strip()
        local = subprocess.run(["git", "-C", str(self.repo), "branch", "--list", "feat/0001-a"],
                               capture_output=True, text=True).stdout.strip()
        show("AC-5/6", result=res, state=rec["state"], merges=self.merges(), notes=self.r.notes,
             pushed_branch_tip_parents_and_subject=parents, local_branch_after=local)

    def test_ac6_conflict(self):
        rec, head = self.branch({"docs/x.md": "branch\n"})
        (self.repo / "docs" / "x.md").write_text("main\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "main clashes")
        self.git("push", "-q", "origin", "work")
        self.views(head)
        res = pr.merge_green(self.r, rec)
        mh = (self.repo / ".git" / "MERGE_HEAD").exists()
        show("AC-6 conflict", result=res, asked=self.r.asked, merge_head_left=mh, merges=self.merges(),
             branch_tip_unchanged=self.git("rev-parse", "feat/0001-a") == head)

    def test_ac7_cleanup(self):
        rec, head = self.branch()
        self.gh({"views": [{"state": "CLOSED", "headRefOid": head}]})
        self.r.repo["origin_url"] = tc.test_pr.ORIGIN
        notes = pr.cleanup(self.r, rec)
        remote = subprocess.run(["git", "--git-dir", str(self.origin), "branch", "--list", "feat/0001-a"],
                                capture_output=True, text=True).stdout.strip()
        local = self.git("branch", "--list", "feat/0001-a")
        # A branch with commits after the PR head is kept.
        rec2, head2 = self.branch(name="feat/0002-b", push=True)
        self.git("switch", "-q", "feat/0002-b")
        (self.repo / "later.txt").write_text("x\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "later")
        self.git("switch", "-q", "work")
        self.gh({"views": [{"state": "MERGED", "headRefOid": head2}]})
        notes2 = pr.cleanup(self.r, rec2)
        show("AC-7", closed_notes=notes, remote_left=remote, local_left=local, ahead_notes=notes2,
             ahead_local=self.git("branch", "--list", "feat/0002-b"))

    def test_ac8_ready(self):
        rec, head = self.branch({"runner/x.py": "x = 1\n"})
        self.views(head, checks=[{"name": "ci", "conclusion": "SUCCESS"}])
        pr.merge_green(self.r, rec)
        asked = list(self.r.asked)
        extra = list(self.r.extras)
        d = {"case": "merge_ready", "asked_head": head, "answer": "later", "repo": str(self.repo),
             "feature": rec["feature"], "options": ["merge now", "later"], "source": "keyboard"}
        self.r.q["decisions"] = []
        pr.ready_answer(self.r, rec, d)
        later = rec.get("later")
        pr.ready_answer(self.r, rec, dict(d, answer="sure go ahead"))
        m_after_other = len(self.merges())
        pr.ready_answer(self.r, rec, dict(d, answer="merge now", source="ntfy"))
        m_after_weak = len(self.merges())
        # The head moves after the question: merge now asks again naming the new head.
        self.git("switch", "-q", "feat/0001-a")
        (self.repo / "more.txt").write_text("m\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "more")
        self.git("push", "-q", "origin", "feat/0001-a")
        self.git("switch", "-q", "work")
        rec["pushed_sha"] = self.git("rev-parse", "feat/0001-a")
        self.r.asked.clear()
        pr.ready_answer(self.r, rec, dict(d, answer="merge now"))
        moved_ask = list(self.r.asked)
        m_after_moved = len(self.merges())
        new = self.git("rev-parse", "feat/0001-a")
        self.views(new, checks=[{"name": "ci", "conclusion": "SUCCESS"}])
        (self.fakes / "gh-views").unlink(missing_ok=True)
        pr.ready_answer(self.r, rec, dict(d, answer="merge now", asked_head=new))
        show("AC-8", asked=asked, extras=extra, later=later, merges_after_other_reply=m_after_other,
             merges_after_ntfy_no_code=m_after_weak, moved_ask=moved_ask, merges_after_moved=m_after_moved,
             final_merges=self.merges(), state=rec["state"], notes=self.r.notes)

    def test_ac9_allow(self):
        s = "a" * 40
        good = ["pr", "merge", "7", "--repo", "o/r", "--squash", "--delete-branch", "--match-head-commit", s]
        res = {"green_ok": pr.allowed(good, green=True), "no_green": pr.allowed(good),
               "admin": pr.allowed(good + ["--admin"], green=True), "auto": pr.allowed(good[:-1] + ["--auto", s], green=True),
               "ready_green": pr.allowed(["pr", "ready", "7", "--repo", "o/r"], green=True),
               "ready_plain": pr.allowed(["pr", "ready", "7", "--repo", "o/r"]),
               "create_nodraft_plain": pr.allowed(["pr", "create", "--repo", "o/r", "--base", "main", "--head", "x",
                                                   "--title", "t", "--body-file", "/tmp/b"]),
               "rulesets": pr.allowed(["api", "repos/o/r/rulesets"])}
        try:
            pr.gh("true", *good, "--admin", green=True)
            res["gh_raises"] = False
        except pr.Refused:
            res["gh_raises"] = True
        show("AC-9", **res)

    def test_ac10_settings(self):
        self.gh({"methods": {**tc.GOOD, "mergeCommitAllowed": True}, "rulesets": []})
        off = pr.settings_check(self.r)
        show("AC-10 runner", off=off, notes=self.r.notes, settings_off=self.r.repo.get("settings_off"))

    def test_ac12_warnings(self):
        old = "2026-10-10T10:00:00"
        os.environ["GIT_AUTHOR_DATE"] = old
        os.environ["GIT_COMMITTER_DATE"] = old
        try:
            rec, head = self.branch({"big.txt": "l\n" * 450}, push=False)
        finally:
            del os.environ["GIT_AUTHOR_DATE"], os.environ["GIT_COMMITTER_DATE"]
        old_w = pr.warnings(self.r, rec)
        self.git("switch", "-q", "work")
        rec2, _ = self.branch({"s.txt": "s\n"}, name="feat/small", push=False)
        show("AC-12", old_large=old_w, fresh_small=pr.warnings(self.r, rec2))

    def test_ac12_publish(self):
        rec, head = self.branch({"docs/big.md": "l\n" * 450}, push=False)
        rec.update(state="local", number=None, pr=None)
        self.views(head, checks=[{"name": "ci", "conclusion": "SUCCESS"}])
        pr.publish(self.r, rec)
        create = next((c for c in self.gh_calls() if c[:2] == ["pr", "create"]), None)
        body = None
        if create and os.path.exists(create[-1]):
            body = [l for l in open(create[-1]).read().splitlines() if l.startswith(("large:", "old:"))]
        show("AC-12 publish", body_warn_lines=body, create=create, state=rec["state"], asked=self.r.asked, notes=self.r.notes,
             merges=self.merges())

    def test_ac13_cases(self):
        show("AC-13", ready=run.plain_question("merge_ready", "1. A", "PR #7 ..."),
             conflict=run.plain_question("merge_conflict", "1. A", "feat clashes"),
             cases=[run.CASES[c][1] for c in ("merge_ready", "merge_conflict")])

    def test_ac15_land_plan(self):
        (self.repo / "docs" / "scope" / "scope.md").write_text(tc.SCOPE + "\nplan note\n")
        self.git("commit", "-qam", "docs(scope): note")
        self.gh({"land": str(self.origin)})
        self.r.repo["start_branch"] = "work"
        res = pr.land_plan(self.r)
        calls = [c[:2] + [x for x in c if x in ("--draft", "--squash", "--delete-branch")] for c in self.gh_calls()]
        heads = subprocess.run(["git", "--git-dir", str(self.origin), "for-each-ref", "--format=%(refname)"],
                               capture_output=True, text=True).stdout.split()
        synced = self.git("rev-parse", "work") == self.git("rev-parse", "origin/work")
        (self.repo / "code.py").write_text("x\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "code")
        self.r.notes.clear()
        res2 = pr.land_plan(self.r)
        show("AC-15", result=res, gh=calls, origin_refs=heads, local_synced=synced, outside=(res2, self.r.notes))


if __name__ == "__main__":
    unittest.main(verbosity=0)
