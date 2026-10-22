"""Spec 0072 AC-7 and AC-10: every old AGENTS.md line has a home that exists, and every path a map card cites exists."""
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PINNED = "c08534f65dd3a85710901aa1bea5f2024264199c"
ROW = re.compile(r"^\| (\d+)(?:-(\d+))? \| (\S+) \|$")


def old_lines():
    text = subprocess.run(["git", "-C", str(REPO), "show", f"{PINNED}:AGENTS.md"], capture_output=True, text=True,
                          check=True, stdin=subprocess.DEVNULL).stdout
    return {n: l for n, l in enumerate(text.splitlines(), 1) if l.strip() and not l.startswith("#")}


def homes():
    out = {}
    for row in (REPO / "map/_meta/line-homes.md").read_text().splitlines():
        m = ROW.match(row)
        if m:
            for n in range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1):
                out[n] = m.group(3)
    return out


class TestLineHomes(unittest.TestCase):
    # covers: AC-7 (no old AGENTS.md line without an entry; no entry naming a file that does not exist)
    def test_every_old_line_has_a_home(self):
        have = homes()
        missing = [f"{n}: {l[:60]}" for n, l in old_lines().items() if n not in have]
        self.assertEqual(missing, [], f"{len(missing)} old lines with no home:\n" + "\n".join(missing))

    def test_homes_exist(self):
        gone = sorted({f for f in homes().values() if not (REPO / f).is_file()})
        self.assertEqual(gone, [], f"{len(gone)} home files do not exist: {gone}")


class TestCards(unittest.TestCase):
    # covers: AC-10 (the catalog, context, schema, both templates, 8 object cards, 5 process cards and effects page exist)
    def test_card_set(self):
        want = ["CLAUDE.md", "CONTEXT.md", "_meta/schema.md", "_templates/object.md", "_templates/process.md",
                "effects/CONTEXT.md"]
        want += [f"objects/{n}.md" for n in ("install", "mods", "rules", "skills", "specs", "scope", "suite", "runner")]
        want += [f"processes/{n}.md" for n in ("install", "sync", "checks", "land-a-feature", "handoff")]
        gone = [w for w in want if not (REPO / "map" / w).is_file()]
        self.assertEqual(gone, [], f"{len(gone)} cards missing: {gone}")

    # covers: AC-10 (every path or path:line a card cites exists, by the same checker the PR runs)
    def test_citations_exist(self):
        cards = sorted(str(p.relative_to(REPO)) for p in (REPO / "map").rglob("*.md"))
        r = subprocess.run(["python3", str(REPO / "scripts/ref-check.py"), "check", *cards], cwd=REPO,
                           capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
