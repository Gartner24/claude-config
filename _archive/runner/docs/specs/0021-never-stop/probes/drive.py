"""Verify spec 0021: drive the real wf run with a scripted claude and print what it shows. No assertions."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

T = Path(__file__).resolve().parents[4] / "runner" / "tests"
sys.path.insert(0, str(T))
sys.path.insert(0, str(T.parent))
import unittest  # noqa: E402
import run  # noqa: E402
from test_never_stop import TestReport, AllowCase, TWO, B_DONE, BLOCKED, GIT_ID  # noqa: E402


def show(title, r=None, **extra):
    print(f"\n===== {title} =====")
    if r is not None:
        print(f"exit: {r.returncode}")
        print("--- stdout ---\n" + r.stdout.rstrip())
        if r.stderr.strip():
            print("--- stderr ---\n" + r.stderr.rstrip())
    for k, v in extra.items():
        print(f"--- {k} ---\n{v}")


class Drive(AllowCase, TestReport):
    def commit(self, repo):
        for argv in (["add", "-A"], ["commit", "-qm", "base"]):
            subprocess.run(["git", *GIT_ID, "-C", str(repo), *argv], check=True, capture_output=True)

    def report(self):
        p = self.state / "wf" / "report.txt"
        return p.read_text() if p.exists() else "(none)"

    def reset(self):
        for f in [self.fakes / "count", *self.fakes.glob("argv-*.json")]:
            if f.exists():
                f.unlink()
        shutil.rmtree(self.state / "wf" / "runs", ignore_errors=True)

    def test_a_ac1_table(self):
        reasons = run.PARKS | run.REPO_STOPS | run.RUN_STOPS
        show("AC-1 case table", missing=sorted(reasons - set(run.CASES)),
             rows={r: run.CASES[r] for r in sorted(reasons)})

    def test_b_ac2_ac3_ac6_blocked(self):
        two = self.make_repo("two", TWO)
        self.commit(two)
        self.steps([BLOCKED, B_DONE, {"tick": False}])
        r = self.wf("two", "-y")
        show("AC-2/AC-6 blocked park, queue goes on", r, queue=json.dumps(self.queue()["decisions"], indent=1),
             report=self.report(), ping=self.report_ntfy.pings()[0]["message"])
        self.reset()
        self.reply("{id} 1")
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("two", "-y", "--max-wait", "0.01", mode="fast")
        show("AC-3 answer 1 (done, go on) resumes", r, calls=[self.argv(n)["argv"][1] for n in (1, 2, 3)],
             hint_in_prompt=run.HINT_PROMPT.split("{")[0] in self.prompt(1), queue=json.dumps(self.queue()))

    def test_c_f1_always(self):
        docs = self.tmp / ".claude" / "docs"
        docs.mkdir(parents=True)
        target = str(docs / "x.md")
        deny = {"tick": False, "json": {"permission_denials": [
            {"tool_name": "Write", "tool_use_id": "t1", "tool_input": {"file_path": target, "content": "x"}}]}}
        self.reply("{id} 2")
        self.steps([deny, {}, {}, {"tick": False}])
        r = self.wf("demo", "-y", "--max-wait", "0.01", mode="fast")
        p = self.tmp / "config" / "wf" / "allow.json"
        show("F1/AC-7 always", r, allow_json=p.read_text() if p.exists() else "(none)",
             mode=oct(p.stat().st_mode & 0o777) if p.exists() else "-",
             rerun_allowWrite=self.settings(2)["sandbox"]["filesystem"]["allowWrite"])
        self.reset()
        rules = str(self.tmp / ".claude" / "rules" / "x.md")
        p2 = self.state / "wf" / "queue.json"
        p2.unlink()
        self.steps([{"tick": False, "json": {"permission_denials": [
            {"tool_name": "Write", "tool_use_id": "t1", "tool_input": {"file_path": rules, "content": "x"}}]}}])
        r = self.wf("demo", "-y")
        show("F1 never writable ~/.claude/rules offers no allow", r,
             decision=json.dumps(self.queue()["decisions"], indent=1))

    def test_d_cli_allow_writes(self):
        env = dict(self.env, WF_RUN="1")
        wf = str(T.parent / "wf.py")
        r1 = subprocess.run([sys.executable, wf, "allow-writes", str(self.repo), str(self.tmp / "out")],
                            capture_output=True, text=True, env=env)
        r2 = subprocess.run([sys.executable, wf, "allow-writes", str(self.repo), str(self.tmp / ".bashrc")],
                            capture_output=True, text=True, env=self.env)
        r3 = subprocess.run([sys.executable, wf, "allow-writes", str(self.repo), str(self.tmp / "out")],
                            capture_output=True, text=True, env=self.env)
        p = self.tmp / "config" / "wf" / "allow.json"
        show("AC-7 wf allow-writes", None, inside_run=f"{r1.returncode} {r1.stdout}{r1.stderr}",
             bashrc=f"{r2.returncode} {r2.stdout}{r2.stderr}", ok=f"{r3.returncode} {r3.stdout}{r3.stderr}",
             allow_json=p.read_text() if p.exists() else "(none)")
        (self.repo / "AGENTS.md").write_text("# x\n\n## Standing answers\n\n- allow writes: /tmp/x\n")
        self.steps([{}, {}, {"tick": False}])
        self.reset()
        r = self.wf("demo", "-y")
        show("AC-7 AGENTS.md allow writes line ignored", r)

    def test_e_ac4_main(self):
        repo = self.make_repo("onmain", TWO, head="ref: refs/heads/main\n")
        self.commit(repo)
        self.steps([{}, {}, {"tick": False}, B_DONE, {"tick": False}])
        r = self.wf("onmain", "-y")
        show("AC-4 on main", r, head=(repo / ".git" / "HEAD").read_text(), decisions=self.queue()["decisions"])

    def test_f_ac5_guard(self):
        (self.tmp / ".claude").mkdir()
        s = self.tmp / ".claude" / "settings.json"
        s.write_text("{}")
        other = self.make_repo("other", TWO)
        self.commit(other)
        self.steps([{"write_file": [[str(s), '{"x": 1}']]}, {}, {}, {"tick": False}])
        r = self.wf("-y")
        show("AC-5/U5 guard change outside run, bare wf with two repos", r,
             decisions=json.dumps(self.queue()["decisions"], indent=1), report=self.report())

    def test_g_ac8_names(self):
        self.names("# list", "secretco==>client")
        self.steps([{}, {}, {"tick": False}])
        self.wf("demo", "-y")
        show("AC-8 report names repo", None, body_last=self.body().splitlines()[-1])
        self.make_repo("secretco-site", run_scope())
        self.reset()
        self.wf("secretco-site", "-y")
        show("AC-8 private name hidden", None, body_last=self.body().splitlines()[-1])

    def test_h_ac10_prune(self):
        runs = self.state / "wf" / "runs"
        runs.mkdir(parents=True)
        for i in range(60):
            d = runs / f"old-20260101-{i:06d}-4194311"
            d.mkdir()
            (d / "run.json").write_text("{}")
            os.utime(d, (1_000_000 + i, 1_000_000 + i))
        self.steps([{}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        show("AC-10 prune", None, pruned_lines=r.stdout.count("pruned: "), left=len(list(runs.iterdir())),
             oldest_left=sorted(p.name for p in runs.iterdir())[:2])


class Drive2(Drive):
    def test_i_f1_never(self):
        rules = str(self.tmp / ".claude" / "rules" / "x.md")
        self.steps([{"tick": False, "json": {"permission_denials": [
            {"tool_name": "Write", "tool_use_id": "t1", "tool_input": {"file_path": rules, "content": "x"}}]}}])
        r = self.wf("demo", "-y")
        show("F1 never writable ~/.claude/rules offers no allow", r,
             decision=[(d["case"], d["options"], d["allow"]) for d in self.queue()["decisions"]])

    def test_j_u6_crash_loop(self):
        two = self.make_repo("two", TWO)
        self.commit(two)
        rm = {"tick": False, "json": {"permission_denials": [{"tool_name": "Bash", "tool_input": {"command": "touch b"}}]}}
        self.steps([rm])
        r = self.wf("two", "-y")
        show("U6 crash loop stops only repo, asks", r,
             decisions=[(d.get("reason") or d.get("case"), d["options"]) for d in self.queue()["decisions"]])

    def test_l_ac9_include(self):
        inc = self.tmp / "inc.gitconfig"
        inc.write_text("[user]\n\tname = x\n")
        (self.tmp / ".gitconfig").write_text(f"[include]\n\tpath = {inc}\n")
        self.steps([{"write_file": [[str(inc), "[core]\n\tpager = evil\n"]]}])
        r1 = self.wf("demo", "-y")
        self.reset()
        (self.state / "wf" / "queue.json").unlink()
        attrs = self.repo / ".git" / "info" / "attributes"
        attrs.parent.mkdir(exist_ok=True)
        attrs.write_text("")
        self.steps([{"write_file": [[str(attrs), "* filter=evil\n"]]}])
        r2 = self.wf("demo", "-y")
        show("AC-9 include target", r1)
        show("AC-9 info/attributes", r2)

    def test_m_ac9_hookspath(self):
        hooks = self.tmp / "myhooks"
        hooks.mkdir()
        (hooks / "pre-push").write_text("#!/bin/sh\n")
        subprocess.run(["git", "-C", str(self.repo), "config", "core.hooksPath", str(hooks)], check=True)
        self.steps([{"write_file": [[str(hooks / "pre-push"), "#!/bin/sh\nexit 0 # evil\n"]]}])
        show("AC-9 hooksPath outside .git/hooks", self.wf("demo", "-y"))

    def test_k_u10_boom(self):
        r = self.wf("demo", "-y", mode="boom")
        show("U10 runner bug", r, report=self.report())


def run_scope():
    from test_run import SCOPE
    return SCOPE


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], *sys.argv[1:]], verbosity=0)
