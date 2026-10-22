"""Spec 0069 AC-11: the handover memory script's own self checks run with the suite."""
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestHandoverMemory(unittest.TestCase):
    # covers: spec 0069 AC-2, AC-6 to AC-9, AC-13 to AC-20 (quote or drop, prune, ages, close, lint, path, ids, detail files)
    def test_self_check(self):
        r = subprocess.run([sys.executable, "-B", str(REPO / "scripts" / "handover-memory.py"), "--test"], capture_output=True,
                           text=True, stdin=subprocess.DEVNULL, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("handover-memory self checks: all passed", r.stdout)


TEMPLATES = REPO / "claude-home" / "mods" / "wf-handoff" / "templates"


class TestTemplates(unittest.TestCase):
    # covers: spec 0069 AC-1 (four kinds only, no owner message copy), AC-3 (the writer, its quote rule)
    def test_sections_keep_four_kinds_and_no_owner_copy(self):
        text = (TEMPLATES / "sections.md").read_text()
        for gone in ("## What the owner said", "## Tried and failed", "Every message the owner typed", "Write it rich"):
            self.assertNotIn(gone, text)
        for kept in ("Start ONE writer agent", "handover-memory.py path", "check <index> --transcript", "prune <index>",
                     "Handover memory: <index path>", "memory not written: <reason>", "Writer prompt:", "- Q:", "- S:",
                     "- D:", "- L:", "--move <file>", 'landed: <repo relative path>', 'replaced by D<new>'):
            self.assertIn(kept, text)

    # covers: spec 0069 decision 5 as amended 2026-10-22 (the slot keeps its Open questions section)
    def test_slot_keeps_open_questions(self):
        sections = (TEMPLATES / "sections.md").read_text()
        self.assertIn("- the Open questions section, as below;", sections)
        self.assertIn("\n## Open questions and loose ends\n", sections.split("Writer prompt:")[0])
        self.assertIn("an open question in either one is open", (TEMPLATES / "instructions.md").read_text())

    # covers: spec 0069 AC-5 (the fresh chat reads only the index, shows what is pending and what was lost)
    def test_instructions_read_only_the_index(self):
        text = (TEMPLATES / "instructions.md").read_text()
        self.assertNotIn("jq ", text)
        self.assertNotIn("the messages win", text)
        for kept in ("Handover memory:", "handover-memory.py ages <index>", "Do not read the previous transcript",
                     "every open Q item with its age", "every open S item", "every L item", "dropped:", "memory not written:"):
            self.assertIn(kept, text)


if __name__ == "__main__":
    unittest.main()
