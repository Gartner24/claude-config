"""Spec 0072 AC-7 and AC-10: every old AGENTS.md line has a home that exists, and every path a map card cites exists."""
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PINNED = "c08534f65dd3a85710901aa1bea5f2024264199c"
ROW = re.compile(r"^\| (\d+)(?:-(\d+))? \| (\S+) \|$")


# (old line, token) pairs the card words differently on purpose; each has its reason.
PARAPHRASED = {
    (40, "claude-home/rules/x.md"),  # example path: the card says "a file in claude-home/rules/" (ref-check cannot cite a made-up file)
    (40, "~/.claude/rules/x.md"),    # same example, installed side
    (43, "claude-home/mods/<name>/"),  # <name> placeholder: ref-check rejects <> in a cited path; the card names each mod
    (49, "~/claude-config"),         # spelling: CLAUDE.md names the home chat's folder as "home chat" rules in CLAUDE.local.md
    (66, "_archive/runner/wf.py"),   # path: the scope card says "the plan parser" and cites chip-dash plan.py, the live reader
    # spec 0077 AC-3 moved these rule files to claude-home/rules-on-demand/; the cards cite the new path
    (35, "claude-home/rules/cheap-worker.md"),
    (54, "claude-home/rules/check-gates.md"),
    (66, "claude-home/rules/scope-contract.md"),
}


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

    # covers: AC-7 review fix (a row naming an existing file is not enough: every backticked token of the old line
    # must appear in its home file, so a dropped tail like line 51's cannot hide behind a row)
    def test_home_holds_every_token(self):
        have = homes()
        texts = {}
        missing = []
        for n, line in old_lines().items():
            home = texts.setdefault(have[n], (REPO / have[n]).read_text())
            for tok in re.findall(r"`([^`]+)`", line):
                if (n, tok) not in PARAPHRASED and tok not in home:
                    missing.append(f"{n}: `{tok}` not in {have[n]}")
        self.assertEqual(missing, [], f"{len(missing)} tokens lost:\n" + "\n".join(missing))

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
