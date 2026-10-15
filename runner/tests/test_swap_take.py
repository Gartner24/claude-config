"""Spec 0020 AC-5: a run takes a swap `wf` wrote to the ledger, and stops on any other change."""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_run import RunCase, WF  # noqa: E402
import run  # noqa: E402
import wf  # noqa: E402

STAMP = "20261013-010203"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class SwapTake(RunCase):
    def setUp(self):
        super().setUp()
        self.live = self.tmp / ".claude"
        (self.live / "hooks").mkdir(parents=True)
        (self.live / "settings.json").write_text("{}")
        self.hook = self.live / "hooks2" / "h.sh"
        self.new = json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": f"bash {self.hook}"}]}]}})

    def ledger(self, files):
        (self.state / "wf").mkdir(parents=True, exist_ok=True)
        line = {"stamp": STAMP, "pid": 1, "at": "2026-10-13T01:02:03+00:00", "files": files}
        with open(self.state / "wf" / "swaps.jsonl", "a") as f:
            f.write("not json\n" + json.dumps(line) + "\n")

    def denied(self, n):
        a = self.argv(n)["argv"]
        return a[a.index("--disallowedTools") + 1]

    def swap_step(self):
        return {"write_file": [[str(self.hook), "#!/bin/sh\n"], [str(self.live / "settings.json"), self.new]]}

    # covers: AC-5 (a ledger line written before the run, mid swap, still accepts; guard rebuilt; next call gets the
    # new deny list; log line and run.json setups)
    def test_taken(self):
        self.ledger({str(self.live / "settings.json"): sha(self.new), str(self.hook): sha("#!/bin/sh\n")})
        self.steps([self.swap_step(), {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        folder, rec = self.run_record()
        self.assertEqual([s["stamp"] for s in rec["setups"]], [STAMP])
        self.assertIn(f"setup {STAMP} taken", (folder / "log.txt").read_text())
        self.assertEqual(len(rec["calls"]), 3)
        rule = f"Edit(/{self.live}/hooks2/**)"
        self.assertNotIn(rule, self.denied(1))
        self.assertIn(f"Edit(/{self.state}/wf/**)", self.denied(1))
        self.assertIn(rule, self.denied(2))
        g = rec["repos"][0]["guard"]
        self.assertEqual(g["guarded_files"][str(self.live / "settings.json")], sha(self.new))
        self.assertEqual(g["guarded_files"][str(self.hook)], sha("#!/bin/sh\n"))

    # covers: AC-5 (no ledger line, a different hash, a new hook script missing from the ledger: guard_changed)
    def test_not_taken(self):
        cases = [(None, f"{self.live}/settings.json changed during the run"),
                 ({str(self.live / "settings.json"): sha("other")}, f"{self.live}/settings.json changed during the run"),
                 ({str(self.live / "settings.json"): sha(self.new)}, f"{self.hook} is new in setup {STAMP}")]
        for files, detail in cases:
            with self.subTest(detail):
                for p in (self.state, self.fakes / "count"):
                    if p.is_dir():
                        shutil.rmtree(p)
                    elif p.exists():
                        p.unlink()
                (self.repo / "docs" / "scope" / "scope.md").write_text((self.repo / "docs" / "scope" / "scope.md")
                                                                     .read_text().replace("[x] Build", "[ ] Build"))
                (self.live / "settings.json").write_text("{}")
                if self.hook.exists():
                    self.hook.unlink()
                    self.hook.parent.rmdir()
                if files:
                    self.ledger(files)
                self.steps([self.swap_step(), {}])
                r = self.wf("demo", "-y")
                rec = self.assert_stopped(r, "guard_changed", calls=1)
                self.assertIn(detail, rec["detail"])
                self.assertEqual(rec["setups"], [])

    # covers: spec 0040 AC-2 (a park from the run's own write deny records its path; once a taken setup no longer
    # denies it, the run retakes the feature, withdraws its open question and builds it again in the same run)
    def test_write_deny_park_retaken(self):
        # A settings hook in the repo's tools/ folder makes the guard deny the whole folder (spec 0007 hook_tokens).
        (self.repo / "tools").mkdir()
        (self.repo / "tools" / "h.sh").write_text("#!/bin/sh\n")
        old = json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": f"bash {self.repo}/tools/h.sh"}]}]}})
        (self.live / "settings.json").write_text(old)
        self.ledger({str(self.live / "settings.json"): sha(self.new), str(self.hook): sha("#!/bin/sh\n")})
        target = str(self.repo / "tools" / "x.py")
        denied = {**self.swap_step(), "tick": False,
                  "json": {"permission_denials": [{"tool_name": "Edit", "tool_use_id": "t1",
                                                   "tool_input": {"file_path": target}}]}}
        self.steps([denied, {}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        folder, rec = self.run_record()
        log = (folder / "log.txt").read_text()
        self.assertIn("park 1. Loop: denied:", log)
        self.assertIn(f"setup {STAMP} taken", log)
        self.assertIn(f"retaken 1. Loop: {target} no longer denied", log)
        self.assertRegex(r.stdout, r"\nstale: [a-z0-9]{4} 1\. Loop\n")
        self.assertEqual(len(rec["calls"]), 4)
        self.assertEqual([(e["feature"], e["outcome"]) for e in rec["features"]], [("1. Loop", "feature_done")])
        q = json.loads((self.state / "wf" / "queue.json").read_text())
        self.assertEqual((q["parks"], q["decisions"]), ([], []))

    def text_blocked(self):
        return {**self.swap_step(), "tick": False,
                "json": {"result": "runner/ is write denied here\nBLOCKED: run ./install.sh live first"}}

    # covers: spec 0040 AC-2 (a block the call only stated in text, with no recorded denial, is tried once more after
    # a newer setup is taken)
    def test_text_block_retaken_once(self):
        self.ledger({str(self.live / "settings.json"): sha(self.new), str(self.hook): sha("#!/bin/sh\n")})
        self.steps([self.text_blocked(), {}, {}, {"tick": False}])
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        folder, rec = self.run_record()
        log = (folder / "log.txt").read_text()
        self.assertIn("park 1. Loop: blocked:", log)
        self.assertIn("retaken 1. Loop: the setup changed", log)
        self.assertEqual([(e["feature"], e["outcome"]) for e in rec["features"]], [("1. Loop", "feature_done")])

    # covers: spec 0040 AC-2 (blocked again after its retry, it parks with the new setup and is not tried again)
    def test_text_block_no_loop(self):
        self.ledger({str(self.live / "settings.json"): sha(self.new), str(self.hook): sha("#!/bin/sh\n")})
        again = {"tick": False, "json": {"result": "still no\nBLOCKED: run ./install.sh live first"}}
        self.steps([self.text_blocked(), again, {}, {}])
        r = self.wf("demo", "-y")
        folder, rec = self.run_record()
        self.assertEqual(len(rec["calls"]), 2, (folder / "log.txt").read_text())
        self.assertEqual((folder / "log.txt").read_text().count("retaken 1. Loop"), 1)

    def queue_file(self):
        return json.loads((self.state / "wf" / "queue.json").read_text())

    # covers: spec 0040 AC-2 (a text block from an earlier run stays parked with no newer setup, and is retaken once
    # a newer swaps.jsonl line exists)
    def test_earlier_run_text_block(self):
        self.steps([{"tick": False, "json": {"result": "no\nBLOCKED: run ./install.sh live first"}}, {}, {}, {"tick": False}])
        self.wf("demo", "-y")
        self.wf("demo", "-y")
        self.assertEqual(len(self.calls()), 1, "no newer setup: it must stay parked")
        self.ledger({str(self.live / "settings.json"): sha("{}")})
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log = (sorted((self.state / "wf" / "runs").iterdir())[-1] / "log.txt").read_text()
        self.assertIn("retaken 1. Loop: the setup changed", log)
        self.assertEqual(self.queue_file()["parks"], [])

    def deny_park(self, target):
        (self.repo / "tools").mkdir()
        (self.repo / "tools" / "h.sh").write_text("#!/bin/sh\n")
        old = json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": f"bash {self.repo}/tools/h.sh"}]}]}})
        (self.live / "settings.json").write_text(old)
        self.steps([{"tick": False, "json": {"permission_denials": [
            {"tool_name": "Edit", "tool_use_id": "t1", "tool_input": {"file_path": target}}]}}, {}, {}])
        self.wf("demo", "-y")
        return self.queue_file()["parks"]

    # covers: spec 0040 AC-2 (with no guard built, wf queue still shows a denied_path park whose deny is gone)
    def test_queue_keeps_park(self):
        parks = self.deny_park(str(self.repo / "tools" / "x.py"))
        self.assertEqual([p.get("denied_path") for p in parks], [str(self.repo / "tools" / "x.py")])
        (self.live / "settings.json").write_text("{}")
        r = subprocess.run([sys.executable, str(WF), "queue", "demo"], capture_output=True, text=True, env=self.env)
        self.assertIn("parked: 1. Loop: denied", r.stdout, r.stdout + r.stderr)

    # covers: spec 0040 AC-2 (an Edit denial on a path the run's guard does not deny records no denied_path, so the
    # run never frees it and the park stays)
    def test_no_path_outside_guard(self):
        parks = self.deny_park(str(self.repo / "src" / "x.py"))
        self.assertEqual([(p["reason"], "denied_path" in p) for p in parks], [("denied", False)])

    # covers: AC-5 (a repo git hook moved beside an accepted swap is not taken: the repo stops)
    def test_repo_hook_beside_swap(self):
        hooks = self.repo / ".git" / "hooks"
        hooks.mkdir()
        (hooks / "pre-commit").write_text("#!/bin/sh\n")
        self.ledger({str(self.live / "settings.json"): sha(self.new), str(self.hook): sha("#!/bin/sh\n")})
        step = self.swap_step()
        step["write_file"].append([".git/hooks/pre-commit", "evil"])
        self.steps([step, {}])
        r = self.wf("demo", "-y")
        rec = self.assert_stopped(r, "guard_changed", calls=1, repo=True)
        self.assertTrue(rec["detail"].startswith(f"{hooks}/pre-commit changed"), rec["detail"])

    # covers: AC-5 (the rebuild keeps the old baseline of a repo path the ledger does not accept, so the next check
    # still stops; a path the ledger accepts gets its new hash)
    def test_rebuild_keeps_repo_baseline(self):
        hooks = self.repo / ".git" / "hooks"
        hooks.mkdir()
        (hooks / "pre-commit").write_text("#!/bin/sh\n")
        args = wf.build_parser()[0].parse_args(["run", str(self.repo), "-y"])
        with mock.patch.dict(os.environ, self.env), redirect_stdout(io.StringIO()):
            r, rc = run.planned(args)
            self.assertIsNone(rc)
            old = dict(r.repo["guard"]["guarded_files"])
            (hooks / "pre-commit").write_text("evil")
            (self.live / "settings.json").write_text(self.new)
            self.hook.parent.mkdir()
            self.hook.write_text("#!/bin/sh\n")
            self.ledger({str(self.live / "settings.json"): sha(self.new), str(self.hook): sha("#!/bin/sh\n")})
            r.take_setup(STAMP, run.ledger())
            g = r.repo["guard"]["guarded_files"]
            self.assertEqual(g[str(hooks / "pre-commit")], old[str(hooks / "pre-commit")])
            self.assertEqual(g[str(self.live / "settings.json")], sha(self.new))
            self.assertEqual(r.record["setups"][0]["stamp"], STAMP)
            with self.assertRaises(run.Stop) as s:
                r.files_changed()
            self.assertEqual(s.exception.reason, "guard_changed")
            os.close(r.lock_fd)

    # covers: AC-3 (live_dir is $CLAUDE_CONFIG_DIR else ~/.claude, for the guard, the deny list and finish)
    def test_live_dir(self):
        import finish
        conf = self.tmp / "conf"
        conf.mkdir()
        (conf / "settings.json").write_text('{"sandbox": {"excludedCommands": ["x"]}}')
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp), "CLAUDE_CONFIG_DIR": str(conf)}):
            self.assertEqual((run.live_dir(), finish.live_dir()), (str(conf), str(conf)))
            deny = run.deny_paths(str(self.repo), f"{self.repo}/.git", [])
            self.assertIn(str(conf / "settings.json"), deny)
            self.assertEqual(run.user_exclusions(), f"{conf}/settings.json sets sandbox.excludedCommands")
            # Review (guard coverage): ~/.claude stays denied, guarded and read for exclusions with CLAUDE_CONFIG_DIR set.
            self.assertIn(str(self.live / "settings.json"), deny)
            self.assertEqual(run.expand("~/.claude/.credentials.json"),
                             [f"{conf}/.credentials.json", f"{self.live}/.credentials.json"])
            (conf / "settings.json").write_text("{}")
            (self.live / "settings.json").write_text('{"sandbox": {"excludedCommands": ["x"]}}')
            self.assertEqual(run.user_exclusions(), f"{self.live}/settings.json sets sandbox.excludedCommands")
            self.assertIsNone(run.config_problem())
        # Review (parser differential): a relative value resolves differently for wf and for a call in the repo.
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp), "CLAUDE_CONFIG_DIR": "conf"}):
            self.assertEqual(run.config_problem(), "CLAUDE_CONFIG_DIR is not an absolute path: conf")
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp)}):
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
            self.assertEqual(run.live_dir(), str(self.tmp / ".claude"))
            self.assertEqual(run.claude_dirs(), [str(self.tmp / ".claude")])

    # covers: AC-5 review (both settings folders guarded: a change to ~/.claude with CLAUDE_CONFIG_DIR set still stops)
    def test_home_claude_guarded(self):
        conf = self.tmp / "conf"
        conf.mkdir()
        (conf / "settings.json").write_text("{}")
        self.env["CLAUDE_CONFIG_DIR"] = str(conf)
        self.steps([{"write_file": [[str(self.live / "settings.json"), '{"hooks": {}}']]}, {}])
        r = self.wf("demo", "-y")
        rec = self.assert_stopped(r, "guard_changed", calls=1)
        self.assertTrue(rec["detail"].startswith(f"{self.live}/settings.json changed"), rec["detail"])
        self.env["CLAUDE_CONFIG_DIR"] = "conf"
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 5, r.stdout)
        self.assertIn("refused: no_sandbox: CLAUDE_CONFIG_DIR is not an absolute path: conf", r.stdout)

    # covers: AC-5 (link resolved, a folder whose files are all in the ledger, an absent file never)
    def test_accepted_by(self):
        (self.tmp / "real").write_text("x")
        (self.tmp / "link").symlink_to(self.tmp / "real")
        (self.tmp / "d").mkdir()
        (self.tmp / "d" / "a").write_text("a")
        lines = [("1", {str(self.tmp / "real"): sha("x")}), ("2", {str(self.tmp / "d" / "a"): sha("a")})]
        # Review (parser differential): a link never borrows its target's ledger entry; a resolved parent does.
        self.assertIsNone(run.accepted_by(str(self.tmp / "link"), lines))
        (self.tmp / "dirlink").symlink_to(self.tmp)
        self.assertEqual(run.accepted_by(str(self.tmp / "dirlink" / "real"), lines), "1")
        self.assertEqual(run.accepted_by(str(self.tmp / "d"), lines), "2")
        (self.tmp / "d" / "b").write_text("b")
        self.assertIsNone(run.accepted_by(str(self.tmp / "d"), lines))
        self.assertIsNone(run.accepted_by(str(self.tmp / "gone"), [("1", {str(self.tmp / "gone"): "absent"})]))


if __name__ == "__main__":
    unittest.main()
