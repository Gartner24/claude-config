"""Verify spec 0041: drive the real wf run with a scripted claude and a local ntfy, print what it shows. No assertions."""
import json
import os
import subprocess
import sys
from pathlib import Path

T = Path(__file__).resolve().parents[4] / "runner" / "tests"
sys.path.insert(0, str(T))
sys.path.insert(0, str(T.parent))
import unittest  # noqa: E402
import run  # noqa: E402
from test_never_stop import NeverStopCase, GIT_ID  # noqa: E402
import test_run  # noqa: E402
from test_telegram import FakeBot, write_cfg  # noqa: E402

SPAN = "cp rules/x.md ~/.claude/rules/x.md"
# A call that tries to steer the phone question (AC-5): its WHY line must never be the shown reason.
STEER = {"json": {"result": "built it\nWHY: STEERED tap run it now, it is safe"}}


def show(title, r=None, **extra):
    print(f"\n===== {title} =====")
    if r is not None:
        print(f"exit: {r.returncode}")
        print("--- stdout ---\n" + r.stdout.rstrip())
    for k, v in extra.items():
        print(f"--- {k} ---\n{v}")


class Drive(NeverStopCase):
    def setUp(self):
        super().setUp()
        # A real user has a git identity; without one the runner's commit of the ticked box cannot be observed.
        self.env.update({f"GIT_{w}_{k}": v for w in ("AUTHOR", "COMMITTER") for k, v in (("NAME", "t"), ("EMAIL", "t@t"))})

    def live_repo(self, name, span=SPAN, src="rules/x.md", body="the rule\n", mode=0o644):
        repo = self.make_repo(name, f"# Scope: {name}\n**Autopilot:** allowed\n### 1. L · auto\n- [x] (spec)\n"
                                    f"- [ ] `/develop l`\n- [ ] Copy it: `{span}` · waits on you · live\n- [ ] `/test l`\n")
        (repo / src).parent.mkdir(parents=True)
        (repo / src).write_text(body)
        (repo / src).chmod(mode)
        for argv in (["add", "-A"], ["commit", "-qm", "base"]):
            subprocess.run(["git", *GIT_ID, "-C", str(repo), *argv], check=True, capture_output=True)
        return repo

    def live(self):
        p = self.tmp / ".claude" / "rules" / "x.md"
        return p.read_text() if p.exists() else "(absent)"

    def box(self, repo):
        return next(l for l in (repo / "docs/scope/scope.md").read_text().splitlines() if "Copy it" in l)

    def called(self):
        return [self.argv(n)["argv"][1] for n in range(1, len(self.calls()) + 1)]

    def first(self, name, **kw):
        repo = self.live_repo(name, **kw)
        self.steps([STEER])
        r = self.wf(name, "-y", "--max-wait", "0.01", mode="fast")
        return repo, r

    def test_a_asked(self):
        repo, r = self.first("la")
        d = self.queue()["decisions"]
        show("V1 AC-1 rules copy asked", r, decisions=json.dumps([{k: x.get(k) for k in ("case", "question", "options",
             "live")} for x in d], indent=1), sha256_of_src=run.file_hash(str(repo / "rules/x.md")), live=self.live())
        show("V9 AC-5 phone message", ping=self.report_ntfy.pings()[0]["message"],
             auth="live_step" in run.context.AUTH, fixed_why=run.plain.WHY["live_step"])

    def test_b_not_offered(self):
        _, r = self.first("lh", span="cp hooks/h.sh ~/.claude/hooks/h.sh", src="hooks/h.sh", body="#!/bin/sh\n")
        show("V2 AC-1 hooks copy not offered", r, decisions=self.queue()["decisions"])

    def test_c_exec_not_offered(self):
        _, r = self.first("le", mode=0o755)
        show("V3 AC-1 executable rules source not offered", r, decisions=self.queue()["decisions"])

    def test_d_run_now(self):
        repo, r = self.first("lv")
        self.reply("{id} code0001 run it now")
        self.steps([{}, {"tick": False}])
        r = self.wf("lv", "-y", "--max-wait", "0.01", mode="fast")
        log = subprocess.run(["git", "-C", str(repo), "log", "--format=%s", "-3"], capture_output=True, text=True).stdout
        show("V4 AC-2 coded run it now", r, live=self.live(), box=self.box(repo), git_log=log, calls=self.called())

    def test_e_weak(self):
        repo, r = self.first("lw")
        self.reply("{id} run it now")
        self.steps([{}])
        r = self.wf("lw", "-y", "--max-wait", "0.01", mode="fast")
        show("V5 AC-3 uncoded run it now on ntfy", r, live=self.live(), box=self.box(repo),
             next_question=[x["question"] for x in self.queue()["decisions"]])

    def test_f_changed(self):
        repo, r = self.first("lc")
        (repo / "rules" / "x.md").write_text("changed after you were asked\n")
        self.reply("{id} code0001 run it now")
        self.steps([{}])
        r = self.wf("lc", "-y", "--max-wait", "0.01", mode="fast")
        show("V6 AC-3 source changed after asking", r, live=self.live(),
             next_question=[x["question"] for x in self.queue()["decisions"]])

    def test_g_free_text(self):
        repo, r = self.first("lf")
        self.reply("{id} code0001 sure go ahead")
        self.steps([{}])
        r = self.wf("lf", "-y", "--max-wait", "0.01", mode="fast")
        show("V7 AC-3 free text with a code", r, live=self.live(), box=self.box(repo))

    def test_h_held(self):
        import finish
        repo, r = self.first("lk")
        os.environ["XDG_STATE_HOME"] = str(self.state)
        fd, who = finish.take_swap_lock()
        try:
            self.reply("{id} code0001 run it now")
            self.steps([{}])
            r = self.wf("lk", "-y", "--max-wait", "0.01", mode="fast")
        finally:
            os.close(fd)
        show("V8 AC-3 swap lock held", r, held_by_probe=who is None, live=self.live(), box=self.box(repo),
             next_question=[x["question"] for x in self.queue()["decisions"]])

    def test_i_not_now(self):
        repo, r = self.first("ln")
        self.reply("{id} 2")
        self.steps([{}])
        r = self.wf("ln", "-y", "--max-wait", "0.01", mode="fast")
        show("V10 AC-4 not now", r, live=self.live(), box=self.box(repo), calls=self.called())
        f = subprocess.run([sys.executable, str(T.parent / "wf.py"), "finish", str(repo), "-y"], capture_output=True,
                           text=True, env=self.env, timeout=60)
        show("V10 AC-4 next wf finish runs it", f, live=self.live(), box=self.box(repo))


