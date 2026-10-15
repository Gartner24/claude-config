"""Spec 0015 AC-5, AC-8: every spec top file in this repo carries one **Paths:** line, and every glob on it is real."""
import fnmatch
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPECS = REPO / "docs" / "specs"


class TestPathsCorpus(unittest.TestCase):
    def test_every_spec(self):
        tracked = subprocess.run(["git", "-C", str(REPO), "ls-files", "-co", "--exclude-standard"], capture_output=True, text=True,
                                 check=True).stdout.splitlines()
        tops = sorted([*SPECS.glob("[0-9][0-9][0-9][0-9]-*.md"), *SPECS.glob("[0-9][0-9][0-9][0-9]-*/index.md")])
        self.assertGreaterEqual(len(tops), 15)
        # Specs are Accepted before their build, so this used to fail on spec 0046 naming a test its build creates.
        # A spec linked from a plan feature with an open box is not built yet either.
        open_specs = set()
        for block in re.split(r"^### ", (REPO / "docs" / "scope" / "scope.md").read_text(), flags=re.M):
            if re.search(r"^\s*- \[ \]", block, re.M):
                open_specs.update(re.findall(r"specs/(\d{4})-", block))
        bad = []
        for top in tops:
            lines = top.read_text().splitlines()
            at = [i for i, l in enumerate(lines) if l.startswith("**Paths:**")]
            status = [i for i, l in enumerate(lines) if l.startswith("**Status**:")]
            rel = top.relative_to(REPO)
            if len(at) != 1 or len(status) != 1 or at[0] != status[0] + 1:
                bad.append(f"{rel}: Paths lines at {at}, Status at {status}")
                continue
            value = lines[at[0]][len("**Paths:**"):].strip()
            if value == "none":
                continue
            globs = re.findall(r"`([^`]+)`", value)
            if not globs:
                bad.append(f"{rel}: no globs")
            # A spec not yet built (Proposed, In Progress) may name the files its build will create.
            unbuilt = re.match(r"\*\*Status\*\*:\s*(Proposed|In Progress)", lines[status[0]]) or top.relative_to(SPECS).parts[0][:4] in open_specs
            for g in globs:
                if g.startswith("docs/") or not unbuilt and not any(fnmatch.fnmatchcase(f, g) for f in tracked):
                    bad.append(f"{rel}: {g} matches no tracked file or is under docs/")
        self.assertEqual(len(bad), 0, f"{len(bad)} offender(s):\n" + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
