"""claude-home/settings.json (row 105): the user scope file install copies live, so the owner's permission decisions
of 2026-10-22 have to be in it."""
import json
import unittest
from pathlib import Path

SETTINGS = Path(__file__).resolve().parents[1] / "claude-home" / "settings.json"


class TestClaudeSettings(unittest.TestCase):
    # covers: row 105 (project MCP servers do not auto start; no self edit allows on the global rules; Workflow allowed)
    def test_owner_decisions(self):
        s = json.loads(SETTINGS.read_text())
        self.assertIs(s.get("enableAllProjectMcpServers"), False)
        allow = s["permissions"]["allow"]
        for rule in ("Edit(~/.claude/CLAUDE.md)", "Edit(~/.claude/rules/**)"):
            self.assertNotIn(rule, allow)
        self.assertIn("Workflow", allow)
        # claude-config.py: only the read only subcommands; install, sync and update --apply ask first
        tool = [a for a in allow if "claude-config.py" in a]
        self.assertEqual(sorted(a.split("claude-config.py ", 1)[1] for a in tool),
                         ["drift)", "hook-files)", "update --plan)"], tool)


if __name__ == "__main__":
    unittest.main()