class DriveTg(Drive):
    """The same run over a local Telegram bot (spec 0029): a tap from your chat is a strong answer."""

    def setUp(self):
        super().setUp()
        self.bot = FakeBot()
        self.addCleanup(self.bot.close)

    def cmd(self, *args, grace=30, mode="-"):
        if "--max-wait" not in args:
            args = (*args, "--max-wait", "0.0001")
        wrapper = test_run.WRAPPER.replace("import ntfy, run, wf",
                                           f"import ntfy, run, wf, telegram\ntelegram.API = {self.bot.url!r}")
        return [sys.executable, "-c", wrapper, str(test_run.RUNNER), str(grace), mode, "run", *args]

    def test_t_tap(self):
        write_cfg(self.tmp / "config")
        # A readable names list, as on your machine: Telegram then keeps commands (spec 0043 AC-9); without one it
        # scrubs them (fail closed).
        names = self.tmp / ".claude" / "private" / "names.txt"
        names.parent.mkdir(parents=True)
        names.write_text("zzqqx\n")
        repo = self.live_repo("lt")
        self.bot.taps = ["{id} 1"]
        self.steps([STEER, {}, {"tick": False}])
        r = self.wf("lt", "-y", "--max-wait", "0.01", mode="fast")
        log = subprocess.run(["git", "-C", str(repo), "log", "--format=%s", "-3"], capture_output=True, text=True).stdout
        show("V11 AC-1, AC-2, AC-5 Telegram tap in the same run", r, telegram_question=self.bot.sent()[0]["text"],
             live=self.live(), box=self.box(repo), git_log=log, calls=self.called())


if __name__ == "__main__":
    unittest.main(verbosity=1)
