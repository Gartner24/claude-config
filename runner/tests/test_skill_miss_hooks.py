"""Spec 0036: the two missed skill hook entries in the repo settings.json, run as the harness runs them."""
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

SETTINGS = pathlib.Path(__file__).resolve().parents[2] / "claude-home" / "settings.json"
DETECT = "~/.claude/skills/jjstack/hooks/skill-miss-detect.sh"
CLEAR = "~/.claude/skills/jjstack/hooks/skill-fired-clear.sh"


def entries(event):
    return json.loads(SETTINGS.read_text())["hooks"][event]


def commands(event, script):
    return [(e.get("matcher"), h["command"]) for e in entries(event) for h in e["hooks"] if script in h["command"]]


class SkillMissHooks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self.tmp.name)
        hooks = self.home / ".claude" / "skills" / "jjstack" / "hooks"
        hooks.mkdir(parents=True)
        # Stand ins for the vendored jjstack scripts: each notes it ran and the stdin it got.
        for name in ("skill-miss-detect.sh", "skill-fired-clear.sh"):
            p = hooks / name
            p.write_text(f'#!/bin/sh\ncat > "$HOME/{name}.ran"\n')
            p.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def fire(self, shell, command, wf_run):
        env = {k: v for k, v in os.environ.items() if k != "WF_RUN"}
        env["HOME"] = str(self.home)
        if wf_run:
            env["WF_RUN"] = "1"
        return subprocess.run([shell, "-c", command], input='{"prompt": "x"}', env=env, capture_output=True, text=True)

    # covers: AC-1 (one UserPromptSubmit entry, no matcher, that starts skill-miss-detect.sh)
    def test_user_prompt_submit_entry(self):
        found = commands("UserPromptSubmit", DETECT)
        self.assertEqual(len(found), 1, found)
        self.assertIsNone(found[0][0])

    # covers: AC-1 (one PreToolUse entry with matcher Skill that starts skill-fired-clear.sh)
    def test_pre_tool_use_skill_entry(self):
        found = commands("PreToolUse", CLEAR)
        self.assertEqual([m for m, _ in found], ["Skill"], found)

    # covers: AC-1, AC-2 (each command runs its jjstack script with the hook input, and does not under WF_RUN)
    def test_commands_run_outside_wf_and_stay_off_under_it(self):
        for event, script in (("UserPromptSubmit", DETECT), ("PreToolUse", CLEAR)):
            (_, command), = commands(event, script)
            ran = self.home / (script.rsplit("/", 1)[1] + ".ran")
            for shell in ("sh", "bash"):
                with self.subTest(event=event, shell=shell):
                    p = self.fire(shell, command, wf_run=True)
                    self.assertEqual((p.returncode, p.stdout), (0, ""), p.stderr)
                    self.assertFalse(ran.exists(), f"{script} ran under WF_RUN")
                    p = self.fire(shell, command, wf_run=False)
                    self.assertEqual((p.returncode, p.stdout), (0, ""), p.stderr)
                    self.assertEqual(ran.read_text(), '{"prompt": "x"}')
                    ran.unlink()


if __name__ == "__main__":
    unittest.main()
